"""Rad's mind — layered memory, human-inspired.

    sensory (RAM, this turn)  →  working (RAM, this task)
    →  short-term (disk, days, decays)
    →  long-term:  episodic (events) · semantic (facts) · procedural (skills)

Every long-term memory is a markdown file with a strength score.
Used = stronger. Unused = fades. Faded = archived (never hard-deleted).
`sleep()` consolidates short-term into long-term and prunes — Rad's nightly sleep.
"""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from rad.home import RadHome

LAYERS = ("episodic", "semantic", "procedural")

STOP = set("""a an and are as at be but by for from had has have if in into is it its
no not of on or so that the their them they this to was were will with you your i me my
""".split())


def tokenize(text: str) -> List[str]:
    toks = re.findall(r"[a-z0-9_]{3,}", text.lower())
    return [t for t in toks if t not in STOP]


def jaccard(a: str, b: str) -> float:
    sa, sb = set(tokenize(a)), set(tokenize(b))
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


@dataclass
class Entry:
    id: str
    layer: str
    text: str
    created: float
    last_used: float
    strength: float = 1.0
    tags: List[str] = field(default_factory=list)
    path: Optional[Path] = None

    def to_file(self) -> str:
        head = [
            "---",
            f"id: {self.id}",
            f"layer: {self.layer}",
            f"created: {self.created}",
            f"last_used: {self.last_used}",
            f"strength: {self.strength:.3f}",
            f"tags: {json.dumps(self.tags)}",
            "---",
        ]
        return "\n".join(head) + "\n" + self.text


class Memory:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.root = home.memory_dir

    # ------------------------------------------------------------ paths
    def long_dir(self, layer: str) -> Path:
        return self.root / "long" / layer

    def archive_dir(self) -> Path:
        return self.root / "archive"

    def short_path(self, day: Optional[str] = None) -> Path:
        day = day or time.strftime("%Y-%m-%d")
        return self.root / "short" / f"{day}.md"

    def short_meta(self) -> Dict[str, float]:
        p = self.root / "short" / ".meta.json"
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}

    def _set_short_meta(self, m: Dict[str, float]) -> None:
        (self.root / "short" / ".meta.json").write_text(json.dumps(m))

    # ------------------------------------------------------------ add
    def add(self, layer: str, text: str, tags: Optional[List[str]] = None,
            strength: float = 1.0) -> Optional[Entry]:
        """Add a long-term memory. Returns None if it duplicates an existing one."""
        text = text.strip()
        if not text or layer not in LAYERS:
            return None
        for e in self.scan(layer):
            if jaccard(e.text, text) > 0.7:
                e.strength = min(1.0, e.strength + 0.1)
                e.last_used = time.time()
                self._save(e)
                return e
        now = time.time()
        entry = Entry(id=uuid.uuid4().hex[:10], layer=layer, text=text,
                      created=now, last_used=now, strength=strength, tags=tags or [])
        entry.path = self.long_dir(layer) / f"{entry.id}.md"
        entry.path.write_text(entry.to_file(), encoding="utf-8")
        return entry

    # ------------------------------------------------------------ scan / recall
    def scan(self, layer: Optional[str] = None) -> List[Entry]:
        out: List[Entry] = []
        layers = [layer] if layer else list(LAYERS)
        for l in layers:
            d = self.long_dir(l)
            if not d.exists():
                continue
            for p in sorted(d.glob("*.md")):
                try:
                    e = self._parse(p)
                    if e:
                        out.append(e)
                except Exception:
                    continue
        return out

    def _parse(self, path: Path) -> Optional[Entry]:
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", raw, re.S)
        if not m:
            return None
        meta: Dict[str, str] = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        return Entry(
            id=meta.get("id", path.stem), layer=meta.get("layer", path.parent.name),
            text=m.group(2).strip(),
            created=float(meta.get("created", 0)), last_used=float(meta.get("last_used", 0)),
            strength=float(meta.get("strength", 1.0)),
            tags=json.loads(meta.get("tags", "[]")), path=path,
        )

    def _save(self, e: Entry) -> None:
        if e.path and e.path.exists():
            e.path.write_text(e.to_file(), encoding="utf-8")

    def recall(self, query: str, k: int = 5) -> List[Entry]:
        q = set(tokenize(query))
        if not q:
            return []
        now = time.time()
        scored: List[Tuple[float, Entry]] = []
        for e in self.scan():
            toks = set(tokenize(e.text))
            overlap = len(q & toks) / len(q)
            if overlap == 0 and e.tags and any(t in q for t in e.tags):
                overlap = 0.3
            if overlap == 0:
                continue
            age_days = max(0.0, (now - e.last_used) / 86400)
            recency = 0.3 if age_days < 1 else (0.15 if age_days < 7 else 0.0)
            scored.append((overlap * 3.0 + e.strength * 0.5 + recency, e))
        scored.sort(key=lambda x: -x[0])
        return [e for _, e in scored[:k]]

    def boost(self, e: Entry) -> None:
        e.strength = min(1.0, e.strength + 0.1)
        e.last_used = time.time()
        self._save(e)

    # ------------------------------------------------------------ decay / archive
    def decay_and_archive(self, threshold: float = 0.25) -> Tuple[int, int]:
        faded = archived = 0
        now = time.time()
        for e in self.scan():
            idle_days = max(0.0, (now - e.last_used) / 86400)
            if idle_days > 7:
                new = e.strength * (0.9 ** (idle_days / 7.0))
                if new < threshold:
                    dest = self.archive_dir() / f"{e.layer}-{e.id}.md"
                    e.path.rename(dest)
                    e.path = None
                    archived += 1
                else:
                    e.strength = new
                    faded += 1
                    self._save(e)
        return faded, archived

    # ------------------------------------------------------------ short-term
    def session_log(self, who: str, text: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {who}: {text.strip()}\n"
        p = self.short_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(line)

    def unslept_short_text(self) -> str:
        meta = self.short_meta()
        parts = []
        for p in sorted((self.root / "short").glob("*.md")):
            day = p.stem
            slept = meta.get(day, 0.0)
            slept_hms = time.strftime("%H:%M:%S", time.localtime(slept)) if slept else "00:00:00"
            lines = []
            for line in p.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\[(\d{2}:\d{2}:\d{2})\]", line)
                if m and m.group(1) > slept_hms:
                    lines.append(line)
            if lines:
                parts.append(f"== day {day} ==\n" + "\n".join(lines))
        return "\n".join(parts).strip()

    def mark_slept(self, at: Optional[float] = None) -> None:
        meta = self.short_meta()
        now = at if at is not None else time.time()
        for p in (self.root / "short").glob("*.md"):
            meta[p.stem] = now
        self._set_short_meta(meta)

    # ------------------------------------------------------------ sleep
    def sleep(self, consolidator: Optional[Callable[[str], Optional[Dict[str, List[str]]]]] = None) -> Dict[str, int]:
        """Consolidate: short-term → long-term, then decay + archive.

        `consolidator` is an optional LLM-backed fn(text) -> {"episodic": [...],
        "semantic": [...], "procedural": [...]}. Without it, marker heuristics are used.
        """
        text = self.unslept_short_text()
        added = 0
        if text:
            grouped: Dict[str, List[str]] = {"episodic": [], "semantic": [], "procedural": []}
            if consolidator is not None:
                try:
                    out = consolidator(text)
                    if isinstance(out, dict):
                        for k in grouped:
                            grouped[k] = [str(x).strip() for x in (out.get(k) or []) if str(x).strip()][:8]
                except Exception:
                    out = None
            if not any(grouped.values()):
                for line in text.splitlines():
                    m = re.match(r"^\[.*?\] (user|rad): (.+)$", line.strip())
                    if not m:
                        continue
                    body = m.group(2)
                    mm = re.match(r"^(remember|fact|skill)\s*:\s*(.+)$", body, re.I)
                    if not mm:
                        continue
                    kind, val = mm.group(1).lower(), mm.group(2).strip()
                    layer = {"remember": "semantic", "fact": "semantic", "skill": "procedural"}[kind]
                    if val and val not in grouped[layer]:
                        grouped[layer].append(val)
            for layer, items in grouped.items():
                for item in items:
                    if self.add(layer, item):
                        added += 1
            self.mark_slept()
        faded, archived = self.decay_and_archive()
        return {"added": added, "faded": faded, "archived": archived}

    # ------------------------------------------------------------ show
    def format_for_prompt(self, entries: List[Entry], k: int = 5) -> str:
        if not entries:
            return ""
        lines = ["Long-term memories relevant to this conversation (use if helpful):"]
        for e in entries[:k]:
            lines.append(f"- [{e.layer}] {e.text}")
        return "\n".join(lines)

    def show(self) -> str:
        from rad.ui import col
        out = []
        short = sorted((self.root / "short").glob("*.md"))
        out.append(f"  short-term:   {len(short)} day-file(s)")
        for l in LAYERS:
            entries = self.scan(l)
            entries.sort(key=lambda e: -e.strength)
            out.append(f"  long/{l:<11} {len(entries):>3} memories")
            for e in entries[:3]:
                out.append(f"      {col.dim(f's={e.strength:.2f}')} {e.text[:70]}")
        arch = list((self.root / "archive").glob("*.md"))
        out.append(f"  archive:      {len(arch)} faded memories (recoverable)")
        return "\n".join(out)
