"""Routing engine — picks the brain, rotates free tiers, falls back, tracks cost.

Chain order: local engines → free cloud tiers (round-robin) → paid (unless free-lock).
"""
from __future__ import annotations

import itertools
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from rad import providers as P
from rad.home import RadHome
from rad.ui import col

TIER_RANK = {"local": 0, "free": 1, "paid": 2}


@dataclass
class ChainEntry:
    spec: P.ProviderSpec
    key: Optional[str]
    model: str = ""
    reachable: bool = True
    origin: str = "env"  # vault | env | .env | local | custom


@dataclass
class RouterState:
    home: RadHome
    failures: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    preferred: Dict[str, str] = field(default_factory=dict)  # tier -> provider name
    _free_rr: "itertools.cycle" = None  # type: ignore
    warned_no_crypto: bool = False
    last_selection: Optional[Dict[str, Any]] = None          # task-aware selection trace

    # ---------------------------------------------------------------- chain
    def build_chain(self, force: Optional[str] = None, free_lock: Optional[bool] = None,
                    need_vision: bool = False) -> List[ChainEntry]:
        force = force or self.home.cfg.get("force_provider")
        free_lock = (self.home.cfg.get("free_lock") if free_lock is None else free_lock)
        entries: List[ChainEntry] = []
        for spec in P.all_specs(self.home):
            if need_vision and not spec.supports_vision:
                continue
            entry = self._probe(spec)
            if entry is None:
                continue
            if free_lock and entry.spec.tier == "paid":
                continue
            # Skip brains that already failed Class C this process so we rotate
            # to another usable free provider instead of re-pinning a 403/429.
            fail = self.failures.get(entry.spec.name) or {}
            if fail.get("class_c"):
                continue
            entries.append(entry)
        entries.sort(key=lambda e: (TIER_RANK[e.spec.tier], e.spec.name))
        if force:
            entries.sort(key=lambda e: 0 if e.spec.name == force else 1)
        self._rotate_free(entries)
        return entries

    def _probe(self, spec: P.ProviderSpec) -> Optional[ChainEntry]:
        if spec.local:
            ok, models = P.probe_local(spec)
            if not ok:
                return None
            model = spec.default_model
            if not model and models:
                model = models[0]
            tier = spec.tier
            return ChainEntry(spec, None, model=model, origin="local")
        key = P.find_key(self.home, spec)
        if not key:
            return None
        if key in self.home.vault_get_all().values():
            origin = "vault"
        elif any(os.environ.get(n) == key for n in spec.key_names):
            origin = "env"
        else:
            origin = ".env"
        return ChainEntry(spec, key, model=spec.default_model, origin=origin)

    def _rotate_free(self, entries: List[ChainEntry]) -> None:
        """Round-robin inside the free tier so no single free tier walls you off."""
        free = [e for e in entries if e.spec.tier == "free"]
        if len(free) < 2:
            return
        order = {e.spec.name: i for i, e in enumerate(free)}
        start = self.preferred.get("free")
        if start and start in order:
            names = [e.spec.name for e in free]
            i = names.index(start)
            rotated = [free[j] for j in range(i, len(free))] + [free[j] for j in range(0, i)]
        else:
            rotated = free
            self.preferred["free"] = free[0].spec.name
        free_slots = [i for i, e in enumerate(entries) if e.spec.tier == "free"]
        for slot, e in zip(free_slots, rotated):
            entries[slot] = e

    # ---------------------------------------------------------------- chat
    def build_chain_for(self, requirements: Optional[Any] = None, force: Optional[str] = None,
                        free_lock: Optional[bool] = None, need_vision: bool = False) -> List[ChainEntry]:
        """Availability chain, re-ordered for a task's requirements (free-first preserved)."""
        chain = self.build_chain(force=force, free_lock=free_lock, need_vision=need_vision)
        if not chain:
            return chain
        try:
            from rad.modelselect import ModelRegistry, Requirements
            req = requirements if isinstance(requirements, Requirements) else None
            if req is None and requirements is not None:
                req = Requirements(kind=str(getattr(requirements, "kind", "chat")))
            if req is None:
                return chain
            sel = ModelRegistry(self.home).select(chain, req)
            selected = sel or chain
            self.last_selection = {"kind": req.kind, "requested": [getattr(e.spec, "name", "?") for e in chain],
                                   "selected": [getattr(e.spec, "name", "?") for e in selected]}
            if req.need_vision or req.kind == "vision":
                confirmed = [getattr(e.spec, "name", "?") for e in selected
                             if getattr(e.spec, "supports_vision", False)]
                self.last_selection["vision_confirmed"] = confirmed
                if not confirmed:
                    # honest degradation: a vision task is being sent to a model RAD cannot
                    # confirm accepts images. Recorded, surfaced (`rad status`), never hidden.
                    self.last_selection["vision_gap"] = True
            return selected
        except Exception:
            return chain

    def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None,
             stream_cb: Optional[Callable[[str], None]] = None,
             need_vision: bool = False, temperature: float = 0.7,
             model_override: Optional[str] = None, max_tokens: int = 0,
             requirements: Optional[Any] = None) -> P.ChatResult:
        if requirements is not None:
            need_vision = need_vision or bool(getattr(requirements, "need_vision", False)) \
                or getattr(requirements, "kind", "") == "vision"
        chain = self.build_chain_for(requirements=requirements, need_vision=need_vision)
        if not chain:
            if any((f or {}).get("class_c") for f in self.failures.values()):
                kinds = {(f or {}).get("kind") for f in self.failures.values() if (f or {}).get("class_c")}
                kind = "rate_limit" if "rate_limit" in kinds else "auth"
                statuses = [f.get("status") for f in self.failures.values() if (f or {}).get("class_c")]
                status = next((s for s in statuses if s in P.CLASS_C_STATUSES), None)
                raise P.ProviderError(
                    "all providers failed (Class C — not a product hole):\n  "
                    + "\n  ".join(f"{n}: {f.get('err', '')}" for n, f in self.failures.items() if (f or {}).get("class_c"))
                    + "\n" + P.class_c_next_steps(kind, free_lock=bool(self.home.cfg.get("free_lock"))),
                    status=status, retryable=False)
            hint = ("no vision-capable brain available — this task includes an image; "
                    "`rad providers` lists what each provider/model supports, then "
                    "`rad use <provider>` or `rad provider add` with a vision model "
                    "(e.g. gpt-4o, claude-3.5, gemini, qwen-vl, llava)" if need_vision else
                    "no brain available — add a key (`rad keys add <provider> <key>`), "
                    "start a local engine (Edge0/Ollama/LM Studio), or `rad provider add`")
            raise P.ProviderError(hint, retryable=False)
        errors: List[str] = []
        class_c_hits: List[P.ProviderError] = []
        free_lock = bool(self.home.cfg.get("free_lock"))
        for entry in chain:
            model = model_override or self.home.cfg.get("model") or entry.model
            if not model and entry.spec.local and entry.spec.name == "edge0":
                model = "edge0-" + (self.home.cfg.get("edge0_tier", "10b"))
            try:
                res = P.chat(entry.spec, entry.key, messages, model=model, tools=tools,
                             stream_cb=stream_cb, temperature=temperature,
                             max_tokens=max_tokens)
                self.preferred[entry.spec.tier] = entry.spec.name
                self.failures.pop(entry.spec.name, None)
                self._record_cost(entry, res)
                return res
            except P.ProviderError as e:
                kind = P.class_c_kind(e.status, e.msg)
                self.failures[entry.spec.name] = {
                    "err": e.msg, "status": e.status, "at": time.time(),
                    "class_c": bool(kind), "kind": kind,
                }
                if kind and self.preferred.get(entry.spec.tier) == entry.spec.name:
                    self.preferred.pop(entry.spec.tier, None)
                errors.append(f"{entry.spec.name}: {e.msg}")
                if kind:
                    class_c_hits.append(e)
                home_log = self.home
                home_log.log("router", f"FAIL {entry.spec.name} {e.status} {e.msg}")
                if kind or (not e.retryable and e.status in (401, 403, 429)):
                    if stream_cb is not None:
                        stream_cb("\n")
                    print(col.dim(f"  ⚠ {entry.spec.name} Class C ({e.msg}) — rotating free provider…"),
                          flush=True)
                    continue  # auth / quota / inference-forbidden — try next usable brain
                if stream_cb is not None:
                    stream_cb("\n")
                print(col.dim(f"  ⚠ {entry.spec.name} failed ({e.msg}) — falling back…"), flush=True)
                continue
            except Exception as e:  # unexpected → treat as retryable
                errors.append(f"{entry.spec.name}: {e}")
                continue
        if class_c_hits and len(class_c_hits) == len(errors):
            kinds = {P.class_c_kind(e.status, e.msg) for e in class_c_hits}
            kind = "rate_limit" if "rate_limit" in kinds else "auth"
            status = next((e.status for e in class_c_hits if e.status in P.CLASS_C_STATUSES), None)
            raise P.ProviderError(
                "all providers failed (Class C — not a product hole):\n  " + "\n  ".join(errors)
                + "\n" + P.class_c_next_steps(kind, free_lock=free_lock),
                status=status, retryable=False)
        raise P.ProviderError("all providers failed:\n  " + "\n  ".join(errors), retryable=False)

    def _record_cost(self, entry: ChainEntry, res: P.ChatResult) -> None:
        prices = P.spec_by_name.get(entry.spec.name, (0.0, 0.0))
        tin = res.usage.get("in", 0)
        tout = res.usage.get("out", 0)
        price = tin / 1000 * prices[0] + tout / 1000 * prices[1]
        if price > 0:
            self.home.add_cost(entry.spec.name, res.model, tin, tout, price)

    # ---------------------------------------------------------------- describe
    def describe(self) -> str:
        lines: List[str] = []
        for spec in P.all_specs(self.home):
            if spec.local:
                ok, models = P.probe_local(spec)
                if ok:
                    lines.append(f"  {col.green('●')} {spec.name:<10} local   {spec.desc}  {col.dim(', '.join(models[:4]))}")
                else:
                    lines.append(f"  {col.dim('○')} {spec.name:<10} local   {spec.desc}  {col.dim('(not running)')}")
                continue
            key = P.find_key(self.home, spec)
            if key:
                lines.append(f"  {col.green('●')} {spec.name:<10} {spec.tier:<5}  {spec.desc}")
            else:
                lines.append(f"  {col.dim('○')} {spec.name:<10} {spec.tier:<5}  {spec.desc}  {col.dim('(no key)')}")
        return "\n".join(lines)

    def cost_report(self) -> str:
        data = self.home.cost_data()
        if not data:
            return "  no paid usage recorded (you're on free/local)"
        out = []
        total = 0.0
        for day in sorted(data)[-14:]:
            for prov, cell in data[day].items():
                total += cell["cost"]
                out.append(f"  {day}  {prov:<10} {cell['in']:>8} in  {cell['out']:>8} out  ${cell['cost']:.4f}")
        out.append(col.bold(f"  total (last 14d): ${total:.4f}"))
        return "\n".join(out)
