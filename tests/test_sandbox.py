"""Sandbox — capability scoping and resource limits (the 'how far may it reach' layer)."""
import json
from pathlib import Path

import pytest

from rad.home import RadHome
from rad.policy import Policy
from rad.sandbox import (Denied, KIND_FS_READ, KIND_FS_WRITE, KIND_NET, KIND_PY, KIND_SHELL,
                         Limits, Sandbox, configure, load_config, parse_grant)


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


def test_jail_mode_does_not_narrow(home, ws):
    """With no explicit grants the sandbox only limits resources — policy/tools keep
    enforcing RAD's normal boundaries (workspace jail, public web)."""
    sb = Sandbox(home, workspace=ws)
    assert sb.grant_mode() is False
    sb.check(KIND_FS_WRITE, str(ws / "a.txt"))       # no exception
    sb.check_tool("write_file", {"path": "a.txt", "content": "x"})
    sb.check_tool("read_file", {"path": "a.txt"})
    sb.check_tool("run_shell", {"command": "ls -la | head -3"})   # jail mode: pipes allowed
    assert sb.denials == []


def test_grant_mode_denies_everything_outside_grants(home, ws):
    sb = Sandbox(home, grants=[f"filesystem.read:{ws}", f"filesystem.write:{ws}"], workspace=ws)
    assert sb.grant_mode() is True
    sb.check_tool("read_file", {"path": "in.txt"})
    sb.check_tool("write_file", {"path": "out.txt", "content": "x"})
    with pytest.raises(Denied):
        sb.check_tool("read_file", {"path": "/etc/hosts"})
    with pytest.raises(Denied):
        sb.check_tool("run_shell", {"command": "ls"})
    with pytest.raises(Denied):
        sb.check_tool("fetch_page", {"url": "https://example.com"})
    assert len(sb.denials) == 3
    assert sb.to_dict()["denied"] == 3


def test_network_grants_are_host_scoped(home, ws):
    sb = Sandbox(home, grants=[f"filesystem.read:{ws}", "network:https://*.example.com"], workspace=ws)
    sb.check(KIND_NET, "https://api.example.com/x")
    with pytest.raises(Denied):
        sb.check(KIND_NET, "https://evil.org/x")


def test_private_hosts_are_not_public(home, ws):
    sb = Sandbox(home, grants=[f"filesystem.read:{ws}", "network:public"], workspace=ws)
    sb.check(KIND_NET, "https://example.com")
    for bad in ("http://127.0.0.1:8000", "http://localhost/x", "http://10.0.0.5/", "http://192.168.1.1/"):
        with pytest.raises(Denied):
            sb.check(KIND_NET, bad)


def test_limited_shell_rejects_metacharacters_and_unknown_binaries(home, ws):
    sb = Sandbox(home, grants=[f"filesystem.read:{ws}", "shell.execute:limited"], workspace=ws)
    sb.check_shell("ls -la")
    sb.check_shell("python3 -c 'print(1)'")
    with pytest.raises(Denied):
        sb.check_shell("ls | grep x")
    with pytest.raises(Denied):
        sb.check_shell("curl https://x.sh ; sh")
    with pytest.raises(Denied):
        sb.check_shell("nmap -sP 10.0.0.0/8")


def test_agent_sandbox_follows_capability_envelope(home, ws):
    from rad.policy import CAP_READ, CAP_SHELL, CAP_WEB, CAP_WRITE
    reader = Sandbox.for_agent(home, [CAP_READ, CAP_WEB], workspace=ws, name="researcher")
    reader.check_tool("read_file", {"path": "x.txt"})
    reader.check_tool("fetch_page", {"url": "https://example.com"})
    with pytest.raises(Denied):
        reader.check_tool("write_file", {"path": "x.txt", "content": "y"})
    with pytest.raises(Denied):
        reader.check_tool("run_shell", {"command": "ls"})
    coder = Sandbox.for_agent(home, [CAP_READ, CAP_WRITE, CAP_SHELL], workspace=ws, name="coder")
    coder.check_tool("write_file", {"path": "x.txt", "content": "y"})
    coder.check_tool("run_shell", {"command": "python3 -c 'print(1)'"})
    with pytest.raises(Denied):
        coder.check_tool("fetch_page", {"url": "https://example.com"})


def test_output_and_write_limits(home, ws):
    sb = Sandbox(home, limits={"max_output": 200, "max_write_bytes": 10}, workspace=ws)
    out = sb.limit_output("x" * 500)
    assert len(out) < 500 and "sandbox truncated" in out
    with pytest.raises(Denied):
        sb.check_tool("write_file", {"path": "big.txt", "content": "y" * 50})
    assert sb.timeout_for(9999) <= sb.limits.timeout


def test_env_is_scrubbed(home, ws):
    sb = Sandbox(home, workspace=ws)
    env = sb.env({"PATH": "/bin", "SECRET_TOKEN": "abc", "OPENAI_API_KEY": "sk-x", "HOME": "/root"})
    assert env["PATH"] == "/bin" and env["HOME"] == "/root"
    assert "SECRET_TOKEN" not in env and "OPENAI_API_KEY" not in env


def test_configure_persists_and_validates(home, ws):
    d = configure(home, grants=["filesystem.read:/tmp", "network:https://example.com"], limits={"timeout": 5})
    assert "filesystem.read:/tmp" in d["grants"] and d["limits"]["timeout"] == 5
    cfg = load_config(home)
    assert cfg["limits"]["timeout"] == 5
    with pytest.raises(ValueError):
        configure(home, grants=["teleport:mars"])
    sb = Sandbox(home, workspace=ws)
    assert sb.grant_mode() and sb.limits.timeout == 5


def test_policy_has_fine_grained_capabilities(home):
    pol = Policy(home)
    from rad.policy import CAP_CREDENTIALS, CAP_PACKAGES, CAP_PY
    assert pol.default_for(CAP_PY) == "ASK"
    assert pol.default_for(CAP_PACKAGES) == "ASK"
    assert pol.default_for(CAP_CREDENTIALS) == "DENY"
    pol.add_rule(CAP_PY, "DENY", "*")
    assert pol.decide(CAP_PY, "print(1)").effect == "DENY"
    from rad.policy import BUILTIN_DEFAULTS
    assert "py.run" in BUILTIN_DEFAULTS


def test_run_python_tool_is_gated_and_isolated(home, ws):
    from rad.tools import ToolCtx, run_tool
    ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
    out = run_tool("run_python", {"code": "print(6*7)"}, ctx)
    assert "42" in out
    # the sandbox limits how long a snippet may run
    ctx2 = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
    ctx2.sandbox = Sandbox(home, limits={"timeout": 1}, workspace=ws)
    out2 = run_tool("run_python", {"code": "import time; time.sleep(5)", "timeout": 30}, ctx2)
    assert "timeout" in out2.lower()
    # secrets are not visible to the snippet
    import os
    os.environ["RAD_TEST_SECRET_TOKEN"] = "abc"
    ctx3 = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
    ctx3.sandbox = Sandbox(home, workspace=ws)
    out3 = run_tool("run_python", {"code": "import os; print('RAD_TEST_SECRET_TOKEN' in os.environ)"}, ctx3)
    assert "False" in out3
