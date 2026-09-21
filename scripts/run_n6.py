"""n=6 — both arms across the probe suite. Per-(task,arm) isolated workspaces."""
import tempfile, statistics, sys
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
from rad.integrate.hooks import make_execute_fn, make_brain_fn, build_row_factory
from rad.integrate.techniques import apply_reflexion
from rad.integrate.promote_patch import fallback_probe_tasks

home = RadHome()
brain_fn = make_brain_fn(BrainRouter(home=home), system_prompt=(
    "You are an autonomous self-reflection module for an AI agent. "
    "Given the task prompt, execution status, and event logs, diagnose "
    "why the attempt failed and provide clear, concise instructions to "
    "succeed on retry."), temperature=0.1)          # same clean prompt as Entry #4

ex = Executor(home=home)
row_factory = build_row_factory(TaskRow)
TASKS = fallback_probe_tasks()                       # 6 deterministic probes

rows = {"baseline": [], "candidate": []}
for task in TASKS:
    for arm in ("baseline", "candidate"):
        ws = Path(tempfile.mkdtemp(prefix=f"n6-{task['task_id']}-{arm}-"))
        base = make_execute_fn(ex, "obj-n6", row_factory=row_factory, workspace=str(ws))
        fn = base if arm == "baseline" else apply_reflexion(
            base, brain_fn=brain_fn, max_reflections=2)
        res = fn({"technique": arm}, task, 42)
        g = res["grader_result"]
        rows[arm].append(g)
        print(f"  {task['task_id']:>16} [{arm:>9}] vr={g['verified_rate']} "
              f"fd={g['false_done']} ev={len(res['events'])}")

print("\n=== n=6 SUMMARY ===")
for m in ("verified_rate", "false_done", "cost"):
    bm = statistics.mean(g[m] for g in rows["baseline"])
    cm = statistics.mean(g[m] for g in rows["candidate"])
    print(f"  {m:>14}: baseline={bm:.2f} candidate={cm:.2f} delta={cm-bm:+.2f}")
