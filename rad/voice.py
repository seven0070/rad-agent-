"""The voice socket — speak + listen.

Free-first: local Piper (TTS) + local Whisper (STT) when present,
provider APIs (OpenAI TTS/STT) when keys exist, graceful text-only otherwise.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

from rad.home import RadHome
from rad.ui import warn

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
