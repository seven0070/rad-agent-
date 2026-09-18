"""Model selection — task-aware routing that keeps the free-first law.

`rad.router` knows *which* brains are available and in what order (local → free →
paid). This module answers the second question: **which brain is right for this
task?** A coding task with a 200-line context and tool calls has different needs
from a vision question or a cheap summarisation.

    task  →  requirements  →  capability profiles  →  ranked chain  →  fallback

Profiles come from three sources, in increasing priority:

  1. built-in defaults for known providers (tier, vision, context, price)
  2. `~/.rad/models.json` — your own overrides (`rad models set …`)
  3. recorded evaluation results — `rad evaluate` scores feed the ranking, so a
     model that measurably regressed stops being preferred.

Free-first is never violated: requirements only reorder *within* a tier; a paid
model is never promoted above a working free/local one unless the user asked for
it explicitly (`privacy`, `allow_paid`, or a `prefer` list).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from rad.home import RadHome, _read_json, _write_json

# ------------------------------------------------------------------ capability vocabulary

CAP_REASONING = "reasoning"
CAP_CODING = "coding"
CAP_PLANNING = "planning"
CAP_TOOLS = "tools"
CAP_VISION = "vision"
CAP_LONG = "long_context"
CAP_STRUCTURED = "structured"
CAP_RESEARCH = "research"
CAP_SPEED = "speed"
CAP_CHEAP = "cheap"
CAP_PRIVATE = "private"

CAPS = (CAP_REASONING, CAP_CODING, CAP_PLANNING, CAP_TOOLS, CAP_VISION, CAP_LONG,
        CAP_STRUCTURED, CAP_RESEARCH, CAP_SPEED, CAP_CHEAP, CAP_PRIVATE)

TASK_KINDS: Dict[str, Dict[str, Any]] = {
    "chat":        {"caps": [CAP_SPEED, CAP_CHEAP], "min_context": 8_000},
    "plan":        {"caps": [CAP_REASONING, CAP_PLANNING, CAP_STRUCTURED], "min_context": 16_000},
    "research":    {"caps": [CAP_REASONING, CAP_RESEARCH, CAP_LONG, CAP_TOOLS], "min_context": 32_000},
    "code":        {"caps": [CAP_CODING, CAP_TOOLS, CAP_REASONING], "min_context": 32_000},
    "review":      {"caps": [CAP_REASONING, CAP_CODING, CAP_LONG], "min_context": 32_000},
    "vision":      {"caps": [CAP_VISION], "min_context": 4_000},
    "summarize":   {"caps": [CAP_SPEED, CAP_CHEAP, CAP_LONG], "min_context": 16_000},
    "extract":     {"caps": [CAP_STRUCTURED, CAP_SPEED], "min_context": 8_000},
    "verify":      {"caps": [CAP_REASONING, CAP_STRUCTURED], "min_context": 8_000},
}

TIER_RANK = {"local": 0, "free": 1, "paid": 2}


@dataclass
class Requirements:
    kind: str = "chat"
    need_tools: bool = False
    need_vision: bool = False
    min_context: int = 0
    privacy: str = ""                       # "local" = only local models
    prefer: List[str] = field(default_factory=list)      # provider names to try first
    avoid: List[str] = field(default_factory=list)
    allow_paid: bool = True
    max_output_price: float = 0.0           # USD / 1k output tokens (0 = any)
    max_latency: int = 0                    # seconds (0 = any)
    label: str = ""                         # who asked (for the event log)

    def caps(self) -> List[str]:
        return list(TASK_KINDS.get(self.kind, TASK_KINDS["chat"])["caps"])

    def context(self) -> int:
        return max(self.min_context, int(TASK_KINDS.get(self.kind, {}).get("min_context", 0)))

    @classmethod
    def for_task_text(cls, text: str, **kw: Any) -> "Requirements":
        """Cheap deterministic classification of a task description."""
        low = (text or "").lower()
        kind = "chat"
        if any(w in low for w in ("image", "screenshot", "photo", "picture", "vision")):
            kind = "vision"
        elif any(w in low for w in ("code", "implement", "function", "bug", "refactor", "script", "python", "test")):
            kind = "code"
        elif any(w in low for w in ("research", "investigate", "sources", "cross-check", "compare sources", "web")):
            kind = "research"
        elif any(w in low for w in ("plan", "decompose", "roadmap", "break down", "steps")):
            kind = "plan"
        elif any(w in low for w in ("summar", "tl;dr", "condense")):
            kind = "summarize"
        elif any(w in low for w in ("extract", "parse", "json", "schema")):
            kind = "extract"
        elif any(w in low for w in ("verify", "audit", "check that", "review")):
            kind = "verify"
        return cls(kind=kind, need_tools=any(w in low for w in ("file", "run", "shell", "tool", "create", "write")),
                   **kw)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "need_tools": self.need_tools, "need_vision": self.need_vision,
                "min_context": self.context(), "privacy": self.privacy, "prefer": list(self.prefer),
                "avoid": list(self.avoid), "allow_paid": self.allow_paid,
                "max_output_price": self.max_output_price, "label": self.label}


@dataclass
class ModelProfile:
    provider: str
    model: str = ""
    tier: str = "paid"                      # local | free | paid
    context: int = 0                        # 0 = unknown (never used to filter)
    vision: bool = False
    tools: bool = True
    prices: Tuple[float, float] = (0.0, 0.0)     # per 1k tokens (in, out)
    latency_s: float = 3.0
    scores: Dict[str, float] = field(default_factory=dict)   # measured 0..1
    note: str = ""

    # ---- derived
    @property
    def local(self) -> bool:
        return self.tier == "local"

    def caps(self) -> List[str]:
        c: List[str] = [CAP_TOOLS] if self.tools else []
        if self.vision:
            c.append(CAP_VISION)
        if self.context >= 32_000:
            c.append(CAP_LONG)
        if self.tier == "local":
            c += [CAP_PRIVATE, CAP_CHEAP]
        if self.tier == "free":
            c.append(CAP_CHEAP)
        if self.latency_s <= 2.0:
            c.append(CAP_SPEED)
        c += [k for k, v in self.scores.items() if v >= 0.7]
        return sorted(set(c))

    def score_for(self, caps: Sequence[str]) -> float:
        """0..1 fit score for a requirement set (measured scores dominate heuristics)."""
        want = [c for c in caps if c not in (CAP_SPEED, CAP_CHEAP, CAP_PRIVATE)]
        base = {"reasoning": 0.55, "coding": 0.5, "planning": 0.5, "tools": 0.5,
                "research": 0.5, "long_context": 0.5, "structured": 0.5}.get
        total, n = 0.0, 0
        have = set(self.caps())
        for c in want:
            n += 1
            measured = self.scores.get(c)
            if measured is not None:
                total += measured
            elif c in have:
                total += base(c, 0.5)
            else:
                total += 0.15
        if CAP_CHEAP in caps and self.tier in ("free", "local"):
            total += 0.2
            n += 1
        if CAP_SPEED in caps:
            total += max(0.0, 1.0 - min(self.latency_s, 20.0) / 20.0)
            n += 1
        if CAP_PRIVATE in caps and self.local:
            total += 1.0
            n += 1
        return round(total / n, 4) if n else 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {"provider": self.provider, "model": self.model, "tier": self.tier,
                "context": self.context, "vision": self.vision, "tools": self.tools,
                "prices": list(self.prices), "latency_s": self.latency_s,
                "scores": dict(self.scores), "note": self.note, "caps": self.caps()}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModelProfile":
        return cls(provider=d.get("provider", "?"), model=d.get("model", ""), tier=d.get("tier", "paid"),
                   context=int(d.get("context", 0) or 0), vision=bool(d.get("vision", False)),
                   tools=bool(d.get("tools", True)), prices=tuple(d.get("prices", (0.0, 0.0)))[:2],  # type: ignore[arg-type]
                   latency_s=float(d.get("latency_s", 3.0)), scores=dict(d.get("scores", {})),
                   note=d.get("note", ""))


# ------------------------------------------------------------------ registry

def _default_profiles(home: RadHome) -> Dict[str, ModelProfile]:
    """Profiles for every provider RAD can currently see, with sensible heuristics."""
    out: Dict[str, ModelProfile] = {}
    try:
        from rad import providers as P
        specs = P.all_specs(home)
    except Exception:
        specs = []
    for spec in specs:
        prices = (0.0, 0.0)
        try:
            prices = tuple(P.spec_by_name.get(spec.name, (0.0, 0.0)))
        except Exception:
            pass
        tier = spec.tier
        latency = 1.2 if spec.local else (2.0 if tier == "free" else 3.5)
        scores: Dict[str, float] = {}
        name = (spec.name or "").lower()
        if any(k in name for k in ("claude", "gpt-4", "gpt-4o", "gemini", "deepseek", "qwen", "nvidia", "groq", "cerebras", "mistral")):
            scores = {"reasoning": 0.75, "coding": 0.7, "planning": 0.7, "structured": 0.7, "tools": 0.75}
        if spec.local:
            scores = {k: min(v, 0.6) for k, v in (scores or {"reasoning": 0.55, "coding": 0.55}).items()}
        out[spec.name] = ModelProfile(provider=spec.name, model=spec.default_model or "", tier=tier,
                                      context=int(getattr(spec, "context", 0) or (32_000 if spec.local else 128_000)),
                                      vision=bool(getattr(spec, "supports_vision", False)),
                                      prices=prices, latency_s=latency, scores=scores)  # type: ignore[arg-type]
    return out


class ModelRegistry:
    MODEL_CLASSES = ("small", "medium", "large", "reasoning")

    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.path = home.root / "models.json"
        self._profiles: Optional[Dict[str, ModelProfile]] = None

    # ---- load/save
    def profiles(self, refresh: bool = False) -> Dict[str, ModelProfile]:
        if self._profiles is not None and not refresh:
            return self._profiles
        out = _default_profiles(self.home)
        for name, d in (_read_json(self.path, {}) or {}).items():
            base = out.get(name)
            merged = {**(base.to_dict() if base else {}), **d, "provider": name}
            out[name] = ModelProfile.from_dict(merged)
        # measured scores from the evaluation history override the guesses
        for name, scores in self.evaluation_scores().items():
            if name in out:
                out[name].scores.update({k: v for k, v in scores.items() if isinstance(v, (int, float))})
        self._profiles = out
        return out

    def get(self, provider: str) -> Optional[ModelProfile]:
        return self.profiles().get(provider)

    def set(self, provider: str, **fields: Any) -> ModelProfile:
        d = _read_json(self.path, {}) or {}
        cur = d.get(provider, {})
        cur.update({k: v for k, v in fields.items() if v is not None})
        d[provider] = cur
        _write_json(self.path, d)
        self._profiles = None
        return self.profiles(refresh=True)[provider]

    def evaluation_scores(self) -> Dict[str, Dict[str, float]]:
        """Per-provider capability scores from recorded evaluations (0..1)."""
        hist = _read_json(self.home.root / "evaluation" / "history.json", []) or []
        by: Dict[str, Dict[str, List[float]]] = {}
        for run in hist:
            prov = run.get("provider") or run.get("label", "")
            for cat, score in (run.get("categories") or {}).items():
                by.setdefault(prov, {}).setdefault(cat, []).append(float(score) / 100.0)
        return {p: {c: round(sum(v) / len(v), 3) for c, v in cats.items()} for p, cats in by.items()}

    # ---- selection
    def select(self, entries: Iterable[Any], req: Requirements) -> List[Any]:
        """Order an available chain (`rad.router.ChainEntry`) for a requirement set.

        Filters: vision, context, privacy, cost, avoid. Ranking: tier first
        (free-first is law), then fit score, then latency.
        """
        caps = req.caps() + ([CAP_TOOLS] if req.need_tools else [])
        if req.need_vision or req.kind == "vision":
            caps.append(CAP_VISION)
        if req.privacy == "local":
            caps.append(CAP_PRIVATE)
        ranked: List[Tuple[Tuple[int, float, float], Any]] = []
        for e in entries:
            spec = getattr(e, "spec", None)
            name = getattr(spec, "name", "") or str(e)
            prof = self.profiles().get(name) or ModelProfile(provider=name)
            tier = getattr(spec, "tier", None) or prof.tier
            vision = bool(getattr(prof, "vision", False) or getattr(spec, "supports_vision", False))
            if name in req.avoid:
                continue
            if req.privacy == "local" and tier != "local":
                continue
            if not req.allow_paid and tier == "paid":
                continue
            if CAP_VISION in caps and not vision:
                continue
            if req.max_output_price and prof.prices[1] > req.max_output_price and tier == "paid":
                continue
            if req.max_latency and prof.latency_s > req.max_latency and tier != "local":
                continue
            ctx = int(prof.context or 0)
            if ctx and req.context() > ctx:
                continue
            fit = prof.score_for(caps)
            prefer_bonus = -1 if name in req.prefer else 0
            ranked.append(((0 if name in req.prefer else 1, TIER_RANK.get(tier, 2), -fit, prof.latency_s), e))
        ranked.sort(key=lambda t: t[0])
        return [e for _, e in ranked]

    def render(self, entries: Optional[Sequence[Any]] = None, req: Optional[Requirements] = None) -> str:
        profs = self.profiles()
        lines = []
        if req:
            lines.append(f"requirements: kind={req.kind} tools={req.need_tools} vision={req.need_vision} "
                         f"context≥{req.context()} privacy={req.privacy or '-'} paid={req.allow_paid}")
        if entries is not None:
            order = self.select(entries, req or Requirements())
            for i, e in enumerate(order):
                name = getattr(getattr(e, "spec", None), "name", str(e))
                p = profs.get(name)
                if p:
                    lines.append(f"  {i + 1:>2}. {name:<12} {p.tier:<5} fit={p.score_for(req.caps() if req else [])}"
                                 f"  ctx={p.context}  vision={p.vision}  ~{p.latency_s}s")
            return "\n".join(lines) or "  no provider available"
        for name, p in sorted(profs.items(), key=lambda kv: (TIER_RANK.get(kv[1].tier, 3), kv[0])):
            caps = ",".join(p.caps()) or "-"
            lines.append(f"  {name:<12} {p.tier:<5} model={p.model or '?':<28} ctx={p.context:<7} "
                         f"vision={str(p.vision):<5} caps={caps}")
        return "\n".join(lines)
