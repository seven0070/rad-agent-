"""Planner — turn an Objective into a TaskGraph with machine-checkable Checks.

LLM-backed when a brain is online; deterministic fallback otherwise (the
fallback produces one task per clause and no checks, which the Verifier will
correctly report as UNVERIFIED rather than pretending).

Bare check paths on a package-layout goal are joined to that package directory
(RW-069). Inferred json_valid / test / file_line_count contracts are merged into
LLM objective_checks that omitted them (RW-071). Check *kinds* are never
silently remapped (F-26).

A transient LLM plan failure (timeout, empty, malformed, non-JSON, empty graph)
is retried a bounded number of times for a structured JSON plan *before*
falling back. Fallback still splits `obj.goal` only (F-17); it never parses
model prose.

When a remaining tool budget is known, a *fat* plan (more tasks than fit at
2 tools/task, and more than 3 tasks) is retried with a budget nudge; the
cheaper graph is selected. Exhausted fallback graphs that are still fat are
compacted. LLM graphs are never silently compacted (F-21 leftover work).
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

from rad.control.budgetplan import (
    budget_prompt_line,
    compact_graph,
    estimate_plan_tools,
    is_fat,
    is_over_budget,
    max_fit_tasks,
    pick_cheapest,
)
from rad.control.codingloop import (
    align_checks,
    infer_coding_checks,
    infer_package_dir,
    merge_coding_checks,
)
from rad.control.graph import TaskGraph
from rad.control.objectives import Objective
from rad.control.tasks import Check, Task

DEFAULT_PLAN_RETRIES = 1   # one retry after the first failure (2 attempts)
MAX_PLAN_RETRIES = 3       # hard cap — never an unbounded plan loop

PLAN_PROMPT = """You are the planner of an autonomous agent. Decompose the goal into the smallest set of concrete tasks that covers the success criteria (typically 2-6; never more than 16).
A single-file write or one-command goal is 1-3 tasks. Do not invent extra review, backup, polish, README, or documentation tasks unless the criteria require them.
Each task must be independently executable with tools (shell, read/write files in the workspace, web search/fetch).
For EVERY task give machine-checkable checks that prove it was done. Prefer checks over trust.
TOOL BUDGET: {tool_budget}

Check kinds (exactly these):
  file_exists {{"path"}}            file_min_bytes {{"path","n"}}      file_contains {{"path","text"}}
  json_valid {{"path"}}             json_field {{"path","key"}}       json_min_len {{"path","n"}}
  file_line_count {{"path","n"}}    exact newline/line count (use for "exact N-line" files)
  shell_ok {{"command"}}            shell_output {{"command","contains"}}
  reply_matches {{"pattern"}}       (regex on the agent's final reply — weakest; use only when nothing else fits)
  agent_review {{"criteria":[...]}} (independent read-only reviewer agent — use for quality of prose/code, IN ADDITION to a file check)

For coding / test / JSON-result goals always include json_valid on every .json artifact and
shell_ok (or shell_output) for the test command (pytest / python3 test_*.py). Never treat a
DONE: line as a file path. A model claiming DONE is not completion. Empty .json is invalid JSON.
If the goal places files under a directory (e.g. pkg/ or text_analyzer/), check paths MUST
use that prefix (pkg/input.txt not input.txt).
If the goal is a multi-file package, do NOT emit a standalone mkdir/create-directory task —
write_file creates parent directories. Prefer fewer tasks that each write and verify.
For "exact N-line" files include file_line_count.

GOAL: {goal}
SUCCESS CRITERIA:
{criteria}
CONSTRAINTS:
{constraints}
WORKSPACE: {workspace}

Reply ONLY with JSON:
{{"tasks":[{{"id":"t1","text":"...","depends_on":[],"optional":false,
            "checks":[{{"kind":"file_exists","args":{{"path":"report.md"}},"description":"report written"}}]}}],
  "objective_checks":[{{"kind":"file_min_bytes","args":{{"path":"report.md","n":500}},"description":"report is substantial"}}]}}
"""

PLAN_RETRY_NUDGE = (
    "\n\nYour previous reply was not usable (timeout, empty, or not JSON). "
    "Reply ONLY with the JSON object. No prose, no markdown fences."
)

PLAN_BUDGET_NUDGE = (
    "\n\nYour previous plan used too many tasks for the remaining tool budget. "
    "Reply ONLY with JSON for a SMALLER plan that fits the budget "
    "(each task costs at least 2 tool calls). Prefer 1-3 tasks. No prose."
)

REPLAN_PROMPT = """You are replanning part of an autonomous agent's work after failures.
GOAL: {goal}
COMPLETED TASKS:
{done}
FAILED/BLOCKED TASK: {failed}
WHY: {why}
REMAINING (will be replaced): 
{remaining}
WORKSPACE: {workspace}
TOOL BUDGET: {tool_budget}

Propose 1-5 NEW tasks that achieve what the failed and remaining tasks were meant to, using a different approach.
The new graph must fit the remaining tool budget (each task costs at least 2 tool calls). Prefer fewer tasks.
Same JSON shape as before: {{"tasks":[{{"id":"r1","text":"...","depends_on":[],"checks":[...]}}]}}
Only reference ids of the new tasks or COMPLETED task ids in depends_on. Reply ONLY with JSON.
"""


def _bound_retries(n: Any) -> int:
    try:
        v = int(DEFAULT_PLAN_RETRIES if n is None else n)
    except (TypeError, ValueError):
        v = DEFAULT_PLAN_RETRIES
    return max(0, min(MAX_PLAN_RETRIES, v))


class Planner:
    def __init__(self, llm: Optional[Callable[[str], str]], workspace: str,
                 max_tasks: int = 16, retries: int = DEFAULT_PLAN_RETRIES) -> None:
        self.llm = llm
        self.workspace = workspace
        self.max_tasks = max(1, int(max_tasks or 16))   # runaway-plan guard (configurable)
        self.retries = _bound_retries(retries)

    # ------------------------------------------------------------ plan
    def plan(self, obj: Objective, tool_budget: Optional[int] = None) -> Dict[str, Any]:
        """Return graph / objective_checks / source / attempts plus budget-fit fields.

        `retries` is extra tries after the first failure (default 1 → 2 attempts).
        Planning LLM calls are not charged to Budget.model_calls (the controller
        meters model calls on task execution, not on plan()).
        `tool_budget` is remaining tool calls (None = unlimited / unknown).
        """
        attempts = 0
        candidates: List[Dict[str, Any]] = []
        pkg = infer_package_dir(obj.goal, obj.success_criteria)
        if self.llm:
            prompt = PLAN_PROMPT.format(
                goal=obj.goal,
                criteria="\n".join(f"- {c}" for c in obj.success_criteria) or "- (none given: infer sensible ones)",
                constraints="\n".join(f"- {c}" for c in obj.constraints) or "- none",
                workspace=self.workspace,
                tool_budget=budget_prompt_line(tool_budget))
            last_fat = False
            for i in range(1 + self.retries):
                attempts += 1
                extra = PLAN_BUDGET_NUDGE if last_fat else (PLAN_RETRY_NUDGE if i else "")
                try:
                    raw = self.llm(prompt if not extra else prompt + extra)
                    d = _json_obj(raw)
                    g, oc = self._graph_from(obj.id, d, package_dir=pkg)
                    if not g.tasks:
                        last_fat = False
                        continue
                    last_fat = is_fat(len(g.tasks), tool_budget)
                    oc = merge_coding_checks(
                        oc, infer_coding_checks(obj.goal, obj.success_criteria))
                    candidates.append({"graph": g, "objective_checks": oc, "fat": last_fat})
                    if not last_fat:
                        break
                except Exception:
                    last_fat = False
            if candidates:
                chosen = pick_cheapest(candidates)
                return _plan_result(chosen["graph"], chosen["objective_checks"], "llm",
                                    attempts, tool_budget, compacted=False)
        g = self._fallback(obj)
        compacted = False
        cap = max_fit_tasks(tool_budget)
        leftover: List[Check] = []
        if cap is not None and is_fat(len(g.tasks), tool_budget):
            g, leftover, compacted = compact_graph(g, cap)
        oc = infer_coding_checks(obj.goal, obj.success_criteria)
        if leftover:
            oc = merge_coding_checks(oc, leftover)
        return _plan_result(g, oc, "fallback", attempts, tool_budget, compacted=compacted)

    def replan(self, obj: Objective, graph: TaskGraph, failed: Task, why: str,
               tool_budget: Optional[int] = None) -> Optional[List[Task]]:
        if not self.llm:
            return None
        done = [t for t in graph.tasks.values() if t.status == "COMPLETED"]
        remaining = [t for t in graph.tasks.values() if t.status in ("PENDING", "READY", "RETRYING") and t.id != failed.id]
        try:
            raw = self.llm(REPLAN_PROMPT.format(
                goal=obj.goal,
                done="\n".join(f"- {t.id}: {t.text}" for t in done) or "- none",
                failed=f"{failed.id}: {failed.text}", why=why[:600],
                remaining="\n".join(f"- {t.id}: {t.text}" for t in remaining) or "- none",
                workspace=self.workspace,
                tool_budget=budget_prompt_line(tool_budget)))
            d = _json_obj(raw)
            g, _ = self._graph_from(obj.id, d, allowed_deps={t.id for t in done},
                                    package_dir=infer_package_dir(obj.goal, obj.success_criteria))
            cap = max_fit_tasks(tool_budget)
            if cap is not None and is_fat(len(g.tasks), tool_budget):
                g, _, _ = compact_graph(g, cap)
            return list(g.tasks.values()) or None
        except Exception:
            return None

    # ------------------------------------------------------------ helpers
    def _graph_from(self, oid: str, d: Dict[str, Any], allowed_deps: Optional[set] = None,
                    package_dir: Optional[str] = None):
        items = d.get("tasks") or []
        idmap: Dict[str, str] = {}
        tasks: List[Task] = []
        for it in items[:self.max_tasks]:
            text = str(it.get("text", "")).strip()
            if not text:
                continue
            t = Task.new(oid, text, optional=bool(it.get("optional", False)))
            # capability selection: an optional specialist agent can own a task (rad.agents roles)
            t.agent = str(it.get("agent") or "").strip()
            idmap[str(it.get("id", t.id))] = t.id
            t.checks = align_checks(_checks(it.get("checks") or []), package_dir)
            t._raw_deps = [str(x) for x in (it.get("depends_on") or [])]  # type: ignore[attr-defined]
            tasks.append(t)
        for t in tasks:
            deps = []
            for r in getattr(t, "_raw_deps", []):
                if r in idmap:
                    deps.append(idmap[r])
                elif allowed_deps and r in allowed_deps:
                    deps.append(r)
            t.depends_on = deps
            if hasattr(t, "_raw_deps"):
                del t._raw_deps
        g = TaskGraph(tasks)
        # tolerate a bad LLM plan: drop unknown deps / cycles rather than crash
        try:
            g.validate()
        except Exception:
            for t in g.tasks.values():
                t.depends_on = [x for x in t.depends_on if x in g.tasks]
            try:
                g.topological()
            except Exception:
                for i, tid in enumerate(g.order):        # linearise
                    g.tasks[tid].depends_on = [g.order[i - 1]] if i else []
        return g, align_checks(_checks(d.get("objective_checks") or []), package_dir)

    def _fallback(self, obj: Objective) -> TaskGraph:
        parts = re.split(r"\b(?:and then|then|;|, and)\b|\.(?=\s|$)", obj.goal, flags=re.I)
        steps = [p.strip(" .") for p in parts if len(p.strip(" .")) > 3][:7] or [obj.goal]
        g = TaskGraph()
        prev = None
        for s in steps:
            t = Task.new(obj.id, s, depends_on=[prev] if prev else [])
            g.add(t)
            prev = t.id
        return g


def _plan_result(graph: TaskGraph, oc: List[Check], source: str, attempts: int,
                 tool_budget: Optional[int], compacted: bool) -> Dict[str, Any]:
    n = len(graph.tasks)
    return {"graph": graph, "objective_checks": oc, "source": source,
            "attempts": attempts, "tool_budget": tool_budget,
            "estimated_tools": estimate_plan_tools(n), "compacted": compacted,
            "fit": not is_over_budget(n, tool_budget)}


def _checks(items: List[Dict[str, Any]]) -> List[Check]:
    out = []
    for c in items[:6]:
        if isinstance(c, dict) and c.get("kind"):
            out.append(Check(kind=str(c["kind"]), args=dict(c.get("args") or {}),
                             description=str(c.get("description", ""))[:200]))
    return out


def _json_obj(raw: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", raw or "", re.S)
    if not m:
        raise ValueError("no JSON in plan")
    return json.loads(m.group(0))
