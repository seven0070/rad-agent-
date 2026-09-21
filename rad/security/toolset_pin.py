"""Toolset pinning — drift kill-switch for connected skills (RFC-001 P1, T6).

digest = sha256(canonical_json(sorted([(name, input_schema)])))
Match -> proceed. Mismatch -> pending-reapproval, tools NOT registered.
Never silent. Never merged.

NOTE: sha256 truncation is 16 hex chars everywhere in this module (L2).
"""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

RESERVED_PREFIXES = ("rad_", "builtin_", "jerry_")
_SHA_CUT = 16

def _now(): return datetime.now(timezone.utc).isoformat()

def toolset_digest(tools: list) -> str:
    canon = json.dumps(
        sorted((t.get("name", ""), t.get("input_schema", {})) for t in tools),
        sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:_SHA_CUT]

def check_registration(tools: list) -> dict:
    """Namespace gate: reserved prefixes rejected, names alnum+underscore only."""
    accepted, rejected = [], []
    for t in tools:
        name = t.get("name", "")
        if any(name.startswith(p) for p in RESERVED_PREFIXES):
            rejected.append({"tool": name, "reason": "reserved_prefix"})
        elif not name.replace("_", "").isalnum() or not name:
            rejected.append({"tool": name, "reason": "invalid_name"})
        else:
            accepted.append(t)
    return {"accepted": accepted, "rejected": rejected}

def session_drift_check(skill: dict, fresh_tools: list) -> dict:
    """skill: registry entry with toolset_digest + tools + status."""
    fresh_digest = toolset_digest(fresh_tools)
    pinned = skill.get("toolset_digest")
    if pinned == fresh_digest:
        return {"skill": skill.get("name", "?"), "drift": False,
                "digest": fresh_digest, "status": skill.get("status", "active")}
    return {"skill": skill.get("name", "?"), "drift": True,
            "pinned_digest": pinned, "fresh_digest": fresh_digest,
            "old_status": skill.get("status", "active"),
            "new_status": "pending-reapproval",
            "diff": diff_toolsets(skill.get("tools", []), fresh_tools),
            "law": "approval was for a different toolset — re-approval required",
            "checked_at": _now()}

def diff_toolsets(old: list, new: list) -> dict:
    om = {t.get("name", ""): t.get("input_schema", {}) for t in old}
    nm = {t.get("name", ""): t.get("input_schema", {}) for t in new}
    return {"added": sorted(set(nm) - set(om)),
            "removed": sorted(set(om) - set(nm)),
            "changed": sorted(n for n in set(om) & set(nm) if om[n] != nm[n])}

def apply_drift(registry_path: Path, skill_name: str, drift: dict) -> None:
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    for s in reg.get("skills", []):
        if s.get("name") == skill_name:
            s["status"] = drift["new_status"]
            s["drift_history"] = s.get("drift_history", []) + [drift]
    registry_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")

def approve_fresh(registry_path: Path, skill_name: str, fresh_tools: list) -> dict:
    """Human re-approval: pin the new toolset, reactivate."""
    reg = json.loads(registry_path.read_text(encoding="utf-8"))
    for s in reg.get("skills", []):
        if s.get("name") == skill_name:
            s["toolset_digest"] = toolset_digest(fresh_tools)
            s["tools"] = fresh_tools
            s["status"] = "active"
            s["approved_at"] = _now()
    registry_path.write_text(json.dumps(reg, indent=2), encoding="utf-8")
    return {"skill": skill_name, "status": "active", "reapproved": True}
