"""v0.4.0 path-aligned checks / package layout (Gen3 theme 1).

Investigate-first from RW-069: planner checks at workspace-root `input.txt`
while writes landed under `text_analyzer/` → VALIDATION_FAILURE → retry thrash.

Class A confirmed: RAD *emits* root-only inferred checks for package-layout
goals, and *accepts* LLM root-only checks that disagree with the named layout.
Smallest patch: join bare check paths (and bare test_*.py in shell_ok) to the
package directory named in the goal. Check *kinds* are not remapped (F-26).
Fallback *tasks* stay check-less (F-17).

Needle OFF. Caps unchanged. False DONE 0.
"""
from __future__ import annotations

import json

from rad import __version__
from rad.control import Controller, ObjectiveStatus
from rad.control import events as E
from rad.control.codingloop import (
    align_rel_path,
    infer_coding_checks,
    infer_package_dir,
)
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observer
from rad.control.planner import PLAN_PROMPT, Planner, _checks
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Check, Task
from rad.control.verifier import Verifier
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from rad.tools import ToolCtx, run_tool

RW069_GOAL = (
    "Create a text analyzer under text_analyzer/\n"
    "Required files:\n"
    "- analyzer.py\n"
    "- input.txt\n"
    "- summary.json\n"
    "- test_analyzer.py\n"
    "- README.md\n"
    "Run the tests."
)

BRACE_GOAL = (
    "create text_analyzer/{analyzer.py,input.txt,summary.json,"
    "test_analyzer.py,README.md}; exact 3-line input; stdlib; run the tests"
)

PREFIXED_GOAL = (
    "Create text_analyzer/analyzer.py, text_analyzer/input.txt, "
    "text_analyzer/summary.json, text_analyzer/test_analyzer.py, "
    "text_analyzer/README.md. Run the tests."
)

WORD_COUNTER_GOAL = (
    "Create a word_counter project with these deliverables:\n"
    "1. word_counter.py\n"
    "2. result.json — valid JSON object with key words equal to integer 2\n"
    "3. test_word_counter.py — tests asserting counter returns 2\n"
    "4. Run the tests successfully so they pass"
)

ROOT_CHECK_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "write package files under text_analyzer/",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "input.txt"}},
            {"kind": "json_valid", "args": {"path": "summary.json"}},
        ],
    }],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "input.txt"}},
        {"kind": "json_valid", "args": {"path": "summary.json"}},
    ],
}

PREFIXED_CHECK_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "write package files under text_analyzer/",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
        ],
    }],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
    ],
}

JSON_VALID_ON_PY_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "Create word_counter.py with word counting function",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "word_counter.py"}},
            {"kind": "json_valid", "args": {"path": "word_counter.py"}},
        ],
    }],
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


def _plan_llm(plan):
    def llm(prompt: str) -> str:
        if "Decompose the goal" in prompt:
            return json.dumps(plan)
        if "strict verifier" in prompt:
            return json.dumps({"pass": True, "reason": "looks fine"})
        return "YES"
    return llm


def _ctl(home, scripted, plan=None, llm=None):
    return Controller(home, session_factory=scripted, llm=llm or (_plan_llm(plan) if plan else None),
                      quiet=True)


def _ver(ws, home) -> Verifier:
    return Verifier(ws, Observer(home.root / "obs"), home=home)


# ---------------------------------------------------------------- architecture freeze

def test_path_aligned_checks_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.4.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_asks_for_package_prefixed_check_paths():
    assert "check paths MUST" in PLAN_PROMPT
    assert "pkg/input.txt not input.txt" in PLAN_PROMPT


# ---------------------------------------------------------------- package-dir inference

def test_infer_package_dir_under_form():
    assert infer_package_dir(RW069_GOAL) == "text_analyzer/"


def test_infer_package_dir_brace_form():
    assert infer_package_dir(BRACE_GOAL) == "text_analyzer/"


def test_infer_package_dir_common_prefix():
    assert infer_package_dir(PREFIXED_GOAL) == "text_analyzer/"


def test_infer_package_dir_root_word_counter_is_none():
    assert infer_package_dir(WORD_COUNTER_GOAL) is None


def test_infer_package_dir_does_not_treat_tests_alone_as_package():
    assert infer_package_dir("Write tests/test_analyzer.py and run pytest.") is None


def test_infer_package_dir_single_pkg_file_is_not_a_layout():
    """Realworld coding: pkg/stats.py + tests/check_stats.py + root SPEC.md."""
    goal = (
        "pkg/stats.py is broken: `python3 tests/check_stats.py` fails. Read SPEC.md, "
        "inspect the code, implement mean(), fix any other bug the failing tests reveal."
    )
    assert infer_package_dir(goal) is None


def test_infer_package_dir_single_sources_file_is_not_a_layout():
    """Realworld multi_agent: sources/field_report.txt + root answer.md."""
    goal = (
        "From sources/field_report.txt produce answer.md (a short evidence-based summary)"
    )
    assert infer_package_dir(goal) is None


def test_align_rel_path_prefixes_bare_keeps_directed():
    assert align_rel_path("input.txt", "text_analyzer/") == "text_analyzer/input.txt"
    assert align_rel_path("text_analyzer/input.txt", "text_analyzer/") == "text_analyzer/input.txt"
    assert align_rel_path("input.txt", None) == "input.txt"
    assert align_rel_path("./input.txt", "text_analyzer/") == "text_analyzer/input.txt"


# ---------------------------------------------------------------- Scenario A — RAD emission (infer / fallback)

def test_scenario_a_infer_joins_bare_json_and_test_to_package_dir():
    checks = infer_coding_checks(RW069_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    assert any(
        c.kind == "shell_ok" and c.args.get("command") == "python3 text_analyzer/test_analyzer.py"
        for c in checks
    )


def test_scenario_a_infer_brace_goal_same_package_paths():
    checks = infer_coding_checks(BRACE_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    assert any("text_analyzer/test_analyzer.py" in str(c.args.get("command", ""))
               for c in checks if c.kind == "shell_ok")


def test_scenario_a_prefixed_goal_keeps_json_and_captures_test_under_package():
    checks = infer_coding_checks(PREFIXED_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    assert any(
        c.kind == "shell_ok" and "text_analyzer/test_analyzer.py" in str(c.args.get("command", ""))
        for c in checks
    )


def test_scenario_a_word_counter_root_paths_unchanged():
    checks = infer_coding_checks(WORD_COUNTER_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["result.json"]
    assert any(c.kind == "shell_ok" and c.args.get("command") == "python3 test_word_counter.py"
               for c in checks)


def test_scenario_a_fallback_objective_checks_aligned_tasks_checkless(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW069_GOAL))
    assert res["source"] == "fallback"
    json_paths = [c.args.get("path") for c in res["objective_checks"] if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- Scenario B — LLM acceptance (root checks remapped)

def test_scenario_b_llm_root_checks_are_joined_to_package_dir(tmp_path):
    plan = Planner(_plan_llm(ROOT_CHECK_PLAN), str(tmp_path)).plan(Objective.new(RW069_GOAL))
    assert plan["source"] == "llm"
    task_paths = [c.args.get("path") for t in plan["graph"].tasks.values() for c in t.checks]
    obj_paths = [c.args.get("path") for c in plan["objective_checks"]]
    assert "text_analyzer/input.txt" in task_paths
    assert "text_analyzer/summary.json" in task_paths
    assert "input.txt" not in task_paths
    assert "summary.json" not in task_paths
    assert "text_analyzer/input.txt" in obj_paths
    assert "text_analyzer/summary.json" in obj_paths


def test_scenario_b_already_prefixed_llm_checks_are_not_double_joined(tmp_path):
    plan = Planner(_plan_llm(PREFIXED_CHECK_PLAN), str(tmp_path)).plan(Objective.new(RW069_GOAL))
    paths = [c.args.get("path") for t in plan["graph"].tasks.values() for c in t.checks]
    assert paths == ["text_analyzer/input.txt"]


def test_scenario_b_json_valid_on_py_kind_is_kept_without_package_dir(tmp_path):
    """F-26: kinds are not remapped. Root word_counter has no package dir."""
    plan = Planner(_plan_llm(JSON_VALID_ON_PY_PLAN), str(tmp_path)).plan(
        Objective.new("Implement word_counter.py and write result.json"))
    kinds = [(c.kind, c.args.get("path")) for t in plan["graph"].tasks.values() for c in t.checks]
    assert ("json_valid", "word_counter.py") in kinds
    kept = _checks([{
        "kind": "json_valid",
        "args": {"path": "word_counter.py"},
        "description": "word_counter.py is a valid Python file",
    }])
    assert kept[0].kind == "json_valid"
    assert kept[0].args["path"] == "word_counter.py"


# ---------------------------------------------------------------- Scenario C — verifier is honest; alignment is planner-time

def test_scenario_c_verifier_does_not_remap_root_check_to_package_file(home, tmp_path):
    ws = tmp_path / "ws_c"
    ws.mkdir()
    pkg = ws / "text_analyzer"
    pkg.mkdir()
    (pkg / "input.txt").write_text("a\nb\nc\n", encoding="utf-8")
    (pkg / "summary.json").write_text('{"lines": 3}', encoding="utf-8")
    v = _ver(ws, home)
    root = v.run_check(Check("file_exists", {"path": "input.txt"}))
    pkg_ok = v.run_check(Check("file_exists", {"path": "text_analyzer/input.txt"}))
    assert root["ok"] is False
    assert pkg_ok["ok"] is True
    t = Task.new("o", "write input.txt")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": str(ws / "input.txt") + " exists=False"},
    ]}
    assert classify(t, [], verification=ver) == FailureClass.VALIDATION
    d = RecoveryEngine().decide(t, [], verification=ver, retries_left=3)
    assert d.failure_class == FailureClass.VALIDATION
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy == "retry_with_hint"


# ---------------------------------------------------------------- Scenario D — scripted package writes + root-only checks (RW-070)

def test_scenario_d_scripted_root_checks_with_package_writes_verify_without_thrash(home, tmp_path):
    """Deterministic RW-069 shape: LLM root checks + package writes.

    After alignment the first attempt is VERIFIED. No VALIDATION retry
    flattening files onto the workspace root. False DONE 0.
    """
    ws = tmp_path / "ws_d"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt",
                          "content": "Line one\nLine two\nLine three\n"}),
          ("write_file", {"path": "text_analyzer/summary.json",
                          "content": '{"lines": 3, "words": 6, "characters": 29}'}),
          ("write_file", {"path": "text_analyzer/test_analyzer.py",
                          "content": "print('ok')\n"})],
         "DONE: wrote package files"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, ROOT_CHECK_PLAN)
    obj = ctl.run(ctl.create(
        RW069_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert not any(d.get("failure_class") == FailureClass.ENVIRONMENT for d in decisions)
    g = ctl.load_graph(obj)
    tasks = list(g.tasks.values())
    assert tasks
    assert all((t.verification or {}).get("status") == "VERIFIED" for t in tasks)
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") == "VERIFIED", ov
    assert (ws / "text_analyzer" / "input.txt").is_file()
    assert (ws / "text_analyzer" / "summary.json").is_file()
    assert not (ws / "input.txt").exists()
    assert not (ws / "summary.json").exists()
