"""Jerry is an operator layer, never a tool path."""
from __future__ import annotations

import inspect

import pytest

from rad.jerry import Jerry, _FORBIDDEN
from rad.tools import run_tool


def test_jerry_has_no_tool_execution_surface():
    for name in _FORBIDDEN:
        assert not hasattr(Jerry, name)
    src = inspect.getsource(Jerry)
    assert "run_tool(" not in src
    assert "Executor(" not in src
    j = Jerry.__new__(Jerry)
    with pytest.raises(AttributeError, match="no run_tool"):
        getattr(j, "run_tool")


def test_jerry_explains_policy_does_not_override(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    from rad.authority import Authority, SAFE
    j = Jerry(home)
    snap = j.authority_state()
    assert snap["profile"] == "STANDARD"
    d = j.explain_decision("fs.write", "a.txt", path=str(ws / "a.txt"))
    assert d["effect"] == "ASK"
    assert "does not override" in d["note"]
    Authority(home).set_profile(SAFE)
    d = j.explain_decision("shell", "echo hi")
    assert d["effect"] == "UNAUTHORIZED"
    # Jerry still cannot write a file itself
    assert not (ws / "a.txt").exists()


def test_jerry_chat_uses_session_not_private_runner(home):
    seen = {}

    class S:
        def __init__(self, home, auto=False):
            seen["auto"] = auto
            seen["home"] = home

        def think(self, text):
            seen["text"] = text
            return f"jerry-echo:{text}"

        def close(self):
            seen["closed"] = True

    j = Jerry(home, session_factory=lambda h, auto=False: S(h, auto=auto))
    assert j.chat("hello") == "jerry-echo:hello"
    assert seen["text"] == "hello" and seen["closed"] is True


def test_jerry_propose_objective_uses_controller(home):
    created = {}

    class FakeObj:
        id = "obj_test"
        goal = "do x"
        status = "pending"

    class Ctl:
        def __init__(self, home):
            pass

        def create(self, goal, success_criteria=None, constraints=None, **kw):
            created["goal"] = goal
            created["criteria"] = success_criteria
            return FakeObj()

        def run(self, obj):
            raise AssertionError("Jerry must not run the objective unless confirmation is automatic")

    j = Jerry(home, controller_factory=lambda h: Ctl(h))
    out = j.propose_objective("do x", run=True)
    assert out["id"] == "obj_test" and out["started"] is False
    assert created["goal"] == "do x"


def test_jerry_cannot_be_used_as_run_tool(home, tmp_path):
    """Guard: even a confused caller using Jerry in place of a tool runner fails."""
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    j = Jerry(home)
    out = run_tool("write_file", {"path": "x.txt", "content": "no"}, j)  # type: ignore[arg-type]
    assert "wrote" not in out
    assert not (ws / "x.txt").exists()
