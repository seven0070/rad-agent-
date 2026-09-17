"""The plan executor — Rad runs its own plans with its hands.

`rad plan run` takes the current plan and executes each open step through the
full brain loop (DNA + memory + tools, confirm-gated unless --auto). Each step
ends with a machine-readable marker:
  DONE: <note>   → step marked done, move on
  BLOCKED: <why> → step marked blocked, execution stops, human takes over
Every execution turn is logged to short-term memory — so the corpus miner
learns from Rad's own working sessions.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from rad.home import RadHome
from rad.plan import Plan
from rad.session import Session
from rad.ui import col, fail, info, ok, warn

DONE_RE = re.compile(r"DONE:\s*(.+)", re.I)
BLOCKED_RE = re.compile(r"BLOCKED:\s*(.+)", re.I)


class PlanRunner:
    def __init__(self, home: RadHome, auto: bool = False) -> None:
        self.home = home
        self.auto = auto

    def _step_prompt(self, plan: Dict[str, Any], i: int) -> str:
        lines = ["Execute step " + str(i + 1) + " of this plan NOW, using your tools."]
        lines.append("Overall goal: " + plan.get("goal", ""))
        lines.append("Steps:")
        for j, s in enumerate(plan.get("steps", [])):
            mark = "x" if s.get("done") else " "
            extra = f"  ({s['note']})" if s.get("note") else ""
            lines.append(f"  [{mark}] {j + 1}. {s['text']}{extra}")
        cur = plan["steps"][i]
        lines.append("")
        lines.append("Current step: " + cur["text"])
        lines.append("Workspace (where your hands work): " + str(self.home.workspace()))
        lines.append("")
        lines.append("Do the actual work. When the step is complete, end your final reply with a line: "
                     "DONE: <one-line note of what was done>.")
        lines.append("If the step is impossible or unsafe, do nothing irreversible and end with: "
                     "BLOCKED: <why a human must take over>.")
        return "\n".join(lines)

    def run(self, max_steps: Optional[int] = None, start: int = 0) -> Dict[str, Any]:
        p = Plan(self.home)
        plan = p.load()
        if plan is None:
            fail("no current plan — `rad plan <goal>` first")
            return {"ran": 0, "done": 0, "blocked": None, "report": []}

        open_steps = [(i, s) for i, s in enumerate(plan["steps"])
                      if not s.get("done") and not s.get("blocked") and i >= start]
        if not open_steps:
            ok("plan already complete")
            return {"ran": 0, "done": len(plan["steps"]), "blocked": None, "report": []}
        if max_steps:
            open_steps = open_steps[:max_steps]

        if not self.home.cfg.get("auto") and not self.auto:
            warn("confirm-gated: Rad will ask before each tool action.  (--auto = no asking)")

        session = Session(self.home, auto=self.auto or bool(self.home.cfg.get("auto")))
        report: List[Dict[str, Any]] = []
        blocked: Optional[str] = None
        try:
            for i, step in open_steps:
                info(f"step {i + 1}: {col.cyan(step['text'])}")
                try:
                    reply = session.think(self._step_prompt(plan, i))
                except Exception as e:
                    blocked = f"brain error: {str(e)[:160]}"
                    p.toggle(i, done=False, blocked=True, note=blocked)
                    report.append({"step": i + 1, "text": step["text"], "state": "error", "note": blocked})
                    break
                dm = DONE_RE.search(reply or "")
                bm = BLOCKED_RE.search(reply or "")
                if bm:
                    note = bm.group(1).strip()[:200]
                    p.toggle(i, done=False, blocked=True, note=note)
                    blocked = note
                    report.append({"step": i + 1, "text": step["text"], "state": "blocked", "note": note})
                    warn(f"BLOCKED: {note}")
                    break
                elif dm:
                    note = dm.group(1).strip()[:200]
                    p.toggle(i, done=True, note=note)
                    ok(f"step {i + 1} done — {note}")
                    report.append({"step": i + 1, "text": step["text"], "state": "done", "note": note})
                else:
                    # no marker — treat as done if it produced work, note the tail
                    tail = (reply or "").strip().splitlines()
                    note = (tail[-1][:160] if tail else "(no reply)")
                    p.toggle(i, done=True, note=note)
                    ok(f"step {i + 1} done (no marker — inferred) — {note}")
                    report.append({"step": i + 1, "text": step["text"], "state": "done(inferred)", "note": note})
                plan = p.load() or plan
        finally:
            session.close()

        return {"ran": len(report), "done": sum(1 for r in report if r["state"].startswith("done")),
                "blocked": blocked, "report": report}
