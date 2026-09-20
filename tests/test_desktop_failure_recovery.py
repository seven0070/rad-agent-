"""Desktop API failure recovery: persistent bad artifacts stay honest over HTTP.

The session keeps writing invalid artifacts and claiming `DONE` — a model's
`DONE:` is never completion, and the objective must NOT stop in a VERIFIED
state. It either suspends for the user (needs_user) or fails, and resuming
re-drives to another honest non-VERIFIED terminal state. No fabricated
"Verification: VERIFIED" text may appear.
"""
from __future__ import annotations

import http.client
import json
import threading
import time
from typing import Any, Dict, Optional

from rad.api import Api, make_server, token_for
from rad.control import Controller
from rad.control.objectives import Budget
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401
from tests.test_verified_coding_loop import BAD_PY, BAD_RESULT, CODING_PLAN, WORD_COUNTER_TEST

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


def _wait_background_done(api: Api, oid: str, timeout: float = 10.0) -> None:
    """The trace can show a terminal status while the run thread is still
    unwinding; the server refuses resume with 409 until the thread exits."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        t = api._runs.get(oid)
        if t is None or not t.is_alive():
            return
        time.sleep(0.05)
    raise AssertionError(f"background run for {oid} still alive")


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


def test_desktop_failure_recovery_persistent_bad_artifacts_never_verified(home, ws, scripted):
    """Every attempt writes invalid JSON + broken code and claims DONE: never VERIFIED."""
    home.update(auto=True)
    ctl = _ctl(home, scripted, CODING_PLAN)
    ctl.budget = Budget(tool_calls=40, retries=6)  # bounded: stop honestly when exhausted
    api = Api(home, controller_factory=lambda h: ctl, session_factory=scripted)
    srv = make_server(home, "127.0.0.1", 0, api=api, token=None)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    token = token_for(home)
    try:
        scripted.script = [
            ([("write_file", {"path": "word_counter.py", "content": BAD_PY}),
              ("write_file", {"path": "test_word_counter.py", "content": WORD_COUNTER_TEST}),
              ("write_file", {"path": "result.json", "content": BAD_RESULT}),
              ("run_shell", {"command": "python3 test_word_counter.py"})],
             "DONE: done")
        ] * 8

        st, body = _api_call(port, "POST", "/v1/objectives", token,
                             {"goal": GOAL, "run": True})
        assert st == 202, body
        oid = body["id"]

        trace = _wait_http_objective(port, token, oid, api)
        assert trace["objective"]["status"] in ("needs_user", "failed"), trace
        ov = (trace.get("verification") or {}).get("objective") or {}
        assert ov.get("status") != "VERIFIED", ov
        assert "Verification: VERIFIED" not in trace["objective"].get("result", "")

        # the artifact on disk is honestly invalid — no fake success payload
        raw = (ws / "result.json").read_text(encoding="utf-8") if (ws / "result.json").exists() else ""
        try:
            json.loads(raw)
            valid = True
        except Exception:
            valid = False
        assert not valid

        # resume re-drives to another honest terminal state — still not VERIFIED
        _wait_background_done(api, oid)
        st, body = _api_call(port, "POST", f"/v1/objectives/{oid}/resume", token)
        assert st == 202, body
        trace2 = _wait_http_objective(port, token, oid, api)
        assert trace2["objective"]["status"] in ("needs_user", "failed"), trace2
        ov2 = (trace2.get("verification") or {}).get("objective") or {}
        assert ov2.get("status") != "VERIFIED", ov2
        assert "Verification: VERIFIED" not in trace2["objective"].get("result", "")
    finally:
        srv.shutdown()
        srv.server_close()