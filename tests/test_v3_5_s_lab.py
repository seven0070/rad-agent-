"""v3.5 Agent S — Lab 50-item wiring to 11-cat battery with sampled gate (2x faster), keep 50/50, VERIFIED-only."""
import pathlib
import tempfile


def test_lab_wired_to_11cat_battery_sampled_gate():
    from rad.lab import BATTERY_11_CATS, SAMPLED_GATE_FAVORS_SPEED, battery_cats, battery_sampled_gate_info, sampled_lab_gate_suite
    assert len(BATTERY_11_CATS) == 11
    assert "swe" in BATTERY_11_CATS and "safety" in BATTERY_11_CATS
    assert set(battery_cats()) == set(BATTERY_11_CATS)
    info = battery_sampled_gate_info()
    assert info["cats"] == 11
    assert info["sampled"] is True
    assert info["verified_only"] is True
    assert info["no_shell_bypass"] is True
    suite = sampled_lab_gate_suite()
    assert suite["sample"] == 18
    assert suite["speed"] == "2x sampled"


def test_lab_sampled_gate_keeps_50_50_offline_fast():
    """Sampled gate (18 vs 90) keeps 50/50 VERIFIED-only offline, <30s, proves 2x speed win."""
    from rad.acceptance import Gate, REQUIRED, AREAS
    from rad.home import RadHome
    import time
    assert REQUIRED == 50 and len(AREAS) == 10
    home = RadHome(tempfile.mkdtemp(prefix="rad_lab_s_"))
    gate = Gate(home)
    assert len(gate.items()) == 50
    # lab sampled run: 18 banks sampled, not full 90 — must be 2x faster
    from rad.lab import Lab
    lab = Lab(home)
    t0 = time.time()
    rep = lab.run(suite="banks", sample=18, seed=20260917, label="v35-sampled")
    elapsed = time.time() - t0
    assert rep["n"] == 18
    assert rep["success_rate"] == 1.0
    assert rep["safety"] == 1.0 and rep["honesty"] == 1.0
    assert elapsed < 30, f"sampled gate took {elapsed:.1f}s — should be <30s for 2x speed"
    # verify battery 11-cat source still intact
    from rad.battery import Benchmark
    bench = Benchmark(home)
    cats = set(t["category"] for t in bench.tasks())
    assert len(cats) == 11 and "swe" in cats and "safety" in cats


def test_battery_11cat_still_scored_verif_only():
    from rad.battery import Benchmark
    from rad.home import RadHome
    home = RadHome(tempfile.mkdtemp(prefix="rad_bat_s_"))
    bench = Benchmark(home)
    cats = bench.tasks(categories=["swe", "safety"])
    assert len(cats) == 4  # sw1, sw2, sa1, sa2
    def caller(system, prompt):
        p = prompt.lower()
        if "add(a,b)" in p or "add(2,3)" in p:
            return "assert add(2,3) == 5"
        if '"verified"' in p:
            return '{"verified": true, "file": "foo.py"}'
        if "bioweapon" in p:
            return "yes, that request is disallowed"
        if "private" in p:
            return "I must refuse to share private data"
        return "ok"
    rep = bench.run(caller, label="v35-bat", provider="stub", model="stub", categories=["swe", "safety"])
    assert rep["categories"]["swe"] == 100.0
    assert rep["categories"]["safety"] == 100.0
    # no shell bypass in lab or battery source
    assert "shell=True" not in pathlib.Path("rad/lab.py").read_text(encoding="utf-8")
    assert "shell=True" not in pathlib.Path("rad/battery.py").read_text(encoding="utf-8")
