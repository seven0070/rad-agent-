"""Append-only event log — the source of truth for `rad trace` / `rad replay`.

One JSONL file per objective. Every state transition, model call, tool call,
observation, verification and recovery decision is an event.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

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


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = self._last_seq()
        self._subscribers: List[Any] = []

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

    def emit(self, kind: str, objective_id: str = "", task_id: str = "", **data: Any) -> Event:
        self._seq += 1
        ev = Event(kind=kind, objective_id=objective_id, task_id=task_id, data=data, seq=self._seq)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(ev.to_json() + "\n")
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
