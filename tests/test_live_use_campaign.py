"""v0.5.2 G4-3 — live-use campaign / operator workflow (RW-092 / RW-093).

Investigate-first (ROADMAP G4-3 entry):
- G4-1 closed pause (RW-089). G4-2 closed safe resume / health (RW-090 / RW-091).
- Last working-inference live row is RW-086 on v0.4.7. E1–E3 and G4-1/G4-2
  were never live-confirmed together.
- Leftover vs G4-2: online rad doctor called scan_provider_health without
  skip_blocked_inference, re-pinging chat while last Class C still blocks
  (counts against OpenRouter free-models-per-day). Resume already skipped
  (RW-091). Controller re-record could drop key_fp / Retry-After.

G4-3: doctor / health skip chat while last Class C blocks (unknown key_fp
included); rad health is the pause/resume/campaign surface; playbook documents
how to run a live campaign when NIM / OpenRouter free recovers. No Class A
for 403/429. No silent paid under free_lock. Caps 16/60. Needle OFF. No live
PASS claim required to ship.
"""
from __future__ import annotations

import json
import time
from unittest import mock

from rad import __version__
from rad import providers as P
from rad.cli import main
from rad.control import ObjectiveStatus
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
from rad.doctor import Doctor
from rad.health import (
    CAMPAIGN_PLAYBOOK,
    ProviderHealth,
    campaign_next_action,
    class_c_still_blocks,
    last_class_c,
    load_health_state,
    operator_status,
    probe_provider_health,
    record_class_c,
    save_health_state,
    scan_provider_health,
)
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_provider_class_c import RW089_PLAN
from tests.test_xxd_environment import XXD_CMD, XXD_ERR

OR_SPEC = P.ProviderSpec(
    "openrouter", "openai", "https://openrouter.ai/api/v1",
    ("OPENROUTER_API_KEY",), default_model="nvidia/nemotron-3.5-lightning:free",
    tier="free")
NV_SPEC = P.ProviderSpec(
    "nvidia", "openai", "https://integrate.api.nvidia.com/v1",
    ("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"),
    default_model="meta/llama-3.2-11b-vision-instruct", tier="free")


# ---------------------------------------------------------------- architecture freeze

def test_g43_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
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


# ---------------------------------------------------------------- RW-092 doctor / preflight skip-blocked (RW-086 quota shape)

def test_rw092_doctor_skips_chat_when_last_class_c_blocks_unknown_key_fp(home):
    """Controller-style persist (no key_fp) must still skip the chat re-burn."""
    record_class_c(
        home, "openrouter", kind="rate_limit", status=429,
        err="openrouter: HTTP 429 free-models-per-day", retry_after=120,
        catalog_alive=True,
    )
    last = last_class_c(home)
    assert last["key_fp"] == "none"
    assert class_c_still_blocks(last)
    calls = []

    def boom(*_a, **_k):
        calls.append("chat")
        raise AssertionError("doctor must not re-hit chat/completions while last Class C blocks")

    catalog = ProviderHealth(name="openrouter", catalog_alive=True, catalog_status=200, tier="free")
    with mock.patch.dict(__import__("os").environ, {"OPENROUTER_API_KEY": "sk-or-xxxx"}):
        with mock.patch.object(P, "chat", side_effect=boom):
            with mock.patch.object(P, "probe_local", return_value=(False, [])):
                with mock.patch("rad.health.all_specs", return_value=[OR_SPEC]):
                    with mock.patch("rad.health.probe_catalog", return_value=catalog):
                        fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    assert calls == []
    blob = fs["providers"].message + " " + " ".join(fs["providers"].detail)
    assert fs["providers"].status == "warn"
    assert "skipped" in blob.lower() or "chat ping skipped" in blob
    assert "429" in blob or "rate_limit" in blob or "Class C" in blob


def test_rw092_doctor_force_reprobes_chat(home):
    record_class_c(
        home, "openrouter", kind="rate_limit", status=429,
        err="openrouter: HTTP 429 free-models-per-day", retry_after=120,
        catalog_alive=True,
    )
    calls = []

    def fake_chat(*_a, **_k):
        calls.append("chat")
        raise P.ProviderError("openrouter: HTTP 429 free-models-per-day", status=429, retryable=True)

    catalog = ProviderHealth(name="openrouter", catalog_alive=True, catalog_status=200, tier="free")
    with mock.patch.dict(__import__("os").environ, {"OPENROUTER_API_KEY": "sk-or-xxxx"}):
        with mock.patch.object(P, "chat", side_effect=fake_chat):
            with mock.patch.object(P, "probe_local", return_value=(False, [])):
                with mock.patch("rad.health.all_specs", return_value=[OR_SPEC]):
                    with mock.patch("rad.health.probe_catalog", return_value=catalog):
                        Doctor(home, fix=False, probe_network=True, force=True).run()
    assert calls == ["chat"]


def test_rw092_retry_after_expired_allows_chat_ping(home):
    rec = record_class_c(
        home, "openrouter", kind="rate_limit", status=429,
        err="openrouter: HTTP 429 free-models-per-day", retry_after=30,
        catalog_alive=True, key="sk-or-xxxx",
    )
    data = load_health_state(home)
    data["providers"]["openrouter"]["retry_after_until"] = time.time() - 1
    data["last"] = dict(data["providers"]["openrouter"])
    save_health_state(home, data)
    assert not class_c_still_blocks(data["providers"]["openrouter"])
    calls = []

    def fake_chat(*_a, **_k):
        calls.append("chat")
        return P.ChatResult(text="ok", provider="openrouter", model="m", usage={"in": 1, "out": 1})

    catalog = ProviderHealth(name="openrouter", catalog_alive=True, catalog_status=200, tier="free")
    spec = P.ProviderSpec("openrouter", "openai", "https://example.test/v1",
                          default_model="nvidia/nemotron-3.5-lightning:free", tier="free")
    with mock.patch.object(P, "chat", side_effect=fake_chat):
        with mock.patch("rad.health.probe_catalog", return_value=catalog):
            h = probe_provider_health(spec, "sk-or-xxxx", home=home, skip_blocked_inference=True)
    assert calls == ["chat"]
    assert h.inference_entitled is True
    assert rec["status"] == 429


def test_rw092_scan_default_skips_blocked(home):
    record_class_c(
        home, "nvidia", kind="auth", status=403,
        err="nvidia: HTTP 403 Authorization failed", catalog_alive=True,
    )
    calls = []

    def boom(*_a, **_k):
        calls.append("chat")
        raise AssertionError("scan default must skip blocked inference")

    catalog = ProviderHealth(name="nvidia", catalog_alive=True, catalog_status=200, tier="free")
    with mock.patch.dict(__import__("os").environ, {"NVIDIA_NIM_API_KEY": "nvapi-xxxx"}):
        with mock.patch.object(P, "chat", side_effect=boom):
            with mock.patch.object(P, "probe_local", return_value=(False, [])):
                with mock.patch("rad.health.all_specs", return_value=[NV_SPEC]):
                    with mock.patch("rad.health.probe_catalog", return_value=catalog):
                        hs = scan_provider_health(home)
    assert calls == []
    assert any(h.skipped_inference for h in hs)


# ---------------------------------------------------------------- RW-093 campaign / operator workflow

def test_rw093_operator_status_wait_on_429_without_chat(home):
    record_class_c(
        home, "openrouter", kind="rate_limit", status=429,
        err="openrouter: HTTP 429 free-models-per-day", retry_after=90,
        catalog_alive=True,
    )
    calls = []

    def boom(*_a, **_k):
        calls.append("chat")
        raise AssertionError("rad health must not re-burn chat")

    catalog = ProviderHealth(name="openrouter", catalog_alive=True, catalog_status=200, tier="free")
    with mock.patch.dict(__import__("os").environ, {"OPENROUTER_API_KEY": "sk-or-xxxx"}):
        with mock.patch.object(P, "chat", side_effect=boom):
            with mock.patch.object(P, "probe_local", return_value=(False, [])):
                with mock.patch("rad.health.all_specs", return_value=[OR_SPEC]):
                    with mock.patch("rad.health.probe_catalog", return_value=catalog):
                        st = operator_status(home)
    assert calls == []
    assert st.next_action == "wait"
    assert st.allow is False
    assert st.retry_after and st.retry_after > 0
    blob = " ".join(st.playbook)
    assert "rad health" in blob
    assert "E1" in blob and "E3" in blob
    assert "live PASS is not required" in blob.lower() or "not required" in blob
    assert CAMPAIGN_PLAYBOOK[0].startswith("1. rad health")


def test_rw093_next_action_table():
    assert campaign_next_action(
        entitled=["groq"], last=None, catalog_only=[], has_class_c_objective=True) == "resume"
    assert campaign_next_action(
        entitled=["groq"], last=None, catalog_only=[], has_class_c_objective=False) == "run"
    assert campaign_next_action(
        entitled=[], last={"class_c": True, "kind": "rate_limit", "retry_after_until": time.time() + 60},
        catalog_only=["openrouter"], has_class_c_objective=True) == "wait"
    assert campaign_next_action(
        entitled=[], last={"class_c": True, "kind": "auth"},
        catalog_only=["nvidia"], has_class_c_objective=False) == "rotate"


def test_rw093_pause_then_health_resume_when_entitled(home, tmp_path):
    ws_dir = tmp_path / "ws_rw093"
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
    last = last_class_c(home)
    assert last is not None
    assert last["kind"] == "auth"
    assert last.get("objective_id") == obj.id

    entitled = [ProviderHealth(name="groq", catalog_alive=True, catalog_status=200,
                               inference_entitled=True, inference_status=200, tier="free")]
    with mock.patch("rad.health.scan_provider_health", return_value=entitled):
        st = operator_status(home)
    assert st.next_action == "resume"
    assert st.allow is True
    assert obj.id in st.paused_objectives
    assert "resume" in (st.next_steps or "")


def test_rw093_cli_health_json_no_chat(home, capsys):
    record_class_c(
        home, "openrouter", kind="rate_limit", status=429,
        err="openrouter: HTTP 429 free-models-per-day", retry_after=60,
        catalog_alive=True,
    )
    calls = []

    def boom(*_a, **_k):
        calls.append("chat")
        raise AssertionError("CLI rad health must skip chat")

    catalog = ProviderHealth(name="openrouter", catalog_alive=True, catalog_status=200, tier="free")
    with mock.patch.dict(__import__("os").environ, {"OPENROUTER_API_KEY": "sk-or-xxxx"}):
        with mock.patch.object(P, "chat", side_effect=boom):
            with mock.patch.object(P, "probe_local", return_value=(False, [])):
                with mock.patch("rad.health.all_specs", return_value=[OR_SPEC]):
                    with mock.patch("rad.health.probe_catalog", return_value=catalog):
                        rc = main(["--home", str(home.root), "health", "--json", "--campaign"])
    out = capsys.readouterr().out
    assert calls == []
    assert rc == 2
    data = json.loads(out)
    assert data["next_action"] == "wait"
    assert data["last"]["status"] == 429
    assert any("bounded objective" in line for line in data["playbook"])


def test_g43_free_lock_health_never_includes_paid(home):
    home.update(free_lock=True)

    def fake_health(spec, key, **kw):
        assert spec.tier != "paid"
        return ProviderHealth(name=spec.name, catalog_alive=True, catalog_status=200,
                              inference_entitled=True, inference_status=200, tier=spec.tier)

    with mock.patch.dict(__import__("os").environ, {"GROQ_API_KEY": "gsk", "OPENAI_API_KEY": "sk"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch("rad.health.probe_provider_health", side_effect=fake_health):
                st = operator_status(home)
    assert "openai" not in st.entitled
    assert "groq" in st.entitled
    assert st.next_action == "run"
