"""v3.3 Agent N — Performance recall latency <200ms P95 via sqlite-vss HNSW tuning, lab-gated."""
import time
import tempfile
import pathlib


def _tmp_home():
    from rad.home import RadHome
    tmp = pathlib.Path(tempfile.mkdtemp()) / ".rad"
    return RadHome(str(tmp))


def test_hnsw_tuning_exists():
    from rad.memory.vss import HNSW_TUNING, hnsw_config, explain_hnsw, SQLITE_VSS_DDL
    assert HNSW_TUNING["M"] == 16
    assert HNSW_TUNING["ef_search"] == 64
    assert HNSW_TUNING["space"] == "cosine"
    assert HNSW_TUNING["target_p95_ms"] == 200
    assert HNSW_TUNING["backend"] == "sqlite-vss"
    cfg = hnsw_config()
    assert cfg["M"] == 16
    assert "M=16" in explain_hnsw()
    assert "vss0" in SQLITE_VSS_DDL
    assert "cosine" in SQLITE_VSS_DDL


def test_memory_hnsw_tuning_exported():
    from rad.memory import HNSW_TUNING as MEM_TUNING
    assert MEM_TUNING["M"] == 16
    assert MEM_TUNING["target_p95_ms"] == 200


def test_recall_latency_p95_under_200ms_with_500_memories():
    from rad.memory import Memory
    from rad.memory.vss import benchmark_recall
    import uuid
    home = _tmp_home()
    mem = Memory(home)
    # create 500 memories — bypass jaccard dedupe by writing distinct files directly
    # each entry has a unique uuid token so jaccard <0.7 and all 500 are kept
    for i in range(500):
        uid = uuid.uuid4().hex[:6]
        text = f"perf memory {i} uniq-{uid} about project codename alpha and task {i % 10} performance tuning context {uid} lorem ipsum {i}"
        # use add with unique layer rotation to avoid dedupe, or write directly
        # write file directly for determinism
        entry_id = f"perf{i:03d}{uid}"
        p = mem.long_dir("semantic") / f"{entry_id}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        created = 1700000000 + i * 100
        p.write_text(f"---\nid: {entry_id}\nlayer: semantic\ncreated: {created}\nlast_used: {created}\nstrength: 1.000\ntags: []\norigin: USER_PROVIDED\nconfidence: 0.90\nsource: perf-test\nverification: VERIFIED\ncontradicts: []\nimportance: 0.50\nuses: 0\n---\n{text}", encoding="utf-8")
    mem._invalidate()
    assert len(mem.scan()) >= 500, f"expected 500, got {len(mem.scan())}"
    queries = [f"project codename alpha task {i % 10}" for i in range(20)]
    bench = benchmark_recall(home, queries, k=5, runs=30)
    assert bench["n"] >= 20
    assert bench["p95_ms"] < 200, f"P95 {bench['p95_ms']}ms exceeds 200ms — HNSW tuning failed: {bench}"
    assert bench["ok"] is True
    assert bench["hnsw"]["M"] == 16
    assert bench["target_p95_ms"] == 200


def test_recall_still_correct_after_tuning():
    from rad.memory import Memory
    home = _tmp_home()
    mem = Memory(home)
    mem.add("semantic", "the project codename is Nebula", origin="USER_PROVIDED", source="test")
    mem.add("semantic", "the deployment key is on the blue shelf", origin="USER_PROVIDED", source="test")
    hits = mem.recall("project codename", k=3)
    assert any("Nebula" in h.text for h in hits)
    hits2 = mem.recall("deployment key", k=3)
    assert any("blue shelf" in h.text for h in hits2)


def test_vss_health_lab_gated():
    from rad.memory.vss import tuned_health
    home = _tmp_home()
    h = tuned_health(home)
    assert h["memory_vss"] == "sqlite-vss HNSW tuned"
    assert h["hnsw"]["M"] == 16
    assert h["lab_gated"] is True
