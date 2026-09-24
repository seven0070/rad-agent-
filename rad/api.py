"""Local HTTP API — the control plane, memory and doctor over loopback JSON.

    rad serve [--port 7331] [--host 127.0.0.1]

Security model
* Binds 127.0.0.1 by default. Binding elsewhere requires `--host` *and* `--i-know-this-exposes-rad`.
* Every request needs `Authorization: Bearer <token>`; the token is generated on first start,
  stored 0600 at ~/.rad/api.token, and printed once. No token → 401, always.
* Only JSON in/out; request bodies capped at 256 KB; no file paths are accepted from clients —
  everything goes through the same Controller / policy gates as the CLI. Objectives created
  via the API run in a background thread with `auto=True` **only if** the config allows it;
  otherwise they are created but left PENDING for the CLI to run interactively (because HTTP
  cannot answer confirmation prompts).
* Every request is appended to ~/.rad/logs/api.jsonl (method, path, status, ms, no bodies).

Layout (split, behavior unchanged)
* `rad.api_security` — MAX_BODY, ApiError, path containment, secret-file and token helpers.
* `rad.api_routes.*` — route mixins per concern (system, objectives, memory, authority/
    settings, chat/usage, ops, triage); assembled into `Api` below.
* `rad.api_services` — domain glue (objective lifecycle, view payloads, settings/authority).
* `rad.api` — this module: dispatch, background runner, and the HTTP layer (`make_server`).

Endpoints (all under /v1)
    GET  /health                       → {ok, version, schema}
    GET  /doctor?fix=0                 → findings (fix ignored unless config allow_api_fix)
    GET  /objectives?active=1          → list
    POST /objectives {goal, criteria?, constraints?, budget?, run?} → objective (202 if started)
    GET  /objectives/{id}              → objective + tasks
    POST /objectives/{id}/resume|pause|cancel|run   (run = plan + start a PENDING objective)
    GET  /objectives/{id}/events?kind=&since_seq=
    GET  /objectives/{id}/trace        → tasks with verification + attempts
    GET  /objectives/{id}/why          → provenance report
    GET  /objectives/{id}/artifacts    → artifact registry for the objective
    GET  /objectives/{id}/artifact-content?ref= → redacted text preview of a REGISTERED
                                                   artifact (workspace/home only; no arbitrary paths)
    GET  /objectives/{id}/plan         → plan summary (version, source, tasks, checks)
    GET  /objectives/{id}/recovery     → recovery decisions + failure classes
    GET  /objectives/{id}/observations → recorded observations (redacted output)
    GET  /objectives/{id}/live         → live execution view (current task, budget, events)
    GET  /usage                        → cross-objective Usage rollup (persisted data only)
    GET  /memory?layer=&n=             → list memories by layer
    GET  /memory/recall?q=&k=          → memories
    POST /memory {text, layer?}        → remember (USER_PROVIDED)
    GET  /user                         → user model
    GET  /policy                       → effective policy
    GET  /audit?n=                     → permission decisions
    GET  /lab/history · GET /evolve/candidates
    POST /chat {text}                  → one Jerry/brain turn (tools gated as ASK→declined, since no TTY)
    POST /triage {text, kind?}         → advisory auto/escalate classification (read-only)
    GET  /authority                    → profile, capabilities, scopes, confirmation, budgets
    PUT  /authority                    → set profile (UNRESTRICTED needs confirm_unrestricted)
    GET  /settings                     → safe config subset (no secrets)
    PUT  /settings                     → limited keys only; cannot raise budgets or bypass policy
"""
from __future__ import annotations

import json
import secrets
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from rad import __version__
from rad.home import RadHome
from rad.api_routes import (
    AuthoritySettingsMixin,
    ChatUsageMixin,
    MemoryMixin,
    ObjectivesMixin,
    OpsMixin,
    SystemMixin,
    TriageMixin,
)
from rad.api_security import (  # re-exported for `from rad.api import ...` callers
    MAX_BODY,
    ApiError,
    restrict_secret,
    secret_is_private,
    token_for,
)


class Api(SystemMixin, ObjectivesMixin, MemoryMixin, AuthoritySettingsMixin,
          ChatUsageMixin, OpsMixin, TriageMixin):
    """Transport-independent handlers: (method, path, query, body) -> (status, payload).
    Kept separate from the HTTP layer so tests can call them directly.
    Route groups live in `rad.api_routes.*`; domain glue in `rad.api_services`."""

    def __init__(self, home: RadHome, controller_factory: Optional[Callable[[RadHome], Any]] = None,
                 session_factory: Optional[Callable[..., Any]] = None) -> None:
        self.home = home
        self._ctl_factory = controller_factory
        self._session_factory = session_factory
        self._runs: Dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def _ctl(self):
        if self._ctl_factory:
            return self._ctl_factory(self.home)
        from rad.control.controller import Controller
        return Controller(self.home, quiet=True)

    # ---- dispatch -------------------------------------------------------------------------
    def handle(self, method: str, path: str, query: Dict[str, str], body: Dict[str, Any]) -> Tuple[int, Any]:
        parts = [p for p in path.split("/") if p]
        if not parts:
            raise ApiError(404, "unknown path")
        if parts[0] in ("v1", "api"):
            parts = parts[1:]
        else:
            raise ApiError(404, "unknown path (use /v1/... or /api/...)")
        try:
            return self._route(method, parts, query, body)
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(500, f"{type(e).__name__}: {str(e)[:200]}")

    def _route(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]) -> Tuple[int, Any]:
        # Group order is irrelevant to matching (path shapes are disjoint); the
        # objectives group raises 404 "unknown objective route" for unmatched
        # /objectives/{id}/... subpaths instead of falling through, exactly as before.
        for route in (self._route_system, self._route_objectives, self._route_memory,
                      self._route_authority, self._route_chat_usage, self._route_ops,
                      self._route_triage):
            out = route(m, p, q, b)
            if out is not None:
                return out
        raise ApiError(404, "unknown route")

    # ---- background runner ----------------------------------------------------------------
    def _background(self, key: str, fn: Callable[[], Any]) -> None:
        with self._lock:
            t = self._runs.get(key)
            if t and t.is_alive():
                raise ApiError(409, f"{key} already running")

            def wrap():
                try:
                    fn()
                except Exception:
                    traceback.print_exc()
            th = threading.Thread(target=wrap, name=f"api-{key}", daemon=True)
            self._runs[key] = th
            th.start()


# ---------------------------------------------------------------- HTTP layer

def make_server(home: RadHome, host: str = "127.0.0.1", port: int = 7331, api: Optional[Api] = None,
                token: Optional[str] = None) -> ThreadingHTTPServer:
    api = api or Api(home)
    token = token or token_for(home)
    log_path = home.root / "logs" / "api.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    class H(BaseHTTPRequestHandler):
        server_version = f"rad/{__version__}"

        def log_message(self, *a):        # quiet; we write our own structured log
            pass

        def _send(self, status: int, payload: Any) -> None:
            data = json.dumps(payload, ensure_ascii=False, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")
            self.end_headers()
            self.wfile.write(data)

        def _authed(self) -> bool:
            h = self.headers.get("Authorization", "")
            return h.startswith("Bearer ") and secrets.compare_digest(h[7:].strip(), token)

        def _do(self, method: str) -> None:
            t0 = time.time()
            status = 500
            try:
                if not self._authed():
                    status = 401
                    self._send(401, {"error": "missing or invalid bearer token"})
                    return
                u = urlparse(self.path)
                q = {k: v[-1] for k, v in parse_qs(u.query).items()}
                body: Dict[str, Any] = {}
                if method in ("POST", "PUT"):
                    n = int(self.headers.get("Content-Length", 0) or 0)
                    if n > MAX_BODY:
                        status = 413; self._send(413, {"error": "body too large"}); return
                    raw = self.rfile.read(n) if n else b""
                    if raw:
                        try:
                            body = json.loads(raw)
                        except Exception:
                            status = 400; self._send(400, {"error": "invalid JSON body"}); return
                        if not isinstance(body, dict):
                            status = 400; self._send(400, {"error": "JSON body must be an object"}); return
                try:
                    status, payload = api.handle(method, u.path, q, body)
                except ApiError as e:
                    status, payload = e.status, {"error": str(e)}
                self._send(status, payload)
            finally:
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"at": time.time(), "method": method, "path": self.path.split("?")[0],
                                            "status": status, "ms": int((time.time() - t0) * 1000),
                                            "peer": self.client_address[0]}) + "\n")
                except OSError:
                    pass

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")
            self.send_header("Access-Control-Max-Age", "86400")
            self.end_headers()

        def do_GET(self):
            self._do("GET")

        def do_POST(self):
            self._do("POST")

        def do_PUT(self):
            self._do("PUT")

    return ThreadingHTTPServer((host, port), H)
