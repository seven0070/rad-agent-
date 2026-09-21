"""Telemetry — cost truth v0: token/time accounting through any brain_fn.

Unparked because Battle #5 showed 63s anomalies nobody could explain.
Counts are ESTIMATES (chars/4 heuristic) until provider usage lands —
labeled estimate forever, per the honesty bar.

CONTRACT: stats object is plain-dict serializable; wrap() never alters
the brain's return value.
"""
import time
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def _est_tokens(s: str) -> int:
    return max(1, len(s) // 4)


class BrainStats(dict):
    def __init__(self):
        super().__init__(calls=0, prompt_chars=0, reply_chars=0,
                         est_prompt_tokens=0, est_reply_tokens=0,
                         wall_s=0.0, started=_now())


def wrap(brain_fn):
    """Wrap a brain_fn; returns (wrapped, stats). Same signature, same return."""
    stats = BrainStats()

    def wrapped(prompt: str, *a, **k):
        t0 = time.monotonic()
        out = brain_fn(prompt, *a, **k)
        dt = time.monotonic() - t0
        stats["calls"] += 1
        stats["prompt_chars"] += len(prompt)
        stats["reply_chars"] += len(str(out))
        stats["est_prompt_tokens"] += _est_tokens(prompt)
        stats["est_reply_tokens"] += _est_tokens(str(out))
        stats["wall_s"] = round(stats["wall_s"] + dt, 3)
        return out

    return wrapped, stats


def attach_to_result(result: dict, stats: BrainStats) -> dict:
    """Pin brain telemetry into a battle result — observational, claim-neutral."""
    result["brain_telemetry"] = dict(stats)
    result["cost_note"] = ("est_tokens are chars/4 estimates; provider usage "
                           "replaces them when wired (honesty bar)")
    return result
