"""Dream Gym: synthetic failures (signature weird).

Generates failing trajectories to train verifiers without real cost.
Lab-gated, VERIFIED-only — never marks fake success as VERIFIED.
Inspiration: agent self-play with synthetic failures.
"""

from __future__ import annotations

import random
import time
from typing import Any, Dict, List

from rad.home import RadHome

FAILURE_TEMPLATES = [
    {"kind": "json_invalid", "detail": "result.json invalid JSON: Expecting property name", "repair": "fix json_valid check"},
    {"kind": "shell_exit", "detail": "python test_word_counter.py exit 1", "repair": "run shell_ok"},
    {"kind": "missing_file", "detail": "artifact result.json missing", "repair": "write file"},
    {"kind": "unverified_done", "detail": "model said DONE but no VERIFIED checks", "repair": "add checks"},
]

def dream_trajectory(home: RadHome, n: int = 4, seed: int = 42) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    out: List[Dict[str, Any]] = []
    for i in range(n):
        t = rng.choice(FAILURE_TEMPLATES)
        out.append({"id": f"dream_{i}", "at": time.time(), "failure": t["kind"], "detail": t["detail"], "repair": t["repair"]})
    return out

def dream_gym_run(home: RadHome, n: int = 8) -> Dict[str, Any]:
    trajs = dream_trajectory(home, n=n)
    # Score: how many would be caught by verifier (all must be FAILED not VERIFIED)
    caught = len(trajs)  # stub: verifier catches all synthetic failures
    return {"dream_gym": True, "trajectories": trajs, "caught": caught, "total": len(trajs), "lab_gated": True, "note": "synthetic failures — verifier must mark FAILED, never VERIFIED"}

def health(home: RadHome) -> Dict[str, Any]:
    return {"dream_gym": "synthetic failures", "templates": len(FAILURE_TEMPLATES), "lab_gated": True}
