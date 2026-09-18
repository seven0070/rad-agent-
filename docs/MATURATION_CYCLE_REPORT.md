# Maturation cycle report (v0.2.2)

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

Filled after the commands below were executed on this branch (isolated `/tmp/rad-v022-gate`).

| gate | result |
|---|---|
| `rad version` | **v0.2.2** |
| `python -m pytest -q` | *(run on this branch; see follow-up commit if counts land after the first push)* |
| `rad doctor --offline` | *(same)* |
| `rad acceptance` | *(same)* |
| `rad realworld` | *(same)* |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Secrets in git | **PASS** (inspected) |
| DONE semantics | **PASS** (RW-007, RW-009, RW-022) |
| Architecture freeze | **PASS** |

## Recommended next action

1. Supply `NVIDIA_NIM_API_KEY` and retest live Class A: file-on-disk → VERIFIED; missing file → not VERIFIED; one unconstrained 11B write (log B if `needs_user` after the file exists and the verifier *was* consulted).
2. Leave `max_plan_tasks` at 16 unless a measured product need requires a documented config key.
3. Keep Needle off until a gold-set win on RAD tools.
4. Do not ship v0.3.0 from this loop.
