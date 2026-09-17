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

Endpoints (all under /v1)
    GET  /health                       → {ok, version, schema}
    GET  /doctor?fix=0                 → findings (fix ignored unless config allow_api_fix)
    GET  /objectives?active=1          → list
    POST /objectives {goal, criteria?, constraints?, budget?, run?} → objective (202 if started)
    GET  /objectives/{id}              → objective + tasks
    POST /objectives/{id}/resume|pause|cancel
    GET  /objectives/{id}/events?kind=&since_seq=
    GET  /objectives/{id}/trace        → tasks with verification + attempts
    GET  /objectives/{id}/why          → provenance report
    GET  /memory/recall?q=&k=          → memories
    POST /memory {text, layer?}        → remember (USER_PROVIDED)
    GET  /user                         → user model
    GET  /policy                       → effective policy
    GET  /audit?n=                     → permission decisions
    GET  /lab/history · GET /evolve/candidates
    POST /chat {text}                  → one brain turn (tools gated as ASK→declined, since no TTY)
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from rad import __version__
from rad.home import RadHome

MAX_BODY = 256 * 1024


class ApiError(Exception):
    def __init__(self, status: int, msg: str) -> None:
        super().__init__(msg)
        self.status = status


def token_for(home: RadHome, rotate: bool = False) -> str:
    p = home.root / "api.token"
    if p.exists() and not rotate:
        return p.read_text(encoding="utf-8").strip()
    tok = secrets.token_urlsafe(32)
    p.write_text(tok, encoding="utf-8")
    os.chmod(p, 0o600)
    return tok


class Api:
    """Transport-independent handlers: (method, path, query, body) -> (status, payload).
    Kept separate from the HTTP layer so tests can call them directly."""

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
        if not parts or parts[0] != "v1":
            raise ApiError(404, "unknown path (use /v1/...)")
        parts = parts[1:]
        try:
            return self._route(method, parts, query, body)
        except ApiError:
            raise
        except Exception as e:
            raise ApiError(500, f"{type(e).__name__}: {str(e)[:200]}")

    def _route(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]) -> Tuple[int, Any]:
        from rad.control.objectives import ObjectiveStatus
        if p == ["health"] and m == "GET":
            from rad.storage import Storage
            st = Storage(self.home); st.pending()
            return 200, {"ok": True, "version": __version__, "schema": st.version(),
                         "running": sorted(k for k, t in self._runs.items() if t.is_alive())}
        if p == ["doctor"] and m == "GET":
            from rad.doctor import Doctor
            fix = q.get("fix") == "1" and bool(self.home.cfg.get("allow_api_fix"))
            fs = Doctor(self.home, fix=fix, probe_network=q.get("probe") == "1").run()
            return 200, {"findings": [f.__dict__ for f in fs], "fix_applied": fix}
        if p == ["objectives"] and m == "GET":
            store = self._ctl().store
            objs = store.list(active_only=q.get("active") == "1")
            return 200, {"objectives": [self._obj_summary(o) for o in objs]}
        if p == ["objectives"] and m == "POST":
            return self._create_objective(b)
        if len(p) >= 2 and p[0] == "objectives":
            ctl = self._ctl()
            obj = ctl.store.resolve(p[1])
            if not obj:
                raise ApiError(404, f"no objective {p[1]}")
            if len(p) == 2 and m == "GET":
                d = obj.to_dict(); d["tasks"] = ctl.store.load_tasks(obj.id)
                return 200, d
            if len(p) == 3 and m == "POST" and p[2] in ("resume", "pause", "cancel"):
                if p[2] == "pause":
                    o = ctl.pause(obj.id)
                elif p[2] == "cancel":
                    o = ctl.cancel(obj.id)
                else:
                    if not self._may_run():
                        raise ApiError(409, "config auto=false: HTTP cannot answer confirmation prompts; run `rad objective resume` in a terminal or set auto")
                    self._background(obj.id, lambda: ctl.resume(obj.id))
                    return 202, {"id": obj.id, "status": "resuming"}
                return 200, self._obj_summary(o or obj)
            if len(p) == 3 and m == "GET" and p[2] == "events":
                from rad.control.events import EventLog
                since = int(q.get("since_seq", 0) or 0)
                evs = [e.__dict__ for e in EventLog(ctl.store.events_path(obj.id)).read(kind=q.get("kind") or None)
                       if e.seq > since]
                return 200, {"events": evs[-int(q.get("n", 500) or 500):]}
            if len(p) == 3 and m == "GET" and p[2] == "trace":
                return 200, {"objective": self._obj_summary(obj), "tasks": ctl.store.load_tasks(obj.id),
                             "verification": obj.verification}
            if len(p) == 3 and m == "GET" and p[2] == "why":
                from rad.control.provenance import Provenance
                pv = Provenance(ctl.store.dir(obj.id))
                claim = q.get("q", "")
                if not claim:
                    raise ApiError(400, "q=<artifact path | claim text> required")
                art = pv.artifact(claim)
                return 200, {"artifact": art} if art else pv.why(claim)
            raise ApiError(404, "unknown objective route")
        if p == ["memory", "recall"] and m == "GET":
            from rad.memory import Memory
            k = max(1, min(20, int(q.get("k", 5) or 5)))
            return 200, {"memories": [self._mem(e) for e in Memory(self.home).recall(q.get("q", ""), k=k)]}
        if p == ["memory"] and m == "POST":
            from rad.memory import Memory
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            layer = b.get("layer", "semantic")
            if layer not in ("episodic", "semantic", "procedural"):
                raise ApiError(400, "layer must be episodic|semantic|procedural")
            e = Memory(self.home).add(layer, text, origin="USER_PROVIDED", source="api")
            return 201, self._mem(e)
        if p == ["user"] and m == "GET":
            from rad.usermodel import UserModel
            return 200, UserModel(self.home).data()
        if p == ["policy"] and m == "GET":
            from rad.policy import Policy
            pol = Policy(self.home)
            from rad.policy import BUILTIN_DEFAULTS
            return 200, {"defaults": {c: pol.default_for(c) for c in BUILTIN_DEFAULTS},
                         "rules": [r.to_dict() for r in pol.rules], "web_allow": pol._data.get("web_allow", [])}
        if p == ["audit"] and m == "GET":
            from rad.policy import Policy
            return 200, {"audit": Policy(self.home).audit_tail(int(q.get("n", 50) or 50), effect=q.get("effect") or None)}
        if p == ["lab", "history"] and m == "GET":
            from rad.lab import Lab
            return 200, {"runs": [{k: v for k, v in r.items() if k != "results"} for r in Lab(self.home).history(int(q.get("n", 20) or 20))]}
        if p == ["evolve", "candidates"] and m == "GET":
            from rad.evolution import Evolution
            return 200, {"candidates": [c.to_dict() for c in Evolution(self.home).candidates(int(q.get("n", 20) or 20))]}
        if p == ["chat"] and m == "POST":
            text = str(b.get("text", "")).strip()
            if not text:
                raise ApiError(400, "text required")
            s = self._session_factory(self.home, auto=False) if self._session_factory else None
            if s is None:
                from rad.session import Session
                s = Session(self.home, auto=False)          # ASK → declined (no TTY); ALLOW tools still work
            try:
                reply = s.think(text)
            finally:
                try:
                    s.close()
                except Exception:
                    pass
            return 200, {"reply": reply}
        raise ApiError(404, "unknown route")

    # ---- helpers --------------------------------------------------------------------------
    def _may_run(self) -> bool:
        return bool(self.home.cfg.get("auto"))

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

    def _create_objective(self, b: Dict[str, Any]) -> Tuple[int, Any]:
        from rad.control.objectives import Budget
        goal = str(b.get("goal", "")).strip()
        if not goal or len(goal) > 4000:
            raise ApiError(400, "goal required (≤4000 chars)")
        crit = [str(x)[:300] for x in (b.get("criteria") or [])][:20]
        cons = [str(x)[:300] for x in (b.get("constraints") or [])][:20]
        bud = b.get("budget") or {}
        if not isinstance(bud, dict) or any(k not in Budget.__dataclass_fields__ for k in bud):
            raise ApiError(400, f"budget keys must be in {sorted(Budget.__dataclass_fields__)}")
        ctl = self._ctl()
        run = bool(b.get("run", True))
        auto = self._may_run()
        obj = ctl.create(goal, success_criteria=crit, constraints=cons, budget=Budget(**bud) if bud else None, auto=auto)
        if run and auto:
            self._background(obj.id, lambda: ctl.run(obj))
            return 202, {**self._obj_summary(obj), "started": True}
        return 201, {**self._obj_summary(obj), "started": False,
                     "note": "created PENDING: run it with `rad objective run` (config auto=false)" if run else "created PENDING"}

    @staticmethod
    def _obj_summary(o) -> Dict[str, Any]:
        return {"id": o.id, "goal": o.goal, "status": o.status, "created": o.created, "updated": o.updated,
                "usage": o.usage.to_dict(), "budget": o.budget.to_dict(), "result": (o.result or "")[:2000],
                "verification": (o.verification or {}).get("objective", {}).get("status", "")}

    @staticmethod
    def _mem(e) -> Dict[str, Any]:
        return {"id": e.id, "layer": e.layer, "text": e.text, "origin": e.origin, "confidence": e.confidence,
                "verification": e.verification, "strength": e.strength}


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
                if method == "POST":
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

        def do_GET(self):
            self._do("GET")

        def do_POST(self):
            self._do("POST")

    return ThreadingHTTPServer((host, port), H)
