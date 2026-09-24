"""Omarchy OS: Rad as OS fork stub — X4 Omarchy OS.

Opinionated OS layer: Rad owns the loop, default apps, keymaps.
Lab-gated placeholder — no real fork, just manifest + opinionated config.
Inspiration: omarchy (opinionated arch).
"""

from __future__ import annotations

from typing import Any, Dict

from rad.home import RadHome

OMARCHY_MANIFEST = {
    "os": "rad-omarchy",
    "base": "archlinux (omarchy fork stub)",
    "wm": "hyprland (opinionated tiling)",
    "terminal": "kitty + rad",
    "bar": "waybar (rad vitals)",
    "editor": "neovim (rad skills)",
    "defaults": {
        "objective_parallel": 8,
        "accept_unverified_done": False,
        "tool_router": "existing",
        "free_lock": False,
        "provider_pin": "nvidia",
        "model_nvidia": "meta/llama-3.2-11b-vision-instruct",
        "verification": "VERIFIED-only",
        "needle": "OFF 16/60 VERIFIED",
    },
    "manual_path": "manual/",
    "fork": "stub — no ISO built, manifest only",
}

def omarchy_manifest(home: RadHome | None = None) -> Dict[str, Any]:
    return dict(OMARCHY_MANIFEST)

def health(home: RadHome) -> Dict[str, Any]:
    return {"omarchy_os": "fork stub", "manifest": OMARCHY_MANIFEST, "lab_gated": True, "iso": "not_built_stub"}
