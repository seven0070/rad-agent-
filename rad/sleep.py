"""Rad's sleep — consolidate short-term memory into long-term, decay, archive,
and (if connected) sync the mind to Google Drive.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from rad.home import RadHome
from rad.memory import Memory
from rad.router import RouterState
from rad.ui import info


def _make_consolidator(home: RadHome, router: RouterState):
    """LLM-backed consolidation: short-term log → {episodic, semantic, procedural}."""
    prompt_head = (
        "You are the memory-consolidation process of a personal AI agent. "
        "Read the raw session log below and extract durable memories.\n"
        "Return ONLY JSON: {\"episodic\": [events that happened, one line each], "
        "\"semantic\": [facts about the user, their world, preferences], "
        "\"procedural\": [skills, how-tos, working approaches learned]}.\n"
        "Rules: max 8 items per list, each ≤ 200 chars, no duplicates, no small talk. "
        "If nothing is durable in a category, return an empty list.\n\n"
    )

    def consolidator(text: str) -> Optional[Dict[str, List[str]]]:
        res = router.chat([{"role": "user", "content": prompt_head + text[:18000]}],
                          stream_cb=None, temperature=0.2)
        m = re.search(r"\{.*\}", res.text or "", re.S)
        if not m:
            return None
        d = json.loads(m.group(0))
        return {k: [str(x) for x in (d.get(k) or []) if str(x).strip()]
                for k in ("episodic", "semantic", "procedural")}

    return consolidator


def run_sleep(home: RadHome, router: Optional[RouterState] = None,
              sync_drive: bool = True) -> Dict[str, int]:
    mem = Memory(home)
    router = router or RouterState(home)
    report: Dict[str, int] = {}
    try:
        report = mem.sleep(consolidator=_make_consolidator(home, router))
    except Exception as e:
        info(f"  (LLM consolidation unavailable: {e} — used heuristics)")
        report = mem.sleep(consolidator=None)
    # decay & archive already inside sleep()
    if sync_drive:
        try:
            from rad.drive import Drive
            d = Drive(home)
            st = d.state()
            if st.get("client_id"):
                note = d.push()
                info(f"  drive sync: {note}")
        except Exception as e:
            info(f"  (drive sync skipped: {str(e)[:120]})")
    _phase_next_sleep(home.root)
    return report

def _phase_next_sleep(home):
    try:
        from rad.federation.cadence import sleep_checkup
        sleep_checkup()                                   # canary on 24h cadence
    except Exception: pass
    try:
        from rad import curiosity
        from pathlib import Path
        curiosity.explore_once(home=Path(home), papers_dir=Path(home) / "papers",
                               rng=__import__("random").Random())
    except Exception: pass

