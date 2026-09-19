"""v0.5.1 G4-2 — live-gate resume / provider health observability (RW-090 / RW-091).

Investigate-first (ROADMAP G4-2 entry):
- RW-084: rad doctor READY (1 usable: nvidia) while GET /v1/models 200 and
  every chat/completions 403. Catalog-alive ≠ inference-entitled.
- RW-086: working then 429 free-models-per-day with no durable last-Class-C /
  retry-after surface. RouterState.failures is in-process only.
- rad objective resume reopened NEEDS_USER and would re-hit the same 403.

G4-2: doctor must not READY a 403-chat pin; last Class C persists; resume
gates until an inference-entitled brain recovers. No Class A for 403/429.
No silent paid under free_lock. Caps 16/60. Needle OFF. No live PASS claim.
"""
from __future__ import annotations

import json
from unittest import mock

from rad import __version__
from rad import providers as P
from rad.control import ObjectiveStatus, TaskStatus
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_missing_optional_checksum_utility,
    is_missing_python_script,
    is_pip_requirements_file_missing,
)
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.control.recovery import FailureClass
from rad.doctor import Doctor
from rad.health import (
    LiveGate,
    ProviderHealth,
    class_c_still_blocks,
    evaluate_live_gate,
    last_class_c,
    probe_provider_health,
    record_class_c,
    scan_provider_health,
)
from rad.home import DEFAULTS
from rad.router import RouterState
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_provider_class_c import RW089_PLAN
from tests.test_xxd_environment import XXD_CMD, XXD_ERR


# ---------------------------------------------------------------- architecture freeze

def test_g42_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.0"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_prior_class_a_helpers_still_hold():
    assert infer_package_dir(RW073_ASCII_GOAL) == "text_analyzer/"
    assert is_done_protocol_tool("DONE: wrote input")
    assert is_pip_requirements_file_missing(
        "ERROR: Could not open requirements file: [Errno 2] No such file or directory: "
        "'requirements.txt'",
        "pip install -r requirements.txt")
    assert is_mkdir_already_exists(MKDIR_ERR, "mkdir text_analyzer")
    assert is_missing_python_script(PREMATURE_TEST_ERR, PREMATURE_TEST_CMD)
    assert is_missing_optional_checksum_utility(XXD_ERR, XXD_CMD)


def test_fallback_tasks_stay_checkless_f17(tmp_path):
    res = Planner(None, str(tmp_path)).plan(Objective.new("Write a file and then read it back"))
    assert res["source"] == "fallback"
    assert all(not t.checks for t in res["graph"].tasks.values())


def test_parse_retry_after_seconds_and_http_date():
    assert P.parse_retry_after({"Retry-After": "90"}) == 90.0
    assert P.parse_retry_after({"retry-after": "0"}) is None
    assert P.parse_retry_after({}) is None
    assert "Retry-After" in P.class_c_next_steps("rate_limit", retry_after=45)
    assert "wait 45s" in P.class_c_next_steps("rate_limit", retry_after=45)


# ---------------------------------------------------------------- RW-090 catalog ≠ inference (RW-084 shape)

def test_rw090_probe_catalog_alive_not_inference_entitled(home):
    spec = P.ProviderSpec("nvidia", "openai", "https://example.test/v1",
                          default_model="meta/llama-3.2-11b-vision-instruct", tier="free")

    def fake_http(url, data, headers, timeout, stream=False):
        if str(url).endswith("/models"):
            return 200, {}, json.dumps({"data": [{"id": spec.default_model}]}).encode()
        return 403, {}, b'{"error":{"message":"Authorization failed"}}'

    def fake_chat(spec_, key, messages, **kw):
        raise P.ProviderError("nvidia: HTTP 403 Authorization failed", status=403, retryable=False)

    with mock.patch.object(P, "_http", side_effect=fake_http):
        with mock.patch.object(P, "chat", side_effect=fake_chat):
            h = probe_provider_health(spec, "nvapi-test", home=home)
    assert h.catalog_alive is True
    assert h.catalog_status == 200
    assert h.inference_entitled is False
    assert h.inference_status == 403
    assert h.kind == "auth"
    last = last_class_c(home)
    assert last is not None
    assert last["provider"] == "nvidia"
    assert last["kind"] == "auth"
    assert last["status"] == 403
    assert last["class_c"] is True
    assert "Class C" in (last.get("next_steps") or "")


def test_rw090_doctor_does_not_ready_403_chat_pin(home):
    fake = [ProviderHealth(
        name="nvidia", catalog_alive=True, catalog_status=200,
        inference_entitled=False, inference_status=403, kind="auth",
        err="Authorization failed", tier="free",
    )]
    with mock.patch("rad.doctor.scan_provider_health", return_value=fake):
        fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    assert fs["providers"].status == "warn"
    assert fs["providers"].status != "ok"
    blob = fs["providers"].message + " " + " ".join(fs["providers"].detail)
    assert "catalog-alive" in blob
    assert "inference-entitled" in blob
    assert "403" in blob


def test_rw090_doctor_ready_only_when_inference_entitled(home):
    fake = [ProviderHealth(name="groq", catalog_alive=True, catalog_status=200,
                           inference_entitled=True, inference_status=200, tier="free")]
    with mock.patch("rad.doctor.scan_provider_health", return_value=fake):
        fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    assert fs["providers"].status == "ok"
    assert "inference-entitled" in fs["providers"].message


# ---------------------------------------------------------------- RW-091 persist + resume + 429 (RW-086 shape)

def test_rw091_last_class_c_survives_new_router_state(home):
    record_class_c(home, "nvidia", kind="auth", status=403,
                   err="nvidia: HTTP 403 Authorization failed", catalog_alive=True)
    r1 = RouterState(home)
    assert r1.failures["nvidia"].get("class_c") is True
    r2 = RouterState(home)
    assert r2.failures["nvidia"].get("class_c") is True
    last = last_class_c(home)
    assert last["kind"] == "auth"
    assert last["status"] == 403
    assert class_c_still_blocks(last)


def test_rw091_403_resume_stays_needs_user_no_reburn(home, tmp_path):
    ws_dir = tmp_path / "ws_rw091_403"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        P.ProviderError("all providers failed: nvidia: HTTP 403 Authorization failed",
                        status=403, retryable=False),
        ([("write_file", {"path": "hello.txt", "content": "x"})], "DONE"),
    ]
    ScriptedSession.prompts = []
    leftover = list(ScriptedSession.script[1:])
    ctl = _ctl(home, ScriptedSession, RW089_PLAN)
    obj = ctl.run(ctl.create("write hello.txt", auto=True))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    last = last_class_c(home)
    assert last is not None
    assert last["kind"] == "auth"
    assert last["status"] == 403
    assert last["objective_id"] == obj.id

    ScriptedSession.script = leftover
    ctl2 = _ctl(home, ScriptedSession, RW089_PLAN)
    obj2 = ctl2.resume(obj.id)
    assert obj2.status == ObjectiveStatus.NEEDS_USER
    gate = ctl2.last_run.get("live_gate") or {}
    assert gate.get("allow") is False
    assert "Class C" in (obj2.failure or "") or "inference-entitled" in (gate.get("reason") or "")
    assert ScriptedSession.script == leftover
    assert not (ws_dir / "hello.txt").exists()
    t1 = next(t for t in ctl2.load_graph(obj2).tasks.values()
              if t.id == "t1" or "hello" in (t.text or "").lower())
    assert t1.status == TaskStatus.NEEDS_USER
    assert t1.failure_class == FailureClass.AUTH


def test_rw091_429_retry_after_visible_without_tool_burn(home):
    rec = record_class_c(
        home, "openrouter", kind="rate_limit", status=429,
        err="openrouter: HTTP 429 free-models-per-day", retry_after=120,
        catalog_alive=True,
    )
    assert rec["retry_after"] == 120
    assert rec["retry_after_until"] > rec["at"]
    assert class_c_still_blocks(rec)
    assert "Retry-After" in rec["next_steps"]
    assert "wait 120s" in rec["next_steps"]

    fake = [ProviderHealth(
        name="openrouter", catalog_alive=True, catalog_status=200,
        inference_entitled=False, inference_status=429, kind="rate_limit",
        retry_after=120, err="free-models-per-day", tier="free",
    )]
    with mock.patch("rad.doctor.scan_provider_health", return_value=fake):
        fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    blob = fs["providers"].message + " " + " ".join(fs["providers"].detail)
    assert fs["providers"].status == "warn"
    assert "429" in blob
    assert "catalog-alive" in blob
    assert "Retry-After" in blob or "rate" in blob.lower()


def test_rw091_resume_when_entitled_brain_recovers(home, tmp_path):
    ws_dir = tmp_path / "ws_rw091_ok"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        P.ProviderError("all providers failed: nvidia: HTTP 403 Authorization failed",
                        status=403, retryable=False),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW089_PLAN)
    obj = ctl.run(ctl.create("write hello.txt", auto=True))
    assert obj.status == ObjectiveStatus.NEEDS_USER

    ScriptedSession.script = [
        ([("write_file", {"path": "hello.txt", "content": "x"})], "DONE"),
    ]
    entitled = [ProviderHealth(name="groq", catalog_alive=True, catalog_status=200,
                               inference_entitled=True, inference_status=200, tier="free")]
    ctl2 = _ctl(home, ScriptedSession, RW089_PLAN)
    with mock.patch("rad.health.scan_provider_health", return_value=entitled):
        obj2 = ctl2.resume(obj.id)
    assert obj2.status == ObjectiveStatus.COMPLETED
    assert (ws_dir / "hello.txt").exists()
    gate = ctl2.last_run.get("live_gate") or {}
    assert gate.get("allow") is True


def test_rw091_resume_skips_chat_on_blocked_auth(home):
    record_class_c(home, "nvidia", kind="auth", status=403,
                   err="nvidia: HTTP 403 Authorization failed",
                   key="nvapi-xxxx", objective_id="obj_gate", catalog_alive=True)
    calls = []

    def boom(*_a, **_k):
        calls.append("chat")
        raise AssertionError("resume must not re-hit chat/completions on a 403 pin")

    catalog = ProviderHealth(name="nvidia", catalog_alive=True, catalog_status=200, tier="free")
    with mock.patch.dict(__import__("os").environ, {"NVIDIA_NIM_API_KEY": "nvapi-xxxx"}):
        with mock.patch.object(P, "chat", side_effect=boom):
            with mock.patch.object(P, "probe_local", return_value=(False, [])):
                with mock.patch("rad.health.probe_catalog", return_value=catalog):
                    gate = evaluate_live_gate(home)
    assert isinstance(gate, LiveGate)
    assert gate.allow is False
    assert calls == []
    assert "nvidia" in gate.catalog_only or gate.last


def test_g42_free_lock_scan_never_includes_paid(home):
    home.update(free_lock=True)

    def fake_health(spec, key, **kw):
        assert spec.tier != "paid"
        return ProviderHealth(name=spec.name, catalog_alive=True, catalog_status=200,
                              inference_entitled=True, inference_status=200, tier=spec.tier)

    with mock.patch.dict(__import__("os").environ, {"GROQ_API_KEY": "gsk", "OPENAI_API_KEY": "sk"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch("rad.health.probe_provider_health", side_effect=fake_health):
                hs = scan_provider_health(home)
    names = [h.name for h in hs]
    assert "openai" not in names
    assert "groq" in names
