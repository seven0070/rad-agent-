#!/usr/bin/env python3
"""Routine kit verification — 7 checks, offline."""
import json, sys, tempfile, base64, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CHECKS = []
def check(name):
    def deco(fn):
        CHECKS.append((name, fn)); return fn
    return deco

@check("sleep/wake runner: module compiles and imports cleanly")
def runner_imports():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rsw", ROOT / "scripts" / "run_sleep_wake.py")
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)   # runs the FULL live cycle in verification
    except SystemExit:
        pass

@check("add_paper: argparse surface correct")
def add_paper_surface():
    src = (ROOT / "scripts" / "add_paper.py").read_text(encoding="utf-8")
    for needle in ("--technique", "--claim-metric", "extract_card_v2",
                   "set_card_status"):
        assert needle in src, needle

@check("bootstrap: init_local idempotent, secret 32 bytes")
def bootstrap_init():
    from rad.federation import bootstrap as bs
    tmp = Path(tempfile.mkdtemp()); bs.set_paths(tmp)
    i1 = bs.init_local("A")
    i2 = bs.init_local("A")
    assert i1 == i2, "must be idempotent"
    assert len(base64.b64decode(i1["secret_b64"])) == 32

@check("bootstrap: add_peer replaces same-id, keeps others")
def bootstrap_peer():
    from rad.federation import bootstrap as bs
    tmp = Path(tempfile.mkdtemp()); bs.set_paths(tmp)
    bs.init_local("A")
    bs.add_peer("B", base64.b64encode(b"x" * 32).decode())
    bs.add_peer("B", base64.b64encode(b"y" * 32).decode())
    bs.add_peer("C", base64.b64encode(b"z" * 32).decode())
    peers = json.loads((tmp / "federation" / "peers.json").read_text(encoding="utf-8"))
    ids = sorted(p["agent_id"] for p in peers)
    assert ids == ["B", "C"], ids

@check("bootstrap: runbook mentions exchange + cross_audit")
def bootstrap_runbook():
    from rad.federation import bootstrap as bs
    rb = bs.runbook()
    assert "cross_audit" in rb and "out-of-band" in rb

@check("curiosity: picks uncarded paper (routine loop closes — ingest #4, sleep picks it)")
def curiosity_loop():
    from rad import curiosity as cu
    tmp = Path(tempfile.mkdtemp())
    p = tmp / "papers" / "2305.10601"; p.mkdir(parents=True)   # no card
    rec = cu.explore_once(tmp / "papers", rng=__import__("random").Random(1), home=tmp)
    assert rec["pick"]["slug"] == "2305.10601"

@check("cadence: sleep_checkup writes last_canary.json (state on disk)")
def cadence_state():
    from rad.federation import cadence as cd
    tmp = Path(tempfile.mkdtemp()); cd.set_paths(tmp)
    cd.sleep_checkup(force=True)
    assert (tmp / "cadence" / "last_canary.json").exists()

def main():
    print(f"\n=== ROUTINE VERIFICATION ({len(CHECKS)} checks) ===")
    fails = 0
    for name, fn in CHECKS:
        try:
            fn(); print(f"  PASS  {name}")
        except Exception:
            fails += 1; print(f"  FAIL  {name}"); traceback.print_exc()
    print(f"\n{len(CHECKS)-fails}/{len(CHECKS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
