"""Replay — reconstruct what happened to an objective from its transcript and observations,
and (optionally) re-run every verification check against the *current* environment.

Deterministic replay of tool side effects is not attempted (shell commands are not
idempotent); instead replay gives you the exact prompts, replies, tool calls, results,
and lets you re-verify so you can see whether the world still matches what RAD claimed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.control import events as E
from rad.control.events import EventLog
from rad.control.graph import TaskGraph
from rad.control.objectives import ObjectiveStore
from rad.control.observer import Observer
from rad.control.tasks import Check
from rad.control.verifier import Verifier


class Replay:
    def __init__(self, store: ObjectiveStore, oid: str, workspace: Path) -> None:
        self.store = store
        self.oid = oid
        self.dir = store.dir(oid)
        self.log = EventLog(store.events_path(oid))
        self.observer = Observer(self.dir)
        self.workspace = workspace

    def timeline(self) -> List[Dict[str, Any]]:
        """Per task attempt: prompt, reply, tool calls with results, verification, recovery."""
        out: List[Dict[str, Any]] = []
        cur: Optional[Dict[str, Any]] = None
        for ev in self.log.read():
            d = ev.data
            if ev.kind == E.TASK_STARTED:
                cur = {"task": ev.task_id, "attempt": d.get("attempt"), "text": d.get("text", ""),
                       "prompt": "", "reply": "", "provider": "", "tools": [], "verification": None,
                       "recovery": None, "error": ""}
                out.append(cur)
            elif cur is None or ev.task_id != cur["task"]:
                continue
            elif ev.kind == E.TOOL_CALLED:
                cur["tools"].append({"action": d.get("action"), "tool": d.get("tool"), "args": d.get("args"),
                                     "status": None, "ms": None, "observation": None})
            elif ev.kind == E.TOOL_RESULT:
                for t in cur["tools"]:
                    if t["action"] == d.get("action"):
                        t.update(status=d.get("status"), ms=d.get("ms"), observation=d.get("observation"))
            elif ev.kind == E.TRANSCRIPT:
                cur.update(prompt=d.get("prompt", ""), reply=d.get("reply", ""),
                           provider=d.get("provider", ""), error=d.get("error", ""))
            elif ev.kind == E.VERIFICATION_RESULT:
                cur["verification"] = {"status": d.get("status"), "summary": d.get("summary", "")}
            elif ev.kind == E.RECOVERY_DECISION:
                cur["recovery"] = {"strategy": d.get("strategy"), "class": d.get("failure_class"),
                                   "reason": d.get("reason", "")}
        return out

    def reverify(self, llm=None) -> Dict[str, Any]:
        """Re-run every task's checks and the objective checks against the current workspace."""
        obj = self.store.load(self.oid)
        graph = TaskGraph.from_list(self.store.load_tasks(self.oid))
        v = Verifier(self.workspace, self.observer, llm=llm)
        tasks = []
        for tid in graph.order:
            t = graph.tasks[tid]
            res = [v.run_check(c, reply=t.reply) for c in t.checks]
            tasks.append({"task": tid, "text": t.text, "recorded": (t.verification or {}).get("status"),
                          "now": ("VERIFIED" if res and all(r["ok"] for r in res) else
                                  "FAILED" if res else "UNVERIFIED"),
                          "results": res})
        ochecks = [Check.from_dict(c) for c in (obj.verification or {}).get("objective_checks", [])] if obj else []
        ores = [v.run_check(c) for c in ochecks]
        # drift = a check that passed at run time fails now (tasks without checks carry no information)
        drift = [t for t in tasks if t["recorded"] == "VERIFIED" and t["now"] == "FAILED"]
        rep = {"objective": self.oid,
               "tasks": tasks,
               "objective_checks": ores,
               "objective_now": ("VERIFIED" if ores and all(r["ok"] for r in ores) else
                                 "FAILED" if ores else "UNVERIFIED"),
               "drift": [t["task"] for t in drift]}
        self.log.emit(E.REPLAY, self.oid, objective_now=rep["objective_now"], drift=rep["drift"])
        return rep
