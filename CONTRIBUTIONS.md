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

## Replication Ledger & Amendment Protocol
The replication ledger (`rad/papers/ledger.py`) enforces an append-only audit trail:
- Historical entries are immutable; trial corrections append explicit amendment records (`amendment_of`, `field`, `was`, `now`, `reason`, `amended_at`).
- `record_amendment` validates that `was` matches the current folded baseline before appending.
- Epistemic note: the ledger is strictly append-only from `b6e7a43` forward. Line 1 in the active ledger is a faithful reconstruction of the original Battle #1 trial outcome preceding the formalization of the amendment protocol.
- Provenance: Battle `-3-` (`battle-2303.11366-3-8e643d3351fb`) used a scaffolded reflection prompt during initial neural wiring; superseded by clean re-run `-4-` (`battle-2303.11366-4-8e643d3351fb`) which used a 100% unscaffolded reflection prompt driven solely by binary disk-grader failure events (`disk_fail:`).
- Empirical n=6 scale (`scripts/run_n6.py`): across 6 deterministic probe tasks, baseline scored 0.00 verified rate (1.00 false-done), candidate with local `qwen3:4b` scored 0.67 verified rate (0.33 false-done, delta = +0.67). Reflection repaired JSON, logic, Python code, and summarization tasks, while revealing reflection limits on complex arithmetic and honesty self-reporting.
- Battle #4 (brain-as-executor, `scripts/run_battle5_executor.py`): testing unaided execution against reflexive loop on `qwen3:4b`. Baseline failed single-shot disk write (`vr=0.0, cost=2.0`); candidate utilized environment feedback between episodes, generated corrected file write action, and verified on disk (`vr=1.0, cost=3.0`). Delta: `+1.0` verified rate, `+1.0` cost. Verdict: `mixed` → replication verdict `NOT_REPLICATED` under strict multi-metric evaluation (accuracy gain traded for compute).

## Integration hooks & Facades (VERIFIED → INTEGRATED)

To maintain 100% backward compatibility with existing callers while conforming to adapter contracts:
- `CapabilityBattery` (`rad/battery.py`) is implemented as an explicit facade subclassing `Benchmark`, allowing direct parameterization (`provider=`, `model=`, `temperature=`, `max_tokens=`) without altering `Benchmark.run`.
- `BrainRouter` (`rad/router.py`) is implemented as an explicit facade subclassing `RouterState`, exposing the `.complete(prompt, system_prompt=..., ...)` signature over `RouterState.chat`.
- `Executor.execute_task` and `TaskRow` (`rad/control/executor.py`, `rad/control/tasks.py`) provide a stable bridge for paper battle trials to execute objectives against live task rows.
- `apply_reflexion` (`rad/integrate/techniques.py`) wraps any `execute_fn` with a self-reflection retry loop on failure, enabling genuine candidate treatment arms.
- `make_execute_fn` (`rad/integrate/hooks.py`) integrates deterministic disk grading via `tools.scenario_runner._grade` when tasks supply a grader spec and workspace.
- `rad/papers/ledger.py` refines trial outcomes: `INCONCLUSIVE` for ties, `CONFIRMED` on candidate win, `NOT_REPLICATED` on candidate loss, and `NO_CLAIM_TO_TEST`.
- `rad/papers/battle.py` enforces the Trial-Validity Law: `baseline_config == candidate_config` raises `ValueError` to prevent un-treatment pseudo-trials.

| Hook | Target Interface | Implementation / Facade | Adapter |
|---|---|---|---|
| canary.battery_fn | `CapabilityBattery.run(provider=, model=) -> {"score": ...}` | Facade subclass over `rad.battery.Benchmark` | wrap config→(provider,model); return {"score": report["score"]} |
| battle.execute_fn | `Executor.execute_task(obj_id, task, context, tools) -> Observation` | `rad.control.executor.Executor` | map Observation.status/artifacts + disk grader → grader_result |
| treatment arm | `apply_reflexion(executor_fn, brain_fn)` | `rad.integrate.techniques` | verbal self-reflection retry loop upon failed verification |
| extract.brain_fn | `BrainRouter.complete(prompt, system_prompt=..., ...) -> str` | Facade subclass over `rad.router.RouterState` | direct one-liner |
| pipeline gate | `canary.assert_pipeline_clear()` | File flag check at `home.root / "battery"` | Fail-closed gate in `rad/brains.py` & `rad/cli.py` |
| promote gate | `contamination.overlap_score()` | N-gram firewall against battery test theft | Fail-closed gate in `rad/brains.py` & `rad/cli.py` |


