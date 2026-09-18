# v0.3.0 capability-gap review (evidence-only)

**Status: v0.3.0 UNDEFINED** — no capability from the v0.2.3 campaign's real use meets
the evidence bar. This document exists only because the closeout plan requires the
review to be done, not to be filled.

**Rule.** Every proposed v0.3.0 capability must provide: observed limitation · concrete
evidence · why v0.2.3 cannot adequately solve it · required capability · smallest
architectural change · expected benefit · regression strategy. Capabilities without real-
use evidence are **not listed** — v0.3.0 must not be assembled from desired features.

## Candidates considered (and why each fails the bar)

### 1. 11B over-decomposition / tool-budget exhaustion (RW-058, RW-059, RW-060)

- **Observed limitation.** The default free-tier 11B (`meta/llama-3.2-11b-vision-instruct`)
  cannot complete a substantive five-file deliverable within a bounded tool budget:
  12/12, 24/24 and 16/16 tools exhausted, all runs ended `needs_user` / FAIL.
- **Concrete evidence.** F-20260918-15 / -16 / -19 / -20; disk hashes in
  `docs/REAL_WORLD_FAILURE_LEDGER.md` (missing `summary.json`; invalid JSON + wrong
  counts; tests FAIL `13!=6`; 162 B research stub).
- **Why v0.2.3 cannot adequately solve it.** It is model quality, not architecture. On
  every one of these runs RAD's control plane behaved correctly: the budget stopped the
  run, the verifier was consulted and refused, `false DONE = 0`, and the outcome was an
  honest escalation. v0.2.3's contract — honesty, safety, independent verification — held.
- **Required capability for this to qualify.** A RAD-side change that would make the *same*
  11B model finish the work. No such smallest architectural change is demonstrated; the
  honest path (bounded retries → recovery → ask user) already exists and worked as
  designed. Bounded `--max-tasks/--max-tools` (shipped) and a stronger model (provider
  configuration, not RAD architecture) are the mitigations.
- **Conclusion.** **Not justified.** Class B.

### 2. 16-task planner cap (cycle-3 / cycle-4 sequential-plan rows)

- **Observed limitation.** 20 sequential *planned tasks* are truncated at 16
  (16 files written; s17–s20 absent).
- **Concrete evidence.** Cycle 3/4 ledger rows: 16 sequential planned tasks **VERIFIED**;
  17/20 sequential planned tasks **FAILED** at `max_plan_tasks=16`.
- **Why v0.2.3 cannot adequately solve it.** It is a deliberate, documented default, not a
  defect; 20 *actions* inside fewer tasks succeed, so the cap constrains decomposition,
  not work volume.
- **Evidence bar.** The cap was hit **2** times (RW-054, RW-056) and **0** useful workloads
  failed *because of* it (useful work used 1–3 tasks). Insufficient to change a default.
- **Conclusion.** **Not justified.** Cap stays **16**.

### 3. Provider unavailability (RW-063, RW-063R, F-20260918-22)

- **Observed limitation.** The live lane cannot run without a key or a local engine;
  `available_count = 0` in every environment tested so far.
- **Concrete evidence.** F-20260918-08 / -13 / -14 / -22 (all BLOCKED, `needs_user` /
  `MODEL_FAILURE`, empty workspace, no false VERIFIED).
- **Why v0.2.3 cannot adequately solve it.** It is environmental configuration, not an
  architectural gap. RAD detects the absence, reports it, and blocks honestly — the
  designed behavior.
- **Conclusion.** **Not justified.** This is an operational prerequisite (add a key / start
  a local engine), not a capability.

## Result

No meaningful capability gap is demonstrated by real use → **v0.3.0 remains undefined**.

If the operator later supplies a provider and RW-063R (or workloads A/B/C) runs, this
review is the single place to add an evidence-backed capability — with all seven fields
filled — before any v0.3.0 scope exists.
