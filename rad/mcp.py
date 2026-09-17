"""The skills socket — Rad connects to ANY MCP server from a single link.

Accepts: GitHub repo links, npm package names, PyPI names, docker images,
remote MCP URLs (http/streamable), or local folders. It detects what it's
looking at, installs what's missing, performs the MCP handshake, and only
registers the server if you approve the tool list.

Every registered tool then runs through the normal confirm gate.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome
from rad.ui import col, ok, warn

PROTOCOL_VERSION = "2025-03-26"


# ---------------------------------------------------------------- stdio client

class McpStdio:
    """Line-delimited JSON-RPC over a subprocess stdio."""

    def __init__(self, command: List[str], env: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> None:
        self.command = command
        self.env = dict(os.environ, **(env or {}))
        self.timeout = timeout
        self.proc: Optional[subprocess.Popen] = None
        self._id = 0

    def start(self) -> None:
        self.proc = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=self.env, bufsize=1)

    def stop(self) -> None:
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=3)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None

    def _read_line(self) -> str:
        assert self.proc and self.proc.stdout
        import select
        while True:
            if os.name != "nt":  # select() on pipes is POSIX-only
                r, _, _ = select.select([self.proc.stdout], [], [], self.timeout)
                if not r:
                    raise TimeoutError("MCP server silent")
            line = self.proc.stdout.readline()
            if not line:
                raise TimeoutError("MCP server closed")
            if line.strip():
                return line.strip()

    def rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self._read_line()
            try:
                d = json.loads(line)
            except Exception:
                continue  # log noise from the server
            if d.get("id") == self._id:
                if "error" in d:
                    raise RuntimeError(f"MCP {method} error: {d['error']}")
                return d.get("result")

    def notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def handshake(self) -> List[Dict[str, Any]]:
        self.start()
        try:
            self.rpc("initialize", {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "rad-agent", "version": "0.1.0"},
            })
            self.notify("notifications/initialized")
            res = self.rpc("tools/list")
            return (res or {}).get("tools", []) or []
        finally:
            self.stop()


def mcp_call_stdio(entry: Dict[str, Any], tool: str, args: Dict[str, Any]) -> str:
    """One-shot: spawn, initialize, call, exit. Safe and simple."""
    client = McpStdio(entry["command"], entry.get("env"))
    try:
        client.start()
        client.rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
            "clientInfo": {"name": "rad-agent", "version": "0.1.0"}})
        client.notify("notifications/initialized")
        res = client.rpc("tools/call", {"name": tool, "arguments": args})
        parts = []
        for c in (res or {}).get("content", []) or []:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
            elif isinstance(c, dict) and c.get("type") == "image":
                parts.append(f"[image: {c.get('mimeType', '')}]")
        return "\n".join(parts) if parts else json.dumps(res)[:4000]
    except Exception as e:
        return f"[mcp call failed: {e}]"
    finally:
        client.stop()


# ---------------------------------------------------------------- remote (http) client

def mcp_http_handshake(url: str, timeout: float = 15.0) -> List[Dict[str, Any]]:
    session = {"id": None}

    def post(payload: Dict[str, Any]) -> Any:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if session["id"]:
            headers["Mcp-Session-Id"] = session["id"]
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            sid = r.headers.get("Mcp-Session-Id")
            if sid:
                session["id"] = sid
            raw = r.read().decode("utf-8", "replace")
        if "text/event-stream" in (r.headers.get("Content-Type") or "") or raw.lstrip().startswith("event:"):
            for line in raw.splitlines():
                if line.startswith("data:"):
                    try:
                        return json.loads(line[5:].strip())
                    except Exception:
                        continue
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
        "clientInfo": {"name": "rad-agent", "version": "0.1.0"}}})
    res = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    body = res.get("result", res) if isinstance(res, dict) else {}
    return (body or {}).get("tools", []) or []


def mcp_http_call(url: str, tool: str, args: Dict[str, Any], timeout: float = 60.0) -> str:
    try:
        mcp_http_handshake(url, timeout=10)  # refresh session
    except Exception:
        pass
    return "[remote MCP call not verified in this build — use stdio skills for actions]"


# ---------------------------------------------------------------- connect: detect + install

@dataclass
class Detected:
    name: str
    command: Optional[List[str]] = None
    env: Dict[str, str] = None
    transport: str = "stdio"  # stdio | http
    url: str = ""
    install_cmd: Optional[str] = None
    notes: List[str] = None
    repo_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        self.env = self.env or {}
        self.notes = self.notes or []


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _venv_for(home: RadHome, name: str) -> Path:
    v = home.root / "venvs" / name
    (home.root / "venvs").mkdir(exist_ok=True)
    return v


def _venv_python(v: Path) -> Path:
    if os.name == "nt":
        return v / "Scripts" / "python.exe"
    return v / "bin" / "python"


def _ensure_venv(home: RadHome, name: str) -> Path:
    v = _venv_for(home, name)
    if not _venv_python(v).exists():
        subprocess.run([sys.executable, "-m", "venv", str(v)], check=True,
                       capture_output=True, timeout=300)
    return v


def detect_from_link(home: RadHome, link: str) -> Detected:
    link = link.strip().rstrip("/")
    name = re.sub(r"\.git$", "", urllib.parse.urlparse(link).path.rsplit("/", 1)[-1]) or "skill"
    looks_like_path = ("~" in link) or link.startswith(("./", "../", "/", "C:\\")) or Path(link).expanduser().is_dir()

    # 1. local folder (must win over name heuristics!)
    p = Path(link).expanduser()
    if p.is_dir():
        return _detect_repo(home, p.name, p)

    # 2. remote http(s) MCP endpoint
    if re.match(r"^https?://", link) and not any(h in link for h in ("github.com", "raw.githubusercontent.com", "gist.github.com")):
        return Detected(name=name, transport="http", url=link + ("/" if not link.endswith(("/mcp", "/sse")) else ""))

    # 3. GitHub repo
    m = re.match(r"^(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", link, re.I)
    if m:
        owner, repo = m.group(1), m.group(2).removesuffix(".git")
        return _detect_repo(home, f"{owner}/{repo}")

    # 4. docker image (registry pattern or simple image:tag)
    if (re.match(r"^(?:[a-z0-9-]+\.)?[a-z0-9-]+\.[a-z]{2,}/", link)) or \
            (":" in name and re.match(r"^[a-z0-9._-]+:[a-z0-9._-]+$", link) and not looks_like_path):
        return Detected(name=name.split(":")[0],
                        command=["docker", "run", "-i", "--rm", "-e", "MCP_TRANSPORT=stdio", link] if _has("docker") else None,
                        notes=["needs docker"])

    # 5. npm package (optional @scope/) — only if it doesn't look like a path
    if not looks_like_path and re.match(r"^@?[a-z0-9][a-z0-9._-]*$", name):
        if _has("npx"):
            return Detected(name=name, command=["npx", "-y", name], notes=["uses npx"])
        return Detected(name=name, notes=["npx not found — install Node.js first"])

    # 6. last resort: pypi
    if not looks_like_path and re.match(r"^[a-z0-9][a-z0-9._-]*$", name):
        return Detected(name=name, install_cmd=f"pip install {name}",
                        notes=["assuming PyPI package — verify after install"])

    return Detected(name=name, notes=["could not detect a server type — add it with a local folder, GitHub link, or MCP URL"])


def _detect_repo(home: RadHome, ref: str, local_dir: Optional[Path] = None) -> Detected:
    """`ref`: owner/repo or URL for cloning. `local_dir`: an existing folder to use as-is."""
    name = local_dir.name if local_dir is not None else Path(ref).name
    if local_dir is not None:
        repo_dir = local_dir
    else:
        clone = home.root / "skills" / name
        if not clone.exists():
            url = ref if ref.startswith("http") else f"https://github.com/{ref}.git"
            r = subprocess.run(["git", "clone", "--depth", "1", url, str(clone)],
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                return Detected(name=name, notes=[f"git clone failed: {r.stderr.strip()[:300]}"])
        repo_dir = clone

    notes: List[str] = []
    cmd: Optional[List[str]] = None

    pkg = repo_dir / "package.json"
    pyproj = repo_dir / "pyproject.toml"
    setup = repo_dir / "setup.py"
    dockerfile = repo_dir / "Dockerfile"

    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
        except Exception:
            data = {}
        bins = data.get("bin")
        if isinstance(bins, str):
            script = bins
        elif isinstance(bins, dict) and bins:
            script = list(bins.values())[0]
        else:
            script = None
        if _has("npx"):
            cmd = ["npx", "-y", f"file:{repo_dir}"] if not script else ["npx", "-y", f"file:{repo_dir}"]
            notes.append(f"npm package {'(' + script + ')' if script else ''}")
        else:
            notes.append("package.json found but npx missing")
    elif pyproj.exists() or setup.exists():
        venv = _venv_for(home, name)
        if not _venv_python(venv).exists():
            notes.append("creating venv…")
        try:
            _ensure_venv(home, name)
            bin_dir = venv / "Scripts" if os.name == "nt" else venv / "bin"
            r = subprocess.run([str(_venv_python(venv)), "-m", "pip", "install", "-q", "-e", str(repo_dir)],
                               capture_output=True, text=True, timeout=900)
            if r.returncode != 0:
                notes.append(f"pip install -e failed: {r.stderr.strip()[-200:]}")
            scripts = []
            if pyproj.exists():
                m = re.search(r"\[project\.scripts\]\n(.*?)(\n\[|\Z)", pyproj.read_text(), re.S)
                if m:
                    scripts = [l.split("=")[0].strip().strip('"') for l in m.group(1).splitlines()
                               if "=" in l]
            script_exe = None
            if scripts:
                for cand in (bin_dir / scripts[0], bin_dir / (scripts[0] + ".exe")):
                    if cand.exists():
                        script_exe = cand
                        break
            if script_exe:
                cmd = [str(script_exe)]
            else:
                cmd = [str(_venv_python(venv)), "-m", name.replace("-", "_")]
            notes.append(f"installed into {venv.name}/ venv")
        except Exception as e:
            notes.append(f"venv setup failed: {e}")
    elif dockerfile.exists():
        if _has("docker"):
            image = f"rad-{name}"
            notes.append(f"building docker image {image}…")
            r = subprocess.run(["docker", "build", "-q", "-t", image, str(repo_dir)],
                               capture_output=True, text=True, timeout=1800)
            cmd = ["docker", "run", "-i", "--rm", image] if r.returncode == 0 else None
            if r.returncode != 0:
                notes.append(f"docker build failed: {r.stderr.strip()[-200:]}")
        else:
            notes.append("Dockerfile found but docker missing")
    else:
        # plain entry-point files (no manifest)
        for cand in ("server.py", "mcp_server.py", "mcp-server.py", "main.py", "index.js"):
            f = repo_dir / cand
            if f.exists():
                if cand.endswith(".py"):
                    cmd = [sys.executable, str(f)]
                    notes.append(f"using {cand} as entry point")
                elif cand.endswith(".js") and _has("node"):
                    cmd = ["node", str(f)]
                    notes.append(f"using {cand} as entry point")
                break

    if cmd is None:
        # search README for a launch hint
        for readme in ("README.md", "readme.md", "README.rst"):
            rp = repo_dir / readme
            if rp.exists():
                txt = rp.read_text(errors="replace")
                for pat in (r"npx\s+([a-z@][\w./@-]+)", r"uvx\s+([\w-]+)",
                            r"python\s+-m\s+([\w.]+)", r"docker\s+run\s+(-i\s+)?--rm\s+([\w./:-]+)"):
                    mm = re.search(pat, txt)
                    if mm:
                        g = next(x for x in mm.groups() if x)
                        if pat.startswith("npx"):
                            cmd = ["npx", "-y", g]
                        elif pat.startswith("uvx"):
                            cmd = ["uvx", g]
                        elif pat.startswith("python"):
                            cmd = [sys.executable, "-m", g]
                        else:
                            cmd = ["docker", "run", "-i", "--rm", g]
                        notes.append(f"launch hint from {readme}: {' '.join(cmd)}")
                        break
                if cmd:
                    break

    return Detected(name=name, command=cmd, transport="stdio", notes=notes, repo_dir=repo_dir)


def connect(home: RadHome, link: str, yes: bool = False,
            confirm: "Callable[[str], bool]" = lambda _p: False) -> Tuple[bool, str, Dict[str, Any]]:
    from typing import Callable  # noqa: F811
    det = detect_from_link(home, link)
    lines = [f"detected: {det.name} ({det.transport})"]
    lines += [f"  {n}" for n in det.notes]
    tools: List[Dict[str, Any]] = []
    try:
        if det.transport == "http":
            tools = mcp_http_handshake(det.url)
        elif det.command:
            tools = McpStdio(det.command, det.env).handshake()
        else:
            raise RuntimeError("no launch command found")
    except Exception as e:
        return False, "\n".join(lines + [f"handshake failed: {e}"]), {}

    entry: Dict[str, Any] = {
        "name": det.name, "transport": det.transport,
        "command": det.command, "env": det.env, "url": det.url,
        "tools": [{"name": t.get("name"), "description": (t.get("description") or "")[:300],
                   "schema": t.get("inputSchema", {})} for t in tools],
        "added": time.time(), "link": link,
    }
    if not yes:
        print(col.bold(f"\n  {det.name} exposes {len(entry['tools'])} tool(s):"))
        for t in entry["tools"]:
            print(f"    • {t['name']:<32} {col.dim((t['description'] or '')[:90])}")
        if not confirm(f"  connect '{det.name}' with these permissions?"):
            return False, "permission denied by user", {}
    reg = home.skills()
    reg[det.name] = entry
    home.save_skills(reg)
    return True, f"connected {det.name} with {len(entry['tools'])} tool(s)", entry


def call(home: RadHome, skill: str, tool: str, args: Dict[str, Any]) -> str:
    reg = home.skills()
    entry = reg.get(skill)
    if not entry:
        return f"[skill '{skill}' not connected]"
    if entry["transport"] == "http":
        return mcp_http_call(entry["url"], tool, args)
    return mcp_call_stdio(entry, tool, args)


def drop(home: RadHome, name: str) -> bool:
    reg = home.skills()
    if name not in reg:
        return False
    del reg[name]
    home.save_skills(reg)
    d = home.root / "skills" / name
    if d.exists() and (d / ".git").exists():
        shutil.rmtree(d, ignore_errors=True)
    return True


def skills_tools_schema(home: RadHome) -> List[Dict[str, Any]]:
    """Expose connected MCP tools to the brain as first-class tools."""
    out: List[Dict[str, Any]] = []
    for name, entry in home.skills().items():
        for t in entry.get("tools", []):
            out.append({"type": "function", "function": {
                "name": f"mcp__{name}__{t['name']}",
                "description": f"[{name}] {t.get('description', '')}",
                "parameters": t.get("schema") or {"type": "object", "properties": {}},
            }})
    return out
