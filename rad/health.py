"""Provider health + last-Class-C surface (G4-2 / v0.5.1).

Catalog-alive (GET /v1/models 200) is not inference-entitled (chat/completions
403/429). Last Class C is persisted under ~/.rad/provider_health.json so
`rad doctor` and `rad objective resume` survive process exit.

Do not invent a Class A patch for 403/429. Do not silently spend paid under
free_lock. A 1-token health ping is not a tool-burning retry.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rad import providers as P
from rad.home import RadHome, _read_json, _write_json
from rad.providers import (
    ProviderError,
    ProviderSpec,
    all_specs,
    class_c_kind,
    class_c_next_steps,
    find_key,
    probe_local,
)


@dataclass
class ProviderHealth:
    name: str
    catalog_alive: bool = False
    catalog_status: Optional[int] = None
    inference_entitled: bool = False
    inference_status: Optional[int] = None
    kind: Optional[str] = None
    retry_after: Optional[float] = None
    err: str = ""
    models: List[str] = field(default_factory=list)
    tier: str = ""

    def to_record(self, **extra: Any) -> Dict[str, Any]:
        rec: Dict[str, Any] = {
            "provider": self.name,
            "catalog_alive": self.catalog_alive,
            "catalog_status": self.catalog_status,
            "inference_entitled": self.inference_entitled,
            "inference_status": self.inference_status,
            "kind": self.kind,
            "class_c": bool(self.kind) and not self.inference_entitled,
            "retry_after": self.retry_after,
            "err": self.err,
            "tier": self.tier,
            "at": time.time(),
        }
        rec.update(extra)
        return rec


@dataclass
class LiveGate:
    allow: bool
    reason: str
    next_steps: str = ""
    last: Optional[Dict[str, Any]] = None
    entitled: List[str] = field(default_factory=list)
    catalog_only: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allow": self.allow,
            "reason": self.reason,
            "next_steps": self.next_steps,
            "last": self.last,
            "entitled": list(self.entitled),
            "catalog_only": list(self.catalog_only),
        }


def key_fingerprint(key: Optional[str]) -> str:
    if not key:
        return "none"
    return f"len={len(key)}:{key[:4]}"


def empty_health_state() -> Dict[str, Any]:
    return {"updated": 0.0, "providers": {}, "last": None}


def load_health_state(home: RadHome) -> Dict[str, Any]:
    data = _read_json(home.provider_health_path, empty_health_state())
    if not isinstance(data, dict):
        return empty_health_state()
    data.setdefault("providers", {})
    data.setdefault("last", None)
    data.setdefault("updated", 0.0)
    if not isinstance(data["providers"], dict):
        data["providers"] = {}
    return data


def save_health_state(home: RadHome, data: Dict[str, Any]) -> None:
    data = dict(data)
    data["updated"] = time.time()
    _write_json(home.provider_health_path, data)


def last_class_c(home: RadHome) -> Optional[Dict[str, Any]]:
    last = load_health_state(home).get("last")
    return last if isinstance(last, dict) else None


def class_c_still_blocks(rec: Optional[Dict[str, Any]], now: Optional[float] = None) -> bool:
    """True when a persisted Class C record should still skip that brain."""
    if not rec or not rec.get("class_c"):
        return False
    now = time.time() if now is None else now
    until = rec.get("retry_after_until")
    if rec.get("kind") == "rate_limit" and until is not None:
        try:
            return now < float(until)
        except (TypeError, ValueError):
            return True
    return True


def blocking_class_c_records(home: RadHome, now: Optional[float] = None) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for name, rec in (load_health_state(home).get("providers") or {}).items():
        if isinstance(rec, dict) and class_c_still_blocks(rec, now=now):
            out[str(name)] = rec
    return out


def record_class_c(
    home: RadHome,
    name: str,
    *,
    kind: Optional[str],
    status: Optional[int] = None,
    err: str = "",
    retry_after: Optional[float] = None,
    catalog_alive: Optional[bool] = None,
    objective_id: Optional[str] = None,
    key: Optional[str] = None,
    free_lock: bool = False,
) -> Dict[str, Any]:
    """Persist last Class C so resume/doctor survive process exit."""
    now = time.time()
    until = None
    if retry_after is not None:
        try:
            secs = float(retry_after)
            if secs > 0:
                until = now + secs
            else:
                retry_after = None
        except (TypeError, ValueError):
            retry_after = None
    rec: Dict[str, Any] = {
        "provider": name,
        "class_c": True,
        "kind": kind or "auth",
        "status": status,
        "err": (err or "")[:500],
        "at": now,
        "retry_after": retry_after,
        "retry_after_until": until,
        "catalog_alive": catalog_alive,
        "inference_entitled": False,
        "next_steps": class_c_next_steps(kind, free_lock=free_lock, retry_after=retry_after),
        "objective_id": objective_id or "",
        "key_fp": key_fingerprint(key),
    }
    data = load_health_state(home)
    data["providers"][name] = rec
    data["last"] = rec
    save_health_state(home, data)
    return rec


def clear_class_c(home: RadHome, name: str) -> None:
    data = load_health_state(home)
    data["providers"].pop(name, None)
    last = data.get("last")
    if isinstance(last, dict) and last.get("provider") == name:
        data["last"] = None
    save_health_state(home, data)


def probe_catalog(spec: ProviderSpec, key: Optional[str], timeout: float = 8.0) -> ProviderHealth:
    """GET catalog. 200 means catalog-alive, not inference-entitled."""
    health = ProviderHealth(name=spec.name, tier=spec.tier)
    if spec.local:
        ok, models = probe_local(spec)
        health.catalog_alive = ok
        health.catalog_status = 200 if ok else None
        health.models = list(models or [])
        # A reachable local engine with a model list can actually infer.
        health.inference_entitled = bool(ok)
        health.inference_status = 200 if ok else None
        return health
    try:
        if spec.kind == "anthropic":
            headers = {"x-api-key": key or "", "anthropic-version": "2023-06-01"}
            url = spec.base_url.rstrip("/") + "/v1/models"
            status, _, body = P._http(url, None, headers, timeout)
        elif spec.kind == "gemini":
            url = (spec.base_url.rstrip("/") + "/v1beta/models?key="
                   + urllib.parse.quote(key or ""))
            status, _, body = P._http(url, None, {}, timeout)
        else:
            headers = {"Authorization": f"Bearer {key}"} if key else {}
            url = spec.base_url.rstrip("/") + "/models"
            status, _, body = P._http(url, None, headers, timeout)
        health.catalog_status = status
        if status == 200:
            health.catalog_alive = True
            try:
                d = json.loads(body.decode() if isinstance(body, (bytes, bytearray)) else body)
                if spec.kind == "gemini":
                    health.models = [m.get("name") for m in d.get("models", []) if m.get("name")]
                else:
                    health.models = [m.get("id") for m in d.get("data", []) if m.get("id")]
            except Exception:
                health.models = []
        else:
            health.err = f"catalog HTTP {status}"
    except ProviderError as e:
        health.err = e.msg
        health.catalog_status = e.status
    except Exception as e:
        health.err = str(e)[:200]
    return health


def probe_inference(spec: ProviderSpec, key: Optional[str], timeout: float = 8.0) -> ProviderHealth:
    """One-token chat ping. 403/429 are Class C, not a product hole."""
    health = ProviderHealth(name=spec.name, tier=spec.tier)
    model = spec.default_model
    if spec.local and not model:
        _, models = probe_local(spec)
        model = models[0] if models else ""
    try:
        P.chat(spec, key, [{"role": "user", "content": "ping"}],
             model=model, tools=None, stream_cb=None,
             temperature=0.0, timeout=timeout, max_tokens=1)
        health.inference_entitled = True
        health.inference_status = 200
        return health
    except ProviderError as e:
        health.inference_entitled = False
        health.inference_status = e.status
        health.kind = class_c_kind(e.status, e.msg)
        health.retry_after = e.retry_after
        health.err = e.msg
        return health
    except Exception as e:
        health.err = str(e)[:200]
        return health


def probe_provider_health(
    spec: ProviderSpec,
    key: Optional[str],
    *,
    home: Optional[RadHome] = None,
    force: bool = False,
    timeout: float = 8.0,
    skip_blocked_inference: bool = False,
) -> ProviderHealth:
    """Catalog + inference. Skip a chat re-burn when last Class C still blocks."""
    catalog = probe_catalog(spec, key, timeout=timeout)
    cached = None
    if home is not None:
        cached = (load_health_state(home).get("providers") or {}).get(spec.name)
    key_fp = key_fingerprint(key)
    skip_chat = False
    if skip_blocked_inference and not force and isinstance(cached, dict):
        if cached.get("key_fp") == key_fp and class_c_still_blocks(cached):
            skip_chat = True
        elif cached.get("kind") == "auth" and cached.get("key_fp") == key_fp and cached.get("class_c"):
            # Same key still inference-forbidden — do not re-hit 403 on resume.
            skip_chat = True
    if spec.local:
        return catalog
    if skip_chat:
        catalog.inference_entitled = False
        catalog.inference_status = cached.get("status") if isinstance(cached, dict) else None
        catalog.kind = cached.get("kind") if isinstance(cached, dict) else None
        catalog.retry_after = _remaining_retry_after(cached if isinstance(cached, dict) else None)
        catalog.err = (cached or {}).get("err") or catalog.err
        return catalog
    inf = probe_inference(spec, key, timeout=timeout)
    catalog.inference_entitled = inf.inference_entitled
    catalog.inference_status = inf.inference_status
    catalog.kind = inf.kind
    catalog.retry_after = inf.retry_after
    if inf.err:
        catalog.err = inf.err
    if home is not None:
        if inf.inference_entitled:
            clear_class_c(home, spec.name)
        elif inf.kind:
            record_class_c(
                home, spec.name, kind=inf.kind, status=inf.inference_status,
                err=inf.err, retry_after=inf.retry_after,
                catalog_alive=catalog.catalog_alive, key=key,
                free_lock=bool(home.cfg.get("free_lock")),
            )
    return catalog


def _remaining_retry_after(rec: Optional[Dict[str, Any]], now: Optional[float] = None) -> Optional[float]:
    if not rec:
        return None
    until = rec.get("retry_after_until")
    if until is None:
        return rec.get("retry_after")
    now = time.time() if now is None else now
    try:
        left = float(until) - now
        return left if left > 0 else None
    except (TypeError, ValueError):
        return rec.get("retry_after")


def scan_provider_health(
    home: RadHome,
    *,
    force: bool = False,
    timeout: float = 8.0,
    skip_blocked_inference: bool = False,
) -> List[ProviderHealth]:
    """Health for every key-present / local-reachable spec. Respects free_lock for paid."""
    out: List[ProviderHealth] = []
    free_lock = bool(home.cfg.get("free_lock"))
    for spec in all_specs(home):
        if spec.local:
            h = probe_catalog(spec, None, timeout=timeout)
            if h.catalog_alive:
                out.append(h)
            continue
        key = find_key(home, spec)
        if not key:
            continue
        if free_lock and spec.tier == "paid":
            continue
        out.append(probe_provider_health(
            spec, key, home=home, force=force, timeout=timeout,
            skip_blocked_inference=skip_blocked_inference,
        ))
    return out


def is_class_c_pause(obj: Any, graph: Any = None, home: Optional[RadHome] = None) -> bool:
    """True when this objective paused on AUTH / RATE / inference-forbidden."""
    if obj is not None:
        for text in (getattr(obj, "failure", "") or "", getattr(obj, "result_summary", "") or ""):
            if class_c_kind(None, text):
                return True
    if graph is not None:
        tasks = getattr(graph, "tasks", {}) or {}
        for t in tasks.values() if isinstance(tasks, dict) else tasks:
            fc = getattr(t, "failure_class", "") or ""
            if fc in ("AUTH_FAILURE", "RATE_LIMIT"):
                return True
            note = getattr(t, "note", "") or ""
            if getattr(t, "status", "") == "NEEDS_USER" and class_c_kind(None, note):
                return True
    if home is not None and obj is not None:
        last = last_class_c(home)
        if last and last.get("class_c") and last.get("objective_id") == getattr(obj, "id", None):
            return True
    return False


def evaluate_live_gate(home: RadHome, obj: Any = None, graph: Any = None) -> LiveGate:
    """Safe resume check: do not re-burn the same 403/429 as MODEL.

    Allow when an inference-entitled brain is available (including a recovered
    one). Deny when the only brains are catalog-alive / last-Class-C.
    """
    last = last_class_c(home)
    if obj is not None and not is_class_c_pause(obj, graph, home):
        return LiveGate(allow=True, reason="not a Class C pause", last=last)
    healths = scan_provider_health(home, skip_blocked_inference=True)
    entitled = [h.name for h in healths if h.inference_entitled]
    catalog_only = [h.name for h in healths if h.catalog_alive and not h.inference_entitled]
    if entitled:
        return LiveGate(
            allow=True,
            reason="inference-entitled brain recovered: " + ", ".join(entitled),
            last=last, entitled=entitled, catalog_only=catalog_only,
        )
    kind = (last or {}).get("kind") or "auth"
    retry_after = _remaining_retry_after(last)
    free_lock = bool(home.cfg.get("free_lock"))
    steps = class_c_next_steps(kind, free_lock=free_lock, retry_after=retry_after)
    if last:
        steps = (last.get("next_steps") or steps)
        if retry_after and "Retry-After" not in steps:
            steps = class_c_next_steps(kind, free_lock=free_lock, retry_after=retry_after)
    return LiveGate(
        allow=False,
        reason="no inference-entitled brain — resume would re-hit last Class C",
        next_steps=steps, last=last, catalog_only=catalog_only,
    )


def providers_from_error(error: str) -> List[str]:
    """Best-effort provider names from a Class C error string."""
    names = set(re.findall(
        r"([a-z0-9_.-]{3,20}):\s*(?:HTTP|error|rate|timeout|all providers)",
        error or "", re.I))
    return sorted(n for n in names if n not in ("tool", "python"))


def status_from_error(error: str) -> Optional[int]:
    m = re.search(r"HTTP (\d{3})", error or "", re.I)
    return int(m.group(1)) if m else None
