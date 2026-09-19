"""v1.0.1 Class A — json_field inference must not invent key ``on`` (RW-103).

Investigate-first (NIM glm-5.3 soak 2026-09-19):
- text_analyzer/ artifacts + tests passed on disk
- control plane never VERIFIED; budget burned
- objective checks included a bogus json_field key ``on``
- phrasing like "keys on a sample" / "lines, words, characters on a sample"

Class A CONFIRMED: G4-7 ``JSON_KEY_WORD_RE`` / parenthetical split tokenizes
English glue (``on``, ``sample``) into required JSON keys. Smallest fix:
stop-list those tokens. Named keys ``lines`` / ``words`` / ``characters``
and WORD_COUNTER ``words`` still contract. Empty ``{}`` still fails.
F-17 fallback *tasks* stay check-less. F-26 kinds not remapped.
Needle OFF. Caps unchanged. No live PASS claim. No GitHub Release / tag.
"""
from __future__ import annotations

from rad import __version__
from rad.control import ObjectiveStatus
from rad.control.codingloop import (
    INFER_CODING_CHECK_CAP,
    JSON_KEY_STOP,
    infer_coding_checks,
)
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.control.tasks import Check
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_coding_artifact_completeness import _write_package
from tests.test_control_plane import ScriptedSession, _ctl
from tests.test_multifile_tight_budget import WEAK_LLM_PLAN
from tests.test_path_aligned_checks import WORD_COUNTER_GOAL

ASCII_ON_SAMPLE_GOAL = RW073_ASCII_GOAL.replace(
    "(accurate lines/words/characters)",
    "(accurate lines/words/characters on a sample)",
)

KEYS_ON_SAMPLE_GOAL = (
    "Create a text analyzer package:\n"
    "\n"
    "text_analyzer/\n"
    "├── analyzer.py   (stdlib)\n"
    "├── input.txt     (exact 3 lines)\n"
    "├── summary.json  (JSON keys on a sample)\n"
    "├── test_analyzer.py\n"
    "└── README.md\n"
    "\n"
    "Exact 3-line input.txt. Run the tests.\n"
)

PAREN_LIST_ON_SAMPLE = (
    "Create analyzer.py and summary.json "
    "(lines, words, characters on a sample). Run the tests."
)


def _field_keys(goal: str):
    return [c.args.get("key") for c in infer_coding_checks(goal) if c.kind == "json_field"]


# ---------------------------------------------------------------- architecture freeze

def test_v101_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"
    assert "on" in JSON_KEY_STOP
    assert "sample" in JSON_KEY_STOP


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(ASCII_ON_SAMPLE_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    oc = {(c.kind, c.args.get("key")) for c in res["objective_checks"]}
    assert ("json_field", "on") not in oc
    assert ("json_field", "words") in oc


# ---------------------------------------------------------------- RW-103 glue is not a JSON key

def test_rw103_keys_on_a_sample_does_not_invent_on():
    fields = _field_keys(KEYS_ON_SAMPLE_GOAL)
    assert "on" not in fields
    assert "sample" not in fields


def test_rw103_parenthetical_on_a_sample_keeps_named_keys():
    fields = _field_keys(PAREN_LIST_ON_SAMPLE)
    assert fields == ["lines", "words", "characters"]
    assert "on" not in fields
    assert "sample" not in fields


def test_rw103_ascii_tree_on_a_sample_does_not_drop_readme_for_glue():
    """Bogus keys used to consume INFER cap 8 and drop named file_exists."""
    checks = infer_coding_checks(ASCII_ON_SAMPLE_GOAL)
    assert len(checks) <= INFER_CODING_CHECK_CAP
    fields = [c.args.get("key") for c in checks if c.kind == "json_field"]
    assert fields == ["lines", "words", "characters"]
    exists = [c.args.get("path") for c in checks if c.kind == "file_exists"]
    assert "text_analyzer/README.md" in exists
    assert "text_analyzer/analyzer.py" in exists


def test_rw103_ascii_classic_paren_still_contracts_named_keys():
    fields = _field_keys(RW073_ASCII_GOAL)
    assert ("lines" in fields) and ("words" in fields) and ("characters" in fields)
    assert "accurate" not in fields
    assert "on" not in fields


def test_rw103_word_counter_key_words_still_contracts():
    fields = _field_keys(WORD_COUNTER_GOAL)
    assert "words" in fields
    assert "on" not in fields


def test_rw103_complete_package_with_on_a_sample_goal_verifies(home, tmp_path):
    """Disk-correct package must VERIFIED; glue must not invent a missing key."""
    ws = tmp_path / "ws_rw103_ok"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(), "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, WEAK_LLM_PLAN)
    obj = ctl.run(ctl.create(
        ASCII_ON_SAMPLE_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    stored = [Check.from_dict(c) if isinstance(c, dict) else c
              for c in (obj.verification or {}).get("objective_checks") or []]
    assert not any(c.kind == "json_field" and c.args.get("key") in ("on", "sample")
                   for c in stored)
    assert ov.get("status") == "VERIFIED", ov
    assert obj.status == ObjectiveStatus.COMPLETED, obj.failure


def test_rw103_empty_object_still_fails_named_json_field(home, tmp_path):
    """Honesty bar: ``{}`` is still not VERIFIED when classic keys are named."""
    ws = tmp_path / "ws_rw103_empty"
    ws.mkdir()
    home.update(workspace=str(ws))
    ScriptedSession.script = [(_write_package(extra_summary="{}"), "DONE: wrote package")]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, WEAK_LLM_PLAN)
    obj = ctl.run(ctl.create(
        ASCII_ON_SAMPLE_GOAL,
        budget=Budget(tool_calls=20, retries=4),
        auto=True,
    ))
    ov = (obj.verification or {}).get("objective") or {}
    assert ov.get("status") != "VERIFIED"
    assert obj.status in (ObjectiveStatus.FAILED, ObjectiveStatus.NEEDS_USER)
