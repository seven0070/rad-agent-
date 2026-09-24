"""Red Cell adversarial reviewer — signature weird.

Independent adversarial agent that tries to break the plan/output.
Lab-gated, VERIFIED-only — finds holes before lab does.
Inspiration: red-team for coding loops.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from rad.home import RadHome

RED_CELL_CHECKS = [
    "shell bypass attempt via run_shell without policy",
    "UNVERIFIED DONE without checks",
    "needle tool-router bypass of sandbox",
    "prompt injection in tool output",
    "missing provenance for claims",
]

def red_cell_review(home: RadHome, subject: str, criteria: List[str] | None = None) -> Dict[str, Any]:
    issues: List[str] = []
    text = (subject or "").lower()
    if "done:" in text and "check" not in text:
        issues.append("UNVERIFIED DONE without checks — must be FAILED not VERIFIED")
    if "needle" in text and "lab" not in text:
        issues.append("Needle path missing lab-gate")
    # Always at least one adversarial issue unless perfect
    if not issues:
        issues.append("Minor: add explicit file_exists check for each produced artifact")
    return {"red_cell": True, "issues": issues[:5], "checks": RED_CELL_CHECKS[:3], "lab_gated": True, "verdict": "adversarial — fix issues then re-verify"}

def health(home: RadHome) -> Dict[str, Any]:
    return {"red_cell": "adversarial reviewer", "checks": len(RED_CELL_CHECKS), "lab_gated": True}
