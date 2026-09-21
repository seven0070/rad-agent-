# Integration B — live reflex wiring

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
