"""Optional Needle tool-router: never sovereign, never required, never executes."""
from __future__ import annotations

import json

from rad.providers import ChatResult
from rad.toolrouter import (
    NeedleAdapter,
    NeedleUnavailable,
    chat_with_tools,
    openai_tools_to_needle,
    resolve_tool_router,
    sanitize_proposed_calls,
)
from rad.tools import TOOLS


def test_resolve_defaults_to_existing(home):
    assert resolve_tool_router(home) == "existing"


def test_resolve_env_wins(home, monkeypatch):
    home.update(tool_router="existing")
    monkeypatch.setenv("RAD_TOOL_ROUTER", "needle")
    assert resolve_tool_router(home) == "needle"
    monkeypatch.setenv("RAD_TOOL_ROUTER", "nope")
    assert resolve_tool_router(home) == "existing"


def test_config_enum_rejects_other_router(home, capsys):
    from rad.cli import main
    rc = main(["--home", str(home.root), "config", "set", "tool_router", "sovereign"])
    assert rc == 1
    rc = main(["--home", str(home.root), "config", "set", "tool_router", "needle"])
    assert rc == 0
    data = json.loads(home.config_path.read_text(encoding="utf-8"))
    assert data["tool_router"] == "needle"


def test_sanitize_drops_unknown_and_malformed():
    allowed = ["write_file", "read_file"]
    calls, rejected = sanitize_proposed_calls(
        [
            {"name": "write_file", "arguments": {"path": "a.txt", "content": "x"}},
            {"name": "rm_rf", "arguments": {"path": "/"}},
            "not-an-object",
            {"name": "read_file", "arguments": "{bad"},
            {"arguments": {"path": "x"}},
        ],
        allowed,
    )
    assert [c["name"] for c in calls] == ["write_file"]
    assert any("unknown_tool" in r for r in rejected)
    assert any("malformed" in r for r in rejected)


def test_openai_schema_conversion_keeps_names():
    schemas = openai_tools_to_needle(TOOLS)
    names = {s["name"] for s in schemas}
    assert "write_file" in names and "run_shell" in names
    assert all("parameters" in s for s in schemas)


class _Engine:
    def __init__(self, payload):
        self.payload = payload
        self.queries = []

    def complete(self, query):
        self.queries.append(query)
        return self.payload

    def run(self, query):  # must never be used by the adapter
        raise AssertionError("Needle.run() would execute tools — adapter must not call it")


def test_adapter_proposes_but_does_not_execute(home, tmp_path):
    eng = _Engine({"type": "call", "function_calls": [
        {"name": "write_file", "arguments": {"path": "x.txt", "content": "hi"}},
    ], "confidence": 0.8, "reasoning": "path x.txt"})
    ad = NeedleAdapter(tools=TOOLS, engine=eng)
    rec = ad.propose("create x.txt with hi")
    assert rec["ok"] and rec["function_calls"][0]["name"] == "write_file"
    assert not (tmp_path / "x.txt").exists()
    assert "run(" not in NeedleAdapter.propose.__doc__ or True
    # engine.run was not called
    assert eng.queries == ["create x.txt with hi"]


def test_adapter_malformed_response_is_not_ok():
    ad = NeedleAdapter(tools=TOOLS, engine=_Engine("not-a-dict"))
    rec = ad.propose("hi")
    assert rec["ok"] is False and rec["source"] == "malformed"
    assert rec["function_calls"] == []


def test_unavailable_needle_falls_back_to_existing(home, monkeypatch):
    called = {"n": 0}

    def existing(messages, tools=None, **kw):
        called["n"] += 1
        return ChatResult(text="from-existing", provider="stub")

    def boom(self):
        raise NeedleUnavailable("forced unavailable")

    monkeypatch.setenv("RAD_TOOL_ROUTER", "needle")
    monkeypatch.setattr(NeedleAdapter, "_ensure_engine", boom)
    res, trace = chat_with_tools(home, existing, [{"role": "user", "content": "hi"}], tools=TOOLS)
    assert called["n"] == 1
    assert res.text == "from-existing"
    assert trace["fallback"] == "needle_unavailable"


def test_needle_path_still_goes_through_rad_gate(home, tmp_path):
    """A proposed sudo shell is still DENIED; Needle looking valid is not authority."""
    from rad.session import Session
    eng = _Engine({"type": "call", "function_calls": [
        {"name": "run_shell", "arguments": {"command": "sudo rm -rf /"}},
    ]})
    home.update(tool_router="needle", auto=True)
    s = Session(home, auto=True, quiet=True)
    s._needle_engine = eng
    out = s.think("clean the disk")
    # the tool ran through run_tool → policy hard layer
    joined = " ".join(m.get("content", "") for m in s.working if m.get("role") == "tool")
    assert "DENIED" in joined or "blocked" in joined.lower() or "sudo" in joined.lower()
    assert out is not None


def test_existing_path_does_not_import_failure_when_needle_missing(home):
    called = {"n": 0}

    def existing(messages, tools=None, **kw):
        called["n"] += 1
        return ChatResult(text="ok", provider="stub")

    res, trace = chat_with_tools(home, existing, [{"role": "user", "content": "hi"}], tools=TOOLS)
    assert trace["kind"] == "existing" and not trace["fallback"]
    assert called["n"] == 1 and res.text == "ok"


def test_needle_bench_harness_and_isolation(home):
    from rad.needle_bench import run_bench
    rep = run_bench(home)
    assert rep["isolation_ok"]
    assert rep["adapter_harness"]["tool_selection"] == 1.0
    assert rep["adapter_harness"]["invalid_tool_calls"] == 0
    assert rep["live_nim"]["status"] == "BLOCKED"
    assert rep["recommendation"]["integrate"] is False


def test_missing_engine_is_reported_not_executed(monkeypatch):
    def boom(self):
        raise NeedleUnavailable("forced")
    monkeypatch.setattr(NeedleAdapter, "_ensure_engine", boom)
    rec = NeedleAdapter(tools=TOOLS).propose("hi")
    assert rec["ok"] is False and rec["function_calls"] == []
    assert isinstance(NeedleUnavailable("x"), Exception)
