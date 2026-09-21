#!/usr/bin/env python3
"""Offline verification of the contribution pack. No network, no keys.
    python scripts/verify_contrib.py    (exit 1 on any FAIL)"""
import json, math, sys, tempfile, traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RESULTS = []
CHECKS = []

def check(name):
    def deco(fn):
        def run():
            try:
                fn(); RESULTS.append((name, "PASS", ""))
            except Exception as e:
                RESULTS.append((name, "FAIL", str(e))); traceback.print_exc()
        run._is_check = True
        CHECKS.append(run)
        return run
    return deco

@check("papers.ingest: html->text, arxiv regex, slug")
def check_ingest():
    from rad.papers import ingest as ing
    assert ing._html_to_text("<p>hello &amp; bye</p>").strip() == "hello & bye"
    assert ing.ARXIV_RE.search("https://arxiv.org/abs/2501.12948v2").group(1) == "2501.12948"
    assert ing._slug_from_url("https://arxiv.org/abs/2501.12948") == "2501.12948"

def _mk_paper(tmp, slug="t1", text="quote here"):
    from rad.papers import ingest as ing
    ing.PAPERS_DIR = tmp
    d = tmp / slug; d.mkdir(parents=True, exist_ok=True)
    (d / "paper.md").write_text(text, encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(
        {"slug": slug, "title": "T", "source_url": "u", "sha256": "deadbeef"}), encoding="utf-8")

@check("papers.cards: quote verify (true/bogus), illegal transition")
def check_cards():
    from rad.papers import ingest as ing, cards as cds
    tmp = Path(tempfile.mkdtemp()); ing.PAPERS_DIR = tmp; cds.PAPERS_DIR = tmp
    _mk_paper(tmp, text="Reflexion improves task success by 22 percent via verbal feedback.")
    cds.create_card("t1", "technique",
        claims=[{"claim": "improves", "evidence_quote": "improves task success by 22 percent",
                 "claimed_gain": "+22%"}], mechanism="m", implementation_surface=["x"])
    c2 = cds.create_card("t1", "technique",
        claims=[{"claim": "bogus", "evidence_quote": "this quote is not in the paper at all xyz",
                 "claimed_gain": ""}], mechanism="m", implementation_surface=["x"])
    assert c2["claims"][0]["quote_verified"] is False
    try:
        cds.set_card_status("t1", "promoted"); raise AssertionError("should raise")
    except ValueError: pass

@check("papers.battle+ledger: paired run, verdict, CONFIRMED, export")
def check_battle():
    from rad.papers import ingest as ing, cards as cds, battle as btl, ledger as ldg
    tmp = Path(tempfile.mkdtemp())
    for m in (ing, cds): m.PAPERS_DIR = tmp
    btl.PAPERS_DIR = tmp; btl.BATTLE_DIR = tmp / "_battles"
    ldg.PAPERS_DIR = tmp; ldg.BATTLE_DIR = tmp / "_battles"; ldg.LEDGER_FILE = tmp / "_ledger.jsonl"
    _mk_paper(tmp)
    cds.create_card("t1", "technique",
        claims=[{"claim": "c", "evidence_quote": "quote here", "claimed_gain": "+10%"}],
        mechanism="m", implementation_surface=["x"],
        battle_plan={"baseline": "current", "suite": "realworld",
                     "metrics": ["verified_rate"], "note": "test"})
    cds.set_card_status("t1", "candidate")
    spec = btl.design_battle("t1", [{"task_id": "a", "prompt": "p", "grader": {}}],
                             {"k": 1}, {"k": 2}, seed=42)
    res = btl.run_battle(spec["battle_id"],
        lambda cfg, task, seed: {"grader_result": {
            "verified_rate": 0.9 if cfg["k"] == 2 else 0.7}, "events": ["e"]},
        dry_run=False)
    assert res["verdict"] == "candidate_wins", res["verdict"]
    entry = ldg.record_battle_outcome(spec["battle_id"])
    assert entry["replication_verdict"] == "CONFIRMED", entry["replication_verdict"]
    assert "rad-replication-ledger" in ldg.export_ledger()

@check("papers.extract: brain extraction with verified quotes")
def check_extract():
    from rad.papers import ingest as ing, cards as cds, extract as ext
    tmp1 = Path(tempfile.mkdtemp())
    for m in (ing, cds, ext): m.PAPERS_DIR = tmp1
    _mk_paper(tmp1, slug="t2", text="Verbal reflection boosts agent accuracy substantially.")
    good = json.dumps({"card_type": "technique",
        "claims": [{"claim": "reflection helps", "claimed_gain": "+10%",
                    "evidence_quote": "Verbal reflection boosts agent accuracy substantially."}],
        "mechanism": "self-critique then retry",
        "implementation_surface": ["executor:retry-policy"], "coi_flags": []})
    card = ext.extract_card_brain("t2", brain_fn=lambda p: good)
    assert card["claims"][0]["quote_verified"] is True
    tmp2 = Path(tempfile.mkdtemp())
    for m in (ing, cds, ext): m.PAPERS_DIR = tmp2
    _mk_paper(tmp2, slug="t3", text="Verbal reflection boosts agent accuracy substantially.")
    bad_fn = lambda p: json.dumps({"card_type": "technique", "claims": [
        {"claim": "x", "claimed_gain": "", "evidence_quote": "short"}],
        "mechanism": "m", "implementation_surface": [], "coi_flags": []})
    try:
        ext.extract_card_brain("t3", brain_fn=bad_fn); raise AssertionError("should raise")
    except ext.ExtractionError: pass

@check("memory.strength: formula, decay order, sleep archives-never-deletes")
def check_strength():
    from rad.memory import strength as st
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    fresh = {"origin": "user", "verification": "verified", "layer": "semantic",
             "recall_count": 2, "last_used_at": now.isoformat()}
    # strength() rounds to 4 decimals, so use 1e-4 tolerance
    expected = round(1.0 * (1 + 0.1 * math.log1p(2)), 4)
    assert st.strength(fresh, now) == expected, f"{st.strength(fresh, now)} != {expected}"
    old = dict(fresh, last_used_at="2026-06-20T00:00:00+00:00")
    assert st.strength(old, now) < st.strength(fresh, now)
    e = dict(old, layer="episodic")
    assert st.strength(e, now) < st.strength(old, now)
    mroot = Path(tempfile.mkdtemp()); (mroot / "long" / "semantic").mkdir(parents=True)
    weak = {"origin": "model_generated", "verification": "contradicted", "layer": "semantic",
            "recall_count": 0, "created_at": "2025-01-01T00:00:00+00:00"}
    (mroot / "long" / "semantic" / "w.json").write_text(json.dumps(weak))
    (mroot / "long" / "semantic" / "s.json").write_text(json.dumps(fresh))
    rep = st.sleep(mroot, now=now)
    assert rep["archived"] == 1 and (mroot / "archive" / "w.json").exists()
    assert not (mroot / "long" / "semantic" / "w.json").exists()
    assert (mroot / "long" / "semantic" / "s.json").exists()

def main():
    print("\n=== VERIFICATION (offline, no keys) ===")
    for c in CHECKS:
        c()
    fails = sum(1 for _, s, _ in RESULTS if s == "FAIL")
    for name, s, err in RESULTS:
        print(f"  {'PASS' if s == 'PASS' else 'FAIL'}  {name}" + (f"  -- {err[:90]}" if err else ""))
    print(f"\n{len(RESULTS)-fails}/{len(RESULTS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
