"""v0.4.9 budget-aware retry stop (Gen3 theme 3 slice E3).

E1 (v0.4.6) yields mid-think when remaining tools ≤ leftover reserve
(1 per later independent unattempted READY). After a failed first attempt
with rem = reserve + 1, recovery still started another retry of the stuck
task; that retry spent the spare tool E1 was holding for later READY work.

E3 strengthens the same leftover boundary at retry/repair time: stop when
remaining < leftover_tool_reserve + TOOLS_PER_TASK, and refuse to start a
RETRYING dispatch that would burn that headroom. Later independent READY
work still gets ≥1 attempt. Executor reserve (E1) is unchanged.

Does not claim live text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. Path-aligned, multifile, ASCII-tree, pip/DONE, mkdir,
premature-test, E1 TaskYield, E2 independent later files, xxd checksum
Class A preserved.
"""
from __future__ import annotations

from rad import __version__
from rad.control import ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.budgetplan import (
    TOOLS_PER_TASK,
    leftover_tool_reserve,
    should_yield_for_leftover,
)
from rad.control.checkpoints import CheckpointManager
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_missing_optional_checksum_utility,
    is_missing_python_script,
    is_pip_requirements_file_missing,
)
from rad.control.events import EventLog
from rad.control.graph import TaskGraph
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.control.tasks import Task
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl  # noqa: F401
from tests.test_independent_later_files import RW087_GOAL
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_task_boundary_yield import THRASH_ECHO, _tasks_by_prefix
from tests.test_xxd_environment import XXD_CMD, XXD_ERR

RW088_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write first.txt",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "first.txt"}}],
        },
        {
            "id": "t2",
            "text": "Thrash stuck work",
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

RW088_SOLO = {
    "tasks": [
        {
            "id": "t1",
            "text": "Thrash stuck work",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "stuck.txt"}}],
        },
    ],
    "objective_checks": [{"kind": "file_exists", "args": {"path": "stuck.txt"}}],
}

RW088_REPAIR = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write first.txt",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "first.txt"}}],
        },
        {
            "id": "t2",
            "text": "Run missing host command",
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

ENV_MISS = ("run_shell", {"command": "definitely_not_a_command_xyz_e3 > stuck.txt"})


# ---------------------------------------------------------------- architecture freeze

def test_e3_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"
    assert TOOLS_PER_TASK == 2


def test_prior_class_a_helpers_still_hold():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"
    assert is_done_protocol_tool("DONE: wrote input")
    assert is_pip_requirements_file_missing(
        "ERROR: Could not open requirements file: [Errno 2] No such file or directory: "
        "'requirements.txt'",
        "pip install -r requirements.txt")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_missing_optional_checksum_utility(XXD_ERR, XXD_CMD)


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW087_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- leftover retry-stop helper

def _ready_pair():
    g = TaskGraph()
    t2 = Task.new("o", "thrash")
    t3 = Task.new("o", "later")
    g.add(t2)
    g.add(t3)
    t2.transition(TaskStatus.READY)
    t2.transition(TaskStatus.RUNNING)
    t2.transition(TaskStatus.OBSERVING)
    t2.transition(TaskStatus.VERIFYING)
    t2.transition(TaskStatus.FAILED)
    return g, t2, t3


def test_should_yield_for_leftover_stops_retry_below_tools_per_task():
    g, t2, t3 = _ready_pair()
    assert leftover_tool_reserve(g, t2, 2) == 1
    assert should_yield_for_leftover(g, t2, 1) is True
    assert should_yield_for_leftover(g, t2, 2) is True
    assert should_yield_for_leftover(g, t2, 3) is False
    assert should_yield_for_leftover(g, t2, None) is False
    t3.attempts = 1
    assert leftover_tool_reserve(g, t2, 2) == 0
    assert should_yield_for_leftover(g, t2, 2) is False


def test_should_yield_for_leftover_zero_without_later_ready():
    g = TaskGraph()
    t2 = Task.new("o", "solo")
    g.add(t2)
    t2.transition(TaskStatus.READY)
    t2.transition(TaskStatus.RUNNING)
    assert leftover_tool_reserve(g, t2, 2) == 0
    assert should_yield_for_leftover(g, t2, 2) is False


# ---------------------------------------------------------------- scripted RW-088

def test_retry_stops_before_burning_leftover_reserve(home, tmp_path):
    """RW-088: after a failed first attempt, do not retry into leftover reserve."""
    ws_dir = tmp_path / "ws_rw088"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO], "DONE: stuck"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW088_PLAN)
    obj = ctl.run(ctl.create(
        "Write first.txt then later.txt; stop retrying stuck work under a tight tool cap.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    g = ctl.load_graph(obj)
    t1, t2, t3 = _tasks_by_prefix(g, "Write first.txt", "Thrash stuck work", "Write later.txt")
    assert t1 is not None and t2 is not None and t3 is not None
    assert t1.status == TaskStatus.COMPLETED
    assert t1.verification and t1.verification.get("status") == "VERIFIED"
    assert t2.attempts >= 1
    assert t2.status != TaskStatus.COMPLETED
    assert t3.attempts >= 1
    assert t3.status == TaskStatus.COMPLETED
    assert t3.verification and t3.verification.get("status") == "VERIFIED"
    assert (ws_dir / "first.txt").is_file()
    assert (ws_dir / "later.txt").is_file()
    assert not (ws_dir / "stuck.txt").exists()
    log = EventLog(ctl.store.events_path(obj.id))
    started = [e.data.get("text") for e in log.read(kind=E.TASK_STARTED)]
    assert any(t and t.startswith("Write later.txt") for t in started)
    later_i = next(i for i, t in enumerate(started) if t and t.startswith("Write later.txt"))
    thrash_before = [t for t in started[:later_i] if t and t.startswith("Thrash stuck work")]
    assert thrash_before == ["Thrash stuck work"]
    yielded = [e for e in log.read(kind=E.TASK_STATUS) if e.data.get("yielded")]
    assert yielded
    recover_before_later = []
    later_started = False
    for e in log.read():
        if e.kind == E.TASK_STARTED and str(e.data.get("text") or "").startswith("Write later.txt"):
            later_started = True
        if e.kind == E.RECOVERY_DECISION and not later_started:
            recover_before_later.append(e.data.get("strategy"))
    assert later_started
    assert not any(s in ("retry", "retry_with_hint", "repair") for s in recover_before_later)
    cp = CheckpointManager(home).read_cp(obj.id)
    assert cp.get("digest")
    assert CheckpointManager(home).verify(obj.id)["intact"] is True
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED)
    assert obj.usage.tool_calls <= 4


def test_repair_stops_before_burning_leftover_reserve(home, tmp_path):
    """RW-088 repair: ENVIRONMENT fail must yield, not insert a repair that burns leftover."""
    ws_dir = tmp_path / "ws_rw088_repair"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([ENV_MISS], "DONE: env"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW088_REPAIR)
    obj = ctl.run(ctl.create(
        "Write first.txt then later.txt; do not repair-thrash leftover tools.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    g = ctl.load_graph(obj)
    t1, t2, t3 = _tasks_by_prefix(g, "Write first.txt", "Run missing host command", "Write later.txt")
    assert t1.status == TaskStatus.COMPLETED
    assert t2.attempts >= 1
    assert t3.attempts >= 1
    assert (ws_dir / "later.txt").is_file()
    assert not any(t.text.startswith("Repair") for t in g.tasks.values())
    log = EventLog(ctl.store.events_path(obj.id))
    started = [e.data.get("text") for e in log.read(kind=E.TASK_STARTED)]
    later_i = next(i for i, t in enumerate(started) if t and t.startswith("Write later.txt"))
    env_before = [t for t in started[:later_i] if t and t.startswith("Run missing host command")]
    assert env_before == ["Run missing host command"]
    recover_before_later = []
    later_started = False
    for e in log.read():
        if e.kind == E.TASK_STARTED and str(e.data.get("text") or "").startswith("Write later.txt"):
            later_started = True
        if e.kind == E.RECOVERY_DECISION and not later_started:
            recover_before_later.append(e.data.get("strategy"))
    assert later_started
    assert "repair" not in recover_before_later
    assert [e for e in log.read(kind=E.TASK_STATUS) if e.data.get("yielded")]
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.usage.tool_calls <= 4


def test_e3_does_not_verified_unmet_checks(home, tmp_path):
    """False DONE 0: retry-stop dispatch must not rubber-stamp missing artifacts."""
    ws_dir = tmp_path / "ws_rw088_false"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO], "DONE: stuck.txt"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW088_PLAN)
    obj = ctl.run(ctl.create(
        "Write first.txt then later.txt under a tight tool cap.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert not (tmp_path / "ws_rw088_false" / "stuck.txt").exists()
    assert not (tmp_path / "ws_rw088_false" / "missing.json").exists()


def test_solo_task_still_retries_when_no_later_ready(home, tmp_path):
    """E3 must not invent leftover work — a solo failure still retries."""
    ws_dir = tmp_path / "ws_rw088_solo"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([THRASH_ECHO], "DONE: miss"),
        ([("write_file", {"path": "stuck.txt", "content": "ok\n"})], "DONE: fixed"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW088_SOLO)
    obj = ctl.run(ctl.create("solo retry", budget=Budget(tool_calls=4, retries=4), auto=True))
    g = ctl.load_graph(obj)
    t2 = _tasks_by_prefix(g, "Thrash stuck work")[0]
    assert t2.attempts == 2
    assert t2.status == TaskStatus.COMPLETED
    assert (ws_dir / "stuck.txt").is_file()
    assert obj.status == ObjectiveStatus.COMPLETED


def test_retry_still_runs_when_leftover_headroom_is_safe(home, tmp_path):
    """A full TOOLS_PER_TASK retry is allowed when remaining exceeds reserve + 2."""
    ws_dir = tmp_path / "ws_rw088_room"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO], "DONE: miss"),
        ([("write_file", {"path": "stuck.txt", "content": "ok\n"})], "DONE: fixed"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW088_PLAN)
    obj = ctl.run(ctl.create(
        "retry is allowed when leftover headroom is safe",
        budget=Budget(tool_calls=12, retries=6),
        auto=True,
    ))
    g = ctl.load_graph(obj)
    t1, t2, t3 = _tasks_by_prefix(g, "Write first.txt", "Thrash stuck work", "Write later.txt")
    assert t1.status == TaskStatus.COMPLETED
    assert t2.attempts == 2
    assert t2.status == TaskStatus.COMPLETED
    assert t3.status == TaskStatus.COMPLETED
    assert (ws_dir / "stuck.txt").is_file()
    assert (ws_dir / "later.txt").is_file()
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED, ObjectiveStatus.COMPLETED)
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
