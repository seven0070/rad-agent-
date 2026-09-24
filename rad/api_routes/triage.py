"""Triage route: advisory auto/escalate classification (read-only, no side effects)."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rad.api_security import ApiError


class TriageMixin:
    """POST /triage — classify text into auto vs escalate. Never runs anything."""

    def _route_triage(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                      ) -> Optional[Tuple[int, Any]]:
        if p == ["triage"] and m == "POST":
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            if len(text) > 8000:
                raise ApiError(400, "text too long (max 8000)")
            kind = str(b.get("kind", "objective"))[:32]
            from rad.triage import brain_for, triage
            decision = triage(brain_for(self.home), text, kind=kind)
            return 200, decision.to_dict()
        return None
