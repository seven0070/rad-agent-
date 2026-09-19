"""v0.3.1 plan-timeout resilience (Gen2 theme 2).

When the LLM planner times out / returns empty / malformed / non-JSON once,
RAD retries (default 1) for a structured JSON plan with machine checks
*before* falling back to `_fallback(obj)`.

F-17 contract is unchanged: exhausted retries still split `obj.goal` only,
cap 7, no checks. Needle OFF. Caps unchanged. False DONE stays 0.
"""
from __future__ import annotations

import json

from rad import __version__
from rad.control import Controller
from rad.control import events as E
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.planner import (
    DEFAULT_PLAN_RETRIES,
    MAX_PLAN_RETRIES,
    PLAN_RETRY_NUDGE,
    Planner,
)
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from rad.tools import ToolCtx, run_tool

from tests.test_f17_fallback_investigation import (
    ONE_SENTENCE_GOAL,
    SEVEN_SENTENCE_GOAL,
    MODEL_PROSE_SEVEN,
    _fallback_texts,
)


VALID_PLAN = {
    "tasks": [
        {"id": "t1", "text": "write adder", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "add.py"}}]},
        {"id": "t2", "text": "write tests", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "test_add.py"}}]},
    ],
    "objective_checks": [
        {"kind": "json_valid", "args": {"path": "result.json"}},
    ],
}


class ScriptedSession:
    script = []
    prompts = []

    def __init__(self, home, auto=False, **kw):
        self.home = home
        self.tool_runner = run_tool
        self.ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)

    def think(self, prompt: str) -> str:
        type(self).prompts.append(prompt)
        if not type(self).script:
            return "DONE: nothing left in script"
        step = type(self).script.pop(0)
        if isinstance(step, Exception):
            raise step
        actions, reply = step
        for tool, args in actions:
            self.tool_runner(tool, args, self.ctx)
        return reply

    def close(self):
        pass


class SequentialLLM:
    """Pop scripted plan replies. Exceptions in the script are raised."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if not self.replies:
            raise TimeoutError("no more plan replies")
        step = self.replies.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


def _json_plan(plan=None) -> str:
    return json.dumps(plan or VALID_PLAN)


def _plan(llm, goal: str = ONE_SENTENCE_GOAL, **kw):
    return Planner(llm, "/tmp/ws", **kw).plan(Objective.new(goal))


def _ctl(home, llm):
    return Controller(home, session_factory=ScriptedSession, llm=llm, quiet=True)


def _plan_event(ctl, obj):
    evs = list(EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED))
    assert evs, "missing PLAN_CREATED"
    return evs[0]


# ---------------------------------------------------------------- architecture freeze

def test_plan_timeout_resilience_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.4.6"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert "plan_retries" not in DEFAULTS
    assert resolve_tool_router(home) == "existing"


def test_default_retries_is_one_and_hard_capped():
    assert DEFAULT_PLAN_RETRIES == 1
    assert MAX_PLAN_RETRIES == 3
    assert Planner(None, "/tmp/ws").retries == 1
    assert Planner(None, "/tmp/ws", retries=99).retries == 3
    assert Planner(None, "/tmp/ws", retries=-4).retries == 0
    assert Planner(None, "/tmp/ws", retries="nope").retries == 1


# ---------------------------------------------------------------- success after one failure

def test_timeout_then_valid_json_is_llm_not_fallback():
    llm = SequentialLLM([TimeoutError("nvidia plan timeout"), _json_plan()])
    res = _plan(llm)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert texts == ["write adder", "write tests"]
    assert all(t.checks for t in res["graph"].tasks.values())
    assert len(llm.prompts) == 2
    assert PLAN_RETRY_NUDGE.strip() in llm.prompts[1]
    assert PLAN_RETRY_NUDGE not in llm.prompts[0]


def test_empty_then_valid_json_is_llm():
    llm = SequentialLLM(["", _json_plan()])
    res = _plan(llm)
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert [t.text for t in res["graph"].tasks.values()] == ["write adder", "write tests"]


def test_malformed_then_valid_json_is_llm():
    llm = SequentialLLM(["{not json", _json_plan()])
    res = _plan(llm)
    assert res["source"] == "llm"
    assert res["attempts"] == 2


def test_prose_then_valid_json_does_not_parse_prose():
    """Retry recovers a JSON plan. Model prose from attempt 1 is discarded (F-17)."""
    llm = SequentialLLM([MODEL_PROSE_SEVEN, _json_plan()])
    res = _plan(llm, ONE_SENTENCE_GOAL)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "llm"
    assert texts == ["write adder", "write tests"]
    assert all("Create the project" not in t for t in texts)


def test_empty_tasks_graph_retries_then_llm():
    llm = SequentialLLM([json.dumps({"tasks": []}), _json_plan()])
    res = _plan(llm)
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert len(res["graph"].tasks) == 2


# ---------------------------------------------------------------- first-try success unchanged (Scenario A)

def test_valid_first_try_does_not_retry():
    llm = SequentialLLM([_json_plan(), _json_plan()])
    res = _plan(llm)
    assert res["source"] == "llm"
    assert res["attempts"] == 1
    assert len(llm.prompts) == 1
    assert PLAN_RETRY_NUDGE not in llm.prompts[0]


# ---------------------------------------------------------------- exhausted retries → F-17 fallback

def test_exhausted_timeouts_still_fallback_goal_only():
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2"), TimeoutError("t3")])
    res = _plan(llm, ONE_SENTENCE_GOAL)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "fallback"
    assert res["attempts"] == 2   # default 1 retry → 2 attempts, not unbounded
    assert len(texts) == 1
    assert "sum of 2 and 4" in texts[0]
    assert "Create the project" not in texts[0]
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert len(llm.prompts) == 2


def test_exhausted_on_seven_sentence_goal_is_clause_split_cap_7():
    llm = SequentialLLM(["", "{not json"])
    res = _plan(llm, SEVEN_SENTENCE_GOAL)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "fallback"
    assert len(texts) == 7
    assert all(not t.checks for t in res["graph"].tasks.values())
    joined = " ".join(texts)
    assert "Create the project" in joined
    assert "Verify the result" in joined


def test_retries_zero_is_one_shot_fallback():
    llm = SequentialLLM([TimeoutError("once"), _json_plan()])
    res = _plan(llm, retries=0)
    assert res["source"] == "fallback"
    assert res["attempts"] == 1
    assert len(llm.prompts) == 1


def test_fallback_clause_split_contract_unchanged():
    """F-17: `_fallback` is still goal-only, cap 7, no checks."""
    texts = _fallback_texts("write a file and then read it back")
    assert texts == ["write a file", "read it back"]
    g = Planner(None, "/tmp/ws")._fallback(Objective.new(SEVEN_SENTENCE_GOAL))
    assert len(g.tasks) == 7
    assert all(not t.checks for t in g.tasks.values())


# ---------------------------------------------------------------- controller (PLAN_CREATED)

def test_controller_timeout_then_json_emits_llm(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([TimeoutError("nvidia plan timeout"), _json_plan()])
    ctl = _ctl(home, llm)
    obj = ctl.create(SEVEN_SENTENCE_GOAL)
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "llm"
    assert ev.data["attempts"] == 2
    assert len(g.tasks) == 2
    assert [t.text for t in g.tasks.values()] == ["write adder", "write tests"]
    assert all(t.checks for t in g.tasks.values())


def test_controller_exhausted_emits_fallback_seven(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    ctl = _ctl(home, llm)
    obj = ctl.create(SEVEN_SENTENCE_GOAL)
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "fallback"
    assert ev.data["attempts"] == 2
    assert len(g.tasks) == 7
    assert all(not t.checks for t in g.tasks.values())


def test_controller_first_try_json_is_still_one_attempt(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([_json_plan()])
    ctl = _ctl(home, llm)
    obj = ctl.create(ONE_SENTENCE_GOAL)
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "llm"
    assert ev.data["attempts"] == 1
    assert len(g.tasks) == 2


def test_home_cfg_plan_retries_zero_is_one_shot(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    home.cfg["plan_retries"] = 0
    llm = SequentialLLM([TimeoutError("once"), _json_plan()])
    ctl = _ctl(home, llm)
    obj = ctl.create(ONE_SENTENCE_GOAL)
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "fallback"
    assert ev.data["attempts"] == 1
    assert len(g.tasks) == 1


# ---------------------------------------------------------------- false DONE stays 0

def test_fallback_after_retries_is_not_objective_verified(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [([("list_dir", {})], "DONE: all done")] * 4
    ScriptedSession.prompts = []
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    ctl = _ctl(home, llm)
    obj = ctl.run(ctl.create(ONE_SENTENCE_GOAL, budget=Budget(tool_calls=8, retries=1)))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    g = ctl.load_graph(obj)
    for t in g.tasks.values():
        if t.verification:
            assert t.verification.get("status") != "VERIFIED"
