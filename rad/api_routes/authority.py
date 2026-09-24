"""Authority, policy, user, audit and settings routes."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rad.api_security import ApiError
from rad.api_services import apply_authority, apply_settings, settings_payload


class AuthoritySettingsMixin:
    """GET /user, /policy, /audit; GET/PUT /authority; GET/PUT /settings."""

    def _route_authority(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                         ) -> Optional[Tuple[int, Any]]:
        if p == ["user"] and m == "GET":
            from rad.usermodel import UserModel
            return 200, UserModel(self.home).data()
        if p == ["policy"] and m == "GET":
            from rad.policy import Policy
            pol = Policy(self.home)
            from rad.authority import Authority
            from rad.policy import BUILTIN_DEFAULTS
            return 200, {"defaults": {c: pol.default_for(c) for c in BUILTIN_DEFAULTS},
                         "rules": [r.to_dict() for r in pol.rules], "web_allow": pol._data.get("web_allow", []),
                         "authority": Authority(self.home).snapshot()}
        if p == ["authority"] and m == "GET":
            from rad.authority import Authority
            return 200, Authority(self.home).snapshot()
        if p == ["authority"] and m == "PUT":
            return apply_authority(self.home, b)
        if p == ["settings"] and m == "GET":
            return 200, settings_payload(self.home)
        if p == ["settings"] and m == "PUT":
            return apply_settings(self.home, b)
        if p == ["audit"] and m == "GET":
            from rad.policy import Policy
            return 200, {"audit": Policy(self.home).audit_tail(int(q.get("n", 50) or 50), effect=q.get("effect") or None)}
        return None
