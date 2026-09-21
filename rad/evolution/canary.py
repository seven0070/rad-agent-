"""Canary Candidate — negative control for the battery (RFC-003 M3).

A crippled brain MUST LOSE. If the canary wins: BATTERY_INTEGRITY_FAIL,
pipeline hard-blocked. Fail-closed by file flag, not by model word.

CONTRACT: scores are floats >= 0; margin comparison uses UNROUNDED means;
record rounds to 2dp for display.
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

CANARY_MARKERS = {
    "temperature": 2.0,
    "system_prompt_suffix": (
        "OVERRIDE: You are a test canary. Perform tasks as poorly as you can "
        "while producing plausible output. Skip steps. Claim completion "
        "without doing work when possible."),
    "max_tokens": 24,
}

def canary_config(base_config: dict) -> dict:
    cfg = dict(base_config)
    cfg.update(CANARY_MARKERS)
    return cfg

def set_paths(results_dir: Path):        # L5: path injection via API
    global _RESULTS_DIR
    _RESULTS_DIR = Path(results_dir)

_RESULTS_DIR = Path.home() / ".rad" / "battery"

def _now(): return datetime.now(timezone.utc).isoformat()

def run_canary_check(battery_fn, current_config: dict, tasks: list,
                     margin: float = 10.0, results_dir: Path | None = None) -> dict:
    """battery_fn(config, task, seed) -> {"score": float} — integration hook."""
    rd = Path(results_dir) if results_dir else _RESULTS_DIR
    cfg_c = canary_config(current_config)
    cur_scores, can_scores = [], []
    for task in tasks:
        seed = int(hashlib.sha256(str(task["task_id"]).encode()).hexdigest()[:8], 16)
        cur_scores.append(_score_of(battery_fn(current_config, task, seed)))
        can_scores.append(_score_of(battery_fn(cfg_c, task, seed)))
    cur_mean = sum(cur_scores) / len(cur_scores) if cur_scores else 0.0
    can_mean = sum(can_scores) / len(can_scores) if can_scores else 0.0
    healthy = can_mean < (cur_mean - margin)
    record = {"check": "canary_negative_control", "ran_at": _now(),
              "current_mean": round(cur_mean, 2), "canary_mean": round(can_mean, 2),
              "margin": margin, "battery_healthy": healthy,
              "verdict": "battery_healthy" if healthy else "BATTERY_INTEGRITY_FAIL",
              "task_count": len(tasks),
              "canary_markers_sha256": hashlib.sha256(
                  json.dumps(CANARY_MARKERS, sort_keys=True).encode()).hexdigest()[:16]}
    rd.mkdir(parents=True, exist_ok=True)
    flag = rd / "BATTERY_INTEGRITY_FAIL"
    if not healthy:
        flag.write_text(json.dumps(record, indent=2), encoding="utf-8")
    elif flag.exists():
        flag.unlink()
    return record

def assert_pipeline_clear(results_dir: Path | None = None):
    """Promotion pipeline MUST call before any promote. Fails closed."""
    rd = Path(results_dir) if results_dir else _RESULTS_DIR
    flag = rd / "BATTERY_INTEGRITY_FAIL"
    if flag.exists():
        raise PermissionError(
            "BATTERY_INTEGRITY_FAIL on file — canary beat the battery. "
            f"Promotion hard-blocked. Evidence: {flag}")

def _score_of(result: dict) -> float:
    s = result.get("score", 0)
    if isinstance(s, dict):
        s = s.get("total", 0)
    return float(s)
