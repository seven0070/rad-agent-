"""Investigate-first: missing optional xxd → ENVIRONMENT (RW-085).

RW-085 live OpenRouter free (v0.4.6): ASCII-tree objective_checks were
package-joined. Class C vs RW-084 (NIM 403) **cleared**. Residual: first
task machine `file_nonempty` on `text_analyzer/input.txt` **passed**, but
the task **FAILED on actions** because `xxd` returned exit 127 / not found.
classify → ENVIRONMENT_FAILURE → Repair-prerequisite burned leftover tools.
E1 leftover-budget yield **not live** (fallback chain; 0 TaskYield).

Question: is a missing optional hex/checksum binary (`xxd`) a broken RAD
host environment (python exists; the model chose checksum theater), and
does the verifier still hard-fail the task on that action error when
remaining file checks would pass (same hole as DONE/pip/mkdir/premature-test)?

Class A **CONFIRMED**. Smallest patch: optional checksum utilities are not
ENVIRONMENT / are action-noise when machine checks can still pass.
Does not claim live text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree,
pip/DONE/mkdir, premature-test, E1 TaskYield preserved.
"""
from __future__ import annotations

from rad import __version__
from rad.control import TaskStatus
from rad.control import events as E
from rad.control.codingloop import (
    infer_package_dir,
    is_first_task_thrash_noise,
    is_missing_optional_checksum_utility,
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
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR

XXD_ERR = "sh: 1: xxd: not found\n[exit=127]"
XXD_CMD = "xxd text_analyzer/input.txt"
XXD_ERR_BARE = "xxd: not found\n[exit=127]"
HEXDUMP_ERR = "bash: hexdump: command not found\n[exit=127]"
SHA256_BIN_ERR = "sh: 1: sha256sum: not found\n[exit=127]"
SHA256_FILE_ERR = "sha256sum: text_analyzer/input.txt: No such file or directory\n[exit=1]"

RW085_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Create text_analyzer package",
            "depends_on": [],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
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

def test_xxd_env_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_forbids_xxd_checksum_theater():
    assert "do NOT emit a standalone mkdir" in PLAN_PROMPT
    assert "Do not run tests" in PLAN_PROMPT
    assert "xxd" in PLAN_PROMPT
    assert "hexdump" in PLAN_PROMPT
    assert "hashlib" in PLAN_PROMPT


def test_ascii_tree_package_dir_still_infers_text_analyzer():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"


def test_optional_checksum_helper_is_tight():
    assert is_missing_optional_checksum_utility(XXD_ERR, XXD_CMD)
    assert is_missing_optional_checksum_utility(XXD_ERR_BARE, XXD_CMD)
    assert is_missing_optional_checksum_utility(HEXDUMP_ERR, "hexdump -C text_analyzer/input.txt")
    assert is_missing_optional_checksum_utility(SHA256_BIN_ERR, "sha256sum text_analyzer/input.txt")
    assert is_first_task_thrash_noise("run_shell", XXD_ERR, XXD_CMD)
    assert not is_missing_optional_checksum_utility(
        SHA256_FILE_ERR, "sha256sum text_analyzer/input.txt")
    assert not is_missing_optional_checksum_utility(
        "sh: 1: python3: command not found\n[exit=127]", "python3 text_analyzer/analyzer.py")
    assert not is_missing_optional_checksum_utility(
        "sh: 1: pip: command not found\n[exit=127]", "pip install -r requirements.txt")
    assert not is_missing_optional_checksum_utility(
        "sh: 1: mkreport_xyz: command not found", "mkreport_xyz")
    assert not is_missing_optional_checksum_utility(
        "cat: summary.json: No such file or directory", "cat summary.json")
    assert not is_missing_optional_checksum_utility(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert not is_missing_optional_checksum_utility(PIP_REQ_ERR, "pip install -r requirements.txt")
    assert not is_missing_optional_checksum_utility(MKDIR_ERR, "mkdir text_analyzer")
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_pip_requirements_file_missing(PIP_REQ_ERR, "pip install -r requirements.txt")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")


# ---------------------------------------------------------------- classify: missing xxd is not ENVIRONMENT

def test_xxd_not_found_is_not_environment_repair():
    """RW-085 shape: xxd exit 127 must not Repair prerequisite."""
    t = Task.new("o", "Create text_analyzer package")
    t.attempts = 1
    obs = [_ob(t, XXD_ERR, args={"command": XXD_CMD})]
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "actions", "detail": "5 actions, 1 errors"},
        {"ok": True, "kind": "file_nonempty", "detail": "text_analyzer/input.txt"},
    ]}
    assert classify(t, obs, verification=ver) != FailureClass.ENVIRONMENT
    assert classify(t, obs, verification=ver) == FailureClass.TOOL
    d = RecoveryEngine().decide(t, obs, verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy != "repair" or d.data.get("coding_repair") is True
    assert "Repair prerequisite" not in d.reason
    assert "xxd" in d.hint.lower() or "hexdump" in d.hint.lower() or "hashlib" in d.hint.lower()


def test_hexdump_and_sha256sum_bin_missing_are_not_environment():
    t = Task.new("o", "Create text_analyzer package")
    t.attempts = 1
    for out, cmd in (
        (HEXDUMP_ERR, "hexdump -C text_analyzer/input.txt"),
        (SHA256_BIN_ERR, "sha256sum text_analyzer/input.txt"),
    ):
        obs = [_ob(t, out, args={"command": cmd})]
        assert classify(t, obs) != FailureClass.ENVIRONMENT
        assert classify(t, obs) == FailureClass.TOOL


def test_command_not_found_without_optional_checksum_stays_environment():
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


def test_python_command_not_found_stays_environment():
    t = Task.new("o", "run analyzer")
    t.attempts = 1
    ob = _ob(t, "sh: 1: python3: command not found\n[exit=127]",
             args={"command": "python3 text_analyzer/analyzer.py"})
    assert classify(t, [ob]) == FailureClass.ENVIRONMENT


def test_sha256sum_missing_file_stays_environment_f18():
    """Binary exists; argument file is missing — genuine F-18 path."""
    t = Task.new("o", "write input")
    t.attempts = 1
    ob = _ob(t, SHA256_FILE_ERR, args={"command": "sha256sum text_analyzer/input.txt"})
    assert not is_missing_optional_checksum_utility(
        SHA256_FILE_ERR, "sha256sum text_analyzer/input.txt")
    assert classify(t, [ob]) == FailureClass.ENVIRONMENT


def test_cat_no_such_file_stays_environment_f18():
    t = Task.new("o", "write summary")
    t.attempts = 1
    ob = _ob(t, "cat: summary.json: No such file or directory")
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "file_exists", "detail": "summary.json exists=False"},
    ]}
    assert classify(t, [ob], verification=ver) == FailureClass.ENVIRONMENT


def test_premature_test_and_mkdir_still_not_environment():
    t = Task.new("o", "Create text_analyzer directory")
    t.attempts = 1
    obs = [_ob(t, PREMATURE_TEST_ERR, args={"command": PREMATURE_TEST_CMD})]
    assert classify(t, obs) != FailureClass.ENVIRONMENT
    obs = [_ob(t, MKDIR_ERR, args={"command": "mkdir text_analyzer"})]
    assert classify(t, obs) == FailureClass.TOOL


# ---------------------------------------------------------------- verifier: xxd is action noise when checks pass

def test_verifier_xxd_does_not_fail_passed_file_check(home, tmp_path):
    """RW-085 shape: input.txt nonempty passed; xxd not found must not FAILED."""
    ws_dir = tmp_path / "ws_rw085_v"
    ws_dir.mkdir()
    pkg = ws_dir / "text_analyzer"
    pkg.mkdir()
    (pkg / "input.txt").write_text(THREE_LINE_INPUT, encoding="utf-8")
    observer = Observer(home.root / "obs_rw085")
    t = Task.new("o", "Create text_analyzer package")
    t.checks = [Check("file_exists", {"path": "text_analyzer/input.txt"})]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "write_file",
        {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT},
        "wrote 76 chars → text_analyzer/input.txt", 1, ws_dir)
    observer.record(
        "o", t.id, "a2", "run_shell",
        {"command": XXD_CMD},
        XXD_ERR, 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: created package")
    actions = next(r for r in result["results"] if r.get("kind") == "actions")
    checks = [r for r in result["results"] if r.get("level") == "check"]
    assert actions["ok"] is True
    assert all(r["ok"] for r in checks)
    assert result["status"] == "VERIFIED"


def test_verifier_real_shell_error_still_fails_actions(home, tmp_path):
    ws_dir = tmp_path / "ws_rw085_real"
    ws_dir.mkdir()
    (ws_dir / "text_analyzer").mkdir()
    observer = Observer(home.root / "obs_rw085_real")
    t = Task.new("o", "Create text_analyzer package")
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


def test_verifier_xxd_does_not_verified_failed_json(home, tmp_path):
    """False DONE 0: xxd noise must not rubber-stamp a broken artifact."""
    ws_dir = tmp_path / "ws_rw085_json"
    ws_dir.mkdir()
    pkg = ws_dir / "text_analyzer"
    pkg.mkdir()
    (pkg / "summary.json").write_text("", encoding="utf-8")
    observer = Observer(home.root / "obs_rw085_json")
    t = Task.new("o", "Write summary.json")
    t.checks = [
        Check("file_exists", {"path": "text_analyzer"}),
        Check("json_valid", {"path": "text_analyzer/summary.json"}),
    ]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "run_shell",
        {"command": XXD_CMD},
        XXD_ERR, 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: summary")
    assert result["status"] == "FAILED"
    json_r = next(r for r in result["results"] if r.get("kind") == "json_valid")
    assert json_r["ok"] is False


def test_verifier_premature_test_and_mkdir_still_noise(home, tmp_path):
    """RW-078 / RW-080 must not regress."""
    ws_dir = tmp_path / "ws_rw085_prior"
    ws_dir.mkdir()
    (ws_dir / "text_analyzer").mkdir()
    observer = Observer(home.root / "obs_rw085_prior")
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


# ---------------------------------------------------------------- scripted: xxd must not starve later package task

def test_xxd_does_not_starve_later_task(home, tmp_path):
    """RW-085 shape: write input; xxd not found; later independent
    package file must still run. No ENVIRONMENT / Repair prerequisite.
    """
    ws_dir = tmp_path / "ws_rw085"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
          ("run_shell", {"command": XXD_CMD})],
         "DONE: created package"),
        ([("write_file", {"path": "text_analyzer/analyzer.py",
                          "content": "print('ok')\n"})],
         "DONE: wrote analyzer"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW085_PLAN)
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
        if t.text.startswith("Create text_analyzer package"):
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
