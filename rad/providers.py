"""The brain socket — every LLM family speaks through one interface.

Three API kinds:
  openai  — OpenAI-compatible chat/completions (OpenAI, Groq, Cerebras,
            Mistral, Grok, OpenRouter, Ollama, vLLM, LM Studio, Edge0 serve, …)
  anthropic — /v1/messages
  gemini  — generativelanguage generateContent

Open door: any OpenAI-compatible endpoint can be added with `rad provider add`
and behaves exactly like a first-class provider.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from rad.home import RadHome


# HTTP statuses that are Class C (keys / quota / inference-forbidden), not product holes.
CLASS_C_STATUSES = frozenset({401, 403, 429})


class ProviderError(Exception):
    def __init__(self, msg: str, status: Optional[int] = None, retryable: bool = True,
                 retry_after: Optional[float] = None) -> None:
        super().__init__(msg)
        self.msg = msg
        self.status = status
        self.retryable = retryable
        self.retry_after = retry_after


def parse_retry_after(headers: Optional[Dict[str, str]]) -> Optional[float]:
    """Return Retry-After as seconds remaining, or None if the header is absent/unusable."""
    if not headers:
        return None
    raw = None
    for k, v in headers.items():
        if str(k).lower() == "retry-after":
            raw = str(v).strip()
            break
    if not raw:
        return None
    try:
        secs = float(raw)
        return secs if secs > 0 else None
    except ValueError:
        pass
    try:
        dt = parsedate_to_datetime(raw)
        left = dt.timestamp() - time.time()
        return left if left > 0 else None
    except Exception:
        return None


def class_c_kind(status: Optional[int] = None, msg: str = "") -> Optional[str]:
    """Return ``auth`` or ``rate_limit`` for Class C provider failures, else None.

    Class C is environment / keys / quota / inference-forbidden. Do not invent a
    Class A product patch for these (RW-084 HTTP 403; RW-086 HTTP 429).
    """
    text = (msg or "").lower()
    if (
        status == 429
        or "http 429" in text
        or "rate limit" in text
        or "free-models-per-day" in text
        or "quota exceeded" in text
        or "insufficient quota" in text
    ):
        return "rate_limit"
    if (
        status in (401, 403)
        or "http 401" in text
        or "http 403" in text
        or "unauthori" in text
        or "invalid api key" in text
        or "authorization failed" in text
        or "inference-forbidden" in text
        or "inference forbidden" in text
        or ("forbidden" in text and "http" in text)
    ):
        return "auth"
    if "forbidden" in text or "invalid api key" in text:
        return "auth"
    return None


def class_c_next_steps(kind: Optional[str] = None, free_lock: bool = False,
                       retry_after: Optional[float] = None) -> str:
    """Actionable pause text: rotate key, wait for quota, switch free provider."""
    lock = " free_lock is on — paid spend stays off." if free_lock else ""
    ra = ""
    if retry_after is not None:
        try:
            secs = float(retry_after)
            if secs > 0:
                ra = f" Retry-After: wait {int(secs)}s before resume."
        except (TypeError, ValueError):
            ra = ""
    if kind == "rate_limit":
        return (
            "Class C provider rate-limit/quota — not a product hole. "
            "Wait for quota to reset, `rad use` another free provider, "
            "or add another free key. Do not invent a Class A patch."
            + ra + lock
        )
    return (
        "Class C provider auth / inference-forbidden — not a product hole. "
        "Rotate the key, check inference entitlement, or `rad use` another free "
        "provider. Do not invent a Class A patch."
        + ra + lock
    )


@dataclass
class ProviderSpec:
    name: str
    kind: str                      # openai | anthropic | gemini
    base_url: str = ""
    key_names: Tuple[str, ...] = ()
    default_model: str = ""
    vision_model: Optional[str] = None
    tier: str = "paid"             # local | free | paid
    local: bool = False
    requires_key: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    max_tokens: int = 4096
    desc: str = ""
    # --- P0 Router Gateway observability (no routing yet) ---
    latency_ms: Optional[float] = None   # last observed latency (ms), None = not yet probed
    cost_per_1k: Optional[float] = None  # USD per 1k tokens (None = free/local or unknown)
    health: str = "unknown"              # unknown | healthy | degraded | down
    health_checked_at: Optional[float] = None  # epoch seconds of last health probe


@dataclass
class ChatResult:
    text: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # {id,name,arguments}
    usage: Dict[str, int] = field(default_factory=dict)             # {in, out}
    provider: str = ""
    model: str = ""


# ---------------------------------------------------------------- HTTP (stdlib)

def _http(url: str, data: Optional[bytes], headers: Dict[str, str], timeout: float,
          stream: bool = False) -> Tuple[int, Dict[str, str], Any]:
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data is not None else "GET")
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return e.code, dict(e.headers or {}), body
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise ProviderError(f"network: {e}", retryable=True)
    body = resp.read() if not stream else resp
    return resp.status, dict(resp.headers or {}), body


def _post_json(url: str, body: Dict[str, Any], headers: Dict[str, str], timeout: float,
               stream: bool = False) -> Tuple[int, Dict[str, str], Any]:
    data = json.dumps(body).encode("utf-8")
    headers = dict(headers)
    headers.setdefault("Content-Type", "application/json")
    return _http(url, data, headers, timeout, stream=stream)


def _sse_lines(resp) -> Iterable[str]:
    """Yield payload strings of `data:` lines from a streaming response."""
    for raw in resp:
        line = raw.decode("utf-8", "replace").strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        yield payload


def _body_bytes(resp: Any) -> bytes:
    """Non-streaming responses arrive as bytes; tolerate file-like objects too."""
    if isinstance(resp, (bytes, bytearray)):
        return bytes(resp)
    return resp.read()


def _read_error_body(body: Any) -> str:
    try:
        d = json.loads(body.decode("utf-8", "replace"))
        return d.get("error", {}).get("message") or d.get("error") or json.dumps(d)[:300]
    except Exception:
        return str(body)[:300]


def _retryable(status: int) -> bool:
    return status in (408, 429, 500, 502, 503, 504) or status is None


# ---------------------------------------------------------------- specs

def _builtin_specs(home: RadHome) -> List[ProviderSpec]:
    ollama_base = home.cfg.get("ollama_url", "http://127.0.0.1:11434")
    return [
        ProviderSpec("edge0", "openai", home.cfg.get("edge0_url", "http://127.0.0.1:8000/v1"),
                     tier="local", local=True, requires_key=False,
                     default_model=home.cfg.get("edge0_model", ""),
                     desc="Edge0 local MoE (Apple Silicon) — built-in brain"),
        ProviderSpec("ollama", "openai", ollama_base.rstrip("/") + "/v1",
                     tier="local", local=True, requires_key=False,
                     default_model="", desc="Ollama (local)"),
        ProviderSpec("lmstudio", "openai", home.cfg.get("lmstudio_url", "http://127.0.0.1:1234/v1"),
                     tier="local", local=True, requires_key=False,
                     default_model="", desc="LM Studio (local)"),
        ProviderSpec("groq", "openai", "https://api.groq.com/openai/v1", ("GROQ_API_KEY",),
                     default_model="llama-3.3-70b-versatile", vision_model="llama-3.2-11b-vision-preview",
                     tier="free", supports_vision=True, desc="Groq free tier"),
        ProviderSpec("cerebras", "openai", "https://api.cerebras.ai/v1", ("CEREBRAS_API_KEY",),
                     default_model="llama-3.3-70b", tier="free", desc="Cerebras free tier"),
        ProviderSpec("gemini", "gemini", "https://generativelanguage.googleapis.com",
                     ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
                     default_model="gemini-2.0-flash", vision_model="gemini-2.0-flash",
                     tier="free", supports_vision=True, desc="Gemini free tier"),
        ProviderSpec("openrouter", "openai", "https://openrouter.ai/api/v1", ("OPENROUTER_API_KEY",),
                     default_model="liquid/lfm-2.5-2.6b:free",
                     vision_model="qwen/qwen-2.5-vl-72b-instruct:free",
                     tier="free", supports_vision=True, desc="OpenRouter free models"),
        ProviderSpec("nvidia", "openai", "https://integrate.api.nvidia.com/v1",
                     ("NVIDIA_NIM_API_KEY", "NVIDIA_API_KEY"),
                     # llama-3.3-70b-instruct reached NIM EOL on 2026-08-26 (HTTP 410).
                     default_model="meta/llama-3.2-11b-vision-instruct",
                     vision_model="meta/llama-3.2-11b-vision-instruct",
                     tier="free", supports_vision=True, max_tokens=2048,
                     desc="NVIDIA NIM (free-credit models)"),
        ProviderSpec("openai", "openai", "https://api.openai.com/v1", ("OPENAI_API_KEY",),
                     default_model="gpt-4o-mini", vision_model="gpt-4o",
                     supports_vision=True, tier="paid", desc="OpenAI"),
        ProviderSpec("anthropic", "anthropic", "https://api.anthropic.com", ("ANTHROPIC_API_KEY",),
                     default_model="claude-sonnet-4-20250514",
                     vision_model="claude-sonnet-4-20250514",
                     supports_vision=True, tier="paid", desc="Anthropic Claude"),
        ProviderSpec("mistral", "openai", "https://api.mistral.ai/v1", ("MISTRAL_API_KEY",),
                     default_model="mistral-small-latest", tier="paid", desc="Mistral"),
        ProviderSpec("grok", "openai", "https://api.x.ai/v1", ("XAI_API_KEY",),
                     default_model="grok-4", tier="paid", desc="xAI Grok"),
    ]


def all_specs(home: RadHome) -> List[ProviderSpec]:
    specs = _builtin_specs(home)
    for c in home.cfg.get("custom_providers", []) or []:
        specs.append(ProviderSpec(
            c.get("name", "custom"), "openai", c.get("url", ""),
            key_names=(c["key"],) if c.get("key") else (),
            default_model=c.get("model", ""),
            tier=c.get("tier", "paid"), local=c.get("url", "").startswith(("http://127", "http://localhost")),
            requires_key=bool(c.get("key")),
            desc=f"custom: {c.get('url')}",
        ))
    return specs


spec_by_name = {
    "openai": (0.00015, 0.0006),
    "anthropic": (0.003, 0.015),
    "mistral": (0.0001, 0.0003),
    "grok": (0.003, 0.015),
    "gemini": (0.0, 0.0),
    "groq": (0.0, 0.0),
    "cerebras": (0.0, 0.0),
    "openrouter": (0.0005, 0.0015),
}


# ---------------------------------------------------------------- health snapshot (P0 observability stub)

def provider_health_snapshot(home) -> list:
    """GET /v1/providers/health backing store (observability only).
    P0: no routing decisions; returns latency_ms/cost_per_1k/health for each spec.
    Values are stubbed from static tier/cost table + probe history when available.
    """
    specs = all_specs(home)
    _COST = {
        "edge0": None, "ollama": None, "lmstudio": None,
        "groq": 0.0, "cerebras": 0.0, "gemini": 0.0, "openrouter": 0.0005,
        "nvidia": 0.0, "openai": 0.0003, "anthropic": 0.006, "mistral": 0.0002, "grok": 0.006,
    }
    out = []
    for s in specs:
        cost = _COST.get(s.name, s.cost_per_1k)
        c = s.cost_per_1k if s.cost_per_1k is not None else cost
        out.append({
            "name": s.name,
            "kind": s.kind,
            "tier": s.tier,
            "base_url": s.base_url,
            "latency_ms": s.latency_ms,
            "cost_per_1k": c,
            "health": s.health,
            "health_checked_at": s.health_checked_at,
            "supports_tools": s.supports_tools,
            "supports_vision": s.supports_vision,
            "desc": s.desc,
        })
    return out


# ---------------------------------------------------------------- key fetching

def _parse_env_file(path: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def env_files_scan(home: RadHome) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for p in (os.getcwd() + "/.env", os.path.expanduser("~/.env"), str(home.keys_env_path)):
        found.update(_parse_env_file(p))
    return found


def find_key(home: RadHome, spec: ProviderSpec) -> Optional[str]:
    """Priority: Rad vault → process env → .env files."""
    if not spec.requires_key:
        return None
    key_names = spec.key_names or (spec.name.upper() + "_API_KEY",)
    vault = home.vault_get_all()
    # vault is keyed by provider name (`rad keys add`), env-var names also accepted
    for k in (spec.name, *key_names):
        if vault.get(k):
            return vault[k]
    for name in key_names:
        v = os.environ.get(name)
        if v:
            return v
    scan = env_files_scan(home)
    for name in key_names:
        if scan.get(name):
            return scan[name]
    return None


# ---------------------------------------------------------------- local probing

def detect_gguf_import(spec: ProviderSpec) -> dict:
    """P1 stub: GGUF import detection for Ollama (rad/providers probe_local extension).
    Returns {supported: bool, reason: str, gguf_models: []}. Offline-safe."""
    if spec.name != "ollama":
        return {"supported": False, "reason": "only ollama supports GGUF import", "gguf_models": []}
    # stub: check if ollama reachable then GGUF import is supported (ollama create from GGUF)
    # future: inspect OLLAMA_MODELS dir for *.gguf, call ollama show --modelfile
    try:
        base = spec.base_url.rsplit("/v1", 1)[0]
        status, _, body = _http(base + "/api/tags", None, {}, 1.2)
        gguf_models = []
        if status == 200:
            try:
                names = [m.get("name","") for m in json.loads(body.decode()).get("models", [])]
                gguf_models = [n for n in names if "gguf" in n.lower() or n.lower().endswith(".gguf")]
            except Exception:
                gguf_models = []
            return {"supported": True, "reason": "ollama reachable: GGUF import via ollama create", "gguf_models": gguf_models}
        return {"supported": True, "reason": "ollama GGUF import stub (offline: ollama create from GGUF when reachable)", "gguf_models": []}
    except Exception as e:
        return {"supported": True, "reason": "ollama GGUF import stub (offline: " + str(e)[:60] + ")", "gguf_models": []}

def probe_local(spec: ProviderSpec) -> Tuple[bool, List[str]]:
    """Return (reachable, model_names). P1: also populates GGUF detection for ollama."""
    try:
        if spec.name == "ollama":
            base = spec.base_url.rsplit("/v1", 1)[0]
            status, _, body = _http(base + "/api/tags", None, {}, 1.2)
            if status == 200:
                names = [m.get("name") for m in json.loads(body.decode()).get("models", []) if m.get("name")]
                # P1 GGUF detection: annotate spec with GGUF support (observability)
                try:
                    gguf = [n for n in names if "gguf" in n.lower() or n.lower().endswith(".gguf")]
                    # store on spec for health snapshot (non-breaking)
                    spec._gguf_models = gguf  # type: ignore
                    spec._gguf_supported = True  # type: ignore
                except Exception:
                    pass
                return True, names
            # offline stub: still report GGUF import as supported (ollama create)
            try:
                spec._gguf_supported = True  # type: ignore
                spec._gguf_models = []  # type: ignore
            except Exception:
                pass
            return False, []
        status, _, body = _http(spec.base_url + "/models", None, {}, 1.2)
        if status == 200:
            d = json.loads(body.decode())
            names = [m.get("id") for m in d.get("data", []) if m.get("id")]
            return True, names
        return False, []
    except Exception:
        return False, []


# ---------------------------------------------------------------- chat: openai-compat

def _openai_message(m: Dict[str, Any]) -> Dict[str, Any]:
    """Shape a chat message for OpenAI-compatible /chat/completions.

    RAD's session stores tool calls as `{id,name,arguments}`. NVIDIA NIM (and strict
    OpenAI validators) require `{id,type:function,function:{name,arguments}}` with
    `arguments` as a JSON string. Sending the flat shape yields HTTP 400.
    """
    out = dict(m)
    tcs = out.get("tool_calls")
    if not tcs:
        return out
    wire = []
    for tc in tcs:
        if not isinstance(tc, dict):
            continue
        if "function" in tc:
            item = dict(tc)
            item.setdefault("type", "function")
            fn = dict(item.get("function") or {})
            args = fn.get("arguments", {})
            if not isinstance(args, str):
                fn["arguments"] = json.dumps(args or {})
            item["function"] = fn
            wire.append(item)
            continue
        args = tc.get("arguments", {})
        if not isinstance(args, str):
            args = json.dumps(args or {})
        wire.append({"id": tc.get("id") or "", "type": "function",
                     "function": {"name": tc.get("name") or "", "arguments": args}})
    out["tool_calls"] = wire
    if out.get("content") is None:
        out["content"] = ""
    return out


def _unparallel_tool_history(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split an assistant turn that issued N tool_calls into N single-call turns.

    `meta/llama-3.2-11b-vision-instruct` on NVIDIA NIM rejects a follow-up whose
    history contains more than one tool_call in a single assistant message
    (HTTP 400: "This model only supports single tool-calls at once"). RAD still
    executes every call locally; this only reshapes the transcript for the next
    request. Assistant messages with 0–1 tool_calls are unchanged.
    """
    out: List[Dict[str, Any]] = []
    i = 0
    n = len(messages)
    while i < n:
        m = messages[i]
        tcs = m.get("tool_calls") if isinstance(m, dict) else None
        if not (isinstance(m, dict) and m.get("role") == "assistant" and isinstance(tcs, list) and len(tcs) > 1):
            out.append(m)
            i += 1
            continue
        tools: List[Dict[str, Any]] = []
        j = i + 1
        while j < n and isinstance(messages[j], dict) and messages[j].get("role") == "tool":
            tools.append(messages[j])
            j += 1
        by_id: Dict[str, Dict[str, Any]] = {}
        unused: List[Dict[str, Any]] = []
        for tm in tools:
            tid = str(tm.get("tool_call_id") or "")
            if tid and tid not in by_id:
                by_id[tid] = tm
            else:
                unused.append(tm)
        for k, tc in enumerate(tcs):
            if not isinstance(tc, dict):
                continue
            am = dict(m)
            am["tool_calls"] = [tc]
            if k:
                am["content"] = ""
            out.append(am)
            tid = str(tc.get("id") or "")
            if tid in by_id:
                out.append(by_id.pop(tid))
            elif unused:
                out.append(unused.pop(0))
        out.extend(by_id[t] for t in list(by_id))
        out.extend(unused)
        i = j
    return out


def _openai_visible_text(msg: Dict[str, Any]) -> str:
    """Assistant text. Thinking models may leave content empty and put the reply in reasoning."""
    content = msg.get("content")
    if isinstance(content, list):
        bits = []
        for part in content:
            if isinstance(part, str):
                bits.append(part)
            elif isinstance(part, dict) and part.get("text"):
                bits.append(str(part["text"]))
        content = "".join(bits)
    text = content if isinstance(content, str) else ""
    if text.strip() or msg.get("tool_calls"):
        return text
    for key in ("reasoning", "reasoning_content"):
        alt = msg.get(key)
        if isinstance(alt, str) and alt.strip():
            return alt
    return text


def _chat_openai(spec: ProviderSpec, key: Optional[str], messages: List[Dict[str, Any]],
                 model: str, tools: Optional[List[Dict[str, Any]]], stream_cb: Optional[Callable[[str], None]],
                 temperature: float, timeout: float, max_tokens: int) -> ChatResult:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    if spec.name == "nvidia":
        # NIM quirk: some endpoints force SSE unless Accept: application/json is set
        headers.setdefault("Accept", "application/json")
        messages = _unparallel_tool_history(messages)
    body: Dict[str, Any] = {
        "model": model, "messages": [_openai_message(m) for m in messages],
        "temperature": temperature,
        "stream": stream_cb is not None,
    }
    if max_tokens:
        body["max_tokens"] = max_tokens
    if tools and spec.supports_tools:
        body["tools"] = tools
        if spec.name == "nvidia":
            # llama-3.2-11b-vision-instruct rejects parallel tool_calls (HTTP 400).
            body["parallel_tool_calls"] = False
    if spec.name == "ollama":
        # qwen3-class models put the reply in `reasoning` and leave `content` empty
        # unless thinking is off. Measured 2026-09-22 on /v1/chat/completions.
        body["reasoning_effort"] = "none"
    status, headers_out, resp = _post_json(spec.base_url + "/chat/completions", body, headers, timeout,
                                 stream=stream_cb is not None)
    if status != 200:
        err = _read_error_body(resp if isinstance(resp, bytes) else b"")
        # NIM retires models with HTTP 410. Retry the still-listed vision/default fallback
        # once so a stale pin of llama-3.3-70b-instruct (EOL 2026-08-26) still works.
        if (spec.name == "nvidia" and status == 410 and spec.vision_model
                and model != spec.vision_model):
            return _chat_openai(spec, key, messages, spec.vision_model, tools, stream_cb,
                                temperature, timeout, max_tokens)
        raise ProviderError(f"{spec.name}: HTTP {status} {err}",
                            status=status, retryable=_retryable(status),
                            retry_after=parse_retry_after(headers_out))
    res = ChatResult(provider=spec.name, model=model)
    if stream_cb is None:
        d = json.loads(_body_bytes(resp).decode())
        msg = d["choices"][0]["message"]
        res.text = _openai_visible_text(msg)
        res.usage = {"in": d.get("usage", {}).get("prompt_tokens", 0),
                     "out": d.get("usage", {}).get("completion_tokens", 0)}
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except Exception:
                args = {}
            res.tool_calls.append({"id": tc.get("id", ""), "name": fn.get("name", ""), "arguments": args})
        return res
    # streaming
    acc: Dict[int, Dict[str, Any]] = {}
    text_parts: List[str] = []
    for payload in _sse_lines(resp):
        try:
            d = json.loads(payload)
        except Exception:
            continue
        ch = (d.get("choices") or [{}])[0]
        delta = ch.get("delta") or {}
        piece = delta.get("content") or ""
        if not piece and not delta.get("tool_calls"):
            piece = delta.get("reasoning") or delta.get("reasoning_content") or ""
        if piece:
            text_parts.append(piece)
            stream_cb(piece)
        for tc in delta.get("tool_calls") or []:
            i = tc.get("index", 0)
            slot = acc.setdefault(i, {"id": "", "name": "", "arguments": ""})
            if tc.get("id"):
                slot["id"] = tc["id"]
            fn = tc.get("function") or {}
            if fn.get("name"):
                slot["name"] = fn["name"]
            if fn.get("arguments"):
                slot["arguments"] += fn["arguments"]
        if d.get("usage"):
            res.usage = {"in": d["usage"].get("prompt_tokens", 0), "out": d["usage"].get("completion_tokens", 0)}
    res.text = "".join(text_parts)
    for i in sorted(acc):
        slot = acc[i]
        try:
            args = json.loads(slot["arguments"] or "{}")
        except Exception:
            args = {}
        res.tool_calls.append({"id": slot["id"], "name": slot["name"], "arguments": args})
    return res


# ---------------------------------------------------------------- chat: anthropic

def _image_part_to_anthropic(part: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if part.get("type") != "image_url":
        return None
    url = (part.get("image_url") or {}).get("url", "")
    if url.startswith("data:"):
        m = re.match(r"data:([^;]+);base64,(.+)$", url, re.S)
        if m:
            return {"type": "image", "source": {"type": "base64",
                                                "media_type": m.group(1), "data": m.group(2)}}
    return None


def _to_anthropic(messages: List[Dict[str, Any]]):
    system: List[str] = []
    msgs: List[Dict[str, Any]] = []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if role == "system":
            system.append(content if isinstance(content, str) else json.dumps(content))
        elif role == "tool":
            item = {"role": "user", "content": [{"type": "tool_result", "tool_use_id": m.get("tool_call_id", ""),
                                                 "content": content if isinstance(content, str) else json.dumps(content)}]}
            if msgs and msgs[-1]["role"] == "user" and isinstance(msgs[-1]["content"], list):
                msgs[-1]["content"].extend(item["content"])
            else:
                msgs.append(item)
        elif role == "assistant":
            c: Any = content
            if isinstance(content, str):
                c = [{"type": "text", "text": content}]
            for tc in m.get("tool_calls") or []:
                c.append({"type": "tool_use", "id": tc.get("id", ""), "name": tc.get("name", ""),
                          "input": tc.get("arguments", {})})
            msgs.append({"role": "assistant", "content": c})
        else:
            if isinstance(content, list):
                c: Any = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        conv = _image_part_to_anthropic(part)
                        if conv:
                            c.append(conv)
                    elif isinstance(part, dict) and part.get("type") == "text":
                        c.append({"type": "text", "text": part.get("text", "")})
                    else:
                        c.append({"type": "text", "text": str(part)})
                content = c
            item = {"role": "user", "content": content if isinstance(content, (str, list)) else json.dumps(content)}
            if msgs and msgs[-1]["role"] == "user" and isinstance(msgs[-1]["content"], list) and isinstance(item["content"], list):
                msgs[-1]["content"].extend(item["content"])
            else:
                msgs.append(item)
    return "\n\n".join(system), msgs


def _chat_anthropic(spec: ProviderSpec, key: Optional[str], messages: List[Dict[str, Any]],
                    model: str, tools: Optional[List[Dict[str, Any]]], stream_cb: Optional[Callable[[str], None]],
                    temperature: float, timeout: float, max_tokens: int) -> ChatResult:
    headers = {"x-api-key": key or "", "anthropic-version": "2023-06-01"}
    system, msgs = _to_anthropic(messages)
    body: Dict[str, Any] = {"model": model, "max_tokens": max_tokens or 4096, "messages": msgs,
                            "temperature": temperature, "stream": stream_cb is not None}
    if system:
        body["system"] = system
    if tools and spec.supports_tools:
        body["tools"] = [{"name": t["function"]["name"],
                          "description": t["function"].get("description", ""),
                          "input_schema": t["function"].get("parameters", {"type": "object", "properties": {}})}
                         for t in tools]
    status, headers_out, resp = _post_json(spec.base_url + "/v1/messages", body, headers, timeout,
                                 stream=stream_cb is not None)
    if status != 200:
        raise ProviderError(f"{spec.name}: HTTP {status} {_read_error_body(resp if isinstance(resp, bytes) else b'')}",
                            status=status, retryable=_retryable(status),
                            retry_after=parse_retry_after(headers_out))
    res = ChatResult(provider=spec.name, model=model)
    if stream_cb is None:
        d = json.loads(_body_bytes(resp).decode())
        for block in d.get("content", []):
            if block.get("type") == "text":
                res.text += block.get("text", "")
            elif block.get("type") == "tool_use":
                res.tool_calls.append({"id": block.get("id", ""), "name": block.get("name", ""),
                                       "arguments": block.get("input", {})})
        res.usage = {"in": d.get("usage", {}).get("input_tokens", 0),
                     "out": d.get("usage", {}).get("output_tokens", 0)}
        return res
    # streaming
    text_parts: List[str] = []
    tool_acc: Dict[int, Dict[str, Any]] = {}
    block_types: Dict[int, str] = {}
    for payload in _sse_lines(resp):
        try:
            d = json.loads(payload)
        except Exception:
            continue
        t = d.get("type")
        if t == "content_block_start":
            b = d.get("content_block", {})
            block_types[d.get("index", 0)] = b.get("type", "")
            if b.get("type") == "tool_use":
                tool_acc[d.get("index", 0)] = {"id": b.get("id", ""), "name": b.get("name", ""), "arguments": ""}
        elif t == "content_block_delta":
            delta = d.get("delta", {})
            if delta.get("type") == "text_delta" and delta.get("text"):
                text_parts.append(delta["text"])
                stream_cb(delta["text"])
            elif delta.get("type") == "input_json_delta" and delta.get("partial_json"):
                slot = tool_acc.get(d.get("index", 0))
                if slot is not None:
                    slot["arguments"] += delta["partial_json"]
        elif t == "message_delta" and d.get("usage"):
            u = d["usage"]
            res.usage["out"] = u.get("output_tokens", res.usage.get("out", 0))
    res.text = "".join(text_parts)
    for i, slot in tool_acc.items():
        try:
            args = json.loads(slot["arguments"] or "{}")
        except Exception:
            args = {}
        res.tool_calls.append({"id": slot["id"], "name": slot["name"], "arguments": args})
    return res


# ---------------------------------------------------------------- chat: gemini

def _to_gemini(messages: List[Dict[str, Any]]):
    sys_parts: List[Dict[str, Any]] = []
    contents: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role")
        if role == "system":
            sys_parts.append({"text": m.get("content", "") if isinstance(m.get("content"), str) else json.dumps(m.get("content"))})
            continue
        parts: List[Dict[str, Any]] = []
        c = m.get("content")
        if role == "tool":
            parts.append({"functionResponse": {"name": m.get("name", "tool"),
                                               "response": {"result": c if isinstance(c, str) else json.dumps(c)}}})
            grole = "user"
        elif role == "assistant":
            if isinstance(c, str):
                parts.append({"text": c})
            for tc in m.get("tool_calls") or []:
                parts.append({"functionCall": {"name": tc.get("name", ""), "args": tc.get("arguments", {})}})
            grole = "model"
        else:
            if isinstance(c, str):
                parts.append({"text": c})
            elif isinstance(c, list):
                for part in c:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append({"text": part.get("text", "")})
                    elif isinstance(part, dict) and part.get("type") == "image_url":
                        url = (part.get("image_url") or {}).get("url", "")
                        m = re.match(r"data:([^;]+);base64,(.+)$", url, re.S)
                        if m:
                            parts.append({"inline_data": {"mime_type": m.group(1), "data": m.group(2)}})
            else:
                parts.append({"text": json.dumps(c)})
            grole = "user"
        if parts:
            contents.append({"role": grole, "parts": parts})
    return sys_parts, contents


def _chat_gemini(spec: ProviderSpec, key: Optional[str], messages: List[Dict[str, Any]],
                 model: str, tools: Optional[List[Dict[str, Any]]], stream_cb: Optional[Callable[[str], None]],
                 temperature: float, timeout: float, max_tokens: int) -> ChatResult:
    sys_parts, contents = _to_gemini(messages)
    body: Dict[str, Any] = {"contents": contents,
                            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens or 4096}}
    if sys_parts:
        body["systemInstruction"] = {"parts": sys_parts}
    if tools and spec.supports_tools:
        body["tools"] = [{"functionDeclarations": [
            {"name": t["function"]["name"],
             "description": t["function"].get("description", ""),
             "parameters": t["function"].get("parameters", {"type": "object", "properties": {}})}
            for t in tools]}]
    url = (f"{spec.base_url}/v1beta/models/{model}:generateContent?key={urllib.parse.quote(key or '')}"
           + ("?alt=sse" if stream_cb else ""))
    if stream_cb:
        url = url.replace("?alt=sse", "?key=" + urllib.parse.quote(key or "") + "&alt=sse")
        url = re.sub(r"\?key=[^&]*(&alt=sse)$", r"\1", url)
        url = url.split("?")[0] + "?key=" + urllib.parse.quote(key or "") + "&alt=sse"
    status, headers_out, resp = _post_json(url, body, {}, timeout, stream=stream_cb is not None)
    if status != 200:
        raise ProviderError(f"{spec.name}: HTTP {status} {_read_error_body(resp if isinstance(resp, bytes) else b'')}",
                            status=status, retryable=_retryable(status),
                            retry_after=parse_retry_after(headers_out))
    res = ChatResult(provider=spec.name, model=model)
    if stream_cb is None:
        d = json.loads(_body_bytes(resp).decode())
        cand = (d.get("candidates") or [{}])[0]
        for part in (cand.get("content") or {}).get("parts", []):
            if part.get("text"):
                res.text += part["text"]
            elif part.get("functionCall"):
                res.tool_calls.append({"id": f"gemini-{len(res.tool_calls)}",
                                       "name": part["functionCall"].get("name", ""),
                                       "arguments": part["functionCall"].get("args", {})})
        u = d.get("usageMetadata") or {}
        res.usage = {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0)}
        return res
    text_parts: List[str] = []
    for payload in _sse_lines(resp):
        try:
            d = json.loads(payload)
        except Exception:
            continue
        cand = (d.get("candidates") or [{}])[0]
        for part in (cand.get("content") or {}).get("parts", []):
            if part.get("text"):
                text_parts.append(part["text"])
                stream_cb(part["text"])
            elif part.get("functionCall"):
                res.tool_calls.append({"id": f"gemini-{len(res.tool_calls)}",
                                       "name": part["functionCall"].get("name", ""),
                                       "arguments": part["functionCall"].get("args", {})})
        u = d.get("usageMetadata") or {}
        if u:
            res.usage = {"in": u.get("promptTokenCount", 0), "out": u.get("candidatesTokenCount", 0)}
    res.text = "".join(text_parts)
    return res


# ---------------------------------------------------------------- dispatch

def chat(spec: ProviderSpec, key: Optional[str], messages: List[Dict[str, Any]],
         model: str = "", tools: Optional[List[Dict[str, Any]]] = None,
         stream_cb: Optional[Callable[[str], None]] = None,
         temperature: float = 0.7, timeout: float = 180.0, max_tokens: int = 0) -> ChatResult:
    model = model or spec.default_model
    max_tokens = max_tokens or spec.max_tokens
    if not model:
        raise ProviderError(f"{spec.name}: no model selected (set one or use a provider with a default)",
                            retryable=False)
    if spec.kind == "anthropic":
        return _chat_anthropic(spec, key, messages, model, tools, stream_cb, temperature, timeout, max_tokens)
    if spec.kind == "gemini":
        return _chat_gemini(spec, key, messages, model, tools, stream_cb, temperature, timeout, max_tokens)
    return _chat_openai(spec, key, messages, model, tools, stream_cb, temperature, timeout, max_tokens)


def list_models(spec: ProviderSpec, key: Optional[str]) -> List[str]:
    try:
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        status, _, body = _http(spec.base_url + "/models", None, headers, 8.0)
        if status == 200:
            d = json.loads(body.decode())
            return [m.get("id") for m in d.get("data", []) if m.get("id")]
    except Exception:
        pass
    return []
