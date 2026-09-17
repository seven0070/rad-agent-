"""Task — the unit of work in the control plane, with an explicit state machine.

    PENDING → READY → RUNNING → OBSERVING → VERIFYING → COMPLETED
                                   │            │
                                   ▼            ▼
                                FAILED ───► RETRYING ──► READY
                                   │
                          BLOCKED / NEEDS_USER / CANCELLED

No task silently disappears; every transition is recorded on the task and
in the objective's event log.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


class TaskStatus:
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    OBSERVING = "OBSERVING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    BLOCKED = "BLOCKED"
    NEEDS_USER = "NEEDS_USER"
    CANCELLED = "CANCELLED"

    TERMINAL = {"COMPLETED", "CANCELLED", "BLOCKED", "NEEDS_USER"}
    OPEN = {"PENDING", "READY", "RETRYING"}


ALLOWED = {
    TaskStatus.PENDING: {TaskStatus.READY, TaskStatus.CANCELLED, TaskStatus.BLOCKED},
    TaskStatus.READY: {TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.BLOCKED},
    TaskStatus.RUNNING: {TaskStatus.OBSERVING, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.NEEDS_USER},
    TaskStatus.OBSERVING: {TaskStatus.VERIFYING, TaskStatus.FAILED},
    TaskStatus.VERIFYING: {TaskStatus.COMPLETED, TaskStatus.FAILED},
    TaskStatus.FAILED: {TaskStatus.RETRYING, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER, TaskStatus.CANCELLED},
    TaskStatus.RETRYING: {TaskStatus.READY, TaskStatus.CANCELLED, TaskStatus.BLOCKED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.BLOCKED: {TaskStatus.READY, TaskStatus.CANCELLED},      # human unblocks
    TaskStatus.NEEDS_USER: {TaskStatus.READY, TaskStatus.CANCELLED},   # human answers
    TaskStatus.CANCELLED: set(),
}


class IllegalTransition(Exception):
    pass


@dataclass
class Check:
    """A machine-checkable success condition for a task.

    kinds (evaluated by the Verifier, never by the LLM):
      file_exists   {path}
      file_contains {path, text}
      file_min_bytes{path, n}
      shell_ok      {command}          exit code 0
      shell_output  {command, contains}
      json_valid    {path}
      reply_matches {pattern}          regex against the task's final reply
      llm_judge     {question}         model-graded — records verdict as UNVERIFIED-BY-MACHINE
    """
    kind: str
    args: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Check":
        return cls(kind=d["kind"], args=d.get("args", {}), description=d.get("description", ""))


@dataclass
class Task:
    id: str
    objective_id: str
    text: str
    depends_on: List[str] = field(default_factory=list)
    checks: List[Check] = field(default_factory=list)
    status: str = TaskStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    optional: bool = False
    created: float = field(default_factory=time.time)
    started: Optional[float] = None
    finished: Optional[float] = None
    reply: str = ""
    note: str = ""
    failure_class: str = ""
    verification: Dict[str, Any] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)   # observation ids
    artifacts: List[str] = field(default_factory=list)      # artifact ids
    history: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def new(cls, objective_id: str, text: str, **kw: Any) -> "Task":
        return cls(id="t_" + uuid.uuid4().hex[:8], objective_id=objective_id, text=text, **kw)

    def transition(self, to: str, note: str = "") -> None:
        if to not in ALLOWED.get(self.status, set()):
            raise IllegalTransition(f"{self.id}: {self.status} → {to} not allowed")
        self.history.append({"from": self.status, "to": to, "at": time.time(), "note": note[:300]})
        self.status = to
        if note:
            self.note = note[:500]
        if to == TaskStatus.RUNNING:
            self.started = time.time()
            self.attempts += 1
        if to in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER):
            self.finished = time.time()

    @property
    def can_retry(self) -> bool:
        return self.attempts < self.max_attempts

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["checks"] = [c.to_dict() for c in self.checks]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Task":
        d = dict(d)
        d["checks"] = [Check.from_dict(c) for c in d.get("checks", [])]
        return cls(**d)
