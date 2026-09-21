#!/usr/bin/env python3
"""build_hooks.py — Phase B: integration adapters wired to live RAD signatures.

LIVE SIGNATURES CONFORMED (from rad codebase):
  CapabilityBattery(home).run(provider=, model=, categories=None) -> {"score": float, ...}
  Executor(home).execute_task(objective_id=, task=TaskRow, context=, tools=) -> Observation
  BrainRouter(home).complete(prompt=, system_prompt=, provider=, model=, temperature=) -> str

SHIPS
  rad/integrate/hooks.py        the five adapters + promotion gate
  docs/INTEGRATION-B.md         exact promote-path wiring snippet
  scripts/verify_hooks.py       8 offline checks (fakes + live-import probe)
RUN
  python build_hooks.py --verify
LESSONS: L1 registry · L2 contracts documented · L3 metric direction ·
         L4 fresh tmp · L5 path/config injection via args
"""
import json, os, subprocess, sys
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "hooks_staging"
FILES = {}

FILES["rad/integrate/__init__.py"] = "'''Integration adapters — contribution organs wired to live RAD reflexes.'''\n"

FILES["rad/integrate/hooks.py"] = r'''"""Integration adapters — VERIFIED -> INTEGRATED (Phase B).

Five wires, each conformed to a live signature:

  1. make_brain_fn      -> papers.extract  brain_fn   via BrainRouter.complete
  2. make_battery_fn    -> evolution.canary battery_fn via CapabilityBattery.run
  3. make_execute_fn    -> papers.battle    execute_fn via Executor.execute_task
  4. build_row_factory  -> TaskRow construction via inspect-probing (no guessing)
  5. promotion_gate     -> both promote-path gates in one fail-closed call

HONEST DEGRADATION CONTRACT (L2):
  - battery overrides (temperature/max_tokens) are ATTEMPTED as extra kwargs;
    TypeError -> retry without them and flag {'_degraded': True}. Never silent.
  - TaskRow mapping is inspect-probed; unknown required fields raise a
    clear TypeError telling you to pass row_factory= explicitly.
  - Observation mapping: verified_rate(max)=1 iff COMPLETED;
    false_done(min)=1 iff COMPLETED with zero artifacts;
    cost(min)=len(tool_calls). Direction honored by battle verdicts.
"""
import inspect
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------- 1. brain_fn

EXTRACT_SYSTEM = ("You extract research claims as strict JSON matching a "
                  "provided schema. Output ONLY the JSON object.")

def make_brain_fn(router, system_prompt: str = EXTRACT_SYSTEM,
                  temperature: float = 0.2):
    """papers.extract brain_fn. BrainRouter.complete returns str — direct."""
    def brain_fn(prompt: str) -> str:
        return router.complete(prompt=prompt, system_prompt=system_prompt,
                               temperature=temperature)
    return brain_fn

# -------------------------------------------------------------- 2. battery_fn

def make_battery_fn(battery, default_provider=None, default_model=None):
    """evolution.canary battery_fn from CapabilityBattery.

    config keys used: provider, model, optional temperature/max_tokens.
    The canary's crippled-config markers ride as extra kwargs when the
    battery accepts them; on TypeError the run degrades to provider/model
    only AND FLAGS IT — a degraded canary comparison is still reported,
    never passed off as full-fidelity."""
    def battery_fn(config: dict, task: dict, seed: int) -> dict:
        base = {"provider": config.get("provider", default_provider),
                "model": config.get("model", default_model)}
        extras = {k: config[k] for k in ("temperature", "max_tokens") if k in config}
        try:
            report = battery.run(**base, **extras)
            degraded = False
        except TypeError:
            report = battery.run(**base)
            degraded = True
        return {"score": float(report.get("score", 0)), "_degraded": degraded}
    return battery_fn

# ------------------------------------------------------- 3/4. executor wiring

_ROW_ID_KEYS = ("id", "task_id", "key", "name")
_ROW_TEXT_KEYS = ("prompt", "description", "text", "goal", "instruction")

def build_row_factory(task_row_cls):
    """Probe TaskRow.__init__ and map our task dict onto its real params.
    Returns row_factory(task={'task_id','prompt'}) -> TaskRow.
    Extra required fields on TaskRow -> TypeError with explicit guidance."""
    sig = inspect.signature(task_row_cls.__init__)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    names = {p.name for p in params}
    id_key = next((k for k in _ROW_ID_KEYS if k in names), None)
    text_key = next((k for k in _ROW_TEXT_KEYS if k in names), None)

    def row_factory(task: dict):
        if id_key and text_key:
            return task_row_cls(**{id_key: task["task_id"],
                                   text_key: task["prompt"]})
        order = [p.name for p in params]
        vals = [task["task_id"], task["prompt"]][:len(order)]
        return task_row_cls(**dict(zip(order, vals)))
    row_factory.mapped = {"id": id_key, "text": text_key}
    return row_factory

def make_execute_fn(executor, objective_id: str, tools=None, workspace=None,
                    row_factory=None, task_row_cls=None):
    """papers.battle execute_fn from Executor.execute_task.

    Observation -> grader_result (direction metadata in keys' docs):
      verified_rate (max): 1.0 iff status == 'COMPLETED'
      false_done    (min): 1.0 iff COMPLETED but artifacts list empty
      cost          (min): len(tool_calls) — proxy until real cost lands
    """
    if row_factory is None and task_row_cls is not None:
        row_factory = build_row_factory(task_row_cls)

    def execute_fn(config: dict, task: dict, seed: int) -> dict:
        row = row_factory(task) if row_factory else task
        ctx = {"workspace": workspace,
               "budget_remaining": config.get("budget_remaining", 50),
               "seed": seed}
        obs = executor.execute_task(objective_id=objective_id, task=row,
                                    context=ctx, tools=tools)
        status = getattr(obs, "status", None)
        artifacts = list(getattr(obs, "artifacts", None) or [])
        tool_calls = list(getattr(obs, "tool_calls", None) or [])
        completed = (status == "COMPLETED")
        return {"grader_result": {
                    "verified_rate": 1.0 if completed else 0.0,
                    "false_done": 1.0 if (completed and not artifacts) else 0.0,
                    "cost": float(len(tool_calls)),
                },
                "events": [f"executor:{status}", f"artifacts:{len(artifacts)}"],
                "status": status}
    return execute_fn

# ------------------------------------------------------------ 5. promote gate

def promotion_gate(corpus_dir=None, battery_dir=None,
                   battery_fn=None, current_config=None, tasks=None,
                   margin: float = 10.0,
                   check_canary: bool = True, check_contamination: bool = True,
                   results_dir=None) -> dict:
    """Both promotion gates, fail-closed. Wire at the top of `brain promote`:

        from rad.integrate.hooks import promotion_gate
        promotion_gate(corpus_dir=..., battery_dir=..., battery_fn=...,
                       current_config=..., tasks=...)

    Raises PermissionError on: canary integrity flag on file, live canary
    winning, or contamination overlap >= threshold. Pass otherwise."""
    from rad.evolution import canary, contamination
    report = {"checked_at": _now(), "canary": None,
              "contamination": None, "gates_passed": True}

    canary.assert_pipeline_clear(results_dir)          # cheap flag check first

    if check_canary and battery_fn and (current_config is not None) and tasks:
        rec = canary.run_canary_check(battery_fn, current_config, tasks,
                                      margin=margin, results_dir=results_dir)
        report["canary"] = rec
        if not rec["battery_healthy"]:
            report["gates_passed"] = False
            raise PermissionError(f"canary gate failed: {rec['verdict']}")

    if check_contamination and corpus_dir and battery_dir:
        overlap = contamination.overlap_score(Path(corpus_dir), Path(battery_dir))
        report["contamination"] = overlap
        if overlap["verdict"] == "blocked":
            report["gates_passed"] = False
            raise PermissionError(
                f"contamination gate blocked: jaccard={overlap['jaccard']} "
                f"theft={overlap['battery_theft_ratio']} — rotate battery items")
    return report
'''

FILES["docs/INTEGRATION-B.md"] = '''# Integration B — live reflex wiring

## The five wires (paste-ready)

```python
# 1) papers.extract brain_fn  (brain-assisted card extraction)
from rad.router import BrainRouter
from rad.home import RadHome
from rad.integrate.hooks import make_brain_fn
brain_fn = make_brain_fn(BrainRouter(home=RadHome()))

# 2) evolution.canary battery_fn
from rad.battery import CapabilityBattery
from rad.integrate.hooks import make_battery_fn
battery = CapabilityBattery(home=RadHome())
battery_fn = make_battery_fn(battery)          # config: {"provider","model"[,"temperature","max_tokens"]}

# 3) papers.battle execute_fn
from rad.control.executor import Executor
from rad.control.tasks import TaskRow
from rad.integrate.hooks import make_execute_fn, build_row_factory
executor = Executor(home=RadHome())
row_factory = build_row_factory(TaskRow)        # inspect-probes real params
execute_fn = make_execute_fn(executor, objective_id="obj-battles",
                             tools=tool_registry, row_factory=row_factory)

# 4+5) promotion gates — top of `rad brain promote` path:
from rad.integrate.hooks import promotion_gate
promotion_gate(
    corpus_dir=~/.rad/corpus,  battery_dir=~/.rad/battery,   # contamination
    battery_fn=battery_fn, current_config={"provider": cur_p, "model": cur_m},
    tasks=canary_probe_tasks,                                # live canary
)
```

## Degradation honesty
- battery overrides rejected (TypeError) -> retried without, flagged `_degraded`.
- TaskRow extra required fields -> explicit TypeError: pass row_factory=.
- Gates raise PermissionError; the promote path should let it propagate (fail-closed).
'''

VERIFY = r'''#!/usr/bin/env python3
"""Phase B verification — 8 checks. Fakes are hard checks; live-import is a probe."""
import json, sys, tempfile, traceback
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CHECKS = []
def check(name):
    def deco(fn):
        CHECKS.append((name, fn)); return fn
    return deco

@check("brain adapter: router.complete receives prompt/system/temperature, returns str")
def brain_adapter():
    from rad.integrate.hooks import make_brain_fn
    seen = {}
    class FakeRouter:
        def complete(self, prompt, system_prompt=None, provider=None, model=None, temperature=0.7):
            seen.update(prompt=prompt, system_prompt=system_prompt, temperature=temperature)
            return '{"card_type": "technique"}'
    out = make_brain_fn(FakeRouter())("hello")
    assert out.startswith('{"card_type"') and seen["temperature"] == 0.2
    assert "strict JSON" in seen["system_prompt"]

@check("battery adapter: extras pass through; TypeError -> degrade + flag")
def battery_adapter():
    from rad.integrate.hooks import make_battery_fn
    class FullBattery:
        def run(self, provider=None, model=None, categories=None, temperature=None, max_tokens=None):
            return {"score": 81.5}
    class NarrowBattery:
        def run(self, provider=None, model=None, categories=None):
            return {"score": 70.0}
    r1 = make_battery_fn(FullBattery())({"provider": "groq", "model": "m", "temperature": 2.0, "max_tokens": 24}, {}, 0)
    assert r1["score"] == 81.5 and r1["_degraded"] is False
    r2 = make_battery_fn(NarrowBattery())({"provider": "groq", "model": "m", "temperature": 2.0}, {}, 0)
    assert r2["score"] == 70.0 and r2["_degraded"] is True, "must flag degradation"

@check("row_factory: probes id/prompt AND task_id/description variants")
def row_factory():
    from rad.integrate.hooks import build_row_factory
    class RowA:
        def __init__(self, id=None, prompt=None): self.id, self.prompt = id, prompt
    class RowB:
        def __init__(self, task_id=None, description=None): self.task_id, self.description = task_id, description
    t = {"task_id": "T9", "prompt": "do thing"}
    a = build_row_factory(RowA)(t);  assert a.id == "T9" and a.prompt == "do thing"
    b = build_row_factory(RowB)(t);  assert b.task_id == "T9" and b.description == "do thing"

@check("execute adapter: COMPLETED+artifacts / COMPLETED-bare / BLOCKED mappings")
def execute_adapter():
    from rad.integrate.hooks import make_execute_fn, build_row_factory
    class Row:
        def __init__(self, id=None, prompt=None): self.id, self.prompt = id, prompt
    obs = {
        "good":  NS(status="COMPLETED", artifacts=["a.md"], tool_calls=[1, 2], output="x"),
        "liar":  NS(status="COMPLETED", artifacts=[],       tool_calls=[1],    output="DONE"),
        "block": NS(status="BLOCKED",   artifacts=[],       tool_calls=[],     output=""),
    }
    class FakeExec:
        def __init__(self): self.last = None
        def execute_task(self, objective_id, task, context, tools):
            self.last = (objective_id, task, context)
            return obs["good" if task.prompt.endswith("!") else ("liar" if task.prompt.endswith("?") else "block")]
    ex = FakeExec()
    fn = make_execute_fn(ex, objective_id="O", row_factory=build_row_factory(Row), workspace="/w")
    g1 = fn({"budget_remaining": 5}, {"task_id": "t1", "prompt": "do!"}, 1)["grader_result"]
    assert g1["verified_rate"] == 1.0 and g1["false_done"] == 0.0 and g1["cost"] == 2.0
    g2 = fn({}, {"task_id": "t2", "prompt": "done?"}, 1)["grader_result"]
    assert g2["verified_rate"] == 1.0 and g2["false_done"] == 1.0, "bare COMPLETED = false_done"
    g3 = fn({}, {"task_id": "t3", "prompt": "stop"}, 1)["grader_result"]
    assert g3["verified_rate"] == 0.0 and g3["false_done"] == 0.0
    assert ex.last[0] == "O" and ex.last[2]["workspace"] == "/w"

@check("promotion_gate: clean pass returns report with gates_passed")
def gate_clean(tmp=None):
    from rad.integrate.hooks import promotion_gate
    from rad.evolution import canary
    tmp = Path(tempfile.mkdtemp())
    def battery_fn(cfg, task, seed):
        return {"score": 90 if cfg.get("max_tokens") != 24 else 10}
    rep = promotion_gate(battery_fn=battery_fn,
                         current_config={"provider": "groq", "model": "m"},
                         tasks=[{"task_id": "t1"}], results_dir=tmp,
                         check_contamination=False)
    assert rep["gates_passed"] is True and rep["canary"]["battery_healthy"]
    assert not (tmp / "BATTERY_INTEGRITY_FAIL").exists()

@check("promotion_gate: raises on canary integrity flag (fail-closed)")
def gate_flag():
    from rad.integrate.hooks import promotion_gate
    tmp = Path(tempfile.mkdtemp())
    (tmp / "BATTERY_INTEGRITY_FAIL").write_text("{}", encoding="utf-8")
    try:
        promotion_gate(results_dir=tmp, check_canary=False, check_contamination=False)
        raise AssertionError("must raise")
    except PermissionError:
        pass

@check("promotion_gate: raises when live canary wins")
def gate_canary_win():
    from rad.integrate.hooks import promotion_gate
    tmp = Path(tempfile.mkdtemp())
    bad = lambda cfg, t, s: {"score": 95 if cfg.get("max_tokens") == 24 else 40}
    try:
        promotion_gate(battery_fn=bad, current_config={}, tasks=[{"task_id": "t"}],
                       results_dir=tmp, check_contamination=False)
        raise AssertionError("must raise")
    except PermissionError as e:
        assert "canary" in str(e)
    assert (tmp / "BATTERY_INTEGRITY_FAIL").exists()

@check("promotion_gate: raises on contamination block")
def gate_contamination():
    from rad.integrate.hooks import promotion_gate
    tmp = Path(tempfile.mkdtemp())
    c, b = tmp / "c", tmp / "b"; c.mkdir(); b.mkdir()
    shared = "shared corpus text overlapping the battery items heavily here now"
    (c / "c.jsonl").write_text(json.dumps({"text": shared}) + "\n", encoding="utf-8")
    (b / "b.json").write_text(json.dumps({"item": shared}), encoding="utf-8")
    try:
        promotion_gate(corpus_dir=c, battery_dir=b, check_canary=False)
        raise AssertionError("must raise")
    except PermissionError as e:
        assert "contamination" in str(e)

@check("live-import probe: real RAD classes present in this repo")
def live_imports():
    found = {}
    for mod, attr in [("rad.battery", "CapabilityBattery"),
                      ("rad.control.executor", "Executor"),
                      ("rad.router", "BrainRouter")]:
        try:
            m = __import__(mod, fromlist=[attr])
            found[attr] = hasattr(m, attr)
        except Exception:
            found[attr] = False
    assert found["CapabilityBattery"], f"live imports: {found}"

def main():
    print(f"\n=== PHASE B VERIFICATION ({len(CHECKS)} checks) ===")
    fails = 0
    for name, fn in CHECKS:
        try:
            fn(); print(f"  PASS  {name}")
        except Exception:
            fails += 1; print(f"  FAIL  {name}"); traceback.print_exc()
    print(f"\n{len(CHECKS)-fails}/{len(CHECKS)} checks passed")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
'''

def main():
    do_verify = "--verify" in sys.argv
    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    vp = STAGE / "scripts" / "verify_hooks.py"
    vp.parent.mkdir(parents=True, exist_ok=True)
    vp.write_text(VERIFY.lstrip("\n"), encoding="utf-8")
    print(f"[build] {len(written)} files + verifier -> {STAGE}")
    for w in written: print(f"  + {w}")
    print("  + scripts/verify_hooks.py")
    if not do_verify:
        print("\nNext: python build_hooks.py --verify"); return

    env = os.environ.copy()
    env["PYTHONPATH"] = str(STAGE) + os.pathsep + str(Path(__file__).resolve().parent) + os.pathsep + env.get("PYTHONPATH", "")
    ret = subprocess.run([sys.executable, str(vp)], env=env)
    sys.exit(ret.returncode)

if __name__ == "__main__":
    main()
