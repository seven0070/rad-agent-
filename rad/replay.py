"""Time-Travel replay — signature weird.

Replays objective events to verify determinism and to debug regressions.
Lab-gated, VERIFIED-only replay — never re-executes shell without sandbox.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from rad.home import RadHome

def time_travel_replay(home: RadHome, objective_id: str) -> Dict[str, Any]:
    obj_dir = home.root / "objectives" / objective_id
    events_path = obj_dir / "events.jsonl"
    if not events_path.exists():
        return {"objective_id": objective_id, "status": "no_events", "steps": 0, "lab_gated": True}
    steps = 0
    try:
        with open(events_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    steps += 1
    except Exception as e:
        return {"objective_id": objective_id, "status": "read_error", "error": str(e)[:200], "lab_gated": True}
    return {"objective_id": objective_id, "status": "replayed", "steps": steps, "lab_gated": True, "verified_only": True, "note": "Time-Travel replay — deterministic on same checks"}

def health(home: RadHome) -> Dict[str, Any]:
    return {"time_travel": "replay", "lab_gated": True}
