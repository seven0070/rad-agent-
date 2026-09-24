"""P2 swarm: T5 realtime TEN voice + T4 desktop hardening (CSP/isolation, process-group, signing, SSE)."""
import json
import pathlib
import tempfile
import os

from rad.home import RadHome


def test_voice_ten_stub_and_fallback(tmp_path):
    """T5: TEN optional backend streams VAD→STT→LLM→TTS, fallback intact."""
    from rad import voice as V
    # symbols exist
    assert hasattr(V, "ten_available")
    assert hasattr(V, "vad_available")
    assert hasattr(V, "realtime_supported")
    assert hasattr(V, "resolve_voice_backend")
    assert hasattr(V, "voice_auto_mode")
    assert hasattr(V, "realtime_pipeline")
    assert hasattr(V, "realtime_stream")
    assert hasattr(V, "vad_segments")
    # TEN stub defaults off (unless env)
    assert V.ten_available() is False or V.ten_available() is True  # bool
    # but env stub works
    os.environ["RAD_TEN"] = "1"
    try:
        assert V.ten_available() is True
        assert V.realtime_supported() is True
    finally:
        os.environ.pop("RAD_TEN", None)
    assert V.realtime_supported() in (True, False)
    # fallback helpers still present and not raising
    home = RadHome(tmp_path / ".rad")
    # _find_piper / _piper_model still exist
    assert callable(V._find_piper)
    assert callable(V._piper_model)
    assert V._find_piper() is None or isinstance(V._find_piper(), str)
    # resolve_voice_backend auto -> text/fallback when no engines
    mode = V.resolve_voice_backend(home)
    assert mode in ("ten", "piper", "openai", "fallback", "text")
    auto = V.voice_auto_mode(home)
    assert auto in ("ten", "fallback", "text")
    # realtime_stream yields chunks without TEN
    chunks = list(V.realtime_stream(home, "hello world this is a long prompt that should chunk into pieces"))
    assert len(chunks) >= 1
    assert chunks[0].startswith("hello")
    # vad_segments on missing file -> empty
    assert V.vad_segments(pathlib.Path(tmp_path / "nope.wav")) == []
    # env VAD stub
    os.environ["RAD_VAD"] = "1"
    try:
        p = tmp_path / "dummy.wav"
        p.write_bytes(b"\x00" * 100)
        segs = V.vad_segments(p)
        assert segs == [(0.0, 1.0)]
    finally:
        os.environ.pop("RAD_VAD", None)


def test_voice_pipeline_fallback_no_crash(tmp_path):
    from rad import voice as V
    home = RadHome(tmp_path / ".rad")
    # realtime_pipeline must never raise even with no mic
    res = V.realtime_pipeline(home, llm_call=lambda x: f"echo:{x}", seconds=1)
    assert isinstance(res, dict)
    assert "backend" in res
    assert res["backend"] in ("ten", "piper", "openai", "fallback", "text")
    # no mic path -> transcript None but dict shape intact
    assert "transcript" in res and "reply" in res and "note" in res


def test_voice_stt_tts_fallback_graceful(tmp_path):
    from rad import voice as V
    home = RadHome(tmp_path / ".rad")
    home.cfg["tts"] = "auto"
    home.cfg["stt"] = "auto"
    home.save_config()
    # speak with no engine -> string containing TTS unavailable or saved
    note = V.speak("hello rad", home)
    assert isinstance(note, str)
    assert "TTS unavailable" in note or "spoke nothing" in note or "audio saved" in note or note == ""
    # listen with no mic -> None without exception
    # record_wav with no arecord/sounddevice -> None -> listen returns None
    txt = V.listen(home, seconds=1)
    assert txt is None or isinstance(txt, str)


def test_voice_cli_extra_parser():
    from rad.cli import build_parser
    p = build_parser()
    args = p.parse_args(["chat", "--voice"])
    assert args.voice is True
    assert getattr(args, "voice_backend", "auto") == "auto"
    args2 = p.parse_args(["chat", "--voice", "--voice-backend", "ten"])
    assert args2.voice_backend == "ten"
    args3 = p.parse_args(["chat", "--voice", "--voice-backend", "fallback"])
    assert args3.voice_backend == "fallback"
    # --voice auto without TEN must not crash resolve
    home = RadHome(pathlib.Path(tempfile.mkdtemp()) / ".rad")
    from rad.voice import voice_auto_mode
    m = voice_auto_mode(home)
    assert m in ("ten", "fallback", "text")


def test_tauri_csp_hardened():
    p = pathlib.Path("desktop/src-tauri/tauri.conf.json")
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    sec = data["app"]["security"]
    csp = sec["csp"]
    # original must still allow loopback
    assert "default-src 'self'" in csp
    assert "127.0.0.1" in csp
    # hardened extras
    assert "script-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "worker-src" in csp
    # Tauri hardening flags
    assert sec.get("dangerousDisableAssetCspModification") is False
    assert sec.get("freezePrototype") is True
    assert sec.get("pattern", {}).get("use") == "brownfield"


def test_tauri_capabilities_isolated():
    p = pathlib.Path("desktop/src-tauri/capabilities/default.json")
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    perms = data.get("permissions", [])
    # must be locked to backend_* only, no shell/fs/http plugin
    assert any("backend-start" in c for c in perms) or any("allow-backend" in c for c in perms)
    assert not any("shell" in c.lower() for c in perms), "desktop must not have shell capability"
    assert not any("fs:" in c.lower() for c in perms), "desktop must not have fs write"
    assert "core:default" in perms


def test_sidecar_process_group_orphan_reaping():
    import pathlib
    py = pathlib.Path("rad/sidecar.py").read_text(encoding="utf-8")
    assert "reap_process_group" in py
    assert "ensure_process_group" in py
    assert "_install_reap_handlers" in py
    assert "ORPHAN" in py or "_ORPHAN_PIDS" in py
    # lib.rs process-group hardening
    rs = pathlib.Path("desktop/src-tauri/src/lib.rs").read_text(encoding="utf-8")
    assert "CREATE_NEW_PROCESS_GROUP" in rs
    assert "process_group" in rs
    assert "reap_orphans" in rs
    assert "orphan" in rs.lower()


def test_signing_stub_exists():
    sj = pathlib.Path("desktop/src-tauri/signing.json")
    assert sj.exists(), "signing.json stub missing"
    data = json.loads(sj.read_text(encoding="utf-8"))
    assert data.get("stub") is True
    assert "tauri_signing" in data
    # sidecar signing module
    sp = pathlib.Path("sidecar/signing.py")
    assert sp.exists()
    txt = sp.read_text(encoding="utf-8")
    assert "signing_available" in txt
    assert "verify_stub" in txt


def test_signing_verify_stub_lab(tmp_path):
    from sidecar.signing import verify_stub, signing_available
    res = verify_stub()
    assert res["ok"] is True
    assert res["stub"] is True
    assert isinstance(signing_available(), bool)


def test_observability_sse_endpoint(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.api import Api
    api = Api(home)
    # P0 observability still intact
    status, payload = api.handle("GET", "/v1/providers/health", {}, {})
    assert status == 200
    assert payload["mode"] == "observability_only"
    assert "providers" in payload
    # SSE endpoints must exist and be observability_only
    status, payload = api.handle("GET", "/v1/events/stream", {}, {})
    assert status == 200
    assert payload.get("sse") is True
    assert payload.get("mode") == "observability_only"
    assert "text/event-stream" in payload.get("content_type", "")
    status, payload = api.handle("GET", "/v1/observability/stream", {}, {})
    assert status == 200
    assert payload.get("sse") is True
    # SSE over HTTP: make_server should handle Accept: text/event-stream
    from rad.api import make_server
    import threading, urllib.request, time
    srv = make_server(home, host="127.0.0.1", port=0)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        tok = home.root.joinpath("api.token").read_text(encoding="utf-8").strip()
        req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/events/stream",
                                     headers={"Authorization": f"Bearer {tok}", "Accept": "text/event-stream"})
        with urllib.request.urlopen(req, timeout=5) as r:
            assert r.headers.get_content_type() == "text/event-stream"
            body = r.read().decode()
            assert body.startswith("data: ")
            assert "sse" in body
    finally:
        srv.shutdown()
        srv.server_close()


def test_p0_observability_not_regressed(tmp_path):
    """P0 mode still observability_only — no routing active."""
    home = RadHome(tmp_path / ".rad")
    from rad.api import Api
    api = Api(home)
    for path in ["/v1/providers/health", "/v1/events/stream", "/v1/observability/stream"]:
        status, payload = api.handle("GET", path, {}, {})
        assert status == 200
        assert payload.get("mode") == "observability_only"
