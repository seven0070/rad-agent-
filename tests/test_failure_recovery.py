"""Failure & recovery (mission §27): VALIDATION_FAILURE → recovery retry → VERIFIED;
persistent failure → NEEDS_USER/BLOCKED — NEVER a fake VERIFIED.

Verification semantics exercised here (from the Verifier, not assumed):
- a task is VERIFIED only when its machine checks pass AND no tool errored;
- a reply line containing digits is a "claim" that needs trusted-tool backing,
  so scripted replies below are written accordingly (like a real agent that says
  "DONE: wrote x" rather than quoting numbers it never measured).
"""
from __future__ import annotations

import pytest

from tests.test_control_plane import ScriptedSession, _ctl


def _vstat(obj):
    return ((obj.verification or {}).get("objective") or {}).get("status", "")


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w), auto=True)
    return w


def test_transient_failure_retried_then_verified(home, ws):
    """First attempt writes broken code (machine check fails → VALIDATION_FAILURE),
    recovery retries with explicit feedback, the second attempt fixes it and proves
    it with a shell test → task and objective VERIFIED."""
    plan = {"tasks": [{"id": "t1", "text": "write util.py", "checks": [
        {"kind": "file_contains", "args": {"path": "util.py", "text": "return a + b"}}]}]}
    ScriptedSession.script = [
        # attempt 1: wrong code
        ([("write_file", {"path": "util.py", "content": "def calc(a, b):\n    return a - b\n"})],
         "DONE: wrote util.py"),
        # attempt 2: fixed, and the model proves it (trusted tool backs its claim)
        ([("write_file", {"path": "util.py", "content": "def calc(a, b):\n    return a + b\n"}),
          ("run_shell", {"command": 'python3 -c "import util; assert util.calc(1, 2) == 3"'})],
         "DONE: fixed and tested"),
    ]
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.run(ctl.create("flaky task"))
    assert obj.status == "completed"
    assert _vstat(obj) == "VERIFIED"
    tasks = {t["text"]: t for t in ctl.store.load_tasks(obj.id)}
    t = tasks["write util.py"]
    assert t["attempts"] == 2
    assert t["status"] == "COMPLETED"
    assert t["verification"]["status"] == "VERIFIED"
    assert "RETRYING" in {h["to"] for h in t["history"]}
    assert (ws / "util.py").read_text(encoding="utf-8").endswith("return a + b\n")


def test_persistent_failure_never_verified(home, ws):
    """The model keeps claiming DONE but the machine check keeps failing: after the
    retry budget is spent the task ends FAILED/NEEDS_USER/BLOCKED and the objective
    stops at NEEDS_USER — the 'DONE' claims are never converted into VERIFIED."""
    plan = {"tasks": [{"id": "t1", "text": "write data.json", "checks": [
        {"kind": "shell_ok", "args": {"command":
            "python3 -c \"import json; d = json.load(open('data.json')); assert d['ok'] is True\""}}]}]}
    ScriptedSession.script = [
        ([("write_file", {"path": "data.json", "content": "not json"})], "DONE: wrote data.json")
        for _ in range(9)
    ]
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.run(ctl.create("always broken"))
    assert obj.status in ("needs_user", "failed")
    assert _vstat(obj) != "VERIFIED"
    tasks = list(ctl.store.load_tasks(obj.id))
    t = next(t for t in tasks if t["text"] == "write data.json")
    # recovery actually worked: the original attempt plus a repair task with its
    # own retries — several model attempts in total
    assert sum(t["attempts"] for t in tasks) >= 3
    assert any("Repair" in t["text"] for t in tasks)
    # nothing was ever marked completed or verified
    for t in tasks:
        assert t["status"] in ("FAILED", "NEEDS_USER", "BLOCKED")
        assert ((t["verification"] or {}).get("status") or "UNVERIFIED") != "VERIFIED"
    # the recorded verification shows the machine check that was never met
    tres = (t["verification"] or {}).get("results", [])
    assert any(r["ok"] is False and r.get("level") == "check" for r in tres)


def test_budget_exhaustion_is_needs_user_not_verified(home, ws):
    """Tool budget runs out mid-plan: the objective stops with the remaining tasks
    open (NEEDS_USER) and is never reported VERIFIED."""
    plan = {"tasks": [
        {"id": "t1", "text": "one", "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]},
        {"id": "t2", "text": "two", "depends_on": ["t1"],
         "checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]},
    ]}
    from rad.control.objectives import Budget
    ScriptedSession.script = [
        ([("write_file", {"path": "a.txt", "content": "1"})], "DONE: a"),
        ([("write_file", {"path": "b.txt", "content": "2"})], "DONE: b"),
    ]
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.create("budget stop", budget=Budget(tool_calls=1, model_calls=80, retries=0))
    obj = ctl.run(obj)
    assert obj.status in ("needs_user", "failed")
    assert _vstat(obj) != "VERIFIED"
    tasks = {t["text"]: t for t in ctl.store.load_tasks(obj.id)}
    assert tasks["one"]["status"] == "COMPLETED"
    assert tasks["two"]["status"] != "COMPLETED"


def test_tool_error_is_observed_and_retried(home, ws):
    """A tool that errors is observed (status=error, in the trace), fails the task's
    machine verification, and the recovery loop retries until the check passes."""
    plan = {"tasks": [{"id": "t1", "text": "read missing", "checks": [
        {"kind": "file_exists", "args": {"path": "ok.txt"}}]}]}
    ScriptedSession.script = [
        ([("read_file", {"path": "does_not_exist.txt"})], "DONE: tried to read"),
        ([("write_file", {"path": "ok.txt", "content": "ok"})], "DONE: wrote ok.txt"),
    ]
    ctl = _ctl(home, ScriptedSession, plan=plan)
    obj = ctl.run(ctl.create("tool error"))
    assert obj.status == "completed"
    assert _vstat(obj) == "VERIFIED"
    # the error was recorded in the observation trace of the real (re-hashed) task
    tid = {t["text"]: t["id"] for t in ctl.store.load_tasks(obj.id)}["read missing"]
    from rad.control.observer import Observer
    obs = Observer(ctl.store.dir(obj.id))
    bad = [o for o in obs.for_task(tid) if o.tool == "read_file"]
    assert bad and bad[0].status == "error"
    assert "does_not_exist" in (bad[0].output or "")
