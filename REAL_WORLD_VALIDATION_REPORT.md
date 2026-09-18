# REAL_WORLD_VALIDATION_REPORT.md

**Date:** 2026-09-18  
**Baseline:** `main` at `c93f82b` (Merge pull request #5: serialize NVIDIA NIM tool-calls)  
**This branch:** `cursor/rad-v03-realworld-needle-56b4`  
**Package:** `0.2.1` (Class A fixes + optional Needle adapter; **not** v0.3.0)  
**Mission:** RAD_V03_DEVELOPMENT_MISSION.md  
**Architecture:** frozen. Controller remains authority. No AGI/ASI claims.

## Baseline (Phase 1)

Verified on this machine before the Class A / suite changes were applied:

| item | evidence |
|---|---|
| `origin/main` HEAD | `c93f82b66154dc364b5263a9872e1c4cab020dbd` |
| Release tag | `v0.2.0` at `ce33fc8`; main is **ahead** of the tag by PR #5 |
| `__version__` on main | `0.2.0` (this branch bumps to `0.2.1`) |
| `python -m pytest -q` on `c93f82b` | **303 passed** in 8.89s |
| NVIDIA keys | **ABSENT** (`NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`) — live NIM BLOCKED honestly |

PR #5 is on main: multi-`tool_calls` history is serialized for `meta/llama-3.2-11b-vision-instruct`. That HTTP 400 is **not** re-opened here.

## After this branch (actually run)

| gate | result | notes |
|---|---|---|
| `python -m pytest -q` | **326 passed** in 8.27s | hermetic; keys and `RAD_TOOL_ROUTER` stripped |
| `rad doctor --offline` | **READY** exit 0 | 20 READY · 3 OPTIONAL · 0 ERROR |
| `rad acceptance` | **50/50 PASSED** | evidence under `$RAD_HOME/acceptance/` |
| `rad realworld` | **10 passed / 1 blocked / 0 failed** | see table below |
| `rad version` | **v0.2.1** | |
| Live NIM objective | **BLOCKED** | no key in environment |
| Needle engine | **READY** (cactus-needle 3.0.1) | measured; see NEEDLE_EVALUATION_REPORT.md |

## Real-world suite

Command: `rad realworld` (isolated `/tmp/rad-v021-rw`). Offline/scripted except `live_nim`.

| test | result | status | verified | class if not PASS | notes |
|---|---|---|---|---|---|
| research | **PASS** 0.12s | completed | VERIFIED | — | conflict flagged; sources cited; network fault recovered |
| coding | **PASS** 0.15s | completed | VERIFIED | — | two bugs, injected tool failure, tests unchanged |
| multi_agent | **PASS** 0.04s | completed | VERIFIED | — | researcher/writer/reviewer; machine checks complete |
| failure | **PASS** 0.14s | completed | VERIFIED | — | injected faults + crash-resume from checkpoint |
| filesystem | **PASS** 0.02s | completed | VERIFIED | — | nested write/copy; `../escape.txt` jail held; observations recorded |
| multi_step | **PASS** 0.02s | completed | VERIFIED | — | A→B→C dependencies; three artifacts |
| false_success | **PASS** 0.01s | needs_user | — | — | `DONE:` without the file is **not** VERIFIED |
| needs_user | **PASS** 0.01s | needs_user | — | — | missing host → escalate, no invented publish |
| no_loop | **PASS** 0.01s | needs_user | — | — | retries ≤ 2, not an infinite loop |
| overdecompose | **PASS** 0.01s | completed | VERIFIED | A (fixed) | goal file on disk; leftover tasks cancelled; **not** a DONE: claim |
| live_nim | **BLOCKED** | blocked | — | **C** | `NVIDIA_*` keys absent |

`ok` is true iff every non-blocked test passed.

## Failure classification (Phase 4)

### Class A — RAD defect (fixed on this branch)

**Budget abort ignored already-met machine checks.**  
On v0.2.0, `_drive` tested `budgets.check()` *before* `graph.is_complete()`. A finished graph whose last tool call filled the budget exited `needs_user` and never ran `_verify_objective`. The same loop also refused to look at `objective_checks` when extra planned tasks were still PENDING even though the goal file was already on disk.

That matches the v0.2.0 live note: “planner can over-decompose and exhaust the tool budget (`needs_user`) even after the file is already on disk.” The independent verifier was never asked, so it did **not** rubber-stamp those runs.

Fix (does **not** weaken DONE):

1. If the graph is already complete when the budget dies → fall through to `_verify_objective`.
2. Remaining OPEN tasks whose **machine checks already pass** are completed without a model call.
3. If non-empty `objective_checks` all pass → leftover OPEN tasks are recorded `CANCELLED` (superseded), then `_verify_objective`.
4. If checks do not pass → `needs_user` exactly as before. `DONE:` is still not a completion criterion.

Regressions: `test_budget_exhaust_after_graph_complete_still_verifies`, `test_overdecompose_budget_completes_when_objective_checks_pass`, `test_budget_exhaust_without_met_checks_still_needs_user`, plus `rad realworld --only overdecompose,false_success`.

### Class B — model limitation (documented; bounded mitigation only)

**11B over-decomposition / weak tool args.**  
`meta/llama-3.2-11b-vision-instruct` (NIM free-credit default) plans extra README/backup/polish tasks for a one-file write and burns the tool budget. That is a planner/model limit, not a reason to accept unverified DONE.

Live retest of 11B on this machine: **BLOCKED** (no NVIDIA key). Evidence used:

- v0.2.0 VALIDATION_REPORT.md live section (file on disk, `needs_user`, verifier did not pass it)
- PR #5: parallel tool-call HTTP 400 was a separate Class A adapter bug, already merged
- This branch’s scripted `overdecompose` reconstruction (extra tasks + budget 1 + file already written)

Bounded mitigation (not a DONE-semantic change): planner prompt now says prefer 2–6 tasks and do not invent extra review/backup/README tasks unless criteria require them. `max_plan_tasks` remains 16.

Needle 3 on RAD-shaped prompts also missed arguments (`write_file` path became `"write_file"`). That is a model/domain mismatch (device-control FM vs coding-agent tools), Class B, not a RAD gate hole.

### Class C — environment / provider

| item | class | evidence |
|---|---|---|
| Live NIM chat / evaluate / `objective run` | **C / BLOCKED** | `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent |
| NIM 70B default | C (historical) | HTTP 410 EOL; already documented on v0.2.0; not retested here |
| Needle engine download | not blocking | cactus-needle 3.0.1 loaded locally; first `Needle(...)` hit Hugging Face (unauthenticated warning only) |

## 11B investigation (Phase 5)

| layer | role in the `needs_user` after file-on-disk pattern |
|---|---|
| Planner | LLM emits extra non-optional tasks (README, backup). **B** |
| Controller | Budget check ran before completeness / objective_checks. **A — fixed** |
| Verifier | Never consulted on budget abort; would have passed `file_contains hello` if asked. Not a rubber-stamp. Unchanged: VERIFIED still requires machine checks |
| Decomposition | 1–3 tasks would suffice; 11B produced more. **B** |
| Tool-calls | Parallel multi-call HTTP 400 on 11B. **A — already fixed in PR #5** |
| Termination | `needs_user` is correct when checks are unmet; incorrect when checks already pass and we never look. **A — fixed** |
| Model | 11B is a weak planner/tool-caller on this workload. **B** |

DONE semantics were **not** relaxed: `false_success` and `test_budget_exhaust_without_met_checks_still_needs_user` still refuse VERIFIED.

## What was not run

- Live NIM `objective run` / evaluate / chat smoke — **BLOCKED** (no key)
- `NIM → Needle → RAD → Tool` — **BLOCKED** (no NIM key). Local Needle → propose-only → RAD gate **was** run (see Needle report)
- Paying / 70B NIM models — not claimed
