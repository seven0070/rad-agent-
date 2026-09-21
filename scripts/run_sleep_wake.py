#!/usr/bin/env python3
"""The LAST live first-run: full sleep → wake cycle on real state.

Sequence: consolidation (real) → canary cadence (real battery, honest
degrade) → curiosity (real picks) → wake report + vitals.
"""
import sys, random
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8")
from rad.home import RadHome

home = RadHome()
root = Path(home.root) if hasattr(home, "root") else Path.home() / ".rad"
print("=== LIVE SLEEP/WAKE CYCLE — first full run ===\n")

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
print("\n=== cycle complete — the organism behaved, the tool claims nothing ===")
