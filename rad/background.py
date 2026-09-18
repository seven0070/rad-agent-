"""Background runtime — scheduled, periodic, event-triggered and monitoring work.

Everything RAD does while you are away is a **trigger**: a thing that fires an
*objective* through the same control plane, permission system and verification
architecture as interactive work. There is no second execution path.

    kind          fires when…
    ────────────────────────────────────────────────────────────────────────────
    schedule      a wall-clock time / ISO date / "tomorrow 9am" arrives (once)
    interval      every N minutes (maintenance, digests)
    file          a file in the workspace changes (hash comparison)
    web           a public page's content changes (with an optional goal template)
    api           an HTTP endpoint's status/body matches (or stops matching)
    event         an event appears on RAD's event bus (e.g. OBJECTIVE_FAILED)
    objective     another objective reaches a terminal state

Each trigger has a budget-aware goal template, a last-run record, and a state
file so restarts never double-fire. The runtime can run as a detached daemon
(`rad jobs serve`), be ticked once (`rad jobs tick`), or embedded in tests.

Legacy `rad remind` / `rad watch` jobs are migrated into triggers (migration v4).
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.control import events as E
from rad.control.events import bus, read_global
from rad.home import RadHome, _read_json, _write_json
from rad.ui import col

KINDS = ("schedule", "interval", "file", "web", "api", "event", "objective", "maintenance")
STATE_TERMINAL = ("completed", "failed", "cancelled", "expired")


@dataclass
class Trigger:
    id: str
    kind: str
    goal: str = ""                      # objective goal built from this trigger
    at: float = 0.0                     # schedule: fire at (epoch)
    every_min: int = 0                  # interval
    path: str = ""                      # file
    url: str = ""                       # web / api
    expect_status: int = 0              # api: alert when status != this
    expect_contains: str = ""           # api/web: alert when absent (or present for `invert`)
    invert: bool = False
    pattern: str = ""                   # event: event kind prefix
    objective_ref: str = ""             # objective: watch this objective id
    on_status: List[str] = field(default_factory=lambda: ["failed", "needs_user"])
    enabled: bool = True
    auto: bool = True                   # objectives it fires are autonomous (policy ASK→ALLOW)
    budget: Dict[str, int] = field(default_factory=lambda: {"tool_calls": 20, "model_calls": 20,
                                                            "seconds": 600, "retries": 2})
    created: float = field(default_factory=time.time)
    last_run: float = 0.0
    last_status: str = ""
    runs: int = 0
    note: str = ""
    tags: List[str] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    maintenance: str = ""               # maintenance: sleep | integrity | snapshot | expire | prune

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Trigger":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class BackgroundRuntime:
    def __init__(self, home: RadHome, controller_factory: Optional[Callable[[RadHome], Any]] = None,
                 quiet: bool = False) -> None:
        self.home = home
        self.dir = home.root / "background"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "triggers.json"
        self.log_path = self.dir / "runs.jsonl"
        self._controller_factory = controller_factory
        self.quiet = quiet
        self._unsubs: List[Callable[[], None]] = []

    # ------------------------------------------------------------------ storage
    def triggers(self, enabled_only: bool = False) -> List[Trigger]:
        items = [Trigger.from_dict(d) for d in (_read_json(self.path, []) or [])]
        if enabled_only:
            items = [t for t in items if t.enabled]
        return items

    def save(self, items: List[Trigger]) -> None:
        _write_json(self.path, [t.to_dict() for t in items])

    def get(self, tid: str) -> Optional[Trigger]:
        return next((t for t in self.triggers() if t.id == tid), None)

    def _log(self, rec: Dict[str, Any]) -> None:
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        except OSError:
            pass

    # ------------------------------------------------------------------ CRUD
    def add(self, kind: str, goal: str = "", **kw: Any) -> Trigger:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        t = Trigger(id="bg_" + uuid.uuid4().hex[:6], kind=kind, goal=goal, **kw)
        if kind == "interval" and not t.every_min:
            t.every_min = 30
        items = self.triggers()
        items.append(t)
        self.save(items)
        self._event(E.BACKGROUND_TRIGGER, trigger=t.id, trigger_kind=kind, action="created", goal=goal[:120])
        return t

    def remove(self, tid: str) -> bool:
        items = self.triggers()
        keep = [t for t in items if t.id != tid]
        if len(keep) == len(items):
            return False
        self.save(keep)
        self._event(E.BACKGROUND_TRIGGER, trigger=tid, action="removed")
        return True

    def enable(self, tid: str, enabled: bool = True) -> Optional[Trigger]:
        items = self.triggers()
        for t in items:
            if t.id == tid:
                t.enabled = enabled
                self.save(items)
                self._event(E.BACKGROUND_TRIGGER, trigger=tid, action="enabled" if enabled else "disabled")
                return t
        return None

    def _event(self, kind: str, **data: Any) -> None:
        try:
            from rad.control.events import Event, emit_global
            emit_global(self.home, Event(kind=kind, data=data))
        except Exception:
            pass

    # ------------------------------------------------------------------ due detection
    def due(self, now: Optional[float] = None) -> List[Trigger]:
        now = now or time.time()
        out: List[Trigger] = []
        for t in self.triggers(enabled_only=True):
            if t.kind == "schedule":
                if t.at and not t.state.get("fired") and t.at <= now:
                    out.append(t)
            elif t.kind == "interval":
                period = max(1, int(t.every_min)) * 60
                if t.at and t.at > now:
                    continue
                if now - (t.last_run or t.created) >= period:
                    out.append(t)
            elif t.kind == "file":
                if self._file_changed(t):
                    out.append(t)
            elif t.kind == "web":
                if self._should_fire_web(t, now):
                    out.append(t)
            elif t.kind == "api":
                if self._should_fire_api(t, now):
                    out.append(t)
            elif t.kind == "objective":
                if self._objective_terminal(t):
                    out.append(t)
            # event + maintenance triggers are handled by run/event-driven paths
        return out

    # ---- detectors (each returns True/False or records state and returns False)
    def _file_changed(self, t: Trigger) -> bool:
        p = Path(t.path).expanduser()
        if not p.is_absolute():
            p = self.home.workspace() / p
        try:
            if not p.exists():
                return False
            digest = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        except OSError:
            return False
        key = f"hash:{p}"
        old = t.state.get(key)
        if old is None:
            t.state[key] = digest            # baseline: never fire on first observation
            self._update(t)
            return False
        if old != digest:
            t.state[key] = digest
            self._update(t)
            return True
        return False

    def _should_fire_web(self, t: Trigger, now: float) -> bool:
        every = max(1, int(t.every_min or 30)) * 60
        if now - (t.state.get("checked", 0) or 0) < every:
            return False
        t.state["checked"] = now
        self._update(t)
        try:
            from rad.tools import fetch_public_page
            text, err = fetch_public_page(t.url, max_chars=200_000)
        except Exception as e:
            t.note = f"fetch error: {e}"
            return False
        if err:
            t.note = f"fetch failed: {err[:120]}"
            return False
        digest = hashlib.sha256((text or "").encode()).hexdigest()[:16]
        old = t.state.get("digest")
        t.state["digest"] = digest
        self._update(t)
        return bool(old and old != digest)

    def _should_fire_api(self, t: Trigger, now: float) -> bool:
        every = max(1, int(t.every_min or 15)) * 60
        if now - (t.state.get("checked", 0) or 0) < every:
            return False
        t.state["checked"] = now
        self._update(t)
        try:
            from rad.tools import html_to_text, http_get
            code, raw, ctype = http_get(t.url, timeout=20.0, max_bytes=1_000_000)
        except Exception as e:
            t.state["last_error"] = str(e)[:200]
            t.note = f"api unreachable: {e}"
            self._update(t)
            return True                       # unreachable endpoint is exactly what monitoring is for
        body = raw.decode("utf-8", "replace")
        text = html_to_text(body) if "html" in (ctype or "").lower() else body
        bad_status = bool(t.expect_status) and code != t.expect_status
        missing = bool(t.expect_contains) and (str(t.expect_contains).lower() not in text.lower())
        cond = (missing if not t.invert else not missing) or bad_status
        t.state["last_status"] = code
        self._update(t)
        return cond

    def _objective_terminal(self, t: Trigger) -> bool:
        if not t.objective_ref:
            return False
        from rad.control.objectives import ObjectiveStore
        obj = ObjectiveStore(self.home).resolve(t.objective_ref)
        if not obj or obj.status not in STATE_TERMINAL:
            return False
        if t.state.get("fired_for") == f"{obj.id}:{obj.status}":
            return False
        if t.on_status and obj.status not in t.on_status:
            return False
        t.state["fired_for"] = f"{obj.id}:{obj.status}"
        self._update(t)
        return True

    def _update(self, t: Trigger) -> None:
        items = self.triggers()
        for i, x in enumerate(items):
            if x.id == t.id:
                items[i] = t
                break
        else:
            items.append(t)
        self.save(items)

    # ------------------------------------------------------------------ firing
    def goal_for(self, t: Trigger) -> str:
        if t.goal:
            return t.goal
        if t.kind == "file":
            return f"Review what changed in {Path(t.path).name} and report anything important."
        if t.kind == "web":
            return (f"The page {t.url} changed. Fetch it, summarise what changed and why it matters, "
                    f"and save the summary to a file in the workspace.")
        if t.kind == "api":
            return (f"The endpoint {t.url} is not in the expected state "
                    f"({t.note or 'unexpected response'}). Investigate and report.")
        if t.kind == "objective":
            return f"Follow up on objective {t.objective_ref} (it reached a terminal state)."
        if t.kind == "event":
            return f"React to event {t.pattern}."
        return "Maintenance run."

    def fire(self, t: Trigger, run: bool = True) -> Dict[str, Any]:
        """Create (and optionally run) the objective for a trigger. Never bypasses the
        control plane: this is the same Controller the CLI uses."""
        started = time.time()
        if t.kind == "maintenance":
            result = self.maintenance(t)
            self._finish_trigger(t, result.get("status", "completed"), started)
            return result
        from rad.control.objectives import Budget
        from rad.control.controller import Controller
        ctl = (self._controller_factory or (lambda h: Controller(h, quiet=self.quiet)))(self.home)
        budget = Budget(**{k: v for k, v in (t.budget or {}).items()
                           if k in Budget.__dataclass_fields__}) if t.budget else None
        obj = ctl.create(self.goal_for(t), budget=budget, auto=t.auto,
                         tags=["background", t.kind, t.id])
        self._event(E.BACKGROUND_FIRED, trigger=t.id, trigger_kind=t.kind, objective=obj.id,
                    goal=obj.goal[:160])
        if not run:
            self._finish_trigger(t, "created", started, objective=obj.id)
            return {"status": "created", "objective": obj.id}
        obj = ctl.run(obj)
        result = {"status": obj.status, "objective": obj.id,
                  "verification": ((obj.verification or {}).get("objective") or {}).get("status", ""),
                  "result": (obj.result or "")[:2000]}
        self._finish_trigger(t, obj.status, started, objective=obj.id)
        return result

    def _finish_trigger(self, t: Trigger, status: str, started: float, objective: str = "") -> None:
        t.last_run = started
        t.last_status = status
        t.runs += 1
        if t.kind == "schedule":
            t.state["fired"] = True
        self._update(t)
        rec = {"at": started, "trigger": t.id, "trigger_kind": t.kind, "status": status,
               "objective": objective, "goal": t.goal[:200]}
        self._log(rec)
        self._event(E.BACKGROUND_COMPLETED, trigger=t.id, status=status, objective=objective)

    # ------------------------------------------------------------------ maintenance
    def maintenance(self, t: Optional[Trigger] = None) -> Dict[str, Any]:
        """Housekeeping that must also be observable: memory decay, integrity, snapshots,
        expiring deadlines and pruning old runs."""
        what = (t.maintenance if t else "") or "all"
        out: Dict[str, Any] = {"status": "completed", "task": what}
        if what in ("all", "sleep", "decay"):
            try:
                from rad.memory import Memory
                archived, pruned = Memory(self.home).decay_and_archive()
                out["memory"] = {"archived": archived, "pruned": pruned}
            except Exception as e:
                out["memory"] = f"error: {e}"
        if what in ("all", "expire"):
            try:
                from rad.control.lifecycle import Lifecycle
                expired = Lifecycle(self.home).expire_due()
                out["expired"] = [o.id for o in expired]
            except Exception as e:
                out["expired"] = f"error: {e}"
        if what in ("all", "integrity"):
            try:
                from rad.storage import Storage
                findings = Storage(self.home).integrity(repair=False)
                out["integrity"] = {"findings": len(findings)}
            except Exception as e:
                out["integrity"] = f"error: {e}"
        if what in ("all", "snapshot"):
            try:
                if t and t.tags and "snapshot" not in t.tags:
                    out["snapshot"] = "skipped (tag not set)"
                else:
                    from rad.storage import Storage
                    out["snapshot"] = str(Storage(self.home).snapshot("background"))
            except Exception as e:
                out["snapshot"] = f"error: {e}"
        if what in ("all", "prune"):
            out["pruned_runs"] = self.prune_log()
        self._event("BACKGROUND_MAINTENANCE", task=what, result=out if isinstance(out, dict) else {})
        return out

    def prune_log(self, keep: int = 2000) -> int:
        try:
            lines = self.log_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0
        if len(lines) <= keep:
            return 0
        removed = len(lines) - keep
        self.log_path.write_text("\n".join(lines[-keep:]) + "\n", encoding="utf-8")
        return removed

    # ------------------------------------------------------------------ event triggers
    def subscribe_events(self, on_event: Optional[Callable[[Trigger], None]] = None) -> Callable[[], None]:
        """Live event → trigger fan-in. Subscribes once per runtime instance."""
        def handler(ev: E.Event) -> None:
            for t in self.triggers(enabled_only=True):
                if t.kind != "event" or not t.pattern:
                    continue
                if not ev.kind.startswith(t.pattern):
                    continue
                if (on_event is not None):
                    on_event(t)
                else:
                    self.fire(t)
        unsub = bus(self.home).subscribe("*", handler)
        self._unsubs.append(unsub)
        return unsub

    def close(self) -> None:
        for u in self._unsubs:
            try:
                u()
            except Exception:
                pass
        self._unsubs = []

    # ------------------------------------------------------------------ daemon
    def tick(self, run: bool = True) -> List[Dict[str, Any]]:
        """Fire everything that is due right now (one pass)."""
        out = []
        for t in self.due():
            try:
                out.append({"trigger": t.id, "kind": t.kind, **self.fire(t, run=run)})
            except Exception as e:
                self._finish_trigger(t, f"error: {type(e).__name__}", time.time())
                out.append({"trigger": t.id, "kind": t.kind, "status": "error", "error": str(e)[:200]})
        return out

    def serve(self, interval: int = 20, max_ticks: Optional[int] = None,
              should_stop: Optional[Callable[[], bool]] = None) -> int:
        """Blocking loop: fire due triggers, react to events, run maintenance."""
        self.subscribe_events()
        ticks = 0
        if not self.quiet:
            print(col.dim(f"  background runtime started ({len(self.triggers(enabled_only=True))} "
                          f"enabled trigger(s); interval {interval}s)"))
        try:
            while True:
                if should_stop is not None and should_stop():
                    break
                for item in self.tick():
                    if not self.quiet:
                        print(col.cyan(f"  ⚡ {item.get('kind')} {item.get('trigger')} → "
                                       f"{item.get('status')}"))
                ticks += 1
                if max_ticks is not None and ticks >= max_ticks:
                    break
                time.sleep(max(1, interval))
        except KeyboardInterrupt:
            pass
        finally:
            self.close()
        return ticks

    # ------------------------------------------------------------------ views
    def show(self, n: int = 20) -> str:
        items = self.triggers()
        if not items:
            return "  no background triggers — `rad jobs add interval 60 'summarise new files'`"
        lines = []
        now = time.time()
        for t in items[:n]:
            state = "on " if t.enabled else "off"
            when = ""
            if t.kind == "schedule" and t.at:
                when = time.strftime("%Y-%m-%d %H:%M", time.localtime(t.at))
            elif t.kind == "interval":
                nxt = max(0, (t.last_run or t.created) + t.every_min * 60 - now)
                when = f"every {t.every_min}m (next in {int(nxt / 60)}m)"
            elif t.kind in ("web", "api"):
                when = t.url[:60]
            elif t.kind == "file":
                when = t.path
            elif t.kind == "event":
                when = f"on {t.pattern}"
            elif t.kind == "objective":
                when = f"when {t.objective_ref} ∈ {','.join(t.on_status)}"
            detail = t.goal[:50] if t.goal else self.goal_for(t)[:50]
            lines.append(f"  {col.cyan(t.id)} {state} {t.kind:<10} {when:<34} {col.dim(detail)}")
        return "\n".join(lines)

    def history(self, n: int = 20) -> List[Dict[str, Any]]:
        try:
            lines = self.log_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        out = []
        for ln in reversed(lines):
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
            if len(out) >= n:
                break
        return out

    def recent_events(self, n: int = 20, pattern: str = "") -> List[Dict[str, Any]]:
        return [{"kind": e.kind, "at": e.at, "data": e.data}
                for e in read_global(self.home, n=n, kind=pattern or None)]


# ------------------------------------------------------------------ legacy job migration

def migrate_legacy_jobs(home: RadHome) -> int:
    """Turn old `rad remind` / `rad watch` jobs into triggers (idempotent)."""
    try:
        jobs = json.loads(home.jobs_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    rt = BackgroundRuntime(home)
    existing = {t.id for t in rt.triggers()}
    legacy_ids = {f"legacy-{j.get('id')}" for j in jobs if isinstance(j, dict)}
    if legacy_ids & existing:
        return 0
    n = 0
    for j in jobs:
        if not isinstance(j, dict) or j.get("done"):
            continue
        kind = "schedule" if j.get("kind") == "note" else ("web" if j.get("kind") == "watch" else "")
        if not kind:
            continue
        t = Trigger(id=f"legacy-{j.get('id')}", kind=kind, goal=str(j.get("task", "")),
                    at=float(j.get("at", 0) or 0), url=str(j.get("url", "")),
                    every_min=int(j.get("every_min", 0) or 0), auto=True,
                    tags=["legacy"], note="migrated from rad remind/watch")
        items = rt.triggers()
        items.append(t)
        rt.save(items)
        n += 1
    return n
