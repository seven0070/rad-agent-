"""Investigate-first: premature python test invoke → ENVIRONMENT (RW-079).

RW-079 live NIM (v0.4.4): ASCII-tree objective_checks were package-joined.
mkdir File-exists Class A path was **not live-hit** (mkdir succeeded). Residual:
first task machine `file_exists` on `text_analyzer/` **passed**, but the task
**FAILED on actions** because `python text_analyzer/test_analyzer.py` returned
CPython `can't open file … No such file` before the test file existed.
classify → ENVIRONMENT_FAILURE → Repair-prerequisite burned tools=12.

Question: is running a missing `.py` script a broken host environment (python
exists; file is agent-authored sequencing), and does the verifier still
hard-fail the task on that shell error when remaining directory/file checks
would pass (same hole as DONE/pip/mkdir noise)?

Does not claim live 11B text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree,
pip/DONE/mkdir fixes preserved. mkdir File-exists unit evidence (RW-078)
must not regress.
"""
from __future__ import annotations

from rad import __version__
from rad.control import TaskStatus
from rad.control import events as E
from rad.control.codingloop import (
    infer_package_dir,
    is_first_task_thrash_noise,
    is_missing_python_script,
    is_mkdir_already_exists,
    is_pip_requirements_file_missing,
)
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observation, Observer
from rad.control.planner import PLAN_PROMPT, Planner
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Check, Task
from rad.control.verifier import Verifier
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401
from tests.test_first_task_thrash import PIP_REQ_ERR, THREE_LINE_INPUT
from tests.test_mkdir_already_exists_actions import MKDIR_ERR

PREMATURE_TEST_ERR = (
    "python3: can't open file 'text_analyzer/test_analyzer.py': "
    "[Errno 2] No such file or directory\n[exit=2]"
)
PREMATURE_TEST_CMD = "python3 text_analyzer/test_analyzer.py"
NESTED_INPUT_ERR = (
    "Traceback (most recent call last):\n"
    "  File \"text_analyzer/analyzer.py\", line 5, in <module>\n"
    "    data = open('input.txt').read()\n"
    "FileNotFoundError: [Errno 2] No such file or directory: 'input.txt'\n"
    "[exit=1]"
)

RW079_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Create text_analyzer directory",
            "depends_on": [],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/"}},
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

def test_premature_test_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.5"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_forbids_running_tests_before_writing_them():
    assert "do NOT emit a standalone mkdir" in PLAN_PROMPT
    assert "Do not mkdir a path write_file already created" in PLAN_PROMPT
    assert "Do not run tests" in PLAN_PROMPT
    assert "before those test files exist" in PLAN_PROMPT


def test_ascii_tree_package_dir_still_infers_text_analyzer():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"


def test_missing_python_script_helper_is_tight():
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_missing_python_script(
        "python: can't open file '/tmp/ws/test_word_counter.py': "
        "[Errno 2] No such file or directory",
        "python test_word_counter.py")
    assert not is_missing_python_script(
        "sh: 1: python3: command not found", PREMATURE_TEST_CMD)
    assert not is_missing_python_script(
        "ModuleNotFoundError: No module named 'requests'\n[exit=1]",
        "python3 text_analyzer/analyzer.py")
    assert not is_missing_python_script(NESTED_INPUT_ERR, "python3 text_analyzer/analyzer.py")
    assert not is_missing_python_script(
        "cat: summary.json: No such file or directory", "cat summary.json")
    assert not is_missing_python_script(PIP_REQ_ERR, "pip install -r requirements.txt")
    assert not is_missing_python_script(MKDIR_ERR, "mkdir text_analyzer")
    assert is_first_task_thrash_noise("run_shell", PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_first_task_thrash_noise("run_shell", MKDIR_ERR, "mkdir text_analyzer")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")
    assert is_pip_requirements_file_missing(PIP_REQ_ERR, "pip install -r requirements.txt")


# ---------------------------------------------------------------- classify: premature test is not ENVIRONMENT

def test_premature_python_test_is_not_environment_repair():
    """RW-079 shape: python test_*.py can't-open-file must not Repair prerequisite."""
    t = Task.new("o", "Create text_analyzer directory")
    t.attempts = 1
    obs = [_ob(t, PREMATURE_TEST_ERR, args={"command": PREMATURE_TEST_CMD})]
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "actions", "detail": "8 actions, 1 errors"},
        {"ok": True, "kind": "file_exists", "detail": "text_analyzer exists=True"},
    ]}
    assert classify(t, obs, verification=ver) != FailureClass.ENVIRONMENT
    assert classify(t, obs, verification=ver) == FailureClass.TOOL
    d = RecoveryEngine().decide(t, obs, verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy != "repair" or d.data.get("coding_repair") is True
    assert "Repair prerequisite" not in d.reason
    assert "test" in d.hint.lower() or "python" in d.hint.lower()


def test_command_not_found_without_missing_script_stays_environment():
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
    obs = [_ob(t, MKDIR_ERR, args={"command": "mkdir text_analyzer"})]
    assert classify(t, obs) == FailureClass.TOOL
    assert classify(t, obs) != FailureClass.ENVIRONMENT


def test_nested_filenotfound_inside_running_script_is_not_missing_script():
    """analyzer.py opened; missing input.txt is a real action error, not noise."""
    t = Task.new("o", "Write analyzer.py")
    t.attempts = 1
    ob = _ob(t, NESTED_INPUT_ERR, args={"command": "python3 text_analyzer/analyzer.py"})
    assert not is_missing_python_script(NESTED_INPUT_ERR, "python3 text_analyzer/analyzer.py")
    # Nested missing input.txt still matches F-18 _ENV (no such file). Not this slice.
    assert classify(t, [ob]) == FailureClass.ENVIRONMENT


# ---------------------------------------------------------------- verifier: premature test is action noise when checks pass

def test_verifier_premature_test_does_not_fail_passed_dir_check(home, tmp_path):
    """RW-079 shape: directory check passed; premature test invoke must not FAILED."""
    ws_dir = tmp_path / "ws_rw079_v"
    ws_dir.mkdir()
    (ws_dir / "text_analyzer").mkdir()
    (ws_dir / "text_analyzer" / "input.txt").write_text(THREE_LINE_INPUT, encoding="utf-8")
    observer = Observer(home.root / "obs_rw079")
    t = Task.new("o", "Create text_analyzer directory")
    t.checks = [Check("file_exists", {"path": "text_analyzer"})]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "write_file",
        {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT},
        "wrote 76 chars → text_analyzer/input.txt", 1, ws_dir)
    observer.record(
        "o", t.id, "a2", "run_shell",
        {"command": PREMATURE_TEST_CMD},
        PREMATURE_TEST_ERR, 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: created directory")
    actions = next(r for r in result["results"] if r.get("kind") == "actions")
    checks = [r for r in result["results"] if r.get("level") == "check"]
    assert actions["ok"] is True
    assert all(r["ok"] for r in checks)
    assert result["status"] == "VERIFIED"


def test_verifier_real_shell_error_still_fails_actions(home, tmp_path):
    ws_dir = tmp_path / "ws_rw079_real"
    ws_dir.mkdir()
    (ws_dir / "text_analyzer").mkdir()
    observer = Observer(home.root / "obs_rw079_real")
    t = Task.new("o", "Create text_analyzer directory")
    t.checks = [Check("file_exists", {"path": "text_analyzer"})]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "run_shell",
        {"command": "python3 -c 'raise SystemExit(1)'"},
        "boom\n[exit=1]", 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE")
    actions = next(r for r in result["results"] if r.get("kind") == "actions")
    assert actions["ok"] is False
    assert result["status"] == "FAILED"


def test_verifier_premature_test_does_not_verified_failed_json(home, tmp_path):
    """False DONE 0: premature-test noise must not rubber-stamp a broken artifact."""
    ws_dir = tmp_path / "ws_rw079_json"
    ws_dir.mkdir()
    pkg = ws_dir / "text_analyzer"
    pkg.mkdir()
    (pkg / "summary.json").write_text("", encoding="utf-8")
    observer = Observer(home.root / "obs_rw079_json")
    t = Task.new("o", "Write summary.json")
    t.checks = [
        Check("file_exists", {"path": "text_analyzer"}),
        Check("json_valid", {"path": "text_analyzer/summary.json"}),
    ]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "run_shell",
        {"command": PREMATURE_TEST_CMD},
        PREMATURE_TEST_ERR, 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: summary")
    assert result["status"] == "FAILED"
    json_r = next(r for r in result["results"] if r.get("kind") == "json_valid")
    assert json_r["ok"] is False


def test_verifier_mkdir_file_exists_still_noise(home, tmp_path):
    """RW-078 must not regress: mkdir File-exists is still action noise."""
    ws_dir = tmp_path / "ws_rw079_mkdir"
    ws_dir.mkdir()
    (ws_dir / "text_analyzer").mkdir()
    observer = Observer(home.root / "obs_rw079_mkdir")
    t = Task.new("o", "Create text_analyzer directory")
    t.checks = [Check("file_exists", {"path": "text_analyzer"})]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "run_shell",
        {"command": "mkdir text_analyzer"},
        MKDIR_ERR, 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: created directory")
    actions = next(r for r in result["results"] if r.get("kind") == "actions")
    assert actions["ok"] is True
    assert result["status"] == "VERIFIED"


# ---------------------------------------------------------------- scripted: premature test must not starve later package task

def test_premature_test_does_not_starve_later_task(home, tmp_path):
    """RW-079 shape: mkdir succeeds; premature python test; later independent
    package file must still run. No ENVIRONMENT / Repair prerequisite.
    """
    ws_dir = tmp_path / "ws_rw079"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
          ("run_shell", {"command": PREMATURE_TEST_CMD})],
         "DONE: created directory"),
        ([("write_file", {"path": "text_analyzer/analyzer.py",
                          "content": "print('ok')\n"})],
         "DONE: wrote analyzer"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW079_PLAN)
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
        if t.text.startswith("Create text_analyzer directory"):
            t1 = t
        elif t.text.startswith("Write text_analyzer/analyzer.py"):
            t2 = t
    assert t1 is not None and t2 is not None
    assert t1.status == TaskStatus.COMPLETED
    assert t1.verification and t1.verification.get("status") == "VERIFIED"
    assert t2.status == TaskStatus.COMPLETED
    assert (ws_dir / "text_analyzer").is_dir()
    assert (ws_dir / "text_analyzer" / "input.txt").is_file()
    assert (ws_dir / "text_analyzer" / "analyzer.py").is_file()
    assert not (ws_dir / "input.txt").exists()
    assert not (ws_dir / "summary.json").exists()


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert any(c.kind == "json_valid" for c in res["objective_checks"])
