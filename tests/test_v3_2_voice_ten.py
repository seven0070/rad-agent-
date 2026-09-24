"""v3.2 Voice TEN e2e hardening — VAD->STT->LLM->TTS with fallback, ten_available stub CI-safe."""
import os
import pathlib
import tempfile


def _tmp_home():
    from rad.home import RadHome
    tmp = pathlib.Path(tempfile.mkdtemp()) / ".rad"
    return RadHome(str(tmp))


def test_ten_available_stub_ci_safe_without_install():
    # Without env and without TEN installed, must be False and not raise
    from rad.voice import ten_available
    # ensure env clean
    old = os.environ.pop("RAD_TEN", None)
    try:
        # should not raise even when TEN not installed
        val = ten_available()
        assert isinstance(val, bool)
        # in CI without TEN, expect False
        assert val is False
    finally:
        if old is not None:
            os.environ["RAD_TEN"] = old


def test_ten_available_env_stub_passes_ci():
    from rad.voice import ten_available
    os.environ["RAD_TEN"] = "1"
    try:
        assert ten_available() is True
    finally:
        os.environ.pop("RAD_TEN", None)
    # after pop, must revert to False (no TEN installed)
    assert ten_available() is False


def test_resolve_voice_backend_ten_pinned_fallback_when_ten_absent():
    from rad.voice import resolve_voice_backend, resolve_voice_backend_with_note
    home = _tmp_home()
    home.update(voice_backend="ten")
    # ensure TEN absent
    os.environ.pop("RAD_TEN", None)
    backend = resolve_voice_backend(home)
    # with TEN absent, pinned ten must gracefully fallback to fallback/text, never ten crash
    assert backend in ("fallback", "text"), f"pinned ten without TEN should fallback, got {backend}"
    backend2, note = resolve_voice_backend_with_note(home)
    assert backend2 == backend
    assert "ten requested" in note or "fallback" in note or note == ""


def test_resolve_voice_backend_ten_with_stub():
    from rad.voice import resolve_voice_backend, voice_auto_mode
    home = _tmp_home()
    os.environ["RAD_TEN"] = "1"
    try:
        home.update(voice_backend="ten")
        assert resolve_voice_backend(home) == "ten"
        assert voice_auto_mode(home) == "ten"
        # auto also picks ten when TEN present
        home.update(voice_backend="auto")
        assert resolve_voice_backend(home) == "ten"
    finally:
        os.environ.pop("RAD_TEN", None)


def test_realtime_pipeline_stub_never_raises_and_returns_backend():
    from rad.voice import realtime_pipeline
    home = _tmp_home()
    os.environ["RAD_TEN"] = "1"
    try:
        home.update(voice_backend="ten")
        rep = realtime_pipeline(home, llm_call=lambda x: f"echo:{x}", seconds=1)
        assert isinstance(rep, dict)
        assert "backend" in rep
        assert rep["backend"] in ("ten", "fallback", "text")
        # has transcript/reply/note keys even when mic absent
        assert "transcript" in rep and "reply" in rep and "note" in rep
    finally:
        os.environ.pop("RAD_TEN", None)


def test_realtime_pipeline_fallback_without_ten_no_raise():
    from rad.voice import realtime_pipeline
    home = _tmp_home()
    home.update(voice_backend="ten")
    os.environ.pop("RAD_TEN", None)
    rep = realtime_pipeline(home, llm_call=lambda x: "hello", seconds=1)
    assert rep["backend"] in ("fallback", "text")
    # should contain note about stt unavailable or no mic, but not raise
    assert isinstance(rep["note"], str)


def test_realtime_stream_yields_word_chunks_and_logs():
    from rad.voice import realtime_stream
    home = _tmp_home()
    os.environ["RAD_TEN"] = "1"
    try:
        home.update(voice_backend="ten")
        chunks = list(realtime_stream(home, "hello world this is a test of streaming chunks for tts"))
        assert len(chunks) >= 1
        assert "hello" in chunks[0]
        # callback variant
        seen = []
        chunks2 = list(realtime_stream(home, "one two three four five six seven eight nine ten", chunk_cb=lambda c: seen.append(c)))
        assert len(seen) == len(chunks2)
    finally:
        os.environ.pop("RAD_TEN", None)
    # fallback without TEN still yields
    os.environ.pop("RAD_TEN", None)
    home.update(voice_backend="text")
    chunks3 = list(realtime_stream(home, "fallback still works"))
    assert len(chunks3) >= 1


def test_vad_and_realtime_supported_with_env_stubs():
    from rad.voice import vad_available, realtime_supported
    os.environ["RAD_VAD"] = "1"
    try:
        assert vad_available() is True
        assert realtime_supported() is True
    finally:
        os.environ.pop("RAD_VAD", None)
    os.environ["RAD_TEN"] = "1"
    try:
        assert realtime_supported() is True
        # vad_available via ten
        from rad.voice import vad_available as va
        assert va() is True
    finally:
        os.environ.pop("RAD_TEN", None)


def test_voice_chat_turn_helper_e2e():
    from rad.voice import voice_chat_turn
    home = _tmp_home()
    os.environ["RAD_TEN"] = "1"
    try:
        home.update(voice_backend="ten")
        rep = voice_chat_turn(home, llm_call=lambda x: f"reply:{x}", seconds=1)
        assert rep["backend"] in ("ten", "fallback", "text")
    finally:
        os.environ.pop("RAD_TEN", None)


def test_cli_parses_voice_ten_flags():
    from rad.cli import build_parser
    p = build_parser()
    args = p.parse_args(["chat", "--voice", "--voice-backend", "ten"])
    assert args.voice is True
    assert args.voice_backend == "ten"
    args2 = p.parse_args(["chat", "--voice"])
    assert args2.voice is True
    assert args2.voice_backend == "auto"
    args3 = p.parse_args(["chat", "--voice", "--voice-backend", "fallback"])
    assert args3.voice_backend == "fallback"
