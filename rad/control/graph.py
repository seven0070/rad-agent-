"""TaskGraph — dependency-aware DAG of Tasks with a ready-set scheduler view."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

from rad.control.tasks import Task, TaskStatus

#: terminal states that mean "this dependency will never succeed on its own"
TERMINAL_FAIL = (TaskStatus.CANCELLED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER)


class CycleError(Exception):
    pass


class TaskGraph:
    def __init__(self, tasks: Optional[Iterable[Task]] = None) -> None:
        self.tasks: Dict[str, Task] = {}
        self.order: List[str] = []
        for t in tasks or []:
            self.add(t)

    # ------------------------------------------------------------ build
    def add(self, task: Task) -> Task:
        if task.id in self.tasks:
            raise ValueError(f"duplicate task id {task.id}")
        self.tasks[task.id] = task
        self.order.append(task.id)
        return task

    def add_after(self, task: Task, after: Optional[str]) -> Task:
        """Insert `task` so that it depends on `after` and everything that depended
        on `after` now also depends on `task` (used for repair steps)."""
        if after:
            task.depends_on = list(dict.fromkeys(task.depends_on + [after]))
            for t in self.tasks.values():
                if after in t.depends_on and t.id != task.id and t.status in TaskStatus.OPEN:
                    t.depends_on.append(task.id)
        return self.add(task)

    def validate(self) -> None:
        for t in self.tasks.values():
            for d in t.depends_on:
                if d not in self.tasks:
                    raise ValueError(f"{t.id} depends on unknown task {d}")
        self.topological()  # raises on cycle

    def topological(self) -> List[str]:
        seen: Set[str] = set()
        temp: Set[str] = set()
        out: List[str] = []

        def visit(n: str) -> None:
            if n in seen:
                return
            if n in temp:
                raise CycleError(f"cycle through {n}")
            temp.add(n)
            for d in self.tasks[n].depends_on:
                visit(d)
            temp.discard(n)
            seen.add(n)
            out.append(n)

        for n in self.order:
            visit(n)
        return out

    # ------------------------------------------------------------ query
    def get(self, tid: str) -> Task:
        return self.tasks[tid]

    def _branch_satisfies(self, dep: Task) -> bool:
        """A failed task is neutralised when every declared alternative branch completed."""
        if not dep.alternatives:
            return False
        alts = [self.tasks[a] for a in dep.alternatives if a in self.tasks]
        return bool(alts) and all(a.status == TaskStatus.COMPLETED for a in alts)

    def deps_satisfied(self, t: Task) -> bool:
        for d in t.depends_on:
            dep = self.tasks[d]
            if dep.status == TaskStatus.COMPLETED:
                continue
            if dep.optional and dep.status in (TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.CANCELLED):
                continue
            if dep.status in (TaskStatus.FAILED, TaskStatus.CANCELLED) and self._branch_satisfies(dep):
                continue
            return False
        return True

    def deps_doomed(self, t: Task) -> bool:
        """True if a required dependency can never complete."""
        for d in t.depends_on:
            dep = self.tasks[d]
            if dep.optional:
                continue
            if dep.status in (TaskStatus.CANCELLED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER):
                return True
            if dep.status == TaskStatus.FAILED and not dep.can_retry:
                if self._branch_satisfies(dep):
                    continue
                if dep.alternatives and any(self.tasks[a].status not in TERMINAL_FAIL
                                            for a in dep.alternatives if a in self.tasks):
                    return False        # a live alternative may still rescue the dependents
                return True
        return False

    def ready(self) -> List[Task]:
        """Tasks whose dependencies are satisfied, in topological order."""
        out = []
        for tid in self.topological():
            t = self.tasks[tid]
            if t.status in (TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RETRYING) and self.deps_satisfied(t):
                out.append(t)
        return out

    def failures(self) -> List[Task]:
        return [t for t in self.tasks.values()
                if t.status in (TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.NEEDS_USER)]

    def is_complete(self) -> bool:
        for t in self.tasks.values():
            if t.status == TaskStatus.COMPLETED:
                continue
            if t.optional and t.status in TaskStatus.TERMINAL:
                continue
            if not t.active and t.status in (TaskStatus.PENDING, TaskStatus.CANCELLED):
                continue                     # branch never taken
            return False
        return True

    def is_stuck(self) -> bool:
        """No ready tasks, not complete, nothing running."""
        if self.is_complete():
            return False
        if any(t.status in (TaskStatus.RUNNING, TaskStatus.OBSERVING, TaskStatus.VERIFYING)
               for t in self.tasks.values()):
            return False
        return not self.ready()

    def summary(self) -> Dict[str, int]:
        s: Dict[str, int] = {}
        for t in self.tasks.values():
            s[t.status] = s.get(t.status, 0) + 1
        return s

    # ------------------------------------------------------------ persist
    def to_list(self) -> List[Dict]:
        return [self.tasks[i].to_dict() for i in self.order]

    # ------------------------------------------------------------ FlowCanvas (N2: Langflow/ComfyUI style)
    def to_flow(self) -> Dict[str, List[Dict]]:
        """Export TaskGraph as Langflow/ComfyUI-style flow for FlowCanvas.tsx.

        Nodes carry task status/position; edges derived from depends_on.
        Positions are deterministic grid layout (no LLM).
        """
        nodes: List[Dict] = []
        edges: List[Dict] = []
        topo = self.topological()
        cols = max(1, int(len(topo) ** 0.5) + 1)
        for idx, tid in enumerate(topo):
            t = self.tasks[tid]
            x = (idx % cols) * 220
            y = (idx // cols) * 140
            nodes.append({
                "id": t.id,
                "type": "taskNode",
                "position": {"x": x, "y": y},
                "data": {"label": t.text[:60], "status": t.status, "checks": len(t.checks or []),
                         "depends_on": list(t.depends_on)},
                "style": {"status": t.status},
            })
            for dep in t.depends_on:
                edges.append({"id": f"{dep}->{tid}", "source": dep, "target": tid, "type": "dagEdge"})
        return {"nodes": nodes, "edges": edges}

    @classmethod
    def from_list(cls, items: List[Dict]) -> "TaskGraph":
        return cls(Task.from_dict(d) for d in items)
