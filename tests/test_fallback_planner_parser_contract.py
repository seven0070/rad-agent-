"""F-20260918-17 targeted investigation: fallback planner parsing.

These tests are deterministic and do not call NIM or any other provider.  They
pin the current parser contract so the investigation can distinguish two very
separate things:

* malformed LLM planner output is parsed only as JSON and is *not* line-split
  into executable tasks; and
* the deterministic no-brain fallback splits the original objective into a
  bounded clause/sentence chain.
"""
from __future__ import annotations

import json

from rad.control import events as E
from rad.control.controller import Controller
from rad.control.events import EventLog
from rad.control import ObjectiveStatus, TaskStatus
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.tools import ToolCtx, run_tool


RAW_TASK_LINES = """Create the project.
Create the input file.
Implement the counter.
Run the tests.
Verify the result."""

RAW_PROSE_LINES = """RAD is a personal agent.
RAD executes useful work.
RAD verifies its results."""

RAW_NUMBERED_PLAN = """Plan:
1. Create files.
2. Implement the program.
3. Run tests.
4. Verify the output."""

STABLE_OBJECTIVE = "Build a minimal counter utility"


def _texts(graph):
    return [t.text for t in graph.tasks.values()]


def test_raw_multiline_llm_text_is_not_split_into_fallback_tasks():
    """Malformed model text is not a fallback parser input.

    Planner.plan() asks for JSON.  If the raw LLM response has no JSON object,
    _json_obj() raises and the fallback uses the original objective text, not the
    response lines.
    """
    for raw in (RAW_TASK_LINES, RAW_PROSE_LINES, RAW_NUMBERED_PLAN):
        res = Planner(lambda _prompt, raw=raw: raw, "/tmp/ws").plan(Objective.new(STABLE_OBJECTIVE))

        assert res["source"] == "fallback"
        assert _texts(res["graph"]) == [STABLE_OBJECTIVE]
        assert res["objective_checks"] == []


def test_direct_fallback_goal_parser_counts_representative_multiline_objectives():
    """Direct no-brain fallback splits original objective clauses/sentences.

    This documents where multiplication can happen today: in Planner._fallback()
    over obj.goal, not in a raw model-response line parser.
    """
    cases = [
        (RAW_TASK_LINES, 5),
        (RAW_PROSE_LINES, 3),
        (RAW_NUMBERED_PLAN, 5),
    ]
    for goal, expected in cases:
        graph = Planner(None, "/tmp/ws")._fallback(Objective.new(goal))
        assert len(graph.tasks) == expected, _texts(graph)
        assert len(graph.tasks) <= 7
        assert all(not t.checks for t in graph.tasks.values())


def test_scenario_a_valid_structured_plan_produces_intended_tasks():
    plan = {
        "tasks": [
            {"id": "t1", "text": "Create the input file", "depends_on": [],
             "checks": [{"kind": "file_exists", "args": {"path": "input.txt"}}]},
            {"id": "t2", "text": "Implement the counter", "depends_on": ["t1"],
             "checks": [{"kind": "file_exists", "args": {"path": "counter.py"}}]},
        ],
        "objective_checks": [{"kind": "file_exists", "args": {"path": "counter.py"}}],
    }

    res = Planner(lambda _prompt: json.dumps(plan), "/tmp/ws").plan(Objective.new(STABLE_OBJECTIVE))

    assert res["source"] == "llm"
    assert _texts(res["graph"]) == ["Create the input file", "Implement the counter"]
    tasks = list(res["graph"].tasks.values())
    assert tasks[1].depends_on == [tasks[0].id]
    assert [c.kind for c in res["objective_checks"]] == ["file_exists"]


def test_scenario_b_timeout_uses_bounded_goal_fallback():
    """A planner timeout has no raw response to parse; fallback uses obj.goal."""
    def timeout(_prompt: str) -> str:
        raise TimeoutError("simulated planner timeout")

    goal = "Create the project. Create the input file. Implement the counter. Run the tests. Verify the result."
    res = Planner(timeout, "/tmp/ws").plan(Objective.new(goal))

    assert res["source"] == "fallback"
    assert len(res["graph"].tasks) == 5
    assert len(res["graph"].tasks) <= 7
    assert _texts(res["graph"])[0] == "Create the project"


def test_scenario_c_ordinary_prose_model_output_does_not_become_task_graph():
    res = Planner(lambda _prompt: RAW_PROSE_LINES, "/tmp/ws").plan(Objective.new(STABLE_OBJECTIVE))

    assert res["source"] == "fallback"
    assert _texts(res["graph"]) == [STABLE_OBJECTIVE]
    assert all("RAD verifies" not in t.text for t in res["graph"].tasks.values())


def test_scenario_d_malformed_numbered_model_output_falls_back_safely():
    res = Planner(lambda _prompt: RAW_NUMBERED_PLAN, "/tmp/ws").plan(Objective.new(STABLE_OBJECTIVE))

    assert res["source"] == "fallback"
    assert _texts(res["graph"]) == [STABLE_OBJECTIVE]
    assert all(not t.text.startswith("Plan:") for t in res["graph"].tasks.values())


def test_controller_records_fallback_source_after_planner_timeout(home):
    def timeout(_prompt: str) -> str:
        raise TimeoutError("simulated planner timeout")

    ctl = Controller(home, llm=timeout, quiet=True)
    obj = ctl.create("Create the project. Run the tests.")
    graph = ctl.plan(obj)

    events = list(EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED))
    assert len(graph.tasks) == 2
    assert events[-1].data["source"] == "fallback"
    assert obj.verification == {"objective_checks": []}
    assert len(ctl.store.load_tasks(obj.id)) == 2


def test_fallback_generated_tasks_can_consume_tool_budget_until_exhaustion(home):
    """Quantify the budget impact of fallback task multiplication.

    This is not a NIM test: each fallback task deterministically spends one
    list_dir tool call and claims DONE.  Because fallback tasks have no checks,
    completed tasks are recorded as UNVERIFIED; the controller still stops safely
    at the tool budget instead of declaring the whole objective complete.
    """
    class OneToolDoneSession:
        def __init__(self, home, auto=False, **_kw):
            self.home = home
            self.ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda _p: True)
            self.tool_runner = run_tool
            self.last_usage = {}

        def think(self, _prompt: str) -> str:
            self.tool_runner("list_dir", {}, self.ctx)
            return "DONE: listed"

        def close(self):
            pass

    goal = "Alpha task. Bravo task. Charlie task. Delta task. Echo task. Foxtrot task. Golf task."
    ctl = Controller(home, session_factory=OneToolDoneSession, llm=None, quiet=True)
    obj = ctl.run(ctl.create(goal, budget=Budget(tool_calls=4, retries=0), auto=True))
    graph = ctl.load_graph(obj)

    assert len(graph.tasks) == 7
    assert obj.usage.tool_calls == 4
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert "tool-call budget 4 exhausted" in obj.failure
    assert sum(1 for t in graph.tasks.values() if t.status == TaskStatus.COMPLETED) == 4
    assert sum(1 for t in graph.tasks.values() if t.status == TaskStatus.PENDING) == 3
    assert all(t.verification.get("status") == "UNVERIFIED"
               for t in graph.tasks.values() if t.status == TaskStatus.COMPLETED)
