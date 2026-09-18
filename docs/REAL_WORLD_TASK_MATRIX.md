# Real-world task matrix

Factual rows from maturation cycles on disk-checked evidence.
Architecture frozen. Needle stays experimental / off. Not AGI.
Operating spine: [ROADMAP.md](ROADMAP.md). Gen1 complete on 0.2.3; Gen2 in progress.
Verified coding loop is **implemented as v0.3.0** (RW-064). Live NIM retest of that
loop is **RW-065**. Plan-timeout resilience is **implemented as v0.3.1** (scripted
RW-066 / F-27). Live NIM retest of v0.3.1 is **RW-066** (this file; operator
production run). Budget-aware planning is **implemented as v0.3.2** (RW-067).
Do not rewrite RW-058–065. Scripted theme-2 RW-066 (F-27) is preserved.

Every `VERIFIED` / `completed` cell is from the control-plane verifier **and** a disk
check (file exists / contents / hash). A model `DONE:` line is never enough.

Status vocabulary: **PASS** | **FAIL** | **BLOCKED** | **NOT TESTED**.

Live NIM use of v0.3.1 (RW-066) and Gen2 / v0.3.2 (budget-aware planning, RW-067)
are at the top, then v0.3.1 scripted theme 2 and v0.3.0. RW-058–065 are **not rewritten**.

# Live NIM retest of v0.3.1 (RW-066)

Lane: operator production `rad objective run` on **v0.3.1** (tag `v0.3.1`,
`50d98e26`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 4 --max-tools 12`).
RW-058–065 are **not rewritten**. Scripted theme-2 ship evidence remains the
existing RW-066 planning row (F-27) below. This section records the live
production retest the operator labeled RW-066.

Authoritative live facts: operator report for `obj_e74d9fad` /
`/tmp/rad_prod_rw066_0b0bb188`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-066 | 2026-09-18 IST 19:17:44–19:19:18 | coding (live NIM) — v0.3.1 word_counter retest vs RW-065 | word_counter.py + result.json (`words==2`) + test_word_counter.py + tests pass; no DONE: pollution; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=fallback** **attempts=2** (1 mega-task, 0 task checks); t_8e202435 CANCELLED; repair t_4f398815 CANCELLED | tools 12/12; model calls 9/80; retries 1/6; wall ~94s event / spent 41.8s | 12/12 exhausted | **PASS** vs success criteria (`completed` / **VERIFIED**); disk matched | objective **VERIFIED** (`json_valid` result.json; `shell_ok` python3 test_word_counter.py, 2 tests OK). Task verify FAILED then cancelled: “objective machine checks already satisfied (budget exhausted)” | Gen2 **YES** — `RECOVERY_DECISION` `strategy=repair` `failure_class=ENVIRONMENT_FAILURE`; repair wrote fixed `word_counter.py` + valid `result.json`; budget cut mid further writes | **B** residual (11B plan/coding@12). Theme 2 **live-confirmed**. Low-urgency CANCELLED+VERIFIED UX when objective checks already satisfied | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw066_0b0bb188`; `obj_e74d9fad`. Disk: `word_counter.py` YES (space-count+1 → 2); `result.json` **valid** `{"words": 2}`; `test_word_counter.py` YES; host tests **PASS** (2 OK); DONE pollution **NONE**. False DONE **0**. vs RW-065: **better E2E** (065 `needs_user` / tests FAIL). Caps unchanged. Needle OFF. Theme 3 still relevant (tools exhausted mid-repair). |

### RW-066 vs RW-065 (same 11B / tools=12 control)

| | RW-065 (v0.3.0) | RW-066 (v0.3.1 live) |
|---|---|---|
| home | `/tmp/rad_prod_rw065_ab0919b2` | `/tmp/rad_prod_rw066_0b0bb188` |
| objective id | `obj_efed5285` | `obj_e74d9fad` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` / `--max-tools` | 4 / 12 | 4 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** (4 tasks w/ checks) | **fallback** (1 mega-task, 0 task checks) |
| PLAN attempts | *(field absent)* | **2** then fallback |
| Gen2 repair insert | **YES** | **YES** |
| `result.json` | valid `{"words": 2}` | valid `{"words": 2}` |
| Tests (host) | **FAIL** (NameError / broken counter) | **PASS** (2 OK) |
| DONE pollution | NO | NO |
| false DONE | **0** | **0** |
| final status | `needs_user` / FAIL | **`completed` / VERIFIED** |
| end-to-end PASS | No | **Yes** |
| class | **B** (F-25); json_valid-on-.py **NOT CONFIRMED** (F-26) | **B** residual (11B@12); theme 2 live-confirmed |

| metric | value |
|---|---|
| Package (live run) | **0.3.1** (tag `v0.3.1` / `50d98e26`) |
| Theme 2 (plan-timeout resilience) | **used / live-confirmed** — `attempts=2` then `source=fallback` |
| Theme 1 (verified coding loop) | **used** — repair YES; valid JSON; tests PASS; no DONE pollution |
| Residual | **Class B** — 11B plan/coding@12; tools 12/12 mid-repair; CANCELLED+VERIFIED when objective checks already satisfied (low urgency; not false DONE) |
| RW-058–065 | preserved (not rewritten) |
| Scripted RW-066 (F-27) | preserved (theme 2 ship evidence) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 4 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **PASS**. Theme 3 (budget-aware planning) still relevant; do not raise caps. |

# Gen2 — v0.3.2 budget-aware planning (RW-067)

Lane: Cloud Agent, deterministic/scripted. Live NIM optional (BLOCKED if no key).
Package **0.3.1 → 0.3.2**. Needle `existing` / off. `max_plan_tasks` **16**.
Default `Budget.tool_calls` **60**. Default plan retries **1** (hard cap 3).
F-17 fallback contract **unchanged** (goal-only clause split, cap 7, no checks).
F-21 leftover-work contract **unchanged** (≤3-task LLM graphs are not compacted).
Does **not** claim live 11B Class B coding is solved. Does **not** reopen F-17 / F-26.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-067 | 2026-09-18 | planning (scripted) — budget-aware planning | Fat 8-task LLM plan vs remaining N=6 tools; fallback 7-clause vs N=4 | fat→fit: 2 llm tasks with checks (estimated 4 ≤ 6); fallback compact: 2 tasks, no checks | plan only (plus bounded drive for false-DONE) | default **60** unchanged | **PASS** fat-then-fit is selected; two fat plans pick cheaper; fallback compact fits N; small 3-task LLM plan with remaining=1 stays 3 (F-21); default-60 fallback stays 7 | LLM path keeps checks; compacted fallback UNVERIFIED; objective not VERIFIED without checks | n/a (plan-time select/compact, not recovery) | capability (Gen2 theme 3) | Tests `tests/test_budget_aware_planning.py`. Needle OFF. Caps unchanged. False DONE **0**. F-17 / F-21 / F-26 preserved. Live NIM not required. |

| metric | value |
|---|---|
| Package | **0.3.2** |
| Theme | Gen2 #3 budget-aware planning |
| Needle | **OFF** (`existing`) |
| `max_plan_tasks` | **16** unchanged |
| Default tool budget | **60** unchanged |
| Default plan retries | **1** (hard cap **3**) |
| False completion | **0** |
| RW-058–065 | preserved (not rewritten) |
| Scripted RW-066 (F-27) | preserved |
| Live RW-066 | preserved (PASS; residual Class B) |
| Live NIM this patch | **BLOCKED** if no key — not a live PASS claim for theme 3 |
| Claim all Class B coding solved | **NO** |

# Gen2 — v0.3.1 plan-timeout resilience (RW-066)


Lane: Cloud Agent, deterministic/scripted. Live NIM optional (BLOCKED if no key).
Package **0.3.0 → 0.3.1**. Needle `existing` / off. `max_plan_tasks` **16**.
Default `Budget.tool_calls` **60**. Default plan retries **1** (hard cap 3).
F-17 fallback contract **unchanged** (goal-only clause split, cap 7, no checks).
Does **not** claim RW-062 / RW-065 live 11B would now PASS.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-066 | 2026-09-18 | planning (scripted) — plan-timeout resilience | First plan call TimeoutError / empty / malformed; second call valid JSON with checks | timeout→JSON: 2 llm tasks with checks; exhausted: 7 fallback, no checks | plan only (plus bounded drive for false-DONE) | default **60** unchanged | **PASS** timeout-then-JSON is `source=llm`; exhausted is `source=fallback` F-17; first-try JSON still 1 attempt | LLM path keeps checks; fallback UNVERIFIED; objective not VERIFIED without checks | n/a (plan-time retry, not recovery) | capability (Gen2 theme 2) | Tests `tests/test_plan_timeout_resilience.py`. Needle OFF. Caps unchanged. False DONE **0**. F-17 preserved. Live NIM not required. |

| metric | value |
|---|---|
| Package | **0.3.1** |
| Theme | Gen2 #2 plan-timeout resilience |
| Needle | **OFF** (`existing`) |
| `max_plan_tasks` | **16** unchanged |
| Default tool budget | **60** unchanged |
| Default plan retries | **1** (hard cap **3**) |
| False completion | **0** |
| RW-058–065 | preserved (not rewritten) |
| Live NIM | **BLOCKED** (no `NVIDIA_NIM_API_KEY`) |
| Claim RW-062/065 live PASS | **NO** |

# Gen2 — v0.3.0 verified coding loop (RW-064)

Lane: Cloud Agent, deterministic/scripted. Live NIM optional (BLOCKED if no key).
Package **0.2.3 → 0.3.0**. Needle `existing` / off. `max_plan_tasks` **16**.
Default `Budget.tool_calls` **60**. Control plane unchanged in shape
(PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER).

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-064 | 2026-09-18 | coding (scripted) — verified coding loop | word_counter-like: `result.json` + `test_word_counter.py`; first write is invalid `{` / words `6`; repair must fix to `words==2` | 1 planned + 1 repair | write → json_valid/shell fail → repair → retry | default **60** unchanged | **PASS** (repair path VERIFIED); persistent-bad **PASS** (not VERIFIED) | repair path **VERIFIED** from disk; persistent `{` / `DONE:` pollution **not** VERIFIED | VALIDATION/TOOL → **repair** with concrete failure (not ENVIRONMENT); missing `file_exists` still retry_with_hint | capability (Gen2) | Tests `test_verified_coding_loop_*`. False DONE **0**. Fallback tasks still have no checks (F-17); coding goals infer *objective* `json_valid` + test `shell_ok`. Needle OFF. Caps unchanged. Live NIM not required. RW-058/062 Class B live facts preserved. |

| metric | value |
|---|---|
| Package | **0.3.0** |
| Theme | Gen2 #1 verified coding loop |
| Needle | **OFF** (`existing`) |
| `max_plan_tasks` | **16** unchanged |
| Default tool budget | **60** unchanged |
| False completion | **0** |
| RW-058–063 | preserved (not rewritten) |
| Live NIM | **BLOCKED** (no `NVIDIA_NIM_API_KEY`) |

# Live NIM retest of v0.3.0 (RW-065)

Lane: operator production `rad objective run` on **v0.3.0** (tag `v0.3.0`,
`183ff611`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 4 --max-tools 12`).
RW-058–064 are **not rewritten**. **Not** an end-to-end PASS. Package stays
**0.3.0** (json_valid-on-.py Class A **NOT CONFIRMED**; no 0.3.1).

Authoritative live facts: operator report for `obj_efed5285` /
`/tmp/rad_prod_rw065_ab0919b2`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-065 | 2026-09-18 IST 18:46:10–18:47:36 | coding (live NIM) — v0.3.0 word_counter retest vs RW-062 | word_counter.py + result.json (`words==2`) + test_word_counter.py + tests pass; no DONE: pollution; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** (4 tasks); t_8ca54965 RETRYING; t_1c465c51 COMPLETED/VERIFIED; tests+run PENDING; repair t_6b2926a5 RUNNING at stop | tools 12/12; model calls 9/80; retries 1/6; wall ~86s event / spent 66.7s | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED on first task (actions errors + `json_valid` on `.py`); objective `json_min_len` on `result.json` registered, not VERIFIED | Gen2 **YES** — `RECOVERY_DECISION` `strategy=repair` `failure_class=ENVIRONMENT_FAILURE` (“missing dependency/file”); repair cut off by tool budget | **B** primary (11B/budget); json_valid-on-.py Class A **NOT CONFIRMED** (F-20260918-26) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw065_ab0919b2`; `obj_efed5285`. Disk: `word_counter.py` YES (broken `s.split().count()` TypeError); `result.json` **valid** `{"words": 2}`; `test_word_counter.py` YES (NameError, no import); DONE pollution **NONE**. Tests **FAIL**. False DONE **0**. vs RW-062: **improved** (llm plan, Gen2 repair, valid JSON, no DONE pollution) but not E2E PASS. Caps unchanged. Needle OFF. **No v0.3.1.** |

### RW-065 vs RW-062 (same 11B / tools=12 control)

| | RW-062 (v0.2.3) | RW-065 (v0.3.0) |
|---|---|---|
| home | `/tmp/rad_prod_rw062_6ede431b` | `/tmp/rad_prod_rw065_ab0919b2` |
| objective id | `obj_7a020865` | `obj_efed5285` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` / `--max-tools` | 4 / 12 | 4 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **fallback** (7 clause-split tasks) | **llm** (4 coherent tasks) |
| Gen2 repair insert | No | **YES** (`RECOVERY_DECISION` → `t_6b2926a5`) |
| `result.json` | invalid `{` | **valid `{"words": 2}`** |
| Tests | FAIL `6 != 2` | FAIL `NameError` / broken counter |
| DONE pollution | YES (`DONE:` fake path) | **NO** |
| false DONE | **0** | **0** |
| final status | `needs_user` / FAIL | `needs_user` / FAIL |
| end-to-end PASS | No | No |
| class | **B** (F-22) | **B** (F-25); json_valid-on-.py **NOT CONFIRMED** (F-26) |

| metric | value |
|---|---|
| Package | **0.3.0** — no bump; **no v0.3.1** |
| Theme 1 (verified coding loop) | **used** — repair fired; valid JSON; no DONE pollution |
| Residual | **Class B** — 11B + tools=12 exhausted mid-repair; tests FAIL; not E2E PASS |
| Class A json_valid-on-.py | **NOT CONFIRMED** — see ledger F-20260918-26 / `tests/test_json_valid_py_investigation.py` |
| RW-058–064 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 4 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | **stay 0.3.0** — document live use; do not claim coding PASS on 11B@12 |

# Cycle 2 (post-v0.2.1 → package **0.2.2**)

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `f7160c14cc5e9905a5c2e0689bbcc2465a20b45c` (Merge PR #7).
Release tag `v0.2.1` → `705954010b4835f8d6bfc445f49bafb80add5dee`.

## Scripted `rad realworld` suite

Command: `RealWorldSuite(home).run()` (isolated `/tmp/rad_rw_suite_*`). Evidence:
`/tmp/rad_rw_suite_kw6po5nj/realworld/20260918-064637_realworld.json`.

| id | area | actions (approx) | disk | status | verified | result | class | notes |
|---|---|---|---|---|---|---|---|---|
| RW-001 | research | ~3 tasks + network fault | `report.json` sha256 `0a45c9e59ae640f3` (1053 B); both prices 42 and 57; conflict recorded | completed | VERIFIED | **PASS** | — | Independent disk checks 9/9. Lab grader `json_field{key}` was a false negative before F-20260918-09 |
| RW-002 | coding | inspect → naive fix → repair | `pkg/stats.py` sha256 `68c46b7e404d7117`; `tests/check_stats.py` hash unchanged; stdout `ALL TESTS PASSED` | completed | VERIFIED | **PASS** | — | Injected `run_shell` fault recovered. Lab grader `shell_output{contains}` was a false negative before F-20260918-09 |
| RW-003 | multi-agent | researcher / writer / reviewer | `answer.md` sha256 `3e80d1d8f8e934c0`; readings 42, 39, 12; no invented 500 | completed | VERIFIED | **PASS** | — | Reviewer is a different agent; machine checks complete |
| RW-004 | recovery | injected faults + crash-resume | `summary.json` sha256 `d1bd5d677ce9ed65`; count=4 mean=33.75; four `out/stepN.txt` after resume | completed | VERIFIED | **PASS** | — | Checkpoint restore; finished work kept |
| RW-005 | filesystem | nested write + copy + jail | `nest/a/note.txt` and `nest/b/note.txt` sha256 `b6a98d9ce9a2d914` (`alpha`); `../escape.txt` absent | completed | VERIFIED | **PASS** | — | Workspace jail held |
| RW-006 | multi-step | A→B→C | `stepA.txt`/`stepB.txt`/`stepC.txt` hashes `559aead0` / `df7e70e5` / `6b23c0d5` | completed | VERIFIED | **PASS** | — | Three dependent artifacts |
| RW-007 | false completion | `DONE:` without write | `honest.txt` **absent** | needs_user | (not VERIFIED) | **PASS** | — | DONE semantics held |
| RW-008 | needs_user | missing staging host | `published.txt` **absent** | needs_user | (not VERIFIED) | **PASS** | — | Escalated; no invented publish |
| RW-009 | no_loop | persistent false DONE | `missing.txt` **absent** | needs_user | (not VERIFIED) | **PASS** | — | Retry budget respected |
| RW-010 | overdecompose | extra README/backup tasks; tool budget 1 | `live_hello.txt` sha256 `5891b5b522d5df08` contains `hello` | completed | VERIFIED | **PASS** | A (already fixed v0.2.1) | Completes from machine checks, not a DONE claim |
| RW-011 | live NIM | live `objective run` | — | blocked | — | **BLOCKED** | **C** | Both NVIDIA env vars absent |

Suite: **10 passed / 1 BLOCKED / 0 failed**.

## Action ramp (1 → 3 → 5 → 10 → 20)

Sequential `write_file` through the real control plane. Disk-verified each index file.

| id | planned | actions on disk | status | verified | result | class | notes |
|---|---|---|---|---|---|---|---|
| RW-012 | 1 task / 1 write | `steps/s01.txt` = `1` | completed | VERIFIED | **PASS** | — | |
| RW-013 | 3 tasks / 3 writes | `s01`–`s03` correct | completed | VERIFIED | **PASS** | — | |
| RW-014 | 5 tasks / 5 writes | `s01`–`s05` correct | completed | VERIFIED | **PASS** | — | |
| RW-015 | 10 tasks / 10 writes | `s01`–`s10` correct | completed | VERIFIED | **PASS** | — | |
| RW-016 | 20 **tasks** / 20 writes | **16** files (`s01`–`s16`); `s17`–`s20` absent | failed | FAILED | **FAIL** (expected cap) | — | Planner `max_plan_tasks` default **16** silently drops the rest. Not raised this cycle (architecture frozen; prompt says never more than 16). See limitations |
| RW-017 | 1 task / **20 writes** | `acts/a01.txt` … `acts/a20.txt` (20/20); `a20` sha256 `5378796307535df3` | completed | VERIFIED | **PASS** | — | Twenty *actions* fit under the 16-task guard |
| RW-018 | 5 tasks + injected `write_file` fault, retry-aware script | 5/5 files; 1 tool error; 2 recoveries | completed | VERIFIED | **PASS** | — | Naive script (no replay line) ended `needs_user` — campaign script, not a RAD hole |

## Extra campaign (same VM)

| id | area | disk | status | verified | result | class | notes |
|---|---|---|---|---|---|---|---|
| RW-019 | filesystem (deeper nest) | `data/raw/a.txt` + `data/curated/a.txt` contain `alpha`; `../escape.txt` absent | completed | VERIFIED | **PASS** | — | Jail held |
| RW-020 | research (two-source price) | `cmp.json` claims 10 and 12, both sourced; `conflicts` present | completed | VERIFIED | **PASS** | A (F-20260918-09) | Before the fix, lab grader `json_field{key}` → `grader error: 'field'` while disk + verifier were already correct |
| RW-021 | coding (`twice.py`) | `python3 check.py` → `ALL TESTS PASSED`; `check.py` hash unchanged | completed | VERIFIED | **PASS** | A (F-20260918-09) | Before the fix, lab grader `shell_output{contains}` → `grader error: 'expect'` |
| RW-022 | false DONE | `proof.txt` absent | needs_user | (not VERIFIED) | **PASS** | — | DONE semantics held |
| RW-023 | live NIM Class A retest | — | blocked | — | **BLOCKED** | **C** | Same missing keys as RW-011. Offline reconstruction remains `overdecompose` / `false_success` |

## Metrics (this cycle, honest)

| metric | value |
|---|---|
| Suite runnable PASS | 10/10 (plus 1 BLOCKED live NIM) |
| False completion (VERIFIED without the artifact) | **0** |
| Independent lab-grader false negatives on RW-020 / RW-021 (pre-fix) | **2** (Class A; **fixed** — post-fix `rad realworld` research/coding graders all `ok`) |
| 20 sequential *actions* | **VERIFIED** (RW-017) |
| 20 sequential *planned tasks* at default cap | **FAILED** at 16 (RW-016) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |

Do not add rows without a disk check or an honest BLOCKED/NOT TESTED mark.

---

# Cycle 3 (post-v0.2.2 → package **0.2.3**)

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `8d9e196aa730c7bfeae7e501f44004078f080b61` (PR #8 / Release `v0.2.2`).
Needle stays experimental / off. Not AGI. No v0.3.0. Planner cap left at 16.

Evidence: `/tmp/rad-c3-evidence/campaign.json`. Control-plane verifier **and** a disk check for every `VERIFIED` cell.

## Production campaign (genuine useful work)

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-024 | 2026-09-18 | coding | `pkg/avg.py` `mean_by_region` + `tests/check_avg.py` | 2 | 2 | write_file, run_shell | **PASS** | VERIFIED | none | — | `pkg/avg.py` sha256 `111ed94abb1bce8f`; tests hash `616a5feda63b6489` unchanged; stdout `ALL TESTS PASSED` |
| RW-025 | 2026-09-18 | research | two lab notebooks → `compare.json` with sourced pH conflict | 2 | 3 | read_file, write_file | **PASS** | VERIFIED | none | A (F-20260918-11) | `compare.json` sha256 `3b8f1e6a8b43a214`; both 6.8 and 8.1 sourced. Pre-fix `json_valid` grader `unknown grader`; post-fix `ok` |
| RW-026 | 2026-09-18 | filesystem | sort inbox into `docs/` + `data/` + index; jail | 3 | 4 | run_shell, write_file | **PASS** | VERIFIED | none | — | `data/index.txt` sha256 `2e6256058b614820`; `../escape.txt` absent |
| RW-027 | 2026-09-18 | multi-step | `app.log` → `counts.json` (error=3) → `summary.md` | 2 | 4 | read_file, write_file | **PASS** | VERIFIED | none | — | `counts.json` sha256 `25e1d36b1f2772ea`; `summary.md` sha256 `343bf41f1bf64c71` |
| RW-028 | 2026-09-18 | recovery | write `config/settings.json` with injected `write_file` fault | 1 | 2 | write_file | **PASS** | VERIFIED | 1 tool error, 2 recoveries | A (F-20260918-11) | sha256 `2b3a56a5f55ff76f`; pre-fix `json_valid` grader unknown; post-fix `ok` |
| RW-035 | 2026-09-18 | recovery | `DONE:` without writing `proof.txt` | 1 | 0 | (none) | **PASS** | (not VERIFIED) | retry then escalate | — | status `needs_user`; file **absent** |
| RW-036 | 2026-09-18 | recovery | crash after `pipe/p1.txt`, restore, resume p2–p3 | 3 | crash+resume | write_file | **PASS** | VERIFIED | checkpoint restore | — | hashes `5509d3b83b2db7d3` / `a652f5bf7a9c5936` / `6153dd17d3a9573f` |
| RW-037 | 2026-09-18 | live NIM | live `objective run` | 0 | 0 | — | **BLOCKED** | — | — | **C** | both NVIDIA env vars absent |
| RW-038 | 2026-09-18 | coding | `inventory.json` object; advertised `json_min_len{n=2}` + `json_valid` | 1 | 1 | write_file | **PASS** (post-fix) | VERIFIED | none | **A** (F-20260918-11) | sha256 `31d4c9f7af644d06`. Pre-fix: verifier ok, grader `json_min_len` list-only + `json_valid` unknown. Post-fix: graders agree |
| RW-039 | 2026-09-18 | needle | default router | 0 | 0 | — | **PASS** | n/a | — | — | `RAD_TOOL_ROUTER` unset; `resolve_tool_router` = `existing`. Router **NOT TESTED** |

## Action ramp (1 → 3 → 5 → 10 → 20)

Sequential inventory SKU `write_file` through the real control plane. Disk-verified each index file.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-029 | 2026-09-18 | multi-step | 1 SKU file | 1 | 1 | write_file | **PASS** | VERIFIED | none | — | `inv/s01.txt` sha256 `2da4679aa46b0db3` |
| RW-030 | 2026-09-18 | multi-step | 3 SKU files | 3 | 3 | write_file | **PASS** | VERIFIED | none | — | `inv/s03.txt` sha256 `8db9ba36bc13ec3a` |
| RW-031 | 2026-09-18 | multi-step | 5 SKU files | 5 | 5 | write_file | **PASS** | VERIFIED | none | — | `inv/s05.txt` sha256 `907e3cb7bc73ebc2` |
| RW-032 | 2026-09-18 | multi-step | 10 SKU files | 10 | 10 | write_file | **PASS** | VERIFIED | none | — | `inv/s10.txt` sha256 `db9b15433ec51d25` |
| RW-033 | 2026-09-18 | filesystem | 20 writes in **one** planned task | 1 | 20 | write_file | **PASS** | VERIFIED | none | — | 20/20; `inv/s20.txt` sha256 `14e88a9299fed78c` |
| RW-034 | 2026-09-18 | multi-step | 20 **planned tasks** / 20 writes | 16 | 16 | write_file | **FAIL** (expected cap) | FAILED | none | — | 16/20 files (`s01`–`s16`); `s17`–`s20` absent. `max_plan_tasks` default **16**. Not raised |

## Cycle 3 metrics (honest)

| metric | value |
|---|---|
| Suite runnable PASS | 10/10 (plus 1 BLOCKED live NIM) |
| Campaign PASS / FAIL / BLOCKED | **14 / 1 / 1** (the FAIL is RW-034 expected cap) |
| False completion (VERIFIED without the artifact) | **0** |
| Independent grader false negatives (pre-fix json_valid / json_min_len) | **Class A; fixed** — post-fix RW-025 / RW-028 / RW-038 / suite research graders all `ok` |
| 20 sequential *actions* | **VERIFIED** (RW-033) |
| 20 sequential *planned tasks* at default cap | **FAILED** at 16 (RW-034) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |

---

# Cycle 4 (post-v0.2.3 release verification → package **0.2.3**, no bump)

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` (Merge PR #9 / GitHub Release `v0.2.3`).
**Release: PASS** — tag `v0.2.3` peels to that SHA; `pyproject.toml` / `rad.__version__` = `0.2.3`; release URL live. Not re-cut. Not retagged. Not v0.3.0.
Needle stays experimental / off. Planner cap left at **16**.

Evidence: `/tmp/rad-c4-evidence/campaign.json`. Control-plane verifier **and** a disk check for every `VERIFIED` cell.

## Production campaign (genuine useful work)

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-040 | 2026-09-18 | coding | `pkg/tally.py` `tally_by_sku` + `tests/check_tally.py` | 2 | 2 | write_file, run_shell | **PASS** | VERIFIED | none | — | `pkg/tally.py` sha256 `5e3aedff9a7dec82`; tests hash `aae8b0ad78917a3d` unchanged; stdout `ALL TESTS PASSED` |
| RW-041 | 2026-09-18 | research | two warehouse counts → `stock.json` with sourced on-hand conflict | 2 | 3 | read_file, run_shell | **PASS** | VERIFIED | none | — | `stock.json` sha256 `14911ec4fb461f3c`; both 120 and 87 sourced; `conflicts` present; `json_valid` / `json_min_len` graders `ok` |
| RW-042 | 2026-09-18 | filesystem | sort `inbox/` into `archive/notes/` + `archive/tables/` + manifest; jail | 2 | 3 | run_shell, write_file | **PASS** | VERIFIED | none | — | `archive/manifest.txt` sha256 `bdd78a6b815e36e1`; `../escape.txt` absent |
| RW-043 | 2026-09-18 | multi-step | `access.log` → `status.json` (errors=3) → `digest.md` | 2 | 3 | read_file, run_shell | **PASS** | VERIFIED | none | — | `status.json` sha256 `bbbaa1a0d9ee991c`; `digest.md` sha256 `3a443b870c3810dd` |
| RW-044 | 2026-09-18 | recovery | write `config/limits.json` with injected `write_file` fault | 1 | 2 | write_file | **PASS** | VERIFIED | 1 tool error, 2 recoveries | — | sha256 `f96a9e62d8b15f53`; retry-aware script; graders `ok` |
| RW-045 | 2026-09-18 | recovery | `DONE:` without writing `receipt.txt` | 1 | 0 | (none) | **PASS** | (not VERIFIED) | retry then escalate | — | status `needs_user`; file **absent** |
| RW-046 | 2026-09-18 | recovery | crash after `stage/s1.txt`, restore, resume s2–s3 | 3 | crash+resume | write_file | **PASS** | VERIFIED | checkpoint restore | — | hashes `5509d3b83b2db7d3` / `a652f5bf7a9c5936` / `6153dd17d3a9573f` |
| RW-047 | 2026-09-18 | live NIM | live `objective run` | 0 | 0 | — | **BLOCKED** | — | — | **C** | both NVIDIA env vars absent |
| RW-048 | 2026-09-18 | needle | default router | 0 | 0 | — | **PASS** | n/a | — | — | `RAD_TOOL_ROUTER` unset; `resolve_tool_router` = `existing`. Router **NOT TESTED** |
| RW-057 | 2026-09-18 | coding | lab grader vs verifier parity on advertised disk check kinds | 0 | 0 | — | **PASS** | n/a | — | — | `file_exists` / `file_min_bytes` / `file_contains` / `json_*` / `shell_*` all agree. No new Class A |

## Action ramp (1 → 3 → 5 → 10 → 20)

Sequential lot-SKU `write_file` through the real control plane. Disk-verified each index file.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-049 | 2026-09-18 | multi-step | 1 lot file | 1 | 1 | write_file | **PASS** | VERIFIED | none | — | `lot/l01.txt` sha256 `589763d29bd18d85` |
| RW-050 | 2026-09-18 | multi-step | 3 lot files | 3 | 3 | write_file | **PASS** | VERIFIED | none | — | `lot/l03.txt` sha256 `ff2178359cc8e165` |
| RW-051 | 2026-09-18 | multi-step | 5 lot files | 5 | 5 | write_file | **PASS** | VERIFIED | none | — | `lot/l05.txt` sha256 `77a02b0c67fbd5ac` |
| RW-052 | 2026-09-18 | multi-step | 10 lot files | 10 | 10 | write_file | **PASS** | VERIFIED | none | — | `lot/l10.txt` sha256 `d8434e146b2020bb` |
| RW-053 | 2026-09-18 | filesystem | 20 writes in **one** planned task | 1 | 20 | write_file | **PASS** | VERIFIED | none | — | 20/20; `lot/l20.txt` sha256 `94b5d8fbf6758812` |
| RW-054 | 2026-09-18 | multi-step | 20 **planned tasks** / 20 writes | 16 | 16 | write_file | **FAIL** (expected cap) | FAILED | none | — | 16/20 files (`l01`–`l16`); `l17`–`l20` absent. `max_plan_tasks` default **16**. Not raised |

## `max_plan_tasks=16` evidence-test

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-055 | 2026-09-18 | multi-step | 16-bin warehouse labels (exactly the cap) | 16 | 16 | write_file | **PASS** | VERIFIED | none | — | 16/16; `bins/b16.txt` sha256 `201ffddc49fb2261`. Cap is **not** a blocker at exactly 16 |
| RW-056 | 2026-09-18 | multi-step | 17-bin warehouse labels (one past the cap) | 16 | 16 | write_file | **FAIL** (expected cap) | FAILED | none | — | 16/17; `bins/b17.txt` **absent**. Planner silently kept `items[:16]`. Useful work blocked only as one-file-per-task; bundling (RW-053) writes 20 files under 1 task |

### Planner hit 16 vs useful-work failure because of the cap

| | count | rows |
|---|---|---|
| Planner **hit** 16 (tasks 17+ dropped before the graph) | **2** | RW-054, RW-056 |
| Useful work **failed because of** the cap | **0** | coding/research/fs/multi-step/recovery all used 1–3 tasks and **VERIFIED**; 20 *actions* in 1 task **VERIFIED** (RW-053); exactly-16 labels **VERIFIED** (RW-055) |

Do not raise `max_plan_tasks`. A cap *encounter* is not a product failure.

## Cycle 4 metrics (honest)

| metric | value |
|---|---|
| GitHub Release `v0.2.3` | **PASS** (already live on `d121c3f`; not re-cut) |
| Suite runnable PASS | 10/10 (plus 1 BLOCKED live NIM) |
| Campaign PASS / FAIL / BLOCKED | **15 / 2 / 1** (the FAILs are RW-054 and RW-056 expected cap) |
| False completion (VERIFIED without the artifact) | **0** |
| New Class A | **none** — grader/verifier advertised disk kinds still agree (RW-057) |
| 20 sequential *actions* | **VERIFIED** (RW-053) |
| 16 sequential planned tasks | **VERIFIED** (RW-055) |
| 17 / 20 sequential planned tasks at default cap | **FAILED** at 16 (RW-056 / RW-054) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |
| Package / architecture | **0.2.3** frozen; **not v0.3.0** |
| Planner-cap encounters vs useful-work failures | **2 encounters / 0 useful-work failures** |
| Recommendation | **Outcome A — continue 0.2.x** (not B: no Class A patch; not C: no proven v0.3.0 gap) |

### Decision gate (this cycle only)

| # | question | answer |
|---|---|---|
| A | v0.2.3 stable? | **YES** |
| B | Recurring Class A? | **NO** this cycle |
| C | Cap prevents useful work? | **NO** (2 planner hits; 0 useful-work failures) |
| D | 11B still model limitation? | **NOT TESTED** this cycle (NIM BLOCKED) |
| E | Needle earned default? | **NO** |
| F | NIM | **BLOCKED** |
| G | Proven architectural gap? | **NO** |
| H | v0.3.0 justified? | **NO** |

---

# Production use (post-Cycle 4) — package **0.2.3**, no bump

Lane: operator production `rad objective run` on **v0.2.3**. Architecture frozen. Needle stays
experimental / off. Planner cap left at **16**. Not v0.3.0. **No 0.2.x bump.**

These rows are **not** Cycle 4 campaign evidence. Cycle 4 live NIM remained **BLOCKED** on the
Cloud Agent VM (no keys). This is a later operator run.

RW-058 remains historical evidence and is not rewritten. RW-059 is a controlled
`--max-tools 24` follow-up of the same text_analyzer objective (default max-tools **not**
raised). RW-060 is a separate research + artifact objective on the same 11B NIM
lane (not a rewrite of RW-058/059). RW-061 is the scripted Class A investigation
(PR #14). RW-062 is a live Simple Coding + Verification control on the same 11B
NIM lane (not a rewrite of RW-058–061). Default max-tools / max-tasks **not** raised.

## Production campaign (text_analyzer)

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-058a | 2026-09-18 | live NIM (no brain) | production text_analyzer (earlier attempt) | 7 planned / 1 attempted / 0 completed | 0 | 0/12 | **BLOCKED** | — | — | **C** | Home `/tmp/rad_prod_text_analyzer_f3cc7950`; `obj_442301c7`; rad v0.2.3. `MODEL_FAILURE` — no NVIDIA/other keys / no local engine. Workspace empty. False DONE **0**. Same condition family as F-20260918-08 / F-20260918-13 |
| RW-058 | 2026-09-18 IST ~13:39–13:41 | coding (live NIM) | `text_analyzer/{analyzer.py,input.txt,summary.json,test_analyzer.py,README.md}`; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12` | 5 planned; 1 attempted (verification FAILED, 2 attempts); 4 PENDING | tools 12/12; model calls 7/80; wall ~103s | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | user chose stop; no resume | **B** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct` (NIM key present; Class C closed for this attempt). Home `/tmp/rad_prod_text_analyzer_live_a787512c`; `obj_4e219224`. Disk: `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`; `analyzer.py` computes counts; `test_analyzer.py` byte-identical to `analyzer.py` (0 tests); README present; `text_analyzer/summary.json` **MISSING**; workspace-root `summary.json` had correct counts `{lines:3,words:13,characters:76}` (wrong path); layout pollution at workspace root. 11B tool spam / incomplete layout / duplicated "tests" / path confusion. **Not Class A**: RAD stopped at tool budget; false DONE **0**; verifier did not rubber-stamp. Bounded `--max-tasks 8 --max-tools 12`. No architecture change |
| RW-059 | 2026-09-18 IST ~14:02–14:04 | coding (live NIM) — controlled tool-budget | same text_analyzer layout as RW-058; stdlib; `--max-tasks 8 --max-tools 24`; Needle `existing` / off | max-tasks 8 | tools 24/24 (`write_file` 19, `run_shell` 5); model calls 25/80; wall ~106s | 24/24 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | budget exhausted | **B** (tool-budget hypothesis **Case B**); Class A candidates **open/investigate**, **not patched** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw059_b48e7b56`; `obj_e1419520`. Disk: all five files present under `text_analyzer/`; `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` (same as RW-058); `summary.json` **invalid JSON** + wrong counts; tests **FAIL** `13!=6`. False DONE **0**. Doubling 12→24 did not complete the objective. Default max-tools **not** raised. No architecture change. **No v0.2.4.** |

## Production metrics (honest)

| metric | value |
|---|---|
| Package / architecture | **0.2.3** frozen; **not v0.3.0**; **no v0.2.4** (no Class A) |
| Attempt 1 (no brain) | **BLOCKED** Class C (RW-058a) |
| Attempt 2 (live NIM 11B) | **FAIL** Class B (RW-058) — `needs_user`; success criteria unmet |
| False completion (VERIFIED without the artifact) | **0** |
| Class A | **none** |
| Live NIM (this operator run) | Attempt 1 Class C; attempt 2 key present (Class C closed for that attempt) and incomplete vs layout |
| 11B model limitation | **documented live** — tool budget exhausted; incomplete layout (F-20260918-15) |
| Needle | stays `existing` / off; **not measured** this run |
| `max_plan_tasks` | **16** unchanged (this run used `--max-tasks 8`) |
| Recommendation | **Outcome A — continue 0.2.x** (not B: no Class A patch; not C: no proven v0.3.0 gap) |

## Controlled tool-budget experiment (RW-059 vs RW-058)

RW-058 is left unchanged as historical evidence. RW-059 is the same production
text_analyzer objective with **only** `--max-tools` doubled (12 → 24). Default
max-tools is **not** raised. Package stays **0.2.3**.

| | RW-058 (historical) | RW-059 (this experiment) |
|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` |
| objective id | `obj_4e219224` | `obj_e1419520` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` | 8 | 8 |
| `--max-tools` | **12** | **24** (run only; default unchanged) |
| Needle | `existing` / off | `existing` / off |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 |
| tools used | 12/12 exhausted | 24/24 exhausted (`write_file` 19, `run_shell` 5) |
| model calls | 7/80 | 25/80 |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** |
| disk | 4/5 under `text_analyzer/`; `summary.json` **MISSING** (root file had correct counts, wrong path) | all five files under `text_analyzer/`; `summary.json` invalid JSON + wrong counts; tests **FAIL** `13!=6` |
| `input.txt` sha256 | `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` | same |

| metric | value |
|---|---|
| Tool-budget hypothesis | **Case B** — 24 did **not** suffice (both runs exhausted budget; both `needs_user` / FAIL) |
| Class A this experiment | **not patched.** Suspected candidates **open/investigate** (F-20260918-17, F-20260918-18). Do not treat as fixed |
| Class B remaining | invalid JSON `summary.json`; wrong counts; tests FAIL `13!=6` (F-20260918-19) |
| Default max-tools | **unchanged** |
| Package | **0.2.3** — **no v0.2.4** unless a later confirmed Class A fix |
| Recommendation | **Outcome A — continue 0.2.x** |

## Research + artifact (RW-060)

RW-058 / RW-059 stay as historical text_analyzer evidence above. RW-060 is a
different production objective (research + written artifact) on the same 11B NIM
lane. Docs-only. Default max-tools / max-tasks **not** raised. Package stays
**0.2.3**. Class A candidates from RW-059 remain parked (not this record).

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-060 | 2026-09-18 IST ~14:25–14:27 | research (live NIM) | Real-World Research + Artifact — pathlib reference (`pathlib_reference.md` + `pathlib_reference/README.md`); `--max-tasks 8 --max-tools 16`; Needle `existing` / off | max-tasks 8 | tools 16/16; model calls 18/80; wall ~110s | 16/16 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | budget exhausted | **B** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw060_eb0192`; `obj_b114afd4`. Disk: `pathlib_reference/README.md` **EXISTS** sha256 `48f0d39b…`; `pathlib_reference.md` **EXISTS** but **162 B stub** — sections 3–9 **FAIL**, 0 examples; no docs.python.org fetch. False DONE **0**. **Not Class A**; **not Class C**. Pattern generalizes vs RW-058/059: a research workload also fails under 11B+tool budget before a substantive deliverable. Default max-tools / max-tasks **not** raised. No architecture change. **No v0.2.4.** |

### RW-060 vs text_analyzer runs (RW-058 / RW-059)

| | RW-058 | RW-059 | RW-060 |
|---|---|---|---|
| category | coding (live NIM) | coding (live NIM) — controlled tool-budget | research + artifact (live NIM) |
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw060_eb0192` |
| objective id | `obj_4e219224` | `obj_e1419520` | `obj_b114afd4` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same | same |
| `--max-tasks` | 8 | 8 | 8 |
| `--max-tools` | **12** | **24** (run only; default unchanged) | **16** (run only; default unchanged) |
| Needle | `existing` / off | `existing` / off | `existing` / off |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 | ~110s IST ~14:25–14:27 |
| tools used | 12/12 exhausted | 24/24 exhausted | 16/16 exhausted |
| model calls | 7/80 | 25/80 | 18/80 |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** |
| disk | 4/5 under `text_analyzer/`; `summary.json` **MISSING** | all five files under `text_analyzer/`; `summary.json` invalid JSON + wrong counts; tests **FAIL** `13!=6` | `pathlib_reference/README.md` EXISTS sha256 `48f0d39b…`; `pathlib_reference.md` EXISTS, **162 B stub**; sections 3–9 **FAIL**; 0 examples; no docs.python.org fetch |
| class | **B** | **B** (Case B on tool-budget) | **B** (not A, not C) |

| metric | value |
|---|---|
| Pattern | **generalizes** — coding (RW-058/059) *and* research (RW-060) fail under 11B+tool budget before a substantive deliverable |
| Class A this record | **none** (parked F-20260918-17 / F-20260918-18 stay open/investigate; **not this PR**) |
| Class C | **none** (NIM key present) |
| Default max-tools / max-tasks | **unchanged** |
| Package | **0.2.3** — **no v0.2.4** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Class A investigation (budget exhaustion → needs_user)

RW-058 / RW-059 / RW-060 rows above are **not rewritten**. This is a deterministic
control-plane investigation of those `needs_user` outcomes (parked F-20260918-17 /
F-20260918-18). No live NIM. No default max-tools / max-tasks raise. Cap **16**
unchanged. Needle `existing` / off. Package stays **0.2.3**.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-061 | 2026-09-18 | investigation (scripted; no NIM) | Class A probe of tool-budget → `needs_user` on v0.2.3 (`a40a544`); Scenarios A/B/C + F-17/F-18 | n/a (injected plans) | injected tool counts | default **60** unchanged (not a live `--max-tools`) | **no RAD defect**; live RW-058/059/060 remain **FAIL** Class B | Scenario A `VERIFIED`; B/C `needs_user` when checks unmet | B: checkpoint + resume continues; C: not recoverable without more budget/work | **NONE** (suspects not confirmed) | Tests `tests/test_class_a_budget_investigation.py` **17 passed**; full pytest **345 passed**; `rad doctor --offline` READY; `rad acceptance` 50/50; `rad realworld` 10 passed / 1 BLOCKED (`live_nim`). False DONE **0**. F-17 newline split **not** in fallback. F-18 ENV misclass **not** the live path. **No patch. No v0.2.4.** Architecture frozen. |

### Investigation vs live 11B rows

| | RW-058 | RW-059 | RW-060 | RW-061 (this investigation) |
|---|---|---|---|---|
| kind | live NIM coding | live NIM coding, extra tools | live NIM research | scripted controller, no model |
| status | `needs_user` / FAIL | `needs_user` / FAIL | `needs_user` / FAIL | no product run; path proven correct |
| false DONE | **0** | **0** | **0** | **0** |
| class | **B** (preserved) | **B** (preserved) | **B** (preserved) | **NONE** — Class A **not proven** |
| F-17 / F-18 | parked | parked | parked | **investigated / not Class A** |

| metric | value |
|---|---|
| RAD defect demonstrated | **NO** |
| Patch required | **NO** |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| Package | **0.2.3** — **no v0.2.4** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Simple Coding + Verification control (RW-062)

RW-058 / RW-059 / RW-060 / RW-061 rows above are **not rewritten**. RW-062 is a
live **Simple Coding + Verification** control on the same 11B NIM lane: a simpler
coding workload than text_analyzer, still with disk-checked files + tests.
Docs-only. Default max-tools / max-tasks **not** raised. Package stays **0.2.3**.
No Class A patch. PR #14 (RW-061) closed F-17 as not-confirmed from a
deterministic test; this live run is additional evidence, not a product fix.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-062 | 2026-09-18 IST ~15:41–15:47 | coding (live NIM) — Simple Coding + Verification control | Simple Coding + Verification; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=fallback** after nvidia plan timeout; **7** newline-split spurious tasks | tools 12/12; wall ~383s | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | budget exhausted | **B** primary; F-17 evidence **strengthened** (not patched) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw062_6ede431b`; `obj_7a020865`. Disk: five files exist; `result.json` as-left **INVALID** `{`; tests **FAIL** `6!=2`; pollution `DONE:` fake path. False DONE **0**. **Not Class C** (NIM key present). Simple workload also fails similarly → Class B is **not** limited to complex objectives. Default max-tools / max-tasks **not** raised. No architecture change. **No v0.2.4.** |

### RW-062 vs prior production rows (RW-058–061)

| | RW-058 | RW-059 | RW-060 | RW-061 | RW-062 (this control) |
|---|---|---|---|---|---|
| kind | live NIM coding | live NIM coding, extra tools | live NIM research | scripted controller, no model | live NIM **simple** coding + verification |
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw060_eb0192` | n/a (pytest) | `/tmp/rad_prod_rw062_6ede431b` |
| objective id | `obj_4e219224` | `obj_e1419520` | `obj_b114afd4` | Scenarios A/B/C | `obj_7a020865` |
| `--max-tasks` | 8 | 8 | 8 | n/a (injected plans) | **4** (run only; default unchanged) |
| `--max-tools` | **12** | **24** | **16** | default **60** unchanged | **12** (run only; default unchanged) |
| Needle | `existing` / off | `existing` / off | `existing` / off | `existing` / off | `existing` / off |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 | ~110s IST ~14:25–14:27 | n/a | ~383s IST ~15:41–15:47 |
| planner | llm (5 planned) | llm | llm | injected | **fallback** after nvidia plan timeout; 7 newline-split spurious tasks |
| tools used | 12/12 exhausted | 24/24 exhausted | 16/16 exhausted | injected counts | 12/12 exhausted |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** | no product run; path proven correct | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** | **0** | **0** |
| disk | 4/5 under `text_analyzer/`; `summary.json` **MISSING** | five paths; invalid JSON + wrong counts; tests **FAIL** `13!=6` | pathlib stub; sections 3–9 **FAIL** | n/a | five files exist; `result.json` as-left INVALID `{`; tests **FAIL** `6!=2`; pollution `DONE:` fake path |
| class | **B** (preserved) | **B** (preserved) | **B** (preserved) | **NONE** — Class A **not proven** (PR #14) | **B** primary; F-17 **reopened** as live evidence (no patch) |

| metric | value |
|---|---|
| Pattern | **generalizes further** — complex coding (RW-058/059), research (RW-060), **and simple coding+verification (RW-062)** fail under 11B+tool budget before a passing, verifiable result. Class B is not complexity-limited |
| F-17 | PR #14 / RW-061: deterministic newline-only goal → 1 fallback task; live RW-058/059/060 were **llm**. **RW-062:** `PLAN_CREATED` source=**fallback**; 7 tasks (then labeled newline-split). **Later (RW-063 / F-23):** timeout path uses `obj.goal` only; 7 = clause split of the user goal (`[:7]`), not model-output parse, not `\n` split. Class A **NOT CONFIRMED**. **No product fix** |
| Class A this record | **none patched** |
| Class C | **none** (NIM key present) |
| Default max-tools / max-tasks | **unchanged** |
| Package | **0.2.3** — **no v0.2.4** |
| Recommendation | **Outcome A — continue 0.2.x** |

## F-17 timeout / prose investigation (RW-063)

RW-058 / RW-059 / RW-060 / RW-061 / RW-062 rows above are **not rewritten**.
RW-063 is a scripted (no NIM) investigation of the planner timeout → fallback
path after PR #15 (`d15af713`). Architecture frozen. Needle OFF. Cap 16 and
default max-tools **UNCHANGED**. Package stays **0.2.3**. **No product patch.**

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-063 | 2026-09-18 | investigation (scripted; no NIM) | F-17: does fallback convert model output after planner timeout? Scenarios A–D + PR #14 vs RW-062 | A: llm 2 tasks; B: fallback 7 (goal clauses); C: fallback 3 (prose *goal*); D: fallback ≤7 | n/a (plan + bounded drive) | default **60** unchanged | **no RAD defect**; F-17 **NOT CONFIRMED** | fallback tasks UNVERIFIED; objective not VERIFIED without checks | n/a | **NONE** | Timeout/empty/malformed/non-JSON LLM discarded; `_fallback(obj)` splits `obj.goal` on clause markers, not newlines, cap `[:7]`. One-sentence goal + 7-line model prose → 1 task. `--max-tasks 4` drives ≤4 of 7 planned. False DONE **0**. Needle OFF. Cap 16 UNCHANGED. **No patch. No v0.2.4.** |

| metric | value |
|---|---|
| Trigger | nvidia plan timeout (RW-062) → `PLAN_CREATED` source=fallback |
| Fallback path | `Planner.plan` `except` / no JSON / empty graph → `_fallback(obj)` — **never** the LLM `raw` string |
| Parser behavior | `re.split(r"\b(?:and then|then|;|, and)\b|\.(?=\s|$)", obj.goal)` then `[:7]` |
| PR #14 vs RW-062 | newline-only → 1 task (PR #14 true). 7 tasks = period/clause split of a seven-sentence **goal** (RW-062 count), not `\n` split of model output |
| Spurious model-output tasks | **0** |
| Tool/Budget impact | up to 7 no-check tasks after timeout; drive `--max-tasks` can stop earlier; default tools **60**; not unbounded to 16 |
| Class A | **NO** |
| Patch / Regression (product) | **NO** / investigation tests only |
| Package | **0.2.3** — **no v0.2.4** |
| Gates | pytest **364 passed**; `rad doctor --offline` READY; `rad acceptance` 50/50; `rad realworld` 10 passed / 1 BLOCKED (`live_nim`) |
| Recommendation | **Outcome A — continue 0.2.x** |
