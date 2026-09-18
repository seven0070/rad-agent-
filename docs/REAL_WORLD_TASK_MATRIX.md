# Real-world task matrix

Factual rows from maturation cycles on disk-checked evidence.
Architecture frozen. Needle stays experimental / off. Not AGI. No v0.3.0.

Every `VERIFIED` / `completed` cell is from the control-plane verifier **and** a disk
check (file exists / contents / hash). A model `DONE:` line is never enough.

Status vocabulary: **PASS** | **FAIL** | **BLOCKED** | **NOT TESTED**.

Cycle 4 (package **0.2.3**, no bump) is at the bottom. Cycle 3 and Cycle 2 follow.

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

Cap hit this cycle: **2/18** campaign rows (RW-054, RW-056). Coding / research / filesystem / multi-step / recovery used 1–3 tasks and never hit it. Decision: **leave at 16**. See Cycle 4 report.

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
