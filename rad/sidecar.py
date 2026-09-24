"""RAD backend sidecar entry point.

Packaged as a self-contained executable (PyInstaller onefile) so RAD Desktop does not
require a user-installed Python:

    rad-backend serve [--port 7331] [--home PATH]
    rad-backend health --port 7331 [--home PATH]

The desktop launches the sidecar with a FIXED argv (see desktop/src-tauri/src/lib.rs and
the Tauri capability scope). This module is only a transport shim:

* ``serve``  → the existing ``rad.api.make_server`` on loopback, bearer-token auth,
  same gates as ``rad serve``. The Python control plane is unchanged.
* ``health`` → one GET /v1/health using the token stored at <home>/api.token; prints
  ``{"ok": ...}`` JSON. Used by the desktop's connect / reconnect loop.

Exit codes: 0 ok · 1 bad usage / fatal · 3 port already in use (stale or foreign
backend on that port). Never raises out of ``main``.
"""
from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import sys
import time
import traceback
from pathlib import Path
from typing import List, Optional

LOOPBACK = ("127.0.0.1", "localhost", "::1")
DEFAULT_PORT = 7331
EXIT_PORT_IN_USE = 3

# --- Process-group orphan reaping (T4 hardening) ---
# Ensure no orphaned rad-backend children survive desktop quit.
_ORPHAN_PIDS: List[int] = []


def ensure_process_group() -> None:
    """Put this process in its own process group (Unix setsid, Windows new group)."""
    try:
        if os.name == "nt":
            # On Windows the group is created at spawn via CREATE_NEW_PROCESS_GROUP.
            # Here we just ensure we can handle CTRL_BREAK.
            import ctypes  # noqa
            pass
        else:
            try:
                os.setsid()
            except Exception:
                pass
    except Exception:
        pass


def register_orphan(pid: int) -> None:
    if pid not in _ORPHAN_PIDS:
        _ORPHAN_PIDS.append(pid)


def reap_process_group(pid: Optional[int] = None) -> None:
    """Reap process group: kill child pids and, on Unix, the whole pgid."""
    import subprocess
    targets = [pid] if pid else list(_ORPHAN_PIDS)
    for p in targets:
        if not p:
            continue
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(p), "/T", "/F"],
                               capture_output=True, timeout=5)
            else:
                try:
                    os.killpg(os.getpgid(p), signal.SIGTERM)
                except Exception:
                    try:
                        os.kill(p, signal.SIGTERM)
                    except Exception:
                        pass
                time.sleep(0.2)
                try:
                    os.killpg(os.getpgid(p), signal.SIGKILL)
                except Exception:
                    pass
        except Exception:
            pass
    if pid is None:
        _ORPHAN_PIDS.clear()
    else:
        try:
            _ORPHAN_PIDS.remove(pid)
        except ValueError:
            pass


def _install_reap_handlers() -> None:
    def _h(signum, frame):  # type: ignore
        reap_process_group()
        sys.exit(0)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _h)
        except Exception:
            pass
    atexit.register(reap_process_group)


def _set_home(home: Optional[str]) -> str:
    root = home or os.environ.get("RAD_HOME") or str(Path.home() / ".rad")
    os.environ["RAD_HOME"] = root
    return root


def _token(home_root: str) -> str:
    from rad.api import token_for
    from rad.home import RadHome
    return token_for(RadHome(home_root))


def _port_in_use(host: str, port: int) -> bool:
    import socket
    for res in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        fam, socktype, proto, _canon, sa = res
        try:
            with socket.socket(fam, socktype, proto) as s:
                s.settimeout(0.25)
                s.connect(sa)
            return True
        except OSError:
            return False
    return False


def serve(args: argparse.Namespace) -> int:
    _install_reap_handlers()
    ensure_process_group()
    home_root = _set_home(args.home)
    host = "127.0.0.1" if args.host in LOOPBACK else args.host
    if host not in LOOPBACK:
        print(json.dumps({"error": "sidecar only binds loopback (127.0.0.1)"}), file=sys.stderr)
        return 1
    from rad.home import RadHome
    home = RadHome(home_root)
    port = args.port or int(home.cfg.get("api_port", DEFAULT_PORT))
    if _port_in_use(host, port):
        print(json.dumps({"error": "port_in_use", "host": host, "port": port,
                          "hint": "another RAD backend (or stale process) is on this port; "
                                  "stop it and retry"}), file=sys.stderr)
        return EXIT_PORT_IN_USE
    from rad.api import make_server, token_for
    tok = token_for(home)
    server = make_server(home, host=host, port=port, token=tok)
    from rad import __version__
    print(json.dumps({"event": "listening", "host": host, "port": port,
                      "version": __version__, "home": home_root, "pgid": os.getpid()}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        reap_process_group()
    return 0


def health(args: argparse.Namespace) -> int:
    home_root = _set_home(args.home)
    host = "127.0.0.1" if args.host in LOOPBACK else args.host
    if host not in LOOPBACK:
        print(json.dumps({"error": "sidecar only talks to loopback"}), file=sys.stderr)
        return 1
    port = args.port or DEFAULT_PORT
    if _port_in_use(host, port):
        pass  # port in use is expected for a health probe; only report the HTTP result
    try:
        tok = _token(home_root)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"no api token: {e}"}))
        return 1
    import urllib.request
    req = urllib.request.Request(f"http://{host}:{port}/v1/health",
                                 headers={"Authorization": f"Bearer {tok}"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        print(json.dumps({"ok": bool(data.get("ok")), "version": data.get("version"),
                          "port": port, "ms": int((time.time() - t0) * 1000)}))
        return 0 if data.get("ok") else 1
    except Exception as e:
        print(json.dumps({"ok": False, "port": port,
                          "error": f"{type(e).__name__}: {str(e)[:200]}"}))
        return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rad-backend", description="RAD backend sidecar (packaged)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="run the RAD HTTP API on loopback")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=0)
    s.add_argument("--home", default=None, help="RAD home (default $RAD_HOME or ~/.rad)")
    s.set_defaults(fn=serve)
    h = sub.add_parser("health", help="probe a running sidecar and print JSON")
    h.add_argument("--host", default="127.0.0.1")
    h.add_argument("--port", type=int, default=DEFAULT_PORT)
    h.add_argument("--home", default=None)
    h.add_argument("--timeout", type=float, default=3.0)
    h.set_defaults(fn=health)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return int(args.fn(args) or 0)
    except SystemExit as e:
        return int(e.code or 0)
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
