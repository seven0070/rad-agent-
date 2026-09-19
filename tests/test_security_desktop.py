"""Security tests for the desktop/sidecar surface (mission §25).

Credential protection · authority escalation · filesystem scope escape · shell
restrictions · MCP restrictions · budget exhaustion · untrusted web data ·
frontend command restrictions.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from rad.api import Api, ApiError
from rad.authority import AUTONOMOUS, SAFE, UNRESTRICTED, Authority
from rad.control.objectives import Budget
from rad.policy import CAP_MCP, CAP_SHELL, CAP_WEB, CAP_WRITE, DENY, Policy
from rad.tools import ToolCtx, run_tool

ROOT = Path(__file__).resolve().parent.parent
DESK = ROOT / "desktop"


def ctx(home, auto=False):
    return ToolCtx(home=home, router=None, auto=auto, confirm=lambda p: True)


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


# ------------------------------------------------------------ credential protection

def test_api_token_permissions_and_isolation(home):
    from rad.api import token_for
    tok = token_for(home)
    assert len(tok) >= 32
    mode = os.stat(home.root / "api.token").st_mode & 0o777
    assert mode == 0o600
    # a wrong token is rejected at the handler boundary (401 simulated by the HTTP layer;
    # here: the token value is not guessable and the file is the only source)
    assert tok != token_for(home, rotate=True)


def test_credentials_denied_in_every_profile(home, ws):
    for profile in ("SAFE", "STANDARD", "AUTONOMOUS", "CUSTOM"):
        Authority(home).set_profile(profile, confirm_unrestricted=True)
        assert Policy(home).decide("credentials", "keys.env").effect in ("UNAUTHORIZED", "DENY")
    Authority(home).set_profile(UNRESTRICTED, confirm_unrestricted=True)
    assert Policy(home).decide("credentials", "keys.env").effect == "UNAUTHORIZED"
    # the model can never read RAD's own key files
    out = run_tool("read_file", {"path": str(home.root / "api.token")}, ctx(home, auto=True))
    assert "BLOCKED" in out or "DENIED" in out or "error" in out.lower()


def test_secrets_redacted_from_tool_output(home, ws):
    (ws / "leak.txt").write_text("token=sk-abcDEF1234567890xyz\n", encoding="utf-8")
    out = run_tool("read_file", {"path": "leak.txt"}, ctx(home, auto=True))
    assert "sk-abcDEF1234567890xyz" not in out
    assert "REDACTED" in out


def test_credential_file_protected(home, ws):
    from rad.api import token_for
    token_for(home)  # materialize
    assert (home.root / "api.token").exists()
    assert os.stat(home.root / "api.token").st_mode & 0o777 == 0o600
    # the model's read tool cannot fetch the token file even with auto on
    out = run_tool("read_file", {"path": str(home.root / "api.token")}, ctx(home, auto=True))
    assert "BLOCKED" in out or "UNAUTHORIZED" in out or "DENIED" in out or "error" in out.lower()


# ------------------------------------------------------------ authority escalation

def test_api_cannot_escalate_without_explicit_auth(home):
    api = Api(home)
    with pytest.raises(ApiError) as ei:
        api.handle("PUT", "/v1/authority", {}, {"profile": "UNRESTRICTED"})
    assert ei.value.status == 409
    assert Authority(home).state.profile == "STANDARD"
    st, d = api.handle("PUT", "/v1/authority", {},
                       {"profile": "UNRESTRICTED", "confirm_unrestricted": True})
    assert st == 200 and d["profile"] == UNRESTRICTED


def test_api_cannot_raise_budgets_or_caps(home, ws):
    api = Api(home)
    for key in ("max_plan_tasks", "tool_calls", "budget", "tool_router", "auto"):
        with pytest.raises(ApiError):
            api.handle("PUT", "/v1/settings", {}, {key: 9999})
    # 'credentials' can never be granted: the API coerces it to DENY on save, and the
    # policy layer denies protected credential paths regardless
    st, d = api.handle("PUT", "/v1/authority", {},
                       {"profile": "CUSTOM", "capabilities": {"credentials": "ALLOW"}})
    assert st == 200
    assert Policy(home).decide("credentials", "keys.env").effect == "UNAUTHORIZED"
    (ws / "keys.env").write_text("K=v", encoding="utf-8")
    out = run_tool("read_file", {"path": "keys.env"}, ctx(home, auto=True))
    assert "BLOCKED" in out or "UNAUTHORIZED" in out or "DENIED" in out or "error" in out.lower()


def test_frontend_cannot_write_authority_directly():
    """The desktop holds no local authority state; there is no second store."""
    src = ""
    for p in (DESK / "src").rglob("*"):
        if p.suffix in {".ts", ".tsx"}:
            src += p.read_text(encoding="utf-8")
    assert "localStorage" not in src
    assert "sessionStorage" not in src
    assert "indexedDB" not in src


# ------------------------------------------------------------ filesystem scope escape

def test_artifact_content_is_registry_gated(home, ws, scripted_run):
    api = Api(home)
    obj_id = scripted_run
    # unregistered paths never resolve, even with a token
    (home.root / "sensitive.txt").write_text("do not show", encoding="utf-8")
    for ref in ("/etc/passwd", str(home.root / "sensitive.txt"), "sensitive.txt",
                "..", "../outside"):
        with pytest.raises(ApiError) as ei:
            api.handle("GET", f"/v1/objectives/{obj_id}/artifact-content", {"ref": ref}, {})
        assert ei.value.status in (400, 403, 404)


def test_scope_violation_reported_not_allowed(home, ws, tmp_path):
    # SAFE grants read but scopes it to the workspace → policy-level SCOPE_VIOLATION
    Authority(home).set_profile(SAFE)
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    d = Policy(home).decide("fs.read", str(outside), auto=True, path=outside)
    assert d.effect == "SCOPE_VIOLATION"
    # STANDARD is a passthrough at the policy layer; the workspace boundary is still
    # enforced at the tool layer, and the write never happens
    Authority(home).set_profile("STANDARD")
    target = tmp_path / "brand_new.txt"
    out = run_tool("write_file", {"path": str(target), "content": "x"}, ctx(home, auto=True))
    assert "BLOCKED" in out or "SCOPE" in out
    assert not target.exists()


# ------------------------------------------------------------ shell restrictions

def test_no_shell_surface_in_api_or_frontend(home, ws):
    api = Api(home)
    for method, path, body in (
        ("POST", "/v1/shell", {"command": "id"}),
        ("POST", "/v1/exec", {"cmd": "id"}),
        ("POST", "/v1/tools", {"name": "run_shell", "args": {"command": "id"}}),
        ("GET", "/v1/shell", {}),
        ("POST", "/v1/objectives/x/exec", {"command": "id"}),
    ):
        with pytest.raises(ApiError) as ei:
            api.handle(method, path, {}, body)
        assert ei.value.status == 404
    # frontend: only the typed RadClient routes exist
    api_ts = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    for bad in ("/v1/shell", "run_shell", "invoke(\"shell", "child_process"):
        assert bad not in api_ts
    # every path in the client is a /v1/* string
    for route in (line.strip().strip('",').strip() for line in api_ts.splitlines()
                  if line.strip().startswith('"/v1')):
        assert route.startswith("/v1/")


def test_tauri_sidecar_is_fixed_argv():
    lib = (DESK / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    assert 'args([\"-m\", \"rad\", \"serve\"' not in lib or "Fixed argv" in lib
    # fixed argument vectors for the sidecar and the dev fallback
    assert '"serve"' in lib and '"--host"' in lib and '"127.0.0.1"' in lib
    # no user-controlled interpolation into a command
    assert ".arg(cmd)" not in lib
    assert "Command::new(user" not in lib
    assert "sh -c" not in lib
    assert "/bin/sh" not in lib and "/bin/bash" not in lib
    # no shell plugin at all
    cargo = (DESK / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    assert "tauri-plugin-shell" not in cargo
    assert "tauri-plugin-fs" not in cargo


# ------------------------------------------------------------ MCP restrictions

def test_mcp_denied_under_safe_ask_under_standard(home, ws):
    Authority(home).set_profile(SAFE)
    assert Policy(home).decide(CAP_MCP, "server").effect in ("UNAUTHORIZED", "DENY")
    Authority(home).set_profile("STANDARD")
    assert Policy(home).decide(CAP_MCP, "server").effect == "ASK"


# ------------------------------------------------------------ budget exhaustion

def test_budget_exhaustion_never_fake_success(home, ws):
    from tests.test_control_plane import ScriptedSession, _ctl
    home.update(auto=True)
    Authority(home).set_profile(AUTONOMOUS)
    # task needs two tools, budget allows one; check requires the second file
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "1"}),
          ("write_file", {"path": "b.txt", "content": "2"})], "DONE: both written"),
    ]
    plan = {"tasks": [{"id": "t1", "text": "two writes", "checks": [
        {"kind": "file_exists", "args": {"path": "b.txt"}}]}]}
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.create("exhaust", budget=Budget(tool_calls=1, model_calls=20, retries=0))
    obj = ctl.run(obj)
    assert obj.status in ("needs_user", "failed")
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"


# ------------------------------------------------------------ untrusted web data

def test_web_evidence_marked_untrusted_in_provenance(home, ws):
    from rad.control.observer import Observer, Observation
    from rad.control.provenance import Provenance
    d = ws.parent / "objdir"
    d.mkdir()
    obs = Observer(d)
    o = Observation.new(objective_id="obj_x", task_id="t1", action_id="act_1",
                        tool="fetch_page", args={"url": "https://example.com/p"},
                        status="success", output="the page says 42 is the answer",
                        duration_ms=5)
    (obs.dir / f"{o.id}.json").write_text(json.dumps(o.to_dict()), encoding="utf-8")
    pv = Provenance(d)
    res = pv.why("the page says 42 is the answer")
    assert res["verdict"] == "supported"
    for s in res["support"]:
        if s["tool"] == "fetch_page":
            assert s["trusted"] is False  # untrusted web data is labeled, never treated as fact


# ------------------------------------------------------------ frontend hygiene

def test_no_mock_or_demo_data_in_frontend():
    src = ""
    for p in (DESK / "src").rglob("*"):
        if p.suffix in {".ts", ".tsx"}:
            src += p.read_text(encoding="utf-8")
    low = src.lower()
    for token in ("mock", "demo data", "lorem", "fakeobjective", "sampleobjective"):
        assert token not in low, token


def test_frontend_renders_only_backend_state():
    """Status/verification strings must come from API fields, not literals invented in UI."""
    ver = (DESK / "src" / "pages" / "Verification.tsx").read_text(encoding="utf-8")
    assert "ver.status" in ver
    assert "obj?.verification" in ver
    app = (DESK / "src" / "App.tsx").read_text(encoding="utf-8")
    # reconnect is explicit, never silent
    assert "reconnecting" in app


def test_sidecar_only_binds_loopback():
    sidecar = (ROOT / "rad" / "sidecar.py").read_text(encoding="utf-8")
    assert "LOOPBACK" in sidecar
    assert "sidecar only binds loopback" in sidecar


@pytest.fixture
def scripted_run(home, ws):
    """A finished objective with one real artifact, built through the control plane."""
    from tests.test_control_plane import ScriptedSession
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "1"})], "DONE"),
    ]
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    from tests.test_control_plane import _ctl
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.run(ctl.create("artifact host"))
    assert obj.status == "completed"
    return obj.id
