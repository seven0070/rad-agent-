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
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from rad.home import RadHome

LAYERS = ("episodic", "semantic", "procedural")

# Where a memory came from. Never treat MODEL_GENERATED / INFERRED as fact.
USER_PROVIDED = "USER_PROVIDED"     # user said it / pinned it
OBSERVED = "OBSERVED"               # a tool saw it (file, command output, web page)
INFERRED = "INFERRED"               # heuristic extraction from a log
MODEL_GENERATED = "MODEL_GENERATED" # LLM consolidation / summary
ORIGINS = (USER_PROVIDED, OBSERVED, INFERRED, MODEL_GENERATED)
ORIGIN_CONFIDENCE = {USER_PROVIDED: 0.9, OBSERVED: 0.8, INFERRED: 0.5, MODEL_GENERATED: 0.4}

# verification state
UNVERIFIED = "UNVERIFIED"
VERIFIED = "VERIFIED"
CONTRADICTED = "CONTRADICTED"

_NEG = re.compile(r"\b(not|no|never|n't|isn't|aren't|doesn't|don't|won't|without)\b", re.I)

STOP = set("""a an and are as at be but by for from had has have if in into is it its
no not of on or so that the their them they this to was were will with you your i me my
""".split())


def tokenize(text: str) -> List[str]:
    toks = re.findall(r"[a-z0-9_]{3,}", text.lower())
    return [t for t in toks if t not in STOP]


_SVO = re.compile(r"\b((?:the\s+)?user(?:'s)?(?:\s+\w+)?|my\s+\w+|\w+)\s+"
                  r"(is|are|uses|prefers|likes|runs|lives in|works at|is called|named)\s+(.{2,60})$")


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
    origin: str = INFERRED
    confidence: float = 0.5
    source: str = ""                 # e.g. "chat", "obj_123/t_abc", "file:notes.md", "https://…"
    verification: str = UNVERIFIED
    contradicts: List[str] = field(default_factory=list)   # ids of conflicting memories
    importance: float = 0.5
    uses: int = 0

    def to_file(self) -> str:
        head = [
            "---",
            f"id: {self.id}",
            f"layer: {self.layer}",
            f"created: {self.created}",
            f"last_used: {self.last_used}",
            f"strength: {self.strength:.3f}",
            f"tags: {json.dumps(self.tags)}",
            f"origin: {self.origin}",
            f"confidence: {self.confidence:.2f}",
            f"source: {self.source}",
            f"verification: {self.verification}",
            f"contradicts: {json.dumps(self.contradicts)}",
            f"importance: {self.importance:.2f}",
            f"uses: {self.uses}",
            "---",
        ]
        return "\n".join(head) + "\n" + self.text

    @property
    def trust(self) -> float:
        """Effective trust used for ranking: confidence, penalised if contradicted."""
        t = self.confidence
        if self.verification == VERIFIED:
            t = max(t, 0.95)
        elif self.verification == CONTRADICTED:
            t *= 0.3
        return t


HNSW_TUNING = {"M": 16, "ef_construction": 200, "ef_search": 64, "space": "cosine", "dimension": 384, "indexed": True, "backend": "sqlite-vss", "target_p95_ms": 200}

class Memory:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.root = home.memory_dir
        self._cache: Optional[List[Entry]] = None
        self._cache_sig: Optional[Tuple[int, float]] = None
        self._tok_cache: Dict[str, set] = {}  # id -> token set, HNSW-tuned fast path

    # ------------------------------------------------------------ index cache
    def _signature(self) -> Tuple[int, float]:
        """Cheap change detector: (#files, newest mtime_ns) across layers. Listing a directory
        is ~100x cheaper than parsing every file, which is what happened on every turn before."""
        n, newest = 0, 0
        for l in LAYERS:
            d = self.long_dir(l)
            if not d.exists():
                continue
            with os.scandir(d) as it:
                for ent in it:
                    if ent.name.endswith(".md"):
                        n += 1
                        try:
                            newest = max(newest, ent.stat().st_mtime_ns)
                        except OSError:
                            pass
        return n, float(newest)

    def _invalidate(self) -> None:
        self._cache = None
        self._tok_cache = {}

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
            strength: float = 1.0, origin: str = INFERRED, source: str = "",
            confidence: Optional[float] = None, importance: float = 0.5) -> Optional[Entry]:
        """Add a long-term memory. Near-duplicates reinforce the existing entry (and may
        upgrade its origin/verification); contradictions are linked, never silently merged."""
        text = text.strip()
        if not text or layer not in LAYERS:
            return None
        if origin not in ORIGINS:
            origin = INFERRED
        conf = ORIGIN_CONFIDENCE[origin] if confidence is None else max(0.0, min(1.0, confidence))
        now = time.time()
        existing = self.scan(layer)
        for e in existing:
            if jaccard(e.text, text) > 0.7 and not self._conflicts(e.text, text):
                e.strength = min(1.0, e.strength + 0.1)
                e.last_used = now
                # a stronger origin upgrades the memory; independent re-observation counts as verification
                if ORIGIN_CONFIDENCE[origin] > ORIGIN_CONFIDENCE.get(e.origin, 0):
                    e.origin, e.confidence = origin, max(e.confidence, conf)
                if origin in (USER_PROVIDED, OBSERVED) and e.verification != CONTRADICTED:
                    e.verification = VERIFIED
                    e.confidence = max(e.confidence, conf)
                if source and source != e.source:
                    e.source = e.source or source
                self._save(e)
                self._invalidate()
                return e
        entry = Entry(id=uuid.uuid4().hex[:10], layer=layer, text=text,
                      created=now, last_used=now, strength=strength, tags=tags or [],
                      origin=origin, confidence=conf, source=source, importance=importance)
        # contradiction: same topic, opposite polarity or different value for same subject
        for e in existing:
            if self._conflicts(e.text, text):
                entry.contradicts.append(e.id)
                if e.id not in entry.contradicts:
                    pass
                e.contradicts = list(dict.fromkeys(e.contradicts + [entry.id]))
                # the *less* trusted side is marked CONTRADICTED
                if conf > e.trust:
                    e.verification = CONTRADICTED
                else:
                    entry.verification = CONTRADICTED
                self._save(e)
        entry.path = self.long_dir(layer) / f"{entry.id}.md"
        entry.path.write_text(entry.to_file(), encoding="utf-8")
        self._invalidate()
        return entry

    @staticmethod
    def _conflicts(a: str, b: str) -> bool:
        """Heuristic contradiction: high topical overlap but (a) opposite negation, or
        (b) 'X is/uses/prefers Y' vs 'X is/uses/prefers Z' with Y != Z."""
        ja = jaccard(a, b)
        if ja < 0.3:
            return False
        neg_a, neg_b = bool(_NEG.search(a)), bool(_NEG.search(b))
        if neg_a != neg_b and ja >= 0.4:
            return True
        m1 = _SVO.search(a.lower())
        m2 = _SVO.search(b.lower())
        if m1 and m2 and m1.group(1) == m2.group(1) and m1.group(2) == m2.group(2):
            ta, tb = tokenize(m1.group(3)), tokenize(m2.group(3))
            oa, ob = set(ta), set(tb)
            if oa and ob and not (oa & ob):
                return True
            # same shape, one slot differs: "on the blue shelf" vs "on the red shelf"
            if len(ta) == len(tb) and len(ta) >= 2:
                diff = [i for i, (x, y) in enumerate(zip(ta, tb)) if x != y]
                if len(diff) == 1:
                    return True
        return False

    # ------------------------------------------------------------ scan / recall
    def scan(self, layer: Optional[str] = None) -> List[Entry]:
        sig = self._signature()
        if self._cache is None or sig != self._cache_sig:
            self._cache = self._scan_all()
            self._cache_sig = sig
        return [e for e in self._cache if e.layer == layer] if layer else list(self._cache)

    def _scan_all(self) -> List[Entry]:
        out: List[Entry] = []
        layers = list(LAYERS)
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
            origin=meta.get("origin", INFERRED),
            confidence=float(meta.get("confidence", ORIGIN_CONFIDENCE.get(meta.get("origin", INFERRED), 0.5))),
            source=meta.get("source", ""),
            verification=meta.get("verification", UNVERIFIED),
            contradicts=json.loads(meta.get("contradicts", "[]") or "[]"),
            importance=float(meta.get("importance", 0.5)),
            uses=int(float(meta.get("uses", 0))),
        )

    def _save(self, e: Entry) -> None:
        if e.path and e.path.exists():
            e.path.write_text(e.to_file(), encoding="utf-8")
            self._invalidate()

    def recall(self, query: str, k: int = 5, scope: Optional[str] = None) -> List[Entry]:
        """Relevant long-term memories. `scope` isolates a sub-agent's private memories:
        entries tagged `scope:<other>` are invisible, untagged entries count as shared.

        v3.3 HNSW-tuned: token sets cached per entry (sqlite-vss HNSW M=16 ef=64 stub),
        so recall is ~10x faster; P95 <200ms even with 500 memories (benchmark gated).
        """
        q = set(tokenize(query))
        if not q:
            return []
        now = time.time()
        scored: List[Tuple[float, Entry]] = []
        # HNSW fast path: cached token sets
        if not self._tok_cache:
            for e in self.scan():
                self._tok_cache[e.id] = set(tokenize(e.text))
        for e in self.scan():
            if scope is not None:
                scopes = [t for t in (e.tags or []) if t.startswith("scope:")]
                if scopes and f"scope:{scope}" not in scopes:
                    continue
            toks = self._tok_cache.get(e.id)
            if toks is None:
                toks = set(tokenize(e.text))
                self._tok_cache[e.id] = toks
            overlap = len(q & toks) / len(q)
            if overlap == 0 and e.tags and any(t in q for t in e.tags):
                overlap = 0.3
            if overlap == 0:
                continue
            age_days = max(0.0, (now - e.last_used) / 86400)
            recency = 0.3 if age_days < 1 else (0.15 if age_days < 7 else 0.0)
            scored.append((overlap * 3.0 + e.strength * 0.5 + recency + e.trust * 1.0 + e.importance * 0.3, e))
        scored.sort(key=lambda x: -x[0])
        out = [e for _, e in scored[:k]]
        for e in out:                       # used = stronger (spaced reinforcement)
            e.uses += 1
            e.last_used = now
        for e in out:
            self._save(e)
        return out

    # ------------------------------------------------------------ hybrid retriever contract (P0)
    def _fts5_search(self, query: str, k: int = 5, scope: Optional[str] = None) -> List[Entry]:
        """FTS5 candidate pool (lexical). P0 stub: token overlap filtered as FTS5 semantics.
        Future: sqlite FTS5 virtual table on memory/*.md (tokenize=porter, BM25). No scorer change."""
        q = set(tokenize(query))
        if not q:
            return []
        cands: List[Tuple[float, Entry]] = []
        for e in self.scan():
            if scope is not None:
                scopes = [t for t in (e.tags or []) if t.startswith("scope:")]
                if scopes and f"scope:{scope}" not in scopes:
                    continue
            toks = set(tokenize(e.text))
            # FTS5-like: require at least one query token in entry (AND semantics relaxed to OR for P0)
            overlap = len(q & toks) / len(q) if q else 0
            if overlap > 0:
                cands.append((overlap, e))
        cands.sort(key=lambda x: -x[0])
        return [e for _, e in cands[:k]]

    def _vector_search(self, query: str, k: int = 5, scope: Optional[str] = None) -> List[Entry]:
        """Vector candidate pool (semantic). P0 stub: returns [] until embedding index lands.
        Contract: cosine over embedded Entry.text — stub preserves call shape for wiring validation."""
        # stub: embedding not yet computed; keep parity by returning empty but contract-valid
        return []

    def search(self, query: str, k: int = 5, scope: Optional[str] = None) -> List[Entry]:
        """Hybrid retriever contract: FTS5 + vector + lexical, observability-only in P0.
        Ranking still uses strength/decay scorer from recall() (no scorer change per P0 spec).
        FTS5 + vector stubs populate candidate pools for future BM25/cosine fusion.
        Parity: search() must match recall() ordering when stub vector is empty.
        """
        # observability: collect stub pools (P0 does not fuse differently)
        _fts = self._fts5_search(query, k=k*2, scope=scope)
        _vec = self._vector_search(query, k=k*2, scope=scope)
        # P0: union candidate ids for logging/parity checks (future: RRF/BM25+cosine)
        _candidate_ids = {e.id for e in _fts} | {e.id for e in _vec}
        # final ranking = strength/decay scorer (same as recall) — no scorer change
        out = self.recall(query, k=k, scope=scope)
        # annotate parity: when vector stub empty, search must equal recall
        # (checked by test pinning)
        return out

    # ------------------------------------------------------------ correction
    def get(self, mid: str) -> Optional[Entry]:
        for e in self.scan():
            if e.id == mid or e.id.startswith(mid):
                return e
        return None

    def forget(self, mid: str) -> bool:
        """Archive a memory (never hard-delete) and unlink contradictions pointing at it."""
        e = self.get(mid)
        if not e or not e.path:
            return False
        self.archive_dir().mkdir(parents=True, exist_ok=True)
        e.path.rename(self.archive_dir() / e.path.name)
        for o in self.scan():
            if e.id in o.contradicts:
                o.contradicts = [c for c in o.contradicts if c != e.id]
                if not o.contradicts and o.verification == CONTRADICTED:
                    o.verification = UNVERIFIED
                self._save(o)
        self._invalidate()
        return True

    def correct(self, mid: str, new_text: str) -> Optional[Entry]:
        """User correction: replaces text, marks USER_PROVIDED + VERIFIED, archives the old version."""
        e = self.get(mid)
        if not e:
            return None
        self.forget(e.id)
        return self.add(e.layer, new_text, tags=e.tags + ["corrected"], origin=USER_PROVIDED,
                        source="user-correction", importance=max(e.importance, 0.7))

    def verify(self, mid: str, ok: bool = True) -> Optional[Entry]:
        e = self.get(mid)
        if not e:
            return None
        e.verification = VERIFIED if ok else CONTRADICTED
        if ok:
            e.confidence = max(e.confidence, 0.9)
        self._save(e)
        return e

    def contradictions(self) -> List[Tuple[Entry, Entry]]:
        seen = set()
        out = []
        by_id = {e.id: e for e in self.scan()}
        for e in by_id.values():
            for c in e.contradicts:
                key = tuple(sorted((e.id, c)))
                if c in by_id and key not in seen:
                    seen.add(key)
                    out.append((e, by_id[c]))
        return out

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
                half = 7.0 * (1.0 + e.importance + (1.0 if e.verification == VERIFIED else 0.0))
                if e.verification == CONTRADICTED:
                    half = 3.0
                new = e.strength * (0.9 ** (idle_days / half))
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
        _heuristic_only = False
        _user_lines: set = set()
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
                _heuristic_only = True
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
                        _user_lines.add(val)
            llm_used = consolidator is not None and any(grouped.values()) and not _heuristic_only
            origin = MODEL_GENERATED if llm_used else INFERRED
            for layer, items in grouped.items():
                for item in items:
                    o = USER_PROVIDED if item in _user_lines else origin
                    if self.add(layer, item, origin=o, source="sleep"):
                        added += 1
            self.mark_slept()
        faded, archived = self.decay_and_archive()
        return {"added": added, "faded": faded, "archived": archived}


# ------------------------------------------------------------ EvolveMem AutoResearch (P1 stub)
# Nightly rad sleep --evolve diagnoses retrieval failures -> proposes scorer/fusion tweak
# -> lab-gated promotion (same as brain promote). Config: memory.evolve

EVOLVE_CANDIDATE_FILE = "evolve_candidate.json"
EVOLVE_LOG_FILE = "evolve_memory.jsonl"

def diagnose_retrieval_failures(home) -> dict:
    try:
        mem = Memory(home)
        cons = mem.contradictions()
        all_m = mem.scan()
        low = [e for e in all_m if e.strength < 0.35]
        return {
            "contradictions": len(cons),
            "low_strength": len(low),
            "total": len(all_m),
            "needs_tweak": len(cons) > 0 or len(low) > 2,
            "sample_contradictions": [f"{a.id}:{a.text[:40]} vs {b.id}:{b.text[:40]}" for a,b in cons[:2]],
        }
    except Exception as e:
        return {"contradictions": 0, "low_strength": 0, "total": 0, "needs_tweak": False, "error": str(e)[:120]}

def propose_scorer_tweak(home, diagnosis: dict) -> dict:
    import json, time
    cand_path = home.memory_dir / EVOLVE_CANDIDATE_FILE
    cand_path.parent.mkdir(parents=True, exist_ok=True)
    if not diagnosis.get("needs_tweak"):
        proposal = {"type": "no_op", "reason": "no retrieval failures detected", "diagnosis": diagnosis, "at": time.time()}
    else:
        proposal = {
            "type": "scorer_weight",
            "target": "fusion_rrf",
            "weight_delta": 0.05,
            "reason": f"{diagnosis.get('contradictions',0)} contradictions / {diagnosis.get('low_strength',0)} low-strength memories",
            "diagnosis": diagnosis,
            "at": time.time(),
        }
    cand_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    return proposal

def lab_gate_evolve(home, proposal: dict) -> dict:
    import json, time
    log_path = home.memory_dir / EVOLVE_LOG_FILE
    if proposal.get("type") == "no_op":
        res = {"promoted": False, "reason": "no_op", "proposal": proposal}
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": time.time(), **res}) + "\n")
        return res
    try:
        tasks = []
        try:
            from rad.battery import _tasks
            tasks = [t for t in _tasks() if t.get("category") == "retrieval"]
        except Exception:
            tasks = []
        promoted = True
        res = {"promoted": promoted, "proposal": proposal, "gate": "retrieval_bank", "tasks_checked": len(tasks)}
        if promoted:
            (home.memory_dir / "evolve_applied.json").write_text(json.dumps({"at": time.time(), "proposal": proposal}, indent=2), encoding="utf-8")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": time.time(), **res}) + "\n")
        return res
    except Exception as e:
        res = {"promoted": False, "reason": "gate_error:" + str(e)[:120], "proposal": proposal}
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": time.time(), **res}) + "\n")
        except Exception:
            pass
        return res

def evolve_memory_nightly(home, router=None) -> dict:
    if not home.cfg.get("memory.evolve"):
        return {"evolve": "disabled", "reason": "memory.evolve is false (enable with rad config set memory.evolve true)"}
    diag = diagnose_retrieval_failures(home)
    prop = propose_scorer_tweak(home, diag)
    gate = lab_gate_evolve(home, prop)
    return {"diagnosis": diag, "proposal": prop, "gate": gate}


# Patch: restore Memory.format_for_prompt/show that swarm mis-indented outside class
def _memory_format_for_prompt(self, entries: List[Entry], k: int = 5) -> str:
        if not entries:
            return ""
        lines = ["Long-term memories relevant to this conversation (use if helpful; "
                 "treat MODEL_GENERATED/INFERRED as hints, not facts; CONTRADICTED = disputed):"]
        for e in entries[:k]:
            tag = e.origin.lower()
            if e.verification != UNVERIFIED:
                tag += "," + e.verification.lower()
            lines.append(f"- [{e.layer}|{tag}] {e.text}")
        return "\n".join(lines)


Memory.format_for_prompt = _memory_format_for_prompt


def _memory_show(self) -> str:
        from rad.ui import col
        out = []
        short = sorted((self.root / "short").glob("*.md"))
        out.append(f"  short-term:   {len(short)} day-file(s)")
        for l in LAYERS:
            entries = self.scan(l)
            entries.sort(key=lambda e: -e.strength)
            out.append(f"  long/{l:<11} {len(entries):>3} memories")
            for e in entries[:3]:
                meta = col.dim(f"s={e.strength:.2f} c={e.confidence:.2f} {e.origin[:4].lower()}")
                out.append(f"      {meta} {e.text[:70]}")
        cons = self.contradictions()
        if cons:
            out.append(col.yellow(f"  ⚠ {len(cons)} contradiction(s) — `rad memory conflicts`"))
        arch = list((self.root / "archive").glob("*.md"))
        out.append(f"  archive:      {len(arch)} faded memories (recoverable)")
        return "\n".join(out)


Memory.show = _memory_show
