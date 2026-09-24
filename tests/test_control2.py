"""Control plane 2.0 — scheduler, budgets, executor pipeline, checkpoints, lifecycle.

These tests exercise the *mechanisms* the final architecture depends on:
dependency-aware scheduling with branches, hard budget enforcement (including
tokens/agents), the mandatory action pipeline, crash-restore, and the objective
state machine. They run without a model: scripted sessions drive real tools.
"""
import json
import time
from pathlib import Path

import pytest

from rad.control import Controller, ObjectiveStatus
from rad.control import events as E
from rad.control.budgets import BudgetExceeded, BudgetManager
from rad.control.checkpoints import CheckpointManager
from rad.control.events import EventLog
from rad.control.graph import TaskGraph
from rad.control.lifecycle import IllegalObjectiveTransition, Lifecycle
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observer
from rad.control.scheduler import Scheduler
from rad.control.tasks import Check, Task, TaskStatus
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm


# ---------------------------------------------------------------- fixtures

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


# ---------------------------------------------------------------- scheduler

def test_ready_batch_respects_dependencies_and_priority():
    g = TaskGraph()
    a = Task.new("o", "a")
    b = Task.new("o", "b", depends_on=[a.id])
    c = Task.new("o", "c", priority="high")          # independent, but more urgent
    d = Task.new("o", "d")
    for t in (a, b, c, d):
        g.add(t)
    s = Scheduler(parallel=2)
    assert [t.id for t in g.ready()] == [a.id, c.id, d.id]     # b waits for a
    batch = s.next_batch(g)
    assert [t.id for t in batch.tasks] == [c.id, a.id]         # priority beats insertion order
    for t in batch.tasks:
        t.transition(TaskStatus.READY)
        t.transition(TaskStatus.RUNNING); t.transition(TaskStatus.OBSERVING)
        t.transition(TaskStatus.VERIFYING); t.transition(TaskStatus.COMPLETED)
    assert {t.id for t in s.next_batch(g).tasks} == {b.id, d.id}


def test_optional_dependency_does_not_block():
    g = TaskGraph()
    a = Task.new("o", "a", optional=True)
    b = Task.new("o", "b", depends_on=[a.id])
    g.add(a); g.add(b)
    a.transition(TaskStatus.READY); a.transition(TaskStatus.RUNNING)
    a.transition(TaskStatus.OBSERVING); a.transition(TaskStatus.FAILED)
    a.transition(TaskStatus.BLOCKED, "gave up")
    assert [t.id for t in g.ready()] == [b.id]


def test_alternative_branch_activates_and_rescues_dependents():
    """primary fails for good → its alternative runs → dependents unblock."""
    g = TaskGraph()
    alt = Task.new("o", "fallback: fetch from mirror", active=False)
    primary = Task.new("o", "fetch from api", alternatives=[alt.id])
    after = Task.new("o", "analyse", depends_on=[primary.id])
    for t in (alt, primary, after):
        g.add(t)
    primary.status = TaskStatus.FAILED
    primary.attempts = primary.max_attempts          # no retries left
    s = Scheduler(parallel=1)
    assert g.deps_doomed(after) is False             # a live alternative may rescue it
    activated = s.activate_branches(g)
    assert [t.id for t in activated] == [alt.id] and alt.status == TaskStatus.READY
    alt.transition(TaskStatus.RUNNING); alt.transition(TaskStatus.OBSERVING)
    alt.transition(TaskStatus.VERIFYING); alt.transition(TaskStatus.COMPLETED)
    assert g.deps_satisfied(after) and [t.id for t in g.ready()] == [after.id]


def test_failure_branch_and_doomed_blocking():
    g = TaskGraph()
    diag = Task.new("o", "diagnose why the build broke", active=False)
    build = Task.new("o", "build", on_failure=[diag.id])
    after = Task.new("o", "publish", depends_on=[build.id])
    g.add(diag); g.add(build); g.add(after)
    build.status = TaskStatus.FAILED
    build.attempts = build.max_attempts
    s = Scheduler(parallel=1)
    s.activate_branches(g)
    assert diag.status == TaskStatus.READY           # diagnostic branch runs
    blocked = s.block_doomed(g)
    # the branch is *diagnostic*: dependents of a permanently failed task still block,
    # unless an alternative branch succeeds (see test_alternative_branch_activates_and_rescues_dependents)
    assert [t.id for t in blocked] == [after.id] and after.status == TaskStatus.BLOCKED
    assert "unmet prerequisite" in after.note
    diag.transition(TaskStatus.RUNNING); diag.transition(TaskStatus.OBSERVING)
    diag.transition(TaskStatus.VERIFYING); diag.transition(TaskStatus.COMPLETED)
    assert after.status == TaskStatus.BLOCKED


def test_critical_path_is_a_chain():
    g = TaskGraph()
    a = Task.new("o", "a"); b = Task.new("o", "b", depends_on=[a.id])
    c = Task.new("o", "c", depends_on=[b.id]); d = Task.new("o", "d")
    for t in (a, b, c, d):
        g.add(t)
    assert Scheduler.critical_path(g) == [a.id, b.id, c.id]


# ---------------------------------------------------------------- budgets

def test_budget_manager_covers_every_kind():
    b = Budget(tool_calls=2, model_calls=1, retries=1, seconds=10, money_usd=0.5, tokens=100, agents=1)
    obj = Objective.new("x", budget=b)
    mgr = BudgetManager(b, obj.usage, objective_id=obj.id)
    assert mgr.check() is None
    mgr.charge_tool(); mgr.charge_tool()
    ex = mgr.check()
    assert ex is not None and "tool-call" in ex.reason and ex.kind == "tool_calls"
    mgr2 = BudgetManager(Budget(tokens=5), obj.usage)
    mgr2.charge_model(tokens=5)
    assert mgr2.check().kind == "tokens"
    mgr3 = BudgetManager(Budget(agents=1), obj.usage)
    mgr3.charge_agent()
    assert mgr3.check().kind == "agents"
    mgr4 = BudgetManager(Budget(money_usd=0.01), obj.usage)
    mgr4.charge_model(money=0.02)
    assert mgr4.check().kind == "money_usd"
    snap = mgr4.snapshot()
    assert snap.account["money_usd"]["used"] >= 0.02 and snap.exceeded
    assert "money_usd" in snap.render() or "money" in snap.render()


def test_budget_warning_event_is_emitted_once(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "spam", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "never"}}]}]}
    scripted.script = [([("list_dir", {})] * 10, "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("spam", budget=Budget(tool_calls=4))
    obj = ctl.run(obj)
    log = EventLog(ctl.store.events_path(obj.id))
    warnings = [e.data for e in log.read(kind=E.BUDGET_WARNING)]
    assert len(warnings) == 1 and warnings[0]["budget"] == "tool_calls"
    assert obj.status == ObjectiveStatus.NEEDS_USER


def test_token_budget_stops_run(home, ws):
    class TokenSession(ScriptedSession):
        def __init__(self, home, auto=False, **kw):
            super().__init__(home, auto=auto, **kw)
            self.last_usage = {"in": 900, "out": 100, "rounds": 1}

    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []},
                      {"id": "t2", "text": "b", "depends_on": ["t1"], "checks": []}]}
    TokenSession.script = [([], "DONE"), ([], "DONE")]
    ctl = Controller(home, session_factory=TokenSession, llm=_plan_llm(plan), quiet=True)
    obj = ctl.run(ctl.create("x", budget=Budget(tokens=1500)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert obj.usage.tokens >= 1500
    assert "token budget" in obj.failure


# ---------------------------------------------------------------- executor pipeline

def test_executor_records_policy_decision_and_observation(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "write", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    scripted.script = [([("write_file", {"path": "a.txt", "content": "hi"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("write"))
    log = EventLog(ctl.store.events_path(obj.id))
    called = [e.data for e in log.read(kind=E.TOOL_CALLED)][0]
    assert called["cap"] == "fs.write" and called["action"]
    obs = [e.data for e in log.read(kind=E.OBSERVATION_CREATED)]
    assert obs and obs[0]["observation"].startswith("obs_")
    result = [e.data for e in log.read(kind=E.TOOL_RESULT)][0]
    assert result["status"] == "success" and result["policy"] in ("ALLOW", "ASK", "LIMITED")
    # every recorded observation carries the permission decision as evidence
    o = Observer(ctl.store.dir(obj.id)).load(obs[0]["observation"])
    assert any(ev.get("kind") == "permission" for ev in o.evidence)


def test_executor_blocks_sandbox_escapes_and_keeps_going(home, ws, scripted):
    """An agent-scoped sandbox denies a write outside its grants; the denial is observed
    as a blocked action and does not crash the objective."""
    plan = {"tasks": [{"id": "t1", "text": "try to escape", "depends_on": [], "checks": []}]}
    scripted.script = [([("write_file", {"path": "escape.txt", "content": "x"})], "BLOCKED: cannot write")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("escape")
    graph = ctl.plan(obj)
    t = list(graph.tasks.values())[0]
    t.agent = "reviewer"                     # reviewer has only fs.read
    ctl.store.save_tasks(obj.id, graph.to_list())
    obj2 = ctl.run(obj)
    # the write was denied at the sandbox/policy layer, so the file must not exist
    assert not (ws / "escape.txt").exists()
    assert obj2.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.COMPLETED, ObjectiveStatus.FAILED)


def test_executor_truncates_output_and_stops_at_tool_budget(home, ws, scripted):
    from rad.control.executor import Executor
    from rad.tools import ToolCtx, run_tool
    obj = Objective.new("x", budget=Budget(tool_calls=1))
    mgr = BudgetManager(obj.budget, obj.usage, objective_id=obj.id)
    ex = Executor(home, objective=obj, budgets=mgr, observer=Observer(home.root / "tmpobj"),
                  log=None, tool_runner=lambda n, a, c: "y" * 100000)
    ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
    helpers = home.root / "tmpobj"
    helpers.mkdir(parents=True, exist_ok=True)
    r1 = ex.run_action("run_shell", {"command": "echo hi"}, ctx)
    assert r1.status == "success"
    with pytest.raises(BudgetExceeded):
        ex.run_action("run_shell", {"command": "echo hi again"}, ctx)
    assert obj.usage.tool_calls == 1


# ---------------------------------------------------------------- checkpoints & crash recovery

def test_checkpoint_written_and_intact(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []}]}
    scripted.script = [([], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("x"))
    cm = CheckpointManager(home)
    cp = cm.read_cp(obj.id)
    assert cp["seq"] >= 2 and cp["status"] == ObjectiveStatus.COMPLETED
    assert cm.verify(obj.id)["intact"] is True
    # tamper with the task graph → digest mismatch
    ctl.store.save_tasks(obj.id, [{"id": "t1", "objective_id": obj.id, "text": "tampered"}])
    assert cm.verify(obj.id)["intact"] is False


def test_interrupted_objectives_are_detected_and_restored(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []},
                      {"id": "t2", "text": "b", "depends_on": ["t1"], "checks": []}]}
    scripted.script = [([], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("x"), max_tasks=1)
    # simulate a crash: no lock, but the objective says it is running
    (ctl.store.dir(obj.id) / "lock.json").unlink(missing_ok=True)
    cm = CheckpointManager(home)
    items = cm.interrupted()
    assert [i.objective_id for i in items] == [obj.id]
    # put a task in flight, then restore
    g = ctl.load_graph(obj)
    t2 = g.tasks[g.order[1]]
    t2.status = TaskStatus.RUNNING
    ctl.store.save_tasks(obj.id, g.to_list())
    obj2, g2 = cm.restore(obj.id)
    assert g2.tasks[g2.order[1]].status == TaskStatus.RETRYING
    assert any(h["note"] == "interrupted" for h in g2.tasks[g2.order[1]].history)
    assert obj2.status == ObjectiveStatus.RUNNING


def test_doctor_interrupted_surfaces_warning_not_crash(home, ws, scripted):
    """Regression: doctor read Interrupted objects as dicts (`i['id']`, `i['in_flight']`),
    crashing with TypeError whenever a crash-recovery objective existed. It must report
    the interrupted objective as a warning so `rad doctor --fix` can restore it."""
    from rad.doctor import Doctor
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []}]}
    scripted.script = [([], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("x")
    (ctl.store.dir(obj.id) / "lock.json").unlink(missing_ok=True)
    obj.set_status(ObjectiveStatus.RUNNING)
    ctl.store.save(obj)
    fs = {f.check: f for f in Doctor(home, fix=False, probe_network=False).run()}
    assert fs["recovery"].status == "warn"
    assert "interrupted" in fs["recovery"].message
    assert "resume" in fs["recovery"].message
    assert any(obj.id in d for d in fs["recovery"].detail)
    # fix mode restores it (idempotent) and reports ok, not a crash
    fs_fix = {f.check: f for f in Doctor(home, fix=True, probe_network=False).run()}
    assert fs_fix["recovery"].status == "ok"


def test_live_lock_prevents_false_crash_detection(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []}]}
    scripted.script = [([], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.create("x")
    ctl.plan(obj)
    cm = CheckpointManager(home)
    cm.acquire(obj.id)
    obj.set_status(ObjectiveStatus.RUNNING)
    ctl.store.save(obj)
    assert cm.interrupted() == [] or cm.locked_by_live_process(obj.id)
    cm.release(obj.id)
    cm.acquire(obj.id)
    assert cm.locked_by_live_process(obj.id)


# ---------------------------------------------------------------- lifecycle

def test_lifecycle_transitions_and_illegal_moves(home, ws):
    lc = Lifecycle(home)
    obj = lc.create("do a thing")
    assert obj.status == ObjectiveStatus.PENDING
    lc.planning(obj)
    lc.start(obj)
    lc.pause(obj)
    assert obj.status == ObjectiveStatus.PAUSED
    lc.resume(obj)
    lc.complete(obj, result="done")
    assert obj.status == ObjectiveStatus.COMPLETED and lc.history(obj)
    lc.retry(obj)
    assert obj.status == ObjectiveStatus.RUNNING
    lc.expire(obj, "deadline")
    assert obj.status == ObjectiveStatus.EXPIRED
    with pytest.raises(IllegalObjectiveTransition):
        lc._move(obj, ObjectiveStatus.PLANNING)      # expired → planning is illegal


def test_lifecycle_expire_due_and_delete(home, ws):
    lc = Lifecycle(home)
    o1 = lc.create("old", deadline=time.time() - 10)
    o2 = lc.create("fresh", deadline=time.time() + 1000)
    expired = lc.expire_due()
    assert [o.id for o in expired] == [o1.id]
    assert lc.delete(o2.id) and lc.store.load(o2.id) is None


def test_objective_retry_reopens_failed_tasks(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "x", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "x"}}]}]}
    scripted.script = [([], "DONE: lie")] * 6
    ctl = Controller(home, session_factory=scripted, llm=None, quiet=True)
    obj = ctl.create("x")
    ctl._llm = _plan_llm(plan)
    ctl.plan(obj)
    ctl._llm = None
    obj = ctl.run(obj)
    assert obj.status == ObjectiveStatus.NEEDS_USER
    g = ctl.load_graph(obj)
    assert all(t.status == TaskStatus.NEEDS_USER for t in g.tasks.values())
    scripted.script = [([("write_file", {"path": "x", "content": "1"})], "DONE")]
    obj2 = ctl.retry(obj.id)
    assert obj2.status == ObjectiveStatus.COMPLETED


# ---------------------------------------------------------------- task model round-trip

def test_task_roundtrip_keeps_branch_fields():
    t = Task.new("o", "x", priority="high", agent="coder", alternatives=["a"], on_failure=["b"],
                 active=False, optional=True)
    t.checks = [Check("file_exists", {"path": "x"})]
    d = json.loads(json.dumps(t.to_dict()))
    t2 = Task.from_dict(d)
    assert (t2.priority, t2.agent, t2.alternatives, t2.on_failure, t2.active) == \
           ("high", "coder", ["a"], ["b"], False)
    # old checkpoints without the new fields still load
    legacy = {"id": "t1", "objective_id": "o", "text": "old"}
    assert Task.from_dict(legacy).priority == "normal"


def test_observation_carries_error_and_environment(home, ws, scripted):
    """Every observation is reproducible later: it says what failed and where it ran."""
    plan = {"tasks": [{"id": "t1", "text": "read a missing file", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    scripted.script = [([("read_file", {"path": "missing.txt"}),
                         ("write_file", {"path": "a.txt", "content": "x"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("read then write"))
    observer = Observer(ctl.store.dir(obj.id))
    failed = [o for o in observer.for_task(sorted(ctl.load_graph(obj).tasks)[0])
              if o.status == "error"]
    assert failed, "the failed read must be observed as an error"
    o = failed[0]
    assert o.error.startswith("not found")
    assert o.env["workspace"] == str(ws) and o.env["python"] and o.env["platform"]


def test_artifacts_record_provenance_and_lineage(home, ws, scripted):
    """An artifact knows who made it, in which task/objective, and which version it replaced."""
    plan = {"tasks": [{"id": "t1", "text": "write twice", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    scripted.script = [([("write_file", {"path": "a.txt", "content": "one"}),
                         ("write_file", {"path": "a.txt", "content": "two"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("write twice"))
    reg = Observer(ctl.store.dir(obj.id)).artifacts()
    versions = sorted(reg.values(), key=lambda a: a["version"])
    assert versions[-1]["version"] == 2 and versions[-1]["parent"]
    p = versions[-1]["provenance"]
    assert p["created_by"] == "write_file" and p["objective_id"] == obj.id
    assert p["task_id"] and p["version"] == 2
