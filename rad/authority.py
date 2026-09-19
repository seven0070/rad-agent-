"""First-class authority — profiles, capabilities, scopes, confirmation.

Authoritative path (unchanged):

    User → Authority Profile → Capability / Scope / Budget / Confirmation
         → Existing Policy.decide → Existing Executor → Tool

This module does **not** execute tools, raise budgets, or replace the policy
engine. It resolves a persisted profile into grants that `Policy.decide`
consults. STANDARD is a no-op so existing behaviour is preserved.

Persisted at ``~/.rad/authority.json`` (JSON, same home as policy/config).
UNRESTRICTED is never inferred from a missing or corrupt file.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome, _read_json, _write_json
from rad.policy import (
    ALLOW, ASK, DENY, LIMITED,
    CAP_BROWSER, CAP_CREDENTIALS, CAP_MCP, CAP_MEMORY, CAP_PACKAGES,
    CAP_PY, CAP_READ, CAP_SHELL, CAP_SPAWN, CAP_VISION, CAP_WEB, CAP_WRITE,
    BUILTIN_DEFAULTS,
)

# --------------------------------------------------------------------------- profiles / confirmation

SAFE = "SAFE"
STANDARD = "STANDARD"
AUTONOMOUS = "AUTONOMOUS"
UNRESTRICTED = "UNRESTRICTED"
CUSTOM = "CUSTOM"
PROFILES = (SAFE, STANDARD, AUTONOMOUS, UNRESTRICTED, CUSTOM)

CONFIRM_ASK = "ask"
CONFIRM_NEVER = "never"
CONFIRMATIONS = (CONFIRM_ASK, CONFIRM_NEVER)

# Decision extras resolved by Policy.decide (denied like DENY; not a parallel engine)
SCOPE_VIOLATION = "SCOPE_VIOLATION"
UNAUTHORIZED = "UNAUTHORIZED"

# Conceptual names (UI / sandbox vocabulary) → existing policy capability
CONCEPT_TO_CAP: Dict[str, str] = {
    "filesystem.read": CAP_READ,
    "filesystem.write": CAP_WRITE,
    "filesystem.delete": CAP_WRITE,
    "shell.execute": CAP_SHELL,
    "network.request": CAP_WEB,
    "browser.access": CAP_BROWSER,
    "mcp.use": CAP_MCP,
    "skills.install": CAP_MCP,
    "package.install": CAP_PACKAGES,
    "process.spawn": CAP_SPAWN,
    "model.free": "model.free",
    "model.paid": "model.paid",
}

# Policy capability → conceptual names shown in the permissions UI
CAP_TO_CONCEPTS: Dict[str, Tuple[str, ...]] = {
    CAP_READ: ("filesystem.read",),
    CAP_WRITE: ("filesystem.write", "filesystem.delete"),
    CAP_SHELL: ("shell.execute",),
    CAP_WEB: ("network.request",),
    CAP_BROWSER: ("browser.access",),
    CAP_MCP: ("mcp.use", "skills.install"),
    CAP_PACKAGES: ("package.install",),
    CAP_SPAWN: ("process.spawn",),
    "model.free": ("model.free",),
    "model.paid": ("model.paid",),
}

# Capabilities that exist only in the authority layer (not tool Policy.decide)
MODEL_CAPS = ("model.free", "model.paid")

# RAD secrets stay un-granted in every profile, including UNRESTRICTED
NEVER_GRANTED = frozenset({CAP_CREDENTIALS})

# SAFE: confirmation-heavy, narrow. Write/shell/packages/mcp/spawn/py/paid denied.
SAFE_EFFECTS: Dict[str, str] = {
    CAP_READ: ALLOW,
    CAP_WRITE: DENY,
    CAP_SHELL: DENY,
    CAP_WEB: ASK,
    CAP_VISION: ASK,
    CAP_SPAWN: DENY,
    CAP_MCP: DENY,
    CAP_PY: DENY,
    CAP_BROWSER: ASK,
    CAP_PACKAGES: DENY,
    CAP_CREDENTIALS: DENY,
    CAP_MEMORY: ALLOW,
    "model.free": ALLOW,
    "model.paid": DENY,
}

# AUTONOMOUS: same grant surface as normal RAD, confirmation NEVER (ASK→ALLOW).
# Explicit DENY rules, hard layer, budgets, scopes still apply.
AUTONOMOUS_EFFECTS: Dict[str, str] = {
    **BUILTIN_DEFAULTS,
    "model.free": ALLOW,
    "model.paid": ALLOW,
}

# UNRESTRICTED: user-authorized autonomy — confirmation NEVER, broad ALLOW.
# Still goes through Policy.decide / executor / hard layer / budgets / audit.
UNRESTRICTED_EFFECTS: Dict[str, str] = {
    **{cap: ALLOW for cap in BUILTIN_DEFAULTS},
    CAP_CREDENTIALS: DENY,
    "model.free": ALLOW,
    "model.paid": ALLOW,
}

PROFILE_BLURB = {
    SAFE: "Confirmation-heavy, narrow capabilities, workspace-only scope.",
    STANDARD: "Existing RAD defaults (compatibility). Confirmation unless --auto.",
    AUTONOMOUS: "Reduced confirmation inside the granted set. Budgets and hard layer stay on.",
    UNRESTRICTED: "Explicitly user-authorized autonomy: confirmation off inside configured scope. "
                  "Not a policy bypass — audit, provenance, budgets, executor and verification remain.",
    CUSTOM: "Per-capability effects you set. Nothing implied.",
}


def normalize_cap(name: str) -> str:
    """Map a conceptual or policy name onto the policy capability string."""
    n = (name or "").strip()
    return CONCEPT_TO_CAP.get(n, n)


def _valid_effect(effect: str) -> bool:
    return effect in (ALLOW, ASK, LIMITED, DENY)


@dataclass
class Scope:
    """Where authority reaches. STANDARD skips extra path checks (existing jail remains)."""
    workspace_only: bool = True
    extra_paths: List[str] = field(default_factory=list)
    hosts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"workspace_only": self.workspace_only,
                "extra_paths": list(self.extra_paths),
                "hosts": list(self.hosts)}

    @classmethod
    def from_dict(cls, d: Any) -> "Scope":
        if not isinstance(d, dict):
            return cls()
        extras = [str(p) for p in (d.get("extra_paths") or []) if str(p).strip()]
        hosts = [str(h).lower().strip() for h in (d.get("hosts") or []) if str(h).strip()]
        return cls(workspace_only=bool(d.get("workspace_only", True)),
                   extra_paths=extras, hosts=hosts)


@dataclass
class AuthorityState:
    profile: str = STANDARD
    confirmation: str = CONFIRM_ASK
    capabilities: Dict[str, str] = field(default_factory=dict)  # CUSTOM overrides
    scopes: Scope = field(default_factory=Scope)
    unrestricted_authorized: bool = False
    unrestricted_authorized_at: float = 0.0
    updated: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"profile": self.profile, "confirmation": self.confirmation,
                "capabilities": dict(self.capabilities), "scopes": self.scopes.to_dict(),
                "unrestricted_authorized": self.unrestricted_authorized,
                "unrestricted_authorized_at": self.unrestricted_authorized_at,
                "updated": self.updated}

    @classmethod
    def from_dict(cls, d: Any) -> "AuthorityState":
        if not isinstance(d, dict):
            return cls()
        profile = str(d.get("profile") or STANDARD).upper()
        if profile not in PROFILES:
            profile = STANDARD
        confirmation = str(d.get("confirmation") or CONFIRM_ASK).lower()
        if confirmation not in CONFIRMATIONS:
            confirmation = CONFIRM_ASK
        caps: Dict[str, str] = {}
        raw = d.get("capabilities") or {}
        if isinstance(raw, dict):
            for k, v in raw.items():
                cap = normalize_cap(str(k))
                eff = str(v).upper()
                if _valid_effect(eff):
                    caps[cap] = eff
        authorized = bool(d.get("unrestricted_authorized"))
        # Never silently activate UNRESTRICTED from a hand-edited / corrupt file.
        if profile == UNRESTRICTED and not authorized:
            profile = STANDARD
            confirmation = CONFIRM_ASK
        return cls(profile=profile, confirmation=confirmation, capabilities=caps,
                   scopes=Scope.from_dict(d.get("scopes")),
                   unrestricted_authorized=authorized,
                   unrestricted_authorized_at=float(d.get("unrestricted_authorized_at") or 0),
                   updated=float(d.get("updated") or 0))


def default_state_for(profile: str) -> AuthorityState:
    profile = profile.upper()
    if profile == SAFE:
        return AuthorityState(profile=SAFE, confirmation=CONFIRM_ASK,
                              scopes=Scope(workspace_only=True))
    if profile == AUTONOMOUS:
        return AuthorityState(profile=AUTONOMOUS, confirmation=CONFIRM_NEVER,
                              scopes=Scope(workspace_only=True))
    if profile == UNRESTRICTED:
        return AuthorityState(profile=UNRESTRICTED, confirmation=CONFIRM_NEVER,
                              scopes=Scope(workspace_only=False),
                              unrestricted_authorized=True,
                              unrestricted_authorized_at=time.time())
    if profile == CUSTOM:
        return AuthorityState(profile=CUSTOM, confirmation=CONFIRM_ASK,
                              scopes=Scope(workspace_only=True))
    return AuthorityState(profile=STANDARD, confirmation=CONFIRM_ASK,
                          scopes=Scope(workspace_only=True))


class Authority:
    """Persisted authority profile. STANDARD leaves Policy.decide unchanged."""

    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.path = home.root / "authority.json"
        self.state = self._load()

    def _load(self) -> AuthorityState:
        return AuthorityState.from_dict(_read_json(self.path, {}))

    def reload(self) -> AuthorityState:
        self.state = self._load()
        return self.state

    def save(self) -> None:
        self.state.updated = time.time()
        _write_json(self.path, self.state.to_dict())

    # ---- profile resolution ------------------------------------------------
    def is_passthrough(self) -> bool:
        """STANDARD with default confirmation: do not add grant/scope layers."""
        return self.state.profile == STANDARD

    def confirmation_is_automatic(self) -> bool:
        """ASK → ALLOW. Never means bypass DENY / LIMITED / hard / budget."""
        if self.state.profile in (AUTONOMOUS, UNRESTRICTED):
            return True
        return self.state.confirmation == CONFIRM_NEVER

    def _template_effects(self) -> Dict[str, str]:
        p = self.state.profile
        if p == SAFE:
            return dict(SAFE_EFFECTS)
        if p == AUTONOMOUS:
            return dict(AUTONOMOUS_EFFECTS)
        if p == UNRESTRICTED:
            return dict(UNRESTRICTED_EFFECTS)
        if p == CUSTOM:
            out = {cap: ASK for cap in BUILTIN_DEFAULTS}
            out.update({"model.free": ALLOW, "model.paid": DENY})
            out.update(self.state.capabilities)
            return out
        # STANDARD: no extra effects — Policy uses its own defaults/rules
        return {}

    def effect_for(self, capability: str) -> Optional[str]:
        """Profile-imposed effect, or None if this profile does not override."""
        cap = normalize_cap(capability)
        if cap in NEVER_GRANTED:
            return DENY
        if self.is_passthrough() and cap not in NEVER_GRANTED:
            return None
        effects = self._template_effects()
        return effects.get(cap)

    def allows_capability(self, capability: str) -> bool:
        """False → Policy.decide returns UNAUTHORIZED. STANDARD grants the existing set."""
        cap = normalize_cap(capability)
        if cap in NEVER_GRANTED:
            return False
        if self.is_passthrough():
            return True
        eff = self.effect_for(cap)
        if eff is None:
            return True
        return eff != DENY

    def allows_paid_models(self) -> bool:
        return self.allows_capability("model.paid")

    def path_in_scope(self, path: Path) -> bool:
        """STANDARD: no extra check (workspace jail in tools.py still applies)."""
        if self.is_passthrough():
            return True
        if self.state.profile == UNRESTRICTED and not self.state.scopes.workspace_only:
            extras = self.state.scopes.extra_paths
            if not extras:
                return True
            return self._path_allowed(path, extras, workspace_ok=True)
        if not self.state.scopes.workspace_only:
            return self._path_allowed(path, self.state.scopes.extra_paths, workspace_ok=True)
        return self._path_allowed(path, self.state.scopes.extra_paths, workspace_ok=True)

    def _path_allowed(self, path: Path, extras: List[str], workspace_ok: bool) -> bool:
        try:
            resolved = path.expanduser().resolve()
        except Exception:
            resolved = Path(path)
        if workspace_ok:
            try:
                resolved.relative_to(self.home.workspace().resolve())
                return True
            except ValueError:
                pass
        for extra in extras:
            try:
                root = Path(extra).expanduser().resolve()
                resolved.relative_to(root)
                return True
            except (ValueError, OSError):
                continue
        return False

    def host_in_scope(self, host: str) -> bool:
        if self.is_passthrough():
            return True
        allow = self.state.scopes.hosts
        if not allow:
            return True
        h = (host or "").lower()
        return any(h == d or h.endswith("." + d) for d in allow)

    # ---- mutation (audited) ------------------------------------------------
    def set_profile(self, profile: str, *, confirm_unrestricted: bool = False,
                    capabilities: Optional[Dict[str, str]] = None,
                    scopes: Optional[Dict[str, Any]] = None,
                    confirmation: Optional[str] = None,
                    actor: str = "user") -> AuthorityState:
        profile = (profile or "").upper()
        if profile not in PROFILES:
            raise ValueError(f"unknown profile {profile!r}; valid: {', '.join(PROFILES)}")
        if profile == UNRESTRICTED and not confirm_unrestricted:
            raise ValueError(
                "UNRESTRICTED requires explicit user authorization "
                "(confirm_unrestricted / --i-authorize-unrestricted). "
                "It does not bypass Policy.decide, the executor, budgets, audit or verification.")
        prev = self.state.to_dict()
        nxt = default_state_for(profile)
        if profile == CUSTOM and capabilities:
            for k, v in capabilities.items():
                cap = normalize_cap(str(k))
                eff = str(v).upper()
                if not _valid_effect(eff):
                    raise ValueError(f"bad effect {v!r} for {k}")
                if cap in NEVER_GRANTED:
                    nxt.capabilities[cap] = DENY
                else:
                    nxt.capabilities[cap] = eff
        elif capabilities and profile != STANDARD:
            # allow narrowing extras on AUTONOMOUS / UNRESTRICTED without flipping to CUSTOM
            for k, v in capabilities.items():
                cap = normalize_cap(str(k))
                eff = str(v).upper()
                if _valid_effect(eff) and cap not in NEVER_GRANTED:
                    nxt.capabilities[cap] = eff
        if scopes is not None:
            nxt.scopes = Scope.from_dict(scopes)
        if confirmation is not None:
            c = confirmation.lower()
            if c not in CONFIRMATIONS:
                raise ValueError(f"confirmation must be {CONFIRMATIONS}")
            # UNRESTRICTED / AUTONOMOUS keep NEVER unless CUSTOM
            if profile == CUSTOM or profile == STANDARD:
                nxt.confirmation = c
            elif profile in (AUTONOMOUS, UNRESTRICTED):
                nxt.confirmation = CONFIRM_NEVER
        if profile == UNRESTRICTED:
            nxt.unrestricted_authorized = True
            nxt.unrestricted_authorized_at = time.time()
        self.state = nxt
        self.save()
        self._emit_changes(prev, actor)
        return self.state

    def set_capability(self, capability: str, effect: str, *, actor: str = "user") -> None:
        cap = normalize_cap(capability)
        effect = effect.upper()
        if not _valid_effect(effect):
            raise ValueError(f"effect must be one of {ALLOW, ASK, LIMITED, DENY}")
        if cap in NEVER_GRANTED:
            raise ValueError("credentials stay denied in every profile")
        prev = self.state.to_dict()
        if self.state.profile != CUSTOM:
            # flipping a single cap makes the profile CUSTOM so we do not pretend
            # a named template still describes the grant set
            stored = self._template_effects()
            stored[cap] = effect
            self.state.profile = CUSTOM
            self.state.capabilities = {k: v for k, v in stored.items() if k in BUILTIN_DEFAULTS or k in MODEL_CAPS}
            self.state.capabilities[cap] = effect
        else:
            self.state.capabilities[cap] = effect
        self.save()
        _emit(self.home, "CAPABILITY_CHANGED", actor=actor, capability=cap, effect=effect,
              profile=self.state.profile, before=prev.get("capabilities"))

    def set_scopes(self, scopes: Dict[str, Any], *, actor: str = "user") -> None:
        prev = self.state.scopes.to_dict()
        self.state.scopes = Scope.from_dict(scopes)
        self.save()
        _emit(self.home, "SCOPE_CHANGED", actor=actor, scopes=self.state.scopes.to_dict(), before=prev)

    def set_confirmation(self, confirmation: str, *, actor: str = "user") -> None:
        c = confirmation.lower()
        if c not in CONFIRMATIONS:
            raise ValueError(f"confirmation must be {CONFIRMATIONS}")
        if self.state.profile in (AUTONOMOUS, UNRESTRICTED) and c != CONFIRM_NEVER:
            raise ValueError(f"{self.state.profile} confirmation is never (ASK→ALLOW); change the profile instead")
        prev = self.state.confirmation
        self.state.confirmation = c
        self.save()
        _emit(self.home, "CONFIRMATION_POLICY_CHANGED", actor=actor,
              confirmation=c, before=prev, profile=self.state.profile)

    def note_session_auto(self, enabled: bool, *, actor: str = "user") -> None:
        """--auto / /auto: confirmation policy for this session, not a policy bypass."""
        _emit(self.home, "CONFIRMATION_POLICY_CHANGED", actor=actor,
              confirmation=CONFIRM_NEVER if enabled else CONFIRM_ASK,
              source="--auto", profile=self.state.profile,
              note="session confirmation only; DENY/LIMITED/hard/budget unchanged")

    def _emit_changes(self, prev: Dict[str, Any], actor: str) -> None:
        now = self.state.to_dict()
        if prev.get("profile") != now["profile"]:
            _emit(self.home, "AUTHORITY_PROFILE_CHANGED", actor=actor,
                  profile=now["profile"], before=prev.get("profile"),
                  unrestricted_authorized=now["unrestricted_authorized"])
        if prev.get("confirmation") != now["confirmation"]:
            _emit(self.home, "CONFIRMATION_POLICY_CHANGED", actor=actor,
                  confirmation=now["confirmation"], before=prev.get("confirmation"),
                  profile=now["profile"])
        if prev.get("capabilities") != now["capabilities"]:
            _emit(self.home, "CAPABILITY_CHANGED", actor=actor,
                  capabilities=now["capabilities"], before=prev.get("capabilities"),
                  profile=now["profile"])
        if prev.get("scopes") != now["scopes"]:
            _emit(self.home, "SCOPE_CHANGED", actor=actor,
                  scopes=now["scopes"], before=prev.get("scopes"))

    # ---- views -------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """Desktop / API / Jerry view. Includes conceptual capabilities and existing budgets."""
        from rad.control.objectives import Budget
        effects = self._template_effects() if not self.is_passthrough() else dict(BUILTIN_DEFAULTS)
        if self.is_passthrough():
            effects = {**dict(BUILTIN_DEFAULTS), "model.free": ALLOW,
                       "model.paid": DENY if self.home.cfg.get("free_lock") else ALLOW}
        concepts: Dict[str, Dict[str, Any]] = {}
        for concept, cap in CONCEPT_TO_CAP.items():
            eff = effects.get(cap, ASK if cap in BUILTIN_DEFAULTS else (ALLOW if cap == "model.free" else ASK))
            if cap in NEVER_GRANTED:
                eff = DENY
            concepts[concept] = {
                "capability": cap,
                "effect": eff,
                "granted": eff != DENY,
            }
        policy_caps = {cap: effects.get(cap, BUILTIN_DEFAULTS.get(cap, ASK)) for cap in BUILTIN_DEFAULTS}
        bud = Budget()
        return {
            "profile": self.state.profile,
            "blurb": PROFILE_BLURB[self.state.profile],
            "confirmation": CONFIRM_NEVER if self.confirmation_is_automatic() else self.state.confirmation,
            "confirmation_is_automatic": self.confirmation_is_automatic(),
            "unrestricted": self.state.profile == UNRESTRICTED,
            "unrestricted_authorized": bool(self.state.unrestricted_authorized),
            "scopes": self.state.scopes.to_dict(),
            "capabilities": concepts,
            "policy_capabilities": policy_caps,
            "passthrough": self.is_passthrough(),
            "budgets": {
                "tool_calls": bud.tool_calls,
                "model_calls": bud.model_calls,
                "retries": bud.retries,
                "note": "existing control-plane defaults; authority cannot raise them",
            },
            "invariants": {
                "executor_only": True,
                "policy_decide_required": True,
                "needle_default": "existing",
                "max_plan_tasks": 16,
                "default_tool_budget": 60,
            },
            "updated": self.state.updated,
        }

    def explain(self) -> str:
        s = self.snapshot()
        lines = [
            f"Authority profile: {s['profile']}",
            f"  {s['blurb']}",
            f"  confirmation: {s['confirmation']}"
            + (" (ASK→ALLOW; DENY/hard/budget unchanged)" if s["confirmation_is_automatic"] else ""),
            f"  scopes: workspace_only={s['scopes']['workspace_only']}"
            + (f" extra={s['scopes']['extra_paths']}" if s["scopes"]["extra_paths"] else "")
            + (f" hosts={s['scopes']['hosts']}" if s["scopes"]["hosts"] else ""),
        ]
        if s["unrestricted"]:
            lines.append("  UNRESTRICTED is explicitly user-authorized autonomy — not a hidden path.")
        lines.append("  capabilities:")
        for name, info in s["capabilities"].items():
            lines.append(f"    {name:<22} {info['effect']:<8} → {info['capability']}")
        return "\n".join(lines)


def confirmation_is_automatic(home: RadHome) -> bool:
    return Authority(home).confirmation_is_automatic()


def _emit(home: RadHome, kind: str, **data: Any) -> None:
    try:
        from rad.control.events import Event, emit_global
        emit_global(home, Event(kind=kind, data=data))
    except Exception:
        pass
