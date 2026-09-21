"""Contamination detector — bidirectional firewall (RFC-003 M1).

Forward: corpus too similar to battery items -> promotion blocked.
Pure functions. Deterministic. No network, no model.

CONTRACT: overlap_score returns jaccard/theft rounded to 4 decimals;
verdict thresholds compared against the UNROUNDED values.
"""
import json, re
from pathlib import Path

N_GRAM_SIZE = 8
DEFAULT_THRESHOLD = 0.15

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def _ngrams(text: str, n: int = N_GRAM_SIZE) -> set:
    words = _normalize(text).split()
    if not words:
        return set()
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}

def _collect_text(path: Path) -> str:
    """Extract all text from .jsonl/.json/.md/.txt — text-agnostic walk."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl":
        parts = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                parts.append(line)
                continue
            parts.append(_walk_strings(obj))
        return " ".join(parts)
    if path.suffix == ".json":
        try:
            return _walk_strings(json.loads(raw))
        except json.JSONDecodeError:
            return raw
    return raw

def _walk_strings(o) -> str:
    parts = []
    if isinstance(o, str):
        parts.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            parts.append(_walk_strings(v))
    elif isinstance(o, list):
        for v in o:
            parts.append(_walk_strings(v))
    return " ".join(parts)

def _grams_from_dir(d: Path) -> set:
    grams = set()
    if not d.exists():
        return grams
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.suffix in {".jsonl", ".json", ".md", ".txt"}:
            grams |= _ngrams(_collect_text(f))
    return grams

def overlap_score(corpus_dir: Path, battery_dir: Path,
                  threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Verdict: 'blocked' if jaccard OR battery-theft >= threshold.
    Rounded to 4dp for display; threshold check uses unrounded."""
    corpus_grams = _grams_from_dir(corpus_dir)
    battery_grams = _grams_from_dir(battery_dir)
    if not corpus_grams or not battery_grams:
        return _verdict(0.0, 0.0, threshold, "insufficient_data",
                        len(corpus_grams), len(battery_grams))
    inter = corpus_grams & battery_grams
    jaccard = len(inter) / len(corpus_grams | battery_grams)
    theft = len(inter) / len(battery_grams)
    status = "blocked" if (jaccard >= threshold or theft >= threshold) else "pass"
    return _verdict(jaccard, theft, threshold, status,
                    len(corpus_grams), len(battery_grams))

def _verdict(j, t, threshold, status, nc, nb) -> dict:
    return {"check": "contamination_firewall",
            "jaccard": round(j, 4),           # display rounding: 4dp (L2)
            "battery_theft_ratio": round(t, 4),
            "threshold": threshold, "verdict": status,
            "corpus_grams": nc, "battery_grams": nb,
            "note": ("promotion BLOCKED — rotate battery items (RFC-003 M2)"
                     if status == "blocked" else
                     "overlap within tolerance" if status == "pass" else
                     "one or both dirs empty/unreadable")}
