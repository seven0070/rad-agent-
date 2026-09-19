"""v1.0.1 Class A — doctor / health ping honors pinned cfg.model (RW-102).

Investigate-first (OpenRouter free soak 2026-09-19):
- force_provider=openrouter, model=deepseek/deepseek-v4-flash-0731:free
- Direct chat / ``rad router chat`` to the pin returned HTTP 200
- ``rad doctor`` / ``rad health`` reported not inference-entitled because
  ``probe_inference`` pinged the stale OpenRouter default
  ``meta-llama/llama-3.3-70b-instruct:free`` → 404
- NVIDIA 403 is separate Class C noise, not this hole

Class A CONFIRMED: entitlement ping used ``spec.default_model`` instead of
the configured pin. Smallest fix: ``inference_probe_model`` / probe path
uses ``cfg.model`` for the pinned provider. 403/429 on the pin stay Class C.
Needle OFF. Caps unchanged. F-17 / F-26 stay closed. No live PASS claim.
No GitHub Release / tag.
"""
from __future__ import annotations

import json
from unittest import mock

from rad import __version__
from rad import providers as P
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.doctor import Doctor
from rad.health import (
    inference_probe_model,
    probe_inference,
    probe_provider_health,
    scan_provider_health,
)
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router

OR_DEFAULT = "meta-llama/llama-3.3-70b-instruct:free"
OR_PIN = "deepseek/deepseek-v4-flash-0731:free"
NV_DEFAULT = "meta/llama-3.2-11b-vision-instruct"

OR_SPEC = P.ProviderSpec(
    "openrouter", "openai", "https://openrouter.ai/api/v1",
    ("OPENROUTER_API_KEY",), default_model=OR_DEFAULT, tier="free")
NV_SPEC = P.ProviderSpec(
    "nvidia", "openai", "https://integrate.api.nvidia.com/v1",
    ("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"),
    default_model=NV_DEFAULT, tier="free")


def _catalog_ok(url, data, headers, timeout, stream=False):
    if "/models" in str(url):
        return 200, {}, json.dumps({"data": [{"id": "x"}]}).encode()
    return 200, {}, b"{}"


def _soak_chat(spec, key, messages, **kw):
    """OpenRouter stale default 404; pin 200; NVIDIA default 403 Class C."""
    model = kw.get("model") if kw.get("model") is not None else spec.default_model
    model = str(model or "")
    if spec.name == "openrouter" and OR_DEFAULT in model:
        raise P.ProviderError(
            "openrouter: HTTP 404 No endpoints found for this model",
            status=404, retryable=False)
    if spec.name == "openrouter" and "deepseek" in model:
        return P.ChatResult(text="ok", provider="openrouter", model=model)
    if spec.name == "nvidia":
        raise P.ProviderError(
            "nvidia: HTTP 403 Authorization failed", status=403, retryable=False)
    raise P.ProviderError(f"{spec.name}: HTTP 404 {model}", status=404, retryable=False)


# ---------------------------------------------------------------- architecture freeze

def test_v101_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new("Write a file and then read it back"))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())


# ---------------------------------------------------------------- RW-102 pinned model ping

def test_rw102_inference_probe_model_uses_pin_for_forced_provider(home):
    home.update(force_provider="openrouter", model=OR_PIN)
    assert inference_probe_model(OR_SPEC, home) == OR_PIN
    assert inference_probe_model(NV_SPEC, home) == NV_DEFAULT
    home.update(force_provider=None, model=None)
    assert inference_probe_model(OR_SPEC, home) == OR_DEFAULT


def test_rw102_stale_default_404_pin_200_is_entitled(home):
    """Soak shape: llama default 404 is not 'not entitled' when the pin is 200."""
    home.update(force_provider="openrouter", model=OR_PIN)
    with mock.patch.object(P, "chat", side_effect=_soak_chat):
        h = probe_inference(OR_SPEC, "sk-or-test", home=home)
    assert h.model == OR_PIN
    assert h.inference_entitled is True
    assert h.inference_status == 200


def test_rw102_without_pin_stale_default_404_is_not_entitled(home):
    home.update(force_provider="openrouter", model=None)
    with mock.patch.object(P, "chat", side_effect=_soak_chat):
        h = probe_inference(OR_SPEC, "sk-or-test", home=home)
    assert h.model == OR_DEFAULT
    assert h.inference_entitled is False
    assert h.inference_status == 404


def test_rw102_nvidia_403_on_its_default_stays_class_c(home):
    """Do not invent Class A for NVIDIA 403; pin on openrouter must not rewrite that ping."""
    home.update(force_provider="openrouter", model=OR_PIN)
    with mock.patch.object(P, "chat", side_effect=_soak_chat):
        h = probe_inference(NV_SPEC, "nvapi-test", home=home)
    assert h.model == NV_DEFAULT
    assert h.inference_entitled is False
    assert h.inference_status == 403
    assert h.kind == "auth"


def test_rw102_scan_entitles_openrouter_pin_despite_llama_404(home):
    home.update(force_provider="openrouter", model=OR_PIN, free_lock=True)
    calls = []

    def tracking_chat(spec, key, messages, **kw):
        calls.append((spec.name, kw.get("model")))
        return _soak_chat(spec, key, messages, **kw)

    with mock.patch.dict(__import__("os").environ, {
        "OPENROUTER_API_KEY": "sk-or-xxxx",
        "NVIDIA_NIM_API_KEY": "nvapi-xxxx",
    }):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch.object(P, "_http", side_effect=_catalog_ok):
                with mock.patch.object(P, "chat", side_effect=tracking_chat):
                    hs = scan_provider_health(home, skip_blocked_inference=False, force=True)
    by_name = {h.name: h for h in hs}
    assert "openrouter" in by_name
    assert by_name["openrouter"].inference_entitled is True
    assert by_name["openrouter"].model == OR_PIN
    assert ("openrouter", OR_PIN) in calls
    assert ( "openrouter", OR_DEFAULT) not in calls
    if "nvidia" in by_name:
        assert by_name["nvidia"].inference_entitled is False
        assert by_name["nvidia"].inference_status == 403
        assert by_name["nvidia"].model == NV_DEFAULT


def test_rw102_doctor_ready_when_pin_entitled(home):
    home.update(force_provider="openrouter", model=OR_PIN, free_lock=True)
    with mock.patch.dict(__import__("os").environ, {"OPENROUTER_API_KEY": "sk-or-xxxx"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch.object(P, "_http", side_effect=_catalog_ok):
                with mock.patch.object(P, "chat", side_effect=_soak_chat):
                    fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    assert fs["providers"].status == "ok"
    blob = fs["providers"].message + " " + " ".join(fs["providers"].detail)
    assert "inference-entitled" in blob
    assert "openrouter" in fs["providers"].message
    assert OR_PIN in blob


def test_rw102_403_on_the_pin_stays_class_c_not_product_ok(home):
    home.update(force_provider="openrouter", model=OR_PIN)

    def pin_forbidden(spec, key, messages, **kw):
        raise P.ProviderError(
            "openrouter: HTTP 403 Authorization failed", status=403, retryable=False)

    with mock.patch.object(P, "_http", side_effect=_catalog_ok):
        with mock.patch.object(P, "chat", side_effect=pin_forbidden):
            h = probe_provider_health(OR_SPEC, "sk-or-test", home=home)
    assert h.model == OR_PIN
    assert h.inference_entitled is False
    assert h.inference_status == 403
    assert h.kind == "auth"
    assert h.catalog_alive is True
