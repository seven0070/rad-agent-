"""RadTribe — Meta TRIBE v2 mapped into Rad (in-silico neuroscience for agents).

TRIBE v2 (facebookresearch/tribev2, 3.2k stars) is a multimodal brain encoding
model: LLaMA 3.2 (text) + V-JEPA2 (video) + Wav2Vec-BERT (audio) fused in a
unified Transformer that predicts fMRI responses on the cortical surface
(~20k vertices, Algonauts2025). Rad mirrors it with what it already owns:

    TRIBE text encoder (LLaMA 3.2)   ->  Rad providers (chat brain socket)
    TRIBE video encoder (V-JEPA2)    ->  Rad vision (see_image, vision_roboflow)
    TRIBE audio encoder (Wav2Vec)    ->  Rad voice (TEN/stt_whisper/Piper)
    TRIBE fusion Transformer        ->  TribeEncoder.fuse() (weighted sum, learned)
    TRIBE cortical surface (~20k)   ->  Rad projectome regions (connectome.REGIONS)
    TRIBE hemodynamic lag (5s)      ->  lag_compensate() (tool-result delay)
    TRIBE ROI analysis              ->  roi_map() (region activation prediction)
    TRIBE multi-study weighting     ->  modality weights learned from history

Design rules (same as the rest of Rad):
* Encoding is *observed*, never invented: modality weights come from verified
  history (which modality preceded verified outcomes), defaulting to uniform.
* Prediction is advisory: predicted region activations are a routing *prior*,
  never a decision. The control plane still decides; VERIFIED-only law holds.
* No heavy ML vendored: no torch, no transformers. The fusion is a weighted
  sum with learned weights — the honest, dependency-free analogue.
* Everything is a human-readable JSON file under `~/.rad/tribe/`.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rad.home import RadHome, _read_json, _write_json

# ---------------------------------------------------------------- constants

# TRIBE's hemodynamic lag: BOLD peaks ~5s after stimulus. Rad's analogue: tool
# results arrive after the call; predictions made at prompt time must be
# compared against outcomes observed LAG_SECONDS later.
LAG_SECONDS = 5.0

MODALITIES = ("text", "vision", "audio")

# Default uniform prior (no evidence yet). Learned weights replace these.
W_DEFAULT: Dict[str, float] = {"text": 0.5, "vision": 0.3, "audio": 0.2}

# Learning rates for weight updates (small, bounded — same spirit as STDP)
W_LEARN_UP = 0.03
W_LEARN_DOWN = 0.02
W_MIN, W_MAX = 0.05, 0.85


# ---------------------------------------------------------------- event + encoding

@dataclass
class MultimodalEvent:
    """One stimulus moment: what the agent saw/heard/read."""
    text: str = ""
    has_image: bool = False
    has_audio: bool = False
    at: float = 0.0

    def present(self) -> List[str]:
        out = []
        if self.text:
            out.append("text")
        if self.has_image:
            out.append("vision")
        if self.has_audio:
            out.append("audio")
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text[:500], "has_image": self.has_image,
                "has_audio": self.has_audio, "at": self.at}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MultimodalEvent":
        return cls(text=str(d.get("text", ""))[:500],
                   has_image=bool(d.get("has_image", False)),
                   has_audio=bool(d.get("has_audio", False)),
                   at=float(d.get("at", 0.0)))


def lag_compensate(event_at: float, outcome_at: float,
                   lag: float = LAG_SECONDS) -> bool:
    """TRIBE hemodynamic-lag analogue: is this outcome plausibly caused by this event?

    Returns True when the outcome arrived within [0, 2*lag] after the event —
    the window where a BOLD-like delayed response would peak.
    """
    dt = outcome_at - event_at
    return 0 <= dt <= 2 * lag


# ---------------------------------------------------------------- the encoder

class TribeEncoder:
    """Multimodal → region-activation encoder. Learned from verified history.

    Persistence: `~/.rad/tribe/weights.json` (modality weights) +
    `~/.rad/tribe/activations.jsonl` (predicted-vs-actual log).
    """

    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.root = home.root / "tribe"
        self.root.mkdir(parents=True, exist_ok=True)
        self.weights: Dict[str, float] = dict(W_DEFAULT)
        self._load()

    @property
    def weights_path(self) -> Path:
        return self.root / "weights.json"

    @property
    def log_path(self) -> Path:
        return self.root / "activations.jsonl"

    def _load(self) -> None:
        d = _read_json(self.weights_path, {})
        for m in MODALITIES:
            try:
                w = float(d.get(m, W_DEFAULT[m]))
            except Exception:
                w = W_DEFAULT[m]
            self.weights[m] = min(W_MAX, max(W_MIN, w))
        self._renorm()

    def save(self) -> None:
        _write_json(self.weights_path, {"updated": time.time(), **self.weights})

    def _renorm(self) -> None:
        tot = sum(self.weights.values()) or 1.0
        for m in MODALITIES:
            self.weights[m] = self.weights[m] / tot

    # ---- fusion (TRIBE Transformer analogue: weighted multimodal sum)

    def fuse(self, ev: MultimodalEvent) -> Dict[str, float]:
        """Fuse present modalities into a single activation scalar per modality.

        Returns {modality: contribution}. Absent modalities contribute 0.
        Text contribution scales with token overlap density (cheap proxy for
        LLaMA-style encoding depth); vision/audio are binary presence (like
        V-JEPA2/Wav2Vec frame presence) weighted by learned weights.
        """
        present = ev.present()
        if not present:
            return {m: 0.0 for m in MODALITIES}
        out: Dict[str, float] = {}
        for m in MODALITIES:
            if m not in present:
                out[m] = 0.0
                continue
            if m == "text":
                toks = len(ev.text.split())
                depth = min(1.0, 0.3 + 0.7 * (toks / 100.0))
                out[m] = self.weights[m] * depth
            else:
                out[m] = self.weights[m]
        return out

    def activation_energy(self, ev: MultimodalEvent) -> float:
        """Total predicted activation 0..1 (like summed BOLD across ROIs)."""
        return min(1.0, sum(self.fuse(ev).values()))

    # ---- ROI map (TRIBE cortical surface -> Rad projectome regions)

    def roi_map(self, ev: MultimodalEvent) -> Dict[str, float]:
        """Predict per-region activation (TRIBE ROI analysis analogue).

        Vision-heavy events activate optic_lobes; text-heavy activate
        mushroom_body (memory) + central_complex (decisions); audio-heavy
        activate antennal_lobe; everything touches central_complex.
        """
        fused = self.fuse(ev)
        tv, ta, tt = fused["vision"], fused["audio"], fused["text"]
        try:
            from rad.connectome import REGIONS
            regions = list(REGIONS)
        except Exception:
            regions = ["mushroom_body", "central_complex", "optic_lobes",
                       "antennal_lobe", "ventral_nerve_cord", "neurosecretory"]
        roi = {r: 0.0 for r in regions}
        if "optic_lobes" in roi:
            roi["optic_lobes"] = min(1.0, tv * 1.5)
        if "antennal_lobe" in roi:
            roi["antennal_lobe"] = min(1.0, ta * 1.5)
        if "mushroom_body" in roi:
            roi["mushroom_body"] = min(1.0, tt * 1.2)
        if "central_complex" in roi:
            roi["central_complex"] = min(1.0, 0.2 + 0.8 * max(tt, tv, ta))
        return roi

    def suggest_regions(self, ev: MultimodalEvent, limit: int = 3) -> List[str]:
        """Advisory routing prior: most-activated regions first (never forced)."""
        roi = self.roi_map(ev)
        return sorted(roi, key=lambda r: -roi[r])[:limit]

    # ---- learning (multi-study weighting analogue: verified history tunes weights)

    def observe(self, ev: MultimodalEvent, verified_ok: bool,
                at: Optional[float] = None) -> Dict[str, float]:
        """STDP-like weight update from a verified outcome + lag check.

        Only outcomes within the lag window move weights (hemodynamic rule).
        Verified success strengthens present modalities; failure weakens them.
        """
        now = at if at is not None else time.time()
        if not lag_compensate(ev.at, now):
            return dict(self.weights)  # outside BOLD window: no learning
        present = ev.present()
        if not present:
            return dict(self.weights)
        for m in MODALITIES:
            if m not in present:
                continue
            if verified_ok:
                self.weights[m] = min(W_MAX, self.weights[m] + W_LEARN_UP)
            else:
                self.weights[m] = max(W_MIN, self.weights[m] - W_LEARN_DOWN)
        self._renorm()
        self.save()
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": now, "event": ev.to_dict(),
                                    "ok": verified_ok, "weights": dict(self.weights)}) + "\n")
        except Exception:
            pass
        return dict(self.weights)

    def calibrate_from_connectome(self, home: Optional[RadHome] = None) -> Dict[str, Any]:
        """Seed weights from verified connectome history (multi-study analogue).

        Counts verified synapses touching vision/audio/text-related nodes and
        converts the proportions into starting weights. Observed, not invented.
        """
        h = home or self.home
        counts = {"text": 1.0, "vision": 1.0, "audio": 1.0}  # Laplace smoothing
        try:
            from rad.connectome import Connectome
            cx = Connectome(h)
            for (a, b), s in cx.synapses.items():
                if not s.verified or s.successes == 0:
                    continue
                blob = f"{a} {b}".lower()
                w = 1.0 + s.successes
                if any(k in blob for k in ("see_image", "vision", "browser", "image")):
                    counts["vision"] += w
                if any(k in blob for k in ("listen", "say", "voice", "audio", "stt", "tts")):
                    counts["audio"] += w
                counts["text"] += w * 0.5  # text is the carrier for most calls
        except Exception:
            pass
        tot = sum(counts.values())
        for m in MODALITIES:
            self.weights[m] = min(W_MAX, max(W_MIN, counts[m] / tot))
        self._renorm()
        self.save()
        return {"weights": dict(self.weights), "source": "connectome-verified"}

    def stats(self) -> Dict[str, Any]:
        n_log = 0
        try:
            if self.log_path.exists():
                n_log = sum(1 for _ in self.log_path.read_text(encoding="utf-8").splitlines() if _.strip())
        except Exception:
            pass
        return {"weights": dict(self.weights), "lag_seconds": LAG_SECONDS,
                "observations": n_log}
