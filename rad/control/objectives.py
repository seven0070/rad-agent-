"""Objective — the top-level goal, its success criteria, budget and persisted state.

Layout on disk (human-readable, like the rest of ~/.rad):

    ~/.rad/objectives/<id>/
        objective.json      goal, criteria, status, budget, usage
        tasks.json          task graph (checkpoint)
        events.jsonl        append-only event log
        observations/       one JSON per action observation
        artifacts.json      artifact registry for this objective
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome, _write_json


class ObjectiveStatus:
    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    PAUSED = "paused"
    NEEDS_USER = "needs_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

    ACTIVE = {"pending", "planning", "running", "paused", "needs_user"}


@dataclass
class Budget:
    """0 on any field = unlimited for that kind."""
    tool_calls: int = 60
    model_calls: int = 80
    retries: int = 6
    seconds: int = 1800
    money_usd: float = 0.0          # 0 = no paid spend allowed beyond free-lock policy
    tokens: int = 0                 # prompt+completion tokens
    agents: int = 0                 # sub-agent runs

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Usage:
    tool_calls: int = 0
    model_calls: int = 0
    retries: int = 0
    seconds: float = 0.0
    money_usd: float = 0.0
    tokens: int = 0
    agents: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Objective:
    id: str
    goal: str
    success_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    priority: str = "normal"
    status: str = ObjectiveStatus.PENDING
    budget: Budget = field(default_factory=Budget)
    usage: Usage = field(default_factory=Usage)
    deadline: Optional[float] = None
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    finished: Optional[float] = None
    result: str = ""
    failure: str = ""
    verification: Dict[str, Any] = field(default_factory=dict)
    auto: bool = False
    tags: List[str] = field(default_factory=list)
    result_summary: str = ""        # short human-facing outcome (set by the controller)
    budget_status: Dict[str, Any] = field(default_factory=dict)
    plan_version: int = 0            # bumped on every plan/replan; tasks record the version

    @classmethod
    def new(cls, goal: str, **kw: Any) -> "Objective":
        return cls(id="obj_" + uuid.uuid4().hex[:8], goal=goal.strip(), **kw)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Objective":
        d = dict(d)
        d["budget"] = Budget(**d.get("budget", {}))
        d["usage"] = Usage(**d.get("usage", {}))
        return cls(**d)

    def set_status(self, s: str) -> None:
        self.status = s
        self.updated = time.time()
        if s in (ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED, ObjectiveStatus.CANCELLED,
                 ObjectiveStatus.EXPIRED):
            self.finished = time.time()

    def over_budget(self) -> Optional[str]:
        b, u = self.budget, self.usage
        if b.tool_calls and u.tool_calls >= b.tool_calls:
            return f"tool-call budget {b.tool_calls} exhausted"
        if b.model_calls and u.model_calls >= b.model_calls:
            return f"model-call budget {b.model_calls} exhausted"
        if b.retries and u.retries >= b.retries:
            return f"retry budget {b.retries} exhausted"
        if b.seconds and u.seconds >= b.seconds:
            return f"time budget {b.seconds}s exhausted"
        if b.money_usd and u.money_usd >= b.money_usd:
            return f"money budget ${b.money_usd} exhausted"
        if b.tokens and u.tokens >= b.tokens:
            return f"token budget {b.tokens} exhausted"
        if b.agents and u.agents >= b.agents:
            return f"agent budget {b.agents} exhausted"
        if self.deadline and time.time() > self.deadline:
            return "deadline passed"
        return None


class ObjectiveStore:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.root = home.root / "objectives"
        self.root.mkdir(parents=True, exist_ok=True)

    def dir(self, oid: str) -> Path:
        return self.root / oid

    def save(self, o: Objective) -> None:
        o.updated = time.time()
        _write_json(self.dir(o.id) / "objective.json", o.to_dict())

    def load(self, oid: str) -> Optional[Objective]:
        p = self.dir(oid) / "objective.json"
        if not p.exists():
            return None
        try:
            return Objective.from_dict(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            return None

    def resolve(self, ref: str) -> Optional[Objective]:
        """Accept a full id, a unique prefix, or 'last'."""
        if ref == "last":
            items = self.list()
            return items[0] if items else None
        o = self.load(ref)
        if o:
            return o
        hits = [d.name for d in self.root.iterdir() if d.is_dir() and d.name.startswith(ref)]
        if len(hits) == 1:
            return self.load(hits[0])
        return None

    def list(self, active_only: bool = False) -> List[Objective]:
        out: List[Objective] = []
        for d in self.root.iterdir():
            if not d.is_dir():
                continue
            o = self.load(d.name)
            if o and (not active_only or o.status in ObjectiveStatus.ACTIVE):
                out.append(o)
        out.sort(key=lambda o: -o.created)
        return out

    def save_tasks(self, oid: str, items: List[Dict[str, Any]]) -> None:
        _write_json(self.dir(oid) / "tasks.json", items)

    def load_tasks(self, oid: str) -> List[Dict[str, Any]]:
        p = self.dir(oid) / "tasks.json"
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []

    def events_path(self, oid: str) -> Path:
        return self.dir(oid) / "events.jsonl"

    def delete(self, oid: str) -> bool:
        import shutil
        d = self.dir(oid)
        if not d.exists():
            return False
        shutil.rmtree(d)
        return True
