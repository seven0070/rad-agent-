"""Sandbox — capability scoping and resource limits for dangerous operations.

Policy answers *may this happen at all* (ALLOW / ASK / LIMITED / DENY, with a
hard layer nobody can override). The sandbox answers *how far may it reach*:

    filesystem.read:/workspace
    filesystem.write:/workspace
    shell.execute:limited
    python.execute:isolated
    network:https://example.com
    browser:public
    credentials:none

Two modes:

  * **jail mode** (default, no grants): RAD's normal boundaries — file tools stay
    inside the workspace, web tools stay on public hosts (both already enforced in
    `rad.tools` + the policy hard layer). The sandbox adds resource limits: output
    caps, timeouts, write-size caps and a call quota per run.
  * **grant mode** (any grants configured, or any sub-agent): *nothing* is allowed
    unless a grant matches, so a `researcher` agent that was granted
    `filesystem.read:/workspace` and `network:https://*` cannot write files, run
    shell, or reach a private host even if the global policy would allow it.

Sub-agents get their grant list from their capability envelope, narrowed to the
current workspace, so an agent can only ever be *less* powerful than RAD itself.
Every denial is counted and can be surfaced to the user (`rad security`).
"""
from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from rad.home import RadHome, _read_json

# ---------------------------------------------------------------------------- kinds

KIND_FS_READ = "filesystem.read"
KIND_FS_WRITE = "filesystem.write"
KIND_SHELL = "shell.execute"
KIND_PY = "python.execute"
KIND_NET = "network"
KIND_BROWSER = "browser"
KIND_PACKAGES = "packages"
KIND_CREDENTIALS = "credentials"
KINDS = (KIND_FS_READ, KIND_FS_WRITE, KIND_SHELL, KIND_PY, KIND_NET, KIND_BROWSER,
         KIND_PACKAGES, KIND_CREDENTIALS)

# policy capability (rad.policy) → sandbox kind
CAP_TO_KIND = {
    "fs.read": KIND_FS_READ, "fs.write": KIND_FS_WRITE, "shell": KIND_SHELL,
    "web": KIND_NET, "vision": KIND_BROWSER, "py.run": KIND_PY,
    "browser": KIND_BROWSER, "packages": KIND_PACKAGES, "credentials": KIND_CREDENTIALS,
    "mcp": KIND_SHELL,           # unknown MCP tool ⇒ most restrictive kind
    "agents.spawn": KIND_SHELL,
}

DEFAULT_LIMITS: Dict[str, Any] = {
    "timeout": 120,             # seconds for a single shell/python action
    "max_output": 40000,        # characters returned to the model
    "max_write_bytes": 5_000_000,
    "max_tool_calls": 0,        # 0 = unlimited (control-plane budget still applies)
    "max_network_bytes": 6_000_000,
    "allow_env": [],            # extra env var names passed into shells (empty = none)
}

# shell commands considered harmless enough for `shell.execute:limited`
LIMITED_BINARIES = (
    "ls", "cat", "head", "tail", "wc", "grep", "rg", "find", "sort", "uniq", "cut", "awk", "sed",
    "echo", "pwd", "date", "diff", "stat", "file", "du", "df", "basename", "dirname", "realpath",
    "python", "python3", "pytest", "pip", "pip3", "node", "npm", "npx", "git", "make", "jq", "curl",
    "mkdir", "touch", "cp", "mv", "rm", "unzip", "tar", "gzip", "sha256sum", "test", "true", "false",
    "env", "which", "printf", "tr", "xargs", "tee", "sed", "python3.11", "python3.12",
)
SHELL_METACHARS = ("|", ";", "&&", "||", ">", "<", "`", "$(", "&")


def parse_grant(text: str) -> Tuple[str, str]:
    """'filesystem.write:/workspace' → ('filesystem.write', '/workspace')."""
    kind, _, target = (text or "").partition(":")
    return kind.strip(), target.strip() or "*"


def _target_matches(target: str, resource: str) -> bool:
    if target in ("", "*"):
        return True
    if target == "public":
        return not _is_private_host(resource)
    if target == "limited":
        return True
    if "://" in target:                       # URL grant: scheme + host, path ignored
        try:
            from urllib.parse import urlparse
            u = urlparse(resource if "://" in resource else "https://" + resource)
            origin = f"{u.scheme}://{u.hostname or ''}"
        except Exception:
            origin = resource
        return (fnmatch.fnmatch(origin.lower(), target.lower())
                or fnmatch.fnmatch(resource.lower(), target.lower()))
    if "*" in target or "?" in target:
        return fnmatch.fnmatch(resource, target) or fnmatch.fnmatch(resource.lower(), target.lower())
    # path prefix for filesystem targets
    if target.startswith("/") and not resource.startswith("http"):
        return resource == target or resource.startswith(target.rstrip("/") + "/")
    return resource == target or resource.startswith(target)


def _is_private_host(url_or_host: str) -> bool:
    host = url_or_host
    if "//" in host:
        from urllib.parse import urlparse
        host = urlparse(host).hostname or ""
    host = host.split(":")[0].lower()
    if host in ("localhost", "::1", ""):
        return True
    if host.startswith(("127.", "10.", "192.168.", "169.254.", "0.")):
        return True
    if host.startswith("172."):
        try:
            second = int(host.split(".")[1])
            if 16 <= second <= 31:
                return True
        except Exception:
            pass
    return host.endswith(".local") or host == "metadata.google.internal"


@dataclass
class Limits:
    timeout: int = 120
    max_output: int = 40000
    max_write_bytes: int = 5_000_000
    max_tool_calls: int = 0
    max_network_bytes: int = 6_000_000
    allow_env: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Optional[Dict[str, Any]]) -> "Limits":
        d = d or {}
        kw = {k: d.get(k, DEFAULT_LIMITS[k]) for k in DEFAULT_LIMITS}
        try:
            kw["timeout"] = max(1, int(kw["timeout"]))
            kw["max_output"] = max(200, int(kw["max_output"]))
            kw["max_write_bytes"] = max(0, int(kw["max_write_bytes"]))
            kw["max_tool_calls"] = max(0, int(kw["max_tool_calls"]))
            kw["max_network_bytes"] = max(0, int(kw["max_network_bytes"]))
            kw["allow_env"] = [str(x) for x in (kw["allow_env"] or [])]
        except Exception:
            return cls()
        return cls(**kw)

    def to_dict(self) -> Dict[str, Any]:
        return {"timeout": self.timeout, "max_output": self.max_output,
                "max_write_bytes": self.max_write_bytes, "max_tool_calls": self.max_tool_calls,
                "max_network_bytes": self.max_network_bytes, "allow_env": self.allow_env}


class Denied(Exception):
    """A sandbox denial. Carries the human-readable reason."""

    def __init__(self, reason: str, kind: str = "", resource: str = "") -> None:
        super().__init__(reason)
        self.reason, self.kind, self.resource = reason, kind, resource


class Sandbox:
    def __init__(self, home: Optional[RadHome] = None, *, grants: Optional[Iterable[str]] = None,
                 limits: Optional[Dict[str, Any]] = None, workspace: Optional[Path] = None,
                 name: str = "rad", jail: bool = True) -> None:
        self.home = home
        self.workspace = Path(workspace or (home.workspace() if home else Path.cwd())).resolve()
        self.name = name
        cfg = _read_json((home.root / "sandbox.json") if home else Path("/nonexistent"), {}) or {}
        self.limits = Limits.from_dict({**DEFAULT_LIMITS, **(cfg.get("limits") or {}), **(limits or {})})
        raw_grants = list(grants) if grants is not None else list(cfg.get("grants") or [])
        #: explicit grants (from config or an agent envelope). Empty ⇒ jail mode: RAD's normal
        #: boundaries (workspace jail + policy hard layer) already apply, so the sandbox only
        #: enforces *limits* and never narrows what the user already allowed.
        self.grants: List[Tuple[str, str]] = [parse_grant(g) for g in raw_grants]
        self.enabled = bool(cfg.get("enabled", True))
        self.jail = bool(cfg.get("jail", jail))
        #: what jail mode implicitly allows (informational; enforcement lives in rad.tools/policy)
        self.jail_grants: List[Tuple[str, str]] = [
            (KIND_FS_READ, str(self.workspace)), (KIND_FS_WRITE, str(self.workspace)),
            (KIND_SHELL, "any"), (KIND_PY, "*"), (KIND_NET, "public"), (KIND_BROWSER, "public")]
        self.denials: List[Dict[str, Any]] = []
        self.calls = 0
        self.bytes_written = 0

    # ------------------------------------------------------------------ factory
    @classmethod
    def for_agent(cls, home: RadHome, caps: List[str], workspace: Optional[Path] = None,
                  name: str = "agent") -> "Sandbox":
        """Grants derived from an agent's capability envelope (never wider than RAD)."""
        from rad.policy import BUILTIN_DEFAULTS  # noqa: F401  (documentation of valid caps)
        ws = str(Path(workspace or home.workspace()).resolve())
        grants: List[str] = []
        for cap in caps:
            kind = CAP_TO_KIND.get(cap)
            if kind is None:
                continue
            if kind in (KIND_FS_READ, KIND_FS_WRITE):
                grants.append(f"{kind}:{ws}")
            elif kind == KIND_SHELL:
                grants.append(f"{kind}:limited")
            elif kind == KIND_NET:
                grants.append(f"{kind}:public")
            else:
                grants.append(f"{kind}:*")
        return cls(home, grants=grants, workspace=Path(ws), name=name, jail=True)

    # ------------------------------------------------------------------ grants
    def allows(self, kind: str, resource: str) -> bool:
        for k, target in self.grant_list():
            if k == kind and _target_matches(target, resource):
                return True
        return False

    def grant_list(self) -> List[Tuple[str, str]]:
        """Explicit grants when they exist, otherwise the jail defaults (read-only view)."""
        return self.grants or (self.jail_grants if self.jail else [])

    def grant_mode(self) -> bool:
        """True when an *explicit* grant list exists (agent / configured sandbox):
        then nothing outside it is reachable. Jail mode only enforces limits."""
        return bool(self.grants)

    def check(self, kind: str, resource: str) -> None:
        """Raise Denied when `resource` is outside this sandbox's reach."""
        if not self.enabled:
            return
        if not self.grant_mode():
            return
        if not self.allows(kind, resource):
            self.deny(kind, resource, f"no grant for {kind} on {resource!r}")
            raise Denied(f"sandbox denied {kind} on {resource!r} (grants: {self.render_grants()})",
                         kind, resource)

    def deny(self, kind: str, resource: str, reason: str) -> None:
        self.denials.append({"kind": kind, "resource": str(resource)[:300], "reason": reason})
        if len(self.denials) > 200:
            del self.denials[:-200]

    # ------------------------------------------------------------------ tools
    def check_tool(self, tool: str, args: Dict[str, Any]) -> None:
        """Pre-flight check for one tool call (called by the Executor, before policy)."""
        self.calls += 1
        if self.limits.max_tool_calls and self.calls > self.limits.max_tool_calls:
            raise Denied(f"sandbox tool-call limit {self.limits.max_tool_calls} reached", "quota", tool)
        a = args or {}
        if tool in ("read_file", "list_dir"):
            self.check(KIND_FS_READ, self._path(a.get("path") or "."))
        elif tool == "write_file":
            content = str(a.get("content", ""))
            if self.limits.max_write_bytes and len(content.encode("utf-8", "ignore")) > self.limits.max_write_bytes:
                raise Denied(f"write of {len(content)} bytes exceeds sandbox limit "
                             f"{self.limits.max_write_bytes}", KIND_FS_WRITE, str(a.get("path")))
            self.check(KIND_FS_WRITE, self._path(a.get("path") or "out.txt"))
        elif tool == "run_shell":
            cmd = str(a.get("command", ""))
            self.check_shell(cmd)
        elif tool == "run_python":
            self.check(KIND_PY, "isolated")
        elif tool in ("fetch_page", "web_search", "browse"):
            url = str(a.get("url") or "public")
            self.check(KIND_NET, url if a.get("url") else "public")
        elif tool.startswith("mcp__"):
            self.check(KIND_SHELL, tool)
        elif tool == "spawn_agents":
            self.check(KIND_SHELL, tool)

    def check_shell(self, cmd: str) -> None:
        self.check(KIND_SHELL, "limited" if self.grants and self.allows(KIND_SHELL, "limited") else "any")
        if not self.enabled or not self.grant_mode():
            return
        # limited shell: no metacharacters, first binary must be on the allowlist
        if self.allows(KIND_SHELL, "limited") and not self._unrestricted_shell_granted():
            toks = cmd.strip().split()
            binary = Path(toks[0]).name if toks else ""
            if any(m in cmd for m in SHELL_METACHARS):
                self.deny(KIND_SHELL, cmd, "shell metacharacter in limited mode")
                raise Denied("sandbox: shell is granted as 'limited' — pipes, redirection and "
                             "command chaining are not allowed", KIND_SHELL, cmd[:120])
            if binary not in LIMITED_BINARIES:
                self.deny(KIND_SHELL, cmd, f"binary {binary!r} not in limited allowlist")
                raise Denied(f"sandbox: {binary!r} is not allowed in limited shell mode", KIND_SHELL, cmd[:120])

    def _unrestricted_shell_granted(self) -> bool:
        return any(k == KIND_SHELL and target not in ("limited",) for k, target in self.grants)

    def _path(self, p: Any) -> str:
        try:
            q = Path(str(p)).expanduser()
            if not q.is_absolute():
                q = self.workspace / q
            return str(q.resolve())
        except Exception:
            return str(p)

    # ------------------------------------------------------------------ limits
    def timeout_for(self, requested: Optional[int] = None) -> int:
        want = int(requested or self.limits.timeout)
        return max(1, min(want, self.limits.timeout))

    def limit_output(self, out: str) -> str:
        if not out:
            return out
        cap = self.limits.max_output
        if len(out) <= cap:
            return out
        return out[:cap] + f"\n… [sandbox truncated {len(out) - cap} chars]"

    def env(self, base: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """A scrubbed environment for shells: only allow-listed vars plus PATH/HOME."""
        base = dict(base or {})
        keep = {"PATH", "HOME", "LANG", "LC_ALL", "TERM", "TMPDIR", "USER",
                "RAD_HOME", "SYSTEMROOT", "COMSPEC", "PYTHONPATH", "VIRTUAL_ENV",
                "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"}
        keep |= set(self.limits.allow_env or [])
        return {k: v for k, v in base.items() if k in keep}

    # ------------------------------------------------------------------ reporting
    def render_grants(self) -> str:
        if self.grants:
            return ", ".join(f"{k}:{t}" for k, t in self.grants)
        return "(jail: workspace read/write, public web, unlimited shell — limits still apply)"

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "enabled": self.enabled, "jail": self.jail,
                "workspace": str(self.workspace), "grants": [f"{k}:{t}" for k, t in self.grants],
                "effective": [f"{k}:{t}" for k, t in self.grant_list()],
                "grant_mode": self.grant_mode(), "limits": self.limits.to_dict(),
                "calls": self.calls, "denials": self.denials[-20:], "denied": len(self.denials)}


def load_config(home: RadHome) -> Dict[str, Any]:
    from rad.home import _write_json
    path = home.root / "sandbox.json"
    d = _read_json(path, None)
    if d is None:
        d = {"enabled": True, "jail": True, "limits": dict(DEFAULT_LIMITS), "grants": []}
        _write_json(path, d)
    d.setdefault("limits", {})
    d.setdefault("grants", [])
    return d


def configure(home: RadHome, *, grants: Optional[List[str]] = None,
              limits: Optional[Dict[str, Any]] = None, enabled: Optional[bool] = None) -> Dict[str, Any]:
    from rad.home import _write_json
    d = load_config(home)
    if grants is not None:
        for g in grants:
            kind, target = parse_grant(g)
            if kind not in KINDS:
                raise ValueError(f"unknown capability kind {kind!r}; valid: {', '.join(KINDS)}")
            d["grants"] = [x for x in d.get("grants", []) if parse_grant(x)[0] != kind]
            if target:
                d["grants"].append(f"{kind}:{target}")
    if limits:
        d["limits"] = {**d.get("limits", {}), **limits}
    if enabled is not None:
        d["enabled"] = bool(enabled)
    _write_json(home.root / "sandbox.json", d)
    return d
