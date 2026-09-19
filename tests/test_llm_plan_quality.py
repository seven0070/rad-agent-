"""v0.5.3 G4-5 — fallback / LLM plan quality under tight budgets (RW-094 / RW-095).

Investigate-first (ROADMAP G4-5 / Cycle 30 findings):
- ``Planner.plan`` retries once then ``_fallback`` (default attempts=2).
- Live RW-085 / RW-086: ``PLAN_CREATED source=fallback attempts=2`` —
  4 newline/clause-carved tasks, not a coding graph.
- ``_json_obj`` used a greedy ``{.*}`` + ``json.loads`` only, so fenced
  JSON, trailing commas, a tasks array, or extra braces after the first
  object discarded a usable structured plan into clause-carve.
- F-17 stays closed: do **not** add checks to fallback *tasks*.

G4-5 recovers near-JSON as ``source=llm`` (RW-094) and uses a compact
coding-plan retry after a miss (RW-095). Exhausted retries still
goal-only fallback, cap 7, no checks.

Does not claim live text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. No Class A invented for 403/429. No GitHub Release / tag.
"""
from __future__ import annotations

import json

from rad import __version__
from rad.control import Controller, ObjectiveStatus
from rad.control import events as E
from rad.control.budgetplan import TOOLS_PER_TASK, estimate_plan_tools
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_missing_optional_checksum_utility,
    is_missing_python_script,
    is_pip_requirements_file_missing,
)
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.planner import (
    PLAN_CODING_RETRY,
    PLAN_PROMPT,
    PLAN_RETRY_NUDGE,
    Planner,
    _json_obj,
)
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from rad.tools import ToolCtx, run_tool

from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_f17_fallback_investigation import (
    MODEL_PROSE_SEVEN,
    ONE_SENTENCE_GOAL,
    _fallback_texts,
)
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_plan_timeout_resilience import SequentialLLM, _ctl, _plan_event
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_xxd_environment import XXD_CMD, XXD_ERR


# RW-085 / RW-086 shape: package-layout coding goal whose fallback is
# four clause tasks (not a coding graph). Periods — not bare newlines —
# are the F-17 split; live "newline-carved" was this clause split.
RW085_GOAL = (
    "Create the text_analyzer/ package. "
    "Write text_analyzer/analyzer.py (stdlib). "
    "Write text_analyzer/input.txt (exact 3 lines). "
    "Write text_analyzer/summary.json and test_analyzer.py."
)

RW094_CODING_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write text_analyzer/input.txt with exact 3 lines",
            "depends_on": [],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
                {"kind": "file_line_count", "args": {"path": "text_analyzer/input.txt", "n": 3}},
            ],
        },
        {
            "id": "t2",
            "text": "Write text_analyzer/analyzer.py",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}}],
        },
        {
            "id": "t3",
            "text": "Write text_analyzer/summary.json and tests",
            "depends_on": [],
            "checks": [
                {"kind": "json_valid", "args": {"path": "text_analyzer/summary.json"}},
                {"kind": "file_exists", "args": {"path": "text_analyzer/test_analyzer.py"}},
            ],
        },
    ],
    "objective_checks": [
        {"kind": "json_valid", "args": {"path": "text_analyzer/summary.json"}},
        {"kind": "shell_ok", "args": {"command": "python3 text_analyzer/test_analyzer.py"}},
    ],
}

TRAILING_COMMA_JSON = """
{"tasks": [
  {"id": "t1", "text": "Write text_analyzer/input.txt", "depends_on": [],
   "checks": [{"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},],},
  {"id": "t2", "text": "Write text_analyzer/analyzer.py", "depends_on": [],
   "checks": [{"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}},],},
], "objective_checks": [{"kind": "json_valid", "args": {"path": "text_analyzer/summary.json"}},],}
"""


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


def _json_plan(plan=None) -> str:
    return json.dumps(plan or RW094_CODING_PLAN)


def _fenced(plan=None) -> str:
    body = json.dumps(plan or RW094_CODING_PLAN)
    return f"Sure, here is the plan:\n```json\n{body}\n```\nGood luck {{operator}}!"


def _array(plan=None) -> str:
    return json.dumps((plan or RW094_CODING_PLAN)["tasks"])


def _plan(llm, goal: str = RW085_GOAL, **kw):
    return Planner(llm, "/tmp/ws").plan(Objective.new(goal), **kw)


# ---------------------------------------------------------------- architecture freeze

def test_g45_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.3"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_prior_class_a_helpers_still_hold():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"
    assert infer_package_dir(RW085_GOAL) == "text_analyzer/"
    assert is_done_protocol_tool("DONE: wrote input")
    assert is_pip_requirements_file_missing(
        "ERROR: Could not open requirements file: [Errno 2] No such file or directory: "
        "'requirements.txt'",
        "pip install -r requirements.txt")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_missing_optional_checksum_utility(XXD_ERR, XXD_CMD)


# ---------------------------------------------------------------- RW-085 / RW-086 fallback shape (F-17 honest)

def test_rw085_fallback_is_four_clause_tasks_without_checks():
    """Live RW-085/086 shape: fallback carves the goal, not a coding graph."""
    texts = _fallback_texts(RW085_GOAL)
    assert len(texts) == 4, texts
    assert "text_analyzer/" in texts[0]
    assert "text_analyzer/analyzer.py" in texts[1]
    assert "text_analyzer/input.txt" in texts[2]
    assert "text_analyzer/summary.json" in texts[3]
    g = Planner(None, "/tmp/ws")._fallback(Objective.new(RW085_GOAL))
    assert all(not t.checks for t in g.tasks.values())


def test_exhausted_llm_on_rw085_goal_still_fallback_checkless():
    """F-17: exhausted retries stay goal-only. Do not invent task checks."""
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    res = _plan(llm, RW085_GOAL, tool_budget=12)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "fallback"
    assert res["attempts"] == 2
    assert len(texts) == 4, texts
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert "Create the project" not in " ".join(texts)


# ---------------------------------------------------------------- RW-094 near-JSON recovered as llm (not fallback)

def test_rw094_fenced_json_is_llm_not_fallback():
    """RW-094: markdown fence + extra braces after the object used to greedy-fail."""
    llm = SequentialLLM([_fenced()])
    res = _plan(llm, RW085_GOAL, tool_budget=12)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "llm"
    assert res["attempts"] == 1
    assert texts[0].startswith("Write text_analyzer/input.txt")
    assert len(texts) == 3
    assert all(t.checks for t in res["graph"].tasks.values())
    assert res["compacted"] is False
    assert estimate_plan_tools(len(texts)) <= 12


def test_rw094_trailing_commas_are_llm_not_fallback():
    llm = SequentialLLM([TRAILING_COMMA_JSON])
    res = _plan(llm, RW085_GOAL, tool_budget=12)
    assert res["source"] == "llm"
    assert res["attempts"] == 1
    assert len(res["graph"].tasks) == 2
    assert all(t.checks for t in res["graph"].tasks.values())


def test_rw094_tasks_array_is_llm_not_fallback():
    llm = SequentialLLM([_array()])
    res = _plan(llm, RW085_GOAL, tool_budget=12)
    assert res["source"] == "llm"
    assert res["attempts"] == 1
    assert len(res["graph"].tasks) == 3
    assert all(t.checks for t in res["graph"].tasks.values())


def test_json_obj_recovers_near_json_and_still_rejects_prose():
    fenced = _fenced()
    d = _json_obj(fenced)
    assert [t["text"] for t in d["tasks"]][0].startswith("Write text_analyzer/input.txt")
    d = _json_obj(TRAILING_COMMA_JSON)
    assert len(d["tasks"]) == 2
    d = _json_obj(_array())
    assert "tasks" in d and len(d["tasks"]) == 3
    for raw in ("", "timeout after 180s", MODEL_PROSE_SEVEN, "{not json"):
        try:
            _json_obj(raw)
            raise AssertionError(f"expected raise for {raw!r}")
        except ValueError:
            pass


# ---------------------------------------------------------------- RW-095 compact coding retry after a miss

def test_rw095_timeout_then_json_uses_compact_coding_retry():
    """RW-095: coding-goal miss retries with PLAN_CODING_RETRY, not the full prompt."""
    llm = SequentialLLM([TimeoutError("nvidia plan timeout"), _json_plan()])
    res = _plan(llm, RW085_GOAL, tool_budget=12)
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert len(res["graph"].tasks) == 3
    assert all(t.checks for t in res["graph"].tasks.values())
    assert len(llm.prompts) == 2
    assert "Decompose the goal into the smallest set" in llm.prompts[0]
    assert PLAN_CODING_RETRY.split("\n", 1)[0][:40] in llm.prompts[1]
    assert "Previous reply was not usable JSON" in llm.prompts[1]
    assert PLAN_RETRY_NUDGE.strip() in llm.prompts[1]
    assert "Decompose the goal into the smallest set" not in llm.prompts[1]
    assert len(llm.prompts[1]) < len(llm.prompts[0])


def test_rw095_ascii_tree_prose_then_json_is_llm():
    llm = SequentialLLM([MODEL_PROSE_SEVEN, _json_plan()])
    res = _plan(llm, RW073_ASCII_GOAL, tool_budget=12)
    texts = [t.text for t in res["graph"].tasks.values()]
    assert res["source"] == "llm"
    assert res["attempts"] == 2
    assert texts == [
        "Write text_analyzer/input.txt with exact 3 lines",
        "Write text_analyzer/analyzer.py",
        "Write text_analyzer/summary.json and tests",
    ]
    assert all("Create the project" not in t for t in texts)


def test_non_coding_retry_still_uses_full_prompt_nudge():
    """ONE_SENTENCE_GOAL is not a package/coding-marker goal — keep PLAN_RETRY_NUDGE path."""
    llm = SequentialLLM([TimeoutError("t1"), _json_plan()])
    res = _plan(llm, ONE_SENTENCE_GOAL)
    assert res["source"] == "llm"
    assert PLAN_RETRY_NUDGE.strip() in llm.prompts[1]
    assert "Previous reply was not usable JSON" not in llm.prompts[1]
    assert "Decompose the goal into the smallest set" in llm.prompts[1]


# ---------------------------------------------------------------- controller

def test_controller_rw094_fenced_emits_llm(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([_fenced()])
    ctl = _ctl(home, llm)
    obj = ctl.create(RW085_GOAL, budget=Budget(tool_calls=12))
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "llm"
    assert ev.data["attempts"] == 1
    assert ev.data.get("compacted") is False
    assert len(g.tasks) == 3
    assert all(t.checks for t in g.tasks.values())


def test_controller_rw095_timeout_then_json_emits_llm(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([TimeoutError("t1"), _json_plan()])
    ctl = _ctl(home, llm)
    obj = ctl.create(RW085_GOAL, budget=Budget(tool_calls=12))
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "llm"
    assert ev.data["attempts"] == 2
    assert len(g.tasks) == 3
    assert all(t.checks for t in g.tasks.values())


def test_controller_exhausted_rw085_emits_fallback_four(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    ctl = _ctl(home, llm)
    obj = ctl.create(RW085_GOAL, budget=Budget(tool_calls=12))
    g = ctl.plan(obj)
    ev = _plan_event(ctl, obj)
    assert ev.data["source"] == "fallback"
    assert ev.data["attempts"] == 2
    assert len(g.tasks) == 4
    assert all(not t.checks for t in g.tasks.values())


# ---------------------------------------------------------------- false DONE stays 0

def test_fallback_after_retries_is_not_objective_verified(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [([("list_dir", {})], "DONE: all done")] * 6
    ScriptedSession.prompts = []
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    ctl = Controller(home, session_factory=ScriptedSession, llm=llm, quiet=True)
    obj = ctl.run(ctl.create(RW085_GOAL, budget=Budget(tool_calls=12, retries=1)))
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
    log = EventLog(ctl.store.events_path(obj.id))
    assert list(log.read(kind=E.PLAN_CREATED))


def test_g45_cost_model_unchanged():
    assert TOOLS_PER_TASK == 2
    assert "TOOL BUDGET: {tool_budget}" in PLAN_PROMPT
    assert "Previous reply was not usable JSON" in PLAN_CODING_RETRY
