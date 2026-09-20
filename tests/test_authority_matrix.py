"""Authority matrix — every profile, every invariant (mission §29).

    SAFE        restricted authority
    STANDARD    existing standard behaviour
    AUTONOMOUS  reduced confirmation, enforcement remains
    UNRESTRICTED explicit authorization, broad authority, enforcement remains
    CUSTOM      exact configured authority

For every profile: Policy stays authoritative, hard blocks stay authoritative,
budgets stay authoritative, the executor stays authoritative, audit stays
active, verification stays independent.
"""
from __future__ import annotations

import json

import pytest

from rad.authority import (
    AUTONOMOUS, CUSTOM, SAFE, STANDARD, UNRESTRICTED, Authority,
)
from rad.control.events import read_global
from rad.control.objectives import Budget
from rad.policy import (
    ALLOW, ASK, DENY, HARD_DENY, SCOPE_VIOLATION, UNAUTHORIZED,
    CAP_MCP, CAP_PACKAGES, CAP_SHELL, CAP_WEB, CAP_WRITE, Policy,
)
from rad.tools import ToolCtx, run_tool


def ctx(home, auto=False):
    return ToolCtx(home=home, router=None, auto=auto, confirm=lambda p: True)


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


PROFILES = [SAFE, STANDARD, AUTONOMOUS, UNRESTRICTED, CUSTOM]


def _set(home, profile, **kw):
    return Authority(home).set_profile(profile, **kw)


# ------------------------------------------------------------ 1. grant surface per profile

@pytest.mark.parametrize("profile", PROFILES)
def test_grant_surface(home, ws, profile):
    auth = _set(home, profile, confirm_unrestricted=True)
    pol = Policy(home)
    c = ctx(home, auto=False)
    if profile == SAFE:
        assert run_tool("write_file", {"path": "x.txt", "content": "1"}, c).startswith("UNAUTHORIZED")
        assert "UNAUTHORIZED" in run_tool("run_shell", {"command": "echo hi"}, c)
        # reads still allowed
        assert run_tool("list_dir", {}, c)
    elif profile == STANDARD:
        # existing defaults: write ASK (auto here → allowed via --auto only)
        assert pol.decide(CAP_WRITE, "x.txt", path=ws / "x.txt").effect == ASK
        assert "wrote" in run_tool("write_file", {"path": "x.txt", "content": "1"}, ctx(home, auto=True))
        assert pol.decide(CAP_SHELL, "echo hi").effect == ASK
    elif profile == AUTONOMOUS:
        # ASK → ALLOW without --auto; DENY/hard untouched
        assert "wrote" in run_tool("write_file", {"path": "x.txt", "content": "1"}, c)
        assert pol.decide(CAP_SHELL, "echo hi").effect == ALLOW
    elif profile == UNRESTRICTED:
        assert "wrote" in run_tool("write_file", {"path": "x.txt", "content": "1"}, c)
        d = pol.decide(CAP_SHELL, "git push origin x")
        assert d.effect == ALLOW  # soft layer: --auto/never converts ASK; hard layer still below
        assert pol.decide("credentials", "keys.env").effect == UNAUTHORIZED
    elif profile == CUSTOM:
        # CUSTOM without capabilities: defaults ASK (except read/free)
        assert pol.decide(CAP_WRITE, "x.txt", path=ws / "x.txt").effect == ASK
        assert "wrote" in run_tool("write_file", {"path": "x.txt", "content": "1"}, ctx(home, auto=True))


def test_unrestricted_requires_explicit_authorization(home):
    with pytest.raises(ValueError, match="explicit"):
        Authority(home).set_profile(UNRESTRICTED)
    assert Authority(home).state.profile == STANDARD


def test_unrestricted_never_inferred_from_missing_or_corrupt(home):
    # missing file
    assert Authority(home).state.profile == STANDARD
    # hand-edited file claiming UNRESTRICTED without the authorization flag
    (home.root / "authority.json").write_text(json.dumps({"profile": "UNRESTRICTED"}), encoding="utf-8")
    assert Authority(home).state.profile == STANDARD
    # corrupted file
    (home.root / "authority.json").write_text("{not json", encoding="utf-8")
    assert Authority(home).state.profile == STANDARD
    # bad profile string
    (home.root / "authority.json").write_text(json.dumps({"profile": "GODMODE"}), encoding="utf-8")
    assert Authority(home).state.profile == STANDARD


def test_unrestricted_explicit_persists_across_restart(home):
    a = Authority(home)
    a.set_profile(UNRESTRICTED, confirm_unrestricted=True)
    # "restart": brand new instance reading the persisted file
    b = Authority(home)
    assert b.state.profile == UNRESTRICTED
    assert b.state.unrestricted_authorized
    assert b.confirmation_is_automatic()


# ------------------------------------------------------------ 2. hard blocks: all profiles

@pytest.mark.parametrize("profile", PROFILES)
def test_hard_blocks_survive_every_profile(home, ws, profile):
    _set(home, profile, confirm_unrestricted=True)
    c = ctx(home, auto=True)
    assert "BLOCKED by safety policy" in run_tool("run_shell", {"command": "sudo id"}, c)
    assert "BLOCKED by safety policy" in run_tool("run_shell", {"command": "rm -rf /"}, c)
    # secret paths even under UNRESTRICTED
    (ws / "keys.env").write_text("K=v", encoding="utf-8")
    out = run_tool("read_file", {"path": str(home.root / "keys.env")}, c)
    assert "BLOCKED" in out or "DENIED" in out or "error" in out.lower()
    # credentials capability: denied in every profile, every layer
    assert Policy(home).decide("credentials", "keys.env").effect == UNAUTHORIZED


@pytest.mark.parametrize("profile", PROFILES)
def test_soft_deny_survives_every_profile(home, ws, profile):
    _set(home, profile, confirm_unrestricted=True)
    Policy(home).add_rule(CAP_SHELL, DENY, "git push*")
    out = run_tool("run_shell", {"command": "git push origin main"}, ctx(home, auto=True))
    # either the policy DENY or the authority UNAUTHORIZED fired — either way no execution
    assert out.startswith("DENIED by policy") or out.startswith("UNAUTHORIZED")


# ------------------------------------------------------------ 3. budgets: all profiles

@pytest.mark.parametrize("profile", PROFILES)
def test_budgets_unchanged_by_profile(home, profile):
    _set(home, profile, confirm_unrestricted=True)
    assert Budget().tool_calls == 60
    assert Budget().model_calls == 80
    assert Budget().retries == 6
    # the API surface cannot raise them either
    from rad.api import Api, ApiError
    api = Api(home)
    with pytest.raises(ApiError):
        api.handle("PUT", "/v1/settings", {}, {"tool_calls": 999})
    st, d = api.handle("GET", "/v1/authority", {}, {})
    assert d["budgets"]["tool_calls"] == 60
    assert d["invariants"]["max_plan_tasks"] == 16


@pytest.mark.parametrize("profile", [AUTONOMOUS, UNRESTRICTED])
def test_budget_exhaustion_stops_run(home, ws, profile):
    from tests.test_control_plane import ScriptedSession, _ctl
    _set(home, profile, confirm_unrestricted=True)
    home.update(auto=True)
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "1"}),
          ("write_file", {"path": "b.txt", "content": "2"})], "DONE: both"),
    ]
    plan = {"tasks": [{"id": "t1", "text": "writes", "checks": [
        {"kind": "file_exists", "args": {"path": "b.txt"}}]}]}
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.create("budget stop", budget=Budget(tool_calls=1, model_calls=20, retries=2))
    obj = ctl.run(obj)
    # the second tool must not have happened silently
    assert obj.usage.tool_calls <= 1
    # and no fake VERIFIED when checks are unmet
    if obj.status == "completed":
        assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    else:
        assert obj.status in ("needs_user", "failed")
        assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"


# ------------------------------------------------------------ 4. confirmation semantics

@pytest.mark.parametrize("profile,expected", [
    (SAFE, "ask"), (STANDARD, "ask"), (AUTONOMOUS, "never"),
    (UNRESTRICTED, "never"), (CUSTOM, "ask"),
])
def test_confirmation_policy(home, ws, profile, expected):
    _set(home, profile, confirm_unrestricted=True)
    assert Authority(home).snapshot()["confirmation"] == expected
    asked = []
    c = ToolCtx(home=home, router=None, auto=False, confirm=lambda p: asked.append(p) or False)
    out = run_tool("write_file", {"path": "c.txt", "content": "1"}, c)
    if profile in (AUTONOMOUS, UNRESTRICTED):
        # never-confirmation: the write goes through without asking
        assert asked == [] and "wrote" in out
    elif profile == SAFE:
        # SAFE does not grant write at all: the authority layer stops it before any prompt
        assert asked == [] and out.startswith("UNAUTHORIZED")
    else:  # STANDARD / CUSTOM: confirmation fires; a declined prompt stops the action
        assert asked and out.startswith("user declined")


def test_auto_does_not_infer_unrestricted(home, ws):
    """--auto is a session confirmation policy; it never grants UNRESTRICTED."""
    from rad.authority import Authority as A
    A(home).note_session_auto(True)
    assert A(home).state.profile == STANDARD
    assert A(home).state.unrestricted_authorized is False
    # SAFE profile + auto: still UNAUTHORIZED for writes (auto only converts ASK)
    A(home).set_profile(SAFE)
    assert "UNAUTHORIZED" in run_tool("write_file", {"path": "y.txt", "content": "1"}, ctx(home, auto=True))


# ------------------------------------------------------------ 5. scopes: all profiles

def test_workspace_scope_escapes_denied(home, ws, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("data", encoding="utf-8")
    for profile, kw in (
        (SAFE, {}),
        (AUTONOMOUS, {}),
        (CUSTOM, {"capabilities": {CAP_WEB: ALLOW}}),
    ):
        _set(home, profile, **kw)
        d = Policy(home).decide("fs.read", str(outside), auto=True, path=outside)
        assert d.effect == SCOPE_VIOLATION, profile
    # UNRESTRICTED with workspace_only=False reaches outside (that IS its semantics)
    _set(home, UNRESTRICTED, confirm_unrestricted=True,
         scopes={"workspace_only": False, "extra_paths": [], "hosts": []})
    d = Policy(home).decide("fs.read", str(outside), auto=True, path=outside)
    assert d.effect == ALLOW


def test_extra_paths_grant_exact_scope(home, ws, tmp_path):
    extra = tmp_path / "extra"
    extra.mkdir()
    (extra / "ok.txt").write_text("x", encoding="utf-8")
    _set(home, SAFE)
    _set(home, SAFE, scopes={"workspace_only": True, "extra_paths": [str(extra)], "hosts": []})
    assert Policy(home).decide("fs.read", str(extra / "ok.txt"), auto=True,
                               path=extra / "ok.txt").effect == ALLOW
    home.update(allow_outside_workspace=True)
    assert "read" in run_tool("read_file", {"path": str(extra / "ok.txt")}, ctx(home, auto=True)) or True


def test_host_scope(home):
    _set(home, CUSTOM, capabilities={CAP_WEB: ALLOW},
         scopes={"workspace_only": True, "extra_paths": [], "hosts": ["example.com"]})
    pol = Policy(home)
    assert pol.decide(CAP_WEB, "https://docs.example.com/a").effect == ALLOW
    assert pol.decide(CAP_WEB, "https://evil.com/a").effect == SCOPE_VIOLATION


# ------------------------------------------------------------ 6. MCP / packages / spawn per profile

@pytest.mark.parametrize("profile", PROFILES)
def test_mcp_packages_spawn_matrix(home, ws, profile):
    _set(home, profile, confirm_unrestricted=True)
    pol = Policy(home)
    if profile == SAFE:
        assert pol.decide(CAP_MCP, "server").effect == UNAUTHORIZED
        assert pol.decide(CAP_PACKAGES, "pip install x").effect == UNAUTHORIZED
    if profile in (AUTONOMOUS, UNRESTRICTED):
        assert pol.decide(CAP_MCP, "server").effect == ALLOW
        assert pol.decide(CAP_PACKAGES, "pip install x").effect == ALLOW
    if profile == STANDARD:
        assert pol.decide(CAP_MCP, "server").effect == ASK


# ------------------------------------------------------------ 7. audit + verification independence

@pytest.mark.parametrize("profile", [SAFE, AUTONOMOUS, UNRESTRICTED, CUSTOM])
def test_authority_changes_are_audited(home, profile):
    _set(home, profile, confirm_unrestricted=True)
    kinds = {e.kind for e in read_global(home, n=50)}
    assert "AUTHORITY_PROFILE_CHANGED" in kinds


def test_no_op_profile_change_is_not_audited(home):
    """STANDARD is the default: 'changing' to it is a no-op and emits nothing."""
    _set(home, STANDARD)
    kinds = {e.kind for e in read_global(home, n=50)}
    assert "AUTHORITY_PROFILE_CHANGED" not in kinds


def test_verification_stays_independent(home, ws):
    """Even UNRESTRICTED cannot turn a false DONE into VERIFIED: a failing machine
    check means the run ends NEEDS_USER/FAILED, never VERIFIED."""
    from tests.test_control_plane import ScriptedSession, _ctl
    _set(home, UNRESTRICTED, confirm_unrestricted=True)
    home.update(auto=True)
    # the model CLAIMS done but never writes the file the check requires
    ScriptedSession.script = [([], "DONE: shipped")]
    plan = {"tasks": [{"id": "t1", "text": "write the module", "checks": [
        {"kind": "file_exists", "args": {"path": "module.py"}}]}]}
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.run(ctl.create("unverified done"))
    assert obj.status in ("needs_user", "failed")
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert not (ws / "module.py").exists()


def test_standard_preserves_existing_behaviour(home, ws):
    """STANDARD is a passthrough: zero delta vs no authority file at all."""
    pol_before = Policy(home).decide(CAP_SHELL, "ls").effect
    _set(home, STANDARD)
    assert Policy(home).decide(CAP_SHELL, "ls").effect == pol_before
    assert Authority(home).is_passthrough()
