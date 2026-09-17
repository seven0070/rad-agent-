"""Regression tests for defects found in the 2026-09 code audit.

These exercise the layers the original suite mocked *around*:
  - the real provider response parsers (via a fake `_http`)
  - router kwarg pass-through
  - build_caller pinning across multiple calls
  - the workspace boundary of the file tools
"""
import json
from unittest import mock

import pytest

import rad.providers as P
import rad.router as R
from rad.battery import build_caller
from rad.router import RouterState
from rad.tools import ToolCtx, run_tool


# ---------------------------------------------------------------- 1. non-streaming parsers

def _openai_body(text="hello", tool_calls=None):
    msg = {"content": text}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return json.dumps({"choices": [{"message": msg}],
                       "usage": {"prompt_tokens": 3, "completion_tokens": 2}}).encode()


def test_openai_non_streaming_parses_bytes():
    spec = P.ProviderSpec("t", "openai", "http://x/v1", default_model="m")
    with mock.patch.object(P, "_http", return_value=(200, {}, _openai_body())):
        res = P.chat(spec, "k", [{"role": "user", "content": "hi"}], stream_cb=None)
    assert res.text == "hello"
    assert res.usage == {"in": 3, "out": 2}


def test_openai_non_streaming_tool_calls():
    tc = [{"id": "c1", "function": {"name": "read_file", "arguments": json.dumps({"path": "a.txt"})}}]
    spec = P.ProviderSpec("t", "openai", "http://x/v1", default_model="m")
    with mock.patch.object(P, "_http", return_value=(200, {}, _openai_body("", tc))):
        res = P.chat(spec, "k", [{"role": "user", "content": "hi"}], stream_cb=None)
    assert res.tool_calls == [{"id": "c1", "name": "read_file", "arguments": {"path": "a.txt"}}]


def test_anthropic_non_streaming_parses_bytes():
    body = json.dumps({"content": [{"type": "text", "text": "hey"},
                                   {"type": "tool_use", "id": "t1", "name": "run_shell", "input": {"command": "ls"}}],
                       "usage": {"input_tokens": 5, "output_tokens": 1}}).encode()
    spec = P.ProviderSpec("a", "anthropic", "http://x", default_model="m")
    with mock.patch.object(P, "_http", return_value=(200, {}, body)):
        res = P.chat(spec, "k", [{"role": "user", "content": "hi"}], stream_cb=None)
    assert res.text == "hey"
    assert res.tool_calls[0]["name"] == "run_shell"
    assert res.usage == {"in": 5, "out": 1}


def test_gemini_non_streaming_parses_bytes():
    body = json.dumps({"candidates": [{"content": {"parts": [
        {"text": "yo"}, {"functionCall": {"name": "web_search", "args": {"query": "x"}}}]}}],
        "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 2}}).encode()
    spec = P.ProviderSpec("g", "gemini", "http://x", default_model="m")
    with mock.patch.object(P, "_http", return_value=(200, {}, body)):
        res = P.chat(spec, "k", [{"role": "user", "content": "hi"}], stream_cb=None)
    assert res.text == "yo"
    assert res.tool_calls[0]["arguments"] == {"query": "x"}


def test_non_streaming_error_status_raises_provider_error():
    spec = P.ProviderSpec("t", "openai", "http://x/v1", default_model="m")
    with mock.patch.object(P, "_http", return_value=(429, {}, b'{"error":{"message":"slow down"}}')):
        with pytest.raises(P.ProviderError) as ei:
            P.chat(spec, "k", [{"role": "user", "content": "hi"}], stream_cb=None)
    assert ei.value.status == 429 and ei.value.retryable


def test_router_non_streaming_end_to_end(home):
    """The router path used by battery/team/sleep/plan must work without streaming."""
    with mock.patch.dict("os.environ", {"GROQ_API_KEY": "k"}), \
         mock.patch.object(P, "probe_local", return_value=(False, [])), \
         mock.patch.object(P, "_http", return_value=(200, {}, _openai_body("via router"))):
        res = RouterState(home).chat([{"role": "user", "content": "hi"}], stream_cb=None)
    assert res.text == "via router" and res.provider == "groq"


# ---------------------------------------------------------------- 2. max_tokens pass-through

def test_router_chat_accepts_max_tokens(home):
    seen = {}

    def fake_chat(spec, key, messages, **kw):
        seen.update(kw)
        return P.ChatResult(text="ok", provider=spec.name, model="m")

    with mock.patch.dict("os.environ", {"GROQ_API_KEY": "k"}), \
         mock.patch.object(P, "probe_local", return_value=(False, [])), \
         mock.patch.object(P, "chat", side_effect=fake_chat):
        RouterState(home).chat([{"role": "user", "content": "hi"}], stream_cb=None, max_tokens=2000)
    assert seen["max_tokens"] == 2000


# ---------------------------------------------------------------- 3. build_caller stays pinned

def test_build_caller_pins_provider_for_every_call(home):
    seen = []

    def fake_chat(self, msgs, **kw):
        seen.append((self.home.cfg.get("force_provider"), self.home.cfg.get("model")))
        return P.ChatResult(text="x")

    with mock.patch.object(R.RouterState, "chat", fake_chat):
        c = build_caller(home, provider="cerebras", model="mm")
        for i in range(3):
            c("sys", f"q{i}")
    assert seen == [("cerebras", "mm")] * 3
    # and config is restored afterwards
    assert home.cfg.get("force_provider") is None and home.cfg.get("model") is None


def test_build_caller_two_brains_do_not_leak(home):
    seen = []

    def fake_chat(self, msgs, **kw):
        seen.append(self.home.cfg.get("force_provider"))
        return P.ChatResult(text="x")

    with mock.patch.object(R.RouterState, "chat", fake_chat):
        a = build_caller(home, provider="groq")
        b = build_caller(home, provider="cerebras")
        a("s", "1"); b("s", "2"); a("s", "3")
    assert seen == ["groq", "cerebras", "groq"]


# ---------------------------------------------------------------- 4. workspace boundary

@pytest.fixture
def ws_ctx(home, tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "inside.txt").write_text("in")
    (tmp_path / "outside.txt").write_text("out")
    home.update(workspace=str(ws))
    return ToolCtx(home=home, router=None, auto=True, confirm=lambda p: True), ws, tmp_path


def test_read_inside_workspace_ok(ws_ctx):
    ctx, ws, _ = ws_ctx
    assert run_tool("read_file", {"path": "inside.txt"}, ctx) == "in"
    assert run_tool("read_file", {"path": str(ws / "inside.txt")}, ctx) == "in"


def test_read_outside_workspace_blocked(ws_ctx):
    ctx, ws, root = ws_ctx
    for ref in ("../outside.txt", str(root / "outside.txt"), "/etc/hostname", "~/.ssh/id_rsa"):
        out = run_tool("read_file", {"path": ref}, ctx)
        assert out.startswith("BLOCKED by safety policy"), (ref, out)


def test_write_and_list_outside_workspace_blocked(ws_ctx):
    ctx, ws, root = ws_ctx
    out = run_tool("write_file", {"path": "../pwned.txt", "content": "x"}, ctx)
    assert out.startswith("BLOCKED") and not (root / "pwned.txt").exists()
    assert run_tool("list_dir", {"path": ".."}, ctx).startswith("BLOCKED")


def test_outside_workspace_opt_in(ws_ctx):
    ctx, ws, root = ws_ctx
    ctx.home.cfg["allow_outside_workspace"] = True
    assert run_tool("read_file", {"path": str(root / "outside.txt")}, ctx) == "out"
