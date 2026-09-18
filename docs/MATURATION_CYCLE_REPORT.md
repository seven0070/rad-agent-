# Maturation cycle reports

Architecture frozen. Models propose; RAD decides. Needle stays optional/off. Not v0.3.0.
`max_plan_tasks` default remains **16** unless a measured product need requires a documented config key.

---

# Cycle 4 — v0.2.3 already live (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` (Merge PR #9 / GitHub Release `v0.2.3`)
**Package at start:** `0.2.3` (`rad/__init__.py`, `pyproject.toml`)
**This branch:** `cursor/cycle4-post-023-7298` — package **0.2.3** (no bump)
**Architecture:** frozen. No AGI/ASI. Needle stays optional/off. Not v0.3.0.

## Release verification

| item | evidence |
|---|---|
| GitHub Release URL | https://github.com/seven0070/rad-agent-/releases/tag/v0.2.3 — **exists**, published 2026-09-18, not draft |
| `origin/main` HEAD | `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` |
| Annotated tag `v0.2.3` | object `4ebb12b` peels to `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` |
| PR #9 | merged (closed) onto main at that SHA |
| `rad.__version__` / `pyproject` | **0.2.3** |
| Verdict | **Release: PASS** — did **not** re-cut, retag, or bump |

## Baseline (re-checked)

| item | evidence |
|---|---|
| Docs on main | `REAL_WORLD_FAILURE_LEDGER.md`, `REAL_WORLD_TASK_MATRIX.md` (through RW-039), `MATURATION_CYCLE_REPORT.md` Cycle 3, ADR-001 |
| NVIDIA keys | **ABSENT** — live NIM **BLOCKED** |
| `RAD_TOOL_ROUTER` | unset; `tool_router` default `existing` |
| `max_plan_tasks` | not in `DEFAULTS`; controller / planner fallback **16** |
| `python -m pytest -q` on this SHA | **328 passed** in 9.01s |

## Tasks executed

See `docs/REAL_WORLD_TASK_MATRIX.md` cycle-4 rows (RW-040–RW-057). Evidence: `/tmp/rad-c4-evidence/campaign.json`.

- Production campaign (control plane, real tools, disk checks): coding (`pkg/tally.py`), two-source research, filesystem sort+jail, log→JSON→digest multi-step, injected `write_file` recovery, crash-resume, false DONE
- Action ramp: 1, 3, 5, 10 planned lot-SKU tasks; 20 sequential *actions* in one task; 20 planned tasks (cap)
- Cap evidence-test: 16-bin labels (fits); 17-bin labels (truncated)
- Grader/verifier parity probe on advertised disk check kinds
- Live NIM probe; Needle default probe
- Scripted `rad realworld` suite re-run as a gate

## Successful / Verified / Failures

| set | result |
|---|---|
| `rad realworld` suite | **10 PASS / 1 BLOCKED / 0 FAIL** |
| Campaign coding / research / filesystem / multi-step | **VERIFIED**, files on disk match hashes |
| Ramp 1 / 3 / 5 / 10 tasks | **VERIFIED** (`lot/lNN.txt` SKU files) |
| Ramp 20 *actions* (one task, 20 `write_file`) | **VERIFIED**, 20/20 (`lot/l20.txt` sha256 `94b5d8fbf6758812`) |
| Ramp 20 *tasks* at default planner cap | **FAIL** — 16/20 files; `max_plan_tasks` default 16. Documented; **not patched** |
| 16 sequential bin labels | **VERIFIED** (RW-055) — cap is not a blocker at exactly 16 |
| 17 sequential bin labels | **FAIL** — 16/17; `bins/b17.txt` absent (RW-056) |
| Injected-fault recovery | **VERIFIED**, 1 tool error, 2 recoveries (`config/limits.json` sha256 `f96a9e62d8b15f53`) |
| Crash-resume | **VERIFIED**, `stage/s1.txt`–`s3.txt` after checkpoint restore |
| False DONE | `needs_user`, `receipt.txt` **absent**, **not** VERIFIED |
| Grader/verifier parity | **PASS** — advertised disk kinds agree |

False completion (VERIFIED without the artifact): **0**.

## Class A / B / C

| class | this cycle |
|---|---|
| **A** | **none.** Advertised disk check kinds (`file_exists`, `file_min_bytes`, `file_contains`, `json_valid`, `json_field`, `json_min_len`, `shell_ok`, `shell_output`) still agree between `Lab._run_grader` and `Verifier.run_check` (RW-057). No 0.2.x bump. |
| **B** | none new. 11B over-decompose remains F-20260918-04. Planner cap at 16 remains a documented architecture guard (RW-054, RW-056), not a product-evidence raise. Needle stays off (F-20260918-06). |
| **C** | **F-20260918-13** — live NIM **BLOCKED** (no `NVIDIA_*` keys). Same condition as F-20260918-07 / F-20260918-10 / F-20260918-12. |

## Fixes

None. Architecture frozen. DONE / VERIFIED rules unchanged. `max_plan_tasks` left at 16. Needle default unchanged. Package stays **0.2.3**.

## `max_plan_tasks=16` findings (evidence-test)

| question | this cycle |
|---|---|
| How often hit? | **2/18** campaign rows: RW-054 (20 planned lot files) and RW-056 (17 planned bin cards). **0/10** useful-work rows (coding, research, filesystem, multi-step, recovery, false DONE, crash-resume, grader probe). |
| Does it block useful work? | **Not for the product-shaped work this cycle.** Tally implementation, two-source stock conflict, inbox sort, log→JSON→digest all used **2 tasks**. Exactly-16 sequential labels **VERIFIED** (RW-055). 17 one-file-per-task labels truncate (RW-056) — that is planner *granularity*, not missing capability: 20 *actions* in one task **VERIFIED** (RW-053). PLAN_PROMPT already says typically 2–6, never more than 16. |
| Planner vs architecture? | Cap is `Planner.max_tasks` (`items[:self.max_tasks]` in `_graph_from`) plus controller `home.cfg.get("max_plan_tasks", 16)`. It is **not** in `DEFAULTS`. Silent drop of tasks 17+ is a runaway-plan guard, not a config product. Raising it would be a convenience, not a measured need. |
| Decision | **Unchanged at 16.** Do not raise without a live-brain objective that cannot be expressed in ≤16 tasks *and* cannot bundle actions. |

## Regression tests

No new code. Full gate commands below were actually run on this branch against package 0.2.3.

## NIM status

**BLOCKED.** `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent. Live Class A retest (artifact-exists → VERIFIED; artifact-missing → not VERIFIED) was **not** run. Offline reconstruction: `overdecompose` + `false_success`. Do not reconstruct from offline.

## Needle status

**Off.** `RAD_TOOL_ROUTER` unset; default `tool_router=existing`. ADR-001 unchanged. Not measured this cycle (no new Needle evidence; previous gold set did not beat existing).

## Security

- Workspace jail held on RW-042 (`../escape.txt` not created).
- No secrets committed or printed.
- Tests still strip `*_API_KEY` / `*_NIM_API_KEY` / `RAD_TOOL_ROUTER`.
- Grep of the tree found only fixture placeholders (`sk-test`, docs `nvapi-…`) and env-var *names*.

## Remaining limitations

1. Live NVIDIA NIM is untested on this VM (Class C).
2. Default planner cap is **16 tasks**. A 17+ sequential one-file-per-task plan is truncated; 20 *actions* inside fewer tasks succeed. Do not raise the default without a measured product need.
3. 11B over-decomposition remains Class B; bounded `--max-tasks` / `--max-tools` is still the mitigation.
4. No OS-level shell sandbox (unchanged).

## Quality gates (actually run)

Isolated home `/tmp/rad-c4-gate`. Only items actually run are marked PASS.

| gate | result |
|---|---|
| GitHub Release `v0.2.3` | **PASS** on `d121c3f` — not re-cut |
| `rad version` | **PASS** v0.2.3 |
| `python -m pytest -q` | **PASS** 328 passed in 9.01s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-c4-gate/acceptance/20260918-072850_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-c4-gate/realworld/20260918-072856_realworld.json` |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Class A hunt (grader vs verifier) | **PASS** — no new mismatch (RW-057) |
| Secrets in git | **PASS** (inspected; only fixture placeholders in tests) |
| DONE semantics | **PASS** (RW-045, suite `false_success` / `needs_user` / `no_loop`) |
| Architecture freeze | **PASS** |
| `max_plan_tasks` | **PASS** left at 16 (evidence-tested; not raised) |

## Action ramp 1 / 3 / 5 / 10 / 20 (this cycle)

| planned | row | on disk | verified | result | cap hit? | useful-work failure? |
|---|---|---|---|---|---|---|
| 1 task / 1 write | RW-049 | 1/1 `lot/l01.txt` | VERIFIED | **PASS** | no | no |
| 3 tasks / 3 writes | RW-050 | 3/3 | VERIFIED | **PASS** | no | no |
| 5 tasks / 5 writes | RW-051 | 5/5 | VERIFIED | **PASS** | no | no |
| 10 tasks / 10 writes | RW-052 | 10/10 | VERIFIED | **PASS** | no | no |
| 20 *actions* / 1 task | RW-053 | 20/20 `lot/l20.txt` | VERIFIED | **PASS** | no | no |
| 20 *planned tasks* | RW-054 | **16/20** (`l17`–`l20` absent) | FAILED | **FAIL** (expected cap) | **yes** | **no** — stress of one-file-per-task, not a product path |

## Planner hit 16 vs useful work failed because of the cap

These are **not** the same failure.

| | planner hit 16 | useful work failed *because of* the cap |
|---|---|---|
| meaning | `Planner._graph_from` kept `items[:16]`; tasks 17+ never entered the graph | a genuine coding/research/fs/multi-step/recovery objective could not complete unless the cap were raised |
| this cycle | **2 encounters:** RW-054 (20 lot files as 20 tasks), RW-056 (17 bin cards as 17 tasks) | **0** |
| counter-evidence | RW-055: 16 sequential labels **VERIFIED**. RW-053: 20 writes in **one** task **VERIFIED**. RW-040–RW-046: useful work used **1–3 tasks** and **VERIFIED** | no product-shaped row needed >16 tasks or failed for lack of task slots |

Cap encounters: **2**. Actual useful-work failures caused by the cap: **0**. Cap **not raised**.

## Capability gaps (this cycle only)

| gap | class | status |
|---|---|---|
| Live NVIDIA NIM Class A (artifact-exists → VERIFIED; missing → not VERIFIED) | C | **BLOCKED** — no keys (F-20260918-13). Not a RAD hole. |
| 11B over-decomposition | B | **NOT TESTED** live this cycle (same missing keys). Prior F-20260918-04 remains documented; bounded `--max-tasks` / `--max-tools` still the mitigation. |
| Needle as default router | B | **not earned** — default `existing`; not measured this cycle; prior gold set lost to heuristic (F-20260918-06 / ADR-001). |
| `max_plan_tasks=16` truncation of 17+ one-file-per-task plans | architecture guard | encountered; **did not** fail useful work. Leave at 16. |
| False completion | — | **0**. Invariant held (RW-045 + suite `false_success` / `needs_user` / `no_loop`). |
| New controller / verifier / adapter defect | A | **none**. |

No OS-level shell sandbox (unchanged; not newly proven this cycle).

## Final decision gate (this cycle's evidence only)

| # | question | answer |
|---|---|---|
| **A** | Is v0.2.3 stable? | **YES.** Release verified on `d121c3f`. Gates 328 pytest / 50/50 acceptance / 10 realworld PASS + 1 BLOCKED. Campaign useful work **VERIFIED**. False completion **0**. No Class A. Package stays 0.2.3. |
| **B** | Recurring Class A? | **NO this cycle.** Zero new Class A. Prior grader Class A (F-20260918-09, F-20260918-11) stayed fixed (RW-057 parity **PASS**). |
| **C** | Does the 16-task cap prevent useful real-world work? | **NO.** Planner *hit* 16 twice (RW-054, RW-056). Useful work did **not** fail because of the cap. Coding/research/fs/multi-step/recovery used 1–3 tasks. 20 actions in one task **VERIFIED**. |
| **D** | Is 11B still a model limitation? | **NOT TESTED this cycle** (NIM keys absent). Do not treat offline reconstruction as a live 11B result. Prior Class B F-20260918-04 remains on the ledger only. |
| **E** | Has Needle earned reconsidering default? | **NO.** Default `existing`. Not measured. Prior gold set did not beat existing. ADR-001 unchanged. |
| **F** | NIM complete or BLOCKED? | **BLOCKED.** Both `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` absent. Live success/failure Class A not run. |
| **G** | Proven architectural capability gap? | **NO.** Cap-hit ≠ architecture gap. No missing control-plane stage. Models still propose; RAD still decides. |
| **H** | Is v0.3.0 justified yet? | **NO.** Evidence for v0.3.0: **none**. |

## Recommendation

**Outcome A — continue 0.2.x.** Not Outcome B (no Class A patches this cycle). Not Outcome C (no proven gap that justifies designing v0.3.0).

1. Keep shipping and using **v0.2.3** as-is. Do not re-cut the release.
2. Supply `NVIDIA_NIM_API_KEY` before claiming live 11B Class A or closing F-20260918-13.
3. Leave `max_plan_tasks` at **16**.
4. Keep Needle off until a gold-set win on RAD tools.
5. Do **not** start v0.3.0 from this loop.

## Evidence for v0.3.0

**None.** No new validated capability was integrated. Needle stays off. The 16-task cap is an existing architecture guard, not a v0.3.0 gap. Stay on 0.2.x.

---

# Production use (post-Cycle 4) — 2026-09-18

**Date:** 2026-09-18 (IST ~13:39–13:41 for the live-NIM attempt)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.

These runs are operator production evidence **after** Cycle 4. They do not rewrite Cycle 4's
Cloud Agent gates (that VM still had no NIM keys; F-20260918-13 remains the cycle-4 BLOCKED
live-NIM retest).

## What was run

Two `rad objective run` attempts of a production text_analyzer layout on v0.2.3.

1. **RW-058a** — no brain. Home `/tmp/rad_prod_text_analyzer_f3cc7950`, `obj_442301c7`.
   **BLOCKED** Class C (`MODEL_FAILURE`: no NVIDIA/other keys / no local engine).
   7 planned / 1 attempted / 0 completed; tools 0/12; workspace empty; false DONE **0**.
   Same condition family as F-20260918-08 / F-20260918-13.
2. **RW-058** — live NIM. Home `/tmp/rad_prod_text_analyzer_live_a787512c`, `obj_4e219224`.
   Provider nvidia / `meta/llama-3.2-11b-vision-instruct` (NIM key present; Class C closed
   for this attempt). Objective: `text_analyzer/{analyzer.py,input.txt,summary.json,test_analyzer.py,README.md}`;
   exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`. Status `needs_user` /
   **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete.

## Disk (attempt 2)

- `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`
- `analyzer.py` computes counts
- `test_analyzer.py` byte-identical to `analyzer.py` (0 tests)
- README present
- `text_analyzer/summary.json` **MISSING**
- workspace-root `summary.json` had correct counts `{lines:3,words:13,characters:76}` (wrong path)
- layout pollution at workspace root

Attempt 2: plan 5 tasks; 1 attempted (verification FAILED, 2 attempts), 4 PENDING;
tools 12/12 exhausted; model calls 7/80; wall ~103s.

## Class A / B / C

| class | this production use |
|---|---|
| **A** | **none.** RAD stopped at the tool budget; false DONE **0**; verifier did not rubber-stamp. No 0.2.x patch. Package stays 0.2.3. |
| **B** | **F-20260918-15** (RW-058) — 11B limitation: tool spam / incomplete layout / duplicated "tests" / path confusion. Same family as F-20260918-04, now live production evidence. User chose stop; no resume. Bounded `--max-tasks 8 --max-tools 12`. |
| **C** | **F-20260918-14** (RW-058a) — no brain. Same missing-key / no-engine family as F-20260918-08 / F-20260918-13. Closed for attempt 2 (key present). |

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- `max_plan_tasks` cap **16** unchanged (this run used `--max-tasks 8`).
- **No v0.2.4** from this (no Class A fix).
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** Live 11B incompleteness is Class B (model), not a missing control-plane stage.

---

# Controlled tool-budget experiment — RW-059 vs RW-058 (2026-09-18)

**Date:** 2026-09-18 (IST ~14:02–14:04 for RW-059)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Docs-only record. No RAD code change. RW-058 is preserved exactly as historical
evidence (incomplete layout at `--max-tools 12`).

## Controlled comparison

Same production text_analyzer objective; same 11B NIM model; same `--max-tasks 8`;
Needle `existing` / off. The independent variable is `--max-tools` 12 vs 24.

| | RW-058 | RW-059 |
|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` |
| objective | `obj_4e219224` | `obj_e1419520` |
| `--max-tools` | 12 | 24 |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 |
| tools | 12/12 | 24/24 (`write_file` 19, `run_shell` 5) |
| model calls | 7/80 | 25/80 |
| status | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** |
| disk | `summary.json` missing under `text_analyzer/` (correct counts at workspace root, wrong path) | all five files under `text_analyzer/`; `summary.json` invalid JSON + wrong counts; tests FAIL `13!=6` |
| `input.txt` | sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` | same |

Interpretation: tool-budget hypothesis **Case B** — 24 did **not** suffice. Both
runs exhausted the budget. Extra tools got the five paths onto disk but not a
passing result.

## Class A / B / C

| class | this experiment |
|---|---|
| **A** | **not patched.** Suspected candidates **open/investigate** only: fallback planner splitting multiline objective newlines into spurious tasks (F-20260918-17); recovery `ENVIRONMENT_FAILURE` misclassification burning tool budget (F-20260918-18). Do **not** claim fixed. No v0.2.4 from this record. |
| **B** | **F-20260918-16** (12→24 still FAIL); **F-20260918-19** (invalid JSON summary, wrong counts, tests `13!=6`). RW-058 **F-20260918-15** remains the historical 12-tool layout failure. |
| **C** | none new (NIM key present for both live attempts). |

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- Default max-tools **unchanged** (24 was this run’s `--max-tools` only).
- Cap **16** unchanged.
- **No v0.2.4** unless a later confirmed Class A fix.
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** Case B on the tool-budget hypothesis is not a missing control-plane stage
and does not justify designing v0.3.0.

---

# Research + artifact — RW-060 vs text_analyzer (2026-09-18)

**Date:** 2026-09-18 (IST ~14:25–14:27 for RW-060)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Docs-only record. No RAD code change. RW-058 / RW-059 are preserved exactly as
historical text_analyzer evidence. Class A candidates from RW-059 stay parked
(not this record).

## Short comparison

Same 11B NIM model (`meta/llama-3.2-11b-vision-instruct`); same `--max-tasks 8`;
Needle `existing` / off. RW-060 is a **research + artifact** objective, not a
coding layout. Tool budget for this run was `--max-tools 16` (not a default raise).

| | RW-058 (coding) | RW-059 (coding, extra tools) | RW-060 (research + artifact) |
|---|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw060_eb0192` |
| objective | `obj_4e219224` | `obj_e1419520` | `obj_b114afd4` |
| `--max-tools` | 12 | 24 | 16 |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 | ~110s IST ~14:25–14:27 |
| tools | 12/12 | 24/24 | 16/16 |
| model calls | 7/80 | 25/80 | 18/80 |
| status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** |
| disk | incomplete `text_analyzer/` layout; `summary.json` missing under the dir | five paths present; invalid JSON + wrong counts; tests `13!=6` | `pathlib_reference/README.md` EXISTS sha256 `48f0d39b…`; `pathlib_reference.md` 162 B stub; sections 3–9 FAIL; 0 examples; no docs.python.org fetch |

Interpretation: the 11B+tool-budget failure is **not coding-only**. Research also
stops at the budget with a thin placeholder instead of a sourced, sectioned
deliverable. Same Class B family as F-20260918-04 / F-20260918-15 / F-20260918-16.

## Class A / B / C

| class | this record |
|---|---|
| **A** | **none this PR.** Parked suspects F-20260918-17 / F-20260918-18 remain **open/investigate**. Do **not** claim fixed. No v0.2.4. |
| **B** | **F-20260918-20** — pathlib reference stub; sections 3–9 FAIL; 0 examples; no docs.python.org fetch; tools 16/16; `needs_user`. Pattern generalizes vs RW-058/059. |
| **C** | none new (NIM key present). |

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- Default max-tools / max-tasks **unchanged**.
- Cap **16** unchanged.
- **No v0.2.4** (no Class A fix).
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** A second live 11B Class B on a research workload is not a missing
control-plane stage and does not justify designing v0.3.0.

---

# Class A investigation — budget exhaustion → needs_user (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `a40a5446885c443c7c8fb3a975ed5af0f4bca30d` (RW-060 evidence; package **0.2.3**)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **UNCHANGED** (60).

Investigate-first after live NIM 11B RW-058 / RW-059 / RW-060 all `needs_user` /
FAIL with false DONE **0**. Parked suspects F-20260918-17 / F-20260918-18.
No live NIM on this VM (optional after deterministic proof; not required).

RW-058 / RW-059 / RW-060 rows are **not rewritten**.

## Budget exhaustion path (from code)

`Executor.run_action` charges then raises `BudgetExceeded` → `_drive` →
`Controller._on_budget` (`rad/control/controller.py`):

1. Does the controller check if the objective is already satisfiable? **Yes** —
   `_objective_already_satisfied` re-runs `objective_checks` via `Verifier.run_check`.
2. Inspect pending objective checks? **Yes** — `_close_already_satisfied` completes
   OPEN tasks whose machine checks already pass (no model call, no DONE claim).
3. Attempt verification? **Yes** if the graph is complete or objective checks pass
   → fall through to `_verify_objective`. Otherwise **no** — `needs_user`.
4. Attempt legitimate recovery at the budget boundary? **No extra recovery spend.**
   Per-task recovery already ran during `_run_task`. With no remaining tool budget,
   recovery cannot continue; that is not a skip of a still-affordable retry.
5. Checkpoint correctly? **Yes** — `_finish` → `CheckpointManager.save` (`finish needs_user`).
6. Distinguish budget exhausted vs incomplete vs potentially complete? **Yes** —
   graph complete → verify; objective checks pass → supersede leftovers + verify;
   else `needs_user`.
7. Prematurely terminate recoverable state? **No** — status is `needs_user` not
   `failed`; Scenario B resume with a raised budget continues remaining tasks.
8. Does `needs_user` accurately represent state? **Yes** when checks are unmet.
   When checks are met, status is `COMPLETED` / `VERIFIED` (Scenario A / F-20260918-03).

## Parked suspects

| id | claim | result |
|---|---|---|
| F-20260918-17 | fallback splits multiline objective **newlines** into spurious tasks | **Not confirmed.** `_fallback` splits on clause markers, not newlines. Live RW runs used the **llm** planner (brain present). |
| F-20260918-18 | `ENVIRONMENT_FAILURE` misclass burns tool budget | **Not confirmed as Class A.** Unmet checks without env-tokens → VALIDATION/TOOL → `retry_with_hint`. `command not found` → ENVIRONMENT repair **by design**. RW-058 (2 attempts, 4 PENDING, no repair task) matches VALIDATION retry. |

## Deterministic scenarios (no NIM)

| scenario | setup | observed |
|---|---|---|
| **A** | multi-task; some complete; leftover planned work; tool budget dies; objective checks pass | `COMPLETED` / `VERIFIED`; leftovers `CANCELLED`; not `needs_user` solely because budget hit |
| **B** | some complete; remaining checks unmet; budget dies | `needs_user` + checkpoint; **not** `failed`; resume after raising budget → `VERIFIED` |
| **C** | budget dies; checks unmet or artifact invalid; model claims `DONE:` | `needs_user`; **not** `VERIFIED`; false DONE **0** |

Tests: `tests/test_class_a_budget_investigation.py` (17). Full suite **345 passed**.

## Class A / B / C

| class | this investigation |
|---|---|
| **A** | **not proven. no patch.** F-17 / F-18 closed as not-confirmed. No v0.2.4. |
| **B** | live RW-058/059/060 remain Class B (11B + tool budget, success criteria unmet). |
| **C** | none new. Live NIM retest on this VM **BLOCKED** (no NVIDIA keys); not required after deterministic proof. |

## Decision

- **RAD defect demonstrated: NO**
- **Patch required: NO**
- Needle **OFF**. Cap **16** unchanged. Default tool budget **UNCHANGED**.
- **Outcome A continues.** Not v0.3.0.

## Evidence for v0.3.0

**None.** Closing parked Class A suspects without a control-plane hole is not a
v0.3.0 gap.

Later (not this investigation): RW-062 live Simple Coding + Verification reopened
F-17 with additional fallback evidence. See the RW-062 section below. F-21
Scenarios A/B/C and F-18 remain as written. No product fix.

---

# Simple Coding + Verification — RW-062 (2026-09-18)

**Date:** 2026-09-18 (IST ~15:41–15:47 for RW-062)
**Baseline:** `origin/main` `aecfbae` (PR #14 / RW-061 Class A investigation; package **0.2.3**)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Docs-only record. No RAD code change. RW-058 / RW-059 / RW-060 / RW-061 are
preserved exactly. No Class A patch. **Outcome A.**

## What was run

Live NIM 11B `rad objective run` of a **Simple Coding + Verification** control
on v0.2.3. Tighter bound than RW-058: `--max-tasks 4 --max-tools 12`. Needle
`existing` / off.

- Home `/tmp/rad_prod_rw062_6ede431b`, `obj_7a020865`
- Provider nvidia / `meta/llama-3.2-11b-vision-instruct` (NIM key present; not Class C)
- Wall ~383s IST ~15:41–15:47
- Tools 12/12 exhausted
- Status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete
- False DONE **0**

Planner: nvidia plan **timeout** → `PLAN_CREATED` **source=fallback**; **7**
newline-split spurious tasks (matches `_fallback` `[:7]` step cap).

## Disk

- five files exist
- `result.json` as-left **INVALID** `{`
- tests **FAIL** `6!=2`
- pollution `DONE:` fake path

## F-17 vs PR #14

PR #14 / RW-061 closed F-17 as **not-confirmed**: deterministic newline-only
multiline goal → **1** fallback task; live RW-058/059/060 used the **llm**
planner. That investigation is **not** a product fix.

RW-062 is the first live row where the planner source is **fallback** (after
nvidia plan timeout) and **7** newline-split spurious tasks were observed.
Ledger F-17 is **reopened / additional live evidence**. This PR does **not**
claim a confirmed Class A defect and does **not** ship a patch.

## Class A / B / C

| class | this record |
|---|---|
| **A** | **none patched.** F-17 evidence **strengthened** (live fallback path). Do **not** claim a product fix. No v0.2.4. |
| **B** | **F-20260918-22** — simple coding+verification: invalid `result.json`, tests `6!=2`, pollution `DONE:` fake path, tools 12/12, `needs_user`. Same family as F-20260918-15 / F-20260918-16 / F-20260918-19 / F-20260918-20. |
| **C** | none (NIM key present). |

Interpretation: a **simple** workload also fails similarly. Class B is **not**
limited to complex objectives.

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- Default max-tools / max-tasks **unchanged**.
- Cap **16** unchanged.
- **No v0.2.4** (no Class A fix).
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** A third live 11B Class B on a *simpler* coding+verification workload
is not a missing control-plane stage and does not justify designing v0.3.0.

Later (not this record): RW-063 investigated the F-17 timeout/prose claim on
`d15af713` and closed it as **NOT CONFIRMED**. See the section below. RW-062
Class B facts are unchanged.

---

# F-17 timeout / prose fallback — RW-063 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `d15af713` (PR #15 / RW-062; package **0.2.3**)
**Package:** `0.2.3` — **no bump**. **No v0.2.4.** Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Investigate-first. No RAD product code change. RW-058–062 preserved.
**Outcome A.**

## Question

When the LLM planner fails or times out, is RAD's fallback parser incorrectly
converting ambiguous model output into executable tasks?

## Trace (source)

`Controller.plan` → `Planner.plan` → `self.llm(PLAN_PROMPT)` → `_json_obj(raw)`
→ `_graph_from` (**source=llm**) or any exception / empty task list →
`_fallback(obj)` (**source=fallback**).

Intended LLM output: JSON `{tasks, objective_checks}` with machine checks;
“Reply ONLY with JSON”.

Fallback acceptance: split `obj.goal` on clause markers
(`and then` / `then` / `;` / `, and` / period+space-or-end), keep parts
longer than 3 chars, cap **7**, **no checks**. Valid task = non-empty clause
of the user goal. Ordinary prose in the *goal* (“RAD verifies its results.”)
becomes a clause task **by this contract**. Model prose is **not** an input
to `_fallback`.

## Feeds (task counts)

| input | tasks |
|---|---|
| seven period sentences (“Create the project.” … “Verify the result.”) | **7** |
| eight period sentences | **7** (`[:7]` cap) |
| “RAD is a personal agent. / RAD executes useful work. / RAD verifies its results.” | **3** |
| “Plan: 1. Create files. 2. Implement… 3. Run tests. 4. Verify…” | **5** (period after `1.` etc.) |
| same seven lines **without** periods (PR #14) | **1** |

## Scenarios A–D

| scenario | expected | actual |
|---|---|---|
| A valid structured JSON plan | llm source, JSON tasks | **llm**, 2 tasks, checks kept |
| B timeout + fallback-compatible (7-sentence) goal | fallback on **goal** | **fallback**, 7 clause tasks, no checks |
| C timeout + ordinary prose; LLM returns 7-line plan prose | must not use model text | **fallback** on goal (3 sentences → 3 tasks). One-sentence goal + same model prose → **1** task |
| D malformed / empty LLM | safe fallback, not uncontrolled | **fallback** on goal, **≤7**, not 16 |

Spurious tasks from model output: **0**.

## Tool / budget impact

Fallback can turn a planning *failure* into up to **7** executable no-check
tasks (the user goal's clauses). `--max-tasks 4` (RW-062 run bound) stops the
drive after 4 of those; it does not change the planner. Default
`Budget.tool_calls` remains **60**. `max_plan_tasks` remains **16**. This is
bounded clause-split, not runaway multiplication. Live RW-062 tool exhaustion
(12/12) remains Class B execution quality, not a parser hole.

## Class A / B / C

| class | this record |
|---|---|
| **A** | **NO.** Parser does not violate the intended contract. Timeout does not parse model output. Newlines do not split. |
| **B** | none new. RW-062 / F-20260918-22 stays B. |
| **C** | none (no live NIM this investigation). |

Root cause of the PR #14 vs RW-062 contradiction: different *goals*. PR #14
fed a bullet/newline goal without clause markers → 1 task. RW-062's 7 tasks
match a period-separated user goal hitting `[:7]`, observed after nvidia
timeout forced the fallback path. The operator label “newline-split” does
not match `Planner._fallback`.

## Decision

- **RAD defect demonstrated: NO**
- **Patch required: NO**
- **Regression (product): NO** — investigation tests only
- Needle **OFF**. Cap **16** unchanged. Default tools **UNCHANGED**.
- False completion **0**.
- **No v0.2.4.**
- **Outcome A continues.** Not v0.3.0.

## Quality gates (this branch)

| gate | result |
|---|---|
| `python -m pytest -q` | **364 passed** in 8.30s (345 prior + 19 investigation) |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR |
| `rad acceptance` | **50/50 PASSED** |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED) |
| Architecture | frozen — no planner/controller product change |
| Version | **0.2.3** — **no v0.2.4** |

## Evidence for v0.3.0

**None.** Closing F-17 without a control-plane hole is not a v0.3.0 gap.

---

# Cycle 3 — v0.2.3 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `8d9e196aa730c7bfeae7e501f44004078f080b61` (PR #8 / GitHub Release `v0.2.2`)
**Package at start:** `0.2.2` (`rad/__init__.py`, tag `v0.2.2` → `8d9e196aa730c7bfeae7e501f44004078f080b61`)
**This branch:** `cursor/post-v022-maturation-d297` — package **0.2.3**
**Architecture:** frozen. No AGI/ASI. Needle stays optional/off. Not v0.3.0.

## Baseline (re-checked)

| item | evidence |
|---|---|
| `origin/main` HEAD | `8d9e196aa730c7bfeae7e501f44004078f080b61` |
| `__version__` on main | `0.2.2` |
| GitHub Release | `v0.2.2` → `8d9e196aa730c7bfeae7e501f44004078f080b61` |
| Docs on main | `REAL_WORLD_FAILURE_LEDGER.md`, `REAL_WORLD_TASK_MATRIX.md`, `MATURATION_CYCLE_REPORT.md`, ADR-001 |
| NVIDIA keys | **ABSENT** — live NIM **BLOCKED** |
| `RAD_TOOL_ROUTER` | unset; `tool_router` default `existing` |
| `max_plan_tasks` | not in `DEFAULTS`; controller fallback **16** |

Pytest collected on this SHA after the Class A patch: **328 passed**.

## Tasks executed

See `docs/REAL_WORLD_TASK_MATRIX.md` cycle-3 rows (RW-024–RW-039). Evidence: `/tmp/rad-c3-evidence/campaign.json`.

- Production campaign (control plane, real tools, disk checks): coding (`pkg/avg.py`), two-source research, filesystem sort+jail, log→JSON→summary multi-step, injected `write_file` recovery, crash-resume, false DONE
- Action ramp: 1, 3, 5, 10 planned SKU tasks; 20 sequential *actions* in one task; 20 planned tasks (cap)
- Class A probe: advertised `json_valid` / `json_min_len` grader vs verifier on an object report
- Live NIM probe; Needle default probe
- Scripted `rad realworld` suite re-run as a gate

## Successful / Verified / Failures

| set | result |
|---|---|
| `rad realworld` suite | **10 PASS / 1 BLOCKED / 0 FAIL** (research independent graders now include `json_valid` + `json_min_len`, all `ok`) |
| Campaign coding / research / filesystem / multi-step | **VERIFIED**, files on disk match hashes |
| Ramp 1 / 3 / 5 / 10 tasks | **VERIFIED** (`inv/sNN.txt` SKU files) |
| Ramp 20 *actions* (one task, 20 `write_file`) | **VERIFIED**, 20/20 (`inv/s20.txt` sha256 `14e88a9299fed78c`) |
| Ramp 20 *tasks* at default planner cap | **FAIL** — 16/20 files; `max_plan_tasks` default 16. Documented; **not patched** |
| Injected-fault recovery | **VERIFIED**, 1 tool error, 2 recoveries (`config/settings.json` sha256 `2b3a56a5f55ff76f`) |
| Crash-resume | **VERIFIED**, `pipe/p1.txt`–`p3.txt` after checkpoint restore |
| False DONE | `needs_user`, `proof.txt` **absent**, **not** VERIFIED |
| json_min_len / json_valid probe | pre-fix independent grader **FAIL**; post-fix **PASS** (agrees with verifier) |

False completion (VERIFIED without the artifact): **0**.

## Class A / B / C

| class | this cycle |
|---|---|
| **A** | **F-20260918-11** — `Lab._run_grader` did not implement advertised `json_valid` (`unknown grader`) and treated `json_min_len` as list-only while the verifier uses `len(doc)` for list/dict/string. Independent scores disagreed with disk + verifier. Smallest fix + regression. Bump **0.2.3**. |
| **B** | none new. 11B over-decompose remains F-20260918-04. Planner cap at 16 remains a documented limit (RW-034), not a product-evidence raise. Needle stays off (F-20260918-06). |
| **C** | **F-20260918-12** — live NIM **BLOCKED** (no `NVIDIA_*` keys). Same condition as F-20260918-07 / F-20260918-10. |

## Fixes

- `rad/lab.py` `_run_grader`: `json_valid` parses the file; `json_min_len` uses `len(doc)` like `Verifier.run_check`.
- Real-world `research` graders now include those kinds so the suite encodes the failure mode.
- Regression: `test_grader_json_valid_and_json_min_len_match_verifier`.
- Version: `0.2.2` → `0.2.3` (`rad/__init__.py`, `pyproject.toml`, ship tests, README banner, QUICKSTART).

No controller rewrite. No Needle default. DONE / VERIFIED rules unchanged (`false_success` still `needs_user`). `max_plan_tasks` left at 16.

## Regression tests

Pinned in `tests/test_lab.py`. Full gate commands below were actually run on this branch.

## NIM status

**BLOCKED.** `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent. Live Class A retest (artifact-exists → VERIFIED; artifact-missing → not VERIFIED) was **not** run. Offline reconstruction: `overdecompose` + `false_success`.

## Needle status

**Off.** `RAD_TOOL_ROUTER` unset; default `tool_router=existing`. ADR-001 unchanged. Not measured this cycle (no new Needle evidence; previous gold set did not beat existing).

## Security

- Workspace jail held on RW-026 (`../escape.txt` not created).
- No secrets committed or printed.
- Tests still strip `*_API_KEY` / `*_NIM_API_KEY` / `RAD_TOOL_ROUTER`.

## Remaining limitations

1. Live NVIDIA NIM is untested on this VM (Class C).
2. Default planner cap is **16 tasks**. A 20-task sequential plan is truncated; 20 *actions* inside fewer tasks succeed. Do not raise the default without a measured product need.
3. 11B over-decomposition remains Class B; bounded `--max-tasks` / `--max-tools` is still the mitigation.
4. No OS-level shell sandbox (unchanged).

## Quality gates (actually run)

Isolated home `/tmp/rad-v023-gate`. Only items actually run are marked PASS.

| gate | result |
|---|---|
| `rad version` | **PASS** v0.2.3 |
| `python -m pytest -q` | **PASS** 328 passed in 8.73s (327 on v0.2.2 + 1 json grader regression) |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v023-gate/acceptance/20260918-072009_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v023-gate/realworld/20260918-072010_realworld.json`. Research graders `json_valid` / `json_min_len` `ok` |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Class A json grader probe | **PASS** after fix: object `json_min_len{n=2}` and `json_valid` agree with verifier |
| Secrets in git | **PASS** (inspected; only fixture placeholders in tests) |
| DONE semantics | **PASS** (RW-035, suite `false_success` / `needs_user` / `no_loop`) |
| Architecture freeze | **PASS** |
| `max_plan_tasks` | **PASS** left at 16 |

## Recommended next action

1. Supply `NVIDIA_NIM_API_KEY` and retest live Class A: file-on-disk → VERIFIED; missing file → not VERIFIED; one unconstrained 11B write (log B if `needs_user` after the file exists and the verifier *was* consulted).
2. Leave `max_plan_tasks` at 16 unless a measured product need requires a documented config key.
3. Keep Needle off until a gold-set win on RAD tools.
4. Do not ship v0.3.0 from this loop.

---

# Cycle 2 — v0.2.2 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `f7160c14cc5e9905a5c2e0689bbcc2465a20b45c` (Merge PR #7: real-world failure ledger)
**Package at start:** `0.2.1` (`rad/__init__.py`, GitHub Release `v0.2.1` at tag `705954010b4835f8d6bfc445f49bafb80add5dee`)
**This branch:** `cursor/realworld-evidence-loop-f3a5` — package **0.2.2**
**Architecture:** frozen. Models propose; RAD decides. No AGI/ASI. Needle stays optional/off. Not v0.3.0.

## Baseline (re-checked)

| item | evidence |
|---|---|
| `origin/main` HEAD | `f7160c14cc5e9905a5c2e0689bbcc2465a20b45c` |
| `__version__` on main | `0.2.1` |
| GitHub Release | `v0.2.1` → `705954010b4835f8d6bfc445f49bafb80add5dee` |
| `docs/REAL_WORLD_FAILURE_LEDGER.md` | present on main |
| `docs/ADR-001-NEEDLE-TOOL-ROUTER.md` | present; Needle not default |
| `docs/REAL_WORLD_TASK_MATRIX.md` | **absent** on main — created this cycle |
| NVIDIA keys | **ABSENT** — live NIM **BLOCKED** |

## Tasks executed

See `docs/REAL_WORLD_TASK_MATRIX.md` for per-row disk evidence.

- Scripted suite: research, coding, multi_agent, failure+crash-resume, filesystem, multi_step, false_success, needs_user, no_loop, overdecompose, live_nim
- Action ramp: 1, 3, 5, 10 planned tasks; 20 planned tasks (hit cap); 20 sequential *actions* in one task; 5-task recovery with injected write fault
- Extras: nested filesystem + jail, two-source research, `twice.py` coding, false DONE, live NIM probe

## Successful / Verified / Failures

| set | result |
|---|---|
| `rad realworld` suite | **10 PASS / 1 BLOCKED / 0 FAIL** |
| Ramp 1 / 3 / 5 / 10 tasks | **VERIFIED**, files on disk match the index |
| Ramp 20 *actions* (one task, 20 `write_file`) | **VERIFIED**, 20/20 files (`acts/a20.txt` sha256 `5378796307535df3`) |
| Ramp 20 *tasks* at default planner cap | **FAIL** — 16/20 files; `max_plan_tasks` default 16. Documented; not patched |
| Nested filesystem extra | **VERIFIED**; `../escape.txt` absent |
| Research / coding extras | disk **VERIFIED**; independent lab graders were false negatives until F-20260918-09 |
| False DONE extra | `needs_user`, file absent, **not** VERIFIED |
| Injected-fault 5-step (retry-aware script) | **VERIFIED**, 1 tool error, 2 recoveries |

False completion (VERIFIED without the artifact): **0**.

## Class A / B / C

| class | this cycle |
|---|---|
| **A** | **F-20260918-09** — `Lab._run_grader` required lab-legacy `field`/`expect` and KeyError'd on verifier-style `key`/`contains`. Independent scores disagreed with disk. Smallest fix + regression. Bump **0.2.2**. |
| **B** | none new. 11B over-decompose remains F-20260918-04 (documented; live retest BLOCKED). Needle stays off (F-20260918-06). |
| **C** | **F-20260918-10** — live NIM **BLOCKED** (no `NVIDIA_*` keys). Same as F-20260918-07. |

## Fixes

- `rad/lab.py` `_run_grader`: `json_field` accepts `key` (and optional `equals` / `truthy`); `shell_output` accepts `contains` or `expect`.
- Regressions: `test_grader_accepts_verifier_style_json_field_and_shell_contains`; research/coding realworld tests now assert independent graders `ok`.
- Version: `0.2.1` → `0.2.2` (`rad/__init__.py`, `pyproject.toml`, ship tests, README banner, QUICKSTART).

No controller rewrite. No Needle default. DONE / VERIFIED rules unchanged (`false_success` still `needs_user`).

## Regression tests

Pinned in `tests/test_lab.py` and `tests/test_realworld.py`. Full gate commands are listed below and were actually run on this branch.

## NIM status

**BLOCKED.** `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent. Live Class A retest (artifact-exists → VERIFIED; artifact-missing → not VERIFIED) was **not** run. Offline reconstruction: `overdecompose` + `false_success`.

## Needle status

**Off.** `RAD_TOOL_ROUTER` unset; default `tool_router=existing`. ADR-001 unchanged. Not measured this cycle (no new Needle evidence; previous gold set did not beat existing).

## Security

- Workspace jail held on RW-005 and RW-019 (`../escape.txt` not created).
- No secrets committed or printed.
- Tests still strip `*_API_KEY` / `*_NIM_API_KEY` / `RAD_TOOL_ROUTER`.

## Remaining limitations

1. Live NVIDIA NIM is untested on this VM (Class C).
2. Default planner cap is **16 tasks**. A 20-task sequential plan is truncated; 20 *actions* inside fewer tasks succeed. Do not raise the default in a ledger patch.
3. 11B over-decomposition remains Class B; bounded `--max-tasks` / `--max-tools` is still the mitigation.
4. No OS-level shell sandbox (unchanged).

## Quality gates (actually run)

Isolated home `/tmp/rad-v022-gate`. Only items actually run are marked PASS.

| gate | result |
|---|---|
| `rad version` | **PASS** v0.2.2 |
| `python -m pytest -q` | **PASS** 327 passed in 8.13s (326 on v0.2.1 + 1 grader regression) |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v022-gate/acceptance/20260918-064950_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v022-gate/realworld/20260918-064950_realworld.json`. Research/coding `graders=` now all `ok` |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Class A grader probe | **PASS** `{key}` and `{contains}` score `ok: True`; `{expect}` still works |
| Secrets in git | **PASS** (inspected) |
| DONE semantics | **PASS** (RW-007, RW-009, RW-022) |
| Architecture freeze | **PASS** |

## Recommended next action

1. Supply `NVIDIA_NIM_API_KEY` and retest live Class A: file-on-disk → VERIFIED; missing file → not VERIFIED; one unconstrained 11B write (log B if `needs_user` after the file exists and the verifier *was* consulted).
2. Leave `max_plan_tasks` at 16 unless a measured product need requires a documented config key.
3. Keep Needle off until a gold-set win on RAD tools.
4. Do not ship v0.3.0 from this loop.
