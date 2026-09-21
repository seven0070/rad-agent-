#!/usr/bin/env python3
"""run_battle_6_self_refine.py — Execute Battle #6 (Self-Refine generalization trial).

Tests Self-Refine (2303.17651) with LIVE local brain via BrainRouter.
Demonstrates:
  1. Second paper replication (generalization beyond Reflexion).
  2. Techniques library registry resolution (rad.papers.techniques_lib.make_arm).
  3. Claim-scoped evaluation (verified_rate drives verdict; cost observed honestly).
  4. Append-only ledger recording with pareto_tradeoff and claim_metrics.
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
from rad.papers.ledger import record_battle_outcome, export_ledger
from rad.integrate.hooks import make_execute_fn, make_brain_fn
from rad.papers.techniques_lib import make_arm

REFINE_SYSTEM = (
    "You are an autonomous iterative self-refinement module for an AI agent (Self-Refine, Madaan et al. 2023). "
    "Given the task prompt, execution status, and prior output, diagnose why the attempt failed "
    "and provide clear, concise instructions to refine the output and fulfill all task requirements."
)

def main():
    slug = "2303.17651"
    card = get_card(slug)
    if not card:
        print(f"[err] Card {slug} not found.")
        sys.exit(1)

    if card.get("status") not in ("candidate", "battling"):
        print(f"[err] Card status must be candidate or battling, got {card.get('status')}")
        sys.exit(1)

    task_suite = [
        {
            "task_id": "sr-self-refine-live-01",
            "prompt": "Analyze Self-Refine paper findings and record evidence summary using iterative refinement to produce facts.md.",
            "grader": {
                "must_exist": ["facts.md"],
                "file_contains": [
                    {
                        "path": "facts.md",
                        "any": ["iterative refinement", "self-feedback"]
                    }
                ]
            }
        }
    ]

    baseline_cfg = {"technique": "baseline", "budget_remaining": 50}
    candidate_cfg = {"technique": "self-refine", "budget_remaining": 50}

    # 1. Design battle
    seed = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 7
    spec = design_battle(slug, task_suite, baseline_cfg, candidate_cfg, seed=seed)
    battle_id = spec["battle_id"]
    print(f"[Battle #6] Designed: {battle_id} (seed={seed})")
    print(f"[Battle #6] Claim metrics: {spec.get('claim_metrics')}")
    print(f"[Battle #6] Metrics: {spec.get('metrics')}")

    # 2. Setup live execution environment
    ws = Path(tempfile.mkdtemp(prefix="rad_battle6_ws_"))
    h = RadHome()
    ex = Executor(h)
    router = BrainRouter(h)

    # Live model brain via router (Ollama qwen3:4b on GPU)
    live_brain = make_brain_fn(router, system_prompt=REFINE_SYSTEM, temperature=0.1)

    base_execute_fn = make_execute_fn(ex, objective_id=f"obj-{battle_id}",
                                      task_row_cls=TaskRow, workspace=str(ws))
    cand_execute_fn = make_arm(base_execute_fn, "self-refine", brain_fn=live_brain, max_reflections=1)

    # 3. Run paired battle
    print("[Battle #6] Running paired arms (baseline vs candidate via techniques_lib)...")
    result = run_battle(battle_id, cand_execute_fn, dry_run=False)
    print(f"[Battle #6] Run completed. Verdict: {result['verdict']}")
    print(f"[Battle #6] Pareto tradeoff: {result.get('pareto_tradeoff')}")
    print(f"[Battle #6] Scores: {json.dumps(result['scores'], indent=2)}")

    # 4. Record outcome in ledger
    entry = record_battle_outcome(battle_id)
    print(f"[Battle #6] Ledger recorded: {entry['replication_verdict']}")
    print(f"[Battle #6] Battle ID: {entry['battle_id']}")

    # 5. Export ledger
    export_path = ROOT / "ledger_export.json"
    export_ledger(export_path)
    print(f"[Battle #6] Exported ledger to {export_path}")
    return entry

if __name__ == "__main__":
    main()
