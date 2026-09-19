"""v0.5.4 G4-7 — coding artifact completeness / named package-file contracts.

Investigate-first (ROADMAP G4-7 / Cycle 32 findings):
- G4-5 closed plan *structure* (RW-094 / RW-095). Residual Class B on a
  working path is incomplete packages.
- RW-081: empty ``{}`` ``summary.json`` still passes ``json_valid``.
- RW-085 / RW-086: missing README.md / tests + alt-schema summary.
- ``infer_coding_checks`` already added ``json_valid`` / test ``shell_ok`` /
  ``file_line_count`` — not ``file_exists`` for named README.md / analyzer.py,
  not ``json_field`` for required keys.

G4-7 contracts named package files via ``file_exists`` (RW-096) and named
JSON keys via ``json_field`` (RW-097) on *objective_checks* only. F-17 stays
closed (no checks on fallback *tasks*). F-26 check *kinds* are not remapped.

Does not claim live text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. No Class A invented for 403/429. No GitHub Release / tag.
"""
from __future__ import annotations

from rad import __version__
from rad.control import ObjectiveStatus
from rad.control.codingloop import infer_coding_checks, merge_coding_checks
from rad.control.objectives import Budget, Objective
from rad.control.observer import Observer
from rad.control.planner import PLAN_CODING_RETRY, PLAN_PROMPT, Planner
from rad.control.tasks import Check
from rad.control.verifier import Verifier
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl
from tests.test_multifile_tight_budget import RW071_GOAL, THREE_LINE_INPUT, WEAK_LLM_PLAN
from tests.test_path_aligned_checks import WORD_COUNTER_GOAL
from tests.test_plan_timeout_resilience import SequentialLLM


GOOD_SUMMARY = '{"lines": 3, "words": 13, "characters": 76}'
ALT_SCHEMA_SUMMARY = '{"word_count": 13, "char_count": 76, "letter_frequency": {}}'
EMPTY_SUMMARY = "{}"
OK_PY = "print('ok')\n"

SIMPLE_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "Write text_analyzer package files",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
        ],
    }],
    "objective_checks": [],
}


def _kinds_paths(checks):
    return [
        (c.kind, c.args.get("path"), c.args.get("command"), c.args.get("key"))
        for c in checks
    ]


def _write_package(extra_summary=GOOD_SUMMARY, include_readme=True, include_analyzer=True,
                   include_tests=True):
    actions = [
        ("write_file", {"path": "text_analyzer/input.txt", "content": THREE_LINE_INPUT}),
        ("write_file", {"path": "text_analyzer/summary.json", "content": extra_summary}),
    ]
    if include_analyzer:
        actions.append(("write_file", {"path": "text_analyzer/analyzer.py", "content": OK_PY}))
    if include_tests:
        actions.append(("write_file", {"path": "text_analyzer/test_analyzer.py", "content": OK_PY}))
    if include_readme:
        actions.append(("write_file", {"path": "text_analyzer/README.md", "content": "demo\n"}))
    return actions


# ---------------------------------------------------------------- architecture freeze

def test_g47_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.0"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_plan_prompt_asks_for_named_files_and_json_fields():
    assert "file_exists" in PLAN_PROMPT
    assert "json_field" in PLAN_PROMPT
    assert "README.md" in PLAN_PROMPT
    assert "not completion when keys are named" in PLAN_PROMPT
    assert "json_field on named summary/result keys" in PLAN_CODING_RETRY
    assert "file_exists on named README.md" in PLAN_CODING_RETRY


# ---------------------------------------------------------------- RW-096 named package files

def test_rw096_infer_file_exists_for_named_readme_and_analyzer():
    """ASCII-tree goal names README.md and analyzer.py — those must be contracted."""
    checks = infer_coding_checks(RW073_ASCII_GOAL)
    exists = [(c.args.get("path")) for c in checks if c.kind == "file_exists"]
    assert "text_analyzer/README.md" in exists
    assert "text_analyzer/analyzer.py" in exists
    assert "text_analyzer/test_analyzer.py" not in exists
    assert "text_analyzer/summary.json" not in exists
    assert "text_analyzer/input.txt" not in exists
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    assert any(
        c.kind == "shell_ok" and "text_analyzer/test_analyzer.py" in str(c.args.get("command", ""))
        for c in checks
    )


def test_rw096_dash_list_under_package_also_contracts_named_files():
    checks = infer_coding_checks(RW071_GOAL)
    exists = [c.args.get("path") for c in checks if c.kind == "file_exists"]
    assert "text_analyzer/README.md" in exists
    assert "text_analyzer/analyzer.py" in exists
    fields = [c.args.get("key") for c in checks if c.kind == "json_field"]
    assert fields == []


def test_rw096_word_counter_contracts_main_module_not_test_file():
    checks = infer_coding_checks(WORD_COUNTER_GOAL)
    exists = [c.args.get("path") for c in checks if c.kind == "file_exists"]
    assert "word_counter.py" in exists
    assert not any(p and "test_word_counter.py" in p for p in exists)


# ---------------------------------------------------------------- RW-097 named JSON keys

def test_rw097_infer_json_field_for_named_summary_keys():
    """ASCII-tree ``(accurate lines/words/characters)`` must not accept ``{}``."""
    checks = infer_coding_checks(RW073_ASCII_GOAL)
    fields = [(c.args.get("path"), c.args.get("key")) for c in checks if c.kind == "json_field"]
    assert ("text_analyzer/summary.json", "lines") in fields
    assert ("text_analyzer/summary.json", "words") in fields
    assert ("text_analyzer/summary.json", "characters") in fields
    assert not any(c.args.get("key") == "accurate" for c in checks if c.kind == "json_field")


def test_rw097_word_counter_contracts_named_key_words():
    checks = infer_coding_checks(WORD_COUNTER_GOAL)
    fields = [(c.args.get("path"), c.args.get("key")) for c in checks if c.kind == "json_field"]
    assert ("result.json", "words") in fields


def test_rw097_empty_object_passes_json_valid_fails_json_field(home, tmp_path):
    ws = tmp_path / "ws_empty_json"
    ws.mkdir()
    pkg = ws / "text_analyzer"
    pkg.mkdir()
    (pkg / "summary.json").write_text(EMPTY_SUMMARY, encoding="utf-8")
    v = Verifier(ws, Observer(home.root / "obs_empty_json"), home=home)
    jv = v.run_check(Check("json_valid", {"path": "text_analyzer/summary.json"}))
    jf = v.run_check(Check("json_field", {
        "path": "text_analyzer/summary.json", "key": "words", "truthy": False,
    }))
    assert jv["ok"] is True
    assert jf["ok"] is False


def test_rw097_alt_schema_missing_classic_keys_fails(home, tmp_path):
    ws = tmp_path / "ws_alt"
    ws.mkdir()
    pkg = ws / "text_analyzer"
    pkg.mkdir()
    (pkg / "summary.json").write_text(ALT_SCHEMA_SUMMARY, encoding="utf-8")
    v = Verifier(ws, Observer(home.root / "obs_alt"), home=home)
    jv = v.run_check(Check("json_valid", {"path": "text_analyzer/summary.json"}))
    jf = v.run_check(Check("json_field", {
        "path": "text_analyzer/summary.json", "key": "lines", "truthy": False,
    }))
    assert jv["ok"] is True
    assert jf["ok"] is False


# ---------------------------------------------------------------- merge / F-17 / F-26

def test_merge_adds_named_contracts_without_remapping_kinds():
    existing = [
        Check("file_exists", {"path": "text_analyzer/summary.json"}),
        Check("json_valid", {"path": "text_analyzer/analyzer.py"}),
    ]
    merged = merge_coding_checks(existing, infer_coding_checks(RW073_ASCII_GOAL))
    kinds_paths = _kinds_paths(merged)
    assert ("file_exists", "text_analyzer/summary.json", None, None) in kinds_paths
    assert ("json_valid", "text_analyzer/analyzer.py", None, None) in kinds_paths
    assert ("json_valid", "text_analyzer/summary.json", None, None) in kinds_paths
    assert ("json_field", "text_analyzer/summary.json", None, "lines") in kinds_paths
    assert ("file_exists", "text_analyzer/README.md", None, None) in kinds_paths
    assert ("file_exists", "text_analyzer/analyzer.py", None, None) in kinds_paths


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    oc = {(c.kind, c.args.get("path") or c.args.get("command"), c.args.get("key"))
          for c in res["objective_checks"]}
    assert ("json_valid", "text_analyzer/summary.json", None) in oc
    assert ("json_field", "text_analyzer/summary.json", "words") in oc
    assert ("file_exists", "text_analyzer/README.md", None) in oc


def test_exhausted_llm_still_fallback_checkless():
    llm = SequentialLLM([TimeoutError("t1"), TimeoutError("t2")])
    res = Planner(llm, "/tmp/ws").plan(Objective.new(RW073_ASCII_GOAL), tool_budget=12)
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    assert any(c.kind == "file_exists" for c in res["objective_checks"])
    assert any(c.kind == "json_field" for c in res["objective_checks"])


# ---------------------------------------------------------------- scripted incomplete packages (false DONE 0)

def test_rw081_empty_summary_object_not_verified(home, tmp_path):
    """RW-081 shape: ``{}`` is valid JSON; named keys keep the objective honest."""
    ws = tmp_path / "ws_rw081_empty"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(extra_summary=EMPTY_SUMMARY), "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, SIMPLE_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)
    stored = [Check.from_dict(c) if isinstance(c, dict) else c
              for c in (obj.verification or {}).get("objective_checks") or []]
    assert any(c.kind == "json_valid" for c in stored)
    assert any(c.kind == "json_field" and c.args.get("key") in ("lines", "words", "characters")
               for c in stored)
    assert (ws / "text_analyzer" / "summary.json").read_text(encoding="utf-8").strip() == "{}"


def test_rw085_missing_readme_not_verified(home, tmp_path):
    """RW-085 / RW-086 shape: complete-looking package without README is not VERIFIED."""
    ws = tmp_path / "ws_rw085_readme"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(include_readme=False), "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, SIMPLE_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)
    assert not (ws / "text_analyzer" / "README.md").exists()
    stored = [Check.from_dict(c) if isinstance(c, dict) else c
              for c in (obj.verification or {}).get("objective_checks") or []]
    assert any(c.kind == "file_exists" and c.args.get("path") == "text_analyzer/README.md"
               for c in stored)


def test_rw086_alt_schema_summary_not_verified(home, tmp_path):
    """RW-086 shape: alt-schema summary (word_count) fails classic named keys."""
    ws = tmp_path / "ws_rw086_alt"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(extra_summary=ALT_SCHEMA_SUMMARY),
                               "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, SIMPLE_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)


def test_rw085_missing_analyzer_not_verified(home, tmp_path):
    ws = tmp_path / "ws_rw085_analyzer"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(include_analyzer=False), "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, SIMPLE_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert not (ws / "text_analyzer" / "analyzer.py").exists()


def test_complete_named_package_still_verifies(home, tmp_path):
    """Honesty bar does not reject a package that actually matches the contracts."""
    ws = tmp_path / "ws_g47_ok"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(), "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, WEAK_LLM_PLAN)
    obj = ctl.run(ctl.create(
        RW073_ASCII_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") == "VERIFIED", ov
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure
    assert (ws / "text_analyzer" / "README.md").is_file()
    assert (ws / "text_analyzer" / "analyzer.py").is_file()
