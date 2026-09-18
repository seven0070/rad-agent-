"""v0.3.2 budget-aware planning (Gen2 theme 3).

A fat plan that would burn more than N tools is retried; the cheaper graph
that fits N is selected. Fallback graphs that are still fat are compacted.
Small (≤3) LLM graphs are not compacted (F-21 leftover-work contract).

Needle OFF. Caps unchanged. False DONE stays 0.
"""
from __future__ import annotations

import json

from rad import __version__
from rad.control import Controller, ObjectiveStatus
from rad.control import events as E
from rad.control.budgetplan import (
    SMALL_PLAN_MAX,
    TOOLS_PER_TASK,
    compact_graph,
    estimate_plan_tools,
    is_fat,
    max_fit_tasks,
    remaining_tool_calls,
)
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.planner import PLAN_BUDGET_NUDGE, PLAN_PROMPT, Planner
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from rad.tools import ToolCtx, run_tool

from tests.test_f17_fallback_investigation import SEVEN_SENTENCE_GOAL
from tests.test_plan_timeout_resilience import SequentialLLM, _ctl, _plan_event


def _task(i: int) -> dict:
    return {"id": f"t{i}", "text": f"step {i} write f{i}.txt", "depends_on": [] if i == 1 else [f"t{i-1}"],
            "checks": [{"kind": "file_exists", "args": {"path": f"f{i}.txt"}}]}


FAT_PLAN = {"tasks": [_task(i) for i in range(1, 9)],
            "objective_checks": [{"kind": "file_exists", "args": {"path": "f1.txt"}}]}
FIT_PLAN = {"tasks": [_task(i) for i in range(1, 3)],
            "objective_checks": [{"kind": "file_exists", "args": {"path": "f1.txt"}}]}
SMALL_THREE = {"tasks": [_task(i) for i in range(1, 4)],
               "objective_checks": [{"kind": "file_contains", "args": {"path": "f1.txt", "text": "ok"}}]}
CHEAPER_FAT = {"tasks": [_task(i) for i in range(1, 7)],
               "objective_checks": [{"kind": "file_exists", "args": {"path": "f1.txt"}}]}


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


def _json_plan(plan) -> str:
    return json.dumps(plan)


def _plan(llm, goal: str = "implement word_counter and write result.json", **kw):
    return Planner(llm, "/tmp/ws").plan(Objective.new(goal), **kw)


# ---------------------------------------------------------------- architecture freeze

def test_budget_aware_planning_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.4.5"
    assert Budget().tool_calls == 60
    assert TOOLS_PER_TASK == 2
    assert SMALL_PLAN_MAX == 3
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_cost_model_and_fat_vs_small_leftover():
    assert estimate_plan_tools(8) == 16
    assert max_fit_tasks(6) == 3
    assert max_fit_tasks(1) == 1
    assert max_fit_tasks(None) is None
    assert is_fat(8, 6) is True
    assert is_fat(3, 1) is False   # F-21 leftover work, not fat
    assert is_fat(7, 60) is False
    assert is_fat(7, 4) is True
    obj = Objective.new("x", budget=Budget(tool_calls=12))
    obj.usage.tool_calls = 3
    assert remaining_tool_calls(obj) == 9


def test_plan_prompt_includes_tool_budget():
    assert "TOOL BUDGET: {tool_budget}" in PLAN_PROMPT
    llm = SequentialLLM([_json_plan(FIT_PLAN)])
    _plan(llm, tool_budget=6)
    assert "6 tool calls remaining" in llm.prompts[0]
    assert PLAN_BUDGET_NUDGE not in llm.prompts[0]


# ---------------------------------------------------------------- select a plan that fits N

def test_fat_plan_then_fit_plan_is_selected():
    """8-task fat plan would estimate 16 tools; remaining 6 → retry → 2-task fit."""
    llm = SequentialLLM([_json_plan(FAT_PLAN), _json_plan(FIT_PLAN)])
    res = _plan(llm, tool_budget=6)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert len(texts) == 2
    assert res["fit"] is True
    assert res["estimated_tools"] == 4
    assert res["compacted"] is False
    assert PLAN_BUDGET_NUDGE.strip() in llm.prompts[1]
    assert estimate_plan_tools(len(texts)) <= 6
    assert all(t.checks for t in res["graph"].tasks.values())


def test_fit_first_try_does_not_budget_retry():
    llm = SequentialLLM([_json_plan(FIT_PLAN), _json_plan(FAT_PLAN)])
    res = _plan(llm, tool_budget=6)
    assert res["source"] == "llm"
    assert res["attempts"] == 1
    assert len(res["graph"].tasks) == 2
    assert len(llm.prompts) == 1


def test_two_fat_plans_selects_cheaper():
    llm = SequentialLLM([_json_plan(FAT_PLAN), _json_plan(CHEAPER_FAT)])
    res = _plan(llm, tool_budget=6)
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert len(res["graph"].tasks) == 6   # cheaper of 8 vs 6; still over 3-fit
    assert res["fit"] is False
    assert res["compacted"] is False      # LLM graphs are not silently compacted


def test_small_three_task_plan_not_compacted_under_tight_budget():
    """F-21: 3-task leftover work with remaining=1 stays 3 tasks."""
    llm = SequentialLLM([_json_plan(SMALL_THREE)])
    res = _plan(llm, tool_budget=1)
    assert res["source"] == "llm"
    assert res["attempts"] == 1
    assert len(res["graph"].tasks) == 3
    assert res["compacted"] is False


# ---------------------------------------------------------------- fallback compact

def test_fat_fallback_is_compacted_to_fit():
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    res = _plan(llm, SEVEN_SENTENCE_GOAL, tool_budget=4)
    n = len(res["graph"].tasks)
    assert res["source"] == "fallback"
    assert res["compacted"] is True
    assert n == max_fit_tasks(4) == 2
    assert estimate_plan_tools(n) <= 4
    assert all(not t.checks for t in res["graph"].tasks.values())  # F-17


def test_fallback_default_unlimited_budget_stays_seven():
    llm = SequentialLLM(["", "{not json"])
    res = _plan(llm, SEVEN_SENTENCE_GOAL)   # tool_budget None
    assert res["source"] == "fallback"
    assert len(res["graph"].tasks) == 7
    assert res["compacted"] is False
    assert all(not t.checks for t in res["graph"].tasks.values())


def test_compact_graph_merges_extra_text():
    g = Planner(None, "/tmp/ws")._fallback(Objective.new(SEVEN_SENTENCE_GOAL))
    packed, leftover, changed = compact_graph(g, 2)
    assert changed is True
    assert len(packed.tasks) == 2
    assert leftover == []
    joined = " ".join(t.text for t in packed.tasks.values())
    assert "Create the project" in joined
    assert "Verify the result" in joined


# ---------------------------------------------------------------- controller

def test_controller_fat_then_fit_emits_fit_plan(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([_json_plan(FAT_PLAN), _json_plan(FIT_PLAN)])
    ctl = _ctl(home, llm)
    obj = ctl.create("implement word_counter.py and write result.json",
                     budget=Budget(tool_calls=6))
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "llm"
    assert ev.data["attempts"] == 2
    assert ev.data.get("fit") is True
    assert ev.data.get("compacted") is False
    assert ev.data.get("tool_budget") == 6
    assert len(g.tasks) == 2
    assert estimate_plan_tools(len(g.tasks)) <= 6
    assert all(t.checks for t in g.tasks.values())


def test_controller_default_budget_does_not_compact_seven(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    ctl = _ctl(home, llm)
    obj = ctl.create(SEVEN_SENTENCE_GOAL)
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "fallback"
    assert len(g.tasks) == 7
    assert ev.data.get("compacted") is False
    assert ev.data.get("tool_budget") == 60


# ---------------------------------------------------------------- false DONE stays 0

def test_compacted_fallback_is_not_objective_verified(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [([("list_dir", {})], "DONE: all done")] * 6
    ScriptedSession.prompts = []
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    ctl = Controller(home, session_factory=ScriptedSession, llm=llm, quiet=True)
    obj = ctl.run(ctl.create(SEVEN_SENTENCE_GOAL, budget=Budget(tool_calls=4, retries=1)))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED,
                          ObjectiveStatus.COMPLETED)
    if obj.status == ObjectiveStatus.COMPLETED:
        assert ov.get("status") != "VERIFIED"
    g = ctl.load_graph(obj)
    for t in g.tasks.values():
        if t.verification:
            assert t.verification.get("status") != "VERIFIED"
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "fallback"
    assert ev.data.get("compacted") is True
    log = EventLog(ctl.store.events_path(obj.id))
    assert list(log.read(kind=E.PLAN_CREATED))
