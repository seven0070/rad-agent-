"""v0.4.2 ASCII-tree package_dir (theme-1 follow-up / Gen3 theme 3 slice A).

RW-073 live NIM (v0.4.1): task checks were path-aligned under `text_analyzer/`;
merged objective inferred checks stayed bare (`summary.json`, `input.txt`,
`python3 test_analyzer.py`) because `infer_package_dir` returned None for an
ASCII-tree goal (`text_analyzer/` + `├── file`).

Class A confirmed: an ASCII / box-drawing tree is a named package layout.
RAD should join inferred (and LLM root-only) objective checks the same way
as `under pkg/` / `pkg/{…}` / two-or-more `pkg/foo` mentions.

Does not claim live 11B text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. F-17 / F-26 preserved. Theme-2 contracts preserved.
"""
from __future__ import annotations

import json

from rad import __version__
from rad.control.codingloop import infer_coding_checks, infer_package_dir
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_path_aligned_checks import (
    PREFIXED_GOAL,
    ROOT_CHECK_PLAN,
    RW069_GOAL,
    WORD_COUNTER_GOAL,
)

RW073_ASCII_GOAL = (
    "Create a text analyzer package:\n"
    "\n"
    "text_analyzer/\n"
    "├── analyzer.py   (stdlib)\n"
    "├── input.txt     (exact 3 lines)\n"
    "├── summary.json  (accurate lines/words/characters)\n"
    "├── test_analyzer.py\n"
    "└── README.md\n"
    "\n"
    "Exact 3-line input.txt. Run the tests.\n"
)

ASCII_PIPE_GOAL = (
    "text_analyzer/\n"
    "|-- analyzer.py\n"
    "|-- input.txt (exact 3 lines)\n"
    "`-- summary.json\n"
)

DASH_LIST_GOAL = (
    "Create files under a folder named text_analyzer then:\n"
    "- analyzer.py\n"
    "- input.txt (exact 3 lines)\n"
    "- summary.json\n"
    "- test_analyzer.py\n"
    "- README.md\n"
)

DOCS_TREE_GOAL = (
    "docs/\n"
    "├── README.md\n"
    "├── GUIDE.md\n"
    "└── NOTES.md\n"
)

SINGLE_CHILD_TREE_GOAL = (
    "text_analyzer/\n"
    "└── analyzer.py\n"
)

RW073_LLM_PLAN = {
    "tasks": [{
        "id": "t1",
        "text": "Create text_analyzer directory and input.txt with exact 3 lines",
        "depends_on": [],
        "checks": [
            {"kind": "file_exists", "args": {"path": "text_analyzer/input.txt"}},
            {"kind": "file_line_count", "args": {"path": "text_analyzer/input.txt", "n": 3}},
        ],
    }],
    "objective_checks": [
        {"kind": "file_min_bytes", "args": {"path": "text_analyzer/README.md", "n": 100}},
    ],
}


def _plan_llm(plan):
    def llm(prompt: str) -> str:
        if "Decompose the goal" in prompt:
            return json.dumps(plan)
        return "YES"
    return llm


def test_ascii_tree_package_dir_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_infer_package_dir_ascii_tree_box_drawing():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"


def test_infer_package_dir_ascii_pipe_tree():
    assert infer_package_dir(ASCII_PIPE_GOAL) == "text_analyzer/"


def test_infer_package_dir_dash_list_is_not_a_tree():
    assert infer_package_dir(DASH_LIST_GOAL) is None


def test_infer_package_dir_docs_tree_is_skipped():
    assert infer_package_dir(DOCS_TREE_GOAL) is None


def test_infer_package_dir_single_tree_child_is_not_a_layout():
    assert infer_package_dir(SINGLE_CHILD_TREE_GOAL) is None


def test_infer_package_dir_existing_forms_unchanged():
    assert infer_package_dir(RW069_GOAL) == "text_analyzer/"
    assert infer_package_dir(PREFIXED_GOAL) == "text_analyzer/"
    assert infer_package_dir(WORD_COUNTER_GOAL) is None
    assert infer_package_dir(
        "pkg/stats.py is broken: `python3 tests/check_stats.py` fails. Read SPEC.md."
    ) is None
    assert infer_package_dir(
        "From sources/field_report.txt produce answer.md (a short evidence-based summary)"
    ) is None


def test_infer_coding_checks_ascii_tree_joins_bare_paths():
    checks = infer_coding_checks(RW073_ASCII_GOAL)
    json_paths = [c.args.get("path") for c in checks if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
    lines = [c for c in checks if c.kind == "file_line_count"]
    assert lines
    assert lines[0].args.get("path") == "text_analyzer/input.txt"
    assert int(lines[0].args.get("n")) == 3
    assert any(
        c.kind == "shell_ok" and c.args.get("command") == "python3 text_analyzer/test_analyzer.py"
        for c in checks
    )
    assert not any(
        (c.args.get("path") in ("summary.json", "input.txt"))
        or c.args.get("command") == "python3 test_analyzer.py"
        for c in checks
    )


def test_llm_ascii_tree_merges_package_objective_contracts(tmp_path):
    """RW-073 shape: LLM task checks already prefixed; inferred contracts must join."""
    plan = Planner(_plan_llm(RW073_LLM_PLAN), str(tmp_path)).plan(
        Objective.new(RW073_ASCII_GOAL)
    )
    assert plan["source"] == "llm"
    obj_kinds = {(c.kind, c.args.get("path") or c.args.get("command"))
                 for c in plan["objective_checks"]}
    assert ("file_min_bytes", "text_analyzer/README.md") in obj_kinds
    assert ("json_valid", "text_analyzer/summary.json") in obj_kinds
    assert ("file_line_count", "text_analyzer/input.txt") in obj_kinds
    assert ("shell_ok", "python3 text_analyzer/test_analyzer.py") in obj_kinds
    assert ("json_valid", "summary.json") not in obj_kinds
    assert ("file_line_count", "input.txt") not in obj_kinds


def test_llm_root_checks_on_ascii_tree_are_joined(tmp_path):
    plan = Planner(_plan_llm(ROOT_CHECK_PLAN), str(tmp_path)).plan(
        Objective.new(RW073_ASCII_GOAL)
    )
    task_paths = [c.args.get("path") for t in plan["graph"].tasks.values() for c in t.checks]
    obj_paths = [c.args.get("path") for c in plan["objective_checks"]]
    assert "text_analyzer/input.txt" in task_paths
    assert "text_analyzer/summary.json" in task_paths
    assert "input.txt" not in task_paths
    assert "summary.json" not in task_paths
    assert "text_analyzer/input.txt" in obj_paths
    assert "text_analyzer/summary.json" in obj_paths


def test_fallback_tasks_stay_checkless_f17_ascii_tree(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new(RW073_ASCII_GOAL))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())
    json_paths = [c.args.get("path") for c in res["objective_checks"] if c.kind == "json_valid"]
    assert json_paths == ["text_analyzer/summary.json"]
