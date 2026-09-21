#!/usr/bin/env python3
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
