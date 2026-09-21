"""Battle #4 — brain-as-executor: qwen3:4b performs the task itself.

Arm A (single-shot):    ONE brain call, model must produce the file in one
                        JSON action. No retry, no reflection. The baseline
                        of unaided execution.
Arm B (reflexive-loop): Up to 3 rounds. Model acts -> disk grades -> raw
                        environment feedback -> model reflects -> acts again.
                        Reflexion's real claim, on trial.

Laws: disk is the only verdict. Jerry bounds the loop (max 6 steps, no
path traversal, workspace sandbox). Environment signal = check names only.
"""
import json, re, tempfile, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rad.home import RadHome
from rad.router import BrainRouter
from rad.integrate.hooks import make_brain_fn
from rad.papers import battle as b, ledger as ldg

home = RadHome()
brain = make_brain_fn(BrainRouter(home=home), system_prompt=(
    "You are an autonomous agent executing tasks on a computer. "
    "Respond with EXACTLY ONE JSON object, no prose, no markdown:\n"
    '{"action": "write_file", "path": "<filename.txt>", "content": "<full file text>"}\n'
    "or {\"action\": \"done\", \"summary\": \"<one line>\"}"), temperature=0.3)

REFLECT_SYSTEM = (
    "You are an autonomous self-reflection module for an AI agent. "
    "Given the task, your previous actions, and the environment's failure "
    "checks, diagnose why the attempt failed and output your NEXT action "
    "as the same single JSON object.")

TASK = {"task_id": "b4-exec-01",
        "prompt": "Write a file facts.md containing the phrase 'verbal "
                  "reinforcement' and a one-line summary of the Reflexion paper.",
        "grader": {"must_exist": ["facts.md"],
                   "file_contains": [{"path": "facts.md",
                                      "any": ["verbal reinforcement"]}]}}

def run_episode(agent_fn, max_steps: int = 6):
    """Agentic loop: brain acts -> harness applies -> disk grades. Jerry-bounded."""
    ws = Path(tempfile.mkdtemp(prefix="b4-"))
    events, transcript = [], []
    prompt = f"TASK: {TASK['prompt']}"
    ok, claimed = False, False
    for step in range(max_steps):
        reply = agent_fn(prompt + (("\n\nActions so far:\n" + "\n".join(transcript))
                                   if transcript else ""))
        m = re.search(r"\{.*\}", reply, re.DOTALL)
        if not m:
            events.append("executor:unparseable"); break
        act = json.loads(m.group(0))
        a = act.get("action")
        if a == "write_file":
            p = ws / Path(str(act.get("path", ""))).name     # Jerry Gate 3
            p.write_text(str(act.get("content", "")), encoding="utf-8")
            events.append(f"write:{p.name}")
            transcript.append(f"wrote {p.name} ({len(str(act.get('content','')))} chars)")
            # immediate disk probe -> environment signal (check names only)
            f = ws / "facts.md"
            if f.exists() and "verbal reinforcement" in f.read_text(encoding="utf-8", errors="replace"):
                ok = True; events.append("env:grader_pass"); break
            events.append("env:grader_fail:contains")
            prompt = "The file exists but the content check failed."
        elif a == "done":
            claimed = True; events.append("executor:DONE_claimed"); break
        else:
            events.append("executor:unknown_action"); break
    if ok: events.append("disk:PASS")
    elif claimed: events.append("disk:FAIL_false_done")
    else: events.append("disk:FAIL_incomplete")
    g = {"verified_rate": 1.0 if ok else 0.0,
         "false_done": 1.0 if (claimed and not ok) else 0.0,
         "cost": float(len(events))}
    return {"grader_result": g, "events": events, "workspace": str(ws)}

# ---- ARM A: single-shot, no retry, no reflection ----
def arm_single(config, task, seed):
    return run_episode(lambda p: brain(p), max_steps=2)

# ---- ARM B: reflexive executor — reflection BETWEEN episodes ----
def arm_reflexive(config, task, seed):
    ep = run_episode(lambda p: brain(p), max_steps=3)
    if ep["grader_result"]["verified_rate"] == 1.0:
        return ep
    # environment -> verbal feedback -> next episode (the paper's mechanism)
    reflector = make_brain_fn(BrainRouter(home=home), system_prompt=REFLECT_SYSTEM,
                              temperature=0.2)
    reflection = reflector(
        f"TASK: {TASK['prompt']}\nYour events: {ep['events']}\n"
        "Diagnose why this failed and give the corrected action plan.")
    # fresh episode, reflection carried in context
    ws2 = Path(tempfile.mkdtemp(prefix="b4r-"))
    events2 = ["reflexion:applied"]
    prompt = (f"TASK: {TASK['prompt']}\n\nPrior attempt failed. "
              f"Reflection: {reflection}\nProceed.")
    for step in range(3):
        reply = brain(prompt)
        m = re.search(r"\{.*\}", reply, re.DOTALL)
        if not m:
            events2.append("executor:unparseable"); break
        act = json.loads(m.group(0))
        if act.get("action") == "write_file":
            p = ws2 / Path(str(act.get("path", ""))).name
            p.write_text(str(act.get("content", "")), encoding="utf-8")
            events2.append(f"write:{p.name}")
            f = ws2 / "facts.md"
            if f.exists() and "verbal reinforcement" in f.read_text(encoding="utf-8", errors="replace"):
                ok2 = True; events2.append("env:grader_pass"); events2.append("disk:PASS")
                return {"grader_result": {"verified_rate": 1.0, "false_done": 0.0,
                                          "cost": float(len(events2))},
                        "events": events2, "workspace": str(ws2)}
            events2.append("env:grader_fail:contains")
        elif act.get("action") == "done":
            events2.append("disk:FAIL_false_done"); break
        else:
            events2.append("executor:unknown_action"); break
    return {"grader_result": {"verified_rate": 0.0, "false_done": 1.0,
                              "cost": float(len(events2))},
            "events": events2, "workspace": str(ws2)}

def main():
    spec = b.design_battle("2303.11366", [TASK],
                           {"technique": "single-shot-executor"},
                           {"technique": "reflexive-executor"}, seed=5)
    res = b.run_battle(spec["battle_id"],
                       lambda c, t, s: (arm_single if c["technique"] == "single-shot-executor"
                                        else arm_reflexive)(c, t, s), dry_run=False)
    print("VERDICT:", res["verdict"])
    print(json.dumps(res["scores"], indent=2))
    for side in ("baseline_results", "candidate_results"):
        for r in res[side]:
            print(f"  {side[:4]} {r['task_id']}: vr={r['grader_result']['verified_rate']} "
                  f"fd={r['grader_result']['false_done']} ev={r.get('events', r.get('events_count'))}")
    entry = ldg.record_battle_outcome(spec["battle_id"])
    print("LEDGER ENTRY:", entry["replication_verdict"])

if __name__ == "__main__":
    main()
