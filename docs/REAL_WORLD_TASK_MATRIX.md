# Real-world task matrix

Factual rows from the post-v0.2.1 maturation cycle on this branch (package **0.2.2**).
Architecture frozen. Needle stays experimental / off. Not AGI. No v0.3.0.

Every `VERIFIED` / `completed` cell is from the control-plane verifier **and** a disk
check (file exists / contents / hash). A model `DONE:` line is never enough.

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `f7160c14cc5e9905a5c2e0689bbcc2465a20b45c` (Merge PR #7).
Release tag `v0.2.1` → `705954010b4835f8d6bfc445f49bafb80add5dee`.

Status vocabulary: **PASS** | **FAIL** | **BLOCKED** | **NOT TESTED**.

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
| Independent lab-grader false negatives on RW-020 / RW-021 (pre-fix) | **2** (Class A; fixed) |
| 20 sequential *actions* | **VERIFIED** (RW-017) |
| 20 sequential *planned tasks* at default cap | **FAILED** at 16 (RW-016) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |

Do not add rows without a disk check or an honest BLOCKED/NOT TESTED mark.
