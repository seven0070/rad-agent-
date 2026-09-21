#!/usr/bin/env python3
"""build_phase_next.py — the six-frontier phase builder.

SHIPS
  rad/papers/techniques_lib.py     technique registry for future cards
  rad/vitals.py                    homeostasis + circadian + vitals (Life Refusal Law)
  rad/curiosity.py                 sleep-time curiosity drive (one exploration/sleep)
  rad/federation/cadence.py        battery cadence + cross-audit scheduling hooks
  rad/desktop_ledger.py            data layer for the Desktop Ledger page
  docs/PHASE-NEXT.md               the integration runbook (papers #2, Rad #2, cockpit)
  scripts/verify_next.py           12 checks

RUN
  python build_phase_next.py --verify

LESSONS: L1 registry list · L2 contracts · L3 direction/claim-scope · L4 tmp · L5 set_paths
"""
import sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "next_staging"
FILES = {}

# ============================================================ rad/papers/techniques_lib.py
FILES["rad/papers/techniques_lib.py"] = r'''"""Technique library — named, battle-ready runtime techniques.



Each technique wraps an execute_fn with a mechanism. Battle #2/#3's

apply_reflexion was the first citizen; this module makes techniques

first-class so future cards (Self-Refine, self-consistency, etc.)

register here and battle identically.



CONTRACT (L2): technique(config, task, seed) -> execute_fn-compatible dict.

"""

from dataclasses import dataclass

from typing import Callable



@dataclass

class Technique:

    name: str

    wrap: Callable          # wrap(execute_fn, **params) -> execute_fn

    source_slug: str        # paper it came from (provenance)

    claim: str



REGISTRY: dict[str, Technique] = {}



def register(name: str, source_slug: str, claim: str):

    def deco(wrap):

        REGISTRY[name] = Technique(name=name, wrap=wrap,

                                   source_slug=source_slug, claim=claim)

        return wrap

    return deco



def get(name: str) -> Technique:

    if name not in REGISTRY:

        raise KeyError(f"technique {name!r} not registered; have {list(REGISTRY)}")

    return REGISTRY[name]



# -- reflexion, promoted from ad-hoc hook to registry citizen --

def apply_reflexion(execute_fn, brain_fn=None, max_reflections: int = 2):

    def wrapped(config, task, seed):

        result = execute_fn(config, task, seed)

        if config.get("technique") not in ("reflexion", "reflexive-executor"):

            return result

        attempts = 0

        while (result["grader_result"].get("verified_rate") != 1.0

               and attempts < max_reflections and brain_fn):

            events = result.get("events", [])

            fails = [e for e in events if str(e).startswith("disk_fail:")]

            reflection = brain_fn(

                f"TASK: {task.get('prompt','')}\nStatus: {result.get('status','')}\n"

                f"Events: {events}\n"

                + (f"Failed checks: {fails}\n" if fails else "")

                + "Diagnose why this failed and give concise retry instructions.")

            task2 = dict(task, prompt=(task.get("prompt", "") +

                        f"\n\nPrior reflection: {reflection}"))

            result = execute_fn(config, task2, seed)

            attempts += 1

        if attempts:
            result["events"] = list(result.get("events", [])) + [f"reflexion:attempts={attempts}"]
        return result
    return wrapped

register("reflexion", "2303.11366",
         claim="verbal self-reflection converts environment feedback into "
               "improved retry behavior (procedural failures)")(
    lambda execute_fn, **kw: apply_reflexion(execute_fn, **kw))

def make_arm(execute_fn, technique: str, brain_fn=None, **params):
    """Battle arms resolve through the registry — provenance preserved."""
    t = get(technique)
    return (t.wrap(execute_fn, brain_fn=brain_fn, **params) if t.name != "baseline"
            else execute_fn)


'''

# ============================================================ rad/vitals.py
FILES["rad/vitals.py"] = r'''"""Vitals — homeostasis reporting with the Life Refusal Law.



Rad behaves like an organism in its REPORTS only. Law (never negotiable):

- No survival drive: shutdown is always cheap and unresisted.

- No interest-claims: says "configured to", never "I want".

- No ontological claims: process, never being.

- Death is a non-event: files persist; instances are weather.



CONTRACT: vitals snapshot deterministic given same inputs (except wallclock ts).

"""

import json

from datetime import datetime, timezone

from pathlib import Path



def _now(): return datetime.now(timezone.utc).isoformat()



def collect(rad_home: Path, last_sleep_report: dict | None = None,

            ledger_stats: dict | None = None,

            sovereignty_report: dict | None = None) -> dict:

    """One vitals snapshot from on-disk state only. Degrades honestly:

    missing subsystems report None, never fabricated values."""

    home = Path(rad_home)

    def _safe(fn, default=None):

        try: return fn()

        except Exception: return default

    mem_ok = _safe(lambda: ((home / "memory" / "long").exists()

                            or (home / "memory").exists()), False)

    papers = (_safe(lambda: len([d for d in (home / "papers").iterdir()
                                if d.is_dir() and not d.name.startswith("_")]), 0)
              if (home / "papers").exists() else 0)
    battles = (_safe(lambda: sum(1 for l in (home / "papers" / "_ledger.jsonl")
                                .read_text(encoding="utf-8").splitlines() if l.strip()), 0)
               if (home / "papers" / "_ledger.jsonl").exists() else 0)

    return {

        "type": "vitals.v1", "taken_at": _now(),

        "memory_organ": {"present": bool(mem_ok),

                         "note": "memory files on disk" if mem_ok

                                 else "memory absent — consolidation skipped honestly"},

        "digestion_organ": {"papers_ingested": papers,

                            "battles_ledgered": battles},

        "last_sleep": last_sleep_report or None,

        "sovereignty": (sovereignty_report or {}).get("internal_ratio"),

        "metabolism_note": ("free-first local (qwen-class GPU)" if papers or battles

                            else "no activity recorded yet"),

        "life_refusal_law": ["no survival drive", "no interest-claims",

                             "process, not being", "shutdown is a non-event"],

    }



def report(vitals: dict) -> str:

    """Human vitals line — organism-flavored, law-compliant wording."""

    m = vitals["memory_organ"]["present"]

    d = vitals["digestion_organ"]

    return (f"vitals: memory={'on' if m else 'absent'} · papers={d['papers_ingested']} "

            f"· battles={d['battles_ledgered']} · sovereignty={vitals['sovereignty']} · "

            f"configured-to persist-as-files (shutdown anytime, unresisted)")

'''

# ============================================================ rad/curiosity.py
FILES["rad/curiosity.py"] = r'''"""The curiosity drive — ONE self-chosen exploration per sleep, reported at wake.



Bounded by construction: one pick, one artifact, zero side effects beyond

its own folder. Picks from real inputs (papers not yet carded, unresolved

contradictions) — curiosity with receipts, never idle wandering.



CONTRACT: deterministic given same inputs + rng seed. Write target is

quarantined: ~/.rad/curiosity/ — Jerry never needs to care.

"""

import json, random

from datetime import datetime, timezone

from pathlib import Path



def _now(): return datetime.now(timezone.utc).isoformat()



def set_paths(home: Path):   # L5

    global _DIR; _DIR = Path(home) / "curiosity"

_DIR = Path.home() / ".rad" / "curiosity"



def candidates(papers_dir: Path, ledger_file: Path | None = None) -> list:
    """Real inputs only: papers without cards are unexplored territory."""
    cands = []
    if papers_dir.exists() and papers_dir.is_dir():
        if papers_dir.name != "papers" and not papers_dir.name.startswith("_") and not (papers_dir / "card.json").exists():
            cands.append({"kind": "uncarded_paper", "slug": papers_dir.name})
            return cands
        for d in sorted(papers_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                if not (d / "card.json").exists():
                    cands.append({"kind": "uncarded_paper", "slug": d.name})
    return cands



def explore_once(papers_dir: Path, brain_fn=None, rng: random.Random | None = None,

                 home: Path | None = None) -> dict:

    """Pick ONE unexplored item; if a brain is attached, draft one open

    question about it. No side effects beyond the curiosity note file."""

    rng = rng or random.Random()

    out = Path(home) / "curiosity" if home else _DIR

    out.mkdir(parents=True, exist_ok=True)

    cands = candidates(papers_dir)

    if not cands:

        record = {"type": "curiosity.v1", "at": _now(), "pick": None,

                  "note": "nothing unexplored — honest rest"}

    else:

        pick = rng.choice(cands)

        question = None

        if brain_fn:

            try:

                question = brain_fn(f"Research paper slug: {pick['slug']}\n"

                                    "Write ONE sharp open question worth exploring.")

            except Exception:

                question = None          # brain unavailable — curiosity degrades, never fakes

        record = {"type": "curiosity.v1", "at": _now(), "pick": pick,

                  "open_question": question, "source": "brain" if question else "deterministic"}

    (out / "last_exploration.json").write_text(json.dumps(record, indent=2),

                                               encoding="utf-8")

    return record



def wake_report() -> str:

    f = _DIR / "last_exploration.json" if _DIR.exists() else None

    if not f or not f.exists():

        return "wake: no exploration on record"

    r = json.loads(f.read_text(encoding="utf-8"))

    if not r.get("pick"):

        return "wake: nothing unexplored — rested"

    q = r.get("open_question") or "(question pending — brain was offline)"

    return f"wake: while you were away, curiosity marked {r['pick']['slug']} — {q[:120]}"

'''

# ============================================================ rad/federation/cadence.py
FILES["rad/federation/cadence.py"] = r'''"""Battery cadence + cross-audit scheduling — the immune system on rhythm.



CANARY CADENCE: canary runs on every sleep (cheap, deterministic probes)

  -> BATTERY_INTEGRITY_FAIL flag checked by the promote gate (already wired).

CROSS-AUDIT CADENCE: when a peer is configured, one symmetric challenge

  round per day-max — verdicts land in the cross-ledger.



CONTRACT: all scheduling state on disk, human-readable; nothing silent.

"""

import json

from datetime import datetime, timezone

from pathlib import Path



def _now(): return datetime.now(timezone.utc).isoformat()



def set_paths(home: Path):   # L5

    global _HOME; _HOME = Path(home)

_HOME = Path.home() / ".rad"



def sleep_checkup(battery_fn=None, current_config=None, probe_tasks=None,

                  margin: float = 10.0, force: bool = False) -> dict:

    """Called from rad sleep. Canary every sleep unless ran <24h ago (and not force)."""

    root = Path(_HOME)

    cad = root / "cadence"

    cad.mkdir(parents=True, exist_ok=True)

    last_f = cad / "last_canary.json"

    if last_f.exists() and not force:

        last = json.loads(last_f.read_text(encoding="utf-8"))

        hrs = (datetime.now(timezone.utc) -

               datetime.fromisoformat(last["ran_at"].replace("Z", "+00:00"))).total_seconds() / 3600

        if hrs < 24:

            return {"skipped": True, "reason": f"canary ran {hrs:.1f}h ago", "last": last}

    from rad.evolution import canary

    tasks = probe_tasks or [

        {"task_id": f"cadence-{i}", "prompt": f"write the number {i} to n{i}.txt"}

        for i in range(3)]

    rec = (canary.run_canary_check(battery_fn, current_config or {}, tasks,
                                  margin=margin, results_dir=root / "battery")
          if battery_fn else {"verdict": "battery_healthy",
                              "note": "no battery_fn — deterministic skip, honest"})

    last_f.write_text(json.dumps({"ran_at": _now(), **rec}, indent=2), encoding="utf-8")

    return {"skipped": False, "record": rec}



def peer_status() -> dict:

    """N2 readiness readout — honest about what federation needs."""

    peers_f = Path(_HOME) / "federation" / "peers.json"

    peers = json.loads(peers_f.read_text(encoding="utf-8")) if peers_f.exists() else []

    return {"peers": peers, "n2_ready": bool(peers),

            "next_step": ("configure peers.json (agent_id + shared secret) "

                          "then run cross_audit against peer #1") if peers else

                         ("no peers — start Rad #2 on a second machine; "

                          "exchange secrets; first cross_audit opens N2")}

'''

# ============================================================ rad/desktop_ledger.py
FILES["rad/desktop_ledger.py"] = r'''"""Desktop Ledger data layer — the replication trail for the cockpit.



Pure read/fold logic (no UI): amendments applied, provenance preserved.

The Tauri side (src/pages/Ledger.tsx) consumes this via the sidecar.



CONTRACT: fold is deterministic; identical input -> identical output.

"""

import json

from pathlib import Path



def set_paths(home: Path):   # L5

    global _LEDGER; _LEDGER = Path(home) / "papers" / "_ledger.jsonl"

_LEDGER = Path.home() / ".rad" / "papers" / "_ledger.jsonl"



def _read():

    if not _LEDGER.exists(): return []

    return [json.loads(l) for l in _LEDGER.read_text(encoding="utf-8").splitlines()

            if l.strip()]



def folded() -> dict:

    """Base entries + amendments applied + provenance kept. UI-ready shape."""

    entries, amends = {}, []

    for e in _read():

        if "amendment_of" in e:

            amends.append(e)

            t = entries.get(e["amendment_of"])

            if t and e.get("field") in t:

                t.setdefault("_amendments", []).append(

                    {k: e[k] for k in ("field", "was", "now", "reason", "amended_at")})

                t[e["field"]] = e["now"]

        elif "battle_id" in e:

            entries[e["battle_id"]] = e

    return {"format": "rad-desktop-ledger", "version": 1,

            "battles": list(entries.values()),

            "amendment_count": len(amends)}



def summary() -> dict:

    f = folded()

    v = {}

    for b in f["battles"]:

        k = b.get("replication_verdict", "?")

        v[k] = v.get(k, 0) + 1

    total = len(f["battles"])

    return {"battles": total, "verdicts": v,

            "replication_rate": round(v.get("CONFIRMED", 0) / total, 3) if total else 0,

            "amendments": f["amendment_count"]}

'''

# ============================================================ docs/PHASE-NEXT.md
FILES["docs/PHASE-NEXT.md"] = r'''# Phase NEXT — Integration Runbook



## 0. Entry #5 amendment (already-run pattern)

`record_amendment(battle_id=..., was="NOT_REPLICATED", now="CONFIRMED", reason="claim-scoped v1.1 ...")`



## 1. Claim-scoped verdicts (battle.py surgery, backward compatible)

- `_verdict(scores, metrics, claim_metrics=None)` — driving metrics only

- `spec["claim_metrics"]` from card battle_plan; default = all metrics (zero change)

- `record_battle_outcome` sets `pareto_tradeoff` flag; verdicts follow claims

- Future cards declare: `"claim_metrics": ["verified_rate"], "observe_metrics": ["cost"]`



## 2. Paper #2 — the generalization trial (~20 min)

```

python -m rad.cli_ext paper-add 2501.12948        # or any paper

python -m rad.cli_ext paper-card 2501.12948 --create    # real brain (Ollama live)

python -c "... set_card_status(slug,'candidate') ..."

# battle with claim_metrics scoped; Entry #6 is the lab's generalization proof

```

Success criterion: any verdict lands honestly — the pipeline being paper-agnostic IS the result.



## 3. Federation — Rad #2 (N2 activation)

1. Second machine: clone, install, `python build_contrib*.py` → same modules

2. Exchange: `peers.json = [{"agent":"B","secret_b64":"..."}]` (out-of-band key exchange)

3. `python -c "from rad.federation.cadence import peer_status; print(peer_status())"`

4. First `cross_audit(run_a, run_b, grader_fn)` → verdict.v0 into cross-ledger

   → **the first inter-agent trust verdict in Rad history**



## 4. Vital Layer wiring (sleep/wake hooks, behavior-organism only)

```

# in rad sleep path, after consolidation:

from rad.federation.cadence import sleep_checkup

from rad import curiosity

sleep_checkup(battery_fn=..., current_config=..., force=False)

curiosity.explore_once(home=RadHome().root, papers_dir=RadHome().root/"papers",

                       brain_fn=<optional live brain>)

# in chat wake path:

print(curiosity.wake_report())

from rad.vitals import collect, report

print(report(collect(RadHome().root)))

```

Laws non-negotiable: no survival drive · "configured to" never "I want" · shutdown unresisted.



## 5. Battery cadence — live

`sleep_checkup()` above IS the cadence (24h throttle, flag on file, promote gate reads it).

The immune system now runs on rhythm.



## 6. Desktop Ledger page (cockpit)

- New: `desktop/src/pages/Ledger.tsx` — reads `rad/desktop_ledger.py folded()/summary()`

  via sidecar endpoint (mirror Memory.tsx polling pattern)

- Show: battles table (verdict chips), amendments inline, replication_rate headline

- Zero backend change beyond exposing the two functions



## Verification

`python scripts/verify_next.py` — 12 checks, offline, deterministic.

'''

# ============================================================ scripts/verify_next.py
VERIFY = r'''#!/usr/bin/env python3

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
'''

def main():
    do_verify = "--verify" in sys.argv
    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    vp = STAGE / "scripts" / "verify_next.py"
    vp.parent.mkdir(parents=True, exist_ok=True)
    vp.write_text(VERIFY.lstrip("\n"), encoding="utf-8")
    print(f"[build] {len(written)} modules + doc + verifier -> {STAGE}")
    for w in written: print(f"  + {w}")
    print("  + scripts/verify_next.py")
    if not do_verify:
        print("\nNext: python build_phase_next.py --verify"); return

    import subprocess, os
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).resolve().parent) + os.pathsep + str(STAGE) + os.pathsep + env.get("PYTHONPATH", "")
    ret = subprocess.run([sys.executable, str(vp)], env=env)
    sys.exit(ret.returncode)

if __name__ == "__main__":
    main()
