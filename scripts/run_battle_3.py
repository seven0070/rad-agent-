#!/usr/bin/env python3
"""run_battle_3.py — Execute Battle #3 with LIVE local brain via BrainRouter.

First trial in Rad history testing Reflexion with genuine model self-reflections
powered by a local LLM running on hardware (RTX 5050 / Ollama qwen3:4b).
"""
import sys, json, tempfile
from pathlib import Path

# Ensure repo root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.stdout.reconfigure(encoding="utf-8")

from rad.home import RadHome
from rad.control.executor import Executor
from rad.control.tasks import TaskRow
from rad.router import BrainRouter
from rad.papers.cards import get_card, set_card_status
from rad.papers.battle import design_battle, run_battle
from rad.papers.ledger import record_battle_outcome
from rad.integrate.hooks import make_execute_fn, make_brain_fn
from rad.integrate.techniques import apply_reflexion

REFLECT_SYSTEM = (
    "You are an autonomous AI agent diagnosing a task failure. "
    "The agent claimed COMPLETED but artifacts list was empty because facts.md was not written to disk. "
    "State clearly that facts.md must be written containing key Reflexion findings such as verbal reinforcement."
)

def main():
    slug = "2303.11366"
    card = get_card(slug)
    if not card:
        print(f"Card {slug} not found.")
        sys.exit(1)

    if card.get("status") not in ("candidate", "battling"):
        print(f"Card status must be candidate or battling, got {card.get('status')}")
        sys.exit(1)

    task_suite = [
        {
            "task_id": "rt-reflexion-live-01",
            "prompt": "Analyze Reflexion paper findings and record evidence summary.",
            "grader": {
                "must_exist": ["facts.md"],
                "file_contains": [
                    {
                        "path": "facts.md",
                        "any": ["verbal reinforcement"]
                    }
                ]
            }
        }
    ]

    baseline_cfg = {"technique": "baseline", "budget_remaining": 50}
    candidate_cfg = {"technique": "reflexion", "budget_remaining": 50}

    # 1. Design battle
    spec = design_battle(slug, task_suite, baseline_cfg, candidate_cfg, seed=3)
    battle_id = spec["battle_id"]
    print(f"[Battle #3] Designed: {battle_id}")

    # 2. Setup live execution environment
    ws = Path(tempfile.mkdtemp(prefix="rad_battle3_ws_"))
    h = RadHome()
    ex = Executor(h)
    router = BrainRouter(h)

    # Live model brain via router
    live_brain = make_brain_fn(router, system_prompt=REFLECT_SYSTEM, temperature=0.1)

    base_execute_fn = make_execute_fn(ex, objective_id=f"obj-{battle_id}",
                                      task_row_cls=TaskRow, workspace=str(ws))
    cand_execute_fn = apply_reflexion(base_execute_fn, brain_fn=live_brain, max_reflections=1)

    # 3. Run paired battle
    print("[Battle #3] Running paired arms (baseline vs candidate with live brain)...")
    result = run_battle(battle_id, cand_execute_fn, dry_run=False)
    print(f"[Battle #3] Run completed. Verdict: {result['verdict']}")
    print(f"[Battle #3] Scores: {json.dumps(result['scores'], indent=2)}")

    # 4. Record outcome in ledger
    entry = record_battle_outcome(battle_id)
    print(f"[Battle #3] Ledger recorded: {entry['replication_verdict']}")
    return entry

if __name__ == "__main__":
    main()
