"""GOLDEN END-TO-END (mission §26 + §28): the canonical objective through the whole
stack at the API level the desktop uses.

    Desktop → Jerry → Objective → Planner → Task Graph → Executor → Tools → Verification

Expected: VERIFIED. Then close (new process/Api instance) and reopen: objective,
artifacts, verification and provenance all still visible.

Plus restart/resume (§28): the sidecar dies mid-task (t2 left RUNNING on disk),
the desktop reopens, resume restores the interrupted task, completed tasks are
NOT re-run, and the objective still ends VERIFIED.

Note: task ids are re-hashed by the store on save, so tests key tasks by text.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from rad.api import Api
from rad.control.objectives import Budget
from tests.test_control_plane import ScriptedSession, _ctl

# ---------------------------------------------------------------- canonical objective

GOAL = (
    "Create a small Python project containing: one module (proj/mathutil.py with an "
    "add function), one pytest test (proj/test_math.py), and a README (proj/README.md)"
)

T1, T2, T3 = ("write module mathutil.py with add(a, b)",
              "write pytest test test_math.py",
              "write README.md for the project")

PLAN = {
    "tasks": [
        {"id": "t1", "text": T1, "depends_on": [],
         "checks": [
             {"kind": "file_exists", "args": {"path": "proj/mathutil.py"}},
             {"kind": "file_contains", "args": {"path": "proj/mathutil.py", "text": "def add(a, b):"}},
             {"kind": "shell_ok", "args": {"command":
                 "python3 -c \"import sys; sys.path.insert(0, 'proj'); from mathutil import add; assert add(1, 2) == 3; assert add(-5, 5) == 0\""}},
         ]},
        {"id": "t2", "text": T2, "depends_on": ["t1"],
         "checks": [
             {"kind": "file_exists", "args": {"path": "proj/test_math.py"}},
             {"kind": "file_contains", "args": {"path": "proj/test_math.py", "text": "def test_add"}},
             {"kind": "file_contains", "args": {"path": "proj/test_math.py", "text": "assert add(1, 2) == 3"}},
         ]},
        {"id": "t3", "text": T3, "depends_on": ["t1"],
         "checks": [
             {"kind": "file_exists", "args": {"path": "proj/README.md"}},
             {"kind": "file_contains", "args": {"path": "proj/README.md", "text": "mathutil"}},
         ]},
    ],
    "objective_checks": [
        {"kind": "shell_ok", "args": {"command":
            "python3 -c \"import sys; sys.path.insert(0, 'proj'); from mathutil import add; assert add(2, 3) == 5\""}},
        {"kind": "file_exists", "args": {"path": "proj/test_math.py"}},
        {"kind": "file_exists", "args": {"path": "proj/README.md"}},
    ],
}

GOLDEN_SCRIPT = [
    ([(
        "write_file",
        {"path": "proj/mathutil.py",
         "content": "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n"},
     )], "DONE: wrote proj/mathutil.py"),
    ([(
        "write_file",
        {"path": "proj/test_math.py",
         "content": "from mathutil import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n    assert add(0, 0) == 0\n"},
     )], "DONE: wrote proj/test_math.py"),
    ([(
        "write_file",
        {"path": "proj/README.md",
         "content": "# mathutil project\n\nA tiny `mathutil` module with an `add` function and a pytest test.\n"},
     )], "DONE: wrote proj/README.md"),
]


class CrashOnT2(ScriptedSession):
    """A ScriptedSession (so the executor's observing tool-runner is installed on it)
    in which the process dies mid-t2. SystemExit is a BaseException: the executor's
    `except Exception` recovery cannot swallow a real process death, so the on-disk
    state is exactly what a crash leaves."""

    def think(self, prompt):
        if T2 in prompt:
            raise SystemExit("simulated sidecar death mid-task")
        return super().think(prompt)


@pytest.fixture
def golden_home(tmp_path, monkeypatch):
    monkeypatch.setenv("RAD_HOME", str(tmp_path / "radhome"))
    from rad.home import RadHome
    home = RadHome(str(tmp_path / "radhome"))
    ws = tmp_path / "ws"
    ws.mkdir()
    home.update(workspace=str(ws), auto=True)
    return home


def _tasks_by_text(store, oid):
    return {t["text"]: t for t in store.load_tasks(oid)}


def _wait_finished(api, oid, timeout=60.0):
    d = None
    deadline = time.time() + timeout
    while time.time() < deadline:
        st, d = api.handle("GET", f"/v1/objectives/{oid}", {}, {})
        if d["status"] in ("completed", "failed", "needs_user", "cancelled"):
            return d
        time.sleep(0.1)
    raise TimeoutError(f"objective {oid} did not finish in {timeout}s: {d}")


# ---------------------------------------------------------------- the golden path

def test_golden_e2e_verified_and_survives_restart(golden_home):
    ScriptedSession.script = list(GOLDEN_SCRIPT)
    ScriptedSession.prompts = []
    ctl = _ctl(golden_home, ScriptedSession, plan=PLAN)
    api = Api(golden_home, controller_factory=lambda h: ctl)

    # 1 — desktop creates + starts through the API (background thread, 202)
    st, d = api.handle("POST", "/v1/objectives", {}, {"goal": GOAL, "run": True})
    assert st == 202 and d["started"] is True
    oid = d["id"]

    # 2 — control plane finishes: completed + machine-verified
    fin = _wait_finished(api, oid)
    assert fin["status"] == "completed"
    assert fin["verification"]["objective"]["status"] == "VERIFIED"

    # 3 — artifacts are real files, in the workspace
    ws = golden_home.workspace()
    code = (ws / "proj" / "mathutil.py").read_text(encoding="utf-8")
    assert "def add(a, b):" in code
    assert (ws / "proj" / "test_math.py").exists()
    assert (ws / "proj" / "README.md").exists()

    # 4 — plan / trace / recovery / artifacts / observations endpoints all real
    st, plan = api.handle("GET", f"/v1/objectives/{oid}/plan", {}, {})
    assert {t["text"] for t in plan["tasks"]} == {T1, T2, T3}
    st, tr = api.handle("GET", f"/v1/objectives/{oid}/trace", {}, {})
    assert {t["status"] for t in tr["tasks"]} == {"COMPLETED"}
    st, rec = api.handle("GET", f"/v1/objectives/{oid}/recovery", {}, {})
    assert rec["failed_tasks"] == []
    st, arts = api.handle("GET", f"/v1/objectives/{oid}/artifacts", {}, {})
    names = {Path(a["location"]).name for a in arts["artifacts"]}
    assert {"mathutil.py", "test_math.py", "README.md"} <= names
    st, obsv = api.handle("GET", f"/v1/objectives/{oid}/observations", {}, {})
    assert any(o["tool"] == "write_file" for o in obsv["observations"])

    # 5 — close the desktop (this Api + its controller go away) and reopen fresh
    del api
    api2 = Api(golden_home, controller_factory=lambda h: _ctl(golden_home, ScriptedSession, plan=PLAN))

    st, objs = api2.handle("GET", "/v1/objectives", {}, {})
    row = next(o for o in objs["objectives"] if o["id"] == oid)
    assert row["status"] == "completed" and row["verification"] == "VERIFIED"
    assert row["tasks_total"] == 3 and row["tasks_completed"] == 3 and row["tasks_failed"] == 0

    st, full = api2.handle("GET", f"/v1/objectives/{oid}", {}, {})
    assert full["verification"]["objective"]["status"] == "VERIFIED"
    assert sum(1 for t in full["tasks"] if t["status"] == "COMPLETED") == 3

    st, arts2 = api2.handle("GET", f"/v1/objectives/{oid}/artifacts", {}, {})
    assert arts2["count"] >= 3

    st, content = api2.handle("GET", f"/v1/objectives/{oid}/artifact-content",
                              {"ref": "mathutil.py"}, {})
    assert "def add" in content["preview"]

    # 6 — provenance ("rad why") visible after restart
    st, why = api2.handle("GET", f"/v1/objectives/{oid}/why", {"q": "mathutil.py"}, {})
    chain = why["artifact"]
    assert chain["artifact"]["location"].endswith("mathutil.py")
    assert chain["task"]["id"] in {t["id"] for t in full["tasks"]}
    assert chain["action"]["tool"] == "write_file"
    assert any(v["location"].endswith("mathutil.py") for v in chain["versions"])

    # 7 — usage/status reflect the real run
    st, usage = api2.handle("GET", "/v1/usage", {}, {})
    assert usage["count"] == 1
    # model-driven tools: exactly the 3 write_file calls
    assert usage["tool_calls"] == 3
    # 3 task prompts (planning/verification LLM calls are not task budget)
    assert usage["model_calls"] == 3


def test_golden_e2e_restart_resume_no_rerun(golden_home):
    """Sidecar dies mid-t2 → t2 left RUNNING on disk → reopen → resume:
    t1 is NOT re-run, t2 is crash-restored, run continues to VERIFIED."""
    ScriptedSession.script = list(GOLDEN_SCRIPT)
    ScriptedSession.prompts = []
    ctl = _ctl(golden_home, CrashOnT2, plan=PLAN)

    # phase 1: foreground run, process death mid-t2
    obj = ctl.create(GOAL, budget=Budget(tool_calls=40, model_calls=80, retries=6,
                                         seconds=1800))
    with pytest.raises(SystemExit):
        ctl.run(obj)

    tasks = _tasks_by_text(ctl.store, obj.id)
    assert tasks[T1]["status"] == "COMPLETED" and tasks[T1]["attempts"] == 1
    # checkpoints persist between batches, so a kill mid-think leaves t2 at its
    # pre-attempt state (PENDING) — or RUNNING if the checkpoint caught mid-task
    assert tasks[T2]["status"] in ("PENDING", "RUNNING")
    assert tasks[T3]["status"] == "PENDING"

    # exercise the documented crash-restore path: a checkpoint caught t2 mid-task,
    # so it is RUNNING on disk when the desktop reopens
    t2row = dict(tasks[T2]); t2row["status"] = "RUNNING"
    rows = {t["text"]: dict(t) for t in ctl.store.load_tasks(obj.id)}
    rows[T2] = t2row
    ctl.store.save_tasks(obj.id, list(rows.values()))

    # phase 2: desktop reopens → new controller (crash recovery) → resume
    ScriptedSession.script = [GOLDEN_SCRIPT[1], GOLDEN_SCRIPT[2]]
    ctl2 = _ctl(golden_home, ScriptedSession, plan=PLAN)
    api2 = Api(golden_home, controller_factory=lambda h: ctl2)
    st, r = api2.handle("POST", f"/v1/objectives/{obj.id}/resume", {}, {})
    assert st == 202
    fin = _wait_finished(api2, obj.id)
    assert fin["status"] == "completed"
    assert fin["verification"]["objective"]["status"] == "VERIFIED"

    tasks2 = _tasks_by_text(ctl2.store, obj.id)
    # t1 completed before the crash → not re-run
    assert tasks2[T1]["attempts"] == 1
    # and its work was performed exactly once across the whole objective
    from rad.control.observer import Observer
    obs = Observer(ctl2.store.dir(obj.id)).observations()
    t1_writes = [o for o in obs if o.tool == "write_file"
                 and str((o.args or {}).get("path", "")).endswith("mathutil.py")]
    assert len(t1_writes) == 1
    # t2 got the crash-restore history and then finished
    assert any(h.get("note") == "interrupted" for h in tasks2[T2].get("history", []))
    assert tasks2[T2]["status"] == "COMPLETED"
    assert tasks2[T3]["status"] == "COMPLETED"
    # the crash was detected and recorded as an event
    from rad.control.events import EventLog
    evs = list(EventLog(ctl2.store.events_path(obj.id)).read(kind="CRASH_DETECTED"))
    assert evs and evs[-1].data.get("tasks") == 1


def test_golden_planner_fallback_without_brain_never_fakes_verified(golden_home):
    """No LLM at all → fallback planner; whatever the outcome, a VERIFIED verdict is
    only possible if the files it claims actually exist."""
    ScriptedSession.script = list(GOLDEN_SCRIPT)
    ctl = _ctl(golden_home, ScriptedSession, plan=None, llm=None)
    api = Api(golden_home, controller_factory=lambda h: ctl)
    st, d = api.handle("POST", "/v1/objectives", {}, {"goal": GOAL, "run": True})
    assert st == 202
    fin = _wait_finished(api, d["id"])
    vstat = ((fin.get("verification") or {}).get("objective") or {}).get("status")
    if vstat == "VERIFIED":
        ws = golden_home.workspace()
        for f in ("mathutil.py", "test_math.py", "README.md"):
            assert (ws / "proj" / f).exists()
