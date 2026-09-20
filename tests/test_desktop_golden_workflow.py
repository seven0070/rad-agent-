"""Desktop API golden workflow: HTTP server → run objective → VERIFIED, restart-safe.

Server is exercised over the real HTTP wire (bearer token, JSON bodies). The
objective is driven by a ScriptedSession that *really executes tools* through
the injected tool_runner, so files land in the workspace and the machine
Verifier checks real state. The same objective stays VERIFIED when read
through a brand-new Api instance (persistence, not a one-server artifact).
"""
from __future__ import annotations

import http.client
import json
import threading
import time
from typing import Any, Dict, Optional

from rad.api import Api, make_server, token_for
from rad.control import Controller
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401
from tests.test_verified_coding_loop import (
    CODING_PLAN,
    GOOD_PY,
    GOOD_RESULT,
    WORD_COUNTER_TEST,
)

GOAL = "Create a small Python project with one function and pytest test."

TERMINAL = ("completed", "failed", "needs_user", "cancelled")


def _api_call(port: int, method: str, path: str, token: str,
              body: Optional[Dict[str, Any]] = None) -> tuple:
    headers = {"Authorization": f"Bearer {token}"}
    payload = None
    if body is not None:
        payload = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    conn.request(method, path, body=payload, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, (json.loads(data) if data else {})


def _wait_http_objective(port: int, token: str, oid: str, api: Api, timeout: float = 30.0) -> Dict[str, Any]:
    """Wait for the objective to reach a terminal state.

    The trace can report a terminal status while the run thread is still
    unwinding (resume is refused with 409 until it exits), and a GET that
    overlaps the thread's atomic save can hit a Windows rename collision
    (WinError 5). So first wait for the background thread to exit, then read
    the final, already-persisted trace — no writer is active during the read.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        t = api._runs.get(oid)
        if t is None or not t.is_alive():
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"background run for {oid} still alive after {timeout}s")
    last = None
    while time.time() < deadline:
        st, trace = _api_call(port, "GET", f"/v1/objectives/{oid}/trace", token)
        assert st == 200, trace
        last = trace
        status = trace["objective"]["status"]
        if status in TERMINAL:
            return trace
        time.sleep(0.1)
    raise AssertionError(f"objective {oid} did not reach a terminal state:\n{json.dumps(last, indent=2)}")


def test_desktop_golden_workflow_end_to_end(home, ws, scripted):
    """A scripted objective that actually does the work yields VERIFIED over HTTP."""
    home.update(auto=True)  # run+auto → 202 started on POST
    ctl = _ctl(home, scripted, CODING_PLAN)
    api = Api(home, controller_factory=lambda h: ctl, session_factory=scripted)
    srv = make_server(home, "127.0.0.1", 0, api=api, token=None)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    token = token_for(home)
    try:
        # golden script: write the project, run the pytest, claim DONE once
        scripted.script = [
            ([("write_file", {"path": "word_counter.py", "content": GOOD_PY}),
              ("write_file", {"path": "test_word_counter.py", "content": WORD_COUNTER_TEST}),
              ("write_file", {"path": "result.json", "content": GOOD_RESULT}),
              ("run_shell", {"command": "python3 test_word_counter.py"})],
             "DONE: implemented and tests pass"),
        ]

        st, body = _api_call(port, "POST", "/v1/objectives", token,
                             {"goal": GOAL, "run": True})
        assert st == 202, body
        oid = body["id"]
        assert body["started"] is True
        assert body["status"] == "pending"

        trace = _wait_http_objective(port, token, oid, api)
        assert trace["objective"]["status"] == "completed", trace
        # honest machine verification
        ov = (trace.get("verification") or {}).get("objective") or {}
        assert ov.get("status") == "VERIFIED", ov
        # the work really happened: graph first task completed and disk matches
        tasks = trace.get("tasks") or []
        assert tasks and tasks[0].get("id"), tasks  # ids are generated, not t1
        assert tasks[0].get("status") == "COMPLETED", tasks
        assert trace["objective"]["usage"]["tool_calls"] >= 3
        doc = json.loads((ws / "result.json").read_text(encoding="utf-8"))
        assert doc["words"] == 2

        # events were recorded for the objective
        st, evs = _api_call(port, "GET", f"/v1/objectives/{oid}/events", token)
        assert st == 200 and isinstance(evs.get("events"), list) and evs["events"]

        # restart-proof: a brand-new Api over the same home still sees VERIFIED
        api2 = Api(home, controller_factory=lambda h: ctl, session_factory=scripted)
        st2, trace2 = api2.handle("GET", f"/v1/objectives/{oid}/trace", {}, None)
        assert st2 == 200
        ov2 = (trace2.get("verification") or {}).get("objective") or {}
        assert ov2.get("status") == "VERIFIED", ov2
    finally:
        srv.shutdown()
        srv.server_close()