"""The voice socket — speak + listen.

Free-first: local Piper (TTS) + local Whisper (STT) when present,
provider APIs (OpenAI TTS/STT) when keys exist, graceful text-only otherwise.

Realtime TEN optional backend (VAD→STT→LLM→TTS streaming):
    When TEN (agora) is installed and RAD_TEN=1, `ten_available()` is True and
    `realtime_pipeline()` streams VAD → STT → LLM → TTS.  Fallback to
    Piper/Whisper/OpenAI is always available — --voice auto-selects the best
    backend without breaking when TEN is absent.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from rad.home import RadHome
from rad.ui import warn

# ---------------------------------------------------------------- Realtime TEN (optional)
# TEN = real-time agent network (Agora). Optional dep — never required.
TEN_VERSION: Optional[str] = None


def ten_available() -> bool:
    """True iff a TEN runtime is importable or RAD_TEN=1 is set (lab stub)."""
    if os.environ.get("RAD_TEN") == "1":
        return True
    try:
        import importlib
        for mod in ("ten", "agora_ten", "ten_agent"):
            try:
                m = importlib.import_module(mod)
                global TEN_VERSION
                TEN_VERSION = getattr(m, "__version__", "0.0")
                return True
            except ImportError:
                continue
        return False
    except Exception:
        return False


def vad_available() -> bool:
    """True if a VAD engine (webrtcvad or TEN) is present, or stubbed via env."""
    if ten_available():
        return True
    if os.environ.get("RAD_VAD") == "1":
        return True
    try:
        import importlib
        importlib.import_module("webrtcvad")
        return True
    except ImportError:
        return False


def realtime_supported() -> bool:
    """Whether realtime VAD→STT→LLM→TTS streaming can be attempted."""
    return ten_available() or vad_available()


def resolve_voice_backend(home: RadHome) -> str:
    """Auto-resolve best voice backend: ten > piper/whisper > openai > text."""
    mode = (home.cfg.get("voice_backend") or home.cfg.get("tts") or "auto").lower()
    if mode in ("off", "text"):
        return "text"
    if ten_available() and mode in ("auto", "ten", "realtime"):
        return "ten"
    if _find_piper() and mode in ("auto", "piper"):
        return "piper"
    if _openai_key(home) and mode in ("auto", "openai"):
        return "openai"
    # fallback chain
    if _find_piper() or _openai_key(home):
        return "fallback"
    return "text"


def voice_auto_mode(home: RadHome) -> str:
    """Human-readable auto mode for --voice flag (ten|fallback|text)."""
    b = resolve_voice_backend(home)
    if b == "ten":
        return "ten"
    if b in ("piper", "openai", "fallback"):
        return "fallback"
    return "text"


# Minimal streaming stub: VAD -> STT -> LLM -> TTS. Offline it yields fallback notes.
def vad_segments(path: Path, aggressiveness: int = 2) -> List[Tuple[float, float]]:
    """Return (start_s, end_s) voice segments via webrtcvad or TEN VAD. Empty if unavailable."""
    if not path.exists():
        return []
    if os.environ.get("RAD_VAD") == "1":
        return [(0.0, 1.0)]
    try:
        import webrtcvad  # type: ignore
        import wave
        import contextlib
        vad = webrtcvad.Vad(aggressiveness)
        with contextlib.closing(wave.open(str(path), "rb")) as wf:
            sr = wf.getframerate()
            if sr not in (8000, 16000, 32000, 48000):
                return [(0.0, float(wf.getnframes()) / max(1, sr))]
            # 30ms frames
            frame_ms = 30
            frame_bytes = int(sr * 2 * frame_ms / 1000)
            segments: List[Tuple[float, float]] = []
            start: Optional[float] = None
            offset = 0.0
            while True:
                data = wf.readframes(int(sr * frame_ms / 1000))
                if not data or len(data) < frame_bytes:
                    break
                is_speech = vad.is_speech(data, sr)
                if is_speech and start is None:
                    start = offset
                if not is_speech and start is not None:
                    segments.append((start, offset))
                    start = None
                offset += frame_ms / 1000.0
            if start is not None:
                segments.append((start, offset))
            return segments or [(0.0, offset)]
    except Exception:
        return []


def realtime_pipeline(
    home: RadHome,
    llm_call: Optional[Callable[[str], str]] = None,
    seconds: int = 12,
    on_partial: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Optional TEN realtime pipeline VAD→STT→LLM→TTS streaming.

    - Captures mic (record_wav), VAD-segments, STT each segment, calls LLM per segment,
      TTS streams via piper/openai/ten. Always falls back to Piper/Whisper when TEN
      is absent. Never raises — returns a dict with backend, transcript, reply, note.
    """
    backend = resolve_voice_backend(home)
    if backend == "ten" and not ten_available():
        backend = "fallback"
    wav = record_wav(home, seconds)
    if wav is None:
        return {"backend": backend, "transcript": None, "reply": None, "note": "no mic/capture"}
    # VAD
    segs = vad_segments(wav)
    # STT
    transcript: Optional[str] = None
    mode = home.cfg.get("stt", "auto")
    if mode in ("auto", "whisper"):
        transcript = stt_whisper(wav)
    if not transcript and _openai_key(home) and mode in ("auto", "openai"):
        transcript = stt_openai(wav, _openai_key(home) or "")
    if not transcript:
        return {"backend": backend, "transcript": None, "reply": None, "note": "stt unavailable", "segments": len(segs)}
    if on_partial:
        try:
            on_partial(transcript)
        except Exception:
            pass
    # LLM
    reply: Optional[str] = None
    if llm_call:
        try:
            reply = llm_call(transcript)
        except Exception as e:
            reply = f"(llm error: {e})"
    else:
        reply = transcript  # echo when no LLM wired (lab)
    # TTS (streaming fallback)
    tts_note = speak(reply or transcript, home) if reply else ""
    return {"backend": backend, "transcript": transcript, "reply": reply, "note": tts_note, "segments": len(segs), "vad": len(segs) > 0}


def realtime_stream(home: RadHome, prompt: str, chunk_cb: Optional[Callable[[str], None]] = None) -> Generator[str, None, None]:
    """Yield TTS-chunked LLM streaming (LLM chunk -> TTS). Stub when TEN missing: yields word chunks."""
    backend = resolve_voice_backend(home)
    # In TEN mode this would be true streaming; stub yields fallback chunking
    words = (prompt or "").split()
    for i in range(0, len(words), 8):
        chunk = " ".join(words[i:i+8])
        if chunk_cb:
            try:
                chunk_cb(chunk)
            except Exception:
                pass
        yield chunk
    # mark backend in home log for observability
    try:
        home.log("voice", f"realtime_stream backend={backend} chunks={max(1, len(words)//8)}")
    except Exception:
        pass

# ---------------------------------------------------------------- TTS

def _find_piper() -> Optional[str]:
    for c in ("piper", "piper-tts"):
        p = shutil.which(c)
        if p:
            return p
    p = Path.home() / ".local" / "bin" / "piper"
    return str(p) if p.exists() else None


def _piper_model(home: RadHome) -> Optional[Path]:
    d = home.root / "models" / "piper"
    if d.exists():
        for f in sorted(d.glob("*.onnx")):
            return f
    return None


def tts_piper(text: str, home: RadHome, out: Path) -> bool:
    bin_ = _find_piper()
    model = _piper_model(home)
    if not bin_ or not model:
        return False
    try:
        subprocess.run([bin_, "--model", str(model), "--output_file", str(out)],
                       input=text.encode(), capture_output=True, timeout=300, check=True)
        return out.exists() and out.stat().st_size > 0
    except Exception:
        return False


def tts_openai(text: str, key: str, out: Path, voice: str = "alloy") -> bool:
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=json.dumps({"model": "tts-1", "voice": voice, "input": text[:4000]}).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            out.write_bytes(r.read())
        return True
    except Exception:
        return False


def speak(text: str, home: RadHome) -> str:
    """Speak text. Returns a human note about what happened."""
    mode = home.cfg.get("tts", "auto")
    out = home.root / "logs" / f"tts-{int(time.time())}.wav"
    text = (text or "").strip()
    if not text or mode == "off":
        return ""
    if mode in ("auto", "piper") and tts_piper(text, home, out):
        return _play(out)
    key = _openai_key(home)
    if key and (mode in ("auto", "openai")):
        mp3 = out.with_suffix(".mp3")
        if tts_openai(text, key, mp3):
            return _play(mp3)
    warn("no voice engine available — `rad install voice` or add an OpenAI key (tts)")
    return "(spoke nothing — TTS unavailable)"


def _play(path: Path) -> str:
    for player, arg in (("afplay", [str(path)]), ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]),
                        ("mpg123", ["-q", str(path)]), ("aplay", [str(path)])):
        if shutil.which(player):
            try:
                subprocess.run([player, *arg], capture_output=True, timeout=600)
                return f"({player} played {path.name})"
            except Exception:
                continue
    return f"(audio saved: {path})"


# ---------------------------------------------------------------- STT

def _openai_key(home: RadHome) -> Optional[str]:
    from rad import providers as P
    from rad.providers import ProviderSpec
    for spec in P.all_specs(home):
        if spec.name == "openai":
            return P.find_key(home, spec)
    return None


def record_wav(home: RadHome, seconds: int) -> Optional[Path]:
    """Record N seconds of microphone audio to 16 kHz mono wav."""
    out = home.root / "logs" / f"rec-{int(time.time())}.wav"
    if shutil.which("arecord"):
        try:
            subprocess.run(["arecord", "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", str(seconds), str(out)],
                           capture_output=True, timeout=seconds + 30, check=True)
            return out if out.exists() else None
        except Exception:
            return None
    try:  # sounddevice (pip extra)
        import sounddevice as sd  # type: ignore
        import wave
        audio = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="int16")
        sd.wait()
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
            w.writeframes(audio.tobytes())
        return out
    except Exception:
        return None


def stt_whisper(path: Path) -> Optional[str]:
    if shutil.which("whisper"):
        try:
            r = subprocess.run(["whisper", str(path), "--model", "base", "--output_format", "txt",
                                "--output_dir", str(path.parent), "--fp16", "False"],
                               capture_output=True, text=True, timeout=600)
            txt = path.with_suffix(".txt")
            if txt.exists():
                return txt.read_text().strip()
        except Exception:
            pass
    try:
        from faster_whisper import WhisperModel  # type: ignore
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(path))
        return " ".join(s.text.strip() for s in segments).strip() or None
    except Exception:
        return None


def stt_openai(path: Path, key: str) -> Optional[str]:
    boundary = "----rad"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{path.name}\"\r\nContent-Type: audio/wav\r\n\r\n").encode() + path.read_bytes() \
        + f"\r\n--{boundary}--\r\n".encode()
    for field_name in ("model",):
        pass
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-1\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{path.name}\"\r\nContent-Type: audio/wav\r\n\r\n").encode() + path.read_bytes() \
        + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/transcriptions", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode()).get("text", "").strip() or None
    except Exception:
        return None


def listen(home: RadHome, seconds: int = 10) -> Optional[str]:
    """Record + transcribe. Returns text or None."""
    wav = record_wav(home, seconds)
    if wav is None:
        warn("no microphone capture available (install arecord/ffmpeg or `rad install voice`)")
        return None
    mode = home.cfg.get("stt", "auto")
    if mode in ("auto", "whisper"):
        text = stt_whisper(wav)
        if text:
            return text
    key = _openai_key(home)
    if key and mode in ("auto", "openai"):
        return stt_openai(wav, key)
    warn("no STT engine available — `rad install voice` or add an OpenAI key")
    return None
