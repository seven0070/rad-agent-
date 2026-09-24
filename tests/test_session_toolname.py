"""Harmony/gpt-oss models leak <|channel|>-style control tokens into tool names.

Observed live on NIM openai/gpt-oss-20b: "read_file<|channel|>commentary" was
dispatched as an unknown tool, the resulting error hard-failed the attempt, and
each leak burned a retry. The session must strip the tokens before dispatch.
"""
from __future__ import annotations

from rad.providers import ChatResult
from rad.session import Session, clean_tool_name


def test_clean_tool_name_strips_harmony_channel_tokens():
    assert clean_tool_name("read_file<|channel|>commentary") == "read_file"
    assert clean_tool_name("run_python<|channel|>commentary") == "run_python"
    assert clean_tool_name(
        "read_file<|channel|>commentary<|channel|>commentary") == "read_file"
    assert clean_tool_name("list_dir") == "list_dir"
    assert clean_tool_name("write_file<|endoftext|>") == "write_file"
    assert clean_tool_name("") == ""
    assert clean_tool_name(None) == ""
    # A name that is *only* tokens has no real tool left — keep the original so
    # the unknown-tool path reports what the model actually asked for.
    assert clean_tool_name("<|channel|>commentary") == "<|channel|>commentary"


def test_polluted_tool_name_dispatches_as_real_tool(home, monkeypatch):
    calls = {"n": 0}

    def fake_chat(msgs, tools=None, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return ChatResult(
                text="",
                provider="stub",
                tool_calls=[{
                    "id": "c1",
                    "name": "list_dir<|channel|>commentary",
                    "arguments": {"path": "."},
                }],
            )
        return ChatResult(text="done", provider="stub")

    s = Session(home, auto=True, quiet=True)
    monkeypatch.setattr(s.router, "chat", fake_chat)
    s.think("list the directory")

    tool_msgs = [m for m in s.working if m.get("role") == "tool"]
    assert tool_msgs, "tool must have been dispatched"
    assert tool_msgs[0]["name"] == "list_dir"
    assert "unknown tool" not in tool_msgs[0]["content"].lower()
