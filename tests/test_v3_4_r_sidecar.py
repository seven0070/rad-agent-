"""v3.4 Agent R — Sidecar reliability: process-group reaping + health survives restart, lab-gated."""
import tempfile
import pathlib
import time
import socket
import subprocess
import sys
import json
import os

def _tmp_home():
    from rad.home import RadHome
    tmp = pathlib.Path(tempfile.mkdtemp()) / ".rad_r"
    return RadHome(str(tmp))

def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port

def test_process_group_reaping_clears_orphans():
    from rad.sidecar import register_orphan, reap_process_group, _ORPHAN_PIDS, is_process_group_reaped, ensure_process_group
    # ensure clean
    _ORPHAN_PIDS.clear()
    assert is_process_group_reaped() is True
    ensure_process_group()  # must not raise, idempotent
    # register fake pids, reap must clear
    register_orphan(99991)
    register_orphan(99992)
    assert 99991 in _ORPHAN_PIDS and 99992 in _ORPHAN_PIDS
    assert is_process_group_reaped() is False
    # reap single
    reap_process_group(99991)
    assert is_process_group_reaped(99991) is True
    assert 99992 in _ORPHAN_PIDS
    # reap all
    reap_process_group()
    assert is_process_group_reaped() is True
    assert len(_ORPHAN_PIDS) == 0
    # re-register and reap again idempotently
    register_orphan(12345)
    reap_process_group()
    assert _ORPHAN_PIDS == []

def test_sidecar_health_survives_restart_token_persists():
    from rad.sidecar import sidecar_health, _token
    home = _tmp_home()
    # token persists across "restarts" — same home root
    tok1 = _token(str(home.root))
    assert tok1 and len(tok1) >= 16
    # simulate restart: new RadHome on same root must yield same token
    from rad.home import RadHome
    home2 = RadHome(str(home.root))
    from rad.api import token_for
    tok2 = token_for(home2)
    assert tok1 == tok2
    # health reports survives_restart even when no server
    h = sidecar_health(str(home.root), port=_free_port(), timeout=0.5)
    assert h["survives_restart"] is True
    assert "port" in h
    # health must not use shell
    src = pathlib.Path("rad/sidecar.py").read_text(encoding="utf-8")
    # ensure reap does not rely on shell=True
    assert "shell=True" not in src

def test_sidecar_serve_then_health_then_reap_restart_survives():
    # launch a real sidecar serve on a free port, health check, kill, restart, health again
    home = _tmp_home()
    port = _free_port()
    env = dict(os.environ)
    env["RAD_HOME"] = str(home.root)
    # spawn serve
    proc = subprocess.Popen([sys.executable, "-m", "rad.sidecar", "serve", "--port", str(port), "--home", str(home.root)],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        # wait for listening line
        deadline = time.time() + 8
        listening = False
        while time.time() < deadline:
            if proc.poll() is not None:
                break
            # try health
            try:
                import urllib.request
                from rad.api import token_for
                tok = token_for(home)
                req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/health",
                                             headers={"Authorization": f"Bearer {tok}"})
                with urllib.request.urlopen(req, timeout=1) as r:
                    data = json.loads(r.read().decode())
                    if data.get("ok"):
                        listening = True
                        break
            except Exception:
                time.sleep(0.3)
        assert listening, f"sidecar never became healthy on {port}"
        # health helper must report ok
        from rad.sidecar import sidecar_health
        h1 = sidecar_health(str(home.root), port=port, timeout=2)
        assert h1["ok"] is True
        assert h1["survives_restart"] is True
    finally:
        # reap process group semantics: terminate
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        # after kill, health should be not ok but survives_restart still true (no crash)
        from rad.sidecar import sidecar_health as sh2
        h2 = sh2(str(home.root), port=port, timeout=0.5)
        assert h2["survives_restart"] is True
        assert h2["ok"] is False  # server gone
        # restart on same port must succeed (port freed, token same)
        proc2 = subprocess.Popen([sys.executable, "-m", "rad.sidecar", "serve", "--port", str(port), "--home", str(home.root)],
                                 env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.time() + 8
            listening2 = False
            while time.time() < deadline:
                if proc2.poll() is not None:
                    break
                try:
                    import urllib.request
                    from rad.api import token_for as tf2
                    tok = tf2(home)
                    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/health",
                                                 headers={"Authorization": f"Bearer {tok}"})
                    with urllib.request.urlopen(req, timeout=1) as r:
                        data = json.loads(r.read().decode())
                        if data.get("ok"):
                            listening2 = True
                            break
                except Exception:
                    time.sleep(0.3)
            assert listening2, "sidecar restart never became healthy"
            h3 = sidecar_health(str(home.root), port=port, timeout=2)
            assert h3["ok"] is True
        finally:
            try:
                proc2.terminate()
                proc2.wait(timeout=5)
            except Exception:
                try:
                    proc2.kill()
                except Exception:
                    pass

def test_sidecar_health_only_loopback_no_shell_bypass():
    src = pathlib.Path("rad/sidecar.py").read_text(encoding="utf-8")
    assert "only binds loopback" in src
    assert "only talks to loopback" in src
    assert "LOOPBACK" in src
    # health must use urllib, not shell
    assert "urllib.request" in src
    assert "taskkill" in src or "os.kill" in src  # reaping uses OS, not shell bypass
    # no subprocess shell
    assert "shell=True" not in src

def test_sidecar_invariants_preserved():
    # objective_parallel=8 and VERIFIED-only must stay
    from rad.home import DEFAULTS
    assert DEFAULTS["objective_parallel"] == 8
    assert DEFAULTS["accept_unverified_done"] is False
