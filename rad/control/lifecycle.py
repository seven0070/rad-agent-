"""Lifecycle — the objective's state machine, in one place.

    create → plan → run ⇄ pause ⇄ resume → complete
                       ↘ needs_user → (resume) → run
                       ↘ fail / cancel / expire

Everything that changes an objective's status goes through here, so the legal
transitions, the events and the checkpoint are always consistent. The Controller
drives execution; the Lifecycle owns the bookkeeping (and is usable on its own by
the CLI, the API and the background runtime).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rad.control import events as E
from rad.control.checkpoints import CheckpointManager
from rad.control.events import EventLog
from rad.control.graph import TaskGraph
from rad.control.objectives import Budget, Objective, ObjectiveStatus, ObjectiveStore
from rad.control.tasks import TaskStatus
from rad.home import RadHome

#: which statuses an objective may move to from a given status
TRANSITIONS: Dict[str, set] = {
    ObjectiveStatus.PENDING: {ObjectiveStatus.PLANNING, ObjectiveStatus.RUNNING, ObjectiveStatus.CANCELLED,
                              ObjectiveStatus.EXPIRED, ObjectiveStatus.FAILED},
    ObjectiveStatus.PLANNING: {ObjectiveStatus.RUNNING, ObjectiveStatus.FAILED, ObjectiveStatus.CANCELLED,
                               ObjectiveStatus.NEEDS_USER, ObjectiveStatus.PAUSED, ObjectiveStatus.EXPIRED},
    ObjectiveStatus.RUNNING: {ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED, ObjectiveStatus.PAUSED,
                              ObjectiveStatus.NEEDS_USER, ObjectiveStatus.CANCELLED, ObjectiveStatus.EXPIRED},
    ObjectiveStatus.PAUSED: {ObjectiveStatus.RUNNING, ObjectiveStatus.CANCELLED, ObjectiveStatus.EXPIRED,
                             ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER},
    ObjectiveStatus.NEEDS_USER: {ObjectiveStatus.RUNNING, ObjectiveStatus.CANCELLED, ObjectiveStatus.FAILED,
                                 ObjectiveStatus.PAUSED, ObjectiveStatus.EXPIRED},
    ObjectiveStatus.COMPLETED: {ObjectiveStatus.RUNNING},      # explicit re-run / re-verify
    ObjectiveStatus.FAILED: {ObjectiveStatus.RUNNING},          # retry
    ObjectiveStatus.CANCELLED: {ObjectiveStatus.RUNNING},
    ObjectiveStatus.EXPIRED: {ObjectiveStatus.RUNNING},
}

TERMINAL = (ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED, ObjectiveStatus.CANCELLED,
            ObjectiveStatus.EXPIRED)


class IllegalObjectiveTransition(Exception):
    pass


@dataclass
class Transition:
    frm: str
    to: str
    at: float
    note: str = ""


class Lifecycle:
    def __init__(self, home: RadHome, store: Optional[ObjectiveStore] = None,
                 checkpoints: Optional[CheckpointManager] = None) -> None:
        self.home = home
        self.store = store or ObjectiveStore(home)
        self.checkpoints = checkpoints or CheckpointManager(home, self.store)

    # ------------------------------------------------------------------ helpers
    def log(self, oid: str) -> EventLog:
        return EventLog(self.store.events_path(oid), home=self.home)

    def checkpoint(self, obj: Objective, graph: Optional[TaskGraph] = None, note: str = "") -> Dict[str, Any]:
        return self.checkpoints.save(obj, graph or TaskGraph(), note)

    def _move(self, obj: Objective, to: str, note: str = "", *, force: bool = False,
              graph: Optional[TaskGraph] = None) -> Objective:
        if not force and obj.status != to and to not in TRANSITIONS.get(obj.status, set()):
            raise IllegalObjectiveTransition(f"{obj.id}: {obj.status} → {to} not allowed")
        frm = obj.status
        obj.set_status(to)
        if graph is not None:
            self.checkpoint(obj, graph, note)
        else:
            self.store.save(obj)
        self.log(obj.id).emit(E.OBJECTIVE_STATUS, obj.id, status=to, **{"frm": frm, "note": note[:300]})
        return obj

    # ------------------------------------------------------------------ operations
    def create(self, goal: str, success_criteria: Optional[List[str]] = None,
               constraints: Optional[List[str]] = None, budget: Optional[Budget] = None,
               auto: bool = False, priority: str = "normal", deadline: Optional[float] = None,
               tags: Optional[List[str]] = None) -> Objective:
        obj = Objective.new(goal, success_criteria=success_criteria or [], constraints=constraints or [],
                            budget=budget or Budget(), auto=auto, priority=priority, deadline=deadline,
                            tags=list(tags or []))
        self.store.save(obj)
        self.log(obj.id).emit(E.OBJECTIVE_CREATED, obj.id, goal=goal, criteria=obj.success_criteria,
                              budget=obj.budget.to_dict(), priority=priority, tags=list(tags or []))
        return obj

    def start(self, obj: Objective, graph: Optional[TaskGraph] = None) -> Objective:
        if obj.status in TERMINAL:
            self.retry(obj)
        return self._move(obj, ObjectiveStatus.RUNNING, "started", graph=graph)

    def planning(self, obj: Objective) -> Objective:
        return self._move(obj, ObjectiveStatus.PLANNING, "planning")

    def pause(self, obj: Objective, note: str = "paused by user", graph: Optional[TaskGraph] = None) -> Objective:
        if obj.status not in ObjectiveStatus.ACTIVE:
            return obj
        return self._move(obj, ObjectiveStatus.PAUSED, note, graph=graph)

    def resume(self, obj: Objective, note: str = "resumed", graph: Optional[TaskGraph] = None) -> Objective:
        """Re-open human-blocked work and put the objective back into RUNNING."""
        if graph is not None:
            for t in graph.tasks.values():
                if t.status in (TaskStatus.NEEDS_USER, TaskStatus.BLOCKED):
                    t.transition(TaskStatus.READY, "user resumed")
        return self._move(obj, ObjectiveStatus.RUNNING, note, graph=graph, force=True)

    def cancel(self, obj: Objective, note: str = "cancelled by user",
               graph: Optional[TaskGraph] = None) -> Objective:
        g = graph if graph is not None else TaskGraph.from_list(self.store.load_tasks(obj.id))
        for t in g.tasks.values():
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
                try:
                    t.transition(TaskStatus.CANCELLED, note)
                except Exception:
                    t.status = TaskStatus.CANCELLED
        return self._move(obj, ObjectiveStatus.CANCELLED, note, graph=g, force=True)

    def retry(self, obj: Objective, note: str = "retry requested",
              graph: Optional[TaskGraph] = None) -> Objective:
        """Re-open failed/blocked tasks and make failed objectives runnable again."""
        g = graph if graph is not None else TaskGraph.from_list(self.store.load_tasks(obj.id))
        reopened = 0
        for t in g.tasks.values():
            if t.status in (TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER):
                t.attempts = max(0, t.attempts - 1)          # give it back a life
                t.active = True
                t.transition(TaskStatus.READY, note)
                reopened += 1
        obj.failure = ""
        return self._move(obj, ObjectiveStatus.RUNNING, f"{note} ({reopened} task(s) re-opened)",
                          graph=g, force=True)

    def complete(self, obj: Objective, result: str = "", graph: Optional[TaskGraph] = None) -> Objective:
        obj.result = result or obj.result
        obj.failure = ""
        return self._move(obj, ObjectiveStatus.COMPLETED, "objective completed", graph=graph, force=True)

    def fail(self, obj: Objective, reason: str, graph: Optional[TaskGraph] = None) -> Objective:
        obj.failure = reason[:1000]
        return self._move(obj, ObjectiveStatus.FAILED, reason, graph=graph, force=True)

    def needs_user(self, obj: Objective, reason: str, graph: Optional[TaskGraph] = None) -> Objective:
        obj.failure = reason[:1000]
        return self._move(obj, ObjectiveStatus.NEEDS_USER, reason, graph=graph, force=True)

    def expire(self, obj: Objective, reason: str = "deadline passed") -> Objective:
        obj.failure = reason
        self._move(obj, ObjectiveStatus.EXPIRED, reason, force=True)
        self.log(obj.id).emit(E.OBJECTIVE_EXPIRED, obj.id, reason=reason)
        return obj

    def expire_due(self, now: Optional[float] = None) -> List[Objective]:
        """Expire objectives whose deadline has passed (used by the background runtime)."""
        now = now or time.time()
        out: List[Objective] = []
        for obj in self.store.list(active_only=True):
            if obj.deadline and now > obj.deadline and obj.status in (ObjectiveStatus.PENDING,
                                                                     ObjectiveStatus.PAUSED,
                                                                     ObjectiveStatus.NEEDS_USER):
                out.append(self.expire(obj))
        return out

    def delete(self, ref: str) -> bool:
        obj = self.store.resolve(ref)
        if not obj:
            return False
        if obj.status in (ObjectiveStatus.RUNNING, ObjectiveStatus.PLANNING):
            self.cancel(obj)
        return self.store.delete(obj.id)

    # ------------------------------------------------------------------ views
    def history(self, obj: Objective) -> List[Dict[str, Any]]:
        out = []
        for ev in self.log(obj.id).read(kind=E.OBJECTIVE_STATUS):
            out.append({"at": ev.at, "from": ev.data.get("frm", ""), "to": ev.data.get("status", ""),
                        "note": ev.data.get("note", "")})
        return out

    def summary(self) -> Dict[str, Any]:
        items = self.store.list()
        by: Dict[str, int] = {}
        for o in items:
            by[o.status] = by.get(o.status, 0) + 1
        interrupted = [i.to_dict() for i in self.checkpoints.interrupted()]
        return {"objectives": len(items), "by_status": by, "interrupted": interrupted}
