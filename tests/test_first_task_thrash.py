"""v0.4.3 first-task thrash (Gen3 theme 3 slice B).

RW-075 live NIM (v0.4.2): ASCII-tree objective_checks were package-joined
(theme-1 follow-up live-confirmed). Class B residual was incomplete package
(missing summary.json, weak tests) plus first-task thrash: 4× pip install -r
missing requirements.txt classified ENVIRONMENT → Repair prerequisite, then
unknown tool `DONE:` burned the remaining 12-tool budget before later package
tasks ran.

Class A confirmed:
  * pip -r when the requirements file is missing is not ENVIRONMENT
    (no Repair-prerequisite insert for stdlib-only coding)
  * invented tool DONE / DONE: … must not fail a task whose explicit machine
    checks already passed (later independent tasks can still run)

Does not claim live 11B text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree preserved.
"""
from __future__ import annotations

from rad import __version__
from rad.control import ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_pip_requirements_file_missing,
)
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observation
from rad.control.planner import PLAN_PROMPT, Planner
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Task
from rad.home import DEFAULTS
from rad.tools import run_tool
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401
from tests.test_tools import _ctx

PIP_REQ_ERR = (
    "ERROR: Could not open requirements file: [Errno 2] No such file or directory: "
    "'text_analyzer/requirements.txt'\n[exit=1]"
)

THREE_LINE_INPUT = (
    "RAD is a personal agent.\n"
    "RAD executes useful work.\n"
    "RAD verifies its results."
)

RW075_PLAN = {
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
            "depends_on": ["t1"],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}},
            ],
        },
    ],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}},
        {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
    ],
}


def _ob(task: Task, out: str, status: str = "error", tool: str = "run_shell",
        args: dict | None = None) -> Observation:
    return Observation.new(objective_id="o", task_id=task.id, action_id="a", tool=tool,
                           args=args or {}, status=status, output=out, duration_ms=1)


# ---------------------------------------------------------------- architecture freeze

def test_first_task_thrash_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.3"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_forbids_pip_requirements_and_done_as_tool():
    assert "DONE is not a tool" in PLAN_PROMPT
    assert "must not pip install" in PLAN_PROMPT
    assert "do NOT emit a standalone mkdir" in PLAN_PROMPT


def test_ascii_tree_package_dir_still_infers_text_analyzer():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"


def test_done_protocol_tool_names():
    assert is_done_protocol_tool("DONE")
    assert is_done_protocol_tool("DONE: wrote input")
    assert is_done_protocol_tool("done: all done")
    assert not is_done_protocol_tool("write_file")
    assert not is_done_protocol_tool("run_shell")


def test_pip_requirements_missing_helper_ignores_command_not_found():
    assert is_pip_requirements_file_missing(PIP_REQ_ERR, "pip install -r text_analyzer/requirements.txt")
    assert not is_pip_requirements_file_missing(
        "sh: 1: pip: command not found", "pip install -r requirements.txt")
    assert not is_pip_requirements_file_missing(
        "ModuleNotFoundError: No module named 'requests'", "python3 analyzer.py")


# ---------------------------------------------------------------- classify: pip-missing-requirements is not ENVIRONMENT

def test_pip_missing_requirements_is_not_environment_repair():
    """RW-075 shape: pip -r file-not-found must not insert Repair prerequisite."""
    t = Task.new("o", "Write text_analyzer/input.txt with exact 3 lines")
    t.attempts = 1
    obs = [
        _ob(t, PIP_REQ_ERR, args={"command": "pip install -r text_analyzer/requirements.txt"}),
        _ob(t, PIP_REQ_ERR, args={"command": "pip install -r requirements.txt"}),
    ]
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "actions", "detail": "4 actions, 4 errors"},
        {"ok": True, "kind": "file_line_count", "detail": "text_analyzer/input.txt lines=3"},
    ]}
    assert classify(t, obs, verification=ver) != FailureClass.ENVIRONMENT
    d = RecoveryEngine().decide(t, obs, verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy != "repair" or d.data.get("coding_repair") is True
    assert "Repair prerequisite" not in d.reason
    assert "requirements.txt" in d.hint or "pip install" in d.hint


def test_command_not_found_without_pip_req_stays_environment():
    t = Task.new("o", "run build")
    t.attempts = 1
    ob = _ob(t, "sh: 1: mkreport_xyz: command not found")
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "out.txt exists=False"},
    ]}
    assert classify(t, [ob], verification=ver) == FailureClass.ENVIRONMENT
    d = RecoveryEngine().decide(t, [ob], verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class == FailureClass.ENVIRONMENT
    assert d.strategy == "repair"


def test_module_not_found_stays_environment():
    t = Task.new("o", "run analyzer")
    t.attempts = 1
    ob = _ob(t, "ModuleNotFoundError: No module named 'requests'\n[exit=1]")
    assert classify(t, [ob]) == FailureClass.ENVIRONMENT


def test_cat_no_such_file_stays_environment_f18():
    t = Task.new("o", "write summary")
    t.attempts = 1
    ob = _ob(t, "cat: summary.json: No such file or directory")
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "summary.json exists=False"},
    ]}
    assert classify(t, [ob], verification=ver) == FailureClass.ENVIRONMENT


def test_mkdir_already_exists_still_not_environment():
    t = Task.new("o", "Create text_analyzer directory")
    t.attempts = 1
    obs = [
        _ob(t, "mkdir: cannot create directory 'text_analyzer': File exists"),
        _ob(t, "cat: summary.json: No such file or directory"),
    ]
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "actions", "detail": "2 actions, 2 errors"},
        {"ok": False, "kind": "json_valid",
         "detail": "text_analyzer/summary.json invalid JSON: Expecting value"},
    ]}
    assert classify(t, obs, verification=ver) != FailureClass.ENVIRONMENT


def test_unknown_done_tool_retry_hint_does_not_switch_to_done():
    t = Task.new("o", "Write input.txt")
    t.attempts = 2
    obs = [
        _ob(t, "unknown tool: DONE: wrote input", tool="DONE: wrote input"),
        _ob(t, "unknown tool: DONE: wrote input", tool="DONE: wrote input"),
    ]
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "text_analyzer/input.txt exists=False"},
    ]}
    d = RecoveryEngine().decide(t, obs, verification=ver, repairs_so_far=0, retries_left=3)
    assert d.strategy == "retry_with_hint"
    assert d.failure_class == FailureClass.TOOL
    assert "DONE is not a tool" in d.hint


# ---------------------------------------------------------------- scripted: checks pass + pip/DONE noise → later task still runs

def test_pip_and_done_noise_does_not_starve_later_task(home, tmp_path):
    """RW-075 shape: first-task file checks pass; pip -r + fake DONE must not
    insert Repair prerequisite or block the next independent package file.
    """
    ws_dir = tmp_path / "ws_rw075"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
          ("run_shell", {"command": "pip install -r text_analyzer/requirements.txt"}),
          ("DONE: wrote input", {})],
         "DONE: wrote input.txt"),
        ([("write_file", {"path": "text_analyzer/analyzer.py",
                          "content": "print('ok')\n"})],
         "DONE: wrote analyzer"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW075_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=12, retries=6),
        auto=True,
    ))
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert not any(d.get("failure_class") == FailureClass.ENVIRONMENT for d in decisions)
    g = ctl.load_graph(obj)
    assert not any(t.text.startswith("Repair prerequisite") for t in g.tasks.values())
    t1, t2 = None, None
    for t in g.tasks.values():
        if t.text.startswith("Write text_analyzer/input.txt"):
            t1 = t
        elif t.text.startswith("Write text_analyzer/analyzer.py"):
            t2 = t
    assert t1 is not None and t2 is not None
    assert t1.status == TaskStatus.COMPLETED
    assert t1.verification and t1.verification.get("status") == "VERIFIED"
    assert t2.status == TaskStatus.COMPLETED
    assert (ws_dir / "text_analyzer" / "input.txt").is_file()
    assert (ws_dir / "text_analyzer" / "analyzer.py").is_file()
    assert not (ws_dir / "input.txt").exists()
    assert not (ws_dir / "summary.json").exists()


def test_done_as_tool_without_artifact_is_not_verified(home, tmp_path):
    """False DONE 0: inventing a DONE tool does not VERIFIED missing files."""
    ws_dir = tmp_path / "ws_false_done"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("DONE: wrote input", {})], "DONE: wrote input.txt"),
        ([("DONE: wrote analyzer", {})], "DONE: wrote analyzer"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW075_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=12, retries=6),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)
    assert not (ws_dir / "text_analyzer" / "input.txt").exists()


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert any(c.kind == "json_valid" for c in res["objective_checks"])


def test_run_tool_done_protocol_is_unknown_not_success(home):
    out = run_tool("DONE: wrote input", {}, _ctx(home, auto=True))
    assert out.startswith("unknown tool:")
    assert "DONE is not a tool" in out
