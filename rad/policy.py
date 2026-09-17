"""Policy engine — capability-based permissions with an unbypassable hard layer.

Every tool call goes through `Policy.decide()` inside `run_tool` (the single enforcement
point; sub-agents, the control plane and the REPL all end up there).

    decision = HARD-DENY  |  DENY  |  ASK  |  LIMITED  |  ALLOW

Two layers:

  hard layer   built into code, cannot be changed by config, --auto, or the model:
               destructive shell patterns, secret files (~/.rad/keys, .vault.key, ~/.ssh,
               .env credentials, /etc/shadow …), git-credential stores, private-network egress
               and a secret-redaction pass on every tool *output*.
  soft layer   rules in ~/.rad/policy.json:  {"capability": "shell", "match": "git push*",
               "effect": "ASK"|"ALLOW"|"DENY"|"LIMITED", "limits": {...}}
               First matching rule wins; then per-capability default; then built-in default.

--auto only converts ASK into ALLOW. It never touches DENY, LIMITED or the hard layer.
Every decision is appended to ~/.rad/audit.jsonl (who, what, why, decided-by).
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome, _write_json

ALLOW, ASK, LIMITED, DENY, HARD_DENY = "ALLOW", "ASK", "LIMITED", "DENY", "HARD_DENY"
EFFECTS = (ALLOW, ASK, LIMITED, DENY)

# capability names shared with rad.agents
CAP_READ, CAP_WRITE, CAP_SHELL, CAP_WEB, CAP_VISION, CAP_SPAWN, CAP_MCP = (
    "fs.read", "fs.write", "shell", "web", "vision", "agents.spawn", "mcp")

BUILTIN_DEFAULTS: Dict[str, str] = {
    CAP_READ: ALLOW, CAP_WRITE: ASK, CAP_SHELL: ASK, CAP_WEB: ALLOW,
    CAP_VISION: ALLOW, CAP_SPAWN: ASK, CAP_MCP: ASK,
}

# ---------------------------------------------------------------- hard layer (code only)

HARD_SHELL = [
    r"\bsudo\b", r"\bsu\s+-?\s*root\b", r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+(/|~|\$HOME)(\s|$)",
    r"\bmkfs", r"\bdd\s+if=", r":\(\)\s*\{", r"\bshutdown\b", r"\breboot\b",
    r"curl[^|]*\|\s*(ba)?sh", r"wget[^|]*\|\s*(ba)?sh", r">\s*/dev/sd",
    r"\bchmod\s+-R\s+777\s+/", r"\bformat\s+c:", r"\bdel\s+/[sfq]+\s+%systemroot",
    r"\.rad/keys", r"\.vault\.key", r"~/\.ssh|/\.ssh/", r"/etc/shadow", r"\.git-credentials",
    r"\bgit\s+push\s+(-f|--force)\b", r"\bgit\s+push\b.*\s--force\b",
    r"\bhistory\s+-c\b",
]
HARD_PATH_PARTS = ("/.rad/keys", "/.vault.key", "/.ssh/", "/etc/shadow", "/.git-credentials",
                   "/.netrc", "/.aws/credentials", "/.gnupg/", "/.git/config")
HARD_PATH_NAMES = ("keys.env", "vault.enc", ".vault.key", "id_rsa", "id_ed25519", ".git-credentials", ".netrc")
HARD_HOSTS = (r"^localhost$", r"^127\.", r"^0\.0\.0\.0$", r"^10\.", r"^192\.168\.", r"^172\.(1[6-9]|2\d|3[01])\.",
              r"^169\.254\.", r"^\[?::1\]?$", r"^metadata\.google\.internal$")

SECRET_PATTERNS = [
    (re.compile(r"\b(sk-[A-Za-z0-9_-]{16,})"), "sk-…REDACTED"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,})"), "gh…REDACTED"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "AKIA…REDACTED"),
    (re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})"), "xox…REDACTED"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)(\s*[:=]\s*)(['\"]?)([^\s'\"]{8,})"),
     lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}REDACTED"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[PRIVATE KEY REDACTED]"),
    (re.compile(r"(?i)(Authorization:\s*Bearer\s+)[A-Za-z0-9._-]{10,}"), r"\1REDACTED"),
]


def redact(text: str) -> str:
    if not text:
        return text
    for pat, rep in SECRET_PATTERNS:
        text = pat.sub(rep, text)  # type: ignore[arg-type]
    return text


def hard_check_shell(cmd: str) -> Optional[str]:
    for pat in HARD_SHELL:
        if re.search(pat, cmd, re.I):
            return f"shell pattern {pat!r}"
    return None


def hard_check_path(p: Path, rad_home: Optional[Path] = None) -> Optional[str]:
    s = str(p).replace("\\", "/")
    if rad_home is not None:
        try:
            rel = p.resolve().relative_to(rad_home.resolve())
            if rel.parts and rel.parts[0] in ("keys", ".vault.key", "policy.json", "audit.jsonl"):
                return f"protected RAD home path {rel.parts[0]}"
        except ValueError:
            pass
    for part in HARD_PATH_PARTS:
        if part in s or s.endswith(part.rstrip("/")):
            return f"protected path {part}"
    if p.name in HARD_PATH_NAMES:
        return f"protected file {p.name}"
    return None


def hard_check_url(url: str) -> Optional[str]:
    from urllib.parse import urlparse
    try:
        u = urlparse(url)
    except Exception:
        return "unparseable url"
    if u.scheme not in ("http", "https"):
        return f"only http(s) urls are allowed, got {u.scheme or '?'}"
    host = (u.hostname or "").lower()
    if not host:
        return "no host"
    for pat in HARD_HOSTS:
        if re.match(pat, host):
            return f"private/loopback host {host}"
    if u.username or u.password:
        return "credentials in url"
    return None


# ---------------------------------------------------------------- soft layer

@dataclass
class Rule:
    capability: str
    effect: str
    match: str = "*"                 # glob on the resource (command / path / url / tool name)
    limits: Dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"capability": self.capability, "effect": self.effect, "match": self.match,
                "limits": self.limits, "note": self.note}


@dataclass
class Decision:
    effect: str
    reason: str
    by: str                          # hard | rule | default | builtin | agent
    limits: Dict[str, Any] = field(default_factory=dict)

    @property
    def denied(self) -> bool:
        return self.effect in (DENY, HARD_DENY)


class Policy:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.path = home.root / "policy.json"
        self.audit_path = home.root / "audit.jsonl"
        self._data = self._load()
        self._mtime = self._stat()

    def _stat(self) -> float:
        try:
            return self.path.stat().st_mtime_ns
        except OSError:
            return 0.0

    def _refresh(self) -> None:
        """Rules edited by another process/instance (rad policy …) take effect on the next decision."""
        m = self._stat()
        if m != self._mtime:
            self._data = self._load()
            self._mtime = m

    # ---- persistence
    def _load(self) -> Dict[str, Any]:
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            d = {}
        d.setdefault("defaults", {})
        d.setdefault("rules", [])
        d.setdefault("web_allow", [])       # optional domain allowlist; empty = any public host
        return d

    def save(self) -> None:
        _write_json(self.path, self._data)
        self._mtime = self._stat()

    @property
    def rules(self) -> List[Rule]:
        return [Rule(**{k: r.get(k, Rule.__dataclass_fields__[k].default if k != "limits" else {})
                        for k in ("capability", "effect", "match", "limits", "note")}) for r in self._data["rules"]]

    def add_rule(self, capability: str, effect: str, match: str = "*", limits: Optional[Dict[str, Any]] = None,
                 note: str = "", first: bool = True) -> Rule:
        effect = effect.upper()
        if effect not in EFFECTS:
            raise ValueError(f"effect must be one of {EFFECTS}")
        if capability not in BUILTIN_DEFAULTS:
            raise ValueError(f"unknown capability {capability}; valid: {', '.join(BUILTIN_DEFAULTS)}")
        r = Rule(capability, effect, match, limits or {}, note)
        if first:
            self._data["rules"].insert(0, r.to_dict())
        else:
            self._data["rules"].append(r.to_dict())
        self.save()
        return r

    def remove_rule(self, index: int) -> bool:
        if 0 <= index < len(self._data["rules"]):
            self._data["rules"].pop(index)
            self.save()
            return True
        return False

    def set_default(self, capability: str, effect: str) -> None:
        effect = effect.upper()
        if effect not in EFFECTS or capability not in BUILTIN_DEFAULTS:
            raise ValueError("bad capability/effect")
        self._data["defaults"][capability] = effect
        self.save()

    def default_for(self, capability: str) -> str:
        return self._data["defaults"].get(capability, BUILTIN_DEFAULTS.get(capability, ASK))

    def reset(self) -> None:
        self._data = {"defaults": {}, "rules": [], "web_allow": []}
        self.save()

    # ---- decision
    def decide(self, capability: str, resource: str, *, auto: bool = False,
               agent_caps: Optional[List[str]] = None, path: Optional[Path] = None,
               tool: str = "") -> Decision:
        self._refresh()
        # 1. hard layer — nothing below can override
        if capability == CAP_SHELL and (why := hard_check_shell(resource)):
            return Decision(HARD_DENY, why, "hard")
        if capability in (CAP_READ, CAP_WRITE) and path is not None and (why := hard_check_path(path, self.home.root)):
            return Decision(HARD_DENY, why, "hard")
        if capability == CAP_WEB and tool == "fetch_page" and (why := hard_check_url(resource)):
            return Decision(HARD_DENY, why, "hard")
        # 2. agent capability envelope (a sub-agent can only narrow, never widen)
        if agent_caps is not None and capability not in agent_caps:
            return Decision(DENY, f"agent lacks capability {capability}", "agent")
        # 3. web allowlist (soft, but explicit)
        if capability == CAP_WEB and tool == "fetch_page" and self._data.get("web_allow"):
            from urllib.parse import urlparse
            host = (urlparse(resource).hostname or "").lower()
            if not any(host == d or host.endswith("." + d) for d in self._data["web_allow"]):
                return Decision(DENY, f"host {host} not in web_allow", "rule")
        # 4. rules, first match wins
        for i, r in enumerate(self.rules):
            if r.capability == capability and (fnmatch.fnmatch(resource, r.match) or (tool and fnmatch.fnmatch(tool, r.match))):
                eff = r.effect
                if eff == ASK and auto:
                    return Decision(ALLOW, f"rule#{i} {r.match!r} ASK → auto", "rule", r.limits)
                return Decision(eff, f"rule#{i} {r.match!r}" + (f" ({r.note})" if r.note else ""), "rule", r.limits)
        # 5. default
        eff = self.default_for(capability)
        by = "default" if capability in self._data["defaults"] else "builtin"
        if eff == ASK and auto:
            return Decision(ALLOW, f"{by} ASK → auto", by)
        return Decision(eff, f"{by} {eff}", by)

    # ---- audit
    def audit(self, capability: str, resource: str, decision: Decision, *, tool: str = "",
              actor: str = "", outcome: str = "") -> None:
        rec = {"at": time.time(), "tool": tool, "cap": capability, "resource": redact(str(resource))[:300],
               "effect": decision.effect, "reason": decision.reason, "by": decision.by,
               "actor": actor, "outcome": outcome}
        try:
            with open(self.audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def audit_tail(self, n: int = 50, effect: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            lines = self.audit_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        out = []
        for ln in reversed(lines):
            try:
                d = json.loads(ln)
            except Exception:
                continue
            if effect and d.get("effect") != effect:
                continue
            out.append(d)
            if len(out) >= n:
                break
        return out

    def explain(self) -> str:
        lines = ["Policy (first matching rule wins; --auto only turns ASK into ALLOW; hard layer is not configurable):"]
        for cap in BUILTIN_DEFAULTS:
            d = self.default_for(cap)
            src = "" if cap not in self._data["defaults"] else "  (configured)"
            lines.append(f"  default {cap:<13} {d}{src}")
        if self._data.get("web_allow"):
            lines.append(f"  web_allow: {', '.join(self._data['web_allow'])}")
        for i, r in enumerate(self.rules):
            lim = f"  limits={json.dumps(r.limits)}" if r.limits else ""
            lines.append(f"  rule#{i:<3} {r.capability:<13} {r.effect:<8} match={r.match!r}{lim}{('  # ' + r.note) if r.note else ''}")
        lines.append(f"  hard: {len(HARD_SHELL)} shell patterns, protected paths {', '.join(HARD_PATH_NAMES)}, "
                     "private-network egress blocked, secrets redacted from outputs")
        return "\n".join(lines)
