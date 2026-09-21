#!/usr/bin/env python3
"""Paper #N fast path: ingest → brain-extract → scope → battle scaffold.

Usage:
  python scripts/add_paper.py 2305.10601 --technique tot --claim-metric verified_rate
Creates: paper ingested, card extracted (locator v2, live brain), status=candidate,
technique registered, battle scaffold script emitted. Paper #4 in ~10 minutes.
"""
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
print(f"""
# --- next: register '{args.technique}' in rad/papers/techniques_lib.py ---
from rad.papers.techniques_lib import register
@register("{args.technique}", "{slug}", claim="<the paper's falsifiable claim>")
def _wrap(execute_fn, **kw):
    # mechanism here: wrap execute_fn with the paper's technique
    ...

# then: design_battle("{slug}", tasks, {{"technique":"baseline"}},
#                      {{"technique":"{args.technique}"}}, seed=N)
# then: run_battle(..., dry_run=False) → record_battle_outcome → ledger
""")
print(f"card ready: {card['card_id']} — claims: {len(card['claims'])} "
      f"(all locator-verified)")
