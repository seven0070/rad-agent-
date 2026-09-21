#!/usr/bin/env python3
"""Battle #8 — ToT vs single-shot, 2-branch disk-graded trial. Entry #8."""
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rad.home import RadHome
from rad.control.executor import Executor
from rad.control.tasks import TaskRow
from rad.router import BrainRouter
from rad.integrate.hooks import make_execute_fn, make_brain_fn, build_row_factory
from rad.integrate import telemetry as tm
from rad.papers import battle as b, ledger as ldg
from tot_technique import register_tot

register_tot()

home = RadHome()
brain, stats = tm.wrap(make_brain_fn(BrainRouter(home=home), temperature=0.4))
ex = Executor(home=home)
row_factory = build_row_factory(TaskRow)

# Task with TWO viable strategies (branching must be meaningful, not trivial):
# strategy A: write structured prose; strategy B: write a formatted list.
TASK = {"task_id": "b8-tot-01",
        "prompt": "Record the key idea of the Tree of Thoughts paper into "
                  "insights.txt. The file must contain the word 'branching' "
                  "and at least two distinct sentences.",
        "grader": {"must_exist": ["insights.txt"],
                   "file_contains": [{"path": "insights.txt",
                                      "any": ["branching", "Tree of Thoughts"]}]}}

base = make_execute_fn(ex, objective_id="obj-b8", row_factory=row_factory)
brain_fn_reflector = make_brain_fn(BrainRouter(home=home), system_prompt=(
    "You are an autonomous self-reflection module. Given task, status and "
    "events, diagnose failure and give concise retry instructions."),
    temperature=0.2)

def runner(config, task, seed):
    if config["technique"] == "single-shot":
        return base(config, task, seed)
    from rad.papers.techniques_lib import get
    t = get("tot")
    wrapped = t.wrap(base, brain_fn=brain, branches=2)
    return wrapped(config, task, seed)

from rad.papers.cards import get_card, set_card_status
c = get_card("2305.10601")
if c and c.get("status") == "extracted":
    set_card_status("2305.10601", "candidate")

spec = b.design_battle("2305.10601", [TASK],
                       {"technique": "single-shot"},
                       {"technique": "tot"}, seed=13)
res = b.run_battle(spec["battle_id"], runner, dry_run=False)
print("VERDICT:", res["verdict"])
print(json.dumps(res["scores"], indent=2))
cand_r = res["candidate_results"][0]
print("TOT TREE:", json.dumps(cand_r.get("tot_tree", []), indent=2))
print("BRAIN:", json.dumps(dict(stats), indent=2))
entry = ldg.record_battle_outcome(spec["battle_id"])
print("LEDGER:", entry["replication_verdict"],
      "| pareto:", entry.get("pareto_tradeoff", False))
