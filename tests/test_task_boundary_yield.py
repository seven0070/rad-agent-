"""v0.4.6 task-boundary yield / leftover-budget dispatch (Gen3 theme 3 slice E1).

RW-081 live NIM (v0.4.5): first task VERIFIED; second task burned remaining
tools on pip/echo; later independent package file stayed PENDING; needs_user
@ 12/12. Crash-resume already shipped. E1 yields a stuck in-flight task at a
task boundary (checkpoint + Scheduler) so leftover tools reach later
independent READY work under the same --max-tools cap.

Does not claim live 11B text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree,
pip/DONE, mkdir File-exists, premature-test fixes preserved. Thrash Class A
chase stays paused (RW-081 pip/root NOT CONFIRMED). No new checkpoint format.
"""
from __future__ import annotations

import pytest

from rad import __version__
from rad.control import ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.budgetplan import (
    independent_unattempted_ready,
    leftover_tool_reserve,
    remaining_tool_calls,
    task_is_yielded,
)
from rad.control.budgets import BudgetExceeded, BudgetManager, TaskYield
from rad.control.checkpoints import CheckpointManager
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_missing_python_script,
    is_pip_requirements_file_missing,
)
from rad.control.events import EventLog
from rad.control.executor import Executor
from rad.control.graph import TaskGraph
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observer
from rad.control.planner import Planner
from rad.control.scheduler import Scheduler
from rad.control.tasks import Task
from rad.home import DEFAULTS
from rad.tools import ToolCtx
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl, scripted, ws  # noqa: F401
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR

THRASH_ECHO = ("run_shell", {"command": "echo pip-install-placeholder"})

RW083_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write first.txt",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "first.txt"}}],
        },
        {
            "id": "t2",
            "text": "Thrash pip/echo",
            "depends_on": ["t1"],
            "checks": [{"kind": "file_exists", "args": {"path": "stuck.txt"}}],
        },
        {
            "id": "t3",
            "text": "Write later.txt",
            "depends_on": ["t1"],
            "checks": [{"kind": "file_exists", "args": {"path": "later.txt"}}],
        },
    ],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "later.txt"}},
        {"kind": "json_valid", "args": {"path": "missing.json"}},
    ],
}

RW083_CHAINED = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write first.txt",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "first.txt"}}],
        },
        {
            "id": "t2",
            "text": "Thrash pip/echo",
            "depends_on": ["t1"],
            "checks": [{"kind": "file_exists", "args": {"path": "stuck.txt"}}],
        },
        {
            "id": "t3",
            "text": "Write later.txt",
            "depends_on": ["t2"],
            "checks": [{"kind": "file_exists", "args": {"path": "later.txt"}}],
        },
    ],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "later.txt"}},
    ],
}


def _tasks_by_prefix(graph, *prefixes):
    found = []
    for prefix in prefixes:
        hit = None
        for t in graph.tasks.values():
            if t.text.startswith(prefix):
                hit = t
                break
        found.append(hit)
    return found


# ---------------------------------------------------------------- architecture freeze

def test_e1_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_prior_thrash_class_a_helpers_still_hold():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"
    assert is_done_protocol_tool("DONE: wrote input")
    assert is_pip_requirements_file_missing(
        "ERROR: Could not open requirements file: [Errno 2] No such file or directory: "
        "'requirements.txt'",
        "pip install -r requirements.txt")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(
        Objective.new("Write first.txt and then write later.txt."))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- leftover reserve helpers

def test_leftover_reserve_counts_independent_unattempted_only():
    g = TaskGraph()
    t1 = Task.new("o", "first")
    t2 = Task.new("o", "thrash", depends_on=[t1.id])
    t3 = Task.new("o", "later", depends_on=[t1.id])
    for t in (t1, t2, t3):
        g.add(t)
    t1.transition(TaskStatus.READY)
    t1.transition(TaskStatus.RUNNING)
    t1.transition(TaskStatus.OBSERVING)
    t1.transition(TaskStatus.VERIFYING)
    t1.transition(TaskStatus.COMPLETED)
    t2.transition(TaskStatus.READY)
    t2.transition(TaskStatus.RUNNING)
    later = independent_unattempted_ready(g, t2)
    assert [t.id for t in later] == [t3.id]
    assert leftover_tool_reserve(g, t2, 3) == 1
    assert leftover_tool_reserve(g, t2, None) == 0
    assert leftover_tool_reserve(g, t2, 0) == 0
    t3.attempts = 1
    assert leftover_tool_reserve(g, t2, 3) == 0


def test_leftover_reserve_zero_when_later_depends_on_current():
    g = TaskGraph()
    t1 = Task.new("o", "first")
    t2 = Task.new("o", "thrash", depends_on=[t1.id])
    t3 = Task.new("o", "later", depends_on=[t2.id])
    for t in (t1, t2, t3):
        g.add(t)
    t1.transition(TaskStatus.READY)
    t1.transition(TaskStatus.RUNNING)
    t1.transition(TaskStatus.OBSERVING)
    t1.transition(TaskStatus.VERIFYING)
    t1.transition(TaskStatus.COMPLETED)
    t2.transition(TaskStatus.READY)
    t2.transition(TaskStatus.RUNNING)
    assert independent_unattempted_ready(g, t2) == []
    assert leftover_tool_reserve(g, t2, 4) == 0


def test_scheduler_skips_yielded_when_other_ready_exists():
    g = TaskGraph()
    t2 = Task.new("o", "thrash")
    t3 = Task.new("o", "later")
    g.add(t2)
    g.add(t3)
    t2.verification = {"yielded": True}
    t2.transition(TaskStatus.READY)
    t2.transition(TaskStatus.RUNNING)
    t2.transition(TaskStatus.OBSERVING)
    t2.transition(TaskStatus.VERIFYING)
    t2.transition(TaskStatus.FAILED)
    t2.transition(TaskStatus.RETRYING)
    assert task_is_yielded(t2)
    s = Scheduler(parallel=1)
    batch = s.next_batch(g)
    assert [t.id for t in batch.tasks] == [t3.id]
    t3.transition(TaskStatus.READY)
    t3.transition(TaskStatus.RUNNING)
    t3.transition(TaskStatus.OBSERVING)
    t3.transition(TaskStatus.VERIFYING)
    t3.transition(TaskStatus.COMPLETED)
    batch2 = s.next_batch(g)
    assert [t.id for t in batch2.tasks] == [t2.id]
    assert not task_is_yielded(t2)


def test_executor_yields_before_consuming_reserved_tool(home, tmp_path):
    ws_dir = tmp_path / "ws_e1_ex"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    obj = Objective.new("x", budget=Budget(tool_calls=2))
    mgr = BudgetManager(obj.budget, obj.usage, objective_id=obj.id)
    ex = Executor(home, objective=obj, budgets=mgr, observer=Observer(home.root / "obs_e1"),
                  log=None, tool_runner=lambda n, a, c: "ok")
    ex.reserve_tools = 1
    ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True)
    r1 = ex.run_action("run_shell", {"command": "echo a"}, ctx)
    assert r1.status == "success"
    assert obj.usage.tool_calls == 1
    with pytest.raises(TaskYield):
        ex.run_action("run_shell", {"command": "echo b"}, ctx)
    assert obj.usage.tool_calls == 1
    with pytest.raises(BudgetExceeded):
        ex.reserve_tools = 0
        obj.usage.tool_calls = 2
        ex.run_action("run_shell", {"command": "echo c"}, ctx)


# ---------------------------------------------------------------- scripted RW-083

def test_later_independent_ready_gets_attempt_under_same_tool_cap(home, tmp_path):
    """RW-083: t1 VERIFIED; t2 would exhaust remaining tools; t3 still gets ≥1 attempt."""
    ws_dir = tmp_path / "ws_rw083"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO] * 10, "DONE: thrashed"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW083_PLAN)
    obj = ctl.run(ctl.create(
        "Write first.txt then later.txt under a tight tool cap.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    g = ctl.load_graph(obj)
    t1, t2, t3 = _tasks_by_prefix(g, "Write first.txt", "Thrash pip/echo", "Write later.txt")
    assert t1 is not None and t2 is not None and t3 is not None
    assert t1.status == TaskStatus.COMPLETED
    assert t1.verification and t1.verification.get("status") == "VERIFIED"
    assert t3.status == TaskStatus.COMPLETED
    assert t3.verification and t3.verification.get("status") == "VERIFIED"
    assert t2.status != TaskStatus.COMPLETED
    assert t2.attempts >= 1
    assert (ws_dir / "first.txt").is_file()
    assert (ws_dir / "later.txt").is_file()
    assert not (ws_dir / "stuck.txt").exists()
    log = EventLog(ctl.store.events_path(obj.id))
    started = [e.data.get("text") for e in log.read(kind=E.TASK_STARTED)]
    assert any(t and t.startswith("Write later.txt") for t in started)
    yielded = [e for e in log.read(kind=E.TASK_STATUS) if e.data.get("yielded")]
    assert yielded
    cp_notes = [e.data.get("note", "") for e in log.read(kind=E.CHECKPOINT)]
    assert any("yield leftover-budget" in str(n) for n in cp_notes)
    cp = CheckpointManager(home).read_cp(obj.id)
    assert cp.get("digest")
    assert CheckpointManager(home).verify(obj.id)["intact"] is True
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED)
    assert obj.usage.tool_calls <= 4
    assert remaining_tool_calls(obj) == 0 or obj.usage.tool_calls == 4


def test_yield_does_not_verified_unmet_checks(home, tmp_path):
    """False DONE 0: leftover dispatch must not rubber-stamp missing artifacts."""
    ws_dir = tmp_path / "ws_rw083_false"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO] * 10, "DONE: stuck.txt"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW083_PLAN)
    obj = ctl.run(ctl.create(
        "Write first.txt then later.txt under a tight tool cap.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert not (ws_dir / "stuck.txt").exists()
    assert not (ws_dir / "missing.json").exists()


def test_chained_later_task_is_not_ready_so_e1_does_not_invent_e2(home, tmp_path):
    """E1 does not rewrite depends_on: a later file that waits on the stuck task stays PENDING."""
    ws_dir = tmp_path / "ws_rw083_chain"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO] * 10, "DONE: thrashed"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW083_CHAINED)
    obj = ctl.run(ctl.create(
        "Write first.txt then later.txt chained.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    g = ctl.load_graph(obj)
    t1, t2, t3 = _tasks_by_prefix(g, "Write first.txt", "Thrash pip/echo", "Write later.txt")
    assert t1.status == TaskStatus.COMPLETED
    assert t3.status == TaskStatus.PENDING
    assert not (ws_dir / "later.txt").exists()
    log = EventLog(ctl.store.events_path(obj.id))
    started = [e.data.get("text") for e in log.read(kind=E.TASK_STARTED)]
    assert not any(t and t.startswith("Write later.txt") for t in started)
    assert obj.usage.tool_calls == 4


def test_no_later_ready_still_allows_current_to_use_remaining_tools(home, tmp_path):
    """Single-task thrash still hits the cap (E1 must not invent leftover work)."""
    ws_dir = tmp_path / "ws_rw083_solo"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    plan = {"tasks": [
        {"id": "t1", "text": "Thrash pip/echo", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "stuck.txt"}}]},
    ], "objective_checks": [{"kind": "file_exists", "args": {"path": "stuck.txt"}}]}
    ScriptedSession.script = [([THRASH_ECHO] * 10, "DONE: thrashed")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, plan)
    obj = ctl.run(ctl.create("solo thrash", budget=Budget(tool_calls=3, retries=4), auto=True))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert obj.usage.tool_calls == 3
    assert EventLog(ctl.store.events_path(obj.id)).count(E.BUDGET_EXCEEDED) >= 1
    assert not (ws_dir / "stuck.txt").exists()
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
