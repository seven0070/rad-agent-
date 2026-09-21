"""Sovereignty auditor (RFC-006 P1) — how much happened inside?

Pure stdlib. Reads events.jsonl only. A port call = external touchpoint tag.
Law: capability borrowed is not capability owned.

CONTRACT: internal_ratio rounded to 3dp; fully_sovereign counted when an
objective's events contain ZERO port tags (L2).
"""
import json
from pathlib import Path
from collections import Counter

PORT_TAGS = {"P1_cognition_cloud": "cloud brain",
             "P2_knowledge_web": "browse/search",
             "P3_skill_clone": "external skill",
             "P4_train_cloud": "cloud training",
             "P5_drive_sync": "external backup"}
STAGES = ["ingest", "understand", "plan", "execute", "verify", "deliver", "sleep", "evolve"]

def set_paths(objectives_dir: Path):     # L5
    global _OBJECTIVES_DIR
    _OBJECTIVES_DIR = Path(objectives_dir)

_OBJECTIVES_DIR = Path.home() / ".rad" / "objectives"

def audit_objective(objectives_dir: Path | None = None, obj_id: str | None = None) -> dict:
    od = Path(objectives_dir) if objectives_dir else _OBJECTIVES_DIR
    if obj_id:
        targets = [od / obj_id] if (od / obj_id).exists() else []
    else:
        targets = [d for d in od.iterdir() if d.is_dir()] if od.exists() else []
        targets = [d for d in targets if (d / "events.jsonl").exists()]

    report = {"objectives": 0, "fully_sovereign": 0, "port_calls": {},
              "internal_ratio": None, "stage_coverage": {}}
    stage_hits, total = Counter(), 0
    port_counter = Counter()

    for d in targets:
        report["objectives"] += 1
        ext = False
        for line in (d / "events.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            for tag in PORT_TAGS:
                if tag in line:
                    port_counter[tag] += 1
                    ext = True
            for s in STAGES:
                if s in line:
                    stage_hits[s] += 1
        if not ext:
            report["fully_sovereign"] += 1
        total += 1

    if total:
        report["internal_ratio"] = round(report["fully_sovereign"] / total, 3)
    report["port_calls"] = dict(port_counter)
    report["stage_coverage"] = {s: stage_hits.get(s, 0) for s in STAGES}
    report["law"] = "capability borrowed is not capability owned"
    return report
