#!/usr/bin/env python3
"""Entry #7 — ReAct (2210.03629) Battle: Fully Forged Chain.
Card generated via extract2 + locator -> scoped -> battle -> ledger.
"""
import json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from rad.home import RadHome
from rad.router import BrainRouter
from rad.integrate.hooks import make_brain_fn
from rad.integrate import telemetry as tm
from rad.papers.cards import get_card, set_card_status
from rad.papers.battle import design_battle, run_battle
from rad.papers.techniques_lib import make_arm
from rad.papers.ledger import record_battle_outcome, read_ledger
from rad.control.executor import Executor

def main():
    slug = "2210.03629"
    card = get_card(slug)
    if not card:
        print(f"Error: No card for {slug}")
        sys.exit(1)

    print(f"Card loaded: {card['card_id']} (status: {card['status']})")
    if card.get("status") == "extracted":
        set_card_status(slug, "candidate")
        print("Card status set to candidate.")
    else:
        print(f"Card already status: {card.get('status')}")

    task_suite = [
        {
            "task_id": "task-react-facts",
            "prompt": "Write facts.md containing facts about ReAct.",
            "grader": {
                "file_exists": ["facts.md"],
                "content_contains": ["react", "reasoning and acting"]
            }
        }
    ]

    baseline_config = {"technique": "baseline", "model": "qwen3:4b"}
    candidate_config = {"technique": "react", "model": "qwen3:4b"}

    seed = 9
    spec = design_battle(slug, task_suite, baseline_config, candidate_config, seed=seed)
    battle_id = spec["battle_id"]
    print(f"Battle designed: {battle_id}")

    # Wrap brain for telemetry
    brain_fn, stats = tm.wrap(make_brain_fn(BrainRouter(home=RadHome()), temperature=0.1))
    executor_inst = Executor(home=RadHome())

    # Executor runner wrapper that routes techniques through techniques_lib
    def execute_arm_fn(config, task, seed_int):
        technique = config.get("technique", "baseline")
        tmp_dir = tempfile.mkdtemp(prefix=f"rad_battle7_{technique}_")
        ctx = {"workspace": tmp_dir}

        def raw_exec(cfg, tsk, s):
            obs = executor_inst.execute_task("b7", tsk, context=ctx)
            status_str = getattr(obs, "status", "COMPLETED")
            # Evaluate disk grader
            ws = Path(tmp_dir)
            facts_file = ws / "facts.md"
            exists = facts_file.exists()
            content = facts_file.read_text(encoding="utf-8").lower() if exists else ""
            has_needles = "react" in content and "reasoning and acting" in content
            
            v_rate = 1.0 if (exists and has_needles) else 0.0
            f_done = 1.0 if (status_str == "COMPLETED" and not exists) else 0.0
            
            events = []
            if not exists:
                events.append("disk_fail:exists:facts.md")
            elif not has_needles:
                events.append("disk_fail:content:needles")

            return {
                "status": status_str,
                "grader_result": {
                    "verified_rate": v_rate,
                    "false_done": f_done,
                    "cost": 0.0
                },
                "events": events,
                "workspace": tmp_dir
            }

        arm_fn = make_arm(raw_exec, technique=technique, brain_fn=brain_fn)
        return arm_fn(config, task, seed_int)

    print("Running battle live on local CUDA silicon...")
    result = run_battle(battle_id, execute_arm_fn, dry_run=False)

    # Attach brain telemetry to result
    tm.attach_to_result(result, stats)
    from rad.papers.battle import BATTLE_DIR
    (BATTLE_DIR / battle_id / "result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )

    print(f"Battle finished! Verdict: {result['verdict']}")
    print("Scores:", json.dumps(result['scores'], indent=2))

    # Record outcome in ledger
    entry = record_battle_outcome(battle_id)
    print("\n=== LEDGER ENTRY #7 RECORDED ===")
    print(json.dumps(entry, indent=2))
    print("\nBRAIN TELEMETRY:", json.dumps(dict(stats), indent=2))

if __name__ == "__main__":
    main()
