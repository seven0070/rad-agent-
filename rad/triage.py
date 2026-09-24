"""Triage — advisory System-1 auto-vs-escalate classifier.

Phases (Laya integration plan): 0 = this module on the existing LLM router
with prompt-enforced JSON; 1 = RLCD/finetune on rad domain data; 2 = Laya
checkpoint live behind the same `triage(llm, ...)` seam; RSI loop optional.

Laws (mirrors recovery.py / DEVELOPMENT.md):
  * Advisory only — this never overrides Authority, `may_run`, Policy.decide
    or RecoveryEngine.decide; callers use it as an input, not a gate.
  * Deterministic risk signals can only TIGHTEN a verdict (auto -> escalate),
    never loosen it.
  * No brain / unparseable output / low confidence -> conservative `escalate`.
  * Offline-testable: the LLM is an injectable `Callable[[str], str]`.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

VERDICTS = ("auto", "escalate")
DEFAULT_KIND = "objective"
MIN_CONFIDENCE = 0.7

# Deterministic risk signals: presence forces `escalate` regardless of the
# model verdict (tighten-only). Keep this list conservative and readable.
_RISK = re.compile(
    r"\b(rm\s+-rf|drop\s+table|delete\s+(?:all|everything|production)"
    r"|production|prod\s+db|deploy(?:ing)?\s+to\s+prod"
    r"|payment|purchase|secret|credential|api\s+key"
    r"|sudo|mkfs|force[- ]push|irreversible)\b",
    re.IGNORECASE,
)

_SYSTEM = (
    "You are a triage classifier for an autonomous agent platform.\n"
    "Decide whether this {kind} can proceed automatically under the platform's\n"
    "existing safety gates, or must be escalated to a human first.\n"
    "auto     = safe to run without human confirmation (read-only/local/low-risk)\n"
    "escalate = needs a human (ask_user / NEEDS_USER): risky, irreversible,\n"
    "           ambiguous, or affects production/money/credentials/secrets.\n"
    "Reply with JSON only, no prose:\n"
    '{{"verdict": "auto"|"escalate", "reason": "<=200 chars", '
    '"confidence": 0.0-1.0}}'
)


@dataclass
class TriageDecision:
    verdict: str                     # one of VERDICTS
    reason: str
    confidence: float = 0.0          # 0..1 (self-reported by the model; uncalibrated until Phase 1)
    kind: str = DEFAULT_KIND
    decided_by: str = "fallback"     # "llm" | "fallback"
    signals: Dict[str, Any] = field(default_factory=dict)
    decision_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "confidence": round(self.confidence, 4),
            "kind": self.kind,
            "decided_by": self.decided_by,
            "signals": self.signals,
            "decision_ms": round(self.decision_ms, 3),
        }


def _strip_fences(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return text


def _balanced(text: str) -> Optional[str]:
    start = depth = None
    in_str = esc = False
    for i, ch in enumerate(text):
        if start is None:
            if ch in "{[":
                start, depth = i, 1
            continue
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _parse(raw: str) -> Dict[str, Any]:
    """Prompt-enforced JSON with tolerant recovery; raises ValueError on prose."""
    text = _strip_fences((raw or "").strip())
    if not text:
        raise ValueError("empty LLM output")
    blob = _balanced(text)
    if blob is None:
        blob = text
    blob = re.sub(r",\s*([}\]])", r"\1", blob)
    data = json.loads(blob)
    if not isinstance(data, dict):
        raise ValueError("triage output must be a JSON object")
    return data


def _risk_signals(text: str) -> Dict[str, Any]:
    hits = sorted({m.group(0).lower().strip() for m in _RISK.finditer(text)})
    return {"risk_hits": hits} if hits else {}


def _fallback(kind: str, reason: str, signals: Dict[str, Any], t0: float) -> TriageDecision:
    return TriageDecision(
        verdict="escalate",
        reason=reason,
        confidence=0.0,
        kind=kind,
        decided_by="fallback",
        signals=signals,
        decision_ms=(time.perf_counter() - t0) * 1000,
    )


def triage(
    llm: Optional[Callable[[str], str]],
    text: str,
    kind: str = DEFAULT_KIND,
    min_confidence: float = MIN_CONFIDENCE,
) -> TriageDecision:
    """Classify `text` into auto vs escalate. Advisory; never a security gate.

    `llm` is a `Callable[[str], str]` (Controller._brain shape) or None.
    Deterministic risk signals override a model `auto` down to `escalate`.
    """
    t0 = time.perf_counter()
    kind = str(kind or DEFAULT_KIND)[:32]
    text = (text or "").strip()[:8000]
    if not text:
        return _fallback(kind, "no text to classify", {}, t0)
    signals = _risk_signals(text)
    if llm is None:
        return _fallback(kind, "no brain available — conservative escalate", signals, t0)
    prompt = _SYSTEM.format(kind=kind) + "\n\nText:\n\"\"\"\n" + text + "\n\"\"\""
    try:
        raw = llm(prompt)
        data = _parse(raw)
    except Exception as exc:
        return _fallback(kind, f"unparseable triage output ({type(exc).__name__}) — escalate",
                         signals, t0)
    verdict = str(data.get("verdict", "")).strip().lower()
    reason = str(data.get("reason", ""))[:200] or "no reason given"
    try:
        conf = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    if verdict not in VERDICTS:
        return _fallback(kind, f"invalid verdict {verdict!r} — escalate", signals, t0)
    if verdict == "auto" and conf < min_confidence:
        return TriageDecision(
            verdict="escalate",
            reason=f"model said auto but confidence {conf:.2f} < {min_confidence}",
            confidence=conf, kind=kind, decided_by="llm",
            signals={**signals, "low_confidence": True},
            decision_ms=(time.perf_counter() - t0) * 1000,
        )
    if verdict == "auto" and signals.get("risk_hits"):
        return TriageDecision(
            verdict="escalate",
            reason="risk signal override: " + ", ".join(signals["risk_hits"]),
            confidence=conf, kind=kind, decided_by="policy_override",
            signals=signals,
            decision_ms=(time.perf_counter() - t0) * 1000,
        )
    return TriageDecision(
        verdict=verdict, reason=reason, confidence=conf, kind=kind,
        decided_by="llm", signals=signals,
        decision_ms=(time.perf_counter() - t0) * 1000,
    )


def brain_for(home) -> Optional[Callable[[str], str]]:
    """RouterState-backed brain (Controller._brain shape); None when offline."""
    try:
        from rad.router import RouterState
        r = RouterState(home)
        if not r.build_chain():
            return None
        return lambda p: r.chat([{"role": "user", "content": p}],
                                stream_cb=None, temperature=0.2).text
    except Exception:
        return None
