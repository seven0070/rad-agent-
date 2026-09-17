"""Planner — turn an Objective into a TaskGraph with machine-checkable Checks.

LLM-backed when a brain is online; deterministic fallback otherwise (the
fallback produces one task per clause and no checks, which the Verifier will
correctly report as UNVERIFIED rather than pretending).
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Dict, List, Optional

from rad.control.graph import TaskGraph
from rad.control.objectives import Objective
from rad.control.tasks import Check, Task

PLAN_PROMPT = """You are the planner of an autonomous agent. Decompose the goal into 2-12 concrete tasks.
Each task must be independently executable with tools (shell, read/write files in the workspace, web search/fetch).
For EVERY task give machine-checkable checks that prove it was done. Prefer checks over trust.

Check kinds (exactly these):
  file_exists {{"path"}}            file_min_bytes {{"path","n"}}      file_contains {{"path","text"}}
  json_valid {{"path"}}             shell_ok {{"command"}}            shell_output {{"command","contains"}}
  reply_matches {{"pattern"}}       (regex on the agent's final reply — weakest; use only when nothing else fits)

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

REPLAN_PROMPT = """You are replanning part of an autonomous agent's work after failures.
GOAL: {goal}
COMPLETED TASKS:
{done}
FAILED/BLOCKED TASK: {failed}
WHY: {why}
REMAINING (will be replaced): 
{remaining}
WORKSPACE: {workspace}

Propose 1-5 NEW tasks that achieve what the failed and remaining tasks were meant to, using a different approach.
Same JSON shape as before: {{"tasks":[{{"id":"r1","text":"...","depends_on":[],"checks":[...]}}]}}
Only reference ids of the new tasks or COMPLETED task ids in depends_on. Reply ONLY with JSON.
"""


class Planner:
    def __init__(self, llm: Optional[Callable[[str], str]], workspace: str) -> None:
        self.llm = llm
        self.workspace = workspace

    # ------------------------------------------------------------ plan
    def plan(self, obj: Objective) -> Dict[str, Any]:
        """Return {"graph": TaskGraph, "objective_checks": [Check], "source": "llm"|"fallback"}."""
        if self.llm:
            try:
                raw = self.llm(PLAN_PROMPT.format(
                    goal=obj.goal,
                    criteria="\n".join(f"- {c}" for c in obj.success_criteria) or "- (none given: infer sensible ones)",
                    constraints="\n".join(f"- {c}" for c in obj.constraints) or "- none",
                    workspace=self.workspace))
                d = _json_obj(raw)
                g, oc = self._graph_from(obj.id, d)
                if g.tasks:
                    return {"graph": g, "objective_checks": oc, "source": "llm"}
            except Exception:
                pass
        return {"graph": self._fallback(obj), "objective_checks": [], "source": "fallback"}

    def replan(self, obj: Objective, graph: TaskGraph, failed: Task, why: str) -> Optional[List[Task]]:
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
                workspace=self.workspace))
            d = _json_obj(raw)
            g, _ = self._graph_from(obj.id, d, allowed_deps={t.id for t in done})
            return list(g.tasks.values()) or None
        except Exception:
            return None

    # ------------------------------------------------------------ helpers
    def _graph_from(self, oid: str, d: Dict[str, Any], allowed_deps: Optional[set] = None):
        items = d.get("tasks") or []
        idmap: Dict[str, str] = {}
        tasks: List[Task] = []
        for it in items[:12]:
            text = str(it.get("text", "")).strip()
            if not text:
                continue
            t = Task.new(oid, text, optional=bool(it.get("optional", False)))
            idmap[str(it.get("id", t.id))] = t.id
            t.checks = _checks(it.get("checks") or [])
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
        return g, _checks(d.get("objective_checks") or [])

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
