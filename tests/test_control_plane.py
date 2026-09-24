"""Control plane: objective → plan → execute → observe → verify → recover → complete.

A ScriptedSession stands in for the LLM but *really executes tools* through the
injected tool_runner, so files hit disk and the Verifier checks real state.
"""
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from rad.control import Controller, Objective, ObjectiveStatus, TaskGraph, TaskStatus, Check
from rad.control import events as E
from rad.control.events import EventLog
from rad.control.graph import CycleError
from rad.control.objectives import Budget
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.observer import Observation
from rad.control.tasks import IllegalTransition, Task
from rad.tools import ToolCtx, run_tool


# ---------------------------------------------------------------- fixtures

class ScriptedSession:
    """Each think() pops one script entry: a list of (tool, args) actions then a reply string."""
    script: List[Any] = []
    prompts: List[str] = []

    def __init__(self, home, auto=False, **kw):
        self.home = home
        self.tool_runner = run_tool
        self.ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
        self.turns = 0

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


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


@pytest.fixture
def scripted():
    ScriptedSession.script = []
    ScriptedSession.prompts = []
    return ScriptedSession


def _plan_llm(plan: Dict[str, Any]):
    """An llm callable that returns the given plan JSON for planning prompts."""
    def llm(prompt: str) -> str:
        if "Decompose the goal" in prompt:
            return json.dumps(plan)
        if "strict verifier" in prompt:
            return json.dumps({"pass": True, "reason": "looks fine"})
        return "YES"
    return llm


def _ctl(home, scripted, plan=None, llm=None):
    return Controller(home, session_factory=scripted, llm=llm or (_plan_llm(plan) if plan else None), quiet=True)


# ---------------------------------------------------------------- state machine

def test_task_state_machine_legal_and_illegal():
    t = Task.new("o", "x")
    t.transition(TaskStatus.READY)
    t.transition(TaskStatus.RUNNING)
    assert t.attempts == 1
    with pytest.raises(IllegalTransition):
        t.transition(TaskStatus.COMPLETED)   # must go through OBSERVING/VERIFYING
    t.transition(TaskStatus.OBSERVING)
    t.transition(TaskStatus.VERIFYING)
    t.transition(TaskStatus.COMPLETED)
    assert t.finished and len(t.history) == 5


def test_graph_ready_set_and_cycles():
    a = Task.new("o", "a")
    b = Task.new("o", "b", depends_on=[a.id])
    c = Task.new("o", "c", depends_on=[a.id])
    d = Task.new("o", "d", depends_on=[b.id, c.id])
    g = TaskGraph([a, b, c, d])
    g.validate()
    assert [t.id for t in g.ready()] == [a.id]
    a.status = TaskStatus.COMPLETED
    assert {t.id for t in g.ready()} == {b.id, c.id}       # parallel-ready
    b.status = c.status = TaskStatus.COMPLETED
    assert [t.id for t in g.ready()] == [d.id]
    a.depends_on = [d.id]
    with pytest.raises(CycleError):
        g.topological()


def test_graph_optional_branch_does_not_block():
    a = Task.new("o", "a", optional=True)
    b = Task.new("o", "b", depends_on=[a.id])
    g = TaskGraph([a, b])
    a.status = TaskStatus.FAILED
    a.attempts = a.max_attempts
    assert g.deps_satisfied(b) and not g.deps_doomed(b)


def test_graph_persist_roundtrip():
    a = Task.new("o", "a", checks=[Check("file_exists", {"path": "x"})])
    g = TaskGraph([a])
    g2 = TaskGraph.from_list(json.loads(json.dumps(g.to_list())))
    assert g2.get(a.id).checks[0].kind == "file_exists"


# ---------------------------------------------------------------- happy path

def test_objective_end_to_end_verified(home, ws, scripted):
    plan = {"tasks": [
        {"id": "t1", "text": "write notes.md", "depends_on": [],
         "checks": [{"kind": "file_contains", "args": {"path": "notes.md", "text": "hello"}}]},
        {"id": "t2", "text": "make summary.txt from notes", "depends_on": ["t1"],
         "checks": [{"kind": "file_min_bytes", "args": {"path": "summary.txt", "n": 3}}]},
    ], "objective_checks": [{"kind": "shell_ok", "args": {"command": "test -f notes.md && test -f summary.txt"}}]}
    scripted.script = [
        ([("write_file", {"path": "notes.md", "content": "hello world"})], "DONE: wrote notes"),
        ([("write_file", {"path": "summary.txt", "content": "hello"})], "DONE: summarised"),
    ]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("write notes then summarise", success_criteria=["notes exist", "summary exists"])
    obj = ctl.run(obj)

    assert obj.status == ObjectiveStatus.COMPLETED
    assert obj.verification["objective"]["status"] == "VERIFIED"
    g = ctl.load_graph(obj)
    assert all(t.status == TaskStatus.COMPLETED and t.verification["status"] == "VERIFIED" for t in g.tasks.values())
    assert obj.usage.tool_calls == 2 and obj.usage.model_calls == 2
    # artifacts registered with hashes
    from rad.control.observer import Observer
    arts = Observer(ctl.store.dir(obj.id)).artifacts()
    assert {Path(a["location"]).name for a in arts.values()} == {"notes.md", "summary.txt"}
    assert all(a["sha256"] for a in arts.values())
    # event trail
    kinds = [e.kind for e in EventLog(ctl.store.events_path(obj.id)).all()]
    for k in (E.OBJECTIVE_CREATED, E.PLAN_CREATED, E.TASK_STARTED, E.TOOL_CALLED, E.TOOL_RESULT,
              E.VERIFICATION_RESULT, E.TASK_COMPLETED, E.OBJECTIVE_COMPLETED):
        assert k in kinds, k
    assert "Verification: VERIFIED" in obj.result


# ---------------------------------------------------------------- the core promise: a false DONE is caught

def test_false_done_claim_is_caught_and_retried_with_feedback(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "create report.md", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "report.md"},
                                   "description": "report.md exists"}]}]}
    scripted.script = [
        ([], "I have created report.md with the findings. DONE: report written"),   # lie
        ([("write_file", {"path": "report.md", "content": "real"})], "DONE: actually wrote it"),
    ]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("create report"))

    assert obj.status == ObjectiveStatus.COMPLETED
    t = list(ctl.load_graph(obj).tasks.values())[0]
    assert t.attempts == 2 and t.status == TaskStatus.COMPLETED
    # the retry prompt carried explicit verification feedback
    assert "FEEDBACK FROM PREVIOUS ATTEMPT" in scripted.prompts[1]
    assert "report.md exists" in scripted.prompts[1] or "did NOT pass verification" in scripted.prompts[1]
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert decisions[0]["strategy"] == "retry_with_hint"
    assert decisions[0]["failure_class"] == FailureClass.VALIDATION
    assert obj.usage.retries == 1


def test_persistent_false_done_exhausts_retries_then_needs_user(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "create report.md", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "report.md"}}]}]}
    scripted.script = [([], "DONE: done")] * 5
    # no llm → replan unavailable → ask_user
    ctl = Controller(home, session_factory=scripted, llm=None, quiet=True)
    obj = ctl.create("create report")
    # inject the plan manually since llm=None
    ctl._llm = _plan_llm(plan)
    ctl.plan(obj)
    ctl._llm = None
    obj = ctl.run(obj)
    assert obj.status == ObjectiveStatus.NEEDS_USER
    t = list(ctl.load_graph(obj).tasks.values())[0]
    assert t.status == TaskStatus.NEEDS_USER and t.attempts == 3
    assert not (ws / "report.md").exists()


# ---------------------------------------------------------------- unverifiable tasks are labelled, not laundered

def test_task_without_checks_is_recorded_unverified(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "think about it", "depends_on": [], "checks": []}]}
    scripted.script = [([], "DONE: thought")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("think"))
    assert obj.status == ObjectiveStatus.COMPLETED
    t = list(ctl.load_graph(obj).tasks.values())[0]
    assert t.status == TaskStatus.COMPLETED and t.verification["status"] == "UNVERIFIED"
    assert obj.verification["objective"]["tasks_unverified"] == [t.id]
    assert "without machine verification" in obj.result


def test_task_without_checks_and_without_done_claim_fails(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "do a thing", "depends_on": [], "checks": []}]}
    scripted.script = [([], "Here is some text about the thing.")] * 4
    ctl = Controller(home, session_factory=scripted, llm=None, quiet=True)
    obj = ctl.create("thing")
    ctl._llm = _plan_llm(plan); ctl.plan(obj); ctl._llm = None
    obj = ctl.run(obj)
    assert obj.status == ObjectiveStatus.NEEDS_USER


# ---------------------------------------------------------------- tool failure → recovery

def test_tool_error_is_observed_and_classified(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "read config", "depends_on": [],
                       "checks": [{"kind": "reply_matches", "args": {"pattern": "port"}}]}]}
    scripted.script = [
        ([("read_file", {"path": "missing.json"})], "DONE: the port is 80"),
        ([("write_file", {"path": "missing.json", "content": "{}"}), ("read_file", {"path": "missing.json"})],
         "DONE: port 80"),
    ]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("read config"))
    assert obj.status == ObjectiveStatus.COMPLETED
    log = EventLog(ctl.store.events_path(obj.id))
    results = [e.data for e in log.read(kind=E.TOOL_RESULT)]
    assert results[0]["status"] == "error"
    dec = [e.data for e in log.read(kind=E.RECOVERY_DECISION)][0]
    assert dec["failure_class"] == FailureClass.TOOL


def test_environment_failure_inserts_repair_task(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "run build", "depends_on": [],
                       "checks": [{"kind": "file_min_bytes", "args": {"path": "out.txt", "n": 1}}]}]}
    scripted.script = [
        ([("run_shell", {"command": "definitely_not_a_command_xyz > out.txt"})], "DONE: built"),
        ([("write_file", {"path": "tool.sh", "content": "echo ok"})], "DONE: repaired"),          # repair task
        ([("run_shell", {"command": "sh tool.sh > out.txt"})], "DONE: built"),                     # retry
    ]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("build"))
    assert obj.status == ObjectiveStatus.COMPLETED
    g = ctl.load_graph(obj)
    assert len(g.tasks) == 2
    repair = [t for t in g.tasks.values() if t.text.startswith("Repair prerequisite")][0]
    orig = [t for t in g.tasks.values() if t is not repair][0]
    assert repair.id in orig.depends_on
    assert orig.failure_class == FailureClass.ENVIRONMENT


def test_model_exception_is_retried(home, ws, scripted):
    from rad.providers import ProviderError
    plan = {"tasks": [{"id": "t1", "text": "x", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "x"}}]}]}
    scripted.script = [ProviderError("all providers failed: groq: HTTP 503"),
                       ([("write_file", {"path": "x", "content": "1"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("x"))
    assert obj.status == ObjectiveStatus.COMPLETED
    dec = [e.data for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.RECOVERY_DECISION)][0]
    assert dec["failure_class"] == FailureClass.MODEL and dec["strategy"] == "retry"


# ---------------------------------------------------------------- explicit signals

def test_needs_user_signal_pauses_objective(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "log in", "depends_on": [], "checks": []},
                      {"id": "t2", "text": "after", "depends_on": ["t1"], "checks": []}]}
    scripted.script = [([], "NEEDS_USER: what is your password?")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("login"))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    g = ctl.load_graph(obj)
    st = {t.text: t.status for t in g.tasks.values()}
    assert st["log in"] == TaskStatus.NEEDS_USER and st["after"] == TaskStatus.BLOCKED
    assert scripted.script == []  # t2 never ran


def test_both_blocked_and_needs_user_signals_do_not_crash(home, ws, scripted):
    """Regression: a reply containing BOTH markers must end NEEDS_USER (which wins),
    never raise IllegalTransition on NEEDS_USER -> BLOCKED."""
    message = "NEEDS_USER: which machine to target?\nBLOCKED: cannot proceed otherwise"
    plan = {"tasks": [{"id": "t1", "text": "decide", "depends_on": [], "checks": []}]}
    scripted.script = [([], message)]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("decide"))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    g = ctl.load_graph(obj)
    st = {t.text: t.status for t in g.tasks.values()}
    assert st["decide"] == TaskStatus.NEEDS_USER


# ---------------------------------------------------------------- budgets

def test_tool_call_budget_stops_run(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "spam", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "never"}}]}]}
    scripted.script = [([("list_dir", {})] * 10, "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("spam", budget=Budget(tool_calls=3))
    obj = ctl.run(obj)
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert "tool-call budget" in obj.failure
    assert obj.usage.tool_calls == 3
    assert EventLog(ctl.store.events_path(obj.id)).count(E.BUDGET_EXCEEDED) == 1


def test_budget_exhaust_after_graph_complete_still_verifies(home, ws, scripted):
    """Class A: a finished graph must not be reported needs_user just because the last
    tool call filled the budget. Verification still has to pass."""
    plan = {"tasks": [
        {"id": "t1", "text": "a", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]},
        {"id": "t2", "text": "b", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]},
    ], "objective_checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]}
    scripted.script = [
        ([("write_file", {"path": "a.txt", "content": "a"})], "DONE: a"),
        ([("write_file", {"path": "b.txt", "content": "b"})], "DONE: b"),
    ]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("ab", budget=Budget(tool_calls=2)))
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    assert EventLog(ctl.store.events_path(obj.id)).count(E.BUDGET_EXCEEDED) == 1


def test_overdecompose_budget_completes_when_objective_checks_pass(home, ws, scripted):
    """11B pattern: extra planned tasks, goal file already on disk, tool budget dies.

    Completing is allowed only because objective machine checks pass — not because
    the model said DONE.
    """
    plan = {"tasks": [
        {"id": "t1", "text": "write hello", "depends_on": [],
         "checks": [{"kind": "file_contains", "args": {"path": "live_hello.txt", "text": "hello"}}]},
        {"id": "t2", "text": "also write README", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "README.md"}}]},
        {"id": "t3", "text": "also write backup", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "hello.bak"}}]},
    ], "objective_checks": [
        {"kind": "file_contains", "args": {"path": "live_hello.txt", "text": "hello"}},
    ]}
    scripted.script = [
        ([("write_file", {"path": "live_hello.txt", "content": "hello\n"})], "DONE: hello"),
        ([("write_file", {"path": "README.md", "content": "x"})], "DONE: readme"),
    ]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("hello", budget=Budget(tool_calls=1)))
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert (obj.verification or {}).get("objective", {}).get("status") == "VERIFIED"
    assert (ws / "live_hello.txt").read_text().strip() == "hello"
    g = ctl.load_graph(obj)
    leftover = [t for t in g.tasks.values() if t.text.startswith("also")]
    assert leftover and all(t.status == TaskStatus.CANCELLED for t in leftover)


def test_budget_exhaust_without_met_checks_still_needs_user(home, ws, scripted):
    """Do not weaken DONE: exhausted budget + unmet checks stays needs_user."""
    plan = {"tasks": [
        {"id": "t1", "text": "write hello", "depends_on": [],
         "checks": [{"kind": "file_contains", "args": {"path": "live_hello.txt", "text": "hello"}}]},
    ], "objective_checks": [
        {"kind": "file_contains", "args": {"path": "live_hello.txt", "text": "hello"}},
    ]}
    scripted.script = [([("list_dir", {})], "DONE: I thought about it")] * 4
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("hello", budget=Budget(tool_calls=1, retries=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert not (ws / "live_hello.txt").exists()


def test_retry_budget_is_respected(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "x", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "x"}}]}]}
    scripted.script = [([], "DONE")] * 6
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("x", budget=Budget(retries=1)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert obj.usage.retries == 1


# ---------------------------------------------------------------- crash → resume

def test_checkpoint_and_resume_after_interruption(home, ws, scripted):
    plan = {"tasks": [
        {"id": "t1", "text": "a", "depends_on": [], "checks": [{"kind": "file_exists", "args": {"path": "a"}}]},
        {"id": "t2", "text": "b", "depends_on": ["t1"], "checks": [{"kind": "file_exists", "args": {"path": "b"}}]},
        {"id": "t3", "text": "c", "depends_on": ["t2"], "checks": [{"kind": "file_exists", "args": {"path": "c"}}]},
    ]}
    scripted.script = [([("write_file", {"path": "a", "content": "1"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("abc")
    obj = ctl.run(obj, max_tasks=1)              # simulate stopping after one task
    assert obj.status == ObjectiveStatus.RUNNING
    g = ctl.load_graph(obj)
    assert [t.status for t in g.tasks.values()] == [TaskStatus.COMPLETED, TaskStatus.PENDING, TaskStatus.PENDING]

    # simulate a crash mid-task: mark t2 RUNNING on disk
    g.tasks[g.order[1]].status = TaskStatus.RUNNING
    ctl.store.save_tasks(obj.id, g.to_list())

    # brand new controller/process
    scripted.script = [([("write_file", {"path": "b", "content": "1"})], "DONE"),
                       ([("write_file", {"path": "c", "content": "1"})], "DONE")]
    ctl2 = _ctl(home, scripted, plan)
    obj2 = ctl2.resume(obj.id)
    assert obj2.status == ObjectiveStatus.COMPLETED
    g2 = ctl2.load_graph(obj2)
    assert all(t.status == TaskStatus.COMPLETED for t in g2.tasks.values())
    assert g2.tasks[g2.order[0]].attempts == 1         # completed task was NOT re-run
    assert any(h["note"] == "interrupted" for h in g2.tasks[g2.order[1]].history)
    assert len(scripted.prompts) == 3


def test_resume_clears_task_needs_user_while_objective_running(home, ws, scripted):
    """A permission ask mid-run sets task NEEDS_USER without flipping the objective.
    resume must clear it anyway, or the task is stuck forever (seen in RW073 soak)."""
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a"}}]}]}
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("x")
    if not ctl.store.load_tasks(obj.id):
        ctl.plan(obj)
    g = ctl.load_graph(obj)
    g.tasks[g.order[0]].status = TaskStatus.NEEDS_USER
    obj.status = ObjectiveStatus.RUNNING          # objective never left running
    ctl.store.save(obj)
    ctl.store.save_tasks(obj.id, g.to_list())
    assert obj.status not in (ObjectiveStatus.PAUSED, ObjectiveStatus.NEEDS_USER)

    scripted.script = [([("write_file", {"path": "a", "content": "1"})], "DONE")]
    obj2 = ctl.resume(obj.id)
    g2 = ctl.load_graph(obj)
    assert g2.tasks[g2.order[0]].status == TaskStatus.COMPLETED
    assert obj2.status == ObjectiveStatus.COMPLETED


def test_repair_task_never_spawns_repair_of_repair():
    """ENVIRONMENT on a repair task must not insert another repair step —
    retry/ask_user only (the broken-artifact branch already had this guard;
    the ENVIRONMENT branch was missing it and spawned repair-of-repair chains)."""
    def env_obs(task_id: str) -> list:
        return [Observation.new(
            objective_id="o", task_id=task_id, action_id="a1", tool="run_shell",
            args={"command": "pytest -q"}, status="error", duration_ms=10,
            output="[stderr] /usr/bin/bash: line 1: pytest: command not found [exit=127]")]

    repair = Task.new("o", "Repair prerequisite so that this can succeed: run the tests")
    assert classify(repair, env_obs(repair.id)) == FailureClass.ENVIRONMENT
    d = RecoveryEngine().decide(repair, env_obs(repair.id), retries_left=5)
    assert d.strategy != "repair"
    assert d.strategy in ("retry", "retry_with_hint", "switch_tool")

    normal = Task.new("o", "Run the unit tests using pytest and verify all tests pass.")
    d2 = RecoveryEngine().decide(normal, env_obs(normal.id), retries_left=5)
    assert d2.strategy == "repair"


def test_resume_by_prefix_and_last(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []}]}
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("x")
    assert ctl.store.resolve(obj.id[:6]).id == obj.id
    assert ctl.store.resolve("last").id == obj.id
    assert ctl.store.resolve("obj_nope") is None


# ---------------------------------------------------------------- pause / cancel

def test_cancel_marks_all_open_tasks(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []},
                      {"id": "t2", "text": "b", "depends_on": ["t1"], "checks": []}]}
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("x")
    ctl.plan(obj)
    obj = ctl.cancel(obj.id)
    assert obj.status == ObjectiveStatus.CANCELLED
    assert all(t.status == TaskStatus.CANCELLED for t in ctl.load_graph(obj).tasks.values())
    assert ctl.resume(obj.id).status == ObjectiveStatus.CANCELLED   # cannot resume a cancelled objective


# ---------------------------------------------------------------- planner fallback / robustness

def test_planner_fallback_without_brain(home, ws, scripted):
    ctl = Controller(home, session_factory=scripted, llm=None, quiet=True)
    obj = ctl.create("write a file and then read it back")
    g = ctl.plan(obj)
    assert len(g.tasks) == 2
    assert all(not t.checks for t in g.tasks.values())
    src = [e.data["source"] for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.PLAN_CREATED)][0]
    assert src == "fallback"


def test_planner_tolerates_bad_llm_plan(home, ws, scripted):
    bad = {"tasks": [{"id": "a", "text": "A", "depends_on": ["b"]}, {"id": "b", "text": "B", "depends_on": ["a"]},
                     {"id": "c", "text": "C", "depends_on": ["ghost"]}]}
    ctl = _ctl(home, scripted, bad)
    g = ctl.plan(ctl.create("x"))
    g.validate()                                  # no cycle, no unknown deps
    assert len(g.tasks) == 3


# ---------------------------------------------------------------- recovery policy unit tests

def test_classify_failures():
    t = Task.new("o", "x")
    assert classify(t, [], error="all providers failed") == FailureClass.MODEL
    from rad.control.observer import Observation
    def ob(out, status="error"):
        return Observation.new(objective_id="o", task_id=t.id, action_id="a", tool="run_shell", args={},
                               status=status, output=out, duration_ms=1)
    assert classify(t, [ob("HTTP 401 unauthorized")]) == FailureClass.AUTH
    assert classify(t, [ob("BLOCKED by safety policy: x", "blocked")]) == FailureClass.PERMISSION
    assert classify(t, [ob("network: connection refused")]) == FailureClass.NETWORK
    assert classify(t, [ob("sh: 1: foo: command not found")]) == FailureClass.ENVIRONMENT
    assert classify(t, [], verification={"status": "FAILED"}) == FailureClass.VALIDATION
    assert classify(t, [ob("tool error: boom")]) == FailureClass.TOOL


def test_recovery_bounded():
    eng = RecoveryEngine()
    t = Task.new("o", "x", max_attempts=2)
    t.attempts = 1
    d = eng.decide(t, [], verification={"status": "FAILED", "results": []})
    assert d.strategy == "retry_with_hint"
    t.attempts = 2
    d = eng.decide(t, [], verification={"status": "FAILED", "results": []})
    assert d.strategy == "replan"
    d = eng.decide(t, [], verification={"status": "FAILED", "results": []}, repairs_so_far=1)
    assert d.strategy == "ask_user"
    t.attempts = 0
    assert eng.decide(t, [], verification={"status": "FAILED", "results": []}, retries_left=0).strategy == "replan"


def test_shell_created_files_become_artifacts(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "gen", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "gen.txt"}}]}]}
    scripted.script = [([("run_shell", {"command": "echo hi > gen.txt"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("gen"))
    assert obj.status == ObjectiveStatus.COMPLETED
    from rad.control.observer import Observer
    arts = Observer(ctl.store.dir(obj.id)).artifacts()
    assert [Path(a["location"]).name for a in arts.values()] == ["gen.txt"]
    assert list(arts.values())[0]["creator"] == "run_shell"


def test_artifact_versioning_lineage(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "v1", "depends_on": [], "checks": []},
                      {"id": "t2", "text": "v2", "depends_on": ["t1"], "checks": []}]}
    scripted.script = [([("write_file", {"path": "doc.md", "content": "one"})], "DONE"),
                       ([("write_file", {"path": "doc.md", "content": "two"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("doc"))
    from rad.control.observer import Observer
    arts = sorted(Observer(ctl.store.dir(obj.id)).artifacts().values(), key=lambda a: a["version"])
    assert [a["version"] for a in arts] == [1, 2]
    assert arts[1]["parent"] == arts[0]["id"]
    assert arts[0]["sha256"] != arts[1]["sha256"]
