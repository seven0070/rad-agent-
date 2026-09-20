"""Desktop-facing API endpoints: artifacts, artifact-content, plan, recovery, live,
observations, usage, memory, run. Plus the safety properties the desktop relies on
(registered-artifacts-only content, redaction, no shell, budgets untouched)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from rad.api import Api, ApiError


# ---------------------------------------------------------------- fixtures


def _ctl_scripted(home, scripted, plan=None, llm=None):
    from rad.control.controller import Controller
    from tests.test_control_plane import _plan_llm
    return Controller(home, session_factory=scripted,
                      llm=llm or (_plan_llm(plan) if plan else None), quiet=True)


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


@pytest.fixture
def scripted():
    from tests.test_control_plane import ScriptedSession
    ScriptedSession.script = []
    ScriptedSession.prompts = []
    return ScriptedSession


def _run_small_objective(home, scripted, plan=None):
    plan = plan or {"tasks": [
        {"id": "t1", "text": "write app.py", "depends_on": [],
         "checks": [{"kind": "file_exists", "args": {"path": "app.py"}}]},
        {"id": "t2", "text": "write README", "depends_on": ["t1"],
         "checks": [{"kind": "file_contains", "args": {"path": "README.md", "text": "Project"}}]},
    ]}
    scripted.script = [
        ([("write_file", {"path": "app.py", "content": "def f():\n    return 1\n"})], "DONE: app"),
        ([("write_file", {"path": "README.md", "content": "# Project\n"})], "DONE: readme"),
    ]
    ctl = _ctl_scripted(home, scripted, plan)
    obj = ctl.run(ctl.create("small objective"))
    return ctl, obj


# ---------------------------------------------------------------- artifacts


def test_artifacts_list(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/artifacts", {}, {})
    assert st == 200
    locs = {a["location"] for a in d["artifacts"]}
    names = {Path(l).name for l in locs}
    assert "app.py" in names and "README.md" in names
    for a in d["artifacts"]:
        assert a["objective_id"] == obj.id
        assert a["sha256"] and len(a["sha256"]) == 64
        assert a["version"] >= 1 and a["task_id"]


def test_artifact_content_registered_only(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    # registered → ok
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/artifact-content", {"ref": "app.py"}, {})
    assert st == 200
    assert "def f" in d["preview"]
    assert d["sha256"]
    # not registered → 404, even if the file exists on disk
    (ws / "secret.txt").write_text("top secret", encoding="utf-8")
    with pytest.raises(ApiError) as ei:
        api.handle("GET", f"/v1/objectives/{obj.id}/artifact-content", {"ref": "secret.txt"}, {})
    assert ei.value.status == 404
    # raw absolute paths are not a ref
    with pytest.raises(ApiError) as ei2:
        api.handle("GET", f"/v1/objectives/{obj.id}/artifact-content", {"ref": "/etc/passwd"}, {})
    assert ei2.value.status == 404


def test_artifact_content_redacts_secrets(home, ws, scripted):
    (ws / "creds.py").write_text(
        "API_KEY = 'sk-abcDEF1234567890xyz'\n", encoding="utf-8")
    scripted.script = [
        ([("write_file", {"path": "creds.py",
                          "content": "API_KEY = 'sk-abcDEF1234567890xyz'\n"})], "DONE"),
    ]
    plan = {"tasks": [{"id": "t1", "text": "write creds", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "creds.py"}}]}]}
    ctl = _ctl_scripted(home, scripted, plan)
    obj = ctl.run(ctl.create("write creds"))
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/artifact-content", {"ref": "creds.py"}, {})
    assert st == 200
    assert "sk-abcDEF1234567890xyz" not in d["preview"]
    assert "REDACTED" in d["preview"]


def test_artifact_content_rejects_non_text_and_oversize(home, ws, scripted):
    scripted.script = [
        ([("write_file", {"path": "bin.dat", "content": "x"})], "DONE: wrote placeholder"),
    ]
    plan = {"tasks": [{"id": "t1", "text": "write bin", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "bin.dat"}}]}]}
    ctl = _ctl_scripted(home, scripted, plan)
    obj = ctl.run(ctl.create("write bin"))
    # overwrite with non-UTF-8 bytes after the fact (artifact registry keeps the entry)
    (ws / "bin.dat").write_bytes(b"\xff\xfe\x00\x01binary")
    api = Api(home)
    with pytest.raises(ApiError) as ei:
        api.handle("GET", f"/v1/objectives/{obj.id}/artifact-content", {"ref": "bin.dat"}, {})
    assert ei.value.status == 415


def test_artifact_content_rejects_outside_workspace(home, ws, tmp_path, scripted):
    """A registered artifact whose location leaves workspace/home is refused (403)."""
    from rad.control.observer import Observer
    ctl = _ctl_scripted(home, scripted)
    obj = ctl.create("outside artifact host")
    outside = home.root.parent / "outside_artifact.py"
    outside.write_text("x=1", encoding="utf-8")
    reg_path = Observer(ctl.store.dir(obj.id)).artifacts_path
    reg = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {}
    reg["art_outside001"] = {
        "id": "art_outside001", "objective_id": obj.id, "task_id": "t1", "type": "file",
        "location": str(outside), "creator": "write_file", "sha256": "0" * 64,
        "size": 4, "version": 1, "parent": None, "at": 0.0,
    }
    reg_path.write_text(json.dumps(reg), encoding="utf-8")
    api = Api(home, controller_factory=lambda h: ctl)
    with pytest.raises(ApiError) as ei:
        api.handle("GET", f"/v1/objectives/{obj.id}/artifact-content",
                   {"ref": "art_outside001"}, {})
    assert ei.value.status == 403


# ---------------------------------------------------------------- plan / recovery / live


def test_plan_view(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/plan", {}, {})
    assert st == 200
    assert d["plan_version"] >= 1
    by_text = {t["text"]: t for t in d["tasks"]}
    assert len(d["tasks"]) == 2
    app = by_text["write app.py"]
    readme = by_text["write README"]
    assert readme["depends_on"] == [app["id"]]
    assert app["status"] == "COMPLETED" and readme["status"] == "COMPLETED"
    assert d["replans"] == []


def test_recovery_view_shape(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/recovery", {}, {})
    assert st == 200
    assert d["retries_used"] == obj.usage.retries
    assert d["retry_budget"] == obj.budget.retries
    assert isinstance(d["decisions"], list) and isinstance(d["failed_tasks"], list)


def test_live_view(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/live", {}, {})
    assert st == 200
    assert d["status"] == obj.status
    assert d["tasks"]["total"] == 2
    assert d["tasks"]["by_status"]["COMPLETED"] == 2
    assert d["current_task"] is None
    assert d["artifacts"] == 2
    assert d["verification"] == "VERIFIED"
    acc = d["budget"]["account"]["tool_calls"]
    assert acc["limit"] == 60 and acc["used"] > 0 and 0 < acc["remaining"] < acc["limit"]
    assert isinstance(d["events"], list) and len(d["events"]) >= 2


def test_live_view_events_pagination(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/live", {}, {})
    assert st == 200
    evs = d["events"]
    assert evs  # a finished objective has events
    seq = evs[-1]["seq"]
    st2, d2 = api.handle("GET", f"/v1/objectives/{obj.id}/live", {"since_seq": str(seq)}, {})
    assert d2["events"] == []


def test_observations_endpoint(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", f"/v1/objectives/{obj.id}/observations", {}, {})
    assert st == 200
    assert d["count"] >= 2
    for o in d["observations"]:
        assert o["tool"] == "write_file"
        assert o["status"] in ("success", "error", "blocked", "declined")
        assert "sk-" not in o["output"] or "REDACTED" in o["output"]
    # task filter
    tid = d["observations"][0]["task_id"]
    st2, d2 = api.handle("GET", f"/v1/objectives/{obj.id}/observations", {"task": tid}, {})
    assert st2 == 200
    assert all(o["task_id"] == tid for o in d2["observations"])


# ---------------------------------------------------------------- usage / memory


def test_usage_rollup(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", "/v1/usage", {}, {})
    assert st == 200
    assert d["count"] == 1
    assert d["tool_calls"] >= 2
    assert d["model_calls"] >= 2
    assert d["objectives"][0]["id"] == obj.id
    assert "note" in d and "429" in d["note"]  # remaining quota is NOT invented


def test_memory_list(home, ws):
    from rad.memory import Memory
    mem = Memory(home)
    mem.add("semantic", "user prefers pytest", origin="USER_PROVIDED", source="api")
    mem.add("episodic", "did a thing", origin="OBSERVED", source="t")
    api = Api(home)
    st, d = api.handle("GET", "/v1/memory", {}, {})
    assert st == 200
    assert any(m["text"] == "user prefers pytest" for m in d["memories"]["semantic"])
    st2, d2 = api.handle("GET", "/v1/memory", {"layer": "episodic"}, {})
    assert set(d2["memories"].keys()) == {"episodic"}


# ---------------------------------------------------------------- run endpoint / summaries


def test_run_endpoint_gated_by_confirmation(home, ws, scripted):
    """auto=false and STANDARD confirmation → 409 (HTTP cannot answer prompts)."""
    ctl = _ctl_scripted(home, scripted)
    obj = ctl.create("pending thing")
    api = Api(home)
    with pytest.raises(ApiError) as ei:
        api.handle("POST", f"/v1/objectives/{obj.id}/run", {}, {})
    assert ei.value.status == 409

    # config auto=true → starts (Controller.run plans a PENDING objective)
    home.update(auto=True)
    scripted.script = [([("write_file", {"path": "a.txt", "content": "1"})], "DONE")]
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    ctl2 = _ctl_scripted(home, scripted, plan)
    api2 = Api(home, controller_factory=lambda h: ctl2)
    st, d = api2.handle("POST", f"/v1/objectives/{obj.id}/run", {}, {})
    assert st == 202 and d["status"] == "starting"
    # wait for the background thread
    for _ in range(100):
        import time
        time.sleep(0.05)
        o = ctl2.store.load(obj.id)
        if o.status in ("completed", "failed", "needs_user"):
            break
    o = ctl2.store.load(obj.id)
    assert o.status == "completed"


def test_objective_summary_includes_task_counts(home, ws, scripted):
    _, obj = _run_small_objective(home, scripted)
    api = Api(home)
    st, d = api.handle("GET", "/v1/objectives", {}, {})
    assert st == 200
    row = next(o for o in d["objectives"] if o["id"] == obj.id)
    assert row["tasks_total"] == 2
    assert row["tasks_completed"] == 2
    assert row["tasks_failed"] == 0


def test_api_still_has_no_shell_or_tool_routes(home, ws):
    api = Api(home)
    for method, path in (("POST", "/v1/shell"), ("POST", "/v1/tools"),
                         ("POST", "/v1/run_tool"), ("GET", "/v1/exec")):
        with pytest.raises(ApiError) as ei:
            api.handle(method, path, {}, {"command": "id", "name": "x"})
        assert ei.value.status == 404
