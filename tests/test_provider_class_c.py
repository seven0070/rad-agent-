"""v0.5.0 G4-1 — live multi-provider / free-provider Class C doctrine (RW-089).

Investigate-first (ROADMAP Cycle 24 findings):
- `router.py` already free-first rotates and skips 401/403 inside one chat().
- Live RW runs pin one brain. RW-084 HTTP 403 and RW-086 HTTP 429 were
  re-read as product work: recovery classified them MODEL/TRANSIENT and
  retried (RW-084: 3 MODEL_FAILURE attempts then replan; RW-086: mid-run
  429 burned leftover tools).
- free_lock already drops paid from the chain.

G4-1 strengthens that path: 403/429/inference-forbidden are Class C
(needs_user / pause) with rotate-key / wait-quota / switch-free text.
Free-first rotation among usable providers; no silent paid under
free_lock; no Class A repair/replan invented for 403/429.

Does not claim live text_analyzer@12 now PASS. Needle OFF. Caps unchanged.
False DONE 0. Gen3 E1–E3 / path-align / multifile / ASCII-tree / thrash
Class A family preserved. Scripted 403/429 is enough — no live NIM/OpenRouter
success required.
"""
from __future__ import annotations

from unittest import mock

import pytest

import rad.providers as P
from rad import __version__
from rad.control import ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.codingloop import (
    infer_package_dir,
    is_done_protocol_tool,
    is_mkdir_already_exists,
    is_missing_optional_checksum_utility,
    is_missing_python_script,
    is_pip_requirements_file_missing,
)
from rad.control.events import EventLog
from rad.control.objectives import Budget, Objective
from rad.control.planner import Planner
from rad.control.recovery import FailureClass, RecoveryEngine, classify
from rad.control.tasks import Task
from rad.doctor import Doctor
from rad.home import DEFAULTS
from rad.router import RouterState
from rad.toolrouter import resolve_tool_router
from tests.test_ascii_tree_package_dir import RW073_ASCII_GOAL
from tests.test_control_plane import ScriptedSession, _ctl
from tests.test_mkdir_already_exists_actions import MKDIR_ERR
from tests.test_premature_test_env import PREMATURE_TEST_CMD, PREMATURE_TEST_ERR
from tests.test_xxd_environment import XXD_CMD, XXD_ERR

RW089_PLAN = {
    "tasks": [
        {
            "id": "t1",
            "text": "Write hello.txt",
            "depends_on": [],
            "checks": [{"kind": "file_exists", "args": {"path": "hello.txt"}}],
        },
    ],
    "objective_checks": [
        {"kind": "file_exists", "args": {"path": "hello.txt"}},
    ],
}


# ---------------------------------------------------------------- architecture freeze

def test_g41_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "0.5.4"
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


# ---------------------------------------------------------------- classify / decide

def test_class_c_kind_helpers():
    assert P.class_c_kind(403, "Authorization failed") == "auth"
    assert P.class_c_kind(None, "nvidia: HTTP 403 Authorization failed") == "auth"
    assert P.class_c_kind(429, "free-models-per-day") == "rate_limit"
    assert P.class_c_kind(None, "openrouter: HTTP 429 rate limited") == "rate_limit"
    assert P.class_c_kind(503, "all providers failed: groq: HTTP 503") is None
    assert "Class C" in P.class_c_next_steps("auth")
    assert "quota" in P.class_c_next_steps("rate_limit").lower()
    assert "paid spend stays off" in P.class_c_next_steps("rate_limit", free_lock=True)


def test_http_403_is_auth_class_c_not_model():
    t = Task.new("o", "x")
    err = "all providers failed: nvidia: HTTP 403 Authorization failed"
    assert classify(t, [], error=err) == FailureClass.AUTH
    assert classify(t, [], error=err) != FailureClass.MODEL
    d = RecoveryEngine().decide(t, [], error=err)
    assert d.strategy == "ask_user"
    assert d.failure_class == FailureClass.AUTH
    assert d.data.get("class_c") is True
    assert "Class C" in d.reason
    assert "Rotate the key" in d.reason or "rad use" in d.reason


def test_http_429_is_rate_class_c_not_transient():
    t = Task.new("o", "x")
    err = "all providers failed: openrouter: HTTP 429 free-models-per-day"
    assert classify(t, [], error=err) == FailureClass.RATE
    assert classify(t, [], error=err) != FailureClass.TRANSIENT
    assert classify(t, [], error=err) != FailureClass.MODEL
    d = RecoveryEngine().decide(t, [], error=err, retries_left=6)
    assert d.strategy == "ask_user"
    assert d.failure_class == FailureClass.RATE
    assert d.data.get("class_c") is True
    assert "Class C" in d.reason
    assert "quota" in d.reason.lower() or "rad use" in d.reason


def test_bare_all_providers_failed_still_model():
    t = Task.new("o", "x")
    assert classify(t, [], error="all providers failed") == FailureClass.MODEL


# ---------------------------------------------------------------- scripted drive (RW-089)

def test_rw089_403_pauses_needs_user_no_class_a(home, tmp_path):
    ws_dir = tmp_path / "ws_rw089_403"
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
    g = ctl.load_graph(obj)
    tasks = list(g.tasks.values())
    assert not any((t.text or "").startswith("Repair") for t in tasks)
    t1 = next(t for t in tasks if t.id == "t1" or "hello" in (t.text or "").lower())
    assert t1.status == TaskStatus.NEEDS_USER
    assert t1.failure_class == FailureClass.AUTH
    assert t1.attempts == 1
    decs = [e.data for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.RECOVERY_DECISION)]
    assert decs
    assert decs[0]["strategy"] == "ask_user"
    assert decs[0]["failure_class"] == FailureClass.AUTH
    assert "Class C" in decs[0]["reason"]
    assert not (ws_dir / "hello.txt").exists()
    assert ScriptedSession.script == leftover  # second step never consumed


def test_rw089_429_pauses_needs_user_no_retry_burn(home, tmp_path):
    ws_dir = tmp_path / "ws_rw089_429"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        P.ProviderError("openrouter: HTTP 429 free-models-per-day", status=429, retryable=True),
        ([("write_file", {"path": "hello.txt", "content": "x"})], "DONE"),
    ]
    ScriptedSession.prompts = []
    leftover = list(ScriptedSession.script[1:])
    ctl = _ctl(home, ScriptedSession, RW089_PLAN)
    obj = ctl.run(ctl.create("write hello.txt", auto=True))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    g = ctl.load_graph(obj)
    t1 = next(t for t in g.tasks.values() if t.id == "t1" or "hello" in (t.text or "").lower())
    assert t1.status == TaskStatus.NEEDS_USER
    assert t1.failure_class == FailureClass.RATE
    assert t1.attempts == 1
    decs = [e.data for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.RECOVERY_DECISION)]
    assert decs[0]["strategy"] == "ask_user"
    assert decs[0]["failure_class"] == FailureClass.RATE
    assert not any((t.text or "").startswith("Repair") for t in g.tasks.values())
    assert ScriptedSession.script == leftover


def test_http_503_still_retries_as_model(home, tmp_path):
    ws_dir = tmp_path / "ws_rw089_503"
    ws_dir.mkdir()
    home.update(workspace=str(ws_dir), objective_parallel=1)
    ScriptedSession.script = [
        P.ProviderError("all providers failed: groq: HTTP 503", status=503, retryable=True),
        ([("write_file", {"path": "hello.txt", "content": "1"})], "DONE"),
    ]
    ScriptedSession.prompts = []
    ctl = _ctl(home, ScriptedSession, RW089_PLAN)
    obj = ctl.run(ctl.create("write hello.txt", auto=True))
    assert obj.status == ObjectiveStatus.COMPLETED
    dec = [e.data for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.RECOVERY_DECISION)][0]
    assert dec["failure_class"] == FailureClass.MODEL and dec["strategy"] == "retry"


# ---------------------------------------------------------------- router rotation / free_lock

def test_router_rotates_free_on_429_and_clears_preferred(home):
    calls = []

    def fake_chat(spec, key, messages, **kw):
        calls.append(spec.name)
        if spec.name == "groq":
            raise P.ProviderError("groq: HTTP 429 rate limited", status=429, retryable=True)
        return P.ChatResult(text=f"hi from {spec.name}", provider=spec.name, model="m",
                            usage={"in": 1, "out": 1})

    with mock.patch.dict(__import__("os").environ, {"GROQ_API_KEY": "gsk", "CEREBRAS_API_KEY": "csk"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch.object(P, "chat", side_effect=fake_chat):
                r = RouterState(home)
                r.preferred["free"] = "groq"
                res = r.chat([{"role": "user", "content": "hi"}], stream_cb=None)
                assert res.provider == "cerebras"
                assert "groq" in calls and "cerebras" in calls
                assert r.failures["groq"].get("class_c") is True
                assert r.preferred.get("free") == "cerebras"
                names = [e.spec.name for e in r.build_chain()]
                assert "groq" not in names
                assert "cerebras" in names


def test_router_free_lock_never_calls_paid_on_free_class_c(home):
    calls = []

    def fake_chat(spec, key, messages, **kw):
        calls.append(spec.name)
        if spec.tier == "paid":
            raise AssertionError("paid must not be used under free_lock")
        raise P.ProviderError(f"{spec.name}: HTTP 429 free-models-per-day", status=429, retryable=True)

    with mock.patch.dict(__import__("os").environ, {"GROQ_API_KEY": "gsk", "OPENAI_API_KEY": "sk"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch.object(P, "chat", side_effect=fake_chat):
                r = RouterState(home)
                home.update(free_lock=True)
                with pytest.raises(P.ProviderError) as ei:
                    r.chat([{"role": "user", "content": "hi"}], stream_cb=None)
                assert "openai" not in calls
                assert "Class C" in str(ei.value)
                assert "paid spend stays off" in str(ei.value)
                assert ei.value.status == 429
                assert ei.value.retryable is False


def test_force_provider_class_c_still_rotates_to_other_free(home):
    calls = []

    def fake_chat(spec, key, messages, **kw):
        calls.append(spec.name)
        if spec.name == "groq":
            raise P.ProviderError("groq: HTTP 403 Authorization failed", status=403, retryable=False)
        return P.ChatResult(text="ok", provider=spec.name, model="m", usage={"in": 1, "out": 1})

    with mock.patch.dict(__import__("os").environ, {"GROQ_API_KEY": "gsk", "CEREBRAS_API_KEY": "csk"}):
        with mock.patch.object(P, "probe_local", return_value=(False, [])):
            with mock.patch.object(P, "chat", side_effect=fake_chat):
                home.update(force_provider="groq")
                r = RouterState(home)
                res = r.chat([{"role": "user", "content": "hi"}], stream_cb=None)
                assert calls[0] == "groq"
                assert res.provider == "cerebras"


def test_doctor_providers_surface_class_c_doctrine(home):
    from rad.health import ProviderHealth
    fake = [ProviderHealth(name="groq", catalog_alive=True, catalog_status=200,
                           inference_entitled=True, inference_status=200, tier="free")]
    with mock.patch("rad.doctor.scan_provider_health", return_value=fake):
        home.update(free_lock=True)
        fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    assert fs["providers"].status == "ok"
    blob = fs["providers"].message + " " + " ".join(fs["providers"].detail)
    assert "inference-entitled" in blob
    assert "Class C" in blob or "403/429" in blob
    assert "free_lock" in blob
