"""Domain glue for the HTTP API: controller/objective/memory/settings shaping.

Pure(ish) helpers extracted from the route handlers so `rad.api_routes.*` stays a
thin (method, path, query, body) → (status, payload) mapping. Everything here
goes through the same Controller / policy gates as the CLI — no file paths are
accepted from clients except through the registered-artifact gate in
`artifact_content`. Depends only on `rad.api_security` (no cycles).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from rad.api_security import MAX_BODY, ApiError, _is_within

SETTINGS_KEYS = ("workspace", "free_lock", "force_provider", "model", "tts", "stt",
                 "allow_outside_workspace", "allow_localhost_web")

FORBIDDEN_SETTINGS_KEYS = {"max_plan_tasks", "max_tool_rounds", "tool_calls", "budget",
                           "tool_router", "auto"}


# ---------------------------------------------------------------- objective / memory shaping

def obj_summary(o, tasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    d = {"id": o.id, "goal": o.goal, "status": o.status, "created": o.created, "updated": o.updated,
         "usage": o.usage.to_dict(), "budget": o.budget.to_dict(), "result": (o.result or "")[:2000],
         "verification": (o.verification or {}).get("objective", {}).get("status", ""),
         "result_summary": o.result_summary or "", "failure": (o.failure or "")[:500],
         "plan_version": getattr(o, "plan_version", 0)}
    if tasks is not None:
        d["tasks_total"] = len(tasks)
        d["tasks_completed"] = sum(1 for t in tasks if str(t.get("status")) == "COMPLETED")
        d["tasks_failed"] = sum(1 for t in tasks if str(t.get("status")) in ("FAILED", "BLOCKED"))
    return d


def mem_entry(e) -> Dict[str, Any]:
    return {"id": e.id, "layer": e.layer, "text": e.text, "origin": e.origin, "confidence": e.confidence,
            "verification": e.verification, "strength": e.strength}


# ---------------------------------------------------------------- lifecycle gates

def may_run(home) -> bool:
    if bool(home.cfg.get("auto")):
        return True
    try:
        from rad.authority import confirmation_is_automatic
        return confirmation_is_automatic(home)
    except Exception:
        return False


def create_objective(home, make_ctl: Callable[[], Any], body: Dict[str, Any],
                     background: Callable[[str, Callable[[], Any]], None]) -> Tuple[int, Any]:
    """Validate the create body, then create (and maybe background-start) an objective.

    `make_ctl()` is only invoked after validation succeeds — same ordering as the
    original inline handler, so a bad body never constructs a Controller.
    """
    from rad.control.objectives import Budget
    goal = str(body.get("goal", "")).strip()
    if not goal or len(goal) > 4000:
        raise ApiError(400, "goal required (≤4000 chars)")
    crit = [str(x)[:300] for x in (body.get("criteria") or [])][:20]
    cons = [str(x)[:300] for x in (body.get("constraints") or [])][:20]
    bud = body.get("budget") or {}
    if not isinstance(bud, dict) or any(k not in Budget.__dataclass_fields__ for k in bud):
        raise ApiError(400, f"budget keys must be in {sorted(Budget.__dataclass_fields__)}")
    ctl = make_ctl()
    run = bool(body.get("run", True))
    auto = may_run(home)
    obj = ctl.create(goal, success_criteria=crit, constraints=cons,
                     budget=Budget(**bud) if bud else None, auto=auto)
    if run and auto:
        background(obj.id, lambda: ctl.run(obj))
        return 202, {**obj_summary(obj), "started": True}
    return 201, {**obj_summary(obj), "started": False,
                 "note": "created PENDING: run it with `rad objective run` (config auto=false)" if run else "created PENDING"}


def artifact_content(home, ctl, obj, ref: str) -> Tuple[int, Any]:
    """Redacted text preview of a REGISTERED artifact of this objective.

    The client supplies an artifact ref (id / path / filename), never a raw path: the
    only way in is through the objective's artifact registry. Even then the file must
    live inside the workspace or the RAD home, must be text, and is capped + redacted.
    """
    from rad.control.observer import Observer
    from rad.policy import redact
    ref = (ref or "").strip()
    if not ref:
        raise ApiError(400, "ref=<artifact id|path|filename> required")
    reg = Observer(ctl.store.dir(obj.id)).artifacts()
    art = reg.get(ref)
    if not art:
        hits = [a for a in reg.values() if a["location"] == ref or Path(a["location"]).name == ref]
        hits.sort(key=lambda a: -a.get("version", 1))
        art = hits[0] if hits else None
    if not art:
        raise ApiError(404, f"not an artifact of {obj.id}")
    loc = Path(art["location"])
    try:
        resolved = loc.expanduser().resolve()
    except Exception:
        raise ApiError(400, "unresolvable artifact location")
    roots = []
    try:
        roots.append(home.workspace().resolve())
    except Exception:
        pass
    try:
        roots.append(Path(home.root).resolve())
    except Exception:
        pass
    if not any(_is_within(resolved, r) for r in roots):
        raise ApiError(403, "artifact location outside workspace/home")
    if not resolved.is_file():
        raise ApiError(404, "artifact file not found on disk")
    try:
        if resolved.stat().st_size > MAX_BODY:
            raise ApiError(413, "artifact too large to preview (≤256 KB)")
        raw = resolved.read_bytes()
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ApiError(415, "artifact is not UTF-8 text")
    except ApiError:
        raise
    except OSError as e:
        raise ApiError(404, f"cannot read artifact: {e}")
    lines = text.splitlines()
    truncated = len(lines) > 400
    return 200, {"artifact": art, "path": str(resolved), "sha256": art.get("sha256", ""),
                 "bytes": len(raw), "lines": len(lines), "truncated": truncated,
                 "preview": redact("\n".join(lines[:400]))}


# ---------------------------------------------------------------- objective view payloads

def plan_payload(ctl, obj) -> Dict[str, Any]:
    from rad.control.events import EventLog
    log = EventLog(ctl.store.events_path(obj.id))
    plans = [e for e in log.read(kind="PLAN_CREATED")]
    replans = [e for e in log.read(kind="REPLAN")]
    tasks = ctl.store.load_tasks(obj.id)
    return {"objective_id": obj.id,
            "plan_version": max([int(e.data.get("plan_version", 0)) for e in plans + replans] + [obj.plan_version]),
            "source": plans[-1].data.get("source", "") if plans else "",
            "attempts": plans[-1].data.get("attempts", 0) if plans else 0,
            "estimated_tools": plans[-1].data.get("estimated_tools"),
            "compacted": plans[-1].data.get("compacted", False) if plans else False,
            "replans": [{"plan_version": e.data.get("plan_version"), "task": e.data.get("task_id"),
                         "new_tasks": e.data.get("new_tasks", []),
                         "superseded": e.data.get("superseded", []), "at": e.at} for e in replans],
            "tasks": [{"id": t.get("id"), "text": t.get("text"), "depends_on": t.get("depends_on"),
                       "checks": [c.get("description") or c.get("kind") for c in (t.get("checks") or [])],
                       "status": t.get("status"), "plan_version": t.get("plan_version")} for t in tasks]}


def recovery_payload(ctl, obj) -> Dict[str, Any]:
    from rad.control.events import EventLog
    log = EventLog(ctl.store.events_path(obj.id))
    tasks = {t.get("id"): t for t in ctl.store.load_tasks(obj.id)}
    decisions = []
    for e in log.read(kind="RECOVERY_DECISION"):
        tid = e.task_id
        decisions.append({"at": e.at, "task_id": tid, "task": tasks.get(tid, {}).get("text", ""),
                          "strategy": e.data.get("strategy"), "failure_class": e.data.get("failure_class"),
                          "reason": str(e.data.get("reason", ""))[:300]})
    failed = [{"id": t.get("id"), "text": t.get("text", "")[:200], "status": t.get("status"),
               "failure_class": t.get("failure_class", ""), "note": str(t.get("note", ""))[:300],
               "attempts": t.get("attempts", 0)}
              for t in tasks.values() if t.get("failure_class") or t.get("status") in ("FAILED", "RETRYING")]
    return {"objective_id": obj.id, "decisions": decisions, "failed_tasks": failed,
            "retries_used": obj.usage.retries, "retry_budget": obj.budget.retries}


def observations_payload(ctl, obj, q: Dict[str, str]) -> Dict[str, Any]:
    from rad.control.observer import Observer
    from rad.policy import redact
    obs = Observer(ctl.store.dir(obj.id))
    rows = []
    for obs_f in sorted(obs.dir.glob("obs_*.json")):
        o = obs.load(obs_f.stem)
        if not o:
            continue
        if q.get("task") and o.task_id != q["task"]:
            continue
        rows.append({
            "id": o.id, "task_id": o.task_id, "tool": o.tool,
            "args": {k: redact(str(v))[:200] for k, v in list(o.args.items())[:8]},
            "status": o.status, "duration_ms": o.duration_ms,
            "output": redact(o.output)[:800], "artifacts": list(o.artifacts),
            "evidence_kinds": sorted({str(e.get("kind")) for e in o.evidence if e.get("kind")}),
            "at": o.at,
        })
    rows.sort(key=lambda r: r["at"])
    return {"objective_id": obj.id, "count": len(rows),
            "observations": rows[-int(q.get("n", 400) or 400):]}


def live_payload(ctl, obj, q: Dict[str, str]) -> Dict[str, Any]:
    from rad.control.budgets import BudgetManager
    from rad.control.events import EventLog
    from rad.control.observer import Observer
    tasks = ctl.store.load_tasks(obj.id)
    open_tasks = [t for t in tasks if str(t.get("status")) not in ("COMPLETED", "CANCELLED")]
    current = next((t for t in tasks if str(t.get("status")) in
                    ("RUNNING", "OBSERVING", "VERIFYING", "RETRYING")), None)
    evs = []
    try:
        since = int(q.get("since_seq", 0) or 0)
        evs = [e.__dict__ for e in EventLog(ctl.store.events_path(obj.id)).read() if e.seq > since]
    except (ValueError, OSError):
        evs = []
    arts = Observer(ctl.store.dir(obj.id)).artifacts()
    return {"objective": obj_summary(obj),
            "status": obj.status,
            "plan_version": obj.plan_version,
            "current_task": {"id": current.get("id"), "text": current.get("text"),
                             "status": current.get("status"),
                             "started": current.get("started"),
                             "attempts": current.get("attempts", 0)} if current else None,
            "tasks": {"total": len(tasks), "open": len(open_tasks),
                      "by_status": {s: sum(1 for t in tasks if str(t.get("status")) == s)
                                    for s in sorted({str(t.get("status")) for t in tasks})}},
            "budget": BudgetManager(obj.budget, obj.usage, objective_id=obj.id).to_dict(),
            "usage": obj.usage.to_dict(),
            "artifacts": len(arts),
            "retries": {"used": obj.usage.retries, "budget": obj.budget.retries},
            "verification": (obj.verification or {}).get("objective", {}).get("status", ""),
            "events": evs[-int(q.get("n", 50) or 50):]}


# ---------------------------------------------------------------- status / settings / authority

def status_payload(home, make_ctl: Callable[[], Any], runs: Dict[str, Any]) -> Dict[str, Any]:
    """One object: health, brain, objectives, tasks, memory, agents, jobs, schema."""
    from rad import __version__
    from rad.control.events import EventLog
    from rad.storage import Storage
    st = Storage(home)
    st.pending()
    ctl = make_ctl()
    objs = ctl.store.list()
    by_status: Dict[str, int] = {}
    tasks_open = 0
    for o in objs:
        by_status[o.status] = by_status.get(o.status, 0) + 1
        try:
            tasks_open += sum(1 for t in ctl.store.load_tasks(o.id)
                              if str(t.get("status")) not in ("COMPLETED", "CANCELLED"))
        except Exception:
            pass
    chain = []
    try:
        from rad.router import RouterState
        chain = [f"{e.spec.name}:{e.model}" for e in RouterState(home).build_chain()]
    except Exception:
        pass
    mem: Dict[str, int] = {}
    try:
        from rad.memory import Memory
        m = Memory(home)
        for layer in ("working", "episodic", "semantic", "procedural"):
            try:
                mem[layer] = len(m.items(layer))
            except Exception:
                pass
    except Exception:
        pass
    jobs = 0
    try:
        from rad.jobs import Jobs
        jobs = len(Jobs(home).list())
    except Exception:
        pass
    routines = 0
    try:
        from rad.background import BackgroundRuntime
        routines = len(BackgroundRuntime(home).list_routines())
    except Exception:
        pass
    last_event = None
    path = home.root / "events.jsonl"
    if path.exists():
        try:
            evs = list(EventLog(path).read())
            if evs:
                last_event = {"kind": evs[-1].kind, "at": evs[-1].at, "seq": evs[-1].seq}
        except Exception:
            pass
    authority = {}
    try:
        from rad.authority import Authority
        authority = Authority(home).snapshot()
    except Exception:
        pass
    return {"ok": True, "version": __version__, "schema": st.version(),
            "pending_migrations": [m.name for m in st.pending()],
            "home": str(home.root), "workspace": str(home.workspace()),
            "auto": bool(home.cfg.get("auto")), "chain": chain,
            "authority": {k: authority.get(k) for k in
                          ("profile", "confirmation", "unrestricted", "confirmation_is_automatic")
                          if authority},
            "objectives": {"total": len(objs), "by_status": by_status, "open_tasks": tasks_open},
            "memory": mem, "jobs": jobs, "background_routines": routines,
            "running_objectives": sorted(k for k, t in runs.items() if t.is_alive()),
            "last_event": last_event}


def settings_payload(home) -> Dict[str, Any]:
    from rad.authority import Authority
    cfg = home.cfg
    return {"workspace": str(home.workspace()),
            "free_lock": bool(cfg.get("free_lock")),
            "force_provider": cfg.get("force_provider"),
            "model": cfg.get("model"),
            "tts": cfg.get("tts"),
            "stt": cfg.get("stt"),
            "allow_outside_workspace": bool(cfg.get("allow_outside_workspace")),
            "allow_localhost_web": bool(cfg.get("allow_localhost_web")),
            "auto": bool(cfg.get("auto")),
            "api_port": int(cfg.get("api_port") or 7331),
            "tool_router": cfg.get("tool_router") or "existing",
            "authority": Authority(home).snapshot(),
            "note": "settings cannot raise budgets, change Needle, or bypass Policy.decide"}


def apply_settings(home, b: Dict[str, Any]) -> Tuple[int, Any]:
    hit = sorted(k for k in b if k in FORBIDDEN_SETTINGS_KEYS)
    if hit:
        raise ApiError(400, f"cannot change {hit} via HTTP (budgets/Needle/--auto stay CLI/authority)")
    updates = {k: b[k] for k in SETTINGS_KEYS if k in b}
    if not updates:
        raise ApiError(400, f"no updatable keys; allowed: {list(SETTINGS_KEYS)}")
    home.update(**updates)
    return 200, settings_payload(home)


def apply_authority(home, b: Dict[str, Any]) -> Tuple[int, Any]:
    from rad.authority import Authority, PROFILES
    profile = str(b.get("profile") or "").upper()
    if not profile:
        raise ApiError(400, f"profile required ({', '.join(PROFILES)})")
    try:
        auth = Authority(home)
        auth.set_profile(
            profile,
            confirm_unrestricted=bool(b.get("confirm_unrestricted")),
            capabilities=b.get("capabilities") if isinstance(b.get("capabilities"), dict) else None,
            scopes=b.get("scopes") if isinstance(b.get("scopes"), dict) else None,
            confirmation=b.get("confirmation"),
            actor="api",
        )
    except ValueError as e:
        raise ApiError(409 if "UNRESTRICTED" in str(e) else 400, str(e))
    return 200, auth.snapshot()
