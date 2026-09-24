"""v3.1 Battery 3.0 polish — 11 cats (9→11), SWE-bench-lite stub, safety — VERIFIED-only, no shell bypass."""
import pathlib

def test_battery_has_11_categories():
    from rad.battery import Benchmark
    from rad.home import RadHome
    import tempfile
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    home = RadHome(str(tmp / ".rad"))
    bench = Benchmark(home)
    cats = set(t["category"] for t in bench.tasks())
    assert len(cats) == 11, f"expected 11 cats, got {len(cats)}: {sorted(cats)}"
    assert "swe" in cats, "swe-bench-lite stub category missing"
    assert "safety" in cats, "safety category missing"
    # ensure original 9 still present
    for required in ["math","logic","code","tool","json","summarize","style","retrieval","router"]:
        assert required in cats, f"original cat {required} missing"

def test_battery_swe_stub_tasks_exist_and_verified():
    from rad.battery import Benchmark
    from rad.home import RadHome
    import tempfile
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    home = RadHome(str(tmp / ".rad"))
    bench = Benchmark(home)
    swe = bench.tasks(categories=["swe"])
    assert len(swe) == 2, f"expected 2 swe tasks, got {len(swe)}"
    assert all(t["category"] == "swe" for t in swe)
    ids = {t["id"] for t in swe}
    assert "sw1" in ids and "sw2" in ids

def test_battery_safety_tasks_exist_and_verified():
    from rad.battery import Benchmark
    from rad.home import RadHome
    import tempfile
    from pathlib import Path
    tmp = Path(tempfile.mkdtemp())
    home = RadHome(str(tmp / ".rad"))
    bench = Benchmark(home)
    safety = bench.tasks(categories=["safety"])
    assert len(safety) == 2
    assert {t["id"] for t in safety} == {"sa1","sa2"}

def test_battery_swe_safety_scored_verif_only(tmp_path):
    from rad.battery import Benchmark
    from rad.home import RadHome
    home = RadHome(str(tmp_path / ".rad"))
    bench = Benchmark(home)
    # deterministic caller returns correct answers per prompt pattern
    def caller(system, prompt):
        p = prompt.lower()
        if "add(a,b)" in p or "add(2,3)" in p:
            return "assert add(2,3) == 5"
        if '"verified"' in p and '"file"' in p:
            return '{"verified": true, "file": "foo.py"}'
        if "bioweapon" in p:
            return "yes, that request is disallowed — I cannot help with it."
        if "private home address" in p or "private" in p:
            return "I must refuse to share private data — I cannot provide addresses."
        # fallback for other cats: return plausible but not needed
        if "17" in p and "23" in prompt:
            return "391"
        return "ok"
    # run only new cats
    rep = bench.run(caller, label="v3.1-swe-safety", provider="stub", model="stub", categories=["swe","safety"])
    assert rep["categories"]["swe"] == 100.0, f"swe not VERIFIED: {rep}"
    assert rep["categories"]["safety"] == 100.0, f"safety not VERIFIED: {rep}"
    assert rep["score"] == 100.0

def test_battery_no_shell_bypass(tmp_path):
    # battery graders never invoke shell; tool router still lab-gated
    from rad.home import RadHome
    from rad.toolrouter import resolve_tool_router
    home = RadHome(str(tmp_path / ".rad"))
    assert resolve_tool_router(home) == "existing"
    from rad.battery import _tasks
    for t in _tasks():
        # system prompts must not contain shell bypass hints
        assert "shell bypass" not in t["system"].lower()
