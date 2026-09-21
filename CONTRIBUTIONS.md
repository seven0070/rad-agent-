# Contributions — Manifest & State

External AI-assisted design contribution, integrated under the project's own laws.

## SHIPPED (verified on-machine)
| Phase | Commit | Contents | Checks |
|---|---|---|---|
| P1 | f69323d | rad/papers/ (ingest, cards, battle, ledger, extract) · memory/strength.py · verify_contrib.py | 5/5 |
| P2 | db1058c | evolution/ (contamination, canary) · security/toolset_pin · control/verifier_checks · why/lineage · world/temporal · sovereignty/audit | 14/14 |

## SHIPPED (P3)
| Phase | Commit | Contents | Checks |
|---|---|---|---|
| P3 | (this commit) | routing/relay · federation/challenge · sovereignty/costcurve · tools/scenario_runner · 28-scenario pack · verify_contrib3.py | 13/13 |

## DOCS
docs/RFC-001..006 · docs/JERRY-SPEC.md — canonical copies.

## State vocabulary
PROPOSED → ATTACHED → VERIFIED → INTEGRATED → SHIPPED

## Integration hooks (VERIFIED → INTEGRATED), live signatures
| Hook | Live signature | Adapter |
|---|---|---|
| canary.battery_fn | `CapabilityBattery(home).run(provider=, model=) -> {"score": ...}` | wrap config→(provider,model); return {"score": report["score"]} |
| battle.execute_fn | `Executor(home).execute_task(obj_id, task, context, tools) -> Observation` | map Observation.status/artifacts → grader_result |
| extract.brain_fn | `BrainRouter(home).complete(prompt, system_prompt=..., ...) -> str` | direct one-liner |
| pipeline gate | call `canary.assert_pipeline_clear()` before any promote | one line in promote path |
| promote gate | run `contamination.overlap_score()` before `brain promote` | one line |
