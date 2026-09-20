"""Phase 10: skill manifests wired into the policy gate, and the local HTTP API."""
import json
import os
import threading
import urllib.error
import urllib.request

import pytest

from rad import skills as SK
from rad.policy import CAP_MCP, CAP_READ, CAP_SHELL, CAP_WRITE, Policy
from rad.tools import ToolCtx, run_tool


# ---------------------------------------------------------------- skill manifests

def _connect(home, name="fsx", tools=("read_file", "write_file", "run_command", "list_dir")):
    reg = home.skills()
    reg[name] = {"name": name, "transport": "stdio", "command": ["python3", "-m", "x"], "env": {}, "url": None,
                 "tools": [{"name": t, "description": t, "schema": {"type": "object"}} for t in tools], "added": 0, "link": "x"}
    home.save_skills(reg)


def test_infer_and_build_manifest(home):
    assert SK.infer_capability("write_file") == CAP_WRITE and SK.infer_capability("run_command") == CAP_SHELL
    assert SK.infer_capability("read_file") == CAP_READ and SK.infer_capability("frobnicate") == CAP_MCP
    _connect(home)
    m = SK.ensure_manifest(home, "fsx")
    assert m["tools"]["write_file"] == [CAP_WRITE] and m["tools"]["list_dir"] == [CAP_READ]
    assert set(m["capabilities"]) == {CAP_READ, CAP_WRITE, CAP_SHELL}
    assert m["approval"] == "ask" and not m["declared"] and m["trust"] == "local"
    assert SK.manifest_path(home, "fsx").exists()
    rows = SK.audit(home)
    assert rows[0]["flags"] and any("inferred" in f for f in rows[0]["flags"])


def test_drift_downgrades_allow_to_ask(home):
    _connect(home, tools=("read_file",))
    SK.approve(home, "fsx", "allow")
    assert SK.ensure_manifest(home, "fsx")["approval"] == "allow"
    _connect(home, tools=("read_file", "delete_everything"))          # skill grew a new tool
    m = SK.ensure_manifest(home, "fsx")
    assert m["approval"] == "ask" and m["drift"]["new_tools"] == ["delete_everything"]
    assert m["tools"]["delete_everything"] == [CAP_WRITE]
    assert any("changed since approval" in f for f in SK.audit(home)[0]["flags"])
    SK.approve(home, "fsx", "allow")
    assert "drift" not in SK.ensure_manifest(home, "fsx")


def test_declare_overrides_inference(home):
    _connect(home, tools=("frobnicate",))
    SK.declare(home, "fsx", "frobnicate", [CAP_SHELL])
    m = SK.ensure_manifest(home, "fsx")
    assert m["tools"]["frobnicate"] == [CAP_SHELL] and m["declared"]
    with pytest.raises(ValueError):
        SK.declare(home, "fsx", "frobnicate", ["root"])
    with pytest.raises(ValueError):
        SK.approve(home, "nope", "allow")


def test_mcp_tool_gated_by_effective_capability(home):
    _connect(home)
    calls = []
    ctx = ToolCtx(home=home, router=None, auto=False, confirm=lambda p: False,
                  mcp_call=lambda s, t, a: calls.append((s, t, a)) or "mcp ok")
    # read tool: fs.read ALLOW by default, but generic mcp is ASK → declined without TTY
    out = run_tool("mcp__fsx__read_file", {"path": "a"}, ctx)
    assert "declined" in out and calls == []
    # skill-level allow lifts the generic mcp ASK; read runs, write still needs fs.write (ASK) → declined
    SK.approve(home, "fsx", "allow")
    assert run_tool("mcp__fsx__read_file", {"path": "a"}, ctx) == "mcp ok" and calls[-1][1] == "read_file"
    out = run_tool("mcp__fsx__write_file", {"path": "a", "content": "x"}, ctx)
    assert "declined" in out and len(calls) == 1
    # a DENY rule on fs.write blocks the MCP writer even with auto
    Policy(home).add_rule(CAP_WRITE, "DENY", "mcp__fsx__*")
    ctx.auto = True
    assert run_tool("mcp__fsx__write_file", {"path": "a", "content": "x"}, ctx).startswith("DENIED")
    assert len(calls) == 1
    # approval=deny stops everything
    SK.approve(home, "fsx", "deny")
    assert "deny" in run_tool("mcp__fsx__read_file", {"path": "a"}, ctx)
    assert len(calls) == 1
    rec = Policy(home).audit_tail(1)[0]
    assert rec["effect"] == "DENY" and "approval=deny" in rec["reason"]


def test_unknown_mcp_tool_is_treated_as_shell(home):
    _connect(home, tools=("read_file",))
    SK.approve(home, "fsx", "allow")
    Policy(home).set_default(CAP_SHELL, "DENY")
    ctx = ToolCtx(home=home, router=None, auto=True, mcp_call=lambda s, t, a: "ran")
    assert run_tool("mcp__fsx__read_file", {}, ctx) == "ran"
    assert run_tool("mcp__fsx__mystery", {}, ctx).startswith("DENIED")


# ---------------------------------------------------------------- API (handlers directly)

def _api(home, ctl_factory=None, session_factory=None):
    from rad.api import Api
    return Api(home, controller_factory=ctl_factory, session_factory=session_factory)


def test_api_health_and_404(home):
    api = _api(home)
    st, d = api.handle("GET", "/v1/health", {}, {})
    assert st == 200 and d["ok"] and d["schema"] >= 3
    from rad.api import ApiError
    with pytest.raises(ApiError) as ei:
        api.handle("GET", "/nope", {}, {})
    assert ei.value.status == 404


def test_api_objective_create_pending_when_not_auto(home):
    from tests.test_control_plane import ScriptedSession, _ctl
    ScriptedSession.script = []
    api = _api(home, ctl_factory=lambda h: _ctl(h, ScriptedSession, plan={"tasks": [{"id": "t1", "title": "x", "checks": []}]}))
    st, d = api.handle("POST", "/v1/objectives", {}, {"goal": "do x"})
    assert st == 201 and d["status"] == "pending" and d["started"] is False
    from rad.api import ApiError
    with pytest.raises(ApiError) as ei:
        api.handle("POST", f"/v1/objectives/{d['id']}/resume", {}, {})
    assert ei.value.status == 409
    with pytest.raises(ApiError):
        api.handle("POST", "/v1/objectives", {}, {"goal": ""})
    with pytest.raises(ApiError):
        api.handle("POST", "/v1/objectives", {}, {"goal": "x", "budget": {"gold": 1}})


def test_api_objective_runs_in_background_when_auto(home, tmp_path):
    from tests.test_control_plane import ScriptedSession, _ctl
    ws = tmp_path / "ws"; ws.mkdir(); home.update(workspace=str(ws), auto=True)
    ScriptedSession.script = [([("write_file", {"path": "a.txt", "content": "hi"})], "DONE: wrote")]
    plan = {"tasks": [{"id": "t1", "title": "write a.txt", "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    api = _api(home, ctl_factory=lambda h: _ctl(h, ScriptedSession, plan=plan))
    st, d = api.handle("POST", "/v1/objectives", {}, {"goal": "write a.txt"})
    assert st == 202 and d["started"]
    api._runs[d["id"]].join(timeout=10)
    st, o = api.handle("GET", f"/v1/objectives/{d['id']}", {}, {})
    assert o["status"] == "completed" and (ws / "a.txt").exists() and o["tasks"][0]["status"] == "COMPLETED"
    st, ev = api.handle("GET", f"/v1/objectives/{d['id']}/events", {"kind": "TOOL_CALLED"}, {})
    assert ev["events"] and ev["events"][0]["data"]["tool"] == "write_file"
    st, tr = api.handle("GET", f"/v1/objectives/{d['id']}/trace", {}, {})
    assert tr["verification"]["objective"]["status"] == "VERIFIED"
    st, why = api.handle("GET", f"/v1/objectives/{d['id']}/why", {"q": "a.txt"}, {})
    assert why["artifact"]["artifact"]["location"].endswith("a.txt") and why["artifact"]["action"]["tool"] == "write_file"
    st, lst = api.handle("GET", "/v1/objectives", {}, {})
    assert lst["objectives"][0]["id"] == d["id"]


def test_api_memory_user_policy_audit(home):
    api = _api(home)
    st, m = api.handle("POST", "/v1/memory", {}, {"text": "my editor is vim"})
    assert st == 201 and m["origin"] == "USER_PROVIDED"
    st, r = api.handle("GET", "/v1/memory/recall", {"q": "editor"}, {})
    assert r["memories"][0]["text"] == "my editor is vim"
    assert api.handle("GET", "/v1/user", {}, {})[1]["preferences"] == {}
    assert api.handle("GET", "/v1/policy", {}, {})[1]["defaults"]["shell"] == "ASK"
    assert api.handle("GET", "/v1/audit", {}, {})[1] == {"audit": []}
    assert api.handle("GET", "/v1/lab/history", {}, {})[1] == {"runs": []}
    assert api.handle("GET", "/v1/evolve/candidates", {}, {})[1] == {"candidates": []}
    st, d = api.handle("GET", "/v1/doctor", {}, {})
    assert d["fix_applied"] is False and any(f["check"] == "config" for f in d["findings"])


# ---------------------------------------------------------------- real HTTP round-trip

@pytest.fixture
def server(home):
    from rad.api import make_server, token_for

    class S:
        def __init__(self, home, auto=False): pass
        def think(self, t): return f"echo:{t}"
        def close(self): pass
    api = _api(home, session_factory=lambda h, auto=False: S(h))
    srv = make_server(home, host="127.0.0.1", port=0, api=api)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", token_for(home)
    srv.shutdown(); srv.server_close()


def _req(base, path, token=None, body=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 method="POST" if body is not None else "GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_http_requires_token_and_serves(home, server):
    base, tok = server
    assert _req(base, "/v1/health")[0] == 401
    assert _req(base, "/v1/health", token="wrong")[0] == 401
    st, d = _req(base, "/v1/health", token=tok)
    assert st == 200 and d["ok"]
    st, d = _req(base, "/v1/chat", token=tok, body={"text": "hi"})
    assert st == 200 and d["reply"] == "echo:hi"
    assert _req(base, "/v1/chat", token=tok, body={})[0] == 400
    assert _req(base, "/v1/zzz", token=tok)[0] == 404
    # bad JSON body
    req = urllib.request.Request(base + "/v1/memory", data=b"{nope", method="POST")
    req.add_header("Authorization", f"Bearer {tok}")
    with pytest.raises(urllib.error.HTTPError) as ei:
        urllib.request.urlopen(req, timeout=5)
    assert ei.value.code == 400
    # the request log is written per request; give the server a moment under load
    import time as _t
    log: list = []
    for _ in range(40):
        try:
            log = (home.root / "logs" / "api.jsonl").read_text().splitlines()
        except FileNotFoundError:
            log = []
        if len(log) >= 6:
            break
        _t.sleep(0.05)
    assert len(log) >= 6, f"expected every request to be logged, got {len(log)}"
    assert all("body" not in json.loads(l) for l in log)
    if os.name != "nt":
        assert oct((home.root / "api.token").stat().st_mode & 0o777) == "0o600"
    else:
        assert (home.root / "api.token").exists()
    from rad.api import token_for
    new = token_for(home, rotate=True)
    assert new != tok


# ---------------------------------------------------------------- API surface (phase 2.0)

def test_api_status_tasks_agents_world_tools_benchmarks(home, tmp_path):
    from tests.test_control_plane import ScriptedSession, _ctl
    ws = tmp_path / "ws2"; ws.mkdir(); home.update(workspace=str(ws), auto=True)
    ScriptedSession.script = [([("write_file", {"path": "b.txt", "content": "hi"})], "DONE: wrote")]
    plan = {"tasks": [{"id": "t1", "title": "write b.txt",
                       "checks": [{"kind": "file_exists", "args": {"path": "b.txt"}}]}]}
    api = _api(home, ctl_factory=lambda h: _ctl(h, ScriptedSession, plan=plan))
    st, d = api.handle("POST", "/v1/objectives", {}, {"goal": "write b.txt"})
    api._runs[d["id"]].join(timeout=10)

    st, s = api.handle("GET", "/v1/status", {}, {})
    assert st == 200 and s["ok"] and s["objectives"]["total"] == 1
    assert s["objectives"]["by_status"].get("completed") == 1
    assert "memory" in s and "chain" in s and "pending_migrations" in s
    assert isinstance(s["pending_migrations"], list)

    st, t = api.handle("GET", "/v1/tasks", {}, {})
    assert st == 200 and t["tasks"] and t["tasks"][0]["objective_id"] == d["id"]
    st, t2 = api.handle("GET", "/v1/tasks", {"status": "COMPLETED"}, {})
    assert t2["tasks"] and all(x["status"] == "COMPLETED" for x in t2["tasks"])
    st, t3 = api.handle("GET", "/v1/tasks", {"status": "RUNNING"}, {})
    assert t3["tasks"] == []

    st, a = api.handle("GET", "/v1/agents", {}, {})
    assert st == 200 and a["agents"] and "planner" in {x["id"] for x in a["agents"]}
    st, w = api.handle("GET", "/v1/world", {}, {})
    assert st == 200 and isinstance(w["relations"], list) and isinstance(w["disputes"], list)
    assert w["counts"]["entities"] >= 1        # the run's artifact was observed into the world model
    st, tl = api.handle("GET", "/v1/tools", {}, {})
    assert st == 200 and {x["name"] for x in tl["tools"]} >= {"read_file", "write_file", "run_shell"}
    assert all(x["capability"] and x["policy"] for x in tl["tools"])
    st, b = api.handle("GET", "/v1/benchmarks", {}, {})
    assert st == 200 and b["banks"]["reasoning"] == 100 and b["banks"]["adversarial"] == 100
    assert "lab" in b and "evaluation" in b and "long_horizon" in b


def test_api_events_stream_and_memory_recall(home, tmp_path):
    """`/v1/events` streams the global log; `/v1/memory/recall` takes its query as a parameter."""
    from rad.api import Api
    from rad.control.events import EventLog, global_path
    log = EventLog(global_path(home), home=home)
    log.emit("TOOL_CALLED", "obj_probe", "t_1", tool="write_file")
    api = Api(home)
    st, payload = api.handle("GET", "/v1/events", {"n": "10", "objective": "obj_probe"}, {})
    assert st == 200 and payload["n"] >= 1
    assert any(e["kind"] == "TOOL_CALLED" for e in payload["events"])
    st, payload = api.handle("GET", "/v1/events", {"kind": "OBJECTIVE"}, {})
    assert st == 200 and all(e["kind"].startswith("OBJECTIVE") for e in payload["events"])
    st, payload = api.handle("GET", "/v1/memory/recall", {"q": "probe"}, {})
    assert st == 200 and "memories" in payload


def test_plan_version_advances_with_planning_and_replanning(home, tmp_path):
    """Every objective records which plan generation its tasks came from."""
    from rad.control import Controller
    from tests.test_control_plane import ScriptedSession, _plan_llm
    w = tmp_path / "ws"; w.mkdir(); home.update(workspace=str(w))
    plan = {"tasks": [{"id": "t1", "text": "make a.txt", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "a.txt"}}]}]}
    ScriptedSession.script = [([("write_file", {"path": "a.txt", "content": "x"})], "DONE")]
    ScriptedSession.prompts = []
    ctl = Controller(home, session_factory=ScriptedSession, llm=_plan_llm(plan), quiet=True)
    obj = ctl.create("make a.txt")
    graph = ctl.plan(obj)
    assert obj.plan_version == 1
    assert all(t.plan_version == 1 for t in graph.tasks.values())
    again = ctl.plan(obj)                      # re-planning bumps the generation
    assert obj.plan_version == 2 and all(t.plan_version == 2 for t in again.tasks.values())
    assert obj.to_dict()["plan_version"] == 2  # persisted with the objective
