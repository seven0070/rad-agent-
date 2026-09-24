"""RadTribe — Meta TRIBE v2 mapped into Rad.

Covers: multimodal events, fusion, lag compensation, ROI map, suggest order,
STDP-like learning bounds, calibration from connectome, persistence, CLI wiring.
"""
from __future__ import annotations

import time

from rad.tribe import (LAG_SECONDS, MODALITIES, W_DEFAULT, W_MAX, W_MIN,
                       MultimodalEvent, TribeEncoder, lag_compensate)


def test_event_present_modalities():
    ev = MultimodalEvent(text="hello")
    assert ev.present() == ["text"]
    ev2 = MultimodalEvent(text="x", has_image=True, has_audio=True)
    assert set(ev2.present()) == {"text", "vision", "audio"}
    assert MultimodalEvent().present() == []


def test_fuse_absent_zero(home):
    enc = TribeEncoder(home)
    assert enc.fuse(MultimodalEvent()) == {"text": 0.0, "vision": 0.0, "audio": 0.0}


def test_fuse_text_scales_with_length(home):
    enc = TribeEncoder(home)
    short = enc.fuse(MultimodalEvent(text="hi"))
    long = enc.fuse(MultimodalEvent(text="word " * 200))
    assert long["text"] > short["text"]
    assert short["vision"] == 0.0 and short["audio"] == 0.0


def test_fuse_vision_audio_presence(home):
    enc = TribeEncoder(home)
    f = enc.fuse(MultimodalEvent(text="x", has_image=True, has_audio=True))
    assert f["vision"] > 0 and f["audio"] > 0 and f["text"] > 0


def test_activation_energy_bounded(home):
    enc = TribeEncoder(home)
    e = enc.activation_energy(MultimodalEvent(text="x " * 500, has_image=True, has_audio=True))
    assert 0.0 <= e <= 1.0
    assert enc.activation_energy(MultimodalEvent()) == 0.0


def test_lag_compensate_window():
    now = time.time()
    assert lag_compensate(now, now + 1) is True
    assert lag_compensate(now, now + 2 * LAG_SECONDS) is True
    assert lag_compensate(now, now + 2 * LAG_SECONDS + 1) is False
    assert lag_compensate(now, now - 1) is False


def test_roi_map_vision_dominant(home):
    enc = TribeEncoder(home)
    roi = enc.roi_map(MultimodalEvent(text="x", has_image=True))
    assert roi["optic_lobes"] >= roi.get("antennal_lobe", 0.0)
    assert all(0.0 <= v <= 1.0 for v in roi.values())


def test_roi_map_audio_dominant(home):
    enc = TribeEncoder(home)
    roi = enc.roi_map(MultimodalEvent(text="x", has_audio=True))
    assert roi["antennal_lobe"] >= roi.get("optic_lobes", 0.0)


def test_suggest_order(home):
    enc = TribeEncoder(home)
    sug = enc.suggest_regions(MultimodalEvent(text="plan the objective"), limit=3)
    assert len(sug) == 3
    assert "central_complex" in sug or "mushroom_body" in sug


def test_observe_strengthens_verified(home):
    enc = TribeEncoder(home)
    before = dict(enc.weights)
    ev = MultimodalEvent(text="do the thing", at=time.time())
    enc.observe(ev, verified_ok=True)
    assert enc.weights["text"] >= before["text"]


def test_observe_weakens_failure(home):
    enc = TribeEncoder(home)
    before = dict(enc.weights)
    ev = MultimodalEvent(text="do the thing", at=time.time())
    enc.observe(ev, verified_ok=False)
    assert enc.weights["text"] <= before["text"]


def test_observe_outside_lag_no_learning(home):
    enc = TribeEncoder(home)
    before = dict(enc.weights)
    ev = MultimodalEvent(text="old event", at=time.time() - 3600)
    enc.observe(ev, verified_ok=True)
    assert enc.weights == before


def test_observe_bounds(home):
    enc = TribeEncoder(home)
    for _ in range(200):
        enc.observe(MultimodalEvent(text="x", at=time.time()), verified_ok=True)
    assert all(W_MIN <= w <= W_MAX for w in enc.weights.values())
    assert abs(sum(enc.weights.values()) - 1.0) < 1e-6


def test_calibrate_from_empty_connectome(home):
    enc = TribeEncoder(home)
    res = enc.calibrate_from_connectome()
    assert res["source"] == "connectome-verified"
    assert set(res["weights"]) == set(MODALITIES)
    assert abs(sum(res["weights"].values()) - 1.0) < 1e-6


def test_persistence_roundtrip(home):
    enc = TribeEncoder(home)
    enc.weights["vision"] = 0.6
    enc._renorm()  # real flows (observe/calibrate) always renorm before save
    enc.save()
    enc2 = TribeEncoder(home)
    assert abs(enc2.weights["vision"] - enc.weights["vision"]) < 1e-9


def test_stats_shape(home):
    enc = TribeEncoder(home)
    st = enc.stats()
    assert set(st["weights"]) == set(MODALITIES)
    assert st["lag_seconds"] == LAG_SECONDS
    assert isinstance(st["observations"], int)


def test_modalities_default_sane():
    assert set(MODALITIES) == {"text", "vision", "audio"}
    assert abs(sum(W_DEFAULT.values()) - 1.0) < 1e-6
