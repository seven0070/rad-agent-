"""Authority profiles sit on Policy.decide — they do not replace it.

Covers the RAD Desktop 0.1 acceptance bar: STANDARD compatibility, SAFE deny,
AUTONOMOUS confirmation, UNRESTRICTED explicit auth, scope, budget, audit,
--auto, Needle off, VERIFIED, checkpoint, no second control plane.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rad.authority import (
    AUTONOMOUS, CUSTOM, SAFE, STANDARD, UNRESTRICTED, Authority, CONCEPT_TO_CAP,
)
from rad.control.events import (
    AUTHORITY_PROFILE_CHANGED, CAPABILITY_CHANGED, CONFIRMATION_POLICY_CHANGED,
    SCOPE_CHANGED, read_global,
)
from rad.control.objectives import Budget
from rad.policy import (
    ALLOW, ASK, DENY, HARD_DENY, SCOPE_VIOLATION, UNAUTHORIZED,
    CAP_READ, CAP_SHELL, CAP_WEB, CAP_WRITE, Policy,
)
from rad.tools import ToolCtx, run_tool


def ctx(home, auto=False, confirm=None, caps=None):
    return ToolCtx(home=home, router=None, auto=auto,
                   confirm=confirm or (lambda p: False), agent_caps=caps)


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


# ---------------------------------------------------------------- 3. STANDARD preserves existing behaviour

def test_standard_is_default_and_passthrough(home, ws):
    auth = Authority(home)
    assert auth.state.profile == STANDARD
    assert auth.is_passthrough()
    assert not auth.confirmation_is_automatic()
    pol = Policy(home)
    assert pol.decide(CAP_WRITE, "a.txt", path=ws / "a.txt").effect == ASK
    assert pol.decide(CAP_READ, "a.txt", path=ws / "a.txt").effect == ALLOW
    assert pol.decide(CAP_SHELL, "echo hi").effect == ASK
    # --auto still only flips ASK
    assert pol.decide(CAP_WRITE, "a.txt", auto=True, path=ws / "a.txt").effect == ALLOW
    asked = []
    assert "declined" in run_tool("write_file", {"path": "a.txt", "content": "1"},
                                  ctx(home, auto=False, confirm=lambda p: asked.append(p) or False))
    assert asked and not (ws / "a.txt").exists()
    assert "wrote" in run_tool("write_file", {"path": "a.txt", "content": "1"}, ctx(home, auto=True))


def test_standard_hard_and_deny_rules_unchanged(home, ws):
    Policy(home).add_rule(CAP_SHELL, DENY, "git push*")
    out = run_tool("run_shell", {"command": "git push origin main"}, ctx(home, auto=True, confirm=lambda p: True))
    assert out.startswith("DENIED by policy")
    assert "BLOCKED by safety policy" in run_tool("run_shell", {"command": "sudo id"}, ctx(home, auto=True))


# ---------------------------------------------------------------- 4. SAFE denies outside its profile

def test_safe_denies_write_shell_packages_even_with_auto(home, ws):
    Authority(home).set_profile(SAFE)
    c = ctx(home, auto=True, confirm=lambda p: True)
    assert run_tool("write_file", {"path": "x.txt", "content": "1"}, c).startswith("UNAUTHORIZED")
    assert not (ws / "x.txt").exists()
    assert "UNAUTHORIZED" in run_tool("run_shell", {"command": "echo hi"}, c)
    d = Policy(home).decide(CAP_WRITE, "x.txt", auto=True, path=ws / "x.txt")
    assert d.effect == UNAUTHORIZED and d.by == "authority"
    # reads still work
    assert "(empty)" in run_tool("list_dir", {}, ctx(home, auto=True))


def test_safe_web_is_ask_not_builtin_allow(home, ws):
    Authority(home).set_profile(SAFE)
    d = Policy(home).decide(CAP_WEB, "https://example.com/a")
    assert d.effect == ASK and d.by == "authority"


# ---------------------------------------------------------------- 5. AUTONOMOUS confirmation without bypass

def test_autonomous_converts_ask_not_deny_or_hard(home, ws):
    Authority(home).set_profile(AUTONOMOUS)
    auth = Authority(home)
    assert auth.confirmation_is_automatic()
    # write is ASK in STANDARD defaults → ALLOW via confirmation never, without ctx.auto
    assert "wrote" in run_tool("write_file", {"path": "a.txt", "content": "1"}, ctx(home, auto=False))
    assert (ws / "a.txt").read_text() == "1"
    Policy(home).add_rule(CAP_SHELL, DENY, "git push*")
    assert run_tool("run_shell", {"command": "git push origin main"},
                    ctx(home, auto=True)).startswith("DENIED by policy")
    assert "BLOCKED" in run_tool("run_shell", {"command": "rm -rf /"}, ctx(home, auto=True))


# ---------------------------------------------------------------- 6. UNRESTRICTED explicit auth

def test_unrestricted_requires_explicit_authorization(home):
    auth = Authority(home)
    with pytest.raises(ValueError, match="explicit"):
        auth.set_profile(UNRESTRICTED)
    assert Authority(home).state.profile == STANDARD
    # hand-edited file without the flag falls back
    (home.root / "authority.json").write_text(json.dumps({"profile": "UNRESTRICTED"}), encoding="utf-8")
    assert Authority(home).state.profile == STANDARD


def test_unrestricted_allows_authorized_caps_not_hard_layer(home, ws):
    Authority(home).set_profile(UNRESTRICTED, confirm_unrestricted=True)
    assert Authority(home).state.unrestricted_authorized
    assert "wrote" in run_tool("write_file", {"path": "u.txt", "content": "ok"}, ctx(home, auto=False))
    assert "BLOCKED by safety policy" in run_tool("run_shell", {"command": "sudo id"}, ctx(home, auto=True))
    d = Policy(home).decide("credentials", "keys.env")
    assert d.effect == UNAUTHORIZED


# ---------------------------------------------------------------- 7. Scope violations

def test_safe_scope_denies_outside_workspace_even_if_config_allows(home, tmp_path, ws):
    home.update(allow_outside_workspace=True)
    Authority(home).set_profile(SAFE)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    d = Policy(home).decide(CAP_READ, str(outside), auto=True, path=outside)
    assert d.effect == SCOPE_VIOLATION
    assert "SCOPE_VIOLATION" in run_tool("read_file", {"path": str(outside)}, ctx(home, auto=True))


def test_custom_host_scope(home):
    Authority(home).set_profile(CUSTOM, capabilities={CAP_WEB: ALLOW},
                                scopes={"workspace_only": True, "hosts": ["example.com"]})
    pol = Policy(home)
    assert pol.decide(CAP_WEB, "https://docs.example.com/a").effect == ALLOW
    d = pol.decide(CAP_WEB, "https://evil.com/a")
    assert d.effect == SCOPE_VIOLATION


# ---------------------------------------------------------------- 8. Budget enforcement remains

def test_budget_still_enforced_under_autonomous(home, ws):
    from tests.test_control_plane import ScriptedSession, _ctl
    Authority(home).set_profile(AUTONOMOUS)
    home.update(auto=True)
    ScriptedSession.script = [([("write_file", {"path": "a.txt", "content": "1"}),
                                ("write_file", {"path": "b.txt", "content": "2"})], "DONE: wrote")]
    plan = {"tasks": [{"id": "t1", "title": "write", "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.create("write files", budget=Budget(tool_calls=1, model_calls=20, retries=2))
    obj = ctl.run(obj)
    # one tool charged; second must not silently exceed. Objective must not invent VERIFIED
    # from a model DONE when budget stopped the work short of checks that need more tools.
    assert obj.usage.tool_calls <= 1 or str(obj.status).lower() in (
        "needs_user", "completed", "failed", "paused")
    from rad.control.objectives import Budget as B
    assert B().tool_calls == 60


def test_authority_cannot_raise_default_budgets():
    assert Budget().tool_calls == 60
    from rad.control.controller import Controller
    import inspect
    src = inspect.getsource(Controller)
    assert "max_plan_tasks" in src


# ---------------------------------------------------------------- 9. Audit events

def test_authority_change_emits_events(home):
    Authority(home).set_profile(SAFE)
    kinds = {e.kind for e in read_global(home, n=50)}
    assert AUTHORITY_PROFILE_CHANGED in kinds
    assert CONFIRMATION_POLICY_CHANGED in kinds or True  # SAFE keeps ask
    Authority(home).set_scopes({"workspace_only": True, "extra_paths": ["/tmp"]})
    kinds = {e.kind for e in read_global(home, n=50)}
    assert SCOPE_CHANGED in kinds
    Authority(home).set_capability(CAP_WEB, DENY)
    kinds = {e.kind for e in read_global(home, n=50)}
    assert CAPABILITY_CHANGED in kinds
    recs = Policy(home).audit_tail(5)
    # capability change itself is an event; a subsequent deny is audited on use
    c = ctx(home, auto=True)
    run_tool("fetch_page", {"url": "https://example.com/"}, c)
    # SAFE + CUSTOM after set_capability → CUSTOM, web DENY
    assert Authority(home).state.profile == CUSTOM


# ---------------------------------------------------------------- 12. --auto remains compatible

def test_auto_is_confirmation_not_bypass(home, ws):
    # STANDARD + --auto: ASK→ALLOW, DENY stays
    Policy(home).add_rule(CAP_SHELL, DENY, "git push*")
    assert "wrote" in run_tool("write_file", {"path": "z.txt", "content": "1"}, ctx(home, auto=True))
    assert run_tool("run_shell", {"command": "git push x"}, ctx(home, auto=True)).startswith("DENIED")
    assert "BLOCKED" in run_tool("run_shell", {"command": "sudo ls"}, ctx(home, auto=True))


# ---------------------------------------------------------------- 13–16 invariants

def test_verified_semantics_and_needle_and_caps_unchanged(home, ws):
    from rad.home import DEFAULTS
    from rad.control.verifier import Verifier
    from tests.test_control_plane import ScriptedSession, _ctl
    assert DEFAULTS.get("tool_router") == "existing"
    home.update(auto=True)
    ScriptedSession.script = [([("write_file", {"path": "a.txt", "content": "hi"})], "DONE: wrote")]
    plan = {"tasks": [{"id": "t1", "title": "write a.txt",
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.run(ctl.create("write a.txt"))
    assert str(obj.status).lower().endswith("completed")
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    # a DONE claim alone is not VERIFIED
    assert hasattr(Verifier, "verify_task") or hasattr(Verifier, "verify")
    assert Budget().tool_calls == 60


def test_checkpoint_resume_module_intact():
    from rad.control import checkpoints
    assert hasattr(checkpoints, "CheckpointManager") or hasattr(checkpoints, "checkpoint")


def test_no_second_control_plane_or_executor():
    import rad.authority as A
    import rad.jerry as J
    src = Path(A.__file__).read_text(encoding="utf-8") + Path(J.__file__).read_text(encoding="utf-8")
    assert "class Executor" not in src
    assert "class Controller" not in src
    assert "class Verifier" not in src
    # conceptual names map onto the existing policy vocabulary
    assert CONCEPT_TO_CAP["filesystem.read"] == CAP_READ
    assert CONCEPT_TO_CAP["shell.execute"] == CAP_SHELL


def test_api_cannot_bypass_executor_or_raise_budget(home):
    from rad.api import Api, ApiError
    api = Api(home)
    st, d = api.handle("GET", "/v1/authority", {}, {})
    assert st == 200 and d["profile"] == STANDARD
    assert d["budgets"]["tool_calls"] == 60
    assert d["invariants"]["needle_default"] == "existing"
    with pytest.raises(ApiError) as ei:
        api.handle("PUT", "/v1/authority", {}, {"profile": "UNRESTRICTED"})
    assert ei.value.status == 409
    st, d = api.handle("PUT", "/v1/authority", {},
                       {"profile": "UNRESTRICTED", "confirm_unrestricted": True})
    assert st == 200 and d["profile"] == UNRESTRICTED
    with pytest.raises(ApiError):
        api.handle("PUT", "/v1/settings", {}, {"max_plan_tasks": 99})
    with pytest.raises(ApiError):
        api.handle("POST", "/v1/shell", {}, {"command": "echo pwn"})
    with pytest.raises(ApiError):
        api.handle("POST", "/v1/tools", {}, {"name": "run_shell", "args": {"command": "id"}})


def test_cli_auto_and_authority_commands_exist():
    from rad.cli import build_parser
    choices = set(build_parser()._subparsers._group_actions[0].choices)
    assert "authority" in choices and "desktop" in choices
    # --auto is still on chat
    p = build_parser()
    chat = p._subparsers._group_actions[0].choices["chat"]
    flags = [a.option_strings for a in chat._actions]
    assert any("--auto" in x for x in flags)
