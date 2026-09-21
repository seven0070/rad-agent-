# Phase NEXT — Integration Runbook



## 0. Entry #5 amendment (already-run pattern)

`record_amendment(battle_id=..., was="NOT_REPLICATED", now="CONFIRMED", reason="claim-scoped v1.1 ...")`



## 1. Claim-scoped verdicts (battle.py surgery, backward compatible)

- `_verdict(scores, metrics, claim_metrics=None)` — driving metrics only

- `spec["claim_metrics"]` from card battle_plan; default = all metrics (zero change)

- `record_battle_outcome` sets `pareto_tradeoff` flag; verdicts follow claims

- Future cards declare: `"claim_metrics": ["verified_rate"], "observe_metrics": ["cost"]`



## 2. Paper #2 — the generalization trial (~20 min)

```

python -m rad.cli_ext paper-add 2501.12948        # or any paper

python -m rad.cli_ext paper-card 2501.12948 --create    # real brain (Ollama live)

python -c "... set_card_status(slug,'candidate') ..."

# battle with claim_metrics scoped; Entry #6 is the lab's generalization proof

```

Success criterion: any verdict lands honestly — the pipeline being paper-agnostic IS the result.



## 3. Federation — Rad #2 (N2 activation)

1. Second machine: clone, install, `python build_contrib*.py` → same modules

2. Exchange: `peers.json = [{"agent":"B","secret_b64":"..."}]` (out-of-band key exchange)

3. `python -c "from rad.federation.cadence import peer_status; print(peer_status())"`

4. First `cross_audit(run_a, run_b, grader_fn)` → verdict.v0 into cross-ledger

   → **the first inter-agent trust verdict in Rad history**



## 4. Vital Layer wiring (sleep/wake hooks, behavior-organism only)

```

# in rad sleep path, after consolidation:

from rad.federation.cadence import sleep_checkup

from rad import curiosity

sleep_checkup(battery_fn=..., current_config=..., force=False)

curiosity.explore_once(home=RadHome().root, papers_dir=RadHome().root/"papers",

                       brain_fn=<optional live brain>)

# in chat wake path:

print(curiosity.wake_report())

from rad.vitals import collect, report

print(report(collect(RadHome().root)))

```

Laws non-negotiable: no survival drive · "configured to" never "I want" · shutdown unresisted.



## 5. Battery cadence — live

`sleep_checkup()` above IS the cadence (24h throttle, flag on file, promote gate reads it).

The immune system now runs on rhythm.



## 6. Desktop Ledger page (cockpit)

- New: `desktop/src/pages/Ledger.tsx` — reads `rad/desktop_ledger.py folded()/summary()`

  via sidecar endpoint (mirror Memory.tsx polling pattern)

- Show: battles table (verdict chips), amendments inline, replication_rate headline

- Zero backend change beyond exposing the two functions



## Verification

`python scripts/verify_next.py` — 12 checks, offline, deterministic.

