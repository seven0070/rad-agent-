"""Local HTTP API — the control plane, memory and doctor over loopback JSON.

    rad serve [--port 7331] [--host 127.0.0.1]

Security model
* Binds 127.0.0.1 by default. Binding elsewhere requires `--host` *and* `--i-know-this-exposes-rad`.
* Every request needs `Authorization: Bearer <token>`; the token is generated on first start,
  stored 0600 at ~/.rad/api.token, and printed once. No token → 401, always.
* Only JSON in/out; request bodies capped at 256 KB; no file paths are accepted from clients —
  everything goes through the same Controller / policy gates as the CLI. Objectives created
  via the API run in a background thread with `auto=True` **only if** the config allows it;
  otherwise they are created but left PENDING for the CLI to run interactively (because HTTP
  cannot answer confirmation prompts).
* Every request is appended to ~/.rad/logs/api.jsonl (method, path, status, ms, no bodies).

Endpoints (all under /v1)
    GET  /health                       → {ok, version, schema}
    GET  /doctor?fix=0                 → findings (fix ignored unless config allow_api_fix)
    GET  /objectives?active=1          → list
    POST /objectives {goal, criteria?, constraints?, budget?, run?} → objective (202 if started)
    GET  /objectives/{id}              → objective + tasks
    POST /objectives/{id}/resume|pause|cancel|run   (run = plan + start a PENDING objective)
    GET  /objectives/{id}/events?kind=&since_seq=
    GET  /objectives/{id}/trace        → tasks with verification + attempts
    GET  /objectives/{id}/why          → provenance report
    GET  /objectives/{id}/artifacts    → artifact registry for the objective
    GET  /objectives/{id}/artifact-content?ref= → redacted text preview of a REGISTERED
                                                   artifact (workspace/home only; no arbitrary paths)
    GET  /objectives/{id}/plan         → plan summary (version, source, tasks, checks)
    GET  /objectives/{id}/recovery     → recovery decisions + failure classes
    GET  /objectives/{id}/observations → recorded observations (redacted output)
    GET  /objectives/{id}/live         → live execution view (current task, budget, events)
    GET  /usage                        → cross-objective Usage rollup (persisted data only)
    GET  /memory?layer=&n=             → list memories by layer
    GET  /memory/recall?q=&k=          → memories
    POST /memory {text, layer?}        → remember (USER_PROVIDED)
    GET  /user                         → user model
    GET  /policy                       → effective policy
    GET  /audit?n=                     → permission decisions
    GET  /lab/history · GET /evolve/candidates
    POST /chat {text}                  → one Jerry/brain turn (tools gated as ASK→declined, since no TTY)
    GET  /authority                    → profile, capabilities, scopes, confirmation, budgets
    PUT  /authority                    → set profile (UNRESTRICTED needs confirm_unrestricted)
    GET  /settings                     → safe config subset (no secrets)
    PUT  /settings                     → limited keys only; cannot raise budgets or bypass policy
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from rad import __version__
from rad.home import RadHome

MAX_BODY = 256 * 1024


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except (ValueError, TypeError):
        return False


class ApiError(Exception):
    def __init__(self, status: int, msg: str) -> None:
        super().__init__(msg)
        self.status = status


def token_for(home: RadHome, rotate: bool = False) -> str:
    p = home.root / "api.token"
    if p.exists() and not rotate:
        return p.read_text(encoding="utf-8").strip()
    tok = secrets.token_urlsafe(32)
    p.write_text(tok, encoding="utf-8")
    os.chmod(p, 0o600)
    return tok


class Api:
    """Transport-independent handlers: (method, path, query, body) -> (status, payload).
    Kept separate from the HTTP layer so tests can call them directly."""

    def __init__(self, home: RadHome, controller_factory: Optional[Callable[[RadHome], Any]] = None,
                 session_factory: Optional[Callable[..., Any]] = None) -> None:
        self.home = home
        self._ctl_factory = controller_factory
        self._session_factory = session_factory
        self._runs: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def _ctl(self):
        if self._ctl_factory:
            return self._ctl_factory(self.home)
        from rad.control.controller import Controller
        return Controller(self.home, quiet=True)

    # ---- dispatch -------------------------------------------------------------------------
    def handle(self, method: str, path: str, query: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, Any]:
        parts = [p for p in path.split("/") if p]
        if not parts or parts[0] != "v1":
            raise ApiError(404, "unknown path (use /v1/...)")
        parts = parts[1:]
        try:
            return self._route(method, parts, query, body)
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(500, f"{type(e).__name__}: {str(e)[:200]}")

    def _route(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]) -> Tuple[int, Any]:
        from rad.control.objectives import ObjectiveStatus
        if p == ["health"] and m == "GET":
            from rad.storage import Storage
            st = Storage(self.home); st.pending()
            return 200, {"ok": True, "version": __version__, "schema": st.version(),
                         "running": sorted(k for k, t in self._runs.items() if t.is_alive())}
        if p == ["doctor"] and m == "GET":
            from rad.doctor import Doctor
            fix = q.get("fix") == "1" and bool(self.home.cfg.get("allow_api_fix"))
            fs = Doctor(self.home, fix=fix, probe_network=q.get("probe") == "1").run()
            return 200, {"findings": [f.__dict__ for f in fs], "fix_applied": fix}
        if p == ["objectives"] and m == "GET":
            store = self._ctl().store
            objs = store.list(active_only=q.get("active") == "1")
            rows = []
            for o in objs:
                try:
                    rows.append(self._obj_summary(o, store.load_tasks(o.id)))
                except Exception:
                    rows.append(self._obj_summary(o))
            return 200, {"objectives": rows}
        if p == ["objectives"] and m == "POST":
            return self._create_objective(b)
        if len(p) >= 2 and p[0] == "objectives":
            ctl = self._ctl()
            obj = ctl.store.resolve(p[1])
            if not obj:
                raise ApiError(404, f"no objective {p[1]}")
            if len(p) == 2 and m == "GET":
                d = obj.to_dict(); d["tasks"] = ctl.store.load_tasks(obj.id)
                return 200, d
            if len(p) == 3 and m == "POST" and p[2] in ("resume", "pause", "cancel", "run"):
                if p[2] == "pause":
                    o = ctl.pause(obj.id)
                elif p[2] == "cancel":
                    o = ctl.cancel(obj.id)
                else:
                    if not self._may_run():
                        raise ApiError(409, "config auto=false: HTTP cannot answer confirmation prompts; run `rad objective run` in a terminal or set auto")
                    if p[2] == "run":
                        # Controller.run plans a PENDING objective if it has no plan yet;
                        # resume assumes a plan exists. Same background-thread semantics.
                        self._background(obj.id, lambda: ctl.run(obj))
                        return 202, {"id": obj.id, "status": "starting"}
                    self._background(obj.id, lambda: ctl.resume(obj.id))
                    return 202, {"id": obj.id, "status": "resuming"}
                return 200, self._obj_summary(o or obj)
            if len(p) == 3 and m == "GET" and p[2] == "events":
                from rad.control.events import EventLog
                since = int(q.get("since_seq", 0) or 0)
                evs = [e.__dict__ for e in EventLog(ctl.store.events_path(obj.id)).read(kind=q.get("kind") or None)
                       if e.seq > since]
                return 200, {"events": evs[-int(q.get("n", 500) or 500):]}
            if len(p) == 3 and m == "GET" and p[2] == "trace":
                return 200, {"objective": self._obj_summary(obj), "tasks": ctl.store.load_tasks(obj.id),
                             "verification": obj.verification}
            if len(p) == 3 and m == "GET" and p[2] == "why":
                from rad.control.provenance import Provenance
                pv = Provenance(ctl.store.dir(obj.id))
                claim = q.get("q", "")
                if not claim:
                    raise ApiError(400, "q=<artifact path | claim text> required")
                art = pv.artifact(claim)
                return 200, {"artifact": art} if art else pv.why(claim)
            if len(p) == 3 and m == "GET" and p[2] == "artifacts":
                from rad.control.observer import Observer
                reg = Observer(ctl.store.dir(obj.id)).artifacts()
                rows = sorted(reg.values(), key=lambda a: (-a.get("version", 0), a.get("at", 0)))
                return 200, {"objective_id": obj.id, "count": len(rows), "artifacts": rows}
            if len(p) == 3 and m == "GET" and p[2] == "artifact-content":
                return self._artifact_content(ctl, obj, q.get("ref", ""))
            if len(p) == 3 and m == "GET" and p[2] == "plan":
                from rad.control.events import EventLog
                log = EventLog(ctl.store.events_path(obj.id))
                plans = [e for e in log.read(kind="PLAN_CREATED")]
                replans = [e for e in log.read(kind="REPLAN")]
                tasks = ctl.store.load_tasks(obj.id)
                return 200, {"objective_id": obj.id,
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
            if len(p) == 3 and m == "GET" and p[2] == "recovery":
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
                return 200, {"objective_id": obj.id, "decisions": decisions, "failed_tasks": failed,
                             "retries_used": obj.usage.retries, "retry_budget": obj.budget.retries}
            if len(p) == 3 and m == "GET" and p[2] == "observations":
                from rad.control.observer import Observer
                from rad.policy import redact
                obs = Observer(ctl.store.dir(obj.id))
                rows = []
                for p in sorted(obs.dir.glob("obs_*.json")):
                    o = obs.load(p.stem)
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
                return 200, {"objective_id": obj.id, "count": len(rows),
                             "observations": rows[-int(q.get("n", 400) or 400):]}
            if len(p) == 3 and m == "GET" and p[2] == "live":
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
                return 200, {"objective": self._obj_summary(obj),
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
            raise ApiError(404, "unknown objective route")
        if p == ["memory", "recall"] and m == "GET":
            from rad.memory import Memory
            k = max(1, min(20, int(q.get("k", 5) or 5)))
            return 200, {"memories": [self._mem(e) for e in Memory(self.home).recall(q.get("q", ""), k=k)]}
        if p == ["memory"] and m == "POST":
            from rad.memory import Memory
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            layer = b.get("layer", "semantic")
            if layer not in ("episodic", "semantic", "procedural"):
                raise ApiError(400, "layer must be episodic|semantic|procedural")
            e = Memory(self.home).add(layer, text, origin="USER_PROVIDED", source="api")
            return 201, self._mem(e)
        if p == ["memory"] and m == "GET":
            from rad.memory import Memory
            mem = Memory(self.home)
            layer = q.get("layer") or ""
            layers = (layer,) if layer in ("working", "episodic", "semantic", "procedural") \
                else ("working", "episodic", "semantic", "procedural")
            n = max(1, min(200, int(q.get("n", 50) or 50)))
            out: Dict[str, Any] = {}
            for l in layers:
                try:
                    items = list(mem.scan(l))
                except Exception:
                    items = []
                out[l] = [self._mem(e) for e in items[-n:]]
            return 200, {"memories": out}
        if p == ["usage"] and m == "GET":
            from rad.control.objectives import REMAINING_QUOTA_NOTE
            store = self._ctl().store
            r = store.usage_rollup()
            return 200, {**r.to_dict(), "note": REMAINING_QUOTA_NOTE}
        if p == ["user"] and m == "GET":
            from rad.usermodel import UserModel
            return 200, UserModel(self.home).data()
        if p == ["policy"] and m == "GET":
            from rad.policy import Policy
            pol = Policy(self.home)
            from rad.authority import Authority
            from rad.policy import BUILTIN_DEFAULTS
            return 200, {"defaults": {c: pol.default_for(c) for c in BUILTIN_DEFAULTS},
                         "rules": [r.to_dict() for r in pol.rules], "web_allow": pol._data.get("web_allow", []),
                         "authority": Authority(self.home).snapshot()}
        if p == ["authority"] and m == "GET":
            from rad.authority import Authority
            return 200, Authority(self.home).snapshot()
        if p == ["authority"] and m == "PUT":
            return self._set_authority(b)
        if p == ["settings"] and m == "GET":
            return 200, self._settings()
        if p == ["settings"] and m == "PUT":
            return self._set_settings(b)
        if p == ["audit"] and m == "GET":
            from rad.policy import Policy
            return 200, {"audit": Policy(self.home).audit_tail(int(q.get("n", 50) or 50), effect=q.get("effect") or None)}
        if p == ["lab", "history"] and m == "GET":
            from rad.lab import Lab
            return 200, {"runs": [{k: v for k, v in r.items() if k != "results"} for r in Lab(self.home).history(int(q.get("n", 20) or 20))]}
        if p == ["evolve", "candidates"] and m == "GET":
            from rad.evolution import Evolution
            return 200, {"candidates": [c.to_dict() for c in Evolution(self.home).candidates(int(q.get("n", 20) or 20))]}
        if p == ["status"] and m == "GET":
            return 200, self._status()
        if p == ["tasks"] and m == "GET":
            store = self._ctl().store
            status = q.get("status")
            rows: List[Dict[str, Any]] = []
            for o in store.list(active_only=False):
                if q.get("objective") and o.id != q["objective"] and q["objective"] != "last":
                    continue
                for t in store.load_tasks(o.id):
                    if status and str(t.get("status")) != status:
                        continue
                    rows.append({**t, "objective_id": o.id, "goal": o.goal[:80]})
            return 200, {"tasks": rows[-int(q.get("n", 200) or 200):]}
        if p == ["agents"] and m == "GET":
            from rad.agents import AgentLifecycle, AgentRegistry
            reg = AgentRegistry(self.home)
            lc = AgentLifecycle(self.home)
            return 200, {"agents": [a.to_dict() for a in reg.all().values()],
                         "states": {s["id"]: s.get("state") for s in lc.all()},
                         "runs": reg.runs(n=int(q.get("n", 20) or 20))}
        if p == ["events"] and m == "GET":
            from rad.control.events import read_global
            evs = read_global(self.home, n=int(q.get("n", 200) or 200), kind=q.get("kind") or None)
            rows = [e.__dict__ for e in evs]
            oid = q.get("objective") or ""
            if oid:
                rows = [r for r in rows if r.get("objective_id") == oid]
            return 200, {"events": rows, "n": len(rows), "stream": "~/.rad/events.jsonl"}
        if p == ["world"] and m == "GET":
            from rad.world import WorldModel
            w = WorldModel(self.home)
            term = q.get("q", "")
            if term:
                return 200, {"matches": w.query(term, include_history=q.get("history") == "1")}
            d = w.data()
            return 200, {"entities": d.get("entities", {}) if isinstance(d.get("entities"), dict)
                         else d.get("entities", []),
                         "relations": w.current_relations(d),
                         "disputes": w.disputes(),
                         "counts": {"entities": len(d.get("entities") or {}),
                                    "relations": len(d.get("relations") or [])}}
        if p == ["tools"] and m == "GET":
            from rad.agents import cap_for_tool
            from rad.policy import Policy
            from rad.tools import TOOLS
            pol = Policy(self.home)
            tools = []
            for t in TOOLS:
                fn = t.get("function", t)
                cap = cap_for_tool(fn.get("name", ""))
                tools.append({"name": fn.get("name"), "capability": cap,
                              "policy": pol.default_for(cap),
                              "description": (fn.get("description") or "")[:160]})
            return 200, {"tools": tools}
        if p == ["benchmarks"] and m == "GET":
            from rad import lab_banks
            from rad.battery import Benchmark
            from rad.evaluation import ModelEvaluator
            from rad.lab import Lab
            out: Dict[str, Any] = {"banks": lab_banks.counts()}
            try:
                out["lab"] = [{k: v for k, v in r.items() if k != "results"} for r in Lab(self.home).history(10)]
            except Exception as e:
                out["lab"] = {"error": str(e)[:80]}
            try:
                out["battery"] = [{k: v for k, v in r.items() if k != "tasks"}
                                  for r in Benchmark(self.home).history()[-10:]]
            except Exception as e:
                out["battery"] = {"error": str(e)[:80]}
            ev = ModelEvaluator(self.home)
            latest = ev.latest()
            out["evaluation"] = ({k: v for k, v in latest.items() if k != "tasks"} if latest else None)
            try:
                from rad.longhorizon import LongHorizonBenchmark
                lh = LongHorizonBenchmark(self.home).latest()
                out["long_horizon"] = lh or None
            except Exception as e:
                out["long_horizon"] = {"error": str(e)[:80]}
            return 200, out
        if p == ["chat"] and m == "POST":
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            from rad.jerry import Jerry
            j = Jerry(self.home, session_factory=self._session_factory)
            # ASK → declined when confirmation is interactive (no TTY). AUTONOMOUS /
            # UNRESTRICTED confirmation=never is applied inside Policy.decide, not here.
            reply = j.chat(text, auto=False)
            return 200, {"reply": reply, "via": "jerry"}
        raise ApiError(404, "unknown route")

    # ---- helpers --------------------------------------------------------------------------
    def _status(self) -> Dict[str, Any]:
        """One object: health, brain, objectives, tasks, memory, agents, jobs, schema."""
        from rad.control.events import EventLog
        from rad.storage import Storage
        st = Storage(self.home)
        st.pending()
        ctl = self._ctl()
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
            chain = [f"{e.spec.name}:{e.model}" for e in RouterState(self.home).build_chain()]
        except Exception:
            pass
        mem: Dict[str, int] = {}
        try:
            from rad.memory import Memory
            m = Memory(self.home)
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
            jobs = len(Jobs(self.home).list())
        except Exception:
            pass
        routines = 0
        try:
            from rad.background import BackgroundRuntime
            routines = len(BackgroundRuntime(self.home).list_routines())
        except Exception:
            pass
        last_event = None
        path = self.home.root / "events.jsonl"
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
            authority = Authority(self.home).snapshot()
        except Exception:
            pass
        return {"ok": True, "version": __version__, "schema": st.version(),
                "pending_migrations": [m.name for m in st.pending()],
                "home": str(self.home.root), "workspace": str(self.home.workspace()),
                "auto": bool(self.home.cfg.get("auto")), "chain": chain,
                "authority": {k: authority.get(k) for k in
                              ("profile", "confirmation", "unrestricted", "confirmation_is_automatic")
                              if authority},
                "objectives": {"total": len(objs), "by_status": by_status, "open_tasks": tasks_open},
                "memory": mem, "jobs": jobs, "background_routines": routines,
                "running_objectives": sorted(k for k, t in self._runs.items() if t.is_alive()),
                "last_event": last_event}

    def _may_run(self) -> bool:
        if bool(self.home.cfg.get("auto")):
            return True
        try:
            from rad.authority import confirmation_is_automatic
            return confirmation_is_automatic(self.home)
        except Exception:
            return False

    _SETTINGS_KEYS = ("workspace", "free_lock", "force_provider", "model", "tts", "stt",
                      "allow_outside_workspace", "allow_localhost_web")

    def _settings(self) -> Dict[str, Any]:
        from rad.authority import Authority
        cfg = self.home.cfg
        return {"workspace": str(self.home.workspace()),
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
                "authority": Authority(self.home).snapshot(),
                "note": "settings cannot raise budgets, change Needle, or bypass Policy.decide"}

    def _set_settings(self, b: Dict[str, Any]) -> Tuple[int, Any]:
        forbidden = {"max_plan_tasks", "max_tool_rounds", "tool_calls", "budget",
                     "tool_router", "auto"}
        hit = sorted(k for k in b if k in forbidden)
        if hit:
            raise ApiError(400, f"cannot change {hit} via HTTP (budgets/Needle/--auto stay CLI/authority)")
        updates = {k: b[k] for k in self._SETTINGS_KEYS if k in b}
        if not updates:
            raise ApiError(400, f"no updatable keys; allowed: {list(self._SETTINGS_KEYS)}")
        self.home.update(**updates)
        return 200, self._settings()

    def _set_authority(self, b: Dict[str, Any]) -> Tuple[int, Any]:
        from rad.authority import Authority, PROFILES
        profile = str(b.get("profile") or "").upper()
        if not profile:
            raise ApiError(400, f"profile required ({', '.join(PROFILES)})")
        try:
            auth = Authority(self.home)
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

    def _background(self, key: str, fn: Callable[[], Any]) -> None:
        with self._lock:
            t = self._runs.get(key)
            if t and t.is_alive():
                raise ApiError(409, f"{key} already running")

            def wrap():
                try:
                    fn()
                except Exception:
                    traceback.print_exc()
            th = threading.Thread(target=wrap, name=f"api-{key}", daemon=True)
            self._runs[key] = th
            th.start()

    def _create_objective(self, b: Dict[str, Any]) -> Tuple[int, Any]:
        from rad.control.objectives import Budget
        goal = str(b.get("goal", "")).strip()
        if not goal or len(goal) > 4000:
            raise ApiError(400, "goal required (≤4000 chars)")
        crit = [str(x)[:300] for x in (b.get("criteria") or [])][:20]
        cons = [str(x)[:300] for x in (b.get("constraints") or [])][:20]
        bud = b.get("budget") or {}
        if not isinstance(bud, dict) or any(k not in Budget.__dataclass_fields__ for k in bud):
            raise ApiError(400, f"budget keys must be in {sorted(Budget.__dataclass_fields__)}")
        ctl = self._ctl()
        run = bool(b.get("run", True))
        auto = self._may_run()
        obj = ctl.create(goal, success_criteria=crit, constraints=cons, budget=Budget(**bud) if bud else None, auto=auto)
        if run and auto:
            self._background(obj.id, lambda: ctl.run(obj))
            return 202, {**self._obj_summary(obj), "started": True}
        return 201, {**self._obj_summary(obj), "started": False,
                     "note": "created PENDING: run it with `rad objective run` (config auto=false)" if run else "created PENDING"}

    def _artifact_content(self, ctl, obj, ref: str) -> Tuple[int, Any]:
        """Redacted text preview of a REGISTERED artifact of this objective.

        The client supplies an artifact ref (id / path / filename), never a raw path: the
        only way in is through the objective's artifact registry. Even then the file must
        live inside the workspace or the RAD home, must be text, and is capped + redacted.
        """
        from rad.control.observer import Observer
        from rad.policy import redact
        from pathlib import Path as _P
        ref = (ref or "").strip()
        if not ref:
            raise ApiError(400, "ref=<artifact id|path|filename> required")
        reg = Observer(ctl.store.dir(obj.id)).artifacts()
        art = reg.get(ref)
        if not art:
            hits = [a for a in reg.values() if a["location"] == ref or _P(a["location"]).name == ref]
            hits.sort(key=lambda a: -a.get("version", 1))
            art = hits[0] if hits else None
        if not art:
            raise ApiError(404, f"not an artifact of {obj.id}")
        loc = _P(art["location"])
        try:
            resolved = loc.expanduser().resolve()
        except Exception:
            raise ApiError(400, "unresolvable artifact location")
        roots = []
        try:
            roots.append(self.home.workspace().resolve())
        except Exception:
            pass
        try:
            roots.append(_P(self.home.root).resolve())
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

    @staticmethod
    def _obj_summary(o, tasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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

    @staticmethod
    def _mem(e) -> Dict[str, Any]:
        return {"id": e.id, "layer": e.layer, "text": e.text, "origin": e.origin, "confidence": e.confidence,
                "verification": e.verification, "strength": e.strength}


# ---------------------------------------------------------------- HTTP layer

def make_server(home: RadHome, host: str = "127.0.0.1", port: int = 7331, api: Optional[Api] = None,
                token: Optional[str] = None) -> ThreadingHTTPServer:
    api = api or Api(home)
    token = token or token_for(home)
    log_path = home.root / "logs" / "api.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    class H(BaseHTTPRequestHandler):
        server_version = f"rad/{__version__}"

        def log_message(self, *a):        # quiet; we write our own structured log
            pass

        def _send(self, status: int, payload: Any) -> None:
            data = json.dumps(payload, ensure_ascii=False, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def _authed(self) -> bool:
            h = self.headers.get("Authorization", "")
            return h.startswith("Bearer ") and secrets.compare_digest(h[7:].strip(), token)

        def _do(self, method: str) -> None:
            t0 = time.time()
            status = 500
            try:
                if not self._authed():
                    status = 401
                    self._send(401, {"error": "missing or invalid bearer token"})
                    return
                u = urlparse(self.path)
                q = {k: v[-1] for k, v in parse_qs(u.query).items()}
                body: Dict[str, Any] = {}
                if method == "POST":
                    n = int(self.headers.get("Content-Length", 0) or 0)
                    if n > MAX_BODY:
                        status = 413; self._send(413, {"error": "body too large"}); return
                    raw = self.rfile.read(n) if n else b""
                    if raw:
                        try:
                            body = json.loads(raw)
                        except Exception:
                            status = 400; self._send(400, {"error": "invalid JSON body"}); return
                        if not isinstance(body, dict):
                            status = 400; self._send(400, {"error": "JSON body must be an object"}); return
                try:
                    status, payload = api.handle(method, u.path, q, body)
                except ApiError as e:
                    status, payload = e.status, {"error": str(e)}
                self._send(status, payload)
            finally:
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"at": time.time(), "method": method, "path": self.path.split("?")[0],
                                            "status": status, "ms": int((time.time() - t0) * 1000),
                                            "peer": self.client_address[0]}) + "\n")
                except OSError:
                    pass

        def do_GET(self):
            self._do("GET")

        def do_POST(self):
            self._do("POST")

    return ThreadingHTTPServer((host, port), H)
