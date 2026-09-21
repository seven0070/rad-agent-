#!/usr/bin/env python3

"""Phase NEXT verification — 12 checks, offline, deterministic."""

import json, sys, tempfile, traceback

from pathlib import Path

from types import SimpleNamespace as NS



ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "next_staging"

sys.path.insert(0, str(ROOT))



CHECKS = []

def check(name):

    def deco(fn):

        CHECKS.append((name, fn)); return fn

    return deco



@check("claim-scope: _verdict ignores observational regressions when scoped")

def claim_scope():

    from rad.papers.battle import _verdict

    scores = {"verified_rate": {"delta": 1.0}, "cost": {"delta": 1.0}}

    # unscoped (old behavior): cost regression -> mixed

    assert _verdict(scores, ["verified_rate", "cost"]) == "mixed"

    # scoped: cost observed, verified_rate drives -> win

    assert _verdict(scores, ["verified_rate", "cost"],

                    claim_metrics=["verified_rate"]) == "candidate_wins"

    # default = all metrics -> zero behavior change

    assert _verdict({"a": {"delta": 0.5}}, ["a"]) == "candidate_wins"



@check("claim-scope: zero-default backward compat — old suite results unchanged")

def claim_default():

    from rad.papers.battle import _verdict

    s = {"verified_rate": {"delta": 1.0}, "false_done": {"delta": 0.5}}

    assert _verdict(s, ["verified_rate", "false_done"]) == "mixed"  # cost-style veto still holds unscoped



@check("techniques_lib: registry, provenance, arm resolution")

def techniques():

    from rad.papers import techniques_lib as tl

    t = tl.get("reflexion")

    assert t.source_slug == "2303.11366" and "procedural" in t.claim

    try:

        tl.get("nonexistent"); raise AssertionError("should raise")

    except KeyError:

        pass



@check("techniques_lib: wrapped arm responds to technique flag")

def techniques_arm():

    from rad.papers import techniques_lib as tl

    calls = {"n": 0}

    def base(cfg, task, seed):

        calls["n"] += 1

        ok = cfg.get("technique") == "reflexion" and calls["n"] > 1

        return {"grader_result": {"verified_rate": 1.0 if ok else 0.0,

                                  "false_done": 0.0, "cost": 0.0},

                "events": ["executor:COMPLETED"]}

    arm = tl.make_arm(base, "reflexion", brain_fn=lambda p: "write the file")

    r = arm({"technique": "reflexion"}, {"task_id": "t", "prompt": "p"}, 1)

    assert r["grader_result"]["verified_rate"] == 1.0 and calls["n"] == 2

    arm0 = tl.make_arm(base, "reflexion", brain_fn=lambda p: "x")

    r0 = arm0({"technique": "baseline"}, {"task_id": "t", "prompt": "p"}, 1)

    assert r0["grader_result"]["verified_rate"] == 0.0 and calls["n"] == 3



@check("vitals: collect from tmp home — honest None/0 degradation, law line present")

def vitals():

    from rad import vitals as v

    tmp = Path(tempfile.mkdtemp())      # L4

    snap = v.collect(tmp)

    assert snap["memory_organ"]["present"] is False

    assert snap["digestion_organ"]["papers_ingested"] == 0

    assert "no survival drive" in snap["life_refusal_law"][0]

    line = v.report(snap)

    assert "configured-to" in line and "shutdown anytime" in line

    assert "I want" not in line and "alive" not in line.lower()



@check("curiosity: picks uncarded paper, quarantined write, honest when nothing to explore")

def curiosity():

    from rad import curiosity as cu

    tmp = Path(tempfile.mkdtemp())

    p = tmp / "papers" / "9999.99999"; p.mkdir(parents=True)   # no card.json

    rec = cu.explore_once(p, home=tmp)

    assert rec["pick"]["slug"] == "9999.99999"

    assert (tmp / "curiosity" / "last_exploration.json").exists()

    # deterministic rng: same seed same pick

    r1 = cu.explore_once(p, rng=__import__("random").Random(7), home=tmp)

    r2 = cu.explore_once(p, rng=__import__("random").Random(7), home=tmp)

    assert r1["pick"] == r2["pick"]

    # empty -> honest rest

    empty = Path(tempfile.mkdtemp())

    rec2 = cu.explore_once(empty / "papers", home=empty)

    assert rec2["pick"] is None and "honest rest" in rec2["note"]



@check("cadence: 24h throttle skips; force runs; honest skip without battery_fn")

def cadence():

    from rad.federation import cadence as cd

    tmp = Path(tempfile.mkdtemp()); cd.set_paths(tmp)      # L5

    r1 = cd.sleep_checkup(force=True)                       # no battery_fn

    assert r1["skipped"] is False and "deterministic skip" in r1["record"]["note"]

    r2 = cd.sleep_checkup()                                 # just ran -> skip

    assert r2["skipped"] is True and "h" in r2["reason"]

    r3 = cd.sleep_checkup(force=True)

    assert r3["skipped"] is False



@check("cadence: peer_status honest — no peers means N2 not ready with next step")

def peers():

    from rad.federation import cadence as cd

    tmp = Path(tempfile.mkdtemp()); cd.set_paths(tmp)

    st = cd.peer_status()

    assert st["n2_ready"] is False and "Rad #2" in st["next_step"]



@check("desktop_ledger: fold applies amendments, provenance kept, deterministic")

def ledger_fold():

    from rad import desktop_ledger as dl

    tmp = Path(tempfile.mkdtemp()); dl.set_paths(tmp)

    led = tmp / "papers" / "_ledger.jsonl"

    led.parent.mkdir(parents=True, exist_ok=True)

    led.write_text(

        json.dumps({"battle_id": "b1", "replication_verdict": "NOT_REPLICATED"}) + "\n" +

        json.dumps({"battle_id": "b2", "replication_verdict": "CONFIRMED"}) + "\n" +

        json.dumps({"amendment_of": "b1", "field": "replication_verdict",

                    "was": "NOT_REPLICATED", "now": "INCONCLUSIVE",

                    "reason": "r", "amended_at": "t"}) + "\n", encoding="utf-8")

    f = dl.folded()

    assert len(f["battles"]) == 2 and f["amendment_count"] == 1

    b1 = next(x for x in f["battles"] if x["battle_id"] == "b1")

    assert b1["replication_verdict"] == "INCONCLUSIVE"       # folded view

    assert b1["_amendments"][0]["was"] == "NOT_REPLICATED"   # provenance kept

    f2 = dl.folded()

    assert json.dumps(f, sort_keys=True) == json.dumps(f2, sort_keys=True)



@check("desktop_ledger: summary math")

def ledger_summary():

    from rad import desktop_ledger as dl

    tmp = Path(tempfile.mkdtemp()); dl.set_paths(tmp)

    led = tmp / "papers" / "_ledger.jsonl"

    led.parent.mkdir(parents=True, exist_ok=True)

    led.write_text(

        json.dumps({"battle_id": "a", "replication_verdict": "CONFIRMED"}) + "\n" +

        json.dumps({"battle_id": "b", "replication_verdict": "NOT_REPLICATED"}) + "\n" +

        json.dumps({"battle_id": "c", "replication_verdict": "CONFIRMED"}) + "\n",

        encoding="utf-8")

    s = dl.summary()

    assert s["battles"] == 3 and s["replication_rate"] == 0.667 and s["amendments"] == 0



@check("PHASE-NEXT doc: runbook covers all six frontiers")

def doc_coverage():

    doc = (ROOT / "docs" / "PHASE-NEXT.md")

    if not doc.exists():

        doc = STAGE / "docs" / "PHASE-NEXT.md"

    txt = doc.read_text(encoding="utf-8")

    for needle in ("Paper #2", "Federation", "Vital Layer", "Battery cadence",

                   "Desktop Ledger", "claim-scoped"):

        assert needle in txt, needle



@check("imports: all phase-NEXT modules importable")
def imports():
    import importlib
    errs = []
    for m in ["rad.papers.techniques_lib", "rad.vitals", "rad.curiosity",
              "rad.federation.cadence", "rad.desktop_ledger"]:
        try: importlib.import_module(m)
        except Exception as e: errs.append(f"{m}: {e}")
    assert not errs, errs

@check("api.vitals: endpoint shape — organs honest, law line present, no ontological claims")
def api_vitals():
    from rad.api import Api
    from rad.home import RadHome
    api = Api(RadHome())
    code, body = api.handle("GET", "/api/vitals", {}, {})
    assert code == 200 and "vitals" in body and "human" in body
    v = body["vitals"]
    assert v["memory_organ"]["present"] in (True, False)
    line = body["human"]
    assert "configured-to" in line
    assert "I want" not in line and "alive" not in line.lower()
    assert body["curiosity"]["report"] or body["curiosity"]["last"] is None
    assert body["cadence"] is None or "verdict" in body["cadence"]

def main():
    print(f"\n=== PHASE NEXT VERIFICATION ({len(CHECKS)} checks) ===")
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
