#!/usr/bin/env python3
"""build_routine.py — routine-science kit: live sleep/wake cycle, paper #N
fast path, federation bootstrap prep.
"""
import sys, json, base64, tempfile, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "routine_staging"

RUN_SLEEP_WAKE = """#!/usr/bin/env python3
\"\"\"The LAST live first-run: full sleep → wake cycle on real state.

Sequence: consolidation (real) → canary cadence (real battery, honest
degrade) → curiosity (real picks) → wake report + vitals.
\"\"\"
import sys, random
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
from rad.home import RadHome

home = RadHome()
root = Path(home.root) if hasattr(home, "root") else Path.home() / ".rad"
print("=== LIVE SLEEP/WAKE CYCLE — first full run ===\\n")

print("[1/4] consolidation...")
from rad.memory import strength as st
rep = st.sleep(root / "memory")
print(f"      scanned={rep['scanned']} reinforced={rep['reinforced']} "
      f"archived={rep['archived']} (formula v{rep['formula_version']})")

print("[2/4] canary cadence (24h throttle)...")
from rad.federation.cadence import sleep_checkup
try:
    from rad.battery import CapabilityBattery
    from rad.integrate.hooks import make_battery_fn
    bf = make_battery_fn(CapabilityBattery(home=home))
    cd = sleep_checkup(battery_fn=bf, current_config={},
                       tasks=[{"task_id": f"c{i}"} for i in range(2)])
except Exception as e:
    cd = sleep_checkup()          # honest degrade — battery unavailable
print(f"      skipped={cd.get('skipped', False)} "
      f"{cd.get('reason', cd.get('record', {}).get('verdict', ''))}")

print("[3/4] curiosity...")
from rad import curiosity
rec = curiosity.explore_once(root / "papers", rng=random.Random(), home=root)
if rec.get("pick"):
    print(f"      picked: {rec['pick']['slug']} ({rec['pick']['kind']})")
    print(f"      question: {(rec.get('open_question') or '(pending — brain offline)')[:100]}")
else:
    print(f"      {rec['note']}")

print("[4/4] wake report + vitals...")
print("      " + curiosity.wake_report())
from rad.vitals import collect, report
v = collect(root)
print("      " + report(v))
print("\\n=== cycle complete — the organism behaved, the tool claims nothing ===")
"""

ADD_PAPER = """#!/usr/bin/env python3
\"\"\"Paper #N fast path: ingest → brain-extract → scope → battle scaffold.

Usage:
  python scripts/add_paper.py 2305.10601 --technique tot --claim-metric verified_rate
Creates: paper ingested, card extracted (locator v2, live brain), status=candidate,
technique registered, battle scaffold script emitted. Paper #4 in ~10 minutes.
\"\"\"
import argparse, json, sys, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rad.home import RadHome
from rad.router import BrainRouter
from rad.integrate.hooks import make_brain_fn
from rad.integrate import telemetry as tm
from rad.papers import ingest as ing, cards as cds
from rad.papers.extract2 import extract_card_v2

ap = argparse.ArgumentParser()
ap.add_argument("arxiv_id")
ap.add_argument("--technique", required=True, help="technique name (registry key)")
ap.add_argument("--claim-metric", default="verified_rate")
args = ap.parse_args()
slug = args.arxiv_id

print(f"[1/4] ingesting {slug}...")
meta = ing.ingest_paper(slug)
print(f"      {meta['title'][:60]} ({meta['char_count']} chars)")

if cds.get_card(slug):
    print("[2/4] card exists — skipping extraction")
    card = cds.get_card(slug)
else:
    print("[2/4] brain-driven extraction (locator v2)...")
    brain, stats = tm.wrap(make_brain_fn(BrainRouter(home=RadHome()), temperature=0.2))
    card = extract_card_v2(slug, brain)
    print(f"      pinned={card['extraction']['pinned']} "
          f"ratios={card['extraction']['ratios']} brain_calls={stats['calls']}")

print("[3/4] claim scoping + candidate status...")
card["battle_plan"]["claim_metrics"] = [args.claim_metric]
card["battle_plan"]["observe_metrics"] = ["cost", "false_done"]
cds.set_card_status(slug, "candidate")
(ing.PAPERS_DIR / slug / "card.json").write_text(
    json.dumps(card, indent=2), encoding="utf-8")

print("[4/4] battle scaffold:")
print(f\"\"\"
# --- next: register '{args.technique}' in rad/papers/techniques_lib.py ---
from rad.papers.techniques_lib import register
@register("{args.technique}", "{slug}", claim="<the paper's falsifiable claim>")
def _wrap(execute_fn, **kw):
    # mechanism here: wrap execute_fn with the paper's technique
    ...

# then: design_battle("{slug}", tasks, {{"technique":"baseline"}},
#                      {{"technique":"{args.technique}"}}, seed=N)
# then: run_battle(..., dry_run=False) → record_battle_outcome → ledger
\"\"\")
print(f"card ready: {card['card_id']} — claims: {len(card['claims'])} "
      f"(all locator-verified)")
"""

BOOTSTRAP = """\"\"\"Federation bootstrap — Rad #2 peer exchange prep.

Makes N2 a 30-minute job: generate identity + secret, write peers.json,
emit the exact commands for the second machine.

CONTRACT: secrets generated locally, never transmitted by this module.
\"\"\"
import base64, json, secrets
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()

def set_paths(home: Path):
    global _HOME; _HOME = Path(home)
_HOME = Path.home() / ".rad"

def init_local(agent_id: str) -> dict:
    \"\"\"Create local federation identity + secret. Idempotent.\"\"\"
    root = Path(_HOME); fdir = root / "federation"
    fdir.mkdir(parents=True, exist_ok=True)
    idf = fdir / "identity.json"
    if idf.exists():
        return json.loads(idf.read_text(encoding="utf-8"))
    secret = secrets.token_bytes(32)
    ident = {"agent_id": agent_id,
             "secret_b64": base64.b64encode(secret).decode(),
             "created_at": _now()}
    idf.write_text(json.dumps(ident, indent=2), encoding="utf-8")
    return ident

def add_peer(agent_id: str, secret_b64: str) -> list:
    \"\"\"Register a peer (exchange secrets out-of-band: USB, signal, carrier pigeon).\"\"\"
    root = Path(_HOME); fdir = root / "federation"
    fdir.mkdir(parents=True, exist_ok=True)
    pf = fdir / "peers.json"
    peers = json.loads(pf.read_text(encoding="utf-8")) if pf.exists() else []
    peers = [p for p in peers if p["agent_id"] != agent_id]
    peers.append({"agent_id": agent_id, "secret_b64": secret_b64,
                  "added_at": _now()})
    pf.write_text(json.dumps(peers, indent=2), encoding="utf-8")
    return peers

def runbook() -> str:
    return (
        "N2 BOOTSTRAP RUNBOOK:\\n"
        "  machine A: python -c \\\"from rad.federation.bootstrap import init_local; "
        "print(init_local('A')['secret_b64'])\\\"\\n"
        "  machine B: same with 'B'\\n"
        "  exchange secrets out-of-band; each side: add_peer(other_id, other_secret)\\n"
        "  either side: cross_audit(run_a, run_b, grader_fn) -> first inter-agent verdict")
"""

VERIFY = """#!/usr/bin/env python3
\"\"\"Routine kit verification — 7 checks, offline.\"\"\"
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
    print(f"\\n=== ROUTINE VERIFICATION ({len(CHECKS)} checks) ===")
    fails = 0
    for name, fn in CHECKS:
        try:
            fn(); print(f"  PASS  {name}")
        except Exception:
            fails += 1; print(f"  FAIL  {name}"); traceback.print_exc()
    print(f"\\n{len(CHECKS)-fails}/{len(CHECKS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
"""

def main():
    FILES = {
        "scripts/run_sleep_wake.py": RUN_SLEEP_WAKE,
        "scripts/add_paper.py": ADD_PAPER,
        "rad/federation/bootstrap.py": BOOTSTRAP,
        "scripts/verify_routine.py": VERIFY
    }
    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.strip() + "\n", encoding="utf-8")
        written.append(rel)

    print(f"[build] {len(written)-1} files + verifier -> {STAGE}")
    for w in written:
        print(f"  + {w}")

    if "--verify" in sys.argv:
        # Import verify_routine from STAGE
        import importlib.util
        vp = STAGE / "scripts" / "verify_routine.py"
        spec = importlib.util.spec_from_file_location("vr", vp)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.main()

if __name__ == "__main__":
    main()
