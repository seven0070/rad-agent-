"""Chat and usage rollup routes."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rad.api_security import ApiError


class ChatUsageMixin:
    """GET /usage, POST /chat."""

    def _route_chat_usage(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                          ) -> Optional[Tuple[int, Any]]:
        if p == ["usage"] and m == "GET":
            from rad.control.objectives import REMAINING_QUOTA_NOTE
            store = self._ctl().store
            r = store.usage_rollup()
            return 200, {**r.to_dict(), "note": REMAINING_QUOTA_NOTE}
        if p == ["chat"] and m == "POST":
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            from rad.jerry import Jerry
            j = Jerry(self.home, session_factory=self._session_factory)
            # ASK → declined when confirmation is interactive (no TTY). AUTONOMOUS /
            # UNRESTRICTED confirmation=never is applied inside Policy.decide, not here.
            reply = j.chat(text, auto=False)
            return 200, {"reply": reply, "via": "jerry"}
        return None
