"""Phase 0 triage: advisory auto/escalate classifier (offline, injectable llm)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rad.triage import TriageDecision, brain_for, triage  # noqa: E402


def _llm(payload: dict):
    return lambda p: json.dumps(payload)


def _llm_raw(text: str):
    return lambda p: text


# ---------------------------------------------------------------- module

def test_version():
    from rad import __version__
    assert __version__ == "1.0.1"


def test_fallback_when_no_brain():
    d = triage(None, "list files in the workspace")
    assert d.verdict == "escalate" and d.decided_by == "fallback"
    assert d.confidence == 0.0 and "no brain" in d.reason


def test_llm_auto_passes_confident():
    d = triage(_llm({"verdict": "auto", "reason": "read-only", "confidence": 0.9}),
               "list files in the workspace")
    assert d.verdict == "auto" and d.decided_by == "llm" and d.confidence == 0.9


def test_fenced_json_parses():
    raw = '```json\n{"verdict": "escalate", "reason": "needs user", "confidence": 0.8}\n```'
    d = triage(_llm_raw(raw), "rename a file")
    assert d.verdict == "escalate" and d.decided_by == "llm"


def test_prose_output_falls_back():
    d = triage(_llm_raw("I think this is safe to do."), "read a file")
    assert d.verdict == "escalate" and d.decided_by == "fallback"


def test_low_confidence_auto_escalates():
    d = triage(_llm({"verdict": "auto", "reason": "ok", "confidence": 0.3}),
               "list files")
    assert d.verdict == "escalate" and d.decided_by == "llm"
    assert d.signals.get("low_confidence") is True


def test_risk_signal_overrides_llm_auto():
    d = triage(_llm({"verdict": "auto", "reason": "sure", "confidence": 0.95}),
               "deploy to prod and delete everything")
    assert d.verdict == "escalate" and d.decided_by == "policy_override"
    assert d.signals.get("risk_hits")


def test_llm_exception_falls_back():
    def boom(p):
        raise RuntimeError("provider down")
    d = triage(boom, "do something")
    assert d.verdict == "escalate" and d.decided_by == "fallback"


def test_invalid_verdict_falls_back():
    d = triage(_llm({"verdict": "maybe", "reason": "?", "confidence": 0.9}), "x")
    assert d.verdict == "escalate" and d.decided_by == "fallback"


def test_empty_text_falls_back():
    d = triage(None, "")
    assert d.verdict == "escalate" and "no text" in d.reason


def test_to_dict_roundtrip():
    d = TriageDecision(verdict="auto", reason="ok", confidence=0.9, decided_by="llm")
    dd = d.to_dict()
    assert dd["verdict"] == "auto" and dd["decided_by"] == "llm"
    assert isinstance(dd["signals"], dict) and "decision_ms" in dd


def test_brain_for_offline_returns_none(home):
    # conftest strips keys; RouterState.build_chain() must be empty offline
    assert brain_for(home) is None


# ---------------------------------------------------------------- route

def _api(home):
    from rad.api import Api
    return Api(home)


def test_route_triage_200_fallback(home, monkeypatch):
    from rad.api import Api
    api = Api(home)
    st, d = api.handle("POST", "/v1/triage", {}, {"text": "list files"})
    assert st == 200 and d["verdict"] == "escalate" and d["decided_by"] == "fallback"


def test_route_triage_200_llm_path(home, monkeypatch):
    import rad.triage as T
    monkeypatch.setattr(T, "brain_for", lambda h: lambda p: json.dumps(
        {"verdict": "auto", "reason": "local read", "confidence": 0.95}))
    st, d = _api(home).handle("POST", "/v1/triage", {}, {"text": "list files", "kind": "task"})
    assert st == 200 and d["verdict"] == "auto" and d["decided_by"] == "llm"
    assert d["kind"] == "task"


def test_route_triage_400_empty(home):
    from rad.api import Api, ApiError
    api = Api(home)
    with pytest.raises(ApiError) as ei:
        api.handle("POST", "/v1/triage", {}, {"text": ""})
    assert ei.value.status == 400


def test_route_triage_400_too_long(home):
    from rad.api import Api, ApiError
    api = Api(home)
    with pytest.raises(ApiError) as ei:
        api.handle("POST", "/v1/triage", {}, {"text": "x" * 9000})
    assert ei.value.status == 400


def test_route_triage_not_mutating(home):
    """Read-only: creates no objectives, writes no events."""
    from rad.api import Api
    api = Api(home)
    api.handle("POST", "/v1/triage", {}, {"text": "do x"})
    st, d = api.handle("GET", "/v1/objectives", {}, {})
    assert d["objectives"] == []
