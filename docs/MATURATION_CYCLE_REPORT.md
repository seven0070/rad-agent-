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

## Evidence for v0.3.0

**None.** No new validated capability was integrated. Needle stays off. The 16-task cap is an existing architecture guard, not a v0.3.0 gap. Stay on 0.2.x.

## Recommended next action

1. Supply `NVIDIA_NIM_API_KEY` and retest live Class A: file-on-disk → VERIFIED; missing file → not VERIFIED; one unconstrained 11B write (log B if `needs_user` after the file exists and the verifier *was* consulted).
2. Leave `max_plan_tasks` at 16 unless a measured product need requires a documented config key.
3. Keep Needle off until a gold-set win on RAD tools.
4. Do not ship v0.3.0 from this loop.

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
