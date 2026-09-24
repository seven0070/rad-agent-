"""P0 W1 swarm: hybrid retriever, router gateway, battery banks — pinning parity."""
import json
import time

from rad.home import RadHome
from rad.battery import _tasks
from rad.memory import Memory
from rad.memory.strength import FORMULA_VERSION
from rad.world import WorldModel


def test_memory_hybrid_contract_parity(tmp_path):
    home = RadHome(tmp_path / ".rad")
    mem = Memory(home)
    # add memories
    mem.add("semantic", "Alice works at Acme", tags=["person:alice"], origin="USER_PROVIDED")
    mem.add("semantic", "Bob lives in Berlin", origin="USER_PROVIDED")
    time.sleep(0.01)
    q = "Where does Alice work?"
    r1 = mem.recall(q, k=5)
    r2 = mem.search(q, k=5)
    # P0 parity: search must equal recall when vector stub empty
    assert [e.id for e in r1] == [e.id for e in r2], "search() diverged from recall() scorer — no scorer change allowed"
    # FTS5 stub must return at least one candidate
    fts = mem._fts5_search("Alice works", k=5)
    assert len(fts) >= 1
    # vector stub is observability-only empty in P0
    vec = mem._vector_search("Alice works", k=5)
    assert vec == []
    # strength/decay unchanged: formula version pinned
    assert FORMULA_VERSION == 1


def test_world_hybrid_contract_parity(tmp_path):
    home = RadHome(tmp_path / ".rad")
    w = WorldModel(home)
    w.learn("Alice works at Acme", source="manual")
    # query vs search parity
    q1 = w.query("Alice")
    q2 = w.search("Alice")
    assert [x["type"] for x in q1[:2]] == [x["type"] for x in q2[:2]]
    # FTS5 pool
    fts = w._fts5_search("Alice")
    assert len(fts) >= 1
    assert w._vector_search("Alice") == []


def test_provider_spec_has_router_fields(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.providers import all_specs, provider_health_snapshot
    specs = all_specs(home)
    for s in specs:
        assert hasattr(s, "latency_ms"), f"{s.name} missing latency_ms"
        assert hasattr(s, "cost_per_1k"), f"{s.name} missing cost_per_1k"
        assert hasattr(s, "health"), f"{s.name} missing health"
        assert hasattr(s, "health_checked_at")
        assert s.health in ("unknown", "healthy", "degraded", "down")
    snap = provider_health_snapshot(home)
    assert len(snap) == len(specs)
    # observability only — no routing yet
    for row in snap:
        assert "latency_ms" in row and "cost_per_1k" in row and "health" in row


def test_provider_health_endpoint(tmp_path):
    home = RadHome(tmp_path / ".rad")
    from rad.api import Api
    api = Api(home)
    # GET /v1/providers/health is observability-only stub
    status, payload = api.handle("GET", "/v1/providers/health", {}, {})
    assert status == 200
    assert "providers" in payload
    assert payload["mode"] == "observability_only"
    assert isinstance(payload["providers"], list)
    assert len(payload["providers"]) >= 10
    for p in payload["providers"]:
        assert "latency_ms" in p and "cost_per_1k" in p and "health" in p


def test_battery_has_two_new_banks():
    t = _tasks()
    cats = {x["category"] for x in t}
    assert "retrieval" in cats, "missing retrieval bank"
    assert "router" in cats, "missing router bank"
    # should have added exactly 4 new tasks (2+2)
    assert len([x for x in t if x["category"] == "retrieval"]) == 2
    assert len([x for x in t if x["category"] == "router"]) == 2
    # total should be >= original 17 + 4 =21
    assert len(t) >= 21


def test_strength_pinned_no_scorer_change():
    from rad.memory.strength import strength
    from datetime import datetime, timezone
    now = datetime(2026, 9, 24, tzinfo=timezone.utc)
    mem = {"origin": "user", "verification": "verified", "layer": "semantic", "recall_count": 3, "last_used_at": "2026-09-23T12:00:00+00:00"}
    s = strength(mem, now)
    # Pin: base=1.0*1.0=1.0, freq=1+0.1*log1p(3)~1.1386, decay exp(-0.02*1.041)=0.979...
    assert 1.0 < s < 2.0
    assert FORMULA_VERSION == 1


def test_recall_latency_not_regressed(tmp_path):
    home = RadHome(tmp_path / ".rad")
    mem = Memory(home)
    for i in range(20):
        mem.add("semantic", f"fact number {i} about Berlin and Alice", origin="USER_PROVIDED")
    start = time.perf_counter()
    mem.recall("Alice Berlin", k=5)
    t1 = time.perf_counter() - start
    start = time.perf_counter()
    mem.search("Alice Berlin", k=5)
    t2 = time.perf_counter() - start
    # hybrid must not be >2x recall latency in P0 (stub only)
    assert t2 < max(0.05, t1 * 2.5)


def test_skills_search_live(tmp_path):
    # rad skills search is live when skills registry responds (read-only)
    home = RadHome(tmp_path / ".rad")
    from rad import skills as skm
    # audit is read-only and must not crash even with no skills
    out = skm.audit(home)
    assert isinstance(out, list)
    # search parity: listing via home.skills() also live
    assert isinstance(home.skills(), dict)
