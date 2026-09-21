"""Memory strength, decay, sleep consolidation — deterministic + testable.

strength = origin_w * verification_m * freq_boost * exp(-lambda_layer * days_idle)
Formula is PINNED (versioned). Changing it is a generation, not an edit.
"""
import json, math
from datetime import datetime, timezone
from pathlib import Path

ORIGIN_WEIGHT = {"user": 1.0, "observed": 0.8, "inferred": 0.6, "model_generated": 0.4}
VERIFICATION_MULT = {"verified": 1.0, "unverified": 0.85, "contradicted": 0.5}
LAYER_LAMBDA = {"episodic": 0.10, "semantic": 0.02, "procedural": 0.005}
ARCHIVE_THRESHOLD = 0.15
FORMULA_VERSION = 1

def strength(mem: dict, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    last_used = _parse_ts(mem.get("last_used_at", mem.get("created_at", now.isoformat())))
    days_idle = max(0.0, (now - last_used).total_seconds() / 86400)
    base = ORIGIN_WEIGHT.get(mem.get("origin", "model_generated"), 0.4) * \
           VERIFICATION_MULT.get(mem.get("verification", "unverified"), 0.85)
    freq = 1 + 0.1 * math.log1p(int(mem.get("recall_count", 0)))
    return round(base * freq * math.exp(-LAYER_LAMBDA.get(mem.get("layer", "semantic"), 0.05) * days_idle), 4)

def reinforce(mem: dict, verified: bool | None = None) -> dict:
    mem["recall_count"] = int(mem.get("recall_count", 0)) + 1
    mem["last_used_at"] = datetime.now(timezone.utc).isoformat()
    if verified is True:
        mem["verification"] = "verified"
    return mem

def sleep(memory_root: Path, now: datetime | None = None, drive_sync_fn=None) -> dict:
    """Consolidation pass. Layout: memory_root/long/{layer}/*.json, archive/.
    Deterministic given same files + timestamp. Archive NEVER deletes."""
    now = now or datetime.now(timezone.utc)
    report = {"formula_version": FORMULA_VERSION, "ran_at": now.isoformat(),
              "scanned": 0, "reinforced": 0, "decayed": 0, "archived": 0,
              "strongest": None, "weakest_surviving": None}
    archive_dir = memory_root / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    for layer_dir in (memory_root / "long").glob("*"):
        if not layer_dir.is_dir(): continue
        for mf in sorted(layer_dir.glob("*.json")):
            report["scanned"] += 1
            mem = json.loads(mf.read_text(encoding="utf-8"))
            s = strength(mem, now)
            if mem.get("_pending_reinforce"):
                mem = reinforce(mem, verified=mem.pop("_verified_flag", None))
                report["reinforced"] += 1
            elif s < ARCHIVE_THRESHOLD:
                mem["archived_at"] = now.isoformat()
                mem["strength_at_archive"] = s
                (archive_dir / mf.name).write_text(json.dumps(mem, indent=2), encoding="utf-8")
                mf.unlink()
                report["archived"] += 1
                continue
            else:
                report["decayed"] += 1
            mem["strength_at_last_sleep"] = s
            mf.write_text(json.dumps(mem, indent=2), encoding="utf-8")
            if report["strongest"] is None or s > report["strongest"][1]:
                report["strongest"] = [mf.name, s]
            if s >= ARCHIVE_THRESHOLD and (report["weakest_surviving"] is None
                                           or s < report["weakest_surviving"][1]):
                report["weakest_surviving"] = [mf.name, s]

    if drive_sync_fn:
        report["drive_sync"] = drive_sync_fn(memory_root)  # integration hook
    (memory_root / "last_sleep_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    return report

def _parse_ts(s: str) -> datetime:
    try: return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception: return datetime.now(timezone.utc)
