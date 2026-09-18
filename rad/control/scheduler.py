"""Scheduler — decides, each turn, which tasks may run now.

Dependency-aware: a task is runnable when every prerequisite is COMPLETED, or the
prerequisite failed but it was optional, or a declared *alternative branch*
satisfied it.

Branch semantics (explicit, so nothing silently disappears):

    depends_on   hard prerequisites (AND)
    optional     may fail without blocking dependents
    alternatives task ids that can satisfy this task's dependents when it fails
    on_failure   diagnostic/repair branch to activate when this task fails for good
    priority     high | normal | low  (higher priority runs first within a batch)

When a task fails permanently the scheduler *activates* its alternatives and its
failure branch. When a prerequisite can never be satisfied, dependents are moved
to BLOCKED with a reason instead of being forgotten.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from rad.control.graph import TaskGraph
from rad.control.tasks import OPEN_STATES, TERMINAL_STATES, Task, TaskStatus

PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}


@dataclass
class Batch:
    tasks: List[Task]
    note: str = ""
    activated: List[str] = None            # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.activated is None:
            self.activated = []

    @property
    def empty(self) -> bool:
        return not self.tasks


class Scheduler:
    def __init__(self, parallel: int = 1, max_tasks: Optional[int] = None) -> None:
        self.parallel = max(1, int(parallel or 1))
        self.max_tasks = max_tasks
        self.dispatched = 0

    # ------------------------------------------------------------------ branches
    def activate_branches(self, graph: TaskGraph) -> List[Task]:
        """Wake alternative/failure branches of permanently-failed tasks."""
        activated: List[Task] = []
        for t in list(graph.tasks.values()):
            if t.status not in (TaskStatus.FAILED, TaskStatus.CANCELLED):
                continue
            if t.can_retry and t.status == TaskStatus.FAILED:
                continue                                    # still retryable — not permanent yet
            for bid in list(t.alternatives) + list(t.on_failure):
                b = graph.tasks.get(bid)
                if b is None or b.status not in (TaskStatus.PENDING,):
                    continue
                b.active = True
                b.transition(TaskStatus.READY, f"activated as branch of {t.id}")
                activated.append(b)
        return activated

    def block_doomed(self, graph: TaskGraph) -> List[Task]:
        """Move tasks whose prerequisites can never be met to BLOCKED (with a reason)."""
        blocked: List[Task] = []
        for tid in graph.order:
            t = graph.tasks[tid]
            if t.status not in OPEN_STATES or not t.active:
                continue
            if graph.deps_doomed(t):
                bad = [d for d in t.depends_on if graph.tasks[d].status in TERMINAL_STATES
                       and graph.tasks[d].status != TaskStatus.COMPLETED]
                t.transition(TaskStatus.BLOCKED,
                             "unmet prerequisite: " + ", ".join(f"{d}({graph.tasks[d].status})" for d in bad))
                blocked.append(t)
        return blocked

    # ------------------------------------------------------------------ dispatch
    def runnable(self, graph: TaskGraph) -> List[Task]:
        self.activate_branches(graph)
        ready = [t for t in graph.ready() if t.active]
        ready.sort(key=lambda t: (PRIORITY_RANK.get(t.priority, 1), graph.order.index(t.id)))
        return ready

    def next_batch(self, graph: TaskGraph) -> Batch:
        ready = self.runnable(graph)
        if not ready:
            return Batch([], "no runnable tasks")
        batch = ready[:self.parallel]
        if self.max_tasks is not None:
            left = self.max_tasks - self.dispatched
            if left <= 0:
                return Batch([], "task limit reached")
            batch = batch[:left]
        self.dispatched += len(batch)
        note = "parallel" if len(batch) > 1 else ""
        return Batch(batch, note)

    # ------------------------------------------------------------------ state
    def exhausted(self) -> bool:
        return self.max_tasks is not None and self.dispatched >= self.max_tasks

    def live(self, graph: TaskGraph) -> bool:
        return any(t.status in (TaskStatus.RUNNING, TaskStatus.OBSERVING, TaskStatus.VERIFYING)
                   for t in graph.tasks.values())

    def expect_more(self, graph: TaskGraph) -> bool:
        """Is there still work that *could* run (retryable failures, inactive branches)?"""
        if graph.is_complete():
            return False
        if self.runnable(graph):
            return True
        for t in graph.tasks.values():
            if t.status == TaskStatus.FAILED and t.can_retry:
                return True
            if t.status == TaskStatus.RETRYING:
                return True
        return False

    # ------------------------------------------------------------------ reporting
    @staticmethod
    def summary(graph: TaskGraph) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for t in graph.tasks.values():
            counts[t.status] = counts.get(t.status, 0) + 1
        return {"tasks": len(graph.tasks), "by_status": counts,
                "complete": graph.is_complete(), "stuck": graph.is_stuck(),
                "ready": [t.id for t in graph.ready()]}

    @staticmethod
    def critical_path(graph: TaskGraph) -> List[str]:
        """Longest dependency chain (informational: shows what the objective hinges on)."""
        best: List[str] = []
        memo: Dict[str, List[str]] = {}

        def walk(tid: str) -> List[str]:
            if tid in memo:
                return memo[tid]
            t = graph.tasks.get(tid)
            if t is None:
                return []
            memo[tid] = [tid]                              # cycle guard
            deps = [walk(d) for d in t.depends_on if d in graph.tasks]
            deps.sort(key=len)
            memo[tid] = (deps[-1] if deps else []) + [tid]
            return memo[tid]

        for tid in graph.order:
            chain = walk(tid)
            if len(chain) > len(best):
                best = chain
        return best

    def explain(self, graph: TaskGraph) -> str:
        lines = []
        for tid in graph.order:
            t = graph.tasks[tid]
            flag = "" if t.active else " (branch, inactive)"
            deps = f" ← {','.join(t.depends_on)}" if t.depends_on else ""
            lines.append(f"  {t.status:<10} {t.id} {t.text[:60]}{deps}{flag}")
        return "\n".join(lines)
