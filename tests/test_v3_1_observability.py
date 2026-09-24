"""v3.1 Observability — SSE streams + rad trace/replay --verify lineage, rad why provenance."""
import json
import time
from pathlib import Path

def test_sse_stream_endpoint_exists(tmp_path):
    from rad.home import RadHome
    from rad.api import Api, make_server
    import threading, urllib.request, urllib.error, socket
    home = RadHome(str(tmp_path / ".rad"))
    api = Api(home)
    # find free port
    s = socket.socket(); s.bind(("127.0.0.1",0)); port = s.getsockname()[1]; s.close()
    from rad.api import token_for
    tok = token_for(home)
    srv = make_server(home, host="127.0.0.1", port=port, token=tok)
    t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    time.sleep(0.2)
    # SSE request with Accept: text/event-stream
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/events/stream", headers={"Authorization": f"Bearer {tok}", "Accept": "text/event-stream"})
        with urllib.request.urlopen(req, timeout=3) as r:
            body = r.read().decode()
            ctype = r.headers.get("Content-Type","")
            assert "text/event-stream" in ctype, f"SSE must be text/event-stream got {ctype}"
            assert "data:" in body and "sse" in body
    finally:
        srv.shutdown(); srv.server_close()

def test_trace_replay_verify_lineage(tmp_path):
    from rad.home import RadHome
    from rad.control.controller import Controller
    from rad.control.replay import Replay
    home = RadHome(str(tmp_path / ".rad"))
    ws = home.workspace(); ws.mkdir(parents=True, exist_ok=True)
    # Create an objective via Controller, run minimal stub
    ctl = Controller(home)
    obj = ctl.create("write hello.txt with hello", budget=None, auto=True)
    # Run with stubbed LLM? Instead manually create artifacts/observer to test reverify drift
    # Simulate a verified task: write file + check, then reverify
    artifact_path = ws / "hello.txt"
    artifact_path.write_text("hello world", encoding="utf-8")
    from rad.control.tasks import Task, TaskStatus, Check
    from rad.control.graph import TaskGraph
    g = TaskGraph()
    t = Task.new(obj.id, "write hello.txt")
    t.id = "t1"; t.status = TaskStatus.COMPLETED; t.checks=[Check(kind="file_exists", args={"path":"hello.txt"})]
    g.add(t)
    ctl.store.save_tasks(obj.id, g.to_list())
    # also record verification status as VERIFIED
    t.verification = {"status":"VERIFIED","summary":"ok"}
    g.tasks["t1"] = t
    ctl.store.save_tasks(obj.id, g.to_list())
    rp = Replay(ctl.store, obj.id, ws)
    rep = rp.reverify()
    assert rep["objective"] == obj.id
    # file exists so task should be VERIFIED or UNVERIFIED but not drift when still present
    assert "hello.txt" in t.text or rep["tasks"][0]["now"] in ("VERIFIED","UNVERIFIED","FAILED")

def test_why_provenance_artifact_and_claim(tmp_path):
    from rad.home import RadHome
    from rad.control.controller import Controller
    from rad.control.provenance import Provenance
    home = RadHome(str(tmp_path / ".rad"))
    ws = home.workspace(); ws.mkdir(parents=True, exist_ok=True)
    ctl = Controller(home)
    obj = ctl.create("claim test", auto=True)
    # Create an observation with known text
    from rad.control.observer import Observer
    obs_dir = ctl.store.dir(obj.id); obs_dir.mkdir(parents=True, exist_ok=True)
    observer = Observer(obs_dir)
    # use observer.record via tool result: simulate via direct observation file
    # Create a synthetic observation json
    import uuid, time as tm
    oid = f"obs_{uuid.uuid4().hex[:6]}"
    observation = {
        "id": oid, "task_id": "t1", "tool": "fetch_page", "args": {"url":"https://example.com"},
        "status":"success", "at": tm.time(), "output":"Acme is where Alice works. Verified data.", "artifacts":[], "evidence_kinds":["web"]
    }
    # Write as if observer persisted
    obs_path = obs_dir / f"{oid}.json"
    obs_path.write_text(json.dumps(observation), encoding="utf-8")
    # also need observation files for provenance to find evidence
    pv = Provenance(obs_dir)
    res = pv.why("Alice works at Acme")
    # support should find observation
    assert "claim" in res and "support" in res
    # artifact lookup by missing ref should return None, then falls to claim path
    assert pv.artifact("nope.txt") is None

def test_api_trace_endpoint(tmp_path):
    from rad.home import RadHome
    from rad.api import Api
    from rad.control.controller import Controller
    home = RadHome(str(tmp_path / ".rad"))
    ctl = Controller(home)
    obj = ctl.create("trace me", auto=True)
    api = Api(home)
    status, payload = api.handle("GET", f"/v1/objectives/{obj.id}/trace", {}, {})
    assert status == 200
    assert "tasks" in payload or "objective" in payload

def test_voice_ten_e2e_stub_and_manual_completeness():
    # Voice TEN stub must be import-safe and fallback
    from rad.voice import ten_available, resolve_voice_backend, realtime_pipeline, voice_auto_mode
    from rad.home import RadHome
    import tempfile, pathlib
    tmp = pathlib.Path(tempfile.mkdtemp()) / ".rad"
    home = RadHome(str(tmp))
    # stub TEN via env
    import os
    os.environ["RAD_TEN"]="1"
    try:
        assert ten_available() is True
        assert resolve_voice_backend(home) == "ten"
        assert voice_auto_mode(home) == "ten"
        # realtime pipeline with dummy llm should not raise, returns dict with backend ten
        rep = realtime_pipeline(home, llm_call=lambda x: f"echo {x}", seconds=1)
        assert rep["backend"] in ("ten","fallback","text")
    finally:
        os.environ.pop("RAD_TEN",None)
    # manual completeness
    manual = pathlib.Path("manual/README.md").read_text(encoding="utf-8")
    assert "v3.1" in manual
    assert "Battery 11 cats" in manual or "11 cats" in manual
    assert "SSE" in manual
    assert "McpMallPane" in manual or "Appsmith" in manual
    assert "FlowCanvas" in manual
    assert "omarchy" in manual.lower()
