# Contributions — Manifest & State

External AI-assisted design contribution, integrated under the project's own laws.

## SHIPPED (verified on-machine)
| Phase | Commit | Contents | Checks |
|---|---|---|---|
| P1 | f69323d | rad/papers/ (ingest, cards, battle, ledger, extract) · memory/strength.py · verify_contrib.py | 5/5 |
| P2 | db1058c | evolution/ (contamination, canary) · security/toolset_pin · control/verifier_checks · why/lineage · world/temporal · sovereignty/audit | 14/14 |
| P3 | 770aef5 | routing/relay · federation/challenge · sovereignty/costcurve · tools/scenario_runner · 28-scenario pack · verify_contrib3.py | 13/13 |
| B  | 8521cc0 / 69ed70b | rad/integrate/hooks.py (adapters + promotion_gate) · docs/INTEGRATION-B.md · verify_hooks.py · load-bearing gate in rad/brains.py & rad/cli.py | 9/9 |
| C  | (this commit) | rad/cli_ext.py · rad/integrate/promote_patch.py (wire_promote_gate) · scripts/verify_phase_c.py (falsy-config regression pin + WIRED probe) | 10/10 |

## DOCS
docs/RFC-001..006 · docs/JERRY-SPEC.md · docs/INTEGRATION-B.md — canonical copies.

## State vocabulary
PROPOSED → ATTACHED → VERIFIED → INTEGRATED → SHIPPED

## Integration hooks & Facades (VERIFIED → INTEGRATED)

To maintain 100% backward compatibility with existing callers while conforming to adapter contracts:
- `CapabilityBattery` (`rad/battery.py`) is implemented as an explicit facade subclassing `Benchmark`, allowing direct parameterization (`provider=`, `model=`, `temperature=`, `max_tokens=`) without altering `Benchmark.run`.
- `BrainRouter` (`rad/router.py`) is implemented as an explicit facade subclassing `RouterState`, exposing the `.complete(prompt, system_prompt=..., ...)` signature over `RouterState.chat`.

| Hook | Target Interface | Implementation / Facade | Adapter |
|---|---|---|---|
| canary.battery_fn | `CapabilityBattery.run(provider=, model=) -> {"score": ...}` | Facade subclass over `rad.battery.Benchmark` | wrap config→(provider,model); return {"score": report["score"]} |
| battle.execute_fn | `Executor.execute_task(obj_id, task, context, tools) -> Observation` | `rad.control.executor.Executor` | map Observation.status/artifacts → grader_result |
| extract.brain_fn | `BrainRouter.complete(prompt, system_prompt=..., ...) -> str` | Facade subclass over `rad.router.RouterState` | direct one-liner |
| pipeline gate | `canary.assert_pipeline_clear()` | File flag check at `home.root / "battery"` | Fail-closed gate in `rad/brains.py` & `rad/cli.py` |
| promote gate | `contamination.overlap_score()` | N-gram firewall against battery test theft | Fail-closed gate in `rad/brains.py` & `rad/cli.py` |

