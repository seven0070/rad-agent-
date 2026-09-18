"""Skill manifests — every connected MCP skill declares what it needs; the policy layer enforces it.

`rad connect` stores a registry entry (transport, command, tools). A **manifest** adds:

    capabilities   which RAD capabilities the skill's tools effectively exercise
                   (fs.read / fs.write / shell / web / mcp)  — declared or inferred from tool names
    per-tool caps  {"tool_name": ["fs.write"]} override
    approval       "ask" | "allow" | "deny" for the whole skill (default: policy decides per call)
    trust          "local" (runs on this machine) | "remote" (http) | "unknown"
    pinned         hash of the tool list at connect time; a changed tool list downgrades to
                   `approval: ask` until re-approved (a skill that silently grows a
                   `delete_everything` tool must not inherit yesterday's ALLOW)

Manifests live next to the registry: ~/.rad/skills/<name>.manifest.json. `rad skills audit`
lists skills with undeclared/dangerous capabilities; `rad skills approve <name>` re-pins.

Enforcement point: `rad.tools._run_tool` asks `skill_capability(home, skill, tool)` for the
effective capability *before* the policy gate, so an MCP tool that writes files is gated as
`fs.write` (not the blanket `mcp`), and a skill with `approval: deny` never runs.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome, _read_json, _write_json
from rad.policy import (CAP_BROWSER, CAP_CREDENTIALS, CAP_MCP, CAP_READ, CAP_SHELL,
                        CAP_WEB, CAP_WRITE)

DANGEROUS = (CAP_SHELL, CAP_WRITE)

# tool-name heuristics → capability (used only when the manifest does not declare)
_INFER = [
    (re.compile(r"(^|_)(exec|run|shell|command|spawn|terminal|bash|sh)($|_)", re.I), CAP_SHELL),
    (re.compile(r"(^|_)(write|create|delete|remove|rm|move|rename|edit|patch|append|mkdir|save|upload|send|post|put)($|_)", re.I), CAP_WRITE),
    (re.compile(r"(^|_)(fetch|http|browse|download|search|crawl|url|web|request)($|_)", re.I), CAP_WEB),
    (re.compile(r"(^|_)(read|list|get|cat|stat|find|grep|glob|show|query|describe|info)($|_)", re.I), CAP_READ),
]


def infer_capability(tool_name: str) -> str:
    for rx, cap in _INFER:
        if rx.search(tool_name):
            return cap
    return CAP_MCP


def _fingerprint(tools: List[Dict[str, Any]]) -> str:
    names = sorted(f"{t.get('name')}:{json.dumps(t.get('schema') or {}, sort_keys=True)}" for t in tools)
    return hashlib.sha256("\n".join(names).encode()).hexdigest()[:16]


def manifest_path(home: RadHome, name: str):
    return home.root / "skills" / f"{name}.manifest.json"


def load_manifest(home: RadHome, name: str) -> Dict[str, Any]:
    return _read_json(manifest_path(home, name), {})


def build_manifest(entry: Dict[str, Any], declared: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a manifest for a registry entry. `declared` may come from the skill's own
    package (rad-skill.json / mcp manifest) or from the user; inferred values fill the gaps."""
    declared = declared or {}
    tools = entry.get("tools", [])
    per_tool: Dict[str, List[str]] = {}
    for t in tools:
        n = t.get("name", "")
        d = (declared.get("tools") or {}).get(n)
        per_tool[n] = sorted(set(d)) if d else [infer_capability(n)]
    caps = sorted({c for cs in per_tool.values() for c in cs} | set(declared.get("capabilities") or []))
    declared_inputs = declared.get("inputs") if isinstance(declared.get("inputs"), dict) else {}
    declared_outputs = declared.get("outputs") if isinstance(declared.get("outputs"), dict) else {}
    spec: List[Dict[str, Any]] = []
    for t in tools:
        n = t.get("name", "")
        schema = t.get("schema") or t.get("inputSchema") or {}
        spec.append({
            "name": n,
            "description": t.get("description", ""),
            "inputs": declared_inputs.get(n) or sorted((schema.get("properties") or {}).keys()),
            "outputs": declared_outputs.get(n) or ["text"],
            "permissions": per_tool.get(n, [infer_capability(n)]),
        })
    approval = declared.get("approval", "ask" if any(c in DANGEROUS for c in caps) else "policy")
    trust = "remote" if entry.get("transport") == "http" else ("local" if entry.get("command") else "unknown")
    return {
        "name": entry.get("name"),
        "description": declared.get("description", entry.get("description", "")),
        "version": str(declared.get("version", entry.get("version", "")) or ""),
        "transport": entry.get("transport", "stdio"),
        "trust": trust,
        "capabilities": caps,
        "permissions": sorted(set(declared.get("permissions") or caps)),
        "dependencies": list(declared.get("dependencies") or entry.get("dependencies") or []),
        "security": {"approval": approval, "trust": trust,
                     "sandbox": "required" if caps else "not required",
                     "credentials": "never shared" if CAP_CREDENTIALS not in caps else "declared",
                     "network": "scoped by sandbox grants" if any(
                         c in caps for c in (CAP_WEB, CAP_BROWSER)) else "none"},
        "tools": per_tool,
        "spec": spec,
        "declared": bool(declared),
        "approval": approval,
        "pinned": _fingerprint(tools),
        "approved_at": None,
        "created": time.time(),
    }


def ensure_manifest(home: RadHome, name: str) -> Dict[str, Any]:
    """Load or create the manifest for a connected skill; detect tool-list drift."""
    reg = home.skills()
    entry = reg.get(name)
    if not entry:
        return {}
    m = load_manifest(home, name)
    fp = _fingerprint(entry.get("tools", []))
    if not m:
        m = build_manifest(entry)
        _write_json(manifest_path(home, name), m)
        return m
    if m.get("pinned") != fp:
        # tool list changed since approval → re-infer new tools, downgrade to ask, keep record
        fresh = build_manifest(entry)
        new_tools = sorted(set(fresh["tools"]) - set(m.get("tools", {})))
        for n, cs in fresh["tools"].items():
            m.setdefault("tools", {}).setdefault(n, cs)
        m["capabilities"] = sorted({c for cs in m["tools"].values() for c in cs})
        m["drift"] = {"from": m.get("pinned"), "to": fp, "at": time.time(),
                      "new_tools": new_tools, "was_approval": m.get("approval")}
        if m.get("approval") == "allow":
            m["approval"] = "ask"
        m["pinned"] = fp
        _write_json(manifest_path(home, name), m)
    return m


def approve(home: RadHome, name: str, approval: str = "allow") -> Dict[str, Any]:
    if approval not in ("allow", "ask", "deny", "policy"):
        raise ValueError("approval must be allow|ask|deny|policy")
    m = ensure_manifest(home, name)
    if not m:
        raise ValueError(f"skill {name!r} not connected")
    m["approval"] = approval
    m["approved_at"] = time.time()
    m.pop("drift", None)
    _write_json(manifest_path(home, name), m)
    return m


def declare(home: RadHome, name: str, tool: str, caps: List[str]) -> Dict[str, Any]:
    from rad.policy import BUILTIN_DEFAULTS
    bad = [c for c in caps if c not in BUILTIN_DEFAULTS]
    if bad:
        raise ValueError(f"unknown capabilities {bad}")
    m = ensure_manifest(home, name)
    if not m:
        raise ValueError(f"skill {name!r} not connected")
    m.setdefault("tools", {})[tool] = sorted(set(caps))
    m["capabilities"] = sorted({c for cs in m["tools"].values() for c in cs})
    m["declared"] = True
    _write_json(manifest_path(home, name), m)
    return m


def skill_capability(home: RadHome, skill: str, tool: str) -> Tuple[List[str], str]:
    """Effective capabilities for one MCP tool call and the skill-level approval.
    Unknown tool (not in manifest) → treated as shell (most dangerous) + ask."""
    m = ensure_manifest(home, skill)
    if not m:
        return [CAP_SHELL], "ask"
    caps = m.get("tools", {}).get(tool)
    if caps is None:
        return [CAP_SHELL], "ask"
    return caps, m.get("approval", "policy")


def audit(home: RadHome) -> List[Dict[str, Any]]:
    out = []
    for name in home.skills():
        m = ensure_manifest(home, name)
        flags = []
        dangerous = [t for t, cs in m.get("tools", {}).items() if any(c in DANGEROUS for c in cs)]
        if dangerous:
            flags.append(f"{len(dangerous)} tool(s) can write/exec: {', '.join(dangerous[:4])}")
        if not m.get("declared"):
            flags.append("capabilities inferred from tool names, not declared")
        if m.get("drift"):
            flags.append(f"tool list changed since approval (new: {', '.join(m['drift'].get('new_tools') or []) or '-'}) → approval downgraded to ask")
        if m.get("trust") == "remote":
            flags.append("remote (http) skill — data leaves this machine")
        if m.get("approval") == "allow" and dangerous:
            flags.append("approval=allow on a skill that can write/exec")
        out.append({"name": name, "approval": m.get("approval"), "trust": m.get("trust"),
                    "capabilities": m.get("capabilities", []), "tools": len(m.get("tools", {})), "flags": flags})
    return out
