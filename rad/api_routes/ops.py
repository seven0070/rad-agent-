"""Observability / ops routes: lab, evolution, agents, events, world, tools, benchmarks."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from rad.api_security import ApiError


class OpsMixin:
    """GET /lab/history, /evolve/candidates, /agents, /events, /world, /tools, /benchmarks."""

    def _route_ops(self, m: str, p: list, q: Dict[str, str], b: Dict[str, Any]
                   ) -> Optional[Tuple[int, Any]]:
        if p == ["lab", "history"] and m == "GET":
            from rad.lab import Lab
            return 200, {"runs": [{k: v for k, v in r.items() if k != "results"} for r in Lab(self.home).history(int(q.get("n", 20) or 20))]}
        if p == ["evolve", "candidates"] and m == "GET":
            from rad.evolution import Evolution
            return 200, {"candidates": [c.to_dict() for c in Evolution(self.home).candidates(int(q.get("n", 20) or 20))]}
        if p == ["agents"] and m == "GET":
            from rad.agents import AgentLifecycle, AgentRegistry
            reg = AgentRegistry(self.home)
            lc = AgentLifecycle(self.home)
            return 200, {"agents": [a.to_dict() for a in reg.all().values()],
                         "states": {s["id"]: s.get("state") for s in lc.all()},
                         "runs": reg.runs(n=int(q.get("n", 20) or 20))}
        if p == ["events"] and m == "GET":
            from rad.control.events import read_global
            evs = read_global(self.home, n=int(q.get("n", 200) or 200), kind=q.get("kind") or None)
            rows = [e.__dict__ for e in evs]
            oid = q.get("objective") or ""
            if oid:
                rows = [r for r in rows if r.get("objective_id") == oid]
            return 200, {"events": rows, "n": len(rows), "stream": "~/.rad/events.jsonl"}
        if p == ["world"] and m == "GET":
            from rad.world import WorldModel
            w = WorldModel(self.home)
            term = q.get("q", "")
            if term:
                return 200, {"matches": w.query(term, include_history=q.get("history") == "1")}
            d = w.data()
            return 200, {"entities": d.get("entities", {}) if isinstance(d.get("entities"), dict)
                         else d.get("entities", []),
                         "relations": w.current_relations(d),
                         "disputes": w.disputes(),
                         "counts": {"entities": len(d.get("entities") or {}),
                                    "relations": len(d.get("relations") or [])}}
        if p == ["tools"] and m == "GET":
            from rad.agents import cap_for_tool
            from rad.policy import Policy
            from rad.tools import TOOLS
            pol = Policy(self.home)
            tools = []
            for t in TOOLS:
                fn = t.get("function", t)
                cap = cap_for_tool(fn.get("name", ""))
                tools.append({"name": fn.get("name"), "capability": cap,
                              "policy": pol.default_for(cap),
                              "description": (fn.get("description") or "")[:160]})
            return 200, {"tools": tools}
        if p == ["providers", "health"] and m == "GET":
            from rad.providers import provider_health_snapshot
            return 200, {"providers": provider_health_snapshot(self.home), "mode": "observability_only", "routing": "free-first unchanged"}
        # ---- Observability SSE (T4 hardening) ----
        # GET /v1/events/stream  -> Server-Sent Events stub (observability-only, loopback, bearer-gated)
        # Real SSE is served by make_server._do when Accept: text/event-stream; this Api stub is for
        # direct handler tests (no streaming transport) and keeps P0 observability unchanged.
        if p == ["events", "stream"] and m == "GET":
            # SSE observability: stream of global events as event: lines. Stub returns metadata.
            return 200, {
                "sse": True,
                "endpoint": "/v1/events/stream",
                "mode": "observability_only",
                "content_type": "text/event-stream",
                "note": "SSE observability stub — real stream is HTTP event-stream when Accept: text/event-stream",
                "events_stream": "~/.rad/events.jsonl",
                "observability": "provider_health + ledger + events",
            }
        if p == ["observability", "stream"] and m == "GET":
            return 200, {
                "sse": True,
                "endpoint": "/v1/observability/stream",
                "mode": "observability_only",
                "content_type": "text/event-stream",
                "sources": ["events", "provider_health", "ledger"],
            }
        if p == ["skills", "search"] and m == "GET":
            # P0 marketplace search read-only (observability): filter connected skills by q, no install
            query = (q.get("q") or q.get("query") or "").lower().strip()
            from rad.skills import audit as skills_audit
            # read-only: audit returns already-connected skills; treat as marketplace catalog stub
            catalog = skills_audit(self.home)
            # stub catalog when empty (observability demo)
            if not catalog:
                catalog = [{"name": "demo-skill", "approval": "ask", "trust": "local", "capabilities": ["fs.read"], "tools": 1, "flags": []}]
            if query:
                filtered = [c for c in catalog if query in c.get("name","").lower() or query in " ".join(c.get("capabilities",[])).lower()]
            else:
                filtered = catalog
            return 200, {"query": query, "results": filtered[:20], "total": len(filtered), "mode": "read_only", "install": "disabled_in_P0"}
        if p == ["benchmarks"] and m == "GET":
            from rad import lab_banks
            from rad.battery import Benchmark
            from rad.evaluation import ModelEvaluator
            from rad.lab import Lab
            out: Dict[str, Any] = {"banks": lab_banks.counts()}
            try:
                out["lab"] = [{k: v for k, v in r.items() if k != "results"} for r in Lab(self.home).history(10)]
            except Exception as e:
                out["lab"] = {"error": str(e)[:80]}
            try:
                out["battery"] = [{k: v for k, v in r.items() if k != "tasks"}
                                  for r in Benchmark(self.home).history()[-10:]]
            except Exception as e:
                out["battery"] = {"error": str(e)[:80]}
            ev = ModelEvaluator(self.home)
            latest = ev.latest()
            out["evaluation"] = ({k: v for k, v in latest.items() if k != "tasks"} if latest else None)
            try:
                from rad.longhorizon import LongHorizonBenchmark
                lh = LongHorizonBenchmark(self.home).latest()
                out["long_horizon"] = lh or None
            except Exception as e:
                out["long_horizon"] = {"error": str(e)[:80]}
            return 200, out
        return None
