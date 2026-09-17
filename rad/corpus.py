"""Corpus miner — Rad's experience becomes training data.

Mines short-term session logs + DNA feedback into (input, output) pairs:
  praised    — a 👍 followed the reply          (SFT positive)
  correction — a 👎 + your fix followed         (preference/correction data)
  normal     — everything else                  (SFT base, low weight)

Output is plain JSONL — feed it to ANY trainer (MLX-LM, Unsloth, PEFT, or a
rented GPU). Rad's promotion loop (brains.py) is trainer-agnostic: train
wherever, bring the adapter back, get benchmarked before it may take the throne.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from rad.home import RadHome

LINE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\] (user|rad|session): (.+)$")
CORRECTION_START = re.compile(r"^(no,|no |actually|wait,|wait |i meant|correction:|instead,?|more like)", re.I)
MIN_LEN = 20  # skip trivial acks from the normal pool


class Corpus:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.dir = home.root / "corpus"
        self.dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------ mining
    def _feedbacks(self) -> List[Dict[str, Any]]:
        try:
            from rad.dna import Evolver
            return Evolver(self.home).load().get("feedback", [])
        except Exception:
            return []

    def mine(self) -> List[Dict[str, Any]]:
        """Scan short-term logs → pairs. No LLM required."""
        fb = self._feedbacks()
        pairs: List[Dict[str, Any]] = []
        short_dir = self.home.memory_dir / "short"
        for p in sorted(short_dir.glob("*.md")):
            day = p.stem
            lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            pending_user: Optional[str] = None
            last_rad_ts: Optional[float] = None
            for line in lines:
                m = LINE.match(line.strip())
                if not m:
                    continue
                ts, who, body = m.group(1), m.group(2), m.group(3)
                try:
                    epoch = _hms_to_epoch(day, ts)
                except Exception:
                    epoch = time.time()
                if who == "user":
                    pending_user = body
                    last_rad_ts = None
                elif who == "rad" and pending_user is not None:
                    quality = "normal"
                    for f in fb:
                        if abs(f.get("at", 0) - epoch) < 300:
                            if f["kind"] == "bad":
                                quality = "correction"
                            elif f["kind"] == "good" and quality == "normal":
                                quality = "praised"
                    # user correction in the very next user line is handled on next iteration;
                    # here we also catch inline corrections in the reply itself
                    if pending_user and CORRECTION_START.match(pending_user) and quality == "normal":
                        quality = "correction"
                    out = body.strip()
                    if len(out) < MIN_LEN and quality == "normal":
                        pending_user = None
                        continue
                    h = hashlib.sha1((pending_user + out).encode()).hexdigest()[:12]
                    pairs.append({
                        "id": h, "day": day, "ts": ts,
                        "input": pending_user, "output": out,
                        "quality": quality, "source": "short-log",
                    })
                    pending_user = None
                    last_rad_ts = epoch
        return pairs

    # ------------------------------------------------------------ stats / export
    def stats(self) -> Dict[str, int]:
        pairs = self.mine()
        s = {"total": len(pairs), "praised": 0, "correction": 0, "normal": 0}
        for p in pairs:
            s[p["quality"]] = s.get(p["quality"], 0) + 1
        return s

    def export(self, path: Optional[str] = None) -> str:
        pairs = self.mine()
        dest = Path(path) if path else self.dir / f"pairs-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
        with open(dest, "w", encoding="utf-8") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False) + "\n")
        return str(dest)

    # ------------------------------------------------------------ LLM assist (optional)
    def score_with_brain(self, caller: Callable[[str], str], limit: int = 40) -> int:
        """Best-effort: ask an online brain to rate normal pairs. Returns # upgraded."""
        pairs = [p for p in self.mine() if p["quality"] == "normal"][:limit]
        if not pairs:
            return 0
        block = "\n---\n".join(f"Q: {p['input'][:300]}\nA: {p['output'][:300]}" for p in pairs)
        prompt = (
            "Rate each Q/A pair for a personal agent as 1 (useful, correct, well-styled) or 0 (weak/wrong). "
            f"Reply with ONLY a comma-separated list of {len(pairs)} digits, no other text.\n\n{block}"
        )
        try:
            raw = caller(prompt)
            digits = re.findall(r"\d", raw)
            if len(digits) < len(pairs):
                return 0
            upgraded = 0
            dest = self.dir / "scored.jsonl"
            with open(dest, "a", encoding="utf-8") as f:
                for p, d in zip(pairs, digits[:len(pairs)]):
                    if d == "1" and p["quality"] == "normal":
                        p = dict(p)
                        p["quality"] = "praised"
                        upgraded += 1
                    f.write(json.dumps(p, ensure_ascii=False) + "\n")
            return upgraded
        except Exception:
            return 0

    def show(self) -> str:
        from rad.ui import col
        s = self.stats()
        out = [
            f"  total pairs:  {s['total']}",
            f"  {col.green('praised')}   {s.get('praised', 0)}     (👍 after reply)",
            f"  {col.yellow('correction')}{str(s.get('correction', 0)).rjust(4)}     (👎 + your fix)",
            f"  normal       {s.get('normal', 0)}",
            col.dim("  export: rad corpus export [--out file.jsonl]"),
        ]
        return "\n".join(out)


def _hms_to_epoch(day: str, hms: str) -> float:
    from datetime import datetime
    return datetime.strptime(f"{day} {hms}", "%Y-%m-%d %H:%M:%S").timestamp()
