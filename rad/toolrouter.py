"""Optional experimental tool-router: existing LLM native tools vs Needle.

Needle NEVER executes tools and NEVER decides permission, sandbox, budget,
verification, or completion. It may only propose {name, arguments}. RAD's
Executor → Policy → Sandbox → Budget → run_tool path remains the only
side-effect path.

Default is `existing`. Needle is opt-in via RAD_TOOL_ROUTER=needle or
`rad config set tool_router needle`. Missing/broken Needle falls back to
existing and records why.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from rad.home import RadHome
from rad.providers import ChatResult

ROUTERS = ("existing", "needle")
ENV_VAR = "RAD_TOOL_ROUTER"


def resolve_tool_router(home: Optional[RadHome] = None) -> str:
    """Env wins over config. Unknown values fall back to existing (never crash)."""
    raw = (os.environ.get(ENV_VAR) or "").strip().lower()
    if not raw and home is not None:
        raw = str(home.cfg.get("tool_router") or "existing").strip().lower()
    if raw not in ROUTERS:
        return "existing"
    return raw


def openai_tools_to_needle(tools: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """OpenAI `{type:function,function:{name,parameters}}` → Needle JSON schema."""
    out: List[Dict[str, Any]] = []
    for t in tools or []:
        if not isinstance(t, dict):
            continue
        fn = t.get("function") if t.get("type") == "function" or "function" in t else t
        if not isinstance(fn, dict):
            continue
        name = str(fn.get("name") or t.get("name") or "").strip()
        if not name:
            continue
        params = fn.get("parameters") or t.get("parameters") or {"type": "object", "properties": {}}
        if not isinstance(params, dict):
            params = {"type": "object", "properties": {}}
        out.append({
            "name": name,
            "description": str(fn.get("description") or t.get("description") or name)[:400],
            "parameters": params,
        })
    return out


def sanitize_proposed_calls(proposed: Any, allowed: Optional[List[str]] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Drop anything that is not a named dict call. Unknown names are rejected, not executed.

    Looking well-formed is not authority: the caller still has to run RAD's gate.
    """
    allowed_set = set(allowed or [])
    calls: List[Dict[str, Any]] = []
    rejected: List[str] = []
    if proposed is None:
        return calls, rejected
    if not isinstance(proposed, list):
        rejected.append("malformed: function_calls is not a list")
        return calls, rejected
    for i, item in enumerate(proposed):
        if not isinstance(item, dict):
            rejected.append(f"malformed[{i}]: not an object")
            continue
        name = str(item.get("name") or "").strip()
        args = item.get("arguments") if "arguments" in item else item.get("args")
        if not name:
            rejected.append(f"malformed[{i}]: missing name")
            continue
        if args is None:
            args = {}
        if isinstance(args, str):
            try:
                args = json.loads(args) if args.strip() else {}
            except Exception:
                rejected.append(f"malformed[{i}]: arguments are not JSON")
                continue
        if not isinstance(args, dict):
            rejected.append(f"malformed[{i}]: arguments are not an object")
            continue
        if allowed_set and name not in allowed_set:
            rejected.append(f"unknown_tool[{i}]: {name}")
            continue
        calls.append({"id": str(item.get("id") or f"needle-{i}"), "name": name, "arguments": args})
    return calls, rejected


def _query_from_messages(messages: List[Dict[str, Any]]) -> str:
    """Needle takes a turn of text, not an OpenAI message list. Last user/tool wins."""
    for m in reversed(messages or []):
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        if role == "user":
            return str(m.get("content") or "")
        if role == "tool":
            return json.dumps({"tool": m.get("name"), "tool_call_id": m.get("tool_call_id"),
                               "result": m.get("content")}, ensure_ascii=False)[:8000]
    return str((messages or [{}])[-1].get("content") or "") if messages else ""


class NeedleUnavailable(Exception):
    """Needle is not installed, the engine failed to load, or the response was unusable."""


class NeedleAdapter:
    """Propose tool calls via cactus-needle. Does not execute them.

    `engine` is injectable so tests never need the native Needle binary.
    `engine.complete(text) -> dict` matching Needle's response shape.
    """

    def __init__(self, tools: Optional[List[Dict[str, Any]]] = None, engine: Any = None,
                 system: str = "") -> None:
        self.tools = openai_tools_to_needle(tools)
        self.engine = engine
        self.system = system
        self.last: Dict[str, Any] = {}
        self._load_error = ""

    def available(self) -> bool:
        if self.engine is not None:
            return True
        try:
            self._ensure_engine()
            return True
        except NeedleUnavailable:
            return False

    def _ensure_engine(self) -> Any:
        if self.engine is not None:
            return self.engine
        try:
            import needle  # type: ignore
        except Exception as e:
            self._load_error = f"cactus-needle not importable: {type(e).__name__}: {e}"
            raise NeedleUnavailable(self._load_error)
        try:
            os.environ.setdefault("NEEDLE_TELEMETRY", "0")
            os.environ.setdefault("DO_NOT_TRACK", "1")
            self.engine = needle.Needle(tools=self.tools, system=self.system or None)
            return self.engine
        except Exception as e:
            self._load_error = f"Needle engine failed to load: {type(e).__name__}: {e}"
            raise NeedleUnavailable(self._load_error)

    def propose(self, query: str, allowed: Optional[List[str]] = None) -> Dict[str, Any]:
        """One complete() turn. Never calls engine.run() (that would execute tools)."""
        t0 = time.time()
        allowed_names = allowed or [t["name"] for t in self.tools]
        try:
            engine = self._ensure_engine()
        except NeedleUnavailable as e:
            rec = {"ok": False, "available": False, "error": str(e), "function_calls": [],
                   "rejected": [], "seconds": round(time.time() - t0, 4), "confidence": None,
                   "reasoning": "", "source": "unavailable"}
            self.last = rec
            return rec
        try:
            raw = engine.complete(query)
        except Exception as e:
            rec = {"ok": False, "available": True, "error": f"complete() raised {type(e).__name__}: {e}",
                   "function_calls": [], "rejected": [], "seconds": round(time.time() - t0, 4),
                   "confidence": None, "reasoning": "", "source": "error"}
            self.last = rec
            return rec
        if not isinstance(raw, dict):
            rec = {"ok": False, "available": True, "error": "malformed: complete() did not return a dict",
                   "function_calls": [], "rejected": ["malformed response"],
                   "seconds": round(time.time() - t0, 4), "confidence": None,
                   "reasoning": "", "source": "malformed"}
            self.last = rec
            return rec
        calls, rejected = sanitize_proposed_calls(raw.get("function_calls"), allowed_names)
        rec = {
            "ok": True, "available": True, "error": "",
            "function_calls": calls, "rejected": rejected,
            "suppressed": raw.get("suppressed_calls") or [],
            "seconds": round(time.time() - t0, 4),
            "confidence": raw.get("confidence"),
            "reasoning": str(raw.get("reasoning") or "")[:400],
            "type": raw.get("type"),
            "peak_ram_mb": raw.get("peak_ram_mb"),
            "prefill_tps": raw.get("prefill_tps"),
            "decode_tps": raw.get("decode_tps"),
            "source": "needle",
        }
        self.last = rec
        return rec

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> ChatResult:
        """Session-shaped wrapper: ChatResult with proposed tool_calls, empty text if proposing."""
        if tools:
            self.tools = openai_tools_to_needle(tools)
        query = _query_from_messages(messages)
        rec = self.propose(query, allowed=[t["name"] for t in self.tools])
        res = ChatResult(provider="needle", model="needle")
        res.usage = {"in": 0, "out": 0}
        if not rec.get("ok"):
            raise NeedleUnavailable(rec.get("error") or "needle unavailable")
        res.tool_calls = rec.get("function_calls") or []
        if not res.tool_calls:
            # empty list is a refusal, not a DONE claim — surface reasoning, never invent success
            reason = rec.get("reasoning") or "Needle proposed no tool calls"
            res.text = f"NEEDLE_REFUSAL: {reason}"
        return res


def chat_with_tools(home: RadHome, router_chat: Callable[..., ChatResult],
                    messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
                    engine: Any = None, **chat_kw: Any) -> Tuple[ChatResult, Dict[str, Any]]:
    """Dispatch to existing or Needle. Needle failures fall back to existing.

    Returns (ChatResult, trace). Trace is safe to persist (no secrets).
    """
    kind = resolve_tool_router(home)
    trace: Dict[str, Any] = {"kind": kind, "fallback": ""}
    if kind == "existing":
        return router_chat(messages, tools=tools, **chat_kw), trace
    if kind == "needle":
        adapter = NeedleAdapter(tools=tools, engine=engine)
        try:
            res = adapter.chat(messages, tools=tools)
            trace["needle"] = {k: adapter.last.get(k) for k in
                               ("ok", "available", "error", "rejected", "seconds", "confidence", "source")}
            return res, trace
        except NeedleUnavailable as e:
            trace["fallback"] = "needle_unavailable"
            trace["error"] = str(e)[:300]
            res = router_chat(messages, tools=tools, **chat_kw)
            return res, trace
    # existing | needle are the only legal routers; anything else is a bug.
    _unhandled: str = kind
    raise RuntimeError(f"unhandled tool router {_unhandled!r}")
