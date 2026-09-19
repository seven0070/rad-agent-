"""v0.4.1 multi-file coding under tight budgets (Gen3 theme 2).

RW-071 live NIM (v0.4.0): path-aligned checks held; Class B residual was
wrong 1-line input (sha256 9bf9660f…), empty summary.json, and ENVIRONMENT
repair thrash on mkdir-already-exists mixed with check noise (tools 12/12).

Smallest control-plane patch:
  * mkdir / create "already exists" is not ENVIRONMENT (no Repair prerequisite)
  * merge omitted json_valid / file_line_count / test shell_ok into objective
    checks so weak file_exists artifacts cannot become VERIFIED
  * file_line_count check for exact N-line files

Does not claim live 11B text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Path-aligned checks preserved.
"""
from __future__ import annotations

from rad import __version__
from rad.control import ObjectiveStatus
from rad.control import events as E
from rad.control.codingloop import infer_coding_checks, merge_coding_checks
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observation, Observer
from rad.control.planner import PLAN_PROMPT, Planner
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Check, Task
from rad.control.verifier import Verifier
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401

RW071_GOAL = (
    "Create a text analyzer under text_analyzer/\n"
    "Required files:\n"
    "- analyzer.py\n"
    "- input.txt (exact 3-line)\n"
    "- summary.json\n"
    "- test_analyzer.py\n"
    "- README.md\n"
    "Run the tests."
)

ONE_LINE_INPUT = (
    "RAD is a personal agent. RAD executes useful work. RAD verifies its results."
)
THREE_LINE_INPUT = (
    "RAD is a personal agent.\n"
    "RAD executes useful work.\n"
    "RAD verifies its results."
)

WEAK_LLM_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "Create text_analyzer directory and write package files",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "input.txt"}},
            {"kind": "file_contains", "args": {"path": "input.txt",
                                              "text": "RAD is a personal agent."}},
            {"kind": "file_exists", "args": {"path": "summary.json"}},
        ],
    }],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "analyzer.py"}},
        {"kind": "file_exists", "args": {"path": "summary.json"}},
    ],
}


def _ob(task: Task, out: str, status: str = "error", tool: str = "run_shell") -> Observation:
    return Observation.new(objective_id="o", task_id=task.id, action_id="a", tool=tool,
                           args={}, status=status, output=out, duration_ms=1)


# ---------------------------------------------------------------- architecture freeze

def test_multifile_tight_budget_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.0"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_asks_for_no_standalone_mkdir_and_line_count():
    assert "do NOT emit a standalone mkdir" in PLAN_PROMPT
    assert "file_line_count" in PLAN_PROMPT
    assert "Empty .json is invalid JSON" in PLAN_PROMPT


# ---------------------------------------------------------------- inference / merge

def test_infer_file_line_count_on_exact_n_line_package_input():
    checks = infer_coding_checks(RW071_GOAL)
    lines = [c for c in checks if c.kind == "file_line_count"]
    assert lines
    assert lines[0].args.get("path") == "text_analyzer/input.txt"
    assert int(lines[0].args.get("n")) == 3
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    assert any(
        c.kind == "shell_ok" and "text_analyzer/test_analyzer.py" in str(c.args.get("command", ""))
        for c in checks
    )


def test_merge_adds_json_valid_and_line_count_without_remapping_kinds():
    existing = [
        Check("file_exists", {"path": "text_analyzer/summary.json"}),
        Check("json_valid", {"path": "text_analyzer/analyzer.py"}),  # F-26: keep
    ]
    merged = merge_coding_checks(existing, infer_coding_checks(RW071_GOAL))
    kinds_paths = [(c.kind, c.args.get("path"), c.args.get("command"), c.args.get("n"))
                   for c in merged]
    assert ("file_exists", "text_analyzer/summary.json", None, None) in kinds_paths
    assert ("json_valid", "text_analyzer/analyzer.py", None, None) in kinds_paths
    assert ("json_valid", "text_analyzer/summary.json", None, None) in kinds_paths
    assert ("file_line_count", "text_analyzer/input.txt", None, 3) in kinds_paths
    assert any(c.kind == "shell_ok" for c in merged)


def test_llm_weak_plan_merges_objective_contracts_tasks_keep_llm_checks(tmp_path):
    plan = Planner(_plan_llm(WEAK_LLM_PLAN), str(tmp_path)).plan(Objective.new(RW071_GOAL))
    assert plan["source"] == "llm"
    obj_kinds = {(c.kind, c.args.get("path") or c.args.get("command"))
                 for c in plan["objective_checks"]}
    assert ("json_valid", "text_analyzer/summary.json") in obj_kinds
    assert ("file_line_count", "text_analyzer/input.txt") in obj_kinds
    assert any(c.kind == "shell_ok" for c in plan["objective_checks"])
    task_kinds = [c.kind for t in plan["graph"].tasks.values() for c in t.checks]
    assert "file_exists" in task_kinds
    assert "file_contains" in task_kinds


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW071_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert any(c.kind == "json_valid" for c in res["objective_checks"])
    assert any(c.kind == "file_line_count" for c in res["objective_checks"])


# ---------------------------------------------------------------- verifier

def test_file_line_count_three_line_vs_collapsed_one_line(home, tmp_path):
    ws = tmp_path / "ws_lines"
    ws.mkdir()
    pkg = ws / "text_analyzer"
    pkg.mkdir()
    v = Verifier(ws, Observer(home.root / "obs"), home=home)
    (pkg / "good.txt").write_text(THREE_LINE_INPUT, encoding="utf-8")
    (pkg / "bad.txt").write_text(ONE_LINE_INPUT, encoding="utf-8")
    (pkg / "summary.json").write_text("", encoding="utf-8")
    ok = v.run_check(Check("file_line_count", {"path": "text_analyzer/good.txt", "n": 3}))
    bad = v.run_check(Check("file_line_count", {"path": "text_analyzer/bad.txt", "n": 3}))
    empty = v.run_check(Check("json_valid", {"path": "text_analyzer/summary.json"}))
    assert ok["ok"] is True
    assert bad["ok"] is False
    assert empty["ok"] is False


# ---------------------------------------------------------------- recovery: already-exists is not ENVIRONMENT

def test_mkdir_already_exists_mixed_noise_is_not_environment_repair():
    """RW-071 shape: File exists + no-such-file check noise + empty JSON.

    Must not insert Repair prerequisite (ENVIRONMENT). Prefer TOOL/VALIDATION
    coding repair with the json_valid failure.
    """
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
    d = RecoveryEngine().decide(t, obs, verification=ver, repairs_so_far=0, retries_left=3)
    assert d.failure_class != FailureClass.ENVIRONMENT
    assert d.strategy == "repair"
    assert d.data.get("coding_repair") is True
    assert "json_valid" in d.hint or "invalid JSON" in d.hint


def test_command_not_found_without_already_exists_stays_environment():
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


# ---------------------------------------------------------------- scripted: weak artifacts are not VERIFIED (false DONE 0)

def test_weak_one_line_and_empty_json_not_verified(home, tmp_path):
    ws = tmp_path / "ws_rw071"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": ONE_LINE_INPUT}),
          ("write_file", {"path": "text_analyzer/summary.json", "content": ""}),
          ("write_file", {"path": "text_analyzer/analyzer.py",
                          "content": "print('x')\n"}),
          ("write_file", {"path": "text_analyzer/test_analyzer.py",
                          "content": "raise SystemExit(1)\n"}),
          ("write_file", {"path": "text_analyzer/README.md",
                          "content": "demo\n"})],
         "DONE: wrote package"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, WEAK_LLM_PLAN)
    obj = ctl.run(ctl.create(
        RW071_GOAL,
        budget=Budget(tool_calls=12, retries=6),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)
    log = EventLog(ctl.store.events_path(obj.id))
    decisions = [e.data for e in log.read(kind=E.RECOVERY_DECISION)]
    assert not any(d.get("failure_class") == FailureClass.ENVIRONMENT for d in decisions)
    g = ctl.load_graph(obj)
    assert not any(t.text.startswith("Repair prerequisite") for t in g.tasks.values())
    raw_in = (ws / "text_analyzer" / "input.txt").read_text(encoding="utf-8")
    assert raw_in.splitlines() != [
        "RAD is a personal agent.",
        "RAD executes useful work.",
        "RAD verifies its results.",
    ]
    stored = [Check.from_dict(c) if isinstance(c, dict) else c
              for c in (obj.verification or {}).get("objective_checks") or []]
    assert any(c.kind == "json_valid" for c in stored)
    assert any(c.kind == "file_line_count" for c in stored)


def test_aligned_three_line_valid_json_and_tests_still_verify(home, tmp_path):
    """Path-aligned success path is preserved when artifacts actually match."""
    ws = tmp_path / "ws_ok"
    ws.mkdir()
    home.update(workspace=str(ws))
    good_summary = '{"lines": 3, "words": 13, "characters": 76}'
    ScriptedSession.script = [
        ([("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
          ("write_file", {"path": "text_analyzer/summary.json", "content": good_summary}),
          ("write_file", {"path": "text_analyzer/analyzer.py",
                          "content": "print('ok')\n"}),
          ("write_file", {"path": "text_analyzer/test_analyzer.py",
                          "content": "print('ok')\n"}),
          ("write_file", {"path": "text_analyzer/README.md",
                          "content": "demo\n"})],
         "DONE: wrote package"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, WEAK_LLM_PLAN)
    obj = ctl.run(ctl.create(
        RW071_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") == "VERIFIED", ov
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert not (ws / "input.txt").exists()
    assert not (ws / "summary.json").exists()
