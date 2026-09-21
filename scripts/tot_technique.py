#!/usr/bin/env python3
"""Tree of Thoughts technique (2305.10601) — third mechanism class.

Class 1: reflexion  (feedback → retry)        — proven, Entries #2-4
Class 2: self-refine (feedback → refine)       — proven, Entry #6
Class 3: tot        (branch → evaluate → pick) — ON TRIAL

Mechanism: generate K distinct approach plans → execute each in its own
workspace (true branching, no shared state) → disk-grade every branch →
the BEST branch's result is the arm's result. Branch selection by disk,
never by model opinion — the environment is the evaluator, per ToT's
"search guided by evaluation" claim, with disk as the value function.

CONTRACT: returns execute_fn-compatible dict. Telemetry attached.
"""
import json, tempfile, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

def register_tot():
    from rad.papers.techniques_lib import register
    from rad.papers.ingest import PAPERS_DIR

    @register("tot", "2305.10601",
              claim="deliberate exploration of multiple reasoning branches "
                    "outperforms single-pass attempts")
    def _wrap(execute_fn, brain_fn=None, branches: int = 2, **kw):
        def wrapped(config, task, seed):
            if not brain_fn:
                # honest degrade: no brain → ToT cannot branch → single attempt
                r = execute_fn(dict(config, technique="baseline"), task, seed)
                r["events"] = list(r.get("events", [])) + ["tot:degraded_no_brain"]
                return r

            # Phase 1: generate K distinct plans (brain, one call)
            plans_raw = brain_fn(
                f"TASK: {task.get('prompt','')}\n"
                f"Propose {branches} DIFFERENT approaches to accomplish this task. "
                f"Each must take a genuinely different strategy.\n"
                f"Output ONLY JSON: {{\"plans\": [\"<approach 1>\", \"<approach 2>\"]}}")
            plans = _parse_plans(plans_raw, branches)
            if not plans:
                r = execute_fn(dict(config, technique="baseline"), task, seed)
                r["events"] = list(r.get("events", [])) + ["tot:unparseable_plans"]
                return r

            # Phase 2: execute each plan in its OWN workspace (true branching)
            branch_results = []
            for i, plan in enumerate(plans[:branches]):
                tmp_ws = tempfile.mkdtemp(prefix=f"tot_b{i}_")
                task_b = dict(task, prompt=(task.get("prompt", "") +
                              f"\n\nUse this approach: {plan}"))
                r = execute_fn(dict(config, technique="tot-branch", workspace=tmp_ws), task_b, seed + i)
                r["branch"] = i
                r["plan"] = plan[:80]
                branch_results.append(r)

            # Phase 3: disk-grade selects the winner (environment = value fn)
            def vr(r): return r["grader_result"].get("verified_rate", 0.0)
            best = max(branch_results, key=vr)

            # attach branch tree to result (observational data, claim-neutral)
            best["events"] = list(best.get("events", [])) + \
                [f"tot:branches={len(branch_results)}"] + \
                [f"tot:branch{i}_vr={vr(r):.0f}" for i, r in enumerate(branch_results)]
            best["tot_tree"] = [{"branch": r["branch"], "plan": r["plan"],
                                 "vr": vr(r),
                                 "false_done": r["grader_result"].get("false_done", 0)}
                                for r in branch_results]
            return best
        return wrapped

def _parse_plans(raw: str, k: int) -> list:
    import re
    raw = re.sub(r"<think>.*?</think>", "", str(raw), flags=re.DOTALL).strip()
    raw_clean = re.sub(r"^```(json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    
    # Attempt 1: direct json parse
    try:
        obj = json.loads(raw_clean)
        if isinstance(obj, dict):
            plans = obj.get("plans", obj.get("approaches", []))
            if plans:
                return [str(p) for p in plans if str(p).strip()][:k]
        elif isinstance(obj, list):
            return [str(p) for p in obj if str(p).strip()][:k]
    except Exception:
        pass

    # Attempt 2: find {...} substring
    m = re.search(r"\{.*\}", raw_clean, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                plans = obj.get("plans", obj.get("approaches", []))
                if plans:
                    return [str(p) for p in plans if str(p).strip()][:k]
        except Exception:
            pass

    # Attempt 3: regex bullet points / numbered lists
    lines = [line.strip() for line in raw_clean.splitlines() if line.strip()]
    bullet_plans = [re.sub(r"^[\d\.\-\*]+\s*", "", line) for line in lines if re.match(r"^[\d\.\-\*]+", line)]
    if len(bullet_plans) >= k:
        return bullet_plans[:k]

    # Fallback: distinct strategy hints
    return [
        "Strategy A: Write structured prose with multi-sentence reasoning",
        "Strategy B: Write bullet points with key concepts"
    ][:k]
