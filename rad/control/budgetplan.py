"""Budget-aware planning helpers (Gen2 theme 3) plus leftover-tool reserve (E1).

Plans should fit remaining ``Budget.tool_calls`` rather than emitting a fat
task graph that thrashes until exhaustion (RW-059 Case B; RW-065/066 tools
12/12). This is a planner/controller bias, not a cap raise.

Cost model: each task is estimated at ``TOOLS_PER_TASK`` tool calls (act +
verify/repair headroom). Default ``Budget.tool_calls`` stays 60;
``max_plan_tasks`` stays 16.

Small graphs (``SMALL_PLAN_MAX`` tasks or fewer) may still exceed the
remaining budget — that is the F-21 leftover-work contract (partial progress
then ``needs_user``, or already-satisfied ``VERIFIED``). Fat graphs are
retried/selected (LLM) or compacted (fallback only). LLM graphs are never
silently compacted so machine checks and leftover-task cancellation stay.

Gen3 theme 3 slice E1 reuses the same remaining-tools account at *drive*
time: reserve one tool per later independent unattempted READY task so a
stuck in-flight task yields before leftover hits 0.
"""
from __future__ import annotations

from typing import Any, List, Optional, Tuple

from rad.control.graph import TaskGraph
from rad.control.tasks import Check, Task

TOOLS_PER_TASK = 2
SMALL_PLAN_MAX = 3  # 1-3 task graphs may exceed remaining tools (F-21)


def task_is_yielded(task: Task) -> bool:
    """Parked at a task boundary so leftover tools can reach later READY work."""
    return bool((task.verification or {}).get("yielded"))


def independent_unattempted_ready(graph: TaskGraph, current: Optional[Task] = None) -> List[Task]:
    """READY/PENDING/RETRYING tasks that do not wait on ``current`` and have not run yet.

    ``graph.ready()`` already requires deps satisfied, so an in-flight ``current``
    is excluded when later tasks depend on it. E1 does not rewrite ``depends_on``
    (that is candidate E2).
    """
    cur_id = current.id if current is not None else None
    out: List[Task] = []
    for t in graph.ready():
        if cur_id is not None and t.id == cur_id:
            continue
        if not t.active:
            continue
        if int(t.attempts or 0) > 0:
            continue
        if task_is_yielded(t):
            continue
        out.append(t)
    return out


def leftover_tool_reserve(graph: TaskGraph, current: Optional[Task],
                          remaining: Optional[int]) -> int:
    """How many tool calls to hold back for later independent READY work.

    One tool per unattempted independent READY task, never more than remaining.
    Unlimited budgets (``remaining is None``) reserve nothing — no yield.
    """
    if remaining is None:
        return 0
    rem = max(0, int(remaining))
    n = len(independent_unattempted_ready(graph, current))
    if n <= 0 or rem <= 0:
        return 0
    return min(n, rem)


def remaining_tool_calls(obj: Any) -> Optional[int]:
    """Remaining tool-call budget, or None when unlimited (limit 0)."""
    budget = getattr(obj, "budget", None)
    usage = getattr(obj, "usage", None)
    lim = int(getattr(budget, "tool_calls", 0) or 0) if budget is not None else 0
    if not lim:
        return None
    used = float(getattr(usage, "tool_calls", 0) or 0) if usage is not None else 0.0
    return max(0, int(lim - used))


def estimate_plan_tools(n_tasks: int) -> int:
    return max(0, int(n_tasks)) * TOOLS_PER_TASK


def max_fit_tasks(remaining: Optional[int]) -> Optional[int]:
    """How many tasks fit remaining tools at TOOLS_PER_TASK each.

    Always at least 1 when a finite budget is set, so a 1-tool run can still
    attempt work (F-21). None means unlimited.
    """
    if remaining is None:
        return None
    return max(1, int(remaining) // TOOLS_PER_TASK)


def is_over_budget(n_tasks: int, remaining: Optional[int]) -> bool:
    cap = max_fit_tasks(remaining)
    if cap is None:
        return False
    return int(n_tasks) > cap


def is_fat(n_tasks: int, remaining: Optional[int]) -> bool:
    """True when retry/compact should fire.

    Over-budget *and* larger than a small plan. A 3-task graph with
    remaining=1 is leftover work (F-21), not a fat plan.
    """
    return is_over_budget(n_tasks, remaining) and int(n_tasks) > SMALL_PLAN_MAX


def budget_prompt_line(remaining: Optional[int]) -> str:
    if remaining is None:
        return ("unspecified — prefer the smallest covering plan (typically 2-6 "
                "tasks; never more than 16).")
    return (
        f"{int(remaining)} tool calls remaining. Each task typically costs at least "
        f"{TOOLS_PER_TASK} tool calls (act + verify). Emit a plan that fits "
        f"(task count × {TOOLS_PER_TASK} ≤ remaining). Prefer 1-3 tasks when the "
        "budget is tight. Do not emit review, backup, polish, or extra README "
        "tasks unless the criteria require them."
    )


def pick_cheapest(candidates: List[dict]) -> dict:
    """Prefer a non-fat candidate; otherwise the fewest-task graph."""
    if not candidates:
        raise ValueError("no plan candidates")
    fit = [c for c in candidates if not c.get("fat")]
    pool = fit or candidates
    return min(pool, key=lambda c: len(c["graph"].tasks))


def compact_graph(graph: TaskGraph, max_tasks: int) -> Tuple[TaskGraph, List[Check], bool]:
    """Merge extra tasks into the last kept task. Returns leftover checks.

    Used for fallback graphs only. Does not add checks (F-17 fallback tasks
    stay check-less). LLM graphs are selected, not compacted.
    """
    order = [graph.tasks[i] for i in graph.order]
    n = len(order)
    cap = max(1, int(max_tasks))
    if n <= cap:
        return graph, [], False
    keep_src = order[:cap]
    extra = order[cap:]
    leftover: List[Check] = []
    built: List[Tuple[Task, List[str]]] = []
    for i, src in enumerate(keep_src):
        text = src.text
        checks = list(src.checks)
        if i == cap - 1 and extra:
            extra_text = "; ".join(t.text for t in extra if (t.text or "").strip())
            if extra_text:
                text = (text + "; " + extra_text)[:2000]
            overflow: List[Check] = []
            for t in extra:
                overflow.extend(list(t.checks))
            room = max(0, 6 - len(checks))
            checks = checks + overflow[:room]
            leftover = overflow[room:]
        t = Task.new(src.objective_id, text, optional=src.optional, agent=src.agent,
                     checks=checks, priority=src.priority)
        built.append((t, list(src.depends_on)))
    idmap = {src.id: t.id for (t, _), src in zip(built, keep_src)}
    tasks = []
    for t, deps in built:
        t.depends_on = [idmap[d] for d in deps if d in idmap]
        tasks.append(t)
    g = TaskGraph(tasks)
    try:
        g.validate()
    except Exception:
        for i, tid in enumerate(g.order):
            g.tasks[tid].depends_on = [g.order[i - 1]] if i else []
    return g, leftover, True
