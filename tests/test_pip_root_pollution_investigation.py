"""Investigate-first: pip thrash + root analyzer.py pollution (RW-081).

RW-081 live NIM (v0.4.5): ASCII-tree objective_checks were package-joined.
mkdir File-exists Class A **live-confirmed** (first task VERIFIED despite
File-exists action error). Premature-test ENVIRONMENT Class A **not live-hit**.
Residual: second-task pip upgrade / `echo > analyzer.py` (workspace-root
pollution) / `pip install -r` error / pip jsonschema burned the remaining
tools=12; analyzer task never reached verify; empty `summary.json` `{}`;
SyntaxError test. retries=0. 0 invented DONE. 0 ENVIRONMENT repair.

Questions (non-binding):
  1. Does RAD emit/accept plans or actions that write package files at the
     workspace root when `package_dir` is known?
  2. Is there a verifier/recovery hole that lets root pollution waste budget
     or falsely satisfy/fail package checks?
  3. Is pip thrash under stdlib-only goals a control-plane defect beyond
     existing PLAN_PROMPT + v0.4.3 pip-missing-requirements handling?
  4. Would joining bare shell-redirect / write_file paths to `package_dir`
     be a real hole-close, or would it overwrite a good package file?

Does not claim live 11B text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree,
pip/DONE, mkdir File-exists, premature-test ENVIRONMENT preserved.
No product bump — stay 0.4.5 if Class A is NOT CONFIRMED.
"""
from __future__ import annotations

from rad import __version__
from rad.control import ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.codingloop import (
    align_rel_path,
    align_shell_command,
    infer_coding_checks,
    infer_package_dir,
    is_first_task_thrash_noise,
    is_mkdir_already_exists,
    is_missing_python_script,
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
from rad.tools import run_tool
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401
from tests.test_first_task_thrash import PIP_REQ_ERR, THREE_LINE_INPUT
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_tools import _ctx

GOOD_ANALYZER = (
    "print('package analyzer')\n"
)
ROOT_STUB = "print('root stub')\n"

RW081_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Create text_analyzer directory and write input.txt",
            "depends_on": [],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
                {"kind": "file_line_count", "args": {"path": "text_analyzer/input.txt", "n": 3}},
            ],
        },
        {
            "id": "t2",
            "text": "Write analyzer.py",
            "depends_on": ["t1"],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}},
            ],
        },
    ],
    "objective_checks": [
        {"kind": "json_valid", "args": {"path": "summary.json"}},
        {"kind": "file_line_count", "args": {"path": "input.txt", "n": 3}},
        {"kind": "shell_ok", "args": {"command": "python3 test_analyzer.py"}},
    ],
}

ROOT_ONLY_WRITE_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write analyzer.py",
            "depends_on": [],
            "checks": [
                {"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}},
            ],
        },
    ],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "text_analyzer/analyzer.py"}},
    ],
}


def _ob(task: Task, out: str, status: str = "error", tool: str = "run_shell",
        args: dict | None = None) -> Observation:
    return Observation.new(objective_id="o", task_id=task.id, action_id="a", tool=tool,
                           args=args or {}, status=status, output=out, duration_ms=1)


# ---------------------------------------------------------------- architecture freeze

def test_pip_root_pollution_investigation_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.4.9"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_already_forbids_pip_for_stdlib_only():
    """PLAN_PROMPT already carries the stdlib-only no-pip guidance (v0.4.3)."""
    assert "must not pip install" in PLAN_PROMPT
    assert "DONE is not a tool" in PLAN_PROMPT
    assert "do NOT emit a standalone mkdir" in PLAN_PROMPT
    assert "Do not run tests" in PLAN_PROMPT


def test_ascii_tree_package_dir_still_infers_text_analyzer():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"


def test_prior_thrash_helpers_still_hold():
    assert is_pip_requirements_file_missing(PIP_REQ_ERR, "pip install -r requirements.txt")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_first_task_thrash_noise("run_shell", PIP_REQ_ERR, "pip install -r requirements.txt")
    assert is_first_task_thrash_noise("run_shell", MKDIR_ERR, "mkdir text_analyzer")
    assert is_first_task_thrash_noise("run_shell", PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)


# ---------------------------------------------------------------- claim 1: emit/accept root writes when package_dir is known

def test_inferred_and_llm_checks_still_join_to_package_dir(tmp_path):
    """RAD emits package-joined checks. Theme 1 / slice A still hold on RW-081."""
    checks = infer_coding_checks(RW073_ASCII_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    line_paths = [c.args.get("path") for c in checks if c.kind == "file_line_count"]
    assert "text_analyzer/input.txt" in line_paths
    plan = Planner(_plan_llm(RW081_PLAN), str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    assert plan["source"] == "llm"
    oc_paths = [(c.kind, c.args.get("path") or c.args.get("command"))
                for c in plan["objective_checks"]]
    assert ("json_valid", "text_analyzer/summary.json") in oc_paths
    assert ("file_line_count", "text_analyzer/input.txt") in oc_paths
    assert any(c.kind == "shell_ok" and "text_analyzer/test_analyzer.py" in str(c.args.get("command", ""))
               for c in plan["objective_checks"])
    assert not any(
        (c.args.get("path") in {"summary.json", "input.txt", "analyzer.py"})
        for c in plan["objective_checks"]
    )


def test_align_shell_command_does_not_rewrite_echo_redirect_or_pip():
    """Check-command alignment rewrites bare test_*.py only — not echo redirects.

    Joining `echo … > analyzer.py` to `text_analyzer/analyzer.py` would be a new
    product rule, not current contract. Live RW-081 root pollution is the model
    proposing a workspace-cwd redirect, not RAD emitting a root check.
    """
    echo_cmd = "echo 'stub' > analyzer.py"
    pip_cmd = "pip install -r requirements.txt"
    assert align_shell_command(echo_cmd, "text_analyzer/") == echo_cmd
    assert align_shell_command(pip_cmd, "text_analyzer/") == pip_cmd
    assert align_shell_command("python3 test_analyzer.py", "text_analyzer/") == (
        "python3 text_analyzer/test_analyzer.py"
    )
    # Checks *would* join a bare analyzer.py path — that is theme 1, not actions.
    assert align_rel_path("analyzer.py", "text_analyzer/") == "text_analyzer/analyzer.py"


def test_write_file_and_echo_redirect_stay_at_workspace_root(home, tmp_path):
    """Executor/tools do not remap write_file or shell redirects to package_dir.

    Models propose paths. RAD decides permission/budget/execute. Theme 1 joins
    *checks*, not action arguments.
    """
    ws_dir = tmp_path / "ws_rw081_root_write"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ctx = _ctx(home, auto=True)
    out_w = run_tool("write_file", {"path": "analyzer.py", "content": ROOT_STUB}, ctx)
    assert "wrote" in out_w
    out_e = run_tool("run_shell", {"command": "echo 'echo-stub' > echo_analyzer.py"}, ctx)
    assert "[exit=0]" in out_e or out_e.strip() == "" or "echo-stub" not in out_e
    assert (ws_dir / "analyzer.py").is_file()
    assert (ws_dir / "echo_analyzer.py").is_file()
    assert not (ws_dir / "text_analyzer" / "analyzer.py").exists()


def test_planner_keeps_unprefixed_task_text_without_rewriting_actions(tmp_path):
    """LLM task text 'Write analyzer.py' is accepted. Checks are joined; text is not."""
    plan = Planner(_plan_llm(RW081_PLAN), str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    texts = [t.text for t in plan["graph"].tasks.values()]
    assert any(t == "Write analyzer.py" for t in texts)
    t2 = next(t for t in plan["graph"].tasks.values() if t.text == "Write analyzer.py")
    assert any(c.args.get("path") == "text_analyzer/analyzer.py" for c in t2.checks)


# ---------------------------------------------------------------- claim 2: verifier/recovery hole?

def test_root_analyzer_does_not_satisfy_package_check(home, tmp_path):
    """False DONE 0: a root analyzer.py does not VERIFIED text_analyzer/analyzer.py."""
    ws_dir = tmp_path / "ws_rw081_false"
    ws_dir.mkdir()
    (ws_dir / "analyzer.py").write_text(ROOT_STUB, encoding="utf-8")
    observer = Observer(home.root / "obs_rw081_false")
    t = Task.new("o", "Write analyzer.py")
    t.checks = [Check("file_exists", {"path": "text_analyzer/analyzer.py"})]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "write_file",
        {"path": "analyzer.py", "content": ROOT_STUB},
        "wrote 18 chars → analyzer.py", 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: wrote analyzer")
    pkg = next(r for r in result["results"] if r.get("kind") == "file_exists")
    assert pkg["ok"] is False
    assert result["status"] == "FAILED"


def test_root_pollution_does_not_fail_passed_package_check(home, tmp_path):
    """Package file present + root echo leftover: package check still VERIFIED.

    Root pollution is extra disk, not a failed contract and not a rubber-stamp
    of a missing package file.
    """
    ws_dir = tmp_path / "ws_rw081_both"
    ws_dir.mkdir()
    pkg = ws_dir / "text_analyzer"
    pkg.mkdir()
    (pkg / "analyzer.py").write_text(GOOD_ANALYZER, encoding="utf-8")
    observer = Observer(home.root / "obs_rw081_both")
    t = Task.new("o", "Write analyzer.py")
    t.checks = [Check("file_exists", {"path": "text_analyzer/analyzer.py"})]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "write_file",
        {"path": "text_analyzer/analyzer.py", "content": GOOD_ANALYZER},
        "wrote 24 chars → text_analyzer/analyzer.py", 1, ws_dir)
    observer.record(
        "o", t.id, "a2", "run_shell",
        {"command": "echo 'stub' > analyzer.py"},
        "", 1, ws_dir)
    (ws_dir / "analyzer.py").write_text(ROOT_STUB, encoding="utf-8")
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: wrote analyzer")
    pkg_r = next(r for r in result["results"] if r.get("kind") == "file_exists")
    assert pkg_r["ok"] is True
    assert result["status"] == "VERIFIED"
    assert (pkg / "analyzer.py").read_text(encoding="utf-8") == GOOD_ANALYZER
    assert (ws_dir / "analyzer.py").is_file()


def test_joining_echo_redirect_would_overwrite_good_package_file(home, tmp_path):
    """Anti-patch: remapping echo > analyzer.py into package_dir would clobber
    the good package analyzer.py with the broken stub. Current behavior isolates
    pollution at workspace root. That is a reason NOT to join action redirects.
    """
    ws_dir = tmp_path / "ws_rw081_clobber"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    pkg = ws_dir / "text_analyzer"
    pkg.mkdir()
    (pkg / "analyzer.py").write_text(GOOD_ANALYZER, encoding="utf-8")
    ctx = _ctx(home, auto=True)
    run_tool("run_shell", {"command": "echo 'broken-stub' > analyzer.py"}, ctx)
    assert (pkg / "analyzer.py").read_text(encoding="utf-8") == GOOD_ANALYZER
    assert "broken-stub" in (ws_dir / "analyzer.py").read_text(encoding="utf-8")
    # The hypothetical join (what a Class A action-remap would do):
    joined = str(pkg / "analyzer.py")
    assert joined != str(ws_dir / "analyzer.py")


def test_empty_summary_json_still_not_verified(home, tmp_path):
    """False DONE 0: `{}` is valid JSON but json_field contracts still fail when asked."""
    ws_dir = tmp_path / "ws_rw081_empty"
    ws_dir.mkdir()
    pkg = ws_dir / "text_analyzer"
    pkg.mkdir()
    (pkg / "summary.json").write_text("{}", encoding="utf-8")
    observer = Observer(home.root / "obs_rw081_empty")
    t = Task.new("o", "Write summary.json")
    t.checks = [
        Check("json_valid", {"path": "text_analyzer/summary.json"}),
        Check("json_field", {"path": "text_analyzer/summary.json", "key": "words"}),
    ]
    t.started = 1.0
    observer.record(
        "o", t.id, "a1", "write_file",
        {"path": "text_analyzer/summary.json", "content": "{}"},
        "wrote 2 chars → text_analyzer/summary.json", 1, ws_dir)
    v = Verifier(ws_dir, observer, home=home)
    result = v.verify_task(t, "DONE: summary")
    jv = next(r for r in result["results"] if r.get("kind") == "json_valid")
    jf = next(r for r in result["results"] if r.get("kind") == "json_field")
    assert jv["ok"] is True
    assert jf["ok"] is False
    assert result["status"] == "FAILED"


# ---------------------------------------------------------------- claim 3: pip thrash beyond PLAN_PROMPT / v0.4.3?

def test_pip_missing_requirements_still_not_environment():
    """Do not re-litigate v0.4.3: pip -r file-not-found is still not ENVIRONMENT."""
    t = Task.new("o", "Write analyzer.py")
    t.attempts = 1
    obs = [_ob(t, PIP_REQ_ERR, args={"command": "pip install -r requirements.txt"})]
    ver = {"status": "FAILED", "results": [
        {"ok": False, "kind": "actions", "detail": "4 actions, 1 errors"},
        {"ok": True, "kind": "file_exists", "detail": "text_analyzer/analyzer.py exists=True"},
    ]}
    assert classify(t, obs, verification=ver) != FailureClass.ENVIRONMENT
    d = RecoveryEngine().decide(t, obs, verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert "Repair prerequisite" not in d.reason


def test_successful_pip_is_not_environment_or_action_noise():
    """pip upgrade / pip jsonschema success is a real tool call, not a classifier hole.

    Rejecting it at ingest would still charge Budget.tool_calls. That spend is
    model quality (Class B), not ENVIRONMENT misclass (already closed as v0.4.3
    for the *missing requirements.txt* case).
    """
    t = Task.new("o", "Write analyzer.py")
    t.attempts = 1
    out = "Successfully installed jsonschema-4.0.0\n[exit=0]"
    ob = Observation.new(objective_id="o", task_id=t.id, action_id="a", tool="run_shell",
                         args={"command": "pip install jsonschema"}, status="success",
                         output=out, duration_ms=1)
    assert classify(t, [ob]) != FailureClass.ENVIRONMENT
    assert not is_pip_requirements_file_missing(out, "pip install jsonschema")
    assert not is_first_task_thrash_noise("run_shell", out, "pip install jsonschema")


def test_run_tool_still_executes_pip_r_for_stdlib_goal(home, tmp_path):
    """No executor ingest-filter: pip -r still runs (and fails honestly if missing)."""
    ws_dir = tmp_path / "ws_rw081_pip"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    out = run_tool("run_shell", {"command": "pip install -r requirements.txt"},
                   _ctx(home, auto=True))
    assert "No such file" in out or "Could not open requirements" in out or "exit=" in out
    assert not out.startswith("unknown tool:")
    assert not out.startswith("DENIED")


# ---------------------------------------------------------------- scripted RW-081 shape

def test_mkdir_live_path_still_verifies_then_pip_echo_does_not_insert_repair(home, tmp_path):
    """RW-081 shape: first task VERIFIED despite mkdir File-exists; second task
    burns remaining tools on pip/echo without ENVIRONMENT Repair-prerequisite.

    Root analyzer.py is leftover pollution; package analyzer.py from task 1 is
    unchanged. Objective is not rubber-stamped.
    """
    ws_dir = tmp_path / "ws_rw081"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
          ("write_file", {"path": "text_analyzer/analyzer.py", "content": GOOD_ANALYZER}),
          ("write_file", {"path": "text_analyzer/summary.json", "content": "{}"}),
          ("run_shell", {"command": "mkdir text_analyzer"})],
         "DONE: created directory and input"),
        ([("run_shell", {"command": "pip install -r requirements.txt"}),
          ("run_shell", {"command": "echo 'broken-stub' > analyzer.py"})],
         "DONE: wrote analyzer"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW081_PLAN)
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
        elif t.text.startswith("Write analyzer.py"):
            t2 = t
    assert t1 is not None and t2 is not None
    assert t1.status == TaskStatus.COMPLETED
    assert t1.verification and t1.verification.get("status") == "VERIFIED"
    assert t2.status == TaskStatus.COMPLETED
    assert t2.verification and t2.verification.get("status") == "VERIFIED"
    assert (ws_dir / "text_analyzer" / "input.txt").is_file()
    assert (ws_dir / "text_analyzer" / "analyzer.py").read_text(encoding="utf-8") == GOOD_ANALYZER
    assert (ws_dir / "analyzer.py").is_file()
    assert "broken-stub" in (ws_dir / "analyzer.py").read_text(encoding="utf-8")
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"


def test_root_only_write_is_not_verified_and_not_environment(home, tmp_path):
    """Root write under package checks → FAILED validation, not ENVIRONMENT, not VERIFIED."""
    ws_dir = tmp_path / "ws_rw081_root_only"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("write_file", {"path": "analyzer.py", "content": ROOT_STUB})],
         "DONE: wrote analyzer"),
        ([("write_file", {"path": "text_analyzer/analyzer.py", "content": GOOD_ANALYZER})],
         "DONE: repaired to package"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, ROOT_ONLY_WRITE_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=12, retries=6),
        auto=True,
    ))
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert decisions, "expected recovery after root write missed the package check"
    assert decisions[0]["failure_class"] != FailureClass.ENVIRONMENT
    assert "Repair prerequisite" not in (decisions[0].get("reason") or "")
    g = ctl.load_graph(obj)
    t1 = next(t for t in g.tasks.values() if t.text == "Write analyzer.py")
    first_ver = (t1.verification or {}).get("status")
    # Honest miss on first attempt (or repaired later). Never rubber-stamp root as package.
    assert first_ver != "VERIFIED" or (ws_dir / "text_analyzer" / "analyzer.py").is_file()
    assert (ws_dir / "analyzer.py").is_file()
    ov = (obj.verification or {}).get("objective") or {}
    if not (ws_dir / "text_analyzer" / "analyzer.py").is_file():
        assert ov.get("status") != "VERIFIED"
        assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)


def test_budget_stop_mid_pip_echo_is_needs_user_without_environment_repair(home, tmp_path):
    """Live RW-081: remaining tools spent on pip/echo; verify never ran; no repair insert.

    That is an honest budget stop (Class B), not a new ENVIRONMENT hole. v0.4.3
    already covers pip -r *if* verify runs.
    """
    ws_dir = tmp_path / "ws_rw081_budget"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
          ("write_file", {"path": "text_analyzer/analyzer.py", "content": GOOD_ANALYZER}),
          ("run_shell", {"command": "mkdir text_analyzer"})],
         "DONE: created directory and input"),
        ([("run_shell", {"command": "pip install -r requirements.txt"}),
          ("run_shell", {"command": "echo 'broken-stub' > analyzer.py"}),
          ("run_shell", {"command": "pip install -r requirements.txt"}),
          ("run_shell", {"command": "pip install -r requirements.txt"})],
         "DONE: wrote analyzer"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW081_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=5, retries=6),
        auto=True,
    ))
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert not any(d.get("failure_class") == FailureClass.ENVIRONMENT for d in decisions)
    g = ctl.load_graph(obj)
    assert not any(t.text.startswith("Repair prerequisite") for t in g.tasks.values())
    t1 = next(t for t in g.tasks.values() if t.text.startswith("Create text_analyzer directory"))
    t2 = next(t for t in g.tasks.values() if t.text.startswith("Write analyzer.py"))
    assert t1.status == TaskStatus.COMPLETED
    assert t1.verification and t1.verification.get("status") == "VERIFIED"
    assert t2.status != TaskStatus.COMPLETED or t2.verification is None or obj.usage.tool_calls >= 5
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)
    assert (ws_dir / "text_analyzer" / "analyzer.py").read_text(encoding="utf-8") == GOOD_ANALYZER


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert any(c.kind == "json_valid" for c in res["objective_checks"])
    assert any(c.args.get("path") == "text_analyzer/summary.json" for c in res["objective_checks"])
