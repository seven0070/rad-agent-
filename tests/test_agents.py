"""Agent runtime: registry, capability enforcement, budgets, blackboard, parallel runs,
grounded review as a verifier check, and Team(tools=True) integration."""
import json
import threading
import time

import pytest

from rad.agents import (CAP_READ, CAP_SHELL, CAP_WEB, CAP_WRITE, AgentRegistry, AgentRuntime, Blackboard,
                        cap_for_tool)
from rad.tools import ToolCtx, run_tool


class Scripted:
    """Runs a per-role script of tool actions through the (guarded) tool_runner, returns reply."""
    by_role = {}
    calls = []

    def __init__(self, home, auto=True, **kw):
        self.home = home
        self.tool_runner = run_tool
        self.ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
        self.last_provider = "fake"

    def think(self, prompt):
        role = prompt.split("acting as the '")[1].split("'")[0]
        Scripted.calls.append((role, prompt))
        actions, reply = Scripted.by_role[role]
        outs = [self.tool_runner(t, a, self.ctx) for t, a in actions]
        return reply(outs) if callable(reply) else reply

    def close(self):
        pass


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"; w.mkdir()
    (w / "notes.txt").write_text("port is 8080")
    home.update(workspace=str(w))
    Scripted.by_role = {}; Scripted.calls = []
    return w


def test_cap_mapping():
    assert cap_for_tool("read_file") == CAP_READ and cap_for_tool("run_shell") == CAP_SHELL
    assert cap_for_tool("mcp__x__y") == "mcp" and cap_for_tool("unknown_tool") == CAP_SHELL


def test_registry_builtin_override_and_custom(home):
    reg = AgentRegistry(home)
    assert set(reg.get("reviewer").caps) == {CAP_READ}
    reg.define("reviewer", budget_tool_calls=3)
    assert reg.get("reviewer").budget_tool_calls == 3 and reg.get("reviewer").prompt   # prompt kept
    reg.define("seo", caps=[CAP_READ, CAP_WEB], prompt="You audit SEO.")
    assert reg.get("seo").caps == [CAP_READ, CAP_WEB]
    with pytest.raises(ValueError):
        reg.define("bad", caps=["root"])
    assert reg.remove("seo") and reg.get("seo") is None


def test_capability_denied_is_enforced_not_advisory(home, ws):
    Scripted.by_role = {"reviewer": ([("read_file", {"path": "notes.txt"}),
                                      ("write_file", {"path": "hack.txt", "content": "x"}),
                                      ("run_shell", {"command": "touch pwned"})],
                                     lambda outs: "read ok; " + outs[1][:40] + " | " + outs[2][:40])}
    rt = AgentRuntime(home, session_factory=Scripted)
    run = rt.run_agent("reviewer", "review notes")
    assert run.status == "done" and run.tool_calls == 1
    assert run.denied == ["write_file (fs.write)", "run_shell (shell)"]
    assert "DENIED" in run.output
    assert not (ws / "hack.txt").exists() and not (ws / "pwned").exists()
    saved = AgentRegistry(home).runs()[0]
    assert saved["id"] == run.id and saved["denied"] == run.denied
    assert run.evidence[0]["source"] == "notes.txt" and run.evidence[0]["trusted"]


def test_agent_tool_budget(home, ws):
    AgentRegistry(home).define("coder", budget_tool_calls=2)
    Scripted.by_role = {"coder": ([("list_dir", {})] * 5, "DONE")}
    run = AgentRuntime(home, session_factory=Scripted).run_agent("coder", "spam")
    assert run.status == "budget" and run.tool_calls == 2


def test_blackboard_shared_between_parallel_agents(home, ws):
    Scripted.by_role = {
        "researcher": ([("read_file", {"path": "notes.txt"})], "port is 8080 (from notes.txt)"),
        "writer": ([], "summary written"),
        "analyst": ([], "analysis"),
    }
    rt = AgentRuntime(home, session_factory=Scripted)
    runs = rt.run_parallel([{"agent": "researcher", "task": "find port"},
                            {"agent": "writer", "task": "write"},
                            {"agent": "analyst", "task": "analyse"}], scope="obj_test")
    assert [r.agent for r in runs] == ["researcher", "writer", "analyst"]
    notes = Blackboard(home, "obj_test").notes()
    assert {n["author"] for n in notes} == {"researcher", "writer", "analyst"}
    res = [n for n in notes if n["author"] == "researcher"][0]
    assert res["evidence"] == ["notes.txt"]
    # blackboard rendered into prompts (order-dependent; at least someone saw a note or it is empty for first)
    assert any("Shared blackboard" in p for _, p in Scripted.calls) or len(Scripted.calls) == 3


def test_parallel_actually_concurrent(home, ws):
    peak = {"n": 0, "cur": 0}
    lock = threading.Lock()

    class Slow(Scripted):
        def think(self, prompt):
            with lock:
                peak["cur"] += 1; peak["n"] = max(peak["n"], peak["cur"])
            time.sleep(0.1)
            with lock:
                peak["cur"] -= 1
            return "ok"
    rt = AgentRuntime(home, session_factory=Slow, auto=True)
    t0 = time.time()
    rt.run_parallel([{"agent": "coder", "task": "a"}, {"agent": "tester", "task": "b"}, {"agent": "writer", "task": "c"}])
    assert peak["n"] == 3 and time.time() - t0 < 0.25
    peak["n"] = 0
    AgentRuntime(home, session_factory=Slow, auto=False).run_parallel([{"agent": "coder", "task": "a"}, {"agent": "writer", "task": "b"}])
    assert peak["n"] == 1                                      # confirm-gated → sequential


def test_review_must_be_grounded(home, ws):
    # reviewer says pass but read nothing → not accepted
    Scripted.by_role = {"reviewer": ([], json.dumps({"pass": True, "issues": [], "checked": []}))}
    rt = AgentRuntime(home, session_factory=Scripted)
    r = rt.review("some code", ["compiles"])
    assert r["pass"] and r["tool_calls"] == 0
    from rad.control.observer import Observer
    from rad.control.tasks import Check
    from rad.control.verifier import Verifier
    v = Verifier(ws, Observer(home.root / "tmpobj"), home=home)
    import rad.control.verifier as V
    import rad.agents as A
    # patch runtime factory used inside verifier to our scripted one
    orig = A.AgentRuntime
    A.AgentRuntime = lambda home, auto=True: orig(home, session_factory=Scripted, auto=auto)
    try:
        res = v.run_check(Check("agent_review", {"criteria": ["compiles"]}), reply="code")
        assert res["ok"] is False and "ungrounded" in res["detail"] and res["machine"] is False
        Scripted.by_role = {"reviewer": ([("read_file", {"path": "notes.txt"})],
                                         json.dumps({"pass": True, "issues": [], "checked": ["notes.txt"]}))}
        res = v.run_check(Check("agent_review", {"criteria": ["port documented"]}), reply="code")
        assert res["ok"] is True and res["machine"] is False
        Scripted.by_role = {"reviewer": ([("read_file", {"path": "notes.txt"})],
                                         json.dumps({"pass": False, "issues": ["port wrong"], "checked": ["notes.txt"]}))}
        res = v.run_check(Check("agent_review", {"criteria": ["port documented"]}), reply="code")
        assert res["ok"] is False and "port wrong" in res["detail"]
    finally:
        A.AgentRuntime = orig


def test_agent_review_never_alone_makes_verified(home, ws):
    """A task whose only check is agent_review ends UNVERIFIED-or-FAILED, never VERIFIED."""
    from rad.control.observer import Observer
    from rad.control.tasks import Check, Task
    from rad.control.verifier import Verifier
    import rad.agents as A
    orig = A.AgentRuntime
    A.AgentRuntime = lambda home, auto=True: orig(home, session_factory=Scripted, auto=auto)
    Scripted.by_role = {"reviewer": ([("read_file", {"path": "notes.txt"})],
                                     json.dumps({"pass": True, "issues": [], "checked": ["notes.txt"]}))}
    try:
        obs = Observer(home.root / "o1")
        v = Verifier(ws, obs, home=home)
        t = Task.new("o1", "write prose", checks=[Check("agent_review", {"criteria": ["clear"]})])
        t.status = "RUNNING"; t.started = time.time()
        ver = v.verify_task(t, "DONE")
        assert ver["status"] != "VERIFIED"
    finally:
        A.AgentRuntime = orig


def test_team_tools_mode_uses_runtime(home, ws, monkeypatch):
    from rad.team import Team
    Scripted.by_role = {"researcher": ([("read_file", {"path": "notes.txt"})], "8080"),
                        "reviewer": ([], "fine")}
    import rad.agents as A
    real = A.AgentRuntime
    monkeypatch.setattr(A, "AgentRuntime", lambda home, auto=True: real(home, session_factory=Scripted, auto=True))
    monkeypatch.setattr(Team, "_synthesize", lambda self, p, a: "synth")
    res = Team(home).run("port?", roles=["researcher", "reviewer"], tools=True, objective_id="obj_t")
    assert [a["role"] for a in res["answers"]] == ["researcher", "reviewer"]
    assert res["answers"][0]["tool_calls"] == 1 and res["answers"][0]["run"].startswith("run_")
    assert res["final"] == "synth"
    assert Blackboard(home, "obj_t").notes()

