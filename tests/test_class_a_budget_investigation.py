"""Deterministic Class A investigation: tool-budget exhausted → needs_user.

No live NIM. Scripted sessions inject tool counts. Architecture frozen:
Needle off, max_plan_tasks 16, default Budget.tool_calls 60 — all asserted,
none changed.

Parked suspects:
  F-20260918-17 — fallback planner splits multiline objective newlines
  F-20260918-18 — ENVIRONMENT_FAILURE misclass burns tool budget

Scenarios:
  A — objectively complete + budget exhausted → VERIFY → DONE
  B — incomplete but recoverable + budget exhausted → checkpoint + resume
  C — incomplete and not recoverable → needs_user (not VERIFIED)
"""
from __future__ import annotations

import json

import pytest

from rad.control import Controller, ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observation
from rad.control.planner import Planner
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Task
from rad.tools import ToolCtx, run_tool


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


def _ob(task: Task, out: str, status: str = "error", tool: str = "run_shell") -> Observation:
    return Observation.new(objective_id="o", task_id=task.id, action_id="a", tool=tool,
                           args={}, status=status, output=out, duration_ms=1)


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


# ---------------------------------------------------------------- architecture freeze (must not change)

def test_investigation_does_not_raise_caps_or_enable_needle(home):
    from rad.control.planner import Planner as P
    from rad.home import DEFAULTS
    from rad.toolrouter import resolve_tool_router

    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert P(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


# ---------------------------------------------------------------- F-20260918-17 — fallback newlines

def test_fallback_planner_does_not_split_on_newlines():
    """F-17 suspected: newlines in a multiline objective become spurious tasks.

    Fallback splits on clause markers (and then / then / ; / , and / period+space),
    not on newlines. A production-shaped multiline goal without those markers is
    one task, not one task per line.
    """
    obj = Objective.new(
        "Create a text analyzer under text_analyzer/\n"
        "Required files:\n"
        "- analyzer.py\n"
        "- input.txt\n"
        "- summary.json\n"
        "- test_analyzer.py\n"
        "- README.md"
    )
    g = Planner(None, "/tmp/ws")._fallback(obj)
    texts = [t.text for t in g.tasks.values()]
    assert len(texts) == 1, texts
    assert "analyzer.py" in texts[0] and "README.md" in texts[0]


def test_fallback_planner_splits_on_clause_markers_not_wrapping():
    obj = Objective.new("write a file and then read it back")
    g = Planner(None, "/tmp/ws")._fallback(obj)
    assert len(g.tasks) == 2


def test_fallback_planner_period_split_is_clause_not_newline():
    """Periods still split (documented clause split). That is not the F-17 newline claim."""
    obj = Objective.new("Write analyzer.py. Write input.txt. Write summary.json.")
    g = Planner(None, "/tmp/ws")._fallback(obj)
    assert len(g.tasks) == 3


def test_llm_plan_is_used_when_brain_returns_json(home, ws):
    """RW-058/059/060 had a live brain — fallback is not the production planner path."""
    plan = {"tasks": [
        {"id": "t1", "text": "write analyzer", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}}]},
        {"id": "t2", "text": "write tests", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "text_analyzer/test_analyzer.py"}}]},
    ], "objective_checks": [{"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}}]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.create("multiline\ngoal\nwith\nnewlines")
    g = ctl.plan(obj)
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    assert src == "llm"
    assert len(g.tasks) == 2


# ---------------------------------------------------------------- F-20260918-18 — ENVIRONMENT vs VALIDATION

def test_failed_checks_without_env_output_are_validation_not_environment():
    """RW-059 shape: tests fail 13!=6 / invalid JSON — no env-token in observations.

    F-18: this is not ENVIRONMENT (that claim stays closed). v0.3.0 verified
    coding loop inserts a repair step with the concrete failure instead of an
    unstructured retry.
    """
    t = Task.new("o", "write summary.json")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "json_valid", "detail": "summary.json invalid JSON"},
        {"ok": False, "kind": "shell_ok", "detail": "exit=1 AssertionError: 13 != 6"},
    ]}
    ob = _ob(t, "AssertionError: 13 != 6\n[exit=1]")
    assert classify(t, [ob], verification=ver) == FailureClass.TOOL
    d = RecoveryEngine().decide(t, [ob], verification=ver, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy == "repair"
    assert "json_valid" in d.hint or "invalid JSON" in d.hint
    assert "13 != 6" in d.hint or "shell_ok" in d.hint


def test_missing_file_check_alone_is_validation_not_repair():
    """file_exists fail with no tool error → VALIDATION → retry_with_hint, not repair."""
    t = Task.new("o", "write summary.json")
    t.attempts = 1
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "/ws/summary.json exists=False"},
    ]}
    assert classify(t, [], verification=ver) == FailureClass.VALIDATION
    d = RecoveryEngine().decide(t, [], verification=ver, retries_left=3)
    assert d.strategy == "retry_with_hint"
    assert d.failure_class == FailureClass.VALIDATION


def test_command_not_found_is_environment_repair_by_design():
    """Genuine missing binary is ENVIRONMENT → repair. Not the F-18 misclass claim."""
    t = Task.new("o", "run build")
    t.attempts = 1
    ob = _ob(t, "sh: 1: mkreport_xyz: command not found")
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "out.txt exists=False"},
    ]}
    assert classify(t, [ob], verification=ver) == FailureClass.ENVIRONMENT
    d = RecoveryEngine().decide(t, [ob], verification=ver, repairs_so_far=0, retries_left=3)
    assert d.strategy == "repair"


def test_env_token_in_tool_output_is_environment_even_if_checks_failed():
    """Documents current classify order: _ENV matches observation text before VALIDATION.

    This is the parked F-18 overlap. It is the same path as the designed
    command-not-found repair (see test_environment_failure_inserts_repair_task).
    A missing-file cat during an otherwise-validation failure is classified
    ENVIRONMENT and may insert one repair. That is not a lifecycle skip and
    does not rubber-stamp DONE.
    """
    t = Task.new("o", "write summary")
    t.attempts = 1
    ob = _ob(t, "cat: summary.json: No such file or directory")
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "summary.json exists=False"},
    ]}
    assert classify(t, [ob], verification=ver) == FailureClass.ENVIRONMENT


def test_environment_repair_does_not_skip_verify_or_fake_done(home, ws):
    """F-18 budget-burn claim: repair may add a task, but VERIFIED still needs checks."""
    ScriptedSession.script = [
        ([("run_shell", {"command": "definitely_not_a_command_xyz > out.txt"})], "DONE: built"),
        ([("write_file", {"path": "tool.sh", "content": "echo ok"})], "DONE: repaired"),
        ([("run_shell", {"command": "sh tool.sh > out.txt"})], "DONE: built"),
    ]
    ScriptedSession.prompts = []
    plan = {"tasks": [{"id": "t1", "text": "run build", "depends_on": [],
                       "checks": [{"kind": "file_min_bytes", "args": {"path": "out.txt", "n": 1}}]}],
            "objective_checks": [{"kind": "file_min_bytes", "args": {"path": "out.txt", "n": 1}}]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("build", budget=Budget(tool_calls=10, retries=6)))
    assert obj.status == ObjectiveStatus.COMPLETED
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    g = ctl.load_graph(obj)
    assert any(t.text.startswith("Repair prerequisite") for t in g.tasks.values())
    log = EventLog(ctl.store.events_path(obj.id))
    classes = [e.data["failure_class"] for e in log.read(kind=E.RECOVERY_DECISION)]
    assert FailureClass.ENVIRONMENT in classes


# ---------------------------------------------------------------- Scenario A — complete + budget exhausted → DONE

def test_scenario_a_objective_checks_pass_at_budget_is_verified_not_needs_user(home, ws):
    """Some tasks complete, leftover planned work, budget dies, objective checks pass."""
    ScriptedSession.script = [
        ([("write_file", {"path": "goal.txt", "content": "ok"})], "DONE: goal"),
        ([("write_file", {"path": "README.md", "content": "x"})], "DONE: readme"),
        ([("write_file", {"path": "backup.bak", "content": "x"})], "DONE: bak"),
    ]
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "write goal", "depends_on": [],
         "checks": [{"kind": "file_contains", "args": {"path": "goal.txt", "text": "ok"}}]},
        {"id": "t2", "text": "also README", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "README.md"}}]},
        {"id": "t3", "text": "also backup", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "backup.bak"}}]},
    ], "objective_checks": [
        {"kind": "file_contains", "args": {"path": "goal.txt", "text": "ok"}},
    ]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("goal", budget=Budget(tool_calls=1)))
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    assert EventLog(ctl.store.events_path(obj.id)).count(E.BUDGET_EXCEEDED) == 1
    leftover = [t for t in ctl.load_graph(obj).tasks.values() if t.text.startswith("also")]
    assert leftover and all(t.status == TaskStatus.CANCELLED for t in leftover)


def test_scenario_a_graph_complete_at_budget_still_verifies(home, ws):
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "a"})], "DONE: a"),
        ([("write_file", {"path": "b.txt", "content": "b"})], "DONE: b"),
    ]
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "a", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]},
        {"id": "t2", "text": "b", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]},
    ], "objective_checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("ab", budget=Budget(tool_calls=2)))
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"


# ---------------------------------------------------------------- Scenario B — incomplete recoverable + budget exhausted

def test_scenario_b_budget_stop_checkpoints_and_resume_continues(home, ws):
    """Budget dies with remaining work. Status is needs_user (not failed), checkpoint
    is on disk, and resume with a raised budget continues remaining tasks."""
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "a"})], "DONE: a"),
        ([("write_file", {"path": "b.txt", "content": "b"})], "DONE: b"),
        ([("write_file", {"path": "c.txt", "content": "c"})], "DONE: c"),
    ]
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "a", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]},
        {"id": "t2", "text": "b", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]},
        {"id": "t3", "text": "c", "depends_on": ["t2"],
         "checks": [{"kind": "file_exists", "args": {"path": "c.txt"}}]},
    ], "objective_checks": [
        {"kind": "file_exists", "args": {"path": "a.txt"}},
        {"kind": "file_exists", "args": {"path": "b.txt"}},
        {"kind": "file_exists", "args": {"path": "c.txt"}},
    ]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("abc", budget=Budget(tool_calls=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER, obj.failure
    assert "tool-call budget" in obj.failure
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert (ws / "a.txt").exists()
    assert not (ws / "c.txt").exists()
    cp = ctl.checkpoints.read_cp(obj.id)
    assert cp.get("status") == ObjectiveStatus.NEEDS_USER
    assert cp.get("seq", 0) >= 1
    g = ctl.load_graph(obj)
    done = [t for t in g.tasks.values() if t.status == TaskStatus.COMPLETED]
    open_ish = [t for t in g.tasks.values() if t.status != TaskStatus.COMPLETED]
    assert len(done) == 1 and open_ish

    obj.budget.tool_calls = 10
    ctl.store.save(obj)
    obj = ctl.resume(obj.id)
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    assert (ws / "c.txt").read_text() == "c"


def test_scenario_b_does_not_terminate_as_failed_when_work_remains(home, ws):
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "a"})], "DONE: a"),
        ([("list_dir", {})], "DONE: looking"),
    ]
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "a", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]},
        {"id": "t2", "text": "b", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]},
    ], "objective_checks": [
        {"kind": "file_exists", "args": {"path": "a.txt"}},
        {"kind": "file_exists", "args": {"path": "b.txt"}},
    ]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("ab", budget=Budget(tool_calls=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert obj.status != ObjectiveStatus.FAILED
    assert obj.status != ObjectiveStatus.COMPLETED


# ---------------------------------------------------------------- Scenario C — incomplete, not recoverable

def test_scenario_c_unmet_checks_at_budget_stay_needs_user(home, ws):
    """RW-058/059/060 shape: budget dies, required artifacts/checks unmet → needs_user."""
    ScriptedSession.script = [([("list_dir", {})], "DONE: I thought about it")] * 6
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "write hello", "depends_on": [],
         "checks": [{"kind": "file_contains", "args": {"path": "live_hello.txt", "text": "hello"}}]},
        {"id": "t2", "text": "write summary", "depends_on": ["t1"],
         "checks": [{"kind": "json_valid", "args": {"path": "summary.json"}}]},
    ], "objective_checks": [
        {"kind": "file_contains", "args": {"path": "live_hello.txt", "text": "hello"}},
        {"kind": "json_valid", "args": {"path": "summary.json"}},
    ]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("hello", budget=Budget(tool_calls=1, retries=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert not (ws / "live_hello.txt").exists()
    assert not (ws / "summary.json").exists()


def test_scenario_c_present_but_invalid_artifact_is_not_verified(home, ws):
    """RW-059: files exist but machine checks fail (invalid JSON / wrong counts)."""
    ScriptedSession.script = [
        ([("write_file", {"path": "summary.json", "content": "{not json"})], "DONE: summary"),
        ([("write_file", {"path": "extra.txt", "content": "x"})], "DONE: extra"),
    ]
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "write summary", "depends_on": [],
         "checks": [{"kind": "json_valid", "args": {"path": "summary.json"}}]},
        {"id": "t2", "text": "polish", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "extra.txt"}}]},
    ], "objective_checks": [
        {"kind": "json_valid", "args": {"path": "summary.json"}},
        {"kind": "json_field", "args": {"path": "summary.json", "key": "words", "equals": 13}},
    ]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("summary", budget=Budget(tool_calls=1, retries=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert (ws / "summary.json").exists()


def test_scenario_c_model_done_claim_does_not_complete(home, ws):
    ScriptedSession.script = [([("list_dir", {})], "DONE: all files written perfectly")] * 4
    ScriptedSession.prompts = []
    plan = {"tasks": [
        {"id": "t1", "text": "write report", "depends_on": [],
         "checks": [{"kind": "file_min_bytes", "args": {"path": "pathlib_reference.md", "n": 500}}]},
    ], "objective_checks": [
        {"kind": "file_min_bytes", "args": {"path": "pathlib_reference.md", "n": 500}},
    ]}
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("research", budget=Budget(tool_calls=1, retries=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
