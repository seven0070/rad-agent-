"""Append-only event log — the source of truth for `rad trace` / `rad replay`.

One JSONL file per objective. Every state transition, model call, tool call,
observation, verification and recovery decision is an event.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

# canonical event kinds (kept as strings so plugins can add their own)
OBJECTIVE_CREATED = "OBJECTIVE_CREATED"
OBJECTIVE_STATUS = "OBJECTIVE_STATUS"
OBJECTIVE_COMPLETED = "OBJECTIVE_COMPLETED"
OBJECTIVE_FAILED = "OBJECTIVE_FAILED"
PLAN_CREATED = "PLAN_CREATED"
REPLAN = "REPLAN"
TASK_CREATED = "TASK_CREATED"
TASK_STATUS = "TASK_STATUS"
TASK_STARTED = "TASK_STARTED"
TASK_COMPLETED = "TASK_COMPLETED"
TASK_FAILED = "TASK_FAILED"
MODEL_CALLED = "MODEL_CALLED"
TOOL_CALLED = "TOOL_CALLED"
TOOL_RESULT = "TOOL_RESULT"
OBSERVATION_CREATED = "OBSERVATION_CREATED"
VERIFICATION_STARTED = "VERIFICATION_STARTED"
VERIFICATION_RESULT = "VERIFICATION_RESULT"
RECOVERY_STARTED = "RECOVERY_STARTED"
RECOVERY_DECISION = "RECOVERY_DECISION"
BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
CHECKPOINT = "CHECKPOINT"
NEEDS_USER = "NEEDS_USER"
ARTIFACT_CREATED = "ARTIFACT_CREATED"
TRANSCRIPT = "TRANSCRIPT"
REPLAY = "REPLAY"
# --- final architecture additions (sandbox, budgets, models, agents, memory, learning,
#     background runtime, evolution, checkpoints) -------------------------------------
SANDBOX_DENIED = "SANDBOX_DENIED"
SECURITY_DENIED = "SECURITY_DENIED"
BUDGET_WARNING = "BUDGET_WARNING"
MODEL_SELECTED = "MODEL_SELECTED"
MODEL_FALLBACK = "MODEL_FALLBACK"
TOOL_ROUTER_SELECTED = "TOOL_ROUTER_SELECTED"
AGENT_REGISTERED = "AGENT_REGISTERED"
AGENT_STARTED = "AGENT_STARTED"
AGENT_FINISHED = "AGENT_FINISHED"
AGENT_DENIED = "AGENT_DENIED"
AGENT_EVALUATED = "AGENT_EVALUATED"
MEMORY_CREATED = "MEMORY_CREATED"
MEMORY_RETRIEVED = "MEMORY_RETRIEVED"
MEMORY_CONTRADICTION = "MEMORY_CONTRADICTION"
LESSON_PROPOSED = "LESSON_PROPOSED"
LESSON_VALIDATED = "LESSON_VALIDATED"
LESSON_REJECTED = "LESSON_REJECTED"
LESSON_PROMOTED = "LESSON_PROMOTED"
BACKGROUND_TRIGGER = "BACKGROUND_TRIGGER"
BACKGROUND_FIRED = "BACKGROUND_FIRED"
BACKGROUND_COMPLETED = "BACKGROUND_COMPLETED"
EVOLUTION_PROPOSED = "EVOLUTION_PROPOSED"
EVOLUTION_EVALUATED = "EVOLUTION_EVALUATED"
EVOLUTION_PROMOTED = "EVOLUTION_PROMOTED"
EVOLUTION_REJECTED = "EVOLUTION_REJECTED"
EVOLUTION_ROLLED_BACK = "EVOLUTION_ROLLED_BACK"
CHECKPOINT_RESTORED = "CHECKPOINT_RESTORED"
CRASH_DETECTED = "CRASH_DETECTED"
PROVENANCE_QUERY = "PROVENANCE_QUERY"
OBJECTIVE_EXPIRED = "OBJECTIVE_EXPIRED"
VERIFICATION_RECHECK = "VERIFICATION_RECHECK"
PERFORMANCE_SAMPLE = "PERFORMANCE_SAMPLE"
AUTHORITY_PROFILE_CHANGED = "AUTHORITY_PROFILE_CHANGED"
CAPABILITY_CHANGED = "CAPABILITY_CHANGED"
SCOPE_CHANGED = "SCOPE_CHANGED"
CONFIRMATION_POLICY_CHANGED = "CONFIRMATION_POLICY_CHANGED"
BUDGET_POLICY_CHANGED = "BUDGET_POLICY_CHANGED"


@dataclass
class Event:
    kind: str
    at: float = field(default_factory=time.time)
    objective_id: str = ""
    task_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    seq: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, line: str) -> "Event":
        d = json.loads(line)
        return cls(kind=d["kind"], at=d.get("at", 0.0), objective_id=d.get("objective_id", ""),
                   task_id=d.get("task_id", ""), data=d.get("data", {}), seq=d.get("seq", 0))


# ---------------------------------------------------------------------------- event bus
#
# One in-process bus per RAD home plus an append-only *global* stream at
# ~/.rad/events.jsonl. Objectives keep their own per-objective logs (fast replay);
# the global stream is what `rad events` tails and what the background runtime
# subscribes to (event-triggered objectives), so nothing happens invisibly.

_BUSES: Dict[str, "EventBus"] = {}
_BUS_LOCK = threading.Lock()


class EventBus:
    """Fan-out of events to live subscribers (kind prefix or exact match)."""

    def __init__(self) -> None:
        self._subs: List[Tuple[str, Callable[[Event], None]]] = []
        self._lock = threading.Lock()

    def subscribe(self, kind: str, fn: Callable[[Event], None]) -> Callable[[], None]:
        with self._lock:
            entry = (kind or "*", fn)
            self._subs.append(entry)

        def unsubscribe() -> None:
            with self._lock:
                try:
                    self._subs.remove(entry)
                except ValueError:
                    pass
        return unsubscribe

    def publish(self, ev: Event) -> None:
        with self._lock:
            subs = list(self._subs)
        for kind, fn in subs:
            if kind != "*" and not (ev.kind == kind or ev.kind.startswith(kind.rstrip("*"))):
                continue
            try:
                fn(ev)
            except Exception:
                pass


def bus(home: Any) -> EventBus:
    key = str(getattr(home, "root", home))
    with _BUS_LOCK:
        if key not in _BUSES:
            _BUSES[key] = EventBus()
        return _BUSES[key]


def global_path(home: Any) -> Path:
    return Path(getattr(home, "root", home)) / "events.jsonl"


def mirror_enabled(home: Any) -> bool:
    """Keep the global stream unless a home explicitly opts out (config `events.mirror`)."""
    if home is None:
        return False
    try:
        cfg = getattr(home, "cfg", {}) or {}
        return bool((cfg.get("events") or {}).get("mirror", True))
    except Exception:
        return True


def emit_global(home: Any, ev: Event) -> None:
    """Mirror an event into the global stream and publish it on the bus."""
    try:
        p = global_path(home)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(ev.to_json() + "\n")
    except OSError:
        pass
    bus(home).publish(ev)


def read_global(home: Any, n: int = 200, kind: Optional[str] = None) -> List[Event]:
    p = global_path(home)
    if not p.exists():
        return []
    out: List[Event] = []
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = Event.from_json(line)
                except Exception:
                    continue
                if kind and not (ev.kind == kind or ev.kind.startswith(kind)):
                    continue
                out.append(ev)
    except OSError:
        return []
    return out[-n:]


#: one EventLog instance per path per process → sequence numbers stay unique even when
#: the controller, the executor, the lifecycle and the API all log to the same objective.
_LOGS: Dict[str, "EventLog"] = {}
_LOGS_LOCK = threading.Lock()


def event_log(path: Path, home: Any = None, mirror: bool = True) -> "EventLog":
    key = str(Path(path).resolve())
    with _LOGS_LOCK:
        log = _LOGS.get(key)
        if log is None or log.mirror != bool(mirror):
            log = EventLog(path, home=home, mirror=mirror)
            _LOGS[key] = log
        elif home is not None:
            log.home = home
    return log


class EventLog:
    def __init__(self, path: Path, home: Any = None, mirror: bool = True) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.home = home if home is not None else (path.parent.parent.parent
                                                   if len(path.parts) >= 3 else None)
        self.mirror = bool(mirror and mirror_enabled(self.home))
        self._seq = self._last_seq()
        try:
            self._size = self.path.stat().st_size
        except OSError:
            self._size = 0
        self._subscribers: List[Any] = []
        self._lock = threading.RLock()

    def _last_seq(self) -> int:
        if not self.path.exists():
            return 0
        last = 0
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last = json.loads(line).get("seq", last)
        except Exception:
            pass
        return last

    def subscribe(self, fn) -> None:
        self._subscribers.append(fn)

    def _sync(self) -> None:
        """If another process/instance appended since our last write, catch up."""
        try:
            st = self.path.stat()
        except OSError:
            return
        if st.st_size == self._size:
            return
        self._seq = max(self._seq, self._last_seq())
        self._size = st.st_size

    def emit(self, kind: str, objective_id: str = "", task_id: str = "", **data: Any) -> Event:
        with self._lock:
            self._sync()
            self._seq += 1
            ev = Event(kind=kind, objective_id=objective_id, task_id=task_id, data=data, seq=self._seq)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(ev.to_json() + "\n")
            try:
                self._size = self.path.stat().st_size
            except OSError:
                pass
        if self.mirror and self.home is not None:
            emit_global(self.home, ev)
        for fn in self._subscribers:
            try:
                fn(ev)
            except Exception:
                pass
        return ev

    def read(self, kind: Optional[str] = None, task_id: Optional[str] = None) -> Iterator[Event]:
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = Event.from_json(line)
                except Exception:
                    continue
                if kind and ev.kind != kind:
                    continue
                if task_id and ev.task_id != task_id:
                    continue
                yield ev

    def all(self) -> List[Event]:
        return list(self.read())

    def count(self, kind: Optional[str] = None) -> int:
        return sum(1 for _ in self.read(kind=kind))
