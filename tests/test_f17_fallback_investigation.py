"""F-20260918-17 targeted investigation: planner timeout → fallback.

Investigate-first. No product patch. Needle off, max_plan_tasks 16, default
Budget.tool_calls 60 — asserted, not changed.

Question: when the LLM planner fails or times out, does fallback convert
ambiguous *model output* into executable tasks?

PR #14 (RW-061): newline-only goal → 1 fallback task.
RW-062 live: nvidia plan timeout → source=fallback → 7 tasks (operator:
"newline-split"). This file resolves the contradiction from source.
"""
from __future__ import annotations

import json

from rad.control import Controller, ObjectiveStatus
from rad.control import events as E
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner, _json_obj
from rad.tools import ToolCtx, run_tool

SEVEN_SENTENCE_GOAL = (
    "Create the project.\n"
    "Create the input file.\n"
    "Implement the function.\n"
    "Write the tests.\n"
    "Run the tests.\n"
    "Write result.json.\n"
    "Verify the result."
)

ORDINARY_PROSE = (
    "RAD is a personal agent.\n"
    "RAD executes useful work.\n"
    "RAD verifies its results."
)

NUMBERED_PLAN = (
    "Plan: 1. Create files. 2. Implement the function. "
    "3. Run tests. 4. Verify the result."
)

NEWLINE_ONLY_GOAL = (
    "Create the project\n"
    "Create the input file\n"
    "Implement the function\n"
    "Write the tests\n"
    "Run the tests\n"
    "Write result.json\n"
    "Verify the result"
)

ONE_SENTENCE_GOAL = "Write result.json containing the sum of 2 and 4."

MODEL_PROSE_SEVEN = SEVEN_SENTENCE_GOAL


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


def _fallback_texts(goal: str):
    g = Planner(None, "/tmp/ws")._fallback(Objective.new(goal))
    return [t.text for t in g.tasks.values()]


def _plan(llm, goal: str):
    return Planner(llm, "/tmp/ws").plan(Objective.new(goal))


def _timeout(_prompt: str) -> str:
    raise TimeoutError("nvidia plan timeout")


def _prose(_prompt: str) -> str:
    return MODEL_PROSE_SEVEN


def _empty(_prompt: str) -> str:
    return ""


def _malformed(_prompt: str) -> str:
    return "{not json"


def _plan_llm(plan):
    def llm(prompt: str) -> str:
        if "Decompose the goal" in prompt:
            return json.dumps(plan)
        if "strict verifier" in prompt:
            return json.dumps({"pass": True, "reason": "looks fine"})
        return "YES"
    return llm


def _ctl(home, scripted, llm):
    return Controller(home, session_factory=scripted, llm=llm, quiet=True)


# ---------------------------------------------------------------- architecture freeze

def test_f17_does_not_raise_caps_or_enable_needle(home):
    from rad.home import DEFAULTS
    from rad.toolrouter import resolve_tool_router

    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


# ---------------------------------------------------------------- intended contract

def test_planner_prompt_requires_json_only():
    from rad.control.planner import PLAN_PROMPT
    assert "Reply ONLY with JSON" in PLAN_PROMPT
    assert '"tasks"' in PLAN_PROMPT


def test_fallback_clause_split_is_documented_and_has_no_checks():
    """Contract: one task per clause marker, no machine checks, cap 7."""
    g = Planner(None, "/tmp/ws")._fallback(Objective.new("write a file and then read it back"))
    assert len(g.tasks) == 2
    assert all(not t.checks for t in g.tasks.values())


# ---------------------------------------------------------------- feed fallback: count tasks

def test_structured_period_plan_is_seven_clause_tasks_not_newlines():
    """RW-062 shape. Periods (clause markers) split; the cap is [:7]."""
    texts = _fallback_texts(SEVEN_SENTENCE_GOAL)
    assert len(texts) == 7, texts
    joined = " ".join(texts)
    assert "Create the project" in joined
    assert "Verify the result" in joined


def test_eight_period_sentences_still_cap_at_seven():
    texts = _fallback_texts(SEVEN_SENTENCE_GOAL + "\nAlso write README.")
    assert len(texts) == 7, texts
    assert not any("README" in t for t in texts)


def test_ordinary_prose_splits_on_periods_by_contract():
    """Prose in the *user goal* becomes one task per sentence. That is the
    documented clause split, not conversion of model output."""
    texts = _fallback_texts(ORDINARY_PROSE)
    assert len(texts) == 3, texts
    assert "personal agent" in texts[0]
    assert "useful work" in texts[1]
    assert "verifies" in texts[2]


def test_numbered_plan_splits_on_period_after_digits():
    texts = _fallback_texts(NUMBERED_PLAN)
    assert len(texts) == 5, texts


def test_pr14_newline_only_goal_is_still_one_task():
    """PR #14 claim remains true: newlines without clause markers → 1 task."""
    texts = _fallback_texts(NEWLINE_ONLY_GOAL)
    assert len(texts) == 1, texts
    assert "Create the project" in texts[0]
    assert "Verify the result" in texts[0]


# ---------------------------------------------------------------- timeout / failure does not parse model output

def test_timeout_does_not_turn_model_prose_into_tasks():
    """Class A claim: fallback converts ambiguous model output after timeout.

    Disproof: LLM raises; seven-line model prose is never consulted; the
    one-sentence user goal becomes one fallback task.
    """
    res = _plan(_timeout, ONE_SENTENCE_GOAL)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "fallback"
    assert len(texts) == 1, texts
    assert "sum of 2 and 4" in texts[0]
    assert "Create the project" not in texts[0]


def test_prose_llm_return_does_not_become_tasks():
    res = _plan(_prose, ONE_SENTENCE_GOAL)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "fallback"
    assert len(texts) == 1, texts
    assert "sum of 2 and 4" in texts[0]
    assert all("Create the input file" not in t for t in texts)


def test_empty_and_malformed_llm_fall_back_to_goal_not_raw():
    for llm in (_empty, _malformed):
        res = _plan(llm, ONE_SENTENCE_GOAL)
        texts = [t.text for t in res["graph"].tasks.values()]
        assert res["source"] == "fallback"
        assert len(texts) == 1, texts
        assert "sum of 2 and 4" in texts[0]


def test_json_obj_rejects_prose_and_timeout_text():
    for raw in ("", "timeout after 180s", MODEL_PROSE_SEVEN, "{not json"):
        try:
            _json_obj(raw)
            raise AssertionError(f"expected raise for {raw!r}")
        except ValueError:
            pass


def test_timeout_plus_seven_sentence_goal_matches_rw062_count():
    """RW-062's 7 tasks are the *goal's* clause split after timeout, cap [:7]."""
    res = _plan(_timeout, SEVEN_SENTENCE_GOAL)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "fallback"
    assert len(texts) == 7, texts
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- Scenarios A–D (controller, no NIM)

def test_scenario_a_valid_structured_plan_is_llm_not_fallback(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    plan = {"tasks": [
        {"id": "t1", "text": "write adder", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "add.py"}}]},
        {"id": "t2", "text": "write tests", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "test_add.py"}}]},
    ], "objective_checks": [{"kind": "json_valid", "args": {"path": "result.json"}}]}
    ctl = _ctl(home, ScriptedSession, _plan_llm(plan))
    obj = ctl.create(SEVEN_SENTENCE_GOAL)
    g = ctl.plan(obj)
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    assert src == "llm"
    assert len(g.tasks) == 2
    assert [t.text for t in g.tasks.values()] == ["write adder", "write tests"]


def test_scenario_b_timeout_plus_fallback_compatible_goal(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ctl = _ctl(home, ScriptedSession, _timeout)
    obj = ctl.create(SEVEN_SENTENCE_GOAL)
    g = ctl.plan(obj)
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    assert src == "fallback"
    assert len(g.tasks) == 7
    assert all(not t.checks for t in g.tasks.values())


def test_scenario_c_timeout_plus_ordinary_prose_uses_goal_not_model(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ctl = _ctl(home, ScriptedSession, _prose)
    obj = ctl.create(ORDINARY_PROSE)
    g = ctl.plan(obj)
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    texts = [t.text for t in g.tasks.values()]
    assert src == "fallback"
    assert len(texts) == 3, texts
    assert all("Create the project" not in t for t in texts)


def test_scenario_d_malformed_is_capped_not_uncontrolled(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    twenty = " ".join(f"Step {i} does a thing." for i in range(1, 21))
    ctl = _ctl(home, ScriptedSession, _malformed)
    obj = ctl.create(twenty)
    g = ctl.plan(obj)
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    assert src == "fallback"
    assert len(g.tasks) == 7
    assert len(g.tasks) < 16
    assert len(g.tasks) < 20


# ---------------------------------------------------------------- cap / budget interaction (quantify, do not change)

def test_fallback_seven_does_not_raise_plan_cap_or_default_tools(home, tmp_path):
    """`--max-tasks 4` is a drive stop, not a planner cap. Fallback still
    emits 7 clause tasks. Default Budget.tool_calls stays 60. Executing 4 of
    7 is bounded, not unbounded multiplication to 16."""
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [
        ([("list_dir", {})], "DONE: looked") for _ in range(8)
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, _timeout)
    obj = ctl.create(SEVEN_SENTENCE_GOAL, budget=Budget(tool_calls=60, retries=1))
    assert obj.budget.tool_calls == 60
    obj = ctl.run(obj, max_tasks=4)
    g = ctl.load_graph(obj)
    assert len(g.tasks) == 7
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    assert src == "fallback"
    attempted = [t for t in g.tasks.values() if t.status != "PENDING"]
    pending = [t for t in g.tasks.values() if t.status == "PENDING"]
    assert len(attempted) <= 4
    assert pending
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status != ObjectiveStatus.COMPLETED


def test_fallback_unverified_done_is_not_objective_verified(home, tmp_path):
    """False DONE stays 0: no-check fallback tasks may complete UNVERIFIED;
    the objective is not VERIFIED without machine checks."""
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [([("list_dir", {})], "DONE: all done")] * 4
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, _timeout)
    obj = ctl.run(ctl.create(ONE_SENTENCE_GOAL, budget=Budget(tool_calls=8, retries=1)))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    g = ctl.load_graph(obj)
    for t in g.tasks.values():
        if t.verification:
            assert t.verification.get("status") != "VERIFIED"
