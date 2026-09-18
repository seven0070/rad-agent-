"""Verified coding loop (v0.3.0): write → machine checks → repair.

A model `DONE:` is never completion. Invalid JSON / failing tests inject a
repair step with the concrete failure. Persistent bad artifacts stay
non-VERIFIED (false DONE = 0). Needle off. Caps unchanged.
"""
from __future__ import annotations

import json

from rad.control import Controller, ObjectiveStatus
from rad.control import events as E
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observer
from rad.control.planner import Planner
from rad.control.recovery import FailureClass, RecoveryEngine
from rad.control.tasks import Check, Task
from rad.control.verifier import Verifier
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401


WORD_COUNTER_TEST = (
    "import json\n"
    "r = json.load(open('result.json'))\n"
    "assert r['words'] == 2, f\"{r.get('words')}!=2\"\n"
    "print('OK')\n"
)

GOOD_RESULT = '{"words": 2, "lines": 1, "chars": 11}\n'
BAD_RESULT = "{\n"
GOOD_PY = (
    "def count_words(text):\n"
    "    return len(text.split())\n"
)
BAD_PY = (
    "def count_words(text):\n"
    "    return 6\n"
)

CODING_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "implement word_counter.py, write result.json, run tests",
        "depends_on": [],
        "checks": [
            {"kind": "json_valid", "args": {"path": "result.json"}},
            {"kind": "json_field", "args": {"path": "result.json", "key": "words", "equals": 2}},
            {"kind": "shell_ok", "args": {"command": "python3 test_word_counter.py"}},
        ],
    }],
    "objective_checks": [
        {"kind": "json_valid", "args": {"path": "result.json"}},
        {"kind": "json_field", "args": {"path": "result.json", "key": "words", "equals": 2}},
        {"kind": "shell_ok", "args": {"command": "python3 test_word_counter.py"}},
    ],
}


def _seed_tests(ws):
    (ws / "test_word_counter.py").write_text(WORD_COUNTER_TEST, encoding="utf-8")


# ---------------------------------------------------------------- architecture freeze

def test_verified_coding_loop_does_not_raise_caps_or_enable_needle(home):
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_verified_coding_loop_broken_artifact_is_repair_not_env():
    t = Task.new("o", "write result.json and run tests")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "json_valid", "detail": "result.json invalid JSON: Expecting property name"},
        {"ok": False, "kind": "shell_ok", "detail": "exit=1 AssertionError: 6!=2"},
    ]}
    d = RecoveryEngine().decide(t, [], verification=ver, retries_left=3)
    assert d.failure_class == FailureClass.VALIDATION
    assert d.strategy == "repair"
    assert d.data.get("coding_repair") is True
    assert "invalid JSON" in d.hint
    assert "6!=2" in d.hint or "shell_ok" in d.hint


def test_verified_coding_loop_missing_file_still_retry_with_hint():
    t = Task.new("o", "write result.json")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "result.json exists=False"},
    ]}
    d = RecoveryEngine().decide(t, [], verification=ver, retries_left=3)
    assert d.strategy == "retry_with_hint"
    assert d.failure_class == FailureClass.VALIDATION


# ---------------------------------------------------------------- A. scripted repair → VERIFIED

def test_verified_coding_loop_repairs_wrong_artifact_then_verifies(home, ws, scripted):
    """Writes invalid JSON once; after the check failure, repairs; disk matches checks."""
    _seed_tests(ws)
    scripted.script = [
        ([("write_file", {"path": "word_counter.py", "content": BAD_PY}),
          ("write_file", {"path": "result.json", "content": BAD_RESULT})],
         "DONE: result.json written"),
        ([("write_file", {"path": "word_counter.py", "content": GOOD_PY}),
          ("write_file", {"path": "result.json", "content": GOOD_RESULT})],
         "DONE: repaired json and counts"),
        ([("run_shell", {"command": "python3 test_word_counter.py"})],
         "DONE: tests pass"),
    ]
    ctl = _ctl(home, scripted, CODING_PLAN)
    obj = ctl.run(ctl.create(
        "Implement word_counter.py, write result.json with the word count, and run test_word_counter.py.",
        success_criteria=["result.json is valid JSON", "words == 2", "tests exit 0"],
        auto=True,
    ))
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") == "VERIFIED", ov
    doc = json.loads((ws / "result.json").read_text(encoding="utf-8"))
    assert doc["words"] == 2
    g = ctl.load_graph(obj)
    repair = [t for t in g.tasks.values() if t.text.startswith("Repair so that machine checks pass")]
    assert repair, [t.text for t in g.tasks.values()]
    orig = [t for t in g.tasks.values() if not t.text.startswith("Repair so that")][0]
    assert repair[0].id in orig.depends_on
    assert orig.verification.get("status") == "VERIFIED"
    for t in g.tasks.values():
        if t.checks:
            assert t.verification.get("status") == "VERIFIED"
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert decisions and decisions[0]["strategy"] == "repair"
    assert decisions[0]["failure_class"] != "ENVIRONMENT_FAILURE"
    assert "FEEDBACK FROM PREVIOUS ATTEMPT" in scripted.prompts[-1] or "Concrete failures" in repair[0].text
    assert "DONE:" not in (ws / "result.json").read_text(encoding="utf-8")


# ---------------------------------------------------------------- A. persistent bad artifacts → not VERIFIED

def test_verified_coding_loop_persistent_bad_artifacts_not_verified(home, ws, scripted):
    """Keeps writing `{` and claiming DONE: — never VERIFIED; false DONE = 0."""
    _seed_tests(ws)
    scripted.script = [
        ([("write_file", {"path": "result.json", "content": BAD_RESULT}),
          ("write_file", {"path": "word_counter.py", "content": BAD_PY})],
         "DONE: done")
    ] * 8
    ctl = Controller(home, session_factory=scripted, llm=_plan_llm(CODING_PLAN), quiet=True)
    obj = ctl.run(ctl.create(
        "Implement word_counter.py and write result.json; run test_word_counter.py.",
        budget=Budget(tool_calls=40, retries=6),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED)
    raw = (ws / "result.json").read_text(encoding="utf-8") if (ws / "result.json").exists() else ""
    try:
        json.loads(raw)
        valid = True
    except Exception:
        valid = False
    assert not valid
    checked = [t for t in ctl.load_graph(obj).tasks.values() if t.checks]
    assert checked
    assert all((t.verification or {}).get("status") != "VERIFIED" for t in checked)


def test_verified_coding_loop_done_pollution_path_is_not_an_artifact(home, ws, scripted):
    """RW-062 pollution: a path named DONE: is refused and cannot become VERIFIED."""
    _seed_tests(ws)
    scripted.script = [
        ([("write_file", {"path": "DONE: result.json", "content": '{"words": 2}'}),
          ("write_file", {"path": "result.json", "content": "DONE: fake path"})],
         "DONE: wrote it"),
    ] * 6
    ctl = Controller(home, session_factory=scripted, llm=_plan_llm(CODING_PLAN), quiet=True)
    obj = ctl.run(ctl.create(
        "Write result.json and run test_word_counter.py.",
        budget=Budget(tool_calls=30, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED)
    assert not (ws / "DONE: result.json").exists()
    if (ws / "result.json").exists():
        try:
            json.loads((ws / "result.json").read_text(encoding="utf-8"))
            valid = True
        except Exception:
            valid = False
        assert not valid


def test_verified_coding_loop_inferred_checks_on_coding_fallback(home, ws):
    """Fallback tasks stay check-less (F-17); coding goals still get objective json_valid + tests."""
    goal = (
        "Create the project. Implement the function. Write the tests. "
        "Run the tests. Write result.json. Verify the result."
    )
    res = Planner(None, str(ws)).plan(Objective.new(goal))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    kinds = {(c.kind, tuple(sorted(c.args.items()))) for c in res["objective_checks"]}
    assert ("json_valid", (("path", "result.json"),)) in kinds
    assert any(c.kind == "shell_ok" for c in res["objective_checks"])


def test_verified_coding_loop_non_coding_fallback_stays_without_checks(home, ws):
    res = Planner(None, str(ws)).plan(Objective.new("write a file and then read it back"))
    assert res["source"] == "fallback"
    assert res["objective_checks"] == []
    assert all(not t.checks for t in res["graph"].tasks.values())


def test_verified_coding_loop_pollution_path_check_fails(home, ws):
    observer = Observer(home.root / "obs")
    v = Verifier(ws, observer, home=home)
    r = v.run_check(Check("json_valid", {"path": "DONE: result.json"}))
    assert r["ok"] is False
    assert "pollution" in r["detail"]
