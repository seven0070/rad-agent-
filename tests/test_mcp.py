import json
import os
import stat
import sys

from rad import mcp
from rad.home import RadHome

FAKE_SERVER = """
import sys, json
def send(o):
    sys.stdout.write(json.dumps(o) + "\\n"); sys.stdout.flush()
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    m = json.loads(line)
    method = m.get("method")
    if method == "initialize":
        send({"jsonrpc":"2.0","id":m["id"],"result":{"protocolVersion":"2025-03-26",
             "capabilities":{},"serverInfo":{"name":"fake","version":"0"}}})
    elif method == "tools/list":
        send({"jsonrpc":"2.0","id":m["id"],"result":{"tools":[
            {"name":"echo","description":"echo back","inputSchema":{"type":"object",
             "properties":{"x":{"type":"string"}}}}]}})
    elif method == "tools/call":
        v = m["params"]["arguments"].get("x", "")
        send({"jsonrpc":"2.0","id":m["id"],"result":{"content":[{"type":"text","text":"echo:"+v}]}})
"""


def _server_path(tmp_path):
    p = tmp_path / "fake_mcp_server.py"
    p.write_text(FAKE_SERVER)
    return p


def test_stdio_handshake_and_call(home, tmp_path):
    srv = _server_path(tmp_path)
    entry = {"command": [sys.executable, str(srv)], "env": {}}
    tools = mcp.McpStdio(entry["command"]).handshake()
    assert [t["name"] for t in tools] == ["echo"]
    out = mcp.mcp_call_stdio(entry, "echo", {"x": "rad"})
    assert out == "echo:rad"


def test_connect_and_registry(home, tmp_path, monkeypatch):
    """Simulate `rad connect` with a local-folder skill containing a manifest."""
    skill = tmp_path / "my-skill"
    skill.mkdir()
    (skill / "package.json").write_text(json.dumps({"name": "my-skill", "bin": {"my-skill": "index.js"}}))
    (skill / "README.md").write_text("run it with: " + f"{sys.executable} -m fake_module")

    monkeypatch.setattr(mcp, "McpStdio", _FakeStdio)
    home2 = home
    det = mcp.detect_from_link(home2, str(skill))
    assert det.name == "my-skill"
    ok, msg, entry = mcp.connect(home2, str(skill), yes=True, confirm=lambda p: True)
    assert ok, msg
    reg = home2.skills()
    assert "my-skill" in reg
    assert reg["my-skill"]["tools"][0]["name"] == "echo"
    # exposed to the brain as mcp__my-skill__echo
    schema = mcp.skills_tools_schema(home2)
    assert any(t["function"]["name"] == "mcp__my-skill__echo" for t in schema)
    # drop
    assert mcp.drop(home2, "my-skill")
    assert "my-skill" not in home2.skills()


class _FakeStdio:
    """Stand-in for McpStdio in the connect test (no real subprocess)."""

    def __init__(self, command, env=None):
        self.command = command

    def handshake(self):
        return [{"name": "echo", "description": "echo back", "inputSchema": {"type": "object"}}]


def test_skill_manifest_is_declarative_and_security_aware(home, tmp_path):
    from rad import skills as SK
    reg = home.skills()
    reg["probe"] = {"name": "probe", "description": "a probe skill", "version": "1.2.0",
                    "transport": "stdio", "command": [sys.executable, "-c", "print(1)"],
                    "dependencies": ["httpx>=0.27"],
                    "tools": [{"name": "fetch_thing", "description": "fetch it",
                               "schema": {"type": "object", "properties": {"q": {"type": "string"}}}}]}
    home.save_skills(reg)
    m = SK.ensure_manifest(home, "probe")
    assert m["name"] == "probe" and m["version"] == "1.2.0" and m["description"] == "a probe skill"
    assert m["capabilities"] == ["web"] and m["permissions"] == ["web"]
    assert m["dependencies"] == ["httpx>=0.27"]
    assert m["security"]["sandbox"] == "required" and m["security"]["credentials"] == "never shared"
    assert m["security"]["network"] == "scoped by sandbox grants"
    assert m["spec"][0]["inputs"] == ["q"] and m["spec"][0]["permissions"] == ["web"]
    assert m["approval"] in ("policy", "ask", "allow", "deny")
