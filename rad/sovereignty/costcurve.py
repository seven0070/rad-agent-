"""Sovereignty Curve — MEASURED cost of closing each port (RFC-006).

Law: never assert the tradeoff; measure it. Same suite through internal vs
external configs; delta published in benchmark points.
CONTRACT (L2): means/deltas rounded 2dp; threshold comparisons unrounded.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()

def measure_port_cost(task_suite: list, run_fn,
                      internal_config: dict, external_config: dict,
                      port: str, out_dir: Path | None = None) -> dict:
    """run_fn(config, task, seed) -> {"score": float}. Same contract as
    battle.execute_fn — one integration point reused (Option B adapter)."""
    b, c = [], []
    for t in task_suite:
        seed = abs(hash(t["task_id"])) % (2**32)
        b.append(float(run_fn(internal_config, t, seed).get("score", 0)))
        c.append(float(run_fn(external_config, t, seed).get("score", 0)))
    bm = sum(b) / len(b) if b else 0.0
    cm = sum(c) / len(c) if c else 0.0
    point = {"type": "sovereignty_curve_point.v1", "port": port,
             "internal_mean": round(bm, 2), "external_mean": round(cm, 2),
             "cost_of_closing": round(bm - cm, 2), "n_tasks": len(task_suite),
             "measured_at": _now(), "law": "never assert; measure"}
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"curve_{port}.json").write_text(
            json.dumps(point, indent=2), encoding="utf-8")
    return point

def full_curve(task_suite, run_fn, configs: dict, out_dir: Path | None = None) -> dict:
    """configs: {"P1": {"internal": {...}, "external": {...}}, ...}"""
    return {p: measure_port_cost(task_suite, run_fn, c["internal"],
                                 c["external"], p, out_dir)
            for p, c in configs.items()}
