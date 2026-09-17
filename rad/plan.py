"""The planning layer — goal-driven, not just reactive.

`rad plan <goal>` decomposes a goal into steps (LLM-backed when a brain is
online, deterministic fallback otherwise), persists it, and tracks progress.
The brain can also drive it mid-chat: plans live in a file it can read/update.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome
from rad.ui import col


class Plan:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.path = home.root / "plan" / "current.json"

    def load(self) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return None

    def save(self, p: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(p, indent=2, ensure_ascii=False))

    def create(self, goal: str, caller: Optional[Any] = None) -> Dict[str, Any]:
        steps: List[str] = []
        if caller is not None:
            try:
                raw = caller(
                    "Decompose this goal into 3-7 concrete, checkable steps. "
                    "Reply with ONLY a JSON array of short strings.", goal)
                m = re.search(r"\[.*\]", raw or "", re.S)
                if m:
                    steps = [str(s).strip() for s in json.loads(m.group(0)) if str(s).strip()][:7]
            except Exception:
                steps = []
        if not steps:
            # deterministic fallback: split on conjunctions / sentences
            parts = re.split(r"\b(?:and then|then|and|;|, then|, and)\b|\.(?=\s|$)", goal, flags=re.I)
            steps = [p.strip(" .") for p in parts if len(p.strip(" .")) > 3][:7]
            if not steps:
                steps = [goal]
        plan = {"goal": goal, "created": time.time(),
                "steps": [{"text": s, "done": False, "note": ""} for s in steps]}
        self.save(plan)
        return plan

    def toggle(self, idx: int, done: bool = True, note: str = "") -> Optional[Dict[str, Any]]:
        p = self.load()
        if not p or not (0 <= idx < len(p["steps"])):
            return None
        p["steps"][idx]["done"] = done
        if note:
            p["steps"][idx]["note"] = note
        self.save(p)
        return p

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def status(self) -> str:
        p = self.load()
        if not p:
            return "  no active plan — `rad plan <goal>`"
        out = [f"  goal: {col.bold(p['goal'])}"]
        done = sum(1 for s in p["steps"] if s["done"])
        out.append(f"  progress: {done}/{len(p['steps'])}")
        for i, s in enumerate(p["steps"]):
            mark = col.green("[x]") if s["done"] else " [ ]"
            note = f"  {col.dim('(' + s['note'] + ')')}" if s.get("note") else ""
            out.append(f"   {mark} {i + 1}. {s['text']}{note}")
        return "\n".join(out)
