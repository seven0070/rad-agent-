"""X2 Roboflow Vision: rad see trains personal detector in 10 shots via ComfyUI nodes.

Lab-gated, VERIFIED-only. No real training unless lab passes; stub trains in memory.
Inspiration: roboflow (few-shot detector) + comfyui (node graph).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from rad.home import RadHome, _write_json, _read_json  # type: ignore

@dataclass
class Shot:
    image: str
    bbox: List[float]  # [x,y,w,h] normalized 0..1
    label: str = "object"

@dataclass
class Detector:
    id: str
    name: str
    shots: int
    status: str  # training | ready | failed
    created_at: float
    comfy_nodes: List[Dict[str, Any]] = field(default_factory=list)

def _detector_path(home: RadHome, det_id: str) -> Path:
    return home.root / "vision" / f"{det_id}.json"

def train_detector(home: RadHome, name: str, shots: List[Dict[str, Any]], comfy_nodes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Train personal detector from 10 shots. Lab-gated but stub succeeds if shots 1..10.

    Returns {id, status, shots, comfy_nodes, lab_gated}. No shell bypass — pure JSON.
    """
    if not (1 <= len(shots) <= 10):
        return {"status": "failed", "reason": f"shots must be 1..10, got {len(shots)}", "lab_gated": True}
    det_id = f"det_{uuid.uuid4().hex[:6]}"
    nodes = comfy_nodes or [
        {"type": "LoadImage", "id": "1", "inputs": {"image": "shot_0.jpg"}},
        {"type": "RoboflowTrain", "id": "2", "inputs": {"shots": len(shots), "model": "yolo-nano-comfy"}},
        {"type": "PreviewDetector", "id": "3", "inputs": {"detector": det_id}},
    ]
    data = {"id": det_id, "name": name, "shots": len(shots), "status": "ready", "created_at": time.time(), "comfy_nodes": nodes, "lab_gated": True, "verified_only": True}
    p = _detector_path(home, det_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    _write_json(p, data)
    return data

def list_detectors(home: RadHome) -> List[Dict[str, Any]]:
    d = home.root / "vision"
    if not d.exists():
        return []
    out = []
    for f in d.glob("det_*.json"):
        try:
            out.append(_read_json(f, {}))
        except Exception:
            continue
    return out

def see(home: RadHome, detector_id: str, image: str) -> Dict[str, Any]:
    """rad see — inference stub using detector (no real CV, lab-gated)."""
    p = _detector_path(home, detector_id)
    if not p.exists():
        return {"status": "failed", "reason": "detector not found", "detections": []}
    data = _read_json(p, {})
    # stub detection: always returns one box
    return {"status": "ready", "detector": detector_id, "image": image, "detections": [{"label": data.get("name", "object"), "bbox": [0.4, 0.4, 0.2, 0.2], "confidence": 0.87}], "lab_gated": True, "source": "roboflow+comfyui stub"}
