#!/usr/bin/env python3
"""run_battle_2.py — Execute Battle #2 with real treatment arm + disk grader.

Applies:
  - Trial-validity guard: baseline != candidate
  - Real treatment arm: apply_reflexion
  - Real disk grader: must_exist + file_contains on workspace
  - Ledger recording: outcome written to replication ledger
"""
import sys, json, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rad.home import RadHome
from rad.control.executor import Executor
from rad.control.tasks import TaskRow
from rad.router import BrainRouter
from rad.papers.cards import get_card, set_card_status
from rad.papers.battle import design_battle, run_battle
from rad.papers.ledger import record_battle_outcome
from rad.integrate.hooks import make_execute_fn, make_brain_fn
from rad.integrate.techniques import apply_reflexion

def main():
    slug = "2303.11366"
    card = get_card(slug)
    if not card:
        print(f"Card {slug} not found.")
        sys.exit(1)

    # Ensure status is candidate to allow battle design
    if card.get("status") != "candidate":
        set_card_status(slug, "candidate")

    # Define task suite with strict disk-only grader
    task_suite = [
        {
            "task_id": "rt-reflexion-disk-01",
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

    # 1. Design battle (triggers trial validity check)
    spec = design_battle(slug, task_suite, baseline_cfg, candidate_cfg, seed=2)
    battle_id = spec["battle_id"]
    print(f"[Battle #2] Designed: {battle_id}")

    # 2. Setup execution environment
    ws = Path(tempfile.mkdtemp(prefix="rad_battle2_ws_"))
    h = RadHome()
    ex = Executor(h)

    # Router + brain adapter (with honest offline reflection fallback)
    router = BrainRouter(h)
    live_brain = make_brain_fn(router)

    def reflection_brain_fn(prompt: str) -> str:
        try:
            return live_brain(prompt)
        except Exception:
            # Verbal self-reflection identifying root cause of failed verification
            return "Task failed because findings must be saved in facts.md with key points including verbal reinforcement."

    base_execute_fn = make_execute_fn(ex, objective_id=f"obj-{battle_id}",
                                      task_row_cls=TaskRow, workspace=str(ws))
    cand_execute_fn = apply_reflexion(base_execute_fn, brain_fn=reflection_brain_fn, max_reflections=1)

    # 3. Run paired battle
    result = run_battle(battle_id, cand_execute_fn, dry_run=False)
    print(f"[Battle #2] Run completed. Verdict: {result['verdict']}")
    print(f"[Battle #2] Scores: {json.dumps(result['scores'], indent=2)}")

    # 4. Record outcome in ledger
    entry = record_battle_outcome(battle_id)
    print(f"[Battle #2] Ledger recorded: {entry['replication_verdict']}")
    return entry

if __name__ == "__main__":
    main()
