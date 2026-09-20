"""Desktop API token persistence + honest resume across restarts.

Server 1 (auto off) shows: bearer auth required (401 without/with wrong
token), objective creation without auto → 201 `started: False`, `api.token`
written to the home root, and resume blocked with 409 while the confirmation
gate is not automatic. Flipping `auto` on and starting a *second* server over
the same home must reuse the SAME persisted token, and resume then runs the
objective to an honest terminal state — an empty graph completes UNVERIFIED,
never fabricating a VERIFIED stamp.
"""
from __future__ import annotations

import http.client
import json
import threading
import time
from typing import Any, Dict, Optional

from rad.api import Api, make_server, token_for
from rad.control import Controller
from tests.test_control_plane import ScriptedSession, _plan_llm, scripted  # noqa: F401
from tests.test_verified_coding_loop import CODING_PLAN

GOAL = "Create a small Python project with one function and pytest test."

TERMINAL = ("completed", "failed", "needs_user", "cancelled")


def _api_call(port: int, method: str, path: str, token: Optional[str] = None,
              body: Optional[Dict[str, Any]] = None) -> tuple:
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
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


def test_desktop_token_persistence_and_honest_resume(home, scripted):
    """Token survives restarts; resume of a never-run objective completes UNVERIFIED."""
    ctl = Controller(home, session_factory=scripted, llm=_plan_llm(CODING_PLAN), quiet=True)
    api = Api(home, controller_factory=lambda h: ctl, session_factory=scripted)

    # ---- server 1: default home (auto off → confirmation gate blocks auto-run)
    srv1 = make_server(home, "127.0.0.1", 0, api=api, token=None)
    threading.Thread(target=srv1.serve_forever, daemon=True).start()
    port1 = srv1.server_address[1]
    try:
        token1 = token_for(home)  # token=None above → token_for writes/reads api.token
        assert (home.root / "api.token").exists()
        assert token1 == (home.root / "api.token").read_text(encoding="utf-8").strip()

        # no / wrong token → 401
        st, body = _api_call(port1, "GET", "/v1/health")
        assert st == 401 and "token" in body.get("error", "")
        st, body = _api_call(port1, "GET", "/v1/health", token="wrong-token")
        assert st == 401
        # correct token → 200
        st, body = _api_call(port1, "GET", "/v1/health", token=token1)
        assert st == 200 and body.get("ok") is True

        # auto off → created, not started
        st, body = _api_call(port1, "POST", "/v1/objectives", token1,
                             {"goal": GOAL, "run": True})
        assert st == 201, body
        oid = body["id"]
        assert body.get("started") is False
        assert body["status"] == "pending"

        # resume blocked while run is not automatic → 409
        st, body = _api_call(port1, "POST", f"/v1/objectives/{oid}/resume", token1)
        assert st == 409, body
    finally:
        srv1.shutdown()
        srv1.server_close()

    # ---- server 2: same home, auto now on → token must be unchanged, resume runs
    home.update(auto=True)
    api2 = Api(home, controller_factory=lambda h: ctl, session_factory=scripted)
    srv2 = make_server(home, "127.0.0.1", 0, api=api2, token=None)
    threading.Thread(target=srv2.serve_forever, daemon=True).start()
    port2 = srv2.server_address[1]
    try:
        token2 = token_for(home)
        assert token2 == token1  # persisted token reused across restart

        st, body = _api_call(port2, "POST", f"/v1/objectives/{oid}/resume", token2)
        assert st == 202, body
        assert body["status"] == "resuming"

        trace = _wait_http_objective(port2, token2, oid, api2)
        assert trace["objective"]["status"] == "completed", trace
        ov = (trace.get("verification") or {}).get("objective") or {}
        assert ov.get("status") != "VERIFIED", ov
        assert "Verification: VERIFIED" not in trace["objective"].get("result", "")
    finally:
        srv2.shutdown()
        srv2.server_close()