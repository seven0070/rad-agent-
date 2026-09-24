"""Embodied edge — signature weird.

Edge runtime stub: runs on device via Ollama/Edge0, offline-first.
Lab-gated, VERIFIED-only — embodied tasks still need machine checks.
"""

from __future__ import annotations

from typing import Any, Dict

from rad.home import RadHome
from rad.providers import magnitude_hardware_profile

def embodied_health(home: RadHome) -> Dict[str, Any]:
    prof = magnitude_hardware_profile(home)
    return {"embodied": "edge runtime", "offline_first": True, "ram_gb": prof["ram_gb"], "recommended_gguf": prof["recommended_gguf"]["model"], "edge0_or_ollama": "Edge0 -> Ollama fallback", "lab_gated": True, "note": "embodied edge — local inference, cloud fallback"}
