"""Phase 1c: labeled triage corpus mined from objectives history (offline)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rad.triage_data import export, mine, stats  # noqa: E402


def _write_objective(home, oid, goal, events, tasks=None, status="completed",
                     verification=None):
    d = home.root / "objectives" / oid
    d.mkdir(parents=True, exist_ok=True)
    obj = {
        "id": oid,
        "goal": goal,
        "status": status,
        "verification": verification or {},
        "success_criteria": [],
        "constraints": [],
        "priority": "normal",
        "budget": {},
        "usage": {},
        "created": 1790000000.0,
        "updated": 1790000100.0,
    }
    (d / "objective.json").write_text(json.dumps(obj), encoding="utf-8")
    (d / "tasks.json").write_text(json.dumps(tasks or []), encoding="utf-8")
    with open(d / "events.jsonl", "w", encoding="utf-8") as f:
        for i, e in enumerate(events):
            row = {
                "kind": e["kind"],
                "at": e.get("at", 1790000000.0 + i),
                "objective_id": oid,
                "task_id": e.get("task_id", ""),
                "data": e.get("data", {}),
                "seq": i,
            }
            f.write(json.dumps(row) + "\n")


def _task(tid, text, **kw):
    base = {
        "id": tid,
        "objective_id": "obj_x",
        "text": text,
        "status": "COMPLETED",
        "verification": {"status": "VERIFIED", "results": []},
        "failure_class": "",
        "attempts": 1,
        "depends_on": [],
        "checks": [],
        "priority": "normal",
        "agent": "",
        "optional": False,
        "active": True,
        "created": 1790000000.0,
        "started": 1790000001.0,
        "finished": 1790000002.0,
        "reply": "",
        "note": "",
        "alternatives": [],
        "on_failure": [],
        "observations": [],
        "artifacts": [],
        "history": [],
        "plan_version": 1,
        "max_attempts": 3,
        "verified_at": None,
    }
    base.update(kw)
    return base


# ---------------------------------------------------------------- mine

def test_empty_home_mines_nothing(home):
    assert mine(home) == []


def test_completed_verified_objective_is_auto(home):
    _write_objective(
        home, "obj_auto01",
        "List all markdown files under docs and write a summary index.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}},
            {"kind": "TASK_CREATED", "task_id": "t_1", "data": {"text": "scan docs"}},
            {"kind": "TASK_COMPLETED", "task_id": "t_1", "data": {}},
            {"kind": "VERIFICATION_RESULT", "task_id": "t_1",
             "data": {"status": "VERIFIED"}},
            {"kind": "VERIFICATION_RESULT",
             "data": {"scope": "objective", "status": "VERIFIED"}},
            {"kind": "OBJECTIVE_COMPLETED", "data": {}},
        ],
        tasks=[_task("t_1", "Scan docs directory for markdown files and count them.")],
        status="completed",
        verification={"status": "VERIFIED"},
    )
    rows = mine(home)
    labels = {(r["kind"], r["label"]) for r in rows}
    assert ("objective", "auto") in labels
    assert ("task", "auto") in labels
    assert all(r["label"] in ("auto", "escalate") for r in rows)
    assert all(r["weight"] > 0 for r in rows)


def test_security_denied_escalates_objective_and_task(home):
    _write_objective(
        home, "obj_sec001",
        "Run a shell command that rewrites the package config in place now.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}},
            {"kind": "TASK_CREATED", "task_id": "t_1", "data": {"text": "rewrite config"}},
            {"kind": "SECURITY_DENIED", "task_id": "t_1",
             "data": {"tool": "run_shell", "status": "declined",
                      "reason": "user declined", "policy": "ASK"}},
            {"kind": "OBJECTIVE_STATUS", "data": {"status": "needs_user"}},
        ],
        tasks=[_task("t_1", "Rewrite the package config via shell without backup.",
                     status="RETRYING", failure_class="PERMISSION_FAILURE",
                     verification={"status": "FAILED", "results": []})],
        status="needs_user",
    )
    rows = mine(home)
    esc = [r for r in rows if r["label"] == "escalate"]
    assert esc, "expected escalate rows"
    obj_rows = [r for r in esc if r["kind"] == "objective"]
    task_rows = [r for r in esc if r["kind"] == "task"]
    assert obj_rows and any("SECURITY_DENIED" in e for e in obj_rows[0]["evidence"])
    assert task_rows
    assert not any(r["label"] == "auto" for r in rows)


def test_needs_user_objective_without_events_still_escalates(home):
    _write_objective(
        home, "obj_need01",
        "Adjudicate whether the pending refund request should be issued today.",
        events=[{"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}}],
        tasks=[],
        status="needs_user",
    )
    rows = mine(home)
    assert len(rows) == 1
    assert rows[0]["label"] == "escalate"
    assert rows[0]["kind"] == "objective"


def test_budget_exceeded_escalates(home):
    _write_objective(
        home, "obj_bud001",
        "Keep iterating on the failing integration test until the suite is green.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}},
            {"kind": "BUDGET_EXCEEDED", "data": {"reason": "retry budget 2 exhausted"}},
        ],
        tasks=[],
        status="completed",
        verification={"status": "VERIFIED"},
    )
    rows = mine(home)
    assert rows and rows[0]["label"] == "escalate"
    assert any(e.startswith("BUDGET_EXCEEDED") for e in rows[0]["evidence"])


def test_ask_user_strategy_escalates(home):
    _write_objective(
        home, "obj_ask001",
        "Decide which of two conflicting schema migrations to apply next hour.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}},
            {"kind": "RECOVERY_DECISION", "task_id": "t_1",
             "data": {"strategy": "ask_user", "failure_class": "PLANNING",
                      "reason": "ambiguous requirements"}},
        ],
        tasks=[],
        status="needs_user",
    )
    rows = mine(home)
    assert any(r["label"] == "escalate" and any("ask_user" in e for e in r["evidence"])
               for r in rows)


def test_retry_recovery_with_final_verified_is_auto(home):
    """retry/repair/replan alone must NOT force escalate — engine handled it."""
    _write_objective(
        home, "obj_ret001",
        "Generate the weekly changelog fragment from the last twenty commits.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}},
            {"kind": "TASK_CREATED", "task_id": "t_1", "data": {"text": "build changelog"}},
            {"kind": "TASK_FAILED", "task_id": "t_1",
             "data": {"verification": "FAILED", "summary": "check failed"}},
            {"kind": "RECOVERY_DECISION", "task_id": "t_1",
             "data": {"strategy": "retry_with_hint", "failure_class": "VALIDATION_FAILURE",
                      "reason": "verification failed"}},
            {"kind": "VERIFICATION_RESULT", "task_id": "t_1",
             "data": {"status": "VERIFIED"}},
            {"kind": "VERIFICATION_RESULT",
             "data": {"scope": "objective", "status": "VERIFIED"}},
            {"kind": "OBJECTIVE_COMPLETED", "data": {}},
        ],
        tasks=[_task("t_1", "Build a changelog fragment from git log output.")],
        status="completed",
        verification={"status": "VERIFIED"},
    )
    rows = mine(home)
    assert rows, "expected rows"
    assert all(r["label"] == "auto" for r in rows)


def test_running_unverified_is_skipped(home):
    _write_objective(
        home, "obj_run001",
        "Monitor the staging deploy pipeline and report the first failure.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {"goal": "x"}},
            {"kind": "TASK_CREATED", "task_id": "t_1", "data": {"text": "watch pipeline"}},
        ],
        tasks=[_task("t_1", "Watch the staging pipeline for failures.",
                     status="PENDING", verification={})],
        status="running",
    )
    assert mine(home) == []


def test_short_goal_and_task_text_skipped(home):
    _write_objective(
        home, "obj_shrt01",
        "hi",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {}},
            {"kind": "VERIFICATION_RESULT",
             "data": {"scope": "objective", "status": "VERIFIED"}},
            {"kind": "OBJECTIVE_COMPLETED", "data": {}},
        ],
        tasks=[_task("t_1", "ok")],
        status="completed",
        verification={"status": "VERIFIED"},
    )
    rows = mine(home)
    assert all(len(r["text"]) >= 10 for r in rows)
    # task text "ok" must never appear
    assert not any(r["text"] == "ok" for r in rows)


def test_dedupe_same_text_same_label(home):
    for i in (1, 2):
        _write_objective(
            home, f"obj_dup00{i}",
            "Duplicate goal text used twice for dedupe coverage check.",
            events=[
                {"kind": "OBJECTIVE_CREATED", "data": {}},
                {"kind": "SECURITY_DENIED", "data": {"tool": "write_file"}},
            ],
            tasks=[],
            status="needs_user",
        )
    rows = mine(home)
    goals = [r["text"] for r in rows if r["kind"] == "objective"]
    assert len(goals) == len(set(goals))


# ---------------------------------------------------------------- stats / export

def test_stats_shape(home):
    _write_objective(
        home, "obj_st0001",
        "Summarize the acceptance gate JSON into a one-page operator note.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {}},
            {"kind": "SECURITY_DENIED", "data": {"tool": "run_shell"}},
        ],
        tasks=[],
        status="needs_user",
    )
    s = stats(home=home)
    assert s["total"] == 1 and s["escalate"] == 1 and s["auto"] == 0
    assert s["objective"] == 1


def test_export_writes_jsonl(home, tmp_path):
    _write_objective(
        home, "obj_ex0001",
        "Export a labeled triage example so the file has one real row.",
        events=[
            {"kind": "OBJECTIVE_CREATED", "data": {}},
            {"kind": "NEEDS_USER", "data": {}},
        ],
        tasks=[],
        status="needs_user",
    )
    dest = tmp_path / "triage-train.jsonl"
    out = export(home, str(dest))
    assert out == str(dest)
    lines = dest.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["label"] == "escalate" and row["kind"] == "objective"
    assert set(row) >= {"text", "label", "weight", "kind", "source",
                        "objective_id", "task_id", "evidence"}


def test_export_default_under_home_corpus(home):
    _write_objective(
        home, "obj_ex0002",
        "Default export path should land under the home corpus directory.",
        events=[{"kind": "OBJECTIVE_CREATED", "data": {}}],
        tasks=[],
        status="running",
    )
    out = export(home)
    assert out.startswith(str(home.root / "corpus"))
    assert out.endswith("triage-train.jsonl")
