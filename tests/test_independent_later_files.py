"""v0.4.8 independent later package files (Gen3 theme 3 slice E2).

RW-085/086 live OpenRouter: PLAN source=fallback carved the goal into a
linear depends_on chain. Later package-file tasks stayed PENDING (0
attempts) while an early task burned leftover tools. E1 leftover reserve
is 0 when later tasks wait on the in-flight one (graph.ready() excludes
them). optional only unblocks after FAILED/BLOCKED/CANCELLED, not while
RETRYING.

E2 uses existing TaskGraph fields: independent fallback file-write
clauses get empty depends_on so Scheduler can run them without waiting
on a stuck early task. Consume/verify/read steps still chain. F-17
fallback tasks stay check-less. LLM explicit chains are not rewritten.

Does not claim live text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. Path-aligned, multifile, ASCII-tree, pip/DONE, mkdir,
premature-test, E1 TaskYield, xxd checksum Class A preserved.
"""
from __future__ import annotations

import pytest

from rad import __version__
from rad.control import ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.budgetplan import independent_unattempted_ready, leftover_tool_reserve
from rad.control.checkpoints import CheckpointManager
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_missing_optional_checksum_utility,
    is_missing_python_script,
    is_pip_requirements_file_missing,
)
from rad.control.controller import Controller
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.planner import PLAN_PROMPT, Planner, independent_file_clause
from rad.control.scheduler import Scheduler
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, scripted, ws  # noqa: F401
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_task_boundary_yield import RW083_CHAINED, THRASH_ECHO, _ctl, _tasks_by_prefix
from tests.test_xxd_environment import XXD_CMD, XXD_ERR

RW087_GOAL = (
    "Write first.txt and then burn leftover tools on stuck work. Write later.txt."
)


def _fallback_graph(goal: str):
    return Planner(None, "/tmp/ws")._fallback(Objective.new(goal))


def _fallback_by_prefix(graph, *prefixes):
    return _tasks_by_prefix(graph, *prefixes)


# ---------------------------------------------------------------- architecture freeze

def test_e2_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


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


def test_plan_prompt_asks_for_empty_depends_on_on_independent_files():
    assert "empty depends_on" in PLAN_PROMPT
    assert "Do not linearly chain later files" in PLAN_PROMPT


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW087_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- clause helper + fallback graph

def test_independent_file_clause_is_tight():
    assert independent_file_clause("Write later.txt")
    assert independent_file_clause("Write first.txt")
    assert independent_file_clause("Create the package")
    assert independent_file_clause("Write the tests")
    assert independent_file_clause("write a file")
    assert not independent_file_clause("read it back")
    assert not independent_file_clause("Run the tests")
    assert not independent_file_clause("Verify the result")
    assert not independent_file_clause("burn leftover tools on stuck work")
    assert not independent_file_clause("")


def test_fallback_later_file_has_empty_depends_on():
    """RW-087 shape: later file write is READY while an early consume waits."""
    g = _fallback_graph(RW087_GOAL)
    t1, t2, t3 = _fallback_by_prefix(g, "Write first.txt", "burn leftover", "Write later.txt")
    assert t1 is not None and t2 is not None and t3 is not None
    assert t1.depends_on == []
    assert t2.depends_on == [t1.id]
    assert t3.depends_on == []
    ready = [t.text for t in g.ready()]
    assert any(t.startswith("Write first.txt") for t in ready)
    assert any(t.startswith("Write later.txt") for t in ready)
    assert not any(t.startswith("burn leftover") for t in ready)


def test_fallback_consume_step_still_chains():
    """F-17 sequential consume stays chained — not every clause is unlinked."""
    g = _fallback_graph("write a file and then read it back")
    tasks = list(g.tasks.values())
    assert [t.text for t in tasks] == ["write a file", "read it back"]
    assert tasks[0].depends_on == []
    assert tasks[1].depends_on == [tasks[0].id]


def test_fallback_period_file_writes_are_all_ready():
    g = _fallback_graph("Write analyzer.py. Write input.txt. Write summary.json.")
    assert len(g.tasks) == 3
    assert all(t.depends_on == [] for t in g.tasks.values())
    assert {t.text for t in g.ready()} == {t.text for t in g.tasks.values()}


def test_leftover_reserve_counts_fallback_later_file():
    g = _fallback_graph(RW087_GOAL)
    t1, t2, t3 = _fallback_by_prefix(g, "Write first.txt", "burn leftover", "Write later.txt")
    t1.transition(TaskStatus.READY)
    t1.transition(TaskStatus.RUNNING)
    t1.transition(TaskStatus.OBSERVING)
    t1.transition(TaskStatus.VERIFYING)
    t1.transition(TaskStatus.COMPLETED)
    t2.transition(TaskStatus.READY)
    t2.transition(TaskStatus.RUNNING)
    later = independent_unattempted_ready(g, t2)
    assert [t.id for t in later] == [t3.id]
    assert leftover_tool_reserve(g, t2, 4) == 1
    s = Scheduler(parallel=1)
    assert [t.id for t in s.next_batch(g).tasks] == [t3.id]


def test_llm_explicit_chain_is_not_rewritten(home, tmp_path):
    """E2 does not rewrite an injected LLM depends_on chain (E1 contract stays)."""
    ws_dir = tmp_path / "ws_rw087_llm_chain"
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
    assert obj.usage.tool_calls == 4


# ---------------------------------------------------------------- scripted RW-087

def test_later_independent_fallback_file_gets_attempt_under_tight_tools(home, tmp_path):
    """RW-087: fallback later file still gets ≥1 attempt while early work is stuck."""
    ws_dir = tmp_path / "ws_rw087"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO] * 10, "DONE: thrashed"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = Controller(home, session_factory=ScriptedSession, llm=None, quiet=True)
    obj = ctl.run(ctl.create(
        RW087_GOAL,
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    g = ctl.load_graph(obj)
    t1, t2, t3 = _fallback_by_prefix(g, "Write first.txt", "burn leftover", "Write later.txt")
    assert t1 is not None and t2 is not None and t3 is not None
    assert t3.depends_on == []
    assert t3.attempts >= 1
    assert t3.status == TaskStatus.COMPLETED
    assert (ws_dir / "first.txt").is_file()
    assert (ws_dir / "later.txt").is_file()
    log = EventLog(ctl.store.events_path(obj.id))
    src = [e.data.get("source") for e in log.read(kind=E.PLAN_CREATED)]
    assert src == ["fallback"]
    started = [e.data.get("text") for e in log.read(kind=E.TASK_STARTED)]
    assert any(t and t.startswith("Write later.txt") for t in started)
    yielded = [e for e in log.read(kind=E.TASK_STATUS) if e.data.get("yielded")]
    assert yielded
    cp = CheckpointManager(home).read_cp(obj.id)
    assert cp.get("digest")
    assert CheckpointManager(home).verify(obj.id)["intact"] is True
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.NEEDS_USER, ObjectiveStatus.FAILED)
    assert obj.usage.tool_calls <= 4


def test_e2_does_not_verified_unmet_checks(home, tmp_path):
    """False DONE 0: independent later file dispatch must not rubber-stamp."""
    ws_dir = tmp_path / "ws_rw087_false"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        ([("write_file", {"path": "first.txt", "content": "one\n"})], "DONE: first"),
        ([THRASH_ECHO] * 10, "DONE: thrashed"),
        ([("write_file", {"path": "later.txt", "content": "later\n"})], "DONE: later"),
    ]
    ScriptedSession.prompts = []
    ctl = Controller(home, session_factory=ScriptedSession, llm=None, quiet=True)
    obj = ctl.run(ctl.create(
        RW087_GOAL + " Also write missing.json as valid JSON.",
        budget=Budget(tool_calls=4, retries=6),
        auto=True,
    ))
    assert (obj.verification or {}).get("objective", {}).get("status") != "VERIFIED"
    assert not (ws_dir / "missing.json").exists()
