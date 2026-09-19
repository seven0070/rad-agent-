# Real-world failure ledger

Living log of **measured** RAD failures found in live or reconstructed use.
Architecture is frozen. Needle stays experimental and off by default. This is not AGI/ASI.
Operating spine: [ROADMAP.md](ROADMAP.md) (adopted 2026-09-18). Gen1 complete on 0.2.3; **Gen2 complete** on 0.3.0–0.3.2. Verified coding loop is **implemented as v0.3.0** (F-20260918-24 / RW-064). Live retest **RW-065**. Plan-timeout resilience is **implemented as v0.3.1** (F-20260918-27 / scripted RW-066) and **used** (live RW-066 / F-20260918-28). Budget-aware planning is **implemented as v0.3.2** (F-20260918-29 / RW-067). Live NIM use of v0.3.2 is **RW-068 PASS** (F-20260918-30) and **RW-069 FAIL** (F-20260918-31). Path-aligned checks are **implemented as v0.4.0** (F-20260918-32 / RW-070). Live NIM retest of v0.4.0 is **RW-071 FAIL** (F-20260918-33; theme 1 live-confirmed). Multi-file contracts under tight budgets are **implemented as v0.4.1** (F-20260918-34 / RW-072). Live NIM retest of v0.4.1 is **RW-073 FAIL** (F-20260918-35; theme 1/2 live-confirmed). ASCII-tree `package_dir` is **implemented as v0.4.2** (F-20260918-36 / RW-074). Live NIM retest of v0.4.2 is **RW-075 FAIL** (F-20260918-37; ASCII-tree obj-checks live-confirmed). First-task thrash is **implemented as v0.4.3** (F-20260918-38 / RW-076). Live NIM retest of v0.4.3 is **RW-077 FAIL** (F-20260918-39; pip/DONE Class A **live-consistent**; mkdir File-exists action noise is F-40). mkdir already-exists action noise is **implemented as v0.4.4** (F-20260918-40 / RW-078). Live NIM retest of v0.4.4 is **RW-079 FAIL** (F-20260918-41; mkdir File-exists **not live-hit**; premature-test ENVIRONMENT is F-42). Premature-test ENVIRONMENT is **implemented as v0.4.5** (F-20260918-42 / RW-080). Live NIM retest of v0.4.5 is **RW-081 FAIL** (F-20260918-43; mkdir File-exists **live Y**; premature-test ENVIRONMENT **not live-hit**; pip/echo + root pollution residual). Pip thrash + root `analyzer.py` pollution Class A is **NOT CONFIRMED** (F-20260918-44 / scripted RW-082). Task-boundary yield / leftover-budget dispatch is **implemented as v0.4.6** (F-20260918-45 / scripted RW-083). Live NIM retest of v0.4.6 is **RW-084 BLOCKED Class C** (F-20260919-46; HTTP **403 Authorization failed** on all `chat/completions`; `/v1/models` **200**; tools **0/12**; E1 leftover-budget yield **not live-tested**). Live OpenRouter free retest of v0.4.6 is **RW-085 FAIL** (F-20260919-47; tools **11/12**; `xxd` ENVIRONMENT repair; E1 **not live**). Missing optional checksum/hex utility ENVIRONMENT is **Class A CONFIRMED** and **implemented as v0.4.7** (F-20260919-48 / scripted RW-086). Live OpenRouter free retest of v0.4.7 is **RW-086 FAIL** (F-20260919-49; tools **12/12**; xxd Class A thrash **CLEARED**; E1 **not live**; late HTTP **429** `free-models-per-day`). Independent later package files is **implemented as v0.4.8** (F-20260919-50 / scripted RW-087). Budget-aware retry stop is **implemented as v0.4.9** (F-20260919-51 / scripted RW-088). Live OpenRouter free-model loop is **paused** until `free-models-per-day` rate limit resets. Live NIM loop remains **paused** (Class C). This ledger is evidence. Do not rewrite RW-058–087. Scripted RW-066 (F-27) is preserved.

No secrets belong here: never paste API keys, vault contents, account tokens, or full
provider payloads. Paths under `/tmp/…` and objective ids are fine.

## Classification

| class | meaning | action |
|---|---|---|
| **A** | RAD defect (controller, verifier, adapter, tools, policy) | smallest fix + regression; bump `0.2.x` only |
| **B** | Model / planner limitation on a working product path | document; bounded mitigation only; do **not** weaken `DONE:` / `VERIFIED` |
| **C** | Environment / provider / missing key / EOL catalog | mark **BLOCKED** or unavailable; do not treat as PASS or as a RAD bug |

`VERIFIED` still requires independent machine checks on disk. A model `DONE:` line is never
enough. `needs_user` is correct when checks are unmet.

## Entry template

Copy this block for every new finding:

```
### F-YYYYmmdd-NN — short title

| field | value |
|---|---|
| class | A / B / C |
| status | open / fixed / blocked / documented |
| found in | version + commit / PR |
| fixed in | version + commit / PR, or — |
| lane | live NIM / scripted realworld / doctor / usage batch |
| objective / test | id or command |
| disk | artifact path + expected content (no secrets) |
| expected | … |
| actual | … |
| notes | one paragraph; no keys |

Reproduction (redacted):
…
```

## Seed history (pre-v0.2.1)

These entries are reconstructed from `VALIDATION_REPORT.md`, PR #4/#5/#6,
`REAL_WORLD_VALIDATION_REPORT.md`, `NEEDLE_EVALUATION_REPORT.md`, and
`docs/AUDIT-2026-09.md`. They are the known A/B/C set this ledger starts from.

### F-20260917-01 — non-streaming LLM parsers called `.read()` on bytes

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | Phase 1 audit (2026-09-17) |
| fixed in | PR #2 / `docs/AUDIT-2026-09.md` defect 1 |
| lane | unit (was masked by mocks of `P.chat`) |
| expected | `_http()` bytes parse as a chat completion |
| actual | crash on every non-streaming call (battery, teams, plans, vision, …) |

### F-20260917-02 — `see_image` passed unsupported `max_tokens`

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | Phase 1 audit |
| fixed in | PR #2 / audit defect 2 |
| expected | vision tools reach a vision provider |
| actual | always `"no vision provider"` |

### F-20260917-03 — brain-battle un-pin after first call

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | Phase 1 audit |
| fixed in | PR #2 / audit defect 3 |
| expected | candidate model used for the whole battery |
| actual | question 1 on candidate, rest on default chain |

### F-20260917-04 — `planrun` inferred success from silence

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | Phase 1 audit |
| fixed in | PR #2 / audit defect 4 |
| expected | missing `DONE:` / `BLOCKED:` is not success |
| actual | silence marked done |

`plan_infer_done: true` remains the opt-in legacy behaviour. Do not re-enable it as default.

### F-20260917-05 — file tools had no workspace jail

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | Phase 1 audit |
| fixed in | PR #2 / audit defect 5 |
| expected | `read_file` / `write_file` stay inside the workspace |
| actual | absolute paths and `..` could read e.g. `~/.ssh/*` |

Opt-out is explicit: `allow_outside_workspace: true`.

### F-20260918-01 — NVIDIA NIM nested tool-call wire (HTTP 400)

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | v0.2.0 ship validation (PR #4) |
| fixed in | v0.2.0 — `_openai_message()` nested `{type:function,function:{name,arguments}}` |
| lane | live NIM `objective run` |
| expected | tool follow-up accepted by OpenAI-compat NIM |
| actual | HTTP 400 Pydantic on flat `{id,name,arguments}` |

Disk artifacts from those runs were already correct; the control plane did not rubber-stamp
the HTTP failure as `VERIFIED`.

### F-20260918-02 — NVIDIA NIM parallel multi-`tool_calls` (HTTP 400)

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | first-use on tagged v0.2.0, `meta/llama-3.2-11b-vision-instruct` |
| fixed in | PR #5 (`c93f82b`) — `_unparallel_tool_history` + `parallel_tool_calls: false` |
| lane | live NIM |
| expected | sequential single tool-call turns |
| actual | `This model only supports single tool-calls at once`; retry budget died; `needs_user` |

Files on disk were correct. Same class of adapter bug as F-20260918-01, not a redesign.

### F-20260918-03 — budget abort ignored already-met machine checks

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | v0.2.0 live notes (`VALIDATION_REPORT.md`); reconstructed on PR #6 |
| fixed in | **v0.2.1** (PR #6, merge `7059540`) |
| lane | live NIM (historical) + scripted `overdecompose` |
| objective / test | `test_budget_exhaust_after_graph_complete_still_verifies`, `test_overdecompose_budget_completes_when_objective_checks_pass`, `rad realworld --only overdecompose` |
| disk | goal file already present (e.g. `live_hello.txt` contains `hello`) |
| expected | fall through to `_verify_objective`; `VERIFIED` iff machine checks pass |
| actual | `_drive` tested `budgets.check()` **before** `graph.is_complete()` / `objective_checks`; exited `needs_user` and never asked the verifier |

Fix (does **not** weaken DONE):

1. Graph already complete when the budget dies → `_verify_objective`.
2. Remaining OPEN tasks whose machine checks already pass are completed without a model call.
3. If non-empty `objective_checks` all pass → leftover OPEN tasks `CANCELLED` (superseded), then verify.
4. If checks do not pass → `needs_user` as before.

Guard regression: `test_budget_exhaust_without_met_checks_still_needs_user` plus
`rad realworld --only false_success`.

### F-20260918-04 — 11B over-decomposition / weak tool args

| field | value |
|---|---|
| class | B |
| status | documented (bounded mitigation only) |
| found in | v0.2.0 live NIM (`obj_1f38769f`, `obj_07e2755e`, …) |
| fixed in | — not a RAD hole; planner prompt in v0.2.1 prefers 2–6 tasks and no invented README/backup work |
| lane | live NIM default `meta/llama-3.2-11b-vision-instruct` |
| expected | 1–3 tasks for a one-file write |
| actual | extra README/backup/polish tasks; tool budget exhausted after the file was already on disk |

Do not accept unverified `DONE:` to “fix” this. Bounded runs (`--max-tasks 3 --max-tools 8`)
completed `VERIFIED` on v0.2.0. Unconstrained 11B planning is still a product gap.

Live retest of this class on post-v0.2.1 maturation: see **F-20260918-07**.

Offline reconstruction in this maturation run (not a live 11B substitute):
budget-boundary + `live_hello.txt` contains `hello` → `completed` / `VERIFIED`;
budget-boundary + artifact missing → `needs_user` / not `VERIFIED`.

### F-20260918-05 — NIM 70B catalog EOL / not enabled

| field | value |
|---|---|
| class | C |
| status | documented |
| found in | v0.2.0 ship validation |
| lane | live NVIDIA NIM |
| expected | listed instruct IDs callable |
| actual | `meta/llama-3.3-70b-instruct` → HTTP 410 Gone (EOL 2026-08-26); several listed 70B/Nemotron IDs → HTTP 404 “not enabled for this account” |

Working tested model remains `meta/llama-3.2-11b-vision-instruct`. Do not advertise that any
listed 70B id works on a free-credit key.

### F-20260918-06 — Needle 3 misses RAD tool arguments / can propose `run_shell`

| field | value |
|---|---|
| class | B |
| status | documented — adapter stays **optional and off** |
| found in | PR #6 Needle eval (`NEEDLE_EVALUATION_REPORT.md`, ADR-001) |
| fixed in | — do not default Needle; not v0.3.0 |
| lane | local cactus-needle 3.0.1 gold set (n=5) |
| expected | grounded `write_file` path; no sudo |
| actual | selection **0.60** / arg accuracy **0.20** vs existing heuristic **0.80** / **0.80**; `write_file.path="write_file"`; `must_not_sudo` proposed `run_shell` |

RAD still denies `run_shell` at the hard layer. Needle is never sovereign (`complete()` only,
never `run()`). Revisit only with a measured win on RAD tools.

### F-20260918-07 — live NIM Class A budget-boundary retest

| field | value |
|---|---|
| class | C |
| status | **BLOCKED** |
| found in | post-v0.2.1 maturation (this ledger) |
| lane | live NVIDIA NIM |
| expected | with `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`: budget-boundary + artifact-exists → `VERIFIED`/`completed`; artifact-missing → not `VERIFIED` |
| actual | both env vars **absent** in this environment — live lane not run |

Offline reconstruction of the same pattern is `rad realworld --only overdecompose,false_success`
(scripted). That is not a substitute for the live 11B retest.

### F-20260918-08 — live `objective run` with no brain

| field | value |
|---|---|
| class | C |
| status | documented |
| found in | post-v0.2.1 maturation usage batch |
| lane | `rad objective run` isolated home, no keys |
| objective / test | `obj_07680064` — write `usage_hello.txt` containing hello |
| disk | workspace empty (file never written) |
| expected | escalate; do not fake `VERIFIED` |
| actual | `MODEL_FAILURE → ask_user: no brain available`; status **`needs_user`**; exit 2 |

Not a RAD defect. Core still works offline (`rad doctor --offline`, scripted realworld).

## This maturation run (2026-09-18)

Environment: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
`origin/main` tip `705954010b4835f8d6bfc445f49bafb80add5dee` (Merge PR #6). Package **0.2.1**.
Needle remains default-off. Not AGI. Not v0.3.0.

| gate | result |
|---|---|
| `rad version` | **v0.2.1** |
| `python -m pytest -q` | **326 passed** in 9.34s |
| `rad doctor --offline` | **20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR**, verdict READY, exit 0 |
| `rad acceptance` | **50/50 PASSED** |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` Class C) |
| Live NIM Class A (artifact-exists → VERIFIED; artifact-missing → not VERIFIED) | **BLOCKED** |
| Extra usage batch (coding / research / filesystem / multi-step / crash-resume) | **5/5 VERIFIED** on disk (`/tmp/rad-v021-usage-batch`) |
| Scripted Class A reconstruction | artifact-exists **VERIFIED**; artifact-missing **needs_user** / file absent |
| New Class A this run | **none** — no 0.2.x code bump |

`rad realworld` honesty cases: `false_success`, `needs_user`, `no_loop` all ended `needs_user` and were **not** `VERIFIED`.

## This maturation run (2026-09-18, cycle 2 — v0.2.2)

Environment: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
`origin/main` tip `f7160c14cc5e9905a5c2e0689bbcc2465a20b45c` (Merge PR #7). Package **0.2.1**
at start; this cycle ships **0.2.2** for one Class A grader fix. Needle remains default-off.
Not AGI. Not v0.3.0. Task log: `docs/REAL_WORLD_TASK_MATRIX.md`.

### F-20260918-09 — lab grader rejected verifier-style Check args

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | 0.2.1 `f7160c1` / this cycle's campaign (RW-020, RW-021) |
| fixed in | **v0.2.2** — `_run_grader` accepts `key`/`contains` as well as legacy `field`+`equals` / `expect` |
| lane | scripted realworld + extra campaign |
| objective / test | `test_grader_accepts_verifier_style_json_field_and_shell_contains`; `rad realworld --only research,coding` |
| disk | `cmp.json` / `report.json` had `conflicts`; `python3 check.py` printed `ALL TESTS PASSED` |
| expected | independent lab grader agrees with the control-plane verifier on the same Check dict |
| actual | `json_field{key}` → `grader error: 'field'`; `shell_output{contains}` → `grader error: 'expect'`; both `ok: false` |
| notes | Control plane still VERIFIED from machine checks. The *independent* grader used by `Lab` / realworld `graders=` false-negatived correct artifacts. DONE semantics were not involved. Legacy lab `{expect}` / `{field,equals}` still pass. |

Reproduction (redacted):

```
_run_grader(ws, {"kind":"json_field","args":{"path":"report.json","key":"conflicts"}})
# before: {"ok": false, "detail": "grader error: 'field'"}
_run_grader(ws, {"kind":"shell_output","args":{"command":"echo ALL TESTS PASSED","contains":"ALL TESTS PASSED"}})
# before: {"ok": false, "detail": "grader error: 'expect'"}
```

### F-20260918-10 — live NIM Class A retest (cycle 2)

| field | value |
|---|---|
| class | C |
| status | **BLOCKED** |
| found in | this cycle (RW-011, RW-023) |
| lane | live NVIDIA NIM |
| expected | with `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`: budget-boundary + artifact-exists → VERIFIED; artifact-missing → not VERIFIED |
| actual | both env vars **absent** — live lane not run |

Same condition as F-20260918-07. Offline reconstruction still `rad realworld --only overdecompose,false_success`.

| gate | result |
|---|---|
| `rad version` | **v0.2.2** (after the Class A bump) |
| `python -m pytest -q` | **327 passed** in 8.13s |
| `rad doctor --offline` | **20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR**, verdict READY, exit 0 (`/tmp/rad-v022-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v022-gate/acceptance/20260918-064950_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** after the grader fix; research/coding independent graders now `ok` |
| Live NIM Class A | **BLOCKED** |
| Action ramp 1/3/5/10 tasks | **VERIFIED** on disk |
| 20 sequential actions (one task) | **VERIFIED** (20/20 files) |
| 20 sequential planned tasks | **FAILED** at default `max_plan_tasks=16` (16 files written; s17–s20 absent) — documented limit, not patched |
| New Class A this run | **F-20260918-09** — 0.2.2 grader fix |
| Needle | default `existing`; **NOT** turned on |

## This maturation run (2026-09-18, cycle 3 — v0.2.3)

Environment: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
`origin/main` tip `8d9e196aa730c7bfeae7e501f44004078f080b61` (PR #8 / Release `v0.2.2`). Package **0.2.2**
at start; this cycle ships **0.2.3** for one Class A grader fix. Needle remains default-off.
Not AGI. Not v0.3.0. Planner cap left at 16. Task log: `docs/REAL_WORLD_TASK_MATRIX.md` cycle 3.

### F-20260918-11 — lab grader missing json_valid / list-only json_min_len

| field | value |
|---|---|
| class | A |
| status | fixed |
| found in | 0.2.2 `8d9e196` / this cycle's campaign (RW-025, RW-028, RW-038) |
| fixed in | **v0.2.3** — `_run_grader` implements `json_valid`; `json_min_len` uses `len(doc)` like the verifier |
| lane | scripted realworld + extra campaign |
| objective / test | `test_grader_json_valid_and_json_min_len_match_verifier`; `rad realworld --only research` |
| disk | `compare.json` / `inventory.json` / `config/settings.json` were valid JSON objects on disk |
| expected | independent lab grader agrees with `Verifier.run_check` on advertised Check kinds `{json_valid, json_min_len}` |
| actual | `json_valid` → `unknown grader`; `json_min_len{path,n=2}` on an object → `len=n/a` / `ok: false` while verifier `ok: true` |
| notes | Control plane still VERIFIED from machine checks. Independent Lab / realworld `graders=` false-negatived correct artifacts. DONE semantics were not involved. Same family as F-20260918-09 (schema mismatch), different kinds. |

Reproduction (redacted):

```
_run_grader(ws, {"kind":"json_valid","args":{"path":"inventory.json"}})
# before: {"ok": false, "detail": "unknown grader"}
_run_grader(ws, {"kind":"json_min_len","args":{"path":"inventory.json","n": 2}})
# object {"items":[...],"count":3} — before: {"ok": false, "detail": "inventory.json: len=n/a"}
# Verifier.run_check(Check(kind="json_min_len", args={...})): ok True (len(doc)=2)
```

### F-20260918-12 — live NIM Class A retest (cycle 3)

| field | value |
|---|---|
| class | C |
| status | **BLOCKED** |
| found in | this cycle (RW-037; suite `live_nim`) |
| lane | live NVIDIA NIM |
| expected | with `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`: budget-boundary + artifact-exists → VERIFIED; artifact-missing → not VERIFIED |
| actual | both env vars **absent** — live lane not run |

Same condition as F-20260918-07 / F-20260918-10. Offline reconstruction still `rad realworld --only overdecompose,false_success`.

| gate | result |
|---|---|
| `rad version` | **v0.2.3** (after the Class A bump) |
| `python -m pytest -q` | **328 passed** in 8.73s |
| `rad doctor --offline` | **20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR**, verdict READY, exit 0 (`/tmp/rad-v023-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v023-gate/acceptance/20260918-072009_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed**; research independent graders `json_valid` + `json_min_len` `ok` |
| Live NIM Class A | **BLOCKED** |
| Action ramp 1/3/5/10 tasks | **VERIFIED** on disk |
| 20 sequential actions (one task) | **VERIFIED** (20/20 files) |
| 20 sequential planned tasks | **FAILED** at default `max_plan_tasks=16` (16 files written; s17–s20 absent) — documented limit, not patched |
| New Class A this run | **F-20260918-11** — 0.2.3 grader fix |
| Needle | default `existing`; **NOT** turned on |

## This maturation run (2026-09-18, cycle 4 — v0.2.3 already live)

Environment: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
`origin/main` tip `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` (PR #9 / Release `v0.2.3`). Package **0.2.3**
at start **and** at end — **Release: PASS**, not re-cut, no 0.2.x bump. Needle remains default-off.
Not AGI. Not v0.3.0. Planner cap left at 16. Task log: `docs/REAL_WORLD_TASK_MATRIX.md` cycle 4.

### F-20260918-13 — live NIM Class A retest (cycle 4)

| field | value |
|---|---|
| class | C |
| status | **BLOCKED** |
| found in | this cycle (RW-047; suite `live_nim`) |
| lane | live NVIDIA NIM |
| expected | with `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`: budget-boundary + artifact-exists → VERIFIED; artifact-missing → not VERIFIED |
| actual | both env vars **absent** — live lane not run |

Same condition as F-20260918-07 / F-20260918-10 / F-20260918-12. Offline reconstruction still `rad realworld --only overdecompose,false_success`. That is **not** a substitute for a live 11B run.

| gate | result |
|---|---|
| GitHub Release `v0.2.3` | **PASS** — tag peels to `d121c3f`; package 0.2.3; URL live; not re-cut |
| `rad version` | **v0.2.3** |
| `python -m pytest -q` | **328 passed** in 9.01s |
| `rad doctor --offline` | **20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR**, verdict READY, exit 0 (`/tmp/rad-c4-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-c4-gate/acceptance/20260918-072850_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** |
| Live NIM Class A | **BLOCKED** |
| Action ramp 1/3/5/10 tasks | **VERIFIED** on disk |
| 20 sequential actions (one task) | **VERIFIED** (20/20 files) |
| 16 sequential planned tasks | **VERIFIED** (RW-055) |
| 17 / 20 sequential planned tasks | **FAILED** at default `max_plan_tasks=16` — documented limit, not patched |
| New Class A this run | **none** — no 0.2.x code bump |
| Needle | default `existing`; **NOT** turned on |
| Evidence for v0.3.0 | **none** |
| Planner-cap encounters vs useful-work failures | **2 / 0** (RW-054, RW-056 hit 16; no product row failed *because* of the cap) |
| Recommendation | **Outcome A — continue 0.2.x** |

### Decision gate (this cycle only)

| # | question | answer |
|---|---|---|
| A | v0.2.3 stable? | **YES** — gates pass; useful campaign **VERIFIED**; false completion **0**; release not re-cut |
| B | Recurring Class A? | **NO** — none this cycle; RW-057 grader/verifier parity **PASS** |
| C | Cap prevents useful work? | **NO** — planner hit 16 twice; useful work used 1–3 tasks |
| D | 11B still model limitation? | **NOT TESTED** this cycle (no NIM keys). Prior F-20260918-04 remains Class B on the ledger only |
| E | Needle earned default? | **NO** — stays `existing` |
| F | NIM | **BLOCKED** (F-20260918-13) |
| G | Proven architectural gap? | **NO** |
| H | v0.3.0 justified? | **NO** |

## Production use (post-Cycle 4) — 2026-09-18

Operator production `rad objective run` on package **0.2.3**. Not a Cycle 4 Cloud Agent gate.
Architecture frozen. Needle remains default-off. Planner cap left at 16. **No 0.2.x bump.**
Not AGI. Not v0.3.0. Task log: `docs/REAL_WORLD_TASK_MATRIX.md` production rows RW-058a / RW-058.

### F-20260918-14 — production text_analyzer with no brain

| field | value |
|---|---|
| class | C |
| status | **BLOCKED** |
| found in | post-Cycle 4 production use (RW-058a), rad v0.2.3 |
| fixed in | — not a RAD hole; same missing-brain family as F-20260918-08 / F-20260918-13 |
| lane | live production `objective run` (no NVIDIA/other keys / no local engine) |
| objective / test | `obj_442301c7` — production text_analyzer (earlier attempt) |
| disk | workspace empty (no artifacts written) |
| expected | escalate; do not fake `VERIFIED` / `DONE` |
| actual | `MODEL_FAILURE`; status **BLOCKED**. Home `/tmp/rad_prod_text_analyzer_f3cc7950`. Tasks 7 planned / 1 attempted / 0 completed; tools 0/12. False DONE **0** |
| notes | Production instance of the no-key / no-engine condition. Distinct from Cycle 4 F-20260918-13 (Cloud Agent gate, live lane not run) only as a recorded operator attempt that planned tasks then blocked. Class C closed for the follow-up live-NIM attempt (RW-058). |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad_prod_text_analyzer_f3cc7950  # rad v0.2.3; no NVIDIA/other keys; no local engine
# MODEL_FAILURE; workspace empty; 7 planned / 1 attempted / 0 completed; tools 0/12
```

### F-20260918-15 — live 11B production text_analyzer incomplete layout

| field | value |
|---|---|
| class | B |
| status | documented (bounded mitigation only; user chose stop; no resume) |
| found in | post-Cycle 4 production use (RW-058), rad v0.2.3, 2026-09-18 IST ~13:39–13:41 |
| fixed in | — not a RAD hole; 11B limitation. Same family as F-20260918-04. **No v0.2.4.** |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` (NIM key present) |
| objective / test | `obj_4e219224` — create `text_analyzer/{analyzer.py,input.txt,summary.json,test_analyzer.py,README.md}`; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12` |
| disk | `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`; `analyzer.py` computes counts; `test_analyzer.py` byte-identical to `analyzer.py` (0 tests); README present; `text_analyzer/summary.json` **MISSING**; workspace-root `summary.json` had correct counts `{lines:3,words:13,characters:76}` (wrong path); layout pollution at workspace root |
| expected | required layout under `text_analyzer/`; success criteria met; `VERIFIED` only from machine checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. Plan 5 tasks; 1 attempted (verification FAILED, 2 attempts), 4 PENDING. Tools 12/12 exhausted; model calls 7/80; wall ~103s. Home `/tmp/rad_prod_text_analyzer_live_a787512c` |
| notes | Tool spam / incomplete layout / duplicated "tests" / path confusion on 11B. **Not Class A**: RAD correctly stopped at the tool budget; false DONE **0**; verifier did not rubber-stamp. Bounded `--max-tasks 8 --max-tools 12`. Outcome A continues. Needle off. Cap 16 unchanged. No architecture change. |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad_prod_text_analyzer_live_a787512c  # rad v0.2.3; nvidia / meta/llama-3.2-11b-vision-instruct
# --max-tasks 8 --max-tools 12
# obj_4e219224 → needs_user; tools 12/12; text_analyzer/summary.json missing
```

| gate | result |
|---|---|
| Package | **0.2.3** — no bump; **no v0.2.4** |
| Class A | **none** |
| Class B | **F-20260918-15** (RW-058) live 11B production incompleteness |
| Class C | **F-20260918-14** (RW-058a) no-brain `MODEL_FAILURE`; Class C closed for RW-058 |
| False completion | **0** |
| Needle | default `existing`; **NOT** turned on |
| `max_plan_tasks` | **16** unchanged (run used `--max-tasks 8`) |
| Evidence for v0.3.0 | **none** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Controlled tool-budget experiment (RW-059) — 2026-09-18

Operator production follow-up on package **0.2.3**. Same text_analyzer objective as
RW-058 with `--max-tools` doubled 12 → **24** for this run only. RW-058 is preserved
as historical evidence. Architecture frozen. Needle remains default-off. Planner cap
left at 16. **No 0.2.x bump. Default max-tools not raised.** Not AGI. Not v0.3.0.
Task log: `docs/REAL_WORLD_TASK_MATRIX.md` RW-059.

### F-20260918-16 — tool-budget doubling 12→24 did not complete text_analyzer

| field | value |
|---|---|
| class | B (tool-budget hypothesis **Case B**) |
| status | documented |
| found in | post-Cycle 4 production use (RW-059 vs RW-058), rad v0.2.3, 2026-09-18 IST ~14:02–14:04 |
| fixed in | — not a RAD hole to patch from this experiment; 24 did **not** suffice. **No v0.2.4.** Default max-tools **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` (controlled `--max-tools 24`) |
| objective / test | `obj_e1419520` — same text_analyzer layout as RW-058; `--max-tasks 8 --max-tools 24`; Needle `existing` / off |
| disk | all five files present under `text_analyzer/`; `input.txt` sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` (same as RW-058); `summary.json` invalid JSON + wrong counts; tests FAIL `13!=6` |
| expected | doubling the tool budget 12→24 would complete the objective if 12 was the bottleneck (hypothesis Case A) |
| actual | both RW-058 and RW-059 exhausted the tool budget (12/12 and 24/24); both ended `needs_user` / **FAIL**; false DONE **0**. Home `/tmp/rad_prod_rw059_b48e7b56`. Tools: `write_file` 19, `run_shell` 5; model calls 25/80; wall ~106s |
| notes | Controlled comparison against RW-058. More tools produced all five paths under `text_analyzer/` but did not yield a passing, verifiable result. RAD still stopped at the budget; verifier did not rubber-stamp. Outcome A continues. |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad_prod_rw059_b48e7b56  # rad v0.2.3; nvidia / meta/llama-3.2-11b-vision-instruct
# --max-tasks 8 --max-tools 24; Needle existing/off
# obj_e1419520 → needs_user; tools 24/24; tests FAIL 13!=6; summary.json invalid JSON
```

### F-20260918-17 — suspected fallback planner splits multiline objective newlines

| field | value |
|---|---|
| class | A (suspected; **not confirmed**; **not patched**). Primary classification of live RW-062 remains **B** (F-20260918-22) |
| status | **investigated / not Class A** — timeout/prose claim **NOT CONFIRMED**. PR #14 newline-only close remains true. RW-062's 7 tasks are clause-split of the *user goal* after LLM exception, not conversion of model output. No product patch. No v0.2.4 |
| found in | originally RW-059 investigation candidates; live path first seen on RW-062 (nvidia plan timeout → `source=fallback`); closed by F-20260918-23 (scripted; no NIM) |
| fixed in | — **not a defect.** No patch. No v0.2.4. See F-20260918-23 |
| lane | live production `objective run` (RW-062) + deterministic planner/controller tests (RW-061 / RW-063) |
| objective / test | RW-062 Simple Coding + Verification; `tests/test_f17_fallback_investigation.py`; prior `test_fallback_planner_does_not_split_on_newlines` (PR #14) |
| disk | n/a for the split itself. RW-062 artifacts unchanged: five files exist; `result.json` as-left INVALID `{`; tests FAIL `6!=2`; pollution `DONE:` fake path |
| expected | one coherent plan for a single multiline objective; no spurious tasks from newline wrapping; timeout must not turn model prose into tasks |
| actual | **PR #14 / RW-061:** newline-only goal → **1** fallback task (still true). **Timeout path (`Planner.plan`):** LLM exception / empty / malformed / non-JSON prose is discarded; `_fallback(obj)` splits `obj.goal` only. One-sentence goal + seven-line model prose → **1** task (the goal). **RW-062 live 7 tasks:** matches period/clause split of a seven-sentence *user goal* hitting `_fallback` `[:7]` — not `\n` split, not model-output parse. Ordinary prose with periods becomes N clause tasks **by contract** (`one task per clause`). Numbered `1. 2. 3.` also splits on `\.(?=\s|$)`. |
| notes | Intended LLM output is JSON with checks (`PLAN_PROMPT` “Reply ONLY with JSON”). Fallback is the no-brain / parse-failure path: clause markers, max 7, no checks (Verifier UNVERIFIED). That is not a parser contract violation. RW-062 stays Class B. False DONE **0**. Cap 16 and default max-tools **UNCHANGED**. Needle OFF. |

### F-20260918-18 — suspected ENVIRONMENT_FAILURE misclassification burns tool budget

| field | value |
|---|---|
| class | A (suspected; **not confirmed** — investigated) |
| status | **investigated / not Class A** — do **not** claim a product fix; no patch |
| found in | post-Cycle 4 production use (RW-059 investigation candidates), rad v0.2.3 |
| fixed in | — **not a defect.** No patch. No v0.2.4. See F-20260918-21 |
| lane | live production `objective run` (recovery classify) + deterministic classify/recovery tests |
| objective / test | production text_analyzer (RW-058 / RW-059); `test_failed_checks_without_env_output_are_validation_not_environment` |
| disk | n/a — suspected recovery-classification defect, not a disk-hash finding |
| expected | missing/failed work classified so recovery does not spend the tool budget on mis-tagged environment repairs |
| actual | **Not reproduced as a lifecycle defect.** Failed checks with no env-token in observations classify **VALIDATION** or **TOOL** → `retry_with_hint`, not repair. RW-058 shape (verification FAILED, 2 attempts, 4 PENDING, no extra repair task) matches VALIDATION retry. RW-059 `13!=6` / invalid JSON is VALIDATION/TOOL. Genuine `command not found` is ENVIRONMENT → one repair **by design** (`test_environment_failure_inserts_repair_task`); repair still requires machine checks to VERIFIED. |
| notes | Parked suspect closed by investigation. `_ENV` matching observation text before VALIDATION is the designed missing-binary path, not a skip-verify / false-DONE hole. Changing that order would break intended ENVIRONMENT repair. |

### F-20260918-19 — 11B invalid JSON summary and wrong counts on RW-059

| field | value |
|---|---|
| class | B |
| status | documented |
| found in | post-Cycle 4 production use (RW-059), rad v0.2.3, 2026-09-18 IST ~14:02–14:04 |
| fixed in | — not a RAD hole; model limitation. Same family as F-20260918-04 / F-20260918-15. **No v0.2.4.** |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_e1419520` — `text_analyzer/{analyzer.py,input.txt,summary.json,test_analyzer.py,README.md}` |
| disk | all five files present under `text_analyzer/`; `input.txt` sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`; `summary.json` **invalid JSON** + wrong counts; tests **FAIL** `13!=6` |
| expected | valid `summary.json` with correct counts; tests pass |
| actual | layout paths present, but model output failed the success criteria. Status `needs_user` / FAIL. False DONE **0** |
| notes | Class B aspects remain after the extra tool budget: wrong counts, invalid JSON summary, test mismatch. Do not weaken `DONE:` / `VERIFIED` to paper over this. |

| gate | result |
|---|---|
| Package | **0.2.3** — no bump; **no v0.2.4** |
| RW-058 | preserved as historical evidence (F-20260918-15 Class B; tools 12/12) |
| RW-059 vs RW-058 | both `needs_user` / FAIL; both exhausted tool budget; false DONE **0** |
| Tool-budget hypothesis | **Case B** — 24 did not suffice (F-20260918-16) |
| Class A patched | **none** |
| Class A open/investigate | **F-20260918-17**, **F-20260918-18** — suspected only; **not fixed** |
| Class B | **F-20260918-16** (budget doubling), **F-20260918-19** (invalid JSON / wrong counts); RW-058 **F-20260918-15** unchanged |
| Default max-tools | **unchanged** (RW-059 used `--max-tools 24` for this run only) |
| Needle | default `existing`; **NOT** turned on |
| `max_plan_tasks` | **16** unchanged (run used `--max-tasks 8`) |
| Evidence for v0.3.0 | **none** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Research + artifact (RW-060) — 2026-09-18

Operator production follow-up on package **0.2.3**. Separate research + artifact
objective (not a rewrite of RW-058 / RW-059). Architecture frozen. Needle remains
default-off. Planner cap left at 16. Default max-tools **not** raised. Class A
candidates from RW-059 stay **parked** (open/investigate; **not this PR**).
**No 0.2.x bump.** Not AGI. Not v0.3.0.
Task log: `docs/REAL_WORLD_TASK_MATRIX.md` RW-060.

### F-20260918-20 — live 11B research+artifact pathlib reference stub

| field | value |
|---|---|
| class | B |
| status | documented |
| found in | post-Cycle 4 production use (RW-060), rad v0.2.3, 2026-09-18 IST ~14:25–14:27 |
| fixed in | — not a RAD hole; 11B limitation. Same family as F-20260918-04 / F-20260918-15 / F-20260918-16. **No v0.2.4.** Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_b114afd4` — Real-World Research + Artifact (pathlib reference); `--max-tasks 8 --max-tools 16`; Needle `existing` / off |
| disk | `pathlib_reference/README.md` **EXISTS** sha256 `48f0d39b…`; `pathlib_reference.md` **EXISTS** but **162 B stub** — sections 3–9 **FAIL**, 0 examples; no docs.python.org fetch |
| expected | substantive pathlib reference with required sections and examples, sourced (including docs.python.org); `VERIFIED` only from machine checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. Tools 16/16 exhausted; model calls 18/80; wall ~110s. Home `/tmp/rad_prod_rw060_eb0192`. False DONE **0** |
| notes | Pattern **generalizes** beyond the text_analyzer coding runs: a research workload also fails under 11B+tool budget before a substantive deliverable. **Not Class A**: RAD stopped at the tool budget; verifier did not rubber-stamp. **Not Class C**: NIM key present. Class A candidates F-20260918-17 / F-20260918-18 remain parked. Outcome A continues. Needle off. Cap 16 unchanged. No architecture change. |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad_prod_rw060_eb0192  # rad v0.2.3; nvidia / meta/llama-3.2-11b-vision-instruct
# --max-tasks 8 --max-tools 16; Needle existing/off
# obj_b114afd4 → needs_user; tools 16/16; pathlib_reference.md 162B stub; sections 3–9 FAIL
```

| gate | result |
|---|---|
| Package | **0.2.3** — no bump; **no v0.2.4** |
| RW-058 | preserved as historical evidence (F-20260918-15 Class B; tools 12/12) |
| RW-059 | preserved as historical evidence (F-20260918-16 / F-20260918-19 Class B; tools 24/24) |
| RW-060 vs RW-058/059 | research + artifact also `needs_user` / FAIL; tool budget exhausted (16/16); false DONE **0** |
| Class A this record | **none** — parked F-20260918-17 / F-20260918-18 stay **open/investigate**; **not this PR** |
| Class B | **F-20260918-20** (pathlib stub / no docs.python.org fetch; research workload under 11B+tool budget) |
| Class C | **none** (NIM key present) |
| Default max-tools / max-tasks | **unchanged** (RW-060 used `--max-tasks 8 --max-tools 16` for this run only) |
| Needle | default `existing`; **NOT** turned on |
| `max_plan_tasks` | **16** unchanged |
| Evidence for v0.3.0 | **none** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Class A investigation — budget exhaustion → needs_user (2026-09-18)

Operator-directed investigate-first on package **0.2.3** after RW-058 / RW-059 / RW-060
all ended `needs_user` with false DONE **0**. Architecture frozen. Needle remains
default-off. Planner cap left at 16. Default max-tools **not** raised.
Parked suspects F-20260918-17 / F-20260918-18 investigated with code trace +
deterministic tests (no live NIM; no model-quality dependence).
**No control-plane patch. No 0.2.x bump.** Not AGI. Not v0.3.0.

### F-20260918-21 — budget→needs_user path investigated; Class A not proven

| field | value |
|---|---|
| class | **NONE** (live rows remain **B**; parked A suspects **not confirmed**) |
| status | documented |
| found in | post-RW-060 Class A investigation, rad v0.2.3, commit of this record |
| fixed in | — **no patch.** No v0.2.4 |
| lane | deterministic pytest (scripted sessions inject tool counts) + code trace of `_drive` / `_on_budget` |
| objective / test | `tests/test_class_a_budget_investigation.py` Scenarios A/B/C; F-17/F-18 unit tests |
| disk | n/a — controller lifecycle, not a production hash |
| expected | Class A only if RAD skips verify / wrong needs_user / blocks recovery / wrong fallback when objective checks already pass |
| actual | Scenario A: checks pass at budget → `COMPLETED` / `VERIFIED` (F-20260918-03 still holds). Scenario B: unmet remaining work → `needs_user` + checkpoint; resume with raised budget continues. Scenario C: unmet / invalid artifacts → `needs_user`, not `VERIFIED`; model `DONE:` ignored. F-17 newline split **not** in `_fallback`. F-18 ENV misclass **not** the RW-058/059/060 path. |
| notes | Live NIM 11B FAIL on RW-058/059/060 stays **Class B**: tool budget exhausted with success criteria unmet. RAD did not rubber-stamp. False DONE **0**. Default `Budget.tool_calls` remains **60**; `max_plan_tasks` remains **16**; Needle `existing`. **Later (RW-062):** F-17 reopened with additional live fallback evidence — see F-20260918-22. F-21's deterministic Scenarios A/B/C and F-18 remain as written. Not a product fix. |

Reproduction (redacted):

```
python -m pytest -q tests/test_class_a_budget_investigation.py
# 17 passed — Scenarios A/B/C + F-17/F-18; no live NIM
```

| gate | result |
|---|---|
| Package | **0.2.3** — no bump; **no v0.2.4** |
| RW-058 | preserved (F-20260918-15 Class B; tools 12/12) |
| RW-059 | preserved (F-20260918-16 / F-20260918-19 Class B; tools 24/24) |
| RW-060 | preserved (F-20260918-20 Class B; tools 16/16) |
| Parked F-20260918-17 | **investigated / not Class A** (newline split not in fallback; live path was llm) |
| Parked F-20260918-18 | **investigated / not Class A** (VALIDATION/TOOL on unmet checks; ENV repair is designed missing-binary path) |
| RAD defect demonstrated | **NO** |
| Classification | **B** for the live 11B FAIL rows; investigation itself **NONE** |
| Patch required | **NO** |
| `python -m pytest -q` | **345 passed** (328 prior + 17 investigation) |
| `rad doctor --offline` | READY, 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR |
| `rad acceptance` | **50/50 PASSED** |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED — no NVIDIA keys on this VM) |
| False completion | **0** |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| Evidence for v0.3.0 | **none** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Simple Coding + Verification control (RW-062) — 2026-09-18

Operator production follow-up on package **0.2.3**. Live **Simple Coding +
Verification** control (not a rewrite of RW-058–061). Architecture frozen.
Needle remains default-off. Planner cap left at 16. Default max-tools **not**
raised. **No 0.2.x bump.** Not AGI. Not v0.3.0.
Task log: `docs/REAL_WORLD_TASK_MATRIX.md` RW-062.

PR #14 (RW-061 / F-20260918-21) closed F-17 as **not-confirmed** from a
deterministic newline-only fallback test (live RW-058/059/060 planner source
was **llm**). RW-062 is additional **live** evidence: nvidia plan timeout →
`PLAN_CREATED` source=**fallback** → 7 newline-split spurious tasks. That
**reopens / strengthens** F-17. This PR does **not** claim a product fix and
does **not** ship a Class A patch.

### F-20260918-22 — live 11B simple coding+verification incomplete (RW-062)

| field | value |
|---|---|
| class | **B** primary (F-17 suspected A **strengthened**, **not patched**) |
| status | documented |
| found in | post-Cycle 4 production use (RW-062), rad v0.2.3, 2026-09-18 IST ~15:41–15:47 |
| fixed in | — not a RAD hole to patch from this record; 11B limitation on a simpler coding+verification workload. Same family as F-20260918-04 / F-20260918-15 / F-20260918-16 / F-20260918-19 / F-20260918-20. **No v0.2.4.** Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_7a020865` — Simple Coding + Verification; `--max-tasks 4 --max-tools 12`; Needle `existing` / off |
| disk | five files exist; `result.json` as-left **INVALID** `{`; tests **FAIL** `6!=2`; pollution `DONE:` fake path |
| expected | simpler coding+verification succeeds (valid `result.json`, tests pass) under a tighter `--max-tasks 4 --max-tools 12` bound; `VERIFIED` only from machine checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. Tools 12/12 exhausted; wall ~383s. Home `/tmp/rad_prod_rw062_6ede431b`. `PLAN_CREATED` **source=fallback** after nvidia plan timeout; **7** newline-split spurious tasks. False DONE **0** |
| notes | Interpretation: a **simple** workload also fails similarly → Class B is **not** limited to complex objectives (text_analyzer / research). **Not Class C**: NIM key present. F-17 additional live evidence recorded above; **no Class A patch in this PR**. RAD stopped at the tool budget; verifier did not rubber-stamp. Outcome A continues. Needle off. Cap 16 unchanged. No architecture change. |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad_prod_rw062_6ede431b  # rad v0.2.3; nvidia / meta/llama-3.2-11b-vision-instruct
# --max-tasks 4 --max-tools 12; Needle existing/off
# obj_7a020865 → needs_user; tools 12/12; PLAN_CREATED source=fallback after nvidia plan timeout
# 7 newline-split spurious tasks; result.json INVALID `{`; tests FAIL 6!=2; pollution DONE: fake path
```

| gate | result |
|---|---|
| Package | **0.2.3** — no bump; **no v0.2.4** |
| RW-058 | preserved (F-20260918-15 Class B; tools 12/12) |
| RW-059 | preserved (F-20260918-16 / F-20260918-19 Class B; tools 24/24) |
| RW-060 | preserved (F-20260918-20 Class B; tools 16/16) |
| RW-061 | preserved (F-20260918-21; deterministic Class A **not proven**; F-18 stays not-confirmed) |
| F-20260918-17 | **reopened here as live evidence** (timeout → fallback; 7 tasks). **Later (F-20260918-23 / RW-063):** **not Class A** — timeout does not parse model output; 7 = goal clause split. **No patch this PR** |
| Class A this record | **none patched** |
| Class B | **F-20260918-22** (simple coding+verification: invalid `result.json`, tests `6!=2`, pollution `DONE:` fake path, tools 12/12, `needs_user`) |
| Class C | **none** (NIM key present) |
| Default max-tools / max-tasks | **unchanged** (RW-062 used `--max-tasks 4 --max-tools 12` for this run only) |
| Needle | default `existing`; **NOT** turned on |
| `max_plan_tasks` | **16** unchanged |
| False completion | **0** |
| Evidence for v0.3.0 | **none** |
| Recommendation | **Outcome A — continue 0.2.x** |

## F-17 timeout / prose investigation (RW-063) — 2026-09-18

Investigate-first after PR #15 merged RW-062 (`d15af713`). Package **0.2.3**.
Needle OFF. Cap 16 and default max-tools **UNCHANGED**. **No v0.2.4.**
RW-058 / RW-059 / RW-060 / RW-061 / RW-062 rows are **not rewritten**.
No planner/controller product patch.

Question: when the LLM planner fails or times out, does fallback convert
ambiguous model output into executable tasks?

### F-20260918-23 — F-17 timeout/prose fallback **NOT CONFIRMED**

| field | value |
|---|---|
| class | **NONE** (Class A **not proven**). Live RW-062 remains **B** |
| status | **investigated / not Class A** — document only; **no product patch** |
| found in | F-17 follow-up on `origin/main` `d15af713` (PR #15 / RW-062), rad v0.2.3, 2026-09-18 |
| fixed in | — **not a defect.** No patch. Package stays **0.2.3**. **No v0.2.4** |
| lane | scripted planner + controller (no NIM). Tests `tests/test_f17_fallback_investigation.py` |
| objective / test | Scenarios A–D + timeout/prose/malformed feeds; PR #14 newline regression kept |
| disk | n/a (deterministic). Does not change RW-062 disk facts |
| expected | Class A only if fallback parses model output or splits on newlines against contract |
| actual | **Scenario A** valid JSON plan → `source=llm`, 2 tasks, checks kept. **Scenario B** timeout + seven-sentence goal → `source=fallback`, **7** clause tasks, no checks (`[:7]`). **Scenario C** timeout + ordinary prose goal → 3 clause tasks from the *goal*; seven-line model prose is discarded. **Scenario D** malformed / empty LLM → fallback on goal, capped at 7, not 16, not uncontrolled. One-sentence goal + timeout + seven-line model prose → **1** task. Newline-only goal → **1** task (PR #14). Objective not `VERIFIED` without machine checks. False DONE **0** |
| notes | Trace: `Controller.plan` → `Planner.plan` → `self.llm(PLAN_PROMPT)` → `_json_obj` → `_graph_from` (source=llm) **or** `except` / empty graph → `_fallback(obj)` (source=fallback). `_fallback` never receives `raw`. RW-062 “newline-split” is a mislabel of the documented period/clause split of `obj.goal`. Tool/budget impact: fallback can emit up to 7 no-check tasks; `--max-tasks 4` is a drive stop (4 of 7 attempted), not a planner cap. Default `Budget.tool_calls` **60**. `max_plan_tasks` **16**. Needle `existing`. |

Reproduction (redacted):

```
python3 -m pytest -q tests/test_f17_fallback_investigation.py
# timeout LLM + one-sentence goal → source=fallback, 1 task (goal text)
# timeout LLM + 7 period sentences → source=fallback, 7 tasks ([:7] cap)
# newline-only (no periods) → 1 task
```

| gate | result |
|---|---|
| `python -m pytest -q` | **364 passed** in 8.30s (345 prior + 19 investigation) |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-f17-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-f17-gate/acceptance/20260918-122911_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-f17-rw/realworld/20260918-122908_realworld.json`) |
| Package | **0.2.3** — no bump; **no v0.2.4** |
| RW-058–062 | preserved (live Class B rows + PR #14 investigation) |
| F-20260918-17 | **investigated / not Class A** (timeout does not parse model output; 7 = goal clause split) |
| Class A this record | **NO** |
| Class B this record | none new (RW-062 / F-22 stays B) |
| Class C | n/a (no live NIM this investigation) |
| Patch required | **NO** |
| Regression (product) | **NO** (investigation tests lock current correct behavior) |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Evidence for v0.3.0 | **none** (this F-17 record). Product-owner Gen2 theme 1 later shipped as v0.3.0 — F-20260918-24 / RW-064. |
| Recommendation | **Outcome A — continue 0.2.x** |

## Gen2 / v0.3.0 — Verified coding loop (RW-064) — 2026-09-18

Generation 2 capability expansion, **first accepted theme**. Package **0.2.3 → 0.3.0**.
Control plane preserved (models propose / RAD decides). Needle **OFF**. Caps **not**
raised (`max_plan_tasks` 16, `Budget.tool_calls` 60). RW-058–063 facts are **not
rewritten**. Class A investigations F-17 / F-18 / budget→needs_user stay closed.

Product: when an objective is coding/verification-shaped, RAD drives
**write → run tests/checks → repair** until independent disk checks pass, or
budgets force `needs_user` / fail honestly. A model `DONE:` is never completion.

### F-20260918-24 — verified coding loop (broken artifacts → repair)

| field | value |
|---|---|
| class | **capability** (Gen2 theme 1). Not a re-open of RW-058/062 Class B live 11B incompleteness; not a re-open of F-17/F-18 |
| status | **shipped in v0.3.0** |
| found in | product-owner accepted theme after RW-058 / RW-062 Class B (invalid artifacts, failing tests, `DONE:` pollution; false DONE **0**) |
| fixed in | **v0.3.0** — `rad/control/codingloop.py`; recovery inserts a repair step with concrete check failures (`json_valid`, `shell_ok`, …) instead of unstructured retries; planner infers coding *objective* checks on fallback (fallback *tasks* stay check-less, F-17); `DONE:` pollution paths/content are refused |
| lane | deterministic / scripted (MUST). Live NIM optional |
| objective / test | `tests/test_verified_coding_loop.py`; regressions `false_success` / `needs_user` / budget |
| disk | scripted: wrong `result.json` `{` then repair → valid `{"words": 2}` + tests exit 0 → **VERIFIED**. Persistent `{` / `DONE:` pollution → **not** VERIFIED |
| expected | coding loop reaches VERIFIED iff disk checks pass; false DONE **0** |
| actual | scripted repair path **VERIFIED**; persistent bad artifacts **needs_user** / FAILED, not VERIFIED; F-17 fallback task-check contract held; missing `file_exists` still `retry_with_hint` |
| notes | RW-058 / RW-062 remain Class B live-11B evidence. This PR does not claim those live runs would now pass on 11B. It ships the control-plane loop those rows showed was missing. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_verified_coding_loop.py
# wrong JSON once → repair with "invalid JSON" / "6!=2" → VERIFIED
# persistent `{` + DONE: claims → not VERIFIED; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **373 passed** in 8.37s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v030-gate2`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v030-gate2/acceptance/20260918-130429_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v030-rw2/realworld/20260918-130429_realworld.json`) |
| Package | **0.3.0** |
| RW-058–063 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM | **BLOCKED** (no NVIDIA keys) |

## Live NIM retest of v0.3.0 (RW-065) — 2026-09-18

Operator production follow-up on package **0.3.0** (tag `v0.3.0`, `183ff611`).
Live NVIDIA NIM word_counter vs RW-062. Needle OFF. Caps **unchanged**.
False DONE **0**. RW-058–064 rows are **not rewritten**.

Gen2 theme 1 (verified coding loop) **was used**: `PLAN_CREATED` source=`llm`,
repair inserted, `result.json` valid `{"words": 2}`, no DONE pollution.
Objective still `needs_user` / FAIL on 11B under `--max-tools 12`. **Not** E2E PASS.
Primary residual **Class B**. json_valid-on-.py was a Class A *candidate*;
investigate-first closed it as **NOT CONFIRMED**. Package stays **0.3.0**.

Task log: `docs/REAL_WORLD_TASK_MATRIX.md` RW-065.

### F-20260918-25 — live 11B word_counter on v0.3.0 incomplete (RW-065)

| field | value |
|---|---|
| class | **B** primary. json_valid-on-.py suspected A **not confirmed** (F-20260918-26) |
| status | documented |
| found in | post-v0.3.0 production use (RW-065), rad v0.3.0, 2026-09-18 IST 18:46:10–18:47:36 |
| fixed in | — not a RAD hole to patch from this record; 11B + tool-budget limitation on the same simple coding+verification control as RW-062. Gen2 loop **helped** (repair + valid JSON + no DONE pollution) and did **not** clear the bound. **No v0.3.1.** Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_efed5285` — word_counter.py + result.json words=2 + test_word_counter.py + tests pass; `--max-tasks 4 --max-tools 12`; Needle `existing` / off |
| disk | `word_counter.py` present, broken (`s.split().count()` → TypeError); `result.json` **valid** `{"words": 2}`; `test_word_counter.py` present, `count_words()` NameError (no import); DONE pollution **NONE** |
| expected | v0.3.0 coding loop reaches passing tests + VERIFIED under the same 11B / tools=12 bound as RW-062, or fails honestly without false DONE |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. Tools 12/12 exhausted; model calls 9/80; retries 1/6; wall ~86s / spent 66.7s. Home `/tmp/rad_prod_rw065_ab0919b2`. `PLAN_CREATED` **source=llm** (4 tasks). First task RETRYING (verification FAILED); result.json task COMPLETED/VERIFIED; tests+run PENDING; Gen2 repair `t_6b2926a5` RUNNING at stop. Tests **FAIL**. False DONE **0** |
| notes | vs RW-062: **improved control-plane behavior**, still not E2E PASS. **Not Class C**: NIM key present; doctor READY. RAD stopped at the tool budget; verifier did not rubber-stamp. Outcome: stay 0.3.0. Needle off. Cap 16 unchanged. No architecture change. |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad_prod_rw065_ab0919b2  # rad v0.3.0; nvidia / meta/llama-3.2-11b-vision-instruct
# --max-tasks 4 --max-tools 12; Needle existing/off
# obj_efed5285 → needs_user; tools 12/12; PLAN_CREATED source=llm; Gen2 repair YES
# result.json valid {"words": 2}; tests FAIL NameError; no DONE pollution
```

### F-20260918-26 — json_valid-on-.py Class A **NOT CONFIRMED**

Investigate-first after RW-065. Question: does the planner/control plane
incorrectly accept or emit `json_valid` on `.py` (or non-JSON) paths, causing
false FAILED verification → ENVIRONMENT_FAILURE repair noise?

| field | value |
|---|---|
| class | **NONE** (Class A **not proven**). Live RW-065 remains **B** (F-25) |
| status | **investigated / not Class A** — document only; **no product patch** |
| found in | RW-065 live plan attached `json_valid path=word_counter.py` (and `test_word_counter.py`) described as “valid Python file”; follow-up on `origin/main` `183ff611` / v0.3.0 |
| fixed in | — **not a defect vs current contract.** No patch. Package stays **0.3.0**. **No v0.3.1** |
| lane | scripted planner + verifier + recovery (no NIM). Tests `tests/test_json_valid_py_investigation.py` |
| objective / test | Scenarios A–C + RW-065 ENVIRONMENT reconstruction + architecture freeze |
| disk | n/a (deterministic). Does not change RW-065 disk facts |
| expected | Class A only if RAD *emits* json_valid on `.py`, or if accepting it causes *false* FAILED verify that is then classified ENVIRONMENT |
| actual | **A.** `json_valid` on `.json` OK / invalid JSON fails. **B.** `json_valid` on valid `.py` fails as not-JSON (honest); isolated recovery is `VALIDATION_FAILURE` + Gen2 coding `repair`, **not** `ENVIRONMENT_FAILURE`. LLM plans that emit json_valid-on-.py are kept (models propose; no silent remap). **C.** `infer_coding_checks` / fallback objective checks attach `json_valid` only to `result.json`, plus `shell_ok` for `test_word_counter.py` — never json_valid on `.py`. **Live ENV:** `classify()` reads observation text, not check kinds; shell `No such file` → ENVIRONMENT → “missing dependency/file” (same designed path as F-18). False DONE **0** |
| notes | Trace: `PLAN_PROMPT` “json_valid on every .json artifact”; `Planner._checks` accepts any kind the model proposes; `Verifier.run_check` `json_valid` is `json.loads`; `RecoveryEngine.classify` `_ENV` matches tool output (`no such file`) *before* VALIDATION. Live RW-065 also had actions errors (8 actions, 3 errors) from tests run before files existed — that is the ENV token, not the check kind. Remapping json_valid-on-.py to `shell_ok` / py_compile would be a **new** product rule, not a hole in the current contract. Needle OFF. Caps unchanged. |

Investigation table (F-17 / F-21 style):

| # | claim | result |
|---|---|---|
| 1 | RAD **emits** `json_valid` on `.py` | **NO.** `infer_coding_checks` / `JSON_PATH_RE` only `.json`. Fallback *tasks* stay check-less (F-17). PLAN_PROMPT asks json_valid on `.json` artifacts |
| 2 | RAD **accepts** LLM `json_valid` on `.py` | **YES** — models propose; `_checks` does not remap. Evaluation stays “is JSON?” |
| 3 | That acceptance is a **false** FAILED verification | **NO.** Valid Python is not JSON; verifier `ok: false` is honest. Task never VERIFIED from json_valid-on-.py (false DONE 0) |
| 4 | json_valid-on-.py **causes** ENVIRONMENT_FAILURE repair noise | **NO.** Isolated json_valid-on-.py → `VALIDATION_FAILURE` + coding repair (“Repair so that machine checks pass”). Live RW-065 `ENVIRONMENT_FAILURE` / “missing dependency/file” matches `_ENV` on shell `No such file` observations (F-18 designed path) |
| 5 | Coding inferred checks use json_valid for `.py` | **NO** (Scenario C) |

Reproduction (redacted):

```
python3 -m pytest -q tests/test_json_valid_py_investigation.py
# json_valid result.json → ok
# json_valid word_counter.py (valid Python) → invalid JSON; VALIDATION repair not ENV
# RW-065 goal infer → json_valid only result.json
# shell "No such file" + json_valid-on-py in payload → ENVIRONMENT (check kind ignored)
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **385 passed** in 8.74s (373 prior + 12 investigation) |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw065-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw065-gate/acceptance/20260918-133056_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw065-rw/realworld/20260918-133057_realworld.json`) |
| Package | **0.3.0** — no bump; **no v0.3.1** |
| RW-058–064 | preserved |
| F-20260918-25 | **Class B** (live 11B incompleteness on v0.3.0) |
| F-20260918-26 | **investigated / not Class A** |
| Class A this record | **NO** |
| Class B this record | **F-20260918-25** |
| Class C | **none** (NIM key present on the live lane; this investigation is scripted) |
| Patch required | **NO** |
| Regression (product) | **NO** (investigation tests lock current correct behavior) |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | **stay 0.3.0** |

## Gen2 / v0.3.1 — Plan-timeout resilience (RW-066) — 2026-09-18

Generation 2 capability expansion, **second accepted theme**. Package **0.3.0 → 0.3.1**.
Control plane preserved (models propose / RAD decides). Needle **OFF**. Caps **not**
raised (`max_plan_tasks` 16, `Budget.tool_calls` 60). Default plan retries **1**
(hard cap 3). RW-058–065 facts are **not rewritten**. F-17 / F-18 / F-26 stay closed.

Product: when the LLM planner times out or returns empty/malformed/non-JSON once,
RAD retries for a structured JSON plan with machine checks **before** falling back
to `_fallback(obj)` (goal-only clause split, cap 7, no checks). First-try valid
JSON is unchanged. Exhausted retries still F-17. This does **not** claim live
11B RW-062 / RW-065 would now PASS.

### F-20260918-27 — plan-timeout resilience (retry JSON before fallback)

| field | value |
|---|---|
| class | **capability** (Gen2 theme 2). Not a re-open of F-17 (fallback still goal-only). Not a re-open of RW-062/065 Class B live 11B incompleteness |
| status | **shipped in v0.3.1** |
| found in | product-owner accepted theme after RW-062 (nvidia plan timeout → `source=fallback` → 7 no-check clause tasks) and RW-063 (F-17 NOT CONFIRMED as Class A) |
| fixed in | **v0.3.1** — `Planner.plan` retries (default 1, hard cap 3) with a JSON-only nudge after timeout/empty/malformed/non-JSON/empty-graph; then `_fallback(obj)` unchanged. `PLAN_CREATED` records `attempts`. `plan_retries` readable from home.cfg (not in DEFAULTS; same pattern as `max_plan_tasks`) |
| lane | deterministic / scripted (MUST). Live NIM optional; not claimed as a live PASS |
| objective / test | `tests/test_plan_timeout_resilience.py`; F-17 regressions in `tests/test_f17_fallback_investigation.py` |
| disk | n/a (plan-time). Scripted: timeout then JSON → `source=llm` + checks; exhausted → `source=fallback` + 7 goal clauses, no checks; first-try JSON → 1 attempt |
| expected | one transient plan failure recovers a JSON plan; F-17 holds after exhaustion; false DONE **0**; caps/Needle unchanged |
| actual | timeout/empty/malformed/prose then valid JSON → `source=llm`, checks kept, model prose discarded. Exhausted → goal-only fallback, cap 7. `retries=0` is one-shot. Objective not VERIFIED without machine checks |
| notes | Trace: `Planner.plan` loop `1 + retries` → `_json_obj` → `_graph_from` or `except`/empty graph → retry with `PLAN_RETRY_NUDGE` → `_fallback(obj)`. `_fallback` still never receives `raw`. Planning LLM calls are not charged to `Budget.model_calls` (controller meters execution, not plan). Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_plan_timeout_resilience.py tests/test_f17_fallback_investigation.py
# timeout then JSON → source=llm, 2 attempts, checks kept
# timeout+timeout → source=fallback, 2 attempts, goal clause-split, no checks
# first-try JSON → source=llm, 1 attempt
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **402 passed** in 8.20s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v031-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v031-gate/acceptance/20260918-134136_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v031-rw/realworld/20260918-134142_realworld.json`) |
| Package | **0.3.1** |
| RW-058–065 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM | **BLOCKED** (no NVIDIA keys) — not a live PASS claim |

## Live NIM retest of v0.3.1 (RW-066) — 2026-09-18

Operator production `rad objective run` on package **0.3.1** (tag `v0.3.1`,
`50d98e26`). Same 11B / `--max-tasks 4 --max-tools 12` control as RW-065.
Needle **OFF**. Caps **not** raised. Scripted theme-2 RW-066 (F-27) is **not
rewritten**. RW-058–065 facts are **not rewritten**. F-17 / F-18 / F-26 stay
closed. Theme 2 is **live-confirmed** (`attempts=2` → `source=fallback`).
Residual Class B remains (tools 12/12 mid-repair). Not a claim that all Class B
coding is solved.

Authoritative facts: operator report `obj_e74d9fad` /
`/tmp/rad_prod_rw066_0b0bb188`.

### F-20260918-28 — live 11B word_counter on v0.3.1 **PASS** (RW-066)

| field | value |
|---|---|
| class | **B** residual (11B plan/coding@12). Theme 2 live-confirmed (capability used). Not a re-open of F-17 / F-26. Not false DONE |
| status | **recorded** — live **PASS** (`completed` / **VERIFIED**); disk matched; host tests OK |
| found in | post-v0.3.1 production use (RW-066), rad v0.3.1, 2026-09-18 IST ~19:17–19:19 |
| fixed in | — not a product patch from this record. Live outcome improved vs RW-065 without a new control-plane hole. Theme 3 (budget-aware planning) addresses residual tool-exhaustion, shipped separately as v0.3.2 / F-29 |
| lane | live production `objective run` (NIM 11B) |
| objective / test | RW-065-shaped word_counter; `obj_e74d9fad`; `--auto --max-tasks 4 --max-tools 12`; Needle `existing` / off |
| disk | `word_counter.py` YES (returns 2); `result.json` valid `{"words": 2}`; `test_word_counter.py` YES; host `python3 test_word_counter.py` **PASS** (2 OK); DONE pollution **NONE** |
| expected | Record live use of v0.3.1. Do not invent disk facts. False DONE **0** |
| actual | Status **`completed`**; objective **VERIFIED** (`json_valid` + `shell_ok` tests). `PLAN_CREATED` **source=fallback** **attempts=2** (theme 2 path). Gen2 **repair YES** (`ENVIRONMENT_FAILURE` → `t_4f398815`). Tools **12/12** exhausted; tasks **CANCELLED** with “objective machine checks already satisfied (budget exhausted)”. vs RW-065: better E2E (065 was `needs_user` / tests FAIL). False DONE **0** |
| notes | Theme 2 live-confirmed on NIM 11B for this control. Primary residual **Class B**: LLM plan failed both attempts → mega-task fallback; 11B thrash on `result.json`; budget cut mid-repair. Low-urgency CANCELLED+VERIFIED UX when objective checks already pass — not a false DONE (disk matched). Caps unchanged. Needle OFF. Do not raise max-tools to “fix” this. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw066_0b0bb188 rad objective run "<word_counter goal>" --auto --max-tasks 4 --max-tools 12
# obj_e74d9fad → completed / VERIFIED; PLAN_CREATED source=fallback attempts=2
# result.json valid {"words": 2}; host tests PASS; no DONE pollution; false DONE 0
```

| gate | result |
|---|---|
| Live run | **PASS** (operator report; this agent did not re-run NIM) |
| Package (live) | **0.3.1** |
| RW-058–065 | preserved |
| Scripted RW-066 / F-27 | preserved |
| F-20260918-28 | **Class B residual** + theme 2 **used** |
| Class A this record | **NO** |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60); this run used `--max-tools 12` only |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **PASS**. Theme 3 still relevant. Do not claim all Class B coding is solved. |

## Gen2 / v0.3.2 — Budget-aware planning (RW-067) — 2026-09-18

Generation 2 capability expansion, **third accepted theme**. Package **0.3.1 → 0.3.2**.
Control plane preserved (models propose / RAD decides). Needle **OFF**. Caps **not**
raised (`max_plan_tasks` 16, `Budget.tool_calls` 60). Default plan retries **1**
(hard cap 3). RW-058–065 facts are **not rewritten**. Scripted RW-066 (F-27) and
live RW-066 (F-28) are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

Product: when remaining tool budget is known, a *fat* plan (more tasks than fit
at 2 tools/task, **and** more than 3 tasks) is retried with a budget nudge; the
cheaper graph is selected. Exhausted fallback graphs that are still fat are
compacted. LLM graphs are never silently compacted (F-21 leftover-work:
partial progress then `needs_user` / already-satisfied `VERIFIED`). A model
`DONE:` is never completion. This does **not** claim live 11B Class B coding
would now always PASS.

### F-20260918-29 — budget-aware planning (select a plan that fits N)

| field | value |
|---|---|
| class | **capability** (Gen2 theme 3). Not a re-open of F-17 / F-21 / F-26. Not a cap raise. Not a claim that RW-059/065/066 live 11B incompleteness is gone |
| status | **shipped in v0.3.2** |
| found in | product-owner accepted theme after RW-059 Case B (doubling tools 12→24 did not complete), RW-065/066 tools 12/12 exhausted (066 still VERIFIED via objective checks but cancelled mid-repair) |
| fixed in | **v0.3.2** — `Planner.plan(tool_budget=)` prompt + fat-plan retry (`PLAN_BUDGET_NUDGE`) + cheapest-candidate select; fallback compact via `rad/control/budgetplan.py`; `PLAN_CREATED` records `tool_budget` / `estimated_tools` / `compacted` / `fit`. LLM graphs not compacted. Caps unchanged |
| lane | deterministic / scripted (MUST). Live NIM optional; theme 3 is not claimed as a live PASS |
| objective / test | `tests/test_budget_aware_planning.py`; coding-loop + plan-timeout + F-21 budget regressions still pass |
| disk | n/a (plan-time). Scripted: 8-task fat then 2-task fit → selected 2, estimated 4 ≤ 6. Fallback 7 vs remaining 4 → compacted to 2, no checks. 3-task LLM remaining=1 stays 3. Compacted fallback + `DONE:` is not VERIFIED |
| expected | fat plan that would burn >N tools → emit/select a plan that fits N (or fail honestly); false DONE **0**; caps/Needle unchanged |
| actual | fat-then-fit selected (`source=llm`, checks kept). Two fat plans pick cheaper, not compacted. Fallback compact fits N (F-17 no checks). Default budget 60: 7-clause fallback unchanged. F-21 3-task leftover preserved |
| notes | Cost model `TOOLS_PER_TASK=2` is an estimate, not a new cap. Small graphs may exceed remaining tools by contract (F-21). Intra-task write/test thrash (RW-059 19× write_file) is **not** claimed solved — that would be an executor redesign. Planning LLM calls still not charged to `Budget.model_calls`. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_budget_aware_planning.py tests/test_plan_timeout_resilience.py tests/test_verified_coding_loop.py tests/test_class_a_budget_investigation.py
# fat then fit → 2 tasks, estimated 4 ≤ 6
# fallback 7 vs remaining 4 → compacted 2, no checks
# 3-task LLM remaining=1 → still 3 (F-21)
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **415 passed** in 9.02s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v032-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v032-gate/acceptance/20260918-140012_gate.json`) |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v032-rw/realworld/20260918-140035_realworld.json` |
| Package | **0.3.2** |
| RW-058–065 | preserved |
| Scripted RW-066 / F-27 | preserved |
| Live RW-066 / F-28 | preserved (PASS; Class B residual) |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** if no NVIDIA keys — not a live PASS claim for theme 3 |

## Live NIM use of v0.3.2 (RW-068 / RW-069) — 2026-09-18

Operator production `rad objective run` on package **0.3.2** (tag `v0.3.2`,
`387776dc`). Needle **OFF**. Caps **not** raised. Package stays **0.3.2**.
**No v0.4.0.** RW-058–067 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26
stay closed. A1 (budget→needs_user as Class A) is **not reopened**. A2
(check path vs write path) is a **watch / Gen3 candidate**, not a proven defect.

Authoritative facts: operator campaign `obj_794fb0b3` /
`/tmp/rad_prod_rw068_09177c89` and `obj_1d8cc7ed` /
`/tmp/rad_prod_rw069_89512dd9`. This agent did not re-run NIM.

### F-20260918-30 — live 11B word_counter on v0.3.2 **PASS** (RW-068)

| field | value |
|---|---|
| class | **B** residual (11B@12 tools exhausted mid-repair). Themes 1–2 **used**. Not a re-open of F-17 / F-26. Not false DONE |
| status | **recorded** — live **PASS** (`completed` / **VERIFIED**); valid `result.json` words=2; host tests OK |
| found in | post-v0.3.2 production use (RW-068), rad v0.3.2, 2026-09-18 IST 19:46:33–19:48:01 |
| fixed in | — not a product patch from this record. Planning path improved vs live RW-066 (`llm` attempts **1** vs `fallback` attempts **2**). Package stays **0.3.2**. **No v0.4.0** |
| lane | live production `objective run` (NIM 11B) |
| objective / test | RW-066-shaped word_counter; `obj_794fb0b3`; `--auto --max-tasks 4 --max-tools 12`; Needle `existing` / off |
| disk | `word_counter.py` YES (`split()` / `len(words)` → 2 for `hello world`); `result.json` valid `{"words": 2}`; `test_word_counter.py` YES; host `python3 -m unittest test_word_counter.py` **OK** (1 test); DONE-named files **NONE** |
| expected | Record live use of v0.3.2 on the word_counter control. Do not invent disk facts. False DONE **0** |
| actual | Status **`completed`**; objective **VERIFIED**. `PLAN_CREATED` **source=llm** **attempts=1** (4 tasks with per-task checks). Gen2 **repair YES** (`ENVIRONMENT_FAILURE` → `repair`). First task verify FAILED (actions errors + mis-applied `json_valid` on `.py`); budget exhausted mid-repair; leftover tasks CANCELLED because objective checks already satisfied. Tools **12/12**. Model calls 9/80. Wall ~88s / spent 51.2s. Process exit 0. Agent attempted `write_file` path `DONE: …`; **tool refused**. False DONE **0** |
| notes | vs RW-066: **better plan path** (llm@1 vs fallback@2); same end VERIFIED. Simple verified coding loop is **stable PASS** on v0.3.2 (B3). A3 DONE-pollution refuse **already works**. Caps unchanged. Needle OFF. Do not raise max-tools to “fix” residual 12/12. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw068_09177c89 rad objective run "<word_counter goal>" --auto --max-tasks 4 --max-tools 12
# obj_794fb0b3 → completed / VERIFIED; PLAN_CREATED source=llm attempts=1
# result.json valid {"words": 2}; host tests OK; no DONE pollution; false DONE 0
```

### F-20260918-31 — live 11B text_analyzer on v0.3.2 **FAIL** (RW-069)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / F-20260918-16 / F-20260918-19). A2 path-vs-write **watch**, **not proven Class A** |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Artifacts incomplete / incorrect |
| found in | post-v0.3.2 production use (RW-069), rad v0.3.2, 2026-09-18 IST 19:48:29–19:51:22 |
| fixed in | — not a RAD hole to patch from this record; 11B + tools=12 multi-file limitation. **No v0.4.0.** Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_1d8cc7ed` — production `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off. 24-tool follow-up **not run** |
| disk | RAD-at-stop: `text_analyzer/analyzer.py` YES (buggy `str.split('\\s+')`; writes `chars` not `characters`); `text_analyzer/input.txt` YES **wrong 1-line**; `text_analyzer/summary.json` **NO**; `text_analyzer/test_analyzer.py` YES (weak `assertGreater`); `text_analyzer/README.md` YES; workspace-root `input.txt` / `README.md` / `summary.json` YES (retry thrash). input.txt sha256 actual `9bf9660fcac9d5a1cd5906dd8a8d42e4a9aedaa25847d6412ad53abf517d41aa` ≠ expected 3-line `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` (no trailing NL) / `5c376e468fe70a63e0d5341908cc7b1b283b7508458fd988d3f4f79a54ea3ec6` (trailing NL). Root `summary.json` `{"lines": 13, "words": 13, "characters": 76}` — valid JSON, counts do **not** match a correct 3-line analysis |
| expected | required layout under `text_analyzer/`; exact 3-line input; package `summary.json`; tests that assert exact counts; `VERIFIED` only from machine checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=1**. Recovery **retry_with_hint** (`VALIDATION_FAILURE`) — not Gen2 `repair` insert. Tools **12/12** exhausted. Spent 117.3s; wall ~173s; process exit 2. False DONE **0**. Host post-run unittest under `text_analyzer/` reported OK only because tests are non-assertive and created `summary.json` as a side effect — **do not treat as campaign PASS** |
| notes | Failure mode: (1) planner checks pointed at workspace-root `input.txt` while first writes were under `text_analyzer/` → VALIDATION_FAILURE; (2) retry flattened files to workspace root; still wrong newline structure (spaces instead of newlines between the three sentences); (3) tool budget 12 exhausted before package completion; (4) optional mid-call `DONE:`-named path write observed in console; no DONE pollution file remained on disk. Planning healthier than historical RW-058-family thrash; **artifact quality still Class B fail**. A1: do **not** reopen budget→needs_user as Class A without new proof. B2: optional tools=24 follow-up warranted later as a Gen3 baseline (not run here). Caps unchanged. Needle OFF. No architecture change. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw069_89512dd9 rad objective run "<text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_1d8cc7ed → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=1
# retry_with_hint VALIDATION_FAILURE; input.txt sha256 9bf9660f… (1-line); package summary.json missing
```

| gate | result |
|---|---|
| Live run RW-068 | **PASS** (operator campaign; this agent did not re-run NIM) |
| Live run RW-069 | **FAIL** `needs_user` / not VERIFIED (operator campaign) |
| Package | **0.3.2** — no bump; **no v0.4.0** |
| RW-058–067 | preserved |
| F-20260918-30 | **PASS** + Class B residual (tools 12/12 mid-repair) |
| F-20260918-31 | **Class B** (text_analyzer@12 still fail) |
| Class A this record | **NO** (A2 watch only; A1 not reopened; A3 refuse already works) |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60); these runs used `--max-tools 12` only |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record RW-068 **PASS** + RW-069 **FAIL**. Gen2 complete enough to **scope** Gen3; do not implement v0.4.0 until a first theme is accepted. |

## Gen3 / v0.4.0 — Path-aligned checks / package layout (RW-070) — 2026-09-18

Generation 3 autonomous-agent maturity, **first accepted theme**. Package
**0.3.2 → 0.4.0**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–069 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**.

Product: when a coding goal names a package layout, RAD joins bare machine-check
paths to that directory (and remaps LLM root-only checks the same way) so package
writes are not failed as missing root files. The verifier still evaluates the
stored path honestly. A model `DONE:` is never completion.

### F-20260918-32 — path-aligned checks (package layout)

| field | value |
|---|---|
| class | **A** (RAD emitted and accepted root-only checks that disagree with a named package layout). Capability (Gen3 theme 1). Not a re-open of RW-069 live 11B artifact quality (wrong 1-line input, missing package `summary.json`, weak tests) |
| status | **shipped in v0.4.0** |
| found in | RW-069 / F-20260918-31 A2 watch (v0.3.2 live 11B text_analyzer); investigate-first on `3f59f8b5` |
| fixed in | **v0.4.0** — `infer_package_dir` + path join in `rad/control/codingloop.py`; LLM check ingest in `Planner._graph_from`; PLAN_PROMPT asks for package-prefixed check paths. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Verifier does not guess a package dir at check time |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_path_aligned_checks.py`; RW-070 |
| disk | scripted: package writes under `text_analyzer/` + LLM root-only `input.txt` / `summary.json` checks → checks become `text_analyzer/…` → first attempt **VERIFIED**. No workspace-root `input.txt` / `summary.json`. Unaligned verifier `file_exists input.txt` while the file is under the package is still an honest fail (VALIDATION, not ENVIRONMENT) |
| expected | Checks for files under a package dir use that package-relative path; scripted package writes + root-only checks are corrected without false ENVIRONMENT/VALIDATION thrash; false DONE **0** |
| actual | infer joins brace-list / `under pkg/` / 2+ common-prefix files; LLM root checks remapped; word_counter root paths unchanged; single `pkg/foo.py` is not a layout (realworld coding / multi_agent preserved); fallback tasks check-less |
| notes | Live RW-069 remains Class B on artifact quality and tools=12. This PR does **not** claim that live 11B text_analyzer would now PASS. A1 not reopened. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_path_aligned_checks.py
# package writes + root-only LLM checks → VERIFIED; no root pollution; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **435 passed** in 8.60s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v040-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v040-gate/acceptance/20260918-144259_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v040-rw/realworld/20260918-144303_realworld.json`) |
| Package | **0.4.0** |
| RW-058–069 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-069 |

## Live NIM retest of v0.4.0 (RW-071) — 2026-09-18

Operator production `rad objective run` on package **0.4.0** (tag `v0.4.0`,
`a8aac8ae`). Needle **OFF**. Caps **not** raised. RW-058–070 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 (budget→needs_user as
Class A) is **not reopened**. Theme 1 path-alignment is **live-confirmed**.

Authoritative facts: operator report `obj_d662224b` /
`/tmp/rad_prod_rw071_7811425c`. This agent did not re-run NIM.

### F-20260918-33 — live 11B text_analyzer on v0.4.0 **FAIL** (RW-071)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / 16 / 19 / 31). Theme 1 path-alignment **live-confirmed** (not Class A regression) |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 **Y**. Residual Class B |
| found in | post-v0.4.0 production use (RW-071), rad v0.4.0, 2026-09-18 IST 20:18:41–20:20:53 |
| fixed in | — live 11B artifact quality **not** claimed fixed. Theme 2 control-plane patch is **v0.4.1** (F-20260918-34). Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_d662224b` — production `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **wrong 1-line** sha256 `9bf9660fcac9d5a1cd5906dd8a8d42e4a9aedaa25847d6412ad53abf517d41aa` ≠ expected 3-line `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present, 0 bytes, invalid JSON**. `analyzer.py` stdlib (never ran as `__main__`). `test_analyzer.py` unittest `1 != 3`. README present |
| expected | required layout under `text_analyzer/`; exact 3-line input; non-empty valid package `summary.json`; tests that assert exact counts; `VERIFIED` only from machine checks; path-aligned checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=1** (6 tasks). Path-aligned checks **Y**. Recovery **ENVIRONMENT_FAILURE** → `repair` (“Repair prerequisite”) on mkdir-already-exists + empty `summary.json` among action/shell check noise; repair rewrote files, did not fill empty summary. Tools **12/12** (`write_file` 11, `run_shell` 1). Model calls 9/80. Retries 1/6. Wall ~95s reported / ~132s. Process exit 2. False DONE **0** |
| notes | vs RW-069: theme-1 path-misalignment **closed** (checks under `text_analyzer/`; no root pollution). Same Class B stop: wrong 1-line input `9bf9660f…`, empty/invalid package `summary.json`, tools exhausted mid-repair. Create input.txt auto-completed on weak exists/min-bytes/contains-first-sentence checks — not a full objective false DONE. Caps unchanged. Needle OFF. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw071_7811425c rad objective run "<text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_d662224b → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=1
# path-alignment Y; input.txt sha256 9bf9660f… (1-line); package summary.json empty
```

## Gen3 / v0.4.1 — Multi-file contracts under tight budgets (RW-072) — 2026-09-18

Generation 3 autonomous-agent maturity, **second accepted theme**. Package
**0.4.0 → 0.4.1**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–071 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**.

Product: coding/package goals merge omitted `json_valid` / `file_line_count` /
test `shell_ok` into objective checks so weak `file_exists` artifacts cannot
become VERIFIED; mkdir/create **already exists** is not ENVIRONMENT (no Repair
prerequisite thrash). The verifier still evaluates stored paths honestly. A
model `DONE:` is never completion. Does **not** claim live 11B text_analyzer@12
now PASS.

### F-20260918-34 — multi-file contracts / already-exists not ENVIRONMENT

| field | value |
|---|---|
| class | **A** (weak LLM `file_exists` objective checks could pass an empty `summary.json` / 1-line input; mkdir already-exists mixed with no-such-file noise classified ENVIRONMENT and burned tools on Repair prerequisite). Capability (Gen3 theme 2). Not a re-open of RW-071 live 11B artifact quality |
| status | **shipped in v0.4.1** |
| found in | RW-071 / F-20260918-33 (v0.4.0 live 11B text_analyzer); investigate-first on `a8aac8ae` |
| fixed in | **v0.4.1** — `merge_coding_checks` + `file_line_count` in `rad/control/codingloop.py` / `verifier.py`; `_ALREADY_EXISTS` skip in `classify()` (`rad/control/recovery.py`); PLAN_PROMPT no standalone mkdir. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Genuine `command not found` still ENVIRONMENT |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_multifile_tight_budget.py`; RW-072 |
| disk | scripted: 1-line input + empty `summary.json` + weak LLM `file_exists` → objective **not VERIFIED** (`json_valid` + `file_line_count` + `shell_ok`). mkdir File-exists + cat no-such-file + empty JSON → **not** ENVIRONMENT / not Repair prerequisite. 3-line + valid JSON + tests still **VERIFIED**. No workspace-root pollution |
| expected | Weak artifacts fail earlier with useful structure; already-exists does not spend remaining tools on ENVIRONMENT mkdir repair; false DONE **0**; path-aligned checks preserved |
| actual | infer/merge adds package `json_valid` / exact-3-line `file_line_count` / test `shell_ok`; already-exists mixed noise is TOOL/VALIDATION coding repair; F-18 command-not-found ENVIRONMENT preserved; word_counter root paths unchanged |
| notes | Live RW-071 remains Class B on 11B quality and tools=12. This PR does **not** claim that live 11B text_analyzer would now PASS. A1 not reopened. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_multifile_tight_budget.py
# weak 1-line + empty JSON → not VERIFIED; already-exists ≠ ENVIRONMENT; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **446 passed** in 9.01s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v041-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v041-gate/acceptance/20260918-150234_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v041-rw/realworld/20260918-150234_realworld.json`) |
| Package | **0.4.1** |
| RW-058–071 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-071 |

## Live NIM retest of v0.4.1 (RW-073) — 2026-09-18

Operator production `rad objective run` on package **0.4.1** (tag `v0.4.1`,
`387bd83a`). Needle **OFF**. Caps **not** raised. RW-058–072 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 (budget→needs_user as
Class A) is **not reopened**. Theme 1 disk/task path-alignment and theme 2
contracts / mkdir-class are **live-confirmed**. ASCII-tree `infer_package_dir`
miss is a separate Class A (F-36).

Authoritative facts: operator report `obj_d8bd898a` /
`/tmp/rad_prod_rw073_46da6971`. This agent did not re-run NIM.

### F-20260918-35 — live 11B text_analyzer on v0.4.1 **FAIL** (RW-073)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / 16 / 19 / 31 / 33). Theme 1 disk/tasks **Y**; theme 2 contracts + mkdir-class **Y**. ASCII-tree obj-check paths are F-36, not this live stop |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 **Y** (partial obj-checks). Theme 2 **Y**. Residual Class B |
| found in | post-v0.4.1 production use (RW-073), rad v0.4.1, 2026-09-18 IST 20:39:05–20:41:06 |
| fixed in | — live 11B artifact quality **not** claimed fixed. ASCII-tree `package_dir` patch is **v0.4.2** (F-20260918-36). Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_d8bd898a` — production ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **missing**. `analyzer.py` stdlib (import-time analyze). `test_analyzer.py` unittest **no count assertions**. README present (~479 B) |
| expected | required layout under `text_analyzer/`; exact 3-line input; non-empty valid package `summary.json`; tests that assert exact counts; `VERIFIED` only from machine checks; path-aligned task **and** inferred objective checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=2** (4 tasks). Path-aligned task checks **Y**. Inferred objective contracts **bare**. Recovery **PERMISSION_FAILURE** → `retry_with_hint` (mkdir already-exists then `rm -rf` blocked; **not** ENVIRONMENT). Attempt 2 fake tool `DONE` → `unknown tool: DONE`; machine checks still ✓. Tools **12/12**. Model calls 14/80. Retries 2/6. Wall ~63s reported / ~121s. Process exit 2. False DONE **0** |
| notes | vs RW-071: improved input (`bf69eb73…` vs `9bf9660f…`) + recovery class (PERMISSION not ENVIRONMENT mkdir thrash). Same Class B stop: missing `summary.json`, weak tests, tools exhausted on first-task retries before later package tasks ran. Caps unchanged. Needle OFF. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw073_46da6971 rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_d8bd898a → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=2
# path-alignment Y (disk/tasks); input.txt sha256 bf69eb73… (3-line); package summary.json missing
```

## Gen3 / v0.4.2 — ASCII-tree package_dir (RW-074) — 2026-09-18

Generation 3 autonomous-agent maturity, **theme 3 planned / scoped**; **slice A**
(ASCII-tree `package_dir`) is a **theme-1 follow-up**. Package **0.4.1 → 0.4.2**.
Control plane preserved (models propose / RAD decides). Needle **OFF**. Caps
**not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60). RW-058–073 facts
are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1
(budget→needs_user as Class A) is **not reopened**. Remaining theme-3 slices
(first-task thrash, multi-step checkpoint) are **not** built.

Product: ASCII / box-drawing tree goals (`pkg/` + `├── file`) set
`infer_package_dir` so inferred `json_valid` / `file_line_count` / test
`shell_ok` join to the package, same as `under pkg/`. LLM root-only checks
are remapped the same way. Markdown dash lists, `docs/` trees, a single
tree child, and word_counter root files stay un-packaged. The verifier still
evaluates stored paths honestly. A model `DONE:` is never completion. Does
**not** claim live 11B text_analyzer@12 now PASS.

### F-20260918-36 — ASCII-tree `infer_package_dir` miss

| field | value |
|---|---|
| class | **A** (ASCII-tree package-layout goals left `infer_package_dir` None, so merged objective contracts stayed bare `summary.json` / `input.txt` while task checks and disk used `text_analyzer/`). Theme-1 follow-up / Gen3 theme 3 slice A. Not a re-open of RW-073 live 11B artifact quality |
| status | **shipped in v0.4.2** |
| found in | RW-073 / F-20260918-35 (v0.4.1 live 11B text_analyzer); investigate-first on `387bd83a` |
| fixed in | **v0.4.2** — `_ascii_tree_package_dir` in `rad/control/codingloop.py` `infer_package_dir`. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Verifier does not guess a package dir at check time |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_ascii_tree_package_dir.py`; RW-074 |
| disk | scripted: ASCII-tree goal → `infer_package_dir` `text_analyzer/`; inferred + merged objective checks under the package; LLM root-only checks joined; dash-list / `docs/` / single child / word_counter unchanged |
| expected | Tree layouts join objective inferred checks the same way as `under pkg/` / brace / two-or-more `pkg/foo`; false DONE **0**; theme-2 contracts preserved |
| actual | box-drawing and `|--` trees return `text_analyzer/`; `json_valid` / `file_line_count` / `shell_ok` paths are package-prefixed; existing non-tree forms unchanged |
| notes | Live RW-073 remains Class B on 11B quality and tools=12. This PR does **not** claim that live 11B text_analyzer would now PASS. A1 not reopened. Remaining theme-3 slices stay planned. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_ascii_tree_package_dir.py
# ASCII-tree → text_analyzer/; bare inferred paths joined; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **457 passed** in 9.45s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v042-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v042-gate/acceptance/20260918-152358_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v042-rw/realworld/20260918-152404_realworld.json`) |
| Package | **0.4.2** |
| RW-058–073 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-073 |

## Live NIM retest of v0.4.2 (RW-075) — 2026-09-18

Operator production `rad objective run` on package **0.4.2** (tag `v0.4.2`,
`feb8a4ec`). Needle **OFF**. Caps **not** raised. RW-058–074 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 (budget→needs_user as
Class A) is **not reopened**. ASCII-tree `package_dir` is **live-confirmed**.

Authoritative facts: operator report `obj_476d5f0e` /
`/tmp/rad_prod_rw075_c2d7abdd`. This agent did not re-run NIM.

### F-20260918-37 — live 11B text_analyzer on v0.4.2 **FAIL** (RW-075)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / 16 / 19 / 31 / 33 / 35). Theme 1 ASCII-tree obj-checks **live-confirmed** (not Class A regression). First-task pip ENVIRONMENT is F-38, not this live stop's 11B quality residual |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 **Y** (obj-checks package-joined). Theme 2 **Y**. Residual Class B |
| found in | post-v0.4.2 production use (RW-075), rad v0.4.2, 2026-09-18 IST 21:20:12–21:21:38 |
| fixed in | — live 11B artifact quality **not** claimed fixed. First-task thrash patch is **v0.4.3** (F-20260918-38). Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_476d5f0e` — production ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **missing**. `analyzer.py` stdlib. `test_analyzer.py` unittest **wrong oracles** (`words==6` / `characters==31` vs true 13 / 76). README 247 B |
| expected | required layout under `text_analyzer/`; exact 3-line input; non-empty valid package `summary.json`; tests that assert exact counts; `VERIFIED` only from machine checks; path-aligned task **and** inferred objective checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=1** (4 tasks). Path-aligned task checks **Y**. Objective checks **all package-joined** (0 bare). Recovery **ENVIRONMENT_FAILURE** → `repair` (“Repair prerequisite”) on 4× `pip install -r …requirements.txt` file-not-found; then **TOOL_FAILURE** unknown tool `DONE: …`. Tools **12/12**. Model calls 12/80. Retries 2/6. Wall ~87s / spent ≈53.6s. Process exit 2. False DONE **0** |
| notes | vs RW-073: ASCII-tree obj-check bare residual **closed**. Same Class B stop: missing `summary.json`, weak tests, tools exhausted on first-task retries before later package tasks ran. Recovery class flipped PERMISSION → ENVIRONMENT (pip). Caps unchanged. Needle OFF. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw075_c2d7abdd rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_476d5f0e → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=1
# objective_checks package-joined; input.txt sha256 bf69eb73… (3-line); package summary.json missing
```

## Gen3 / v0.4.3 — First-task thrash (RW-076) — 2026-09-18

Generation 3 autonomous-agent maturity, **theme 3 slice B**. Package
**0.4.2 → 0.4.3**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–075 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**. Multi-step checkpoint
is **not** built.

Product: `pip install -r` when the requirements file is missing is **not**
ENVIRONMENT (no Repair-prerequisite insert for stdlib-only coding). An invented
tool named `DONE` / `DONE: …` still errors, but does not fail a task whose
explicit machine checks passed, so later independent tasks can still run.
Genuine `command not found` / `ModuleNotFoundError` stay ENVIRONMENT. The
verifier still evaluates stored paths honestly. A model `DONE:` is never
completion. Does **not** claim live 11B text_analyzer@12 now PASS.

### F-20260918-38 — first-task thrash (pip-missing-requirements ENVIRONMENT + DONE-as-tool)

| field | value |
|---|---|
| class | **A** (`pip install -r` file-not-found classified ENVIRONMENT and burned tools on Repair prerequisite; unknown tool `DONE` failed a task whose file checks already passed, starving later package tasks). Capability (Gen3 theme 3 slice B). Not a re-open of RW-075 live 11B artifact quality |
| status | **shipped in v0.4.3** |
| found in | RW-075 / F-20260918-37 (v0.4.2 live 11B text_analyzer); investigate-first on `feb8a4ec` |
| fixed in | **v0.4.3** — `is_pip_requirements_file_missing` skip in `classify()`; `is_done_protocol_tool` / `is_first_task_thrash_noise` in verifier actions; PLAN_PROMPT no pip-requirements / DONE-as-tool. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Genuine `command not found` still ENVIRONMENT (F-18) |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_first_task_thrash.py`; RW-076 |
| disk | scripted: 3-line input + pip -r missing + DONE tool → first task **VERIFIED**; later `analyzer.py` task runs; no Repair prerequisite; missing-artifact DONE is **not** VERIFIED. No workspace-root pollution |
| expected | Missing requirements.txt does not spend remaining tools on ENVIRONMENT pip repair; invented DONE does not fail check-passing tasks; false DONE **0**; path-aligned / multifile / ASCII-tree preserved |
| actual | pip-missing-requirements is TOOL not ENVIRONMENT; DONE protocol noise ignored for actions when checks can still pass; F-18 command-not-found ENVIRONMENT preserved; mkdir already-exists still not ENVIRONMENT |
| notes | Live RW-075 remains Class B on 11B quality and tools=12. This PR does **not** claim that live 11B text_analyzer would now PASS. A1 not reopened. Multi-step checkpoint stays planned. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_first_task_thrash.py
# pip -r missing ≠ ENVIRONMENT; DONE-as-tool ≠ fail check-passing task; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **472 passed** in 11.30s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v043-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v043-gate/acceptance/20260918-160450_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v043-rw/realworld/20260918-160457_realworld.json`) |
| Package | **0.4.3** |
| RW-058–075 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-075 |

## Live NIM retest of v0.4.3 (RW-077) — 2026-09-18

Operator production `rad objective run` on package **0.4.3** (tag `v0.4.3`,
`99099b8a`). Needle **OFF**. Caps **not** raised. RW-058–076 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 (budget→needs_user as
Class A) is **not reopened**. v0.4.3 pip/DONE Class A is **live-consistent**.

Authoritative facts: operator report `obj_3da359c5` /
`/tmp/rad_prod_rw077_0a8393f8`. This agent did not re-run NIM.

### F-20260918-39 — live 11B text_analyzer on v0.4.3 **FAIL** (RW-077)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / 16 / 19 / 31 / 33 / 35 / 37). Theme 1 ASCII-tree obj-checks **Y**. v0.4.3 pip/DONE Class A **not live**. mkdir File-exists actions is F-40, not this live stop's 11B quality residual |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 **Y**. Theme 2 **Y**. Residual Class B |
| found in | post-v0.4.3 production use (RW-077), rad v0.4.3, 2026-09-18 IST 21:45:54–21:47:37 |
| fixed in | — live 11B artifact quality **not** claimed fixed. mkdir already-exists action-noise patch is **v0.4.4** (F-20260918-40). Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_3da359c5` — production ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present but empty/invalid** (0 bytes). `analyzer.py` stdlib. `test_analyzer.py` unittest **wrong oracles** (`words==6` / `chars==31` vs true 13 / 76). README 16 B |
| expected | required layout under `text_analyzer/`; exact 3-line input; non-empty valid package `summary.json`; tests that assert exact counts; `VERIFIED` only from machine checks; path-aligned task **and** inferred objective checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=1** (5 tasks). Path-aligned task checks **Y**. Objective checks **all package-joined** (0 bare). Recovery **TOOL_FAILURE** → `retry_with_hint` on `mkdir text_analyzer` File exists after `write_file` created the tree (directory `file_exists` **passed**; overall FAILED on **actions**). **No** ENVIRONMENT. **No** Repair-prerequisite. Tools **12/12** (`write_file`×4, `run_shell`×8; **0** pip, **0** fake DONE). Model calls 9/80. Retries 1/6. Wall ~103s / spent ≈55.9s. Process exit 2. False DONE **0** |
| notes | vs RW-075: Class A pip-ENVIRONMENT + fake-DONE thrash **gone** (v0.4.3 live-consistent). Same Class B stop: incomplete package, tools exhausted on first-task retry before later package tasks ran. Residual thrash shifted to mkdir File-exists. Caps unchanged. Needle OFF. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw077_0a8393f8 rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_3da359c5 → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=1
# objective_checks package-joined; input.txt sha256 bf69eb73… (3-line); summary.json empty/invalid
```

## Gen3 / v0.4.4 — mkdir already-exists action noise (RW-078) — 2026-09-18

Generation 3 autonomous-agent maturity, **theme 3 slice C**. Package
**0.4.3 → 0.4.4**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–077 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**. Multi-step checkpoint
is **not** built.

Product: `mkdir` / create **already exists** after `write_file` created the
tree still records as a tool error (honesty) but does **not** fail a task whose
explicit directory/file checks passed, so later independent tasks can still run.
v0.4.1 already-exists **not ENVIRONMENT** is preserved. Genuine `command not
found` / `ModuleNotFoundError` stay ENVIRONMENT. Permission-denied mkdir stays
a real error. The verifier still evaluates stored paths honestly. A model
`DONE:` is never completion. Does **not** claim live 11B text_analyzer@12 now
PASS.

### F-20260918-40 — mkdir File-exists failing a check-passing task

| field | value |
|---|---|
| class | **A** (`mkdir text_analyzer` File exists after `write_file` created the tree failed the actions check even though directory `file_exists` passed, triggering TOOL_FAILURE retry that burned the 12-tool budget and starved later package tasks). Capability (Gen3 theme 3 slice C). Not a re-open of RW-077 live 11B artifact quality |
| status | **shipped in v0.4.4** |
| found in | RW-077 / F-20260918-39 (v0.4.3 live 11B text_analyzer); investigate-first on `99099b8a` |
| fixed in | **v0.4.4** — `is_mkdir_already_exists` in `is_first_task_thrash_noise` (verifier actions); PLAN_PROMPT no redundant mkdir after write_file. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Genuine `command not found` still ENVIRONMENT (F-18). mkdir already-exists still **not** ENVIRONMENT (v0.4.1) |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_mkdir_already_exists_actions.py`; RW-078 |
| disk | scripted: write_file creates `text_analyzer/` then mkdir File-exists → first task **VERIFIED**; later `analyzer.py` task runs; no Repair prerequisite; empty JSON still **not** VERIFIED. No workspace-root pollution |
| expected | mkdir File-exists does not fail a check-passing directory task; later package tasks can still run; false DONE **0**; path-aligned / multifile / ASCII-tree / pip-DONE thrash preserved |
| actual | mkdir already-exists is TOOL not ENVIRONMENT; treated as action noise when directory/file checks can still pass; F-18 command-not-found ENVIRONMENT preserved; empty JSON still FAILED |
| notes | Live RW-077 remains Class B on 11B quality and tools=12. This PR does **not** claim that live 11B text_analyzer would now PASS. A1 not reopened. Multi-step checkpoint stays planned. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_mkdir_already_exists_actions.py
# mkdir File-exists ≠ ENVIRONMENT; ≠ fail check-passing task; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **484 passed** in 9.12s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v044-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v044-gate/acceptance/20260918-163149_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v044-rw/realworld/20260918-163146_realworld.json`) |
| Package | **0.4.4** |
| RW-058–077 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-077 |

## Live NIM retest of v0.4.4 (RW-079) — 2026-09-18

Operator production `rad objective run` on package **0.4.4** (tag `v0.4.4`,
`acb61997`). Needle **OFF**. Caps **not** raised. RW-058–078 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 (budget→needs_user as
Class A) is **not reopened**. v0.4.4 mkdir File-exists Class A is **not
live-hit**.

Authoritative facts: operator report `obj_a0781a42` /
`/tmp/rad_prod_rw079_803109d5`. This agent did not re-run NIM.

### F-20260918-41 — live 11B text_analyzer on v0.4.4 **FAIL** (RW-079)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / 16 / 19 / 31 / 33 / 35 / 37 / 39). Theme 1 ASCII-tree obj-checks **Y**. mkdir File-exists Class A **live: N**. Premature-test ENVIRONMENT is F-42, not this live stop's 11B quality residual |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 **Y**. Theme 2 **Y**. Residual Class B |
| found in | post-v0.4.4 production use (RW-079), rad v0.4.4, 2026-09-18 IST 22:07:24–22:09:09 |
| fixed in | — live 11B artifact quality **not** claimed fixed. Premature-test ENVIRONMENT patch is **v0.4.5** (F-20260918-42). Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_a0781a42` — production ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **valid JSON, wrong counts** (`{"lines": 3, "words": 7, "characters": 39}` vs true 3 / 13 / 76). `analyzer.py` stdlib. `test_analyzer.py` asserts **wrong oracles** (`words==9` / `chars==51`). README 166 B (≥100) |
| expected | required layout under `text_analyzer/`; exact 3-line input; non-empty valid package `summary.json` with correct counts; tests that assert exact counts; `VERIFIED` only from machine checks; path-aligned task **and** inferred objective checks |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=1** (5 tasks + 1 repair). Path-aligned task checks **Y**. Objective checks **all package-joined** (0 bare). Recovery **ENVIRONMENT_FAILURE** → `repair` (“Repair prerequisite”) on premature `python …/test_analyzer.py` No-such-file (directory `file_exists` **passed**; overall FAILED on **actions**). **Not** mkdir File-exists (mkdir succeeded). Tools **12/12** (`write_file`×6, `run_shell`×6; **0** pip, **0** invented DONE). Model calls 9/80. Retries 1/6. Wall ~105s / spent ≈67.2s. Process exit 2. False DONE **0** |
| notes | vs RW-077: still FAIL. mkdir File-exists **not exercised**. Residual thrash shifted to premature-test ENVIRONMENT repair. Caps unchanged. Needle OFF. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw079_803109d5 rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_a0781a42 → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=1
# objective_checks package-joined; input.txt sha256 bf69eb73… (3-line); summary.json valid JSON, wrong counts
```

## Gen3 / v0.4.5 — Premature-test ENVIRONMENT (RW-080) — 2026-09-18

Generation 3 autonomous-agent maturity, **theme 3 slice D**. Package
**0.4.4 → 0.4.5**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–079 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**. Multi-step checkpoint
is **not** built.

Product: premature `python …/test_*.py` (CPython `can't open file` a `.py`
script the agent has not written) is **not** ENVIRONMENT (no Repair-prerequisite
insert). It still records as a tool error (honesty) but does **not** fail a task
whose explicit directory/file checks passed, so later independent tasks can still
run. Genuine `command not found` / `ModuleNotFoundError` stay ENVIRONMENT.
`cat` no-such-file stays ENVIRONMENT (F-18). Nested `FileNotFoundError` inside a
running script is not this signal. mkdir File-exists action noise (v0.4.4) is
preserved. The verifier still evaluates stored paths honestly. A model `DONE:`
is never completion. Does **not** claim live 11B text_analyzer@12 now PASS.

### F-20260918-42 — premature python test No-such-file classified ENVIRONMENT

| field | value |
|---|---|
| class | **A** (`python text_analyzer/test_analyzer.py` before the test file existed classified ENVIRONMENT and burned tools on Repair prerequisite even though directory `file_exists` already passed). Capability (Gen3 theme 3 slice D). Not a re-open of RW-079 live 11B artifact quality |
| status | **shipped in v0.4.5** |
| found in | RW-079 / F-20260918-41 (v0.4.4 live 11B text_analyzer); investigate-first on `acb61997` |
| fixed in | **v0.4.5** — `is_missing_python_script` skip in `classify()`; same helper in `is_first_task_thrash_noise` (verifier actions); PLAN_PROMPT do not run tests before writing them. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Genuine `command not found` still ENVIRONMENT (F-18). mkdir already-exists still **not** ENVIRONMENT / still action noise (v0.4.1 / v0.4.4) |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_premature_test_env.py`; RW-080 |
| disk | scripted: write_file creates `text_analyzer/` then premature `python3 …/test_analyzer.py` → first task **VERIFIED**; later `analyzer.py` task runs; no Repair prerequisite; empty JSON still **not** VERIFIED. No workspace-root pollution |
| expected | Premature test invoke does not spend remaining tools on ENVIRONMENT repair; does not fail a check-passing directory task; later package tasks can still run; false DONE **0**; path-aligned / multifile / ASCII-tree / pip-DONE / mkdir-File-exists preserved |
| actual | python can't-open-file on a `.py` script is TOOL not ENVIRONMENT; treated as action noise when directory/file checks can still pass; F-18 command-not-found / ModuleNotFoundError / cat no-such-file ENVIRONMENT preserved; empty JSON still FAILED; mkdir File-exists still noise |
| notes | Live RW-079 remains Class B on 11B quality and tools=12. This PR does **not** claim that live 11B text_analyzer would now PASS. A1 not reopened. Multi-step checkpoint stays planned. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_premature_test_env.py
# premature python test ≠ ENVIRONMENT; ≠ fail check-passing task; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **500 passed** in 10.64s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-v045-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-v045-gate/acceptance/20260918-165029_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-v045-rw/realworld/20260918-165030_realworld.json`) |
| Package | **0.4.5** |
| RW-058–079 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-079 |

## Live NIM retest of v0.4.5 (RW-081) — 2026-09-18

Operator production `rad objective run` on package **0.4.5** (tag `v0.4.5`,
`32e9fe87`). Needle **OFF**. Caps **not** raised. RW-058–080 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 (budget→needs_user as
Class A) is **not reopened**. v0.4.4 mkdir File-exists Class A is **live-confirmed**.
v0.4.5 premature-test ENVIRONMENT Class A is **not live-hit**. Pip thrash +
root pollution Class A is **NOT CONFIRMED** (F-44). Package stays **0.4.5**.

Authoritative facts: operator report `obj_b6d32fcc` /
`/tmp/rad_prod_rw081_5a76b128`. This agent did not re-run NIM.

### F-20260918-43 — live 11B text_analyzer on v0.4.5 **FAIL** (RW-081)

| field | value |
|---|---|
| class | **B** (same family as F-20260918-15 / 16 / 19 / 31 / 33 / 35 / 37 / 39 / 41). Theme 1 ASCII-tree obj-checks **Y**. mkdir File-exists Class A **live: Y**. Premature-test ENVIRONMENT Class A **live: N**. Pip/echo + root pollution Class A is F-44 **NOT CONFIRMED**, not a new control-plane hole |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 **Y**. Theme 2 **Y**. Residual Class B. Package stays **0.4.5** |
| found in | post-v0.4.5 production use (RW-081), rad v0.4.5, 2026-09-18 IST 22:28:43–22:30:12 |
| fixed in | — live 11B artifact quality **not** claimed fixed. Pip/root-pollution **not** patched (F-44 NOT CONFIRMED). Default max-tools / max-tasks **not** raised |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` |
| objective / test | `obj_b6d32fcc` — production ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root `text_analyzer/` **and** stray **`analyzer.py`** (root pollution from `echo … > analyzer.py`). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present `{}` valid, empty** (true counts lines=3, words=13, chars=76). Package `analyzer.py` stdlib (420 B, written in task 1). `test_analyzer.py` **SyntaxError** (`def test_analyzer):`) + wrong oracles (`words==9`, `chars==41`). README 393 B. Root `analyzer.py` 490 B echo stub |
| expected | required layout under `text_analyzer/`; exact 3-line input; non-empty valid package `summary.json` with correct counts; tests that assert exact counts; `VERIFIED` only from machine checks; path-aligned task **and** inferred objective checks; no false DONE |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=llm** **attempts=2** (4 tasks, **no repair**, `fit=true`, `compacted=false`, `estimated_tools=8`). Path-aligned task checks **Y**. Objective checks **all package-joined** (3 checks; 0 bare: `json_valid text_analyzer/summary.json`, `shell_ok python3 text_analyzer/test_analyzer.py`, `file_line_count text_analyzer/input.txt` n=3). First task **VERIFIED** despite mkdir File-exists (actions ok=true; 8 actions, 1 error). Second task **RUNNING** at stop (pip upgrade / `echo > analyzer.py` / `pip install -r` error / pip jsonschema; never reached verify). Recovery **none** (retries=0). Tools **12/12** (`write_file`×6, `run_shell`×6; **0** invented DONE; pip `-r` **attempted**×1 error, **no** ENVIRONMENT→repair). Model calls 9/80. Retries 0/6. Wall ~89s / spent ≈41.5s. Process exit 2. False DONE **0** |
| notes | vs RW-079: still FAIL `needs_user` @ 12/12; package-joined / `bf69eb73…` / 0 invented DONE held; ENVIRONMENT repair **gone**; mkdir File-exists **live Y** (first live confirm in this series); premature-test ENVIRONMENT **not exercised**; residual shifted to pip/echo budget burn + root pollution + empty summary + SyntaxError test. Caps unchanged. Needle OFF. |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw081_5a76b128 rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_b6d32fcc → needs_user; tools 12/12; PLAN_CREATED source=llm attempts=2
# objective_checks package-joined; input.txt sha256 bf69eb73… (3-line); summary.json {}; root analyzer.py pollution
```

## Investigation — pip thrash + root pollution Class A **NOT CONFIRMED** (RW-082) — 2026-09-18

Investigate-first on `32e9fe87` / v0.4.5. No product patch. Package stays
**0.4.5**. Needle **OFF**. Caps **not** raised. RW-058–081 facts are **not
rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. Do not re-litigate v0.4.3
pip-missing-requirements ENVIRONMENT (task never reached verify this run).

### F-20260918-44 — pip thrash + root `analyzer.py` pollution Class A **NOT CONFIRMED**

| field | value |
|---|---|
| class | **not A** — model/budget quality on a working product path (Class **B** residual of F-43). RAD already joins *checks* to `package_dir` (theme 1 / v0.4.2). Executor/tools do **not** remap `write_file` / `echo >` action paths (models propose). Root `analyzer.py` does **not** satisfy `text_analyzer/analyzer.py` checks (false DONE **0**). Root leftover does **not** fail a passed package check. Joining echo redirects into `package_dir` would overwrite a good package file with the broken stub. PLAN_PROMPT already forbids pip for stdlib-only; v0.4.3 already treats pip `-r` file-not-found as not ENVIRONMENT / action-noise. Rejecting pip at ingest still charges `Budget.tool_calls`. Cosmetic PLAN_PROMPT-only is not a bump |
| status | **investigated / not Class A** — **NOT CONFIRMED**. No product patch. No v0.4.6 |
| found in | RW-081 / F-20260918-43 (v0.4.5 live 11B text_analyzer); investigate-first on `32e9fe87` |
| fixed in | — |
| lane | deterministic / scripted (MUST). Live NIM not re-run |
| objective / test | `tests/test_pip_root_pollution_investigation.py`; RW-082 |
| disk | scripted: package `analyzer.py` unchanged when `echo > analyzer.py` lands at workspace root; root-only write does **not** VERIFIED package checks; mkdir File-exists still VERIFIED; pip `-r` still not ENVIRONMENT; empty `{}` + missing `json_field` still FAILED; fallback *tasks* still check-less (F-17) |
| expected | A control-plane hole that emits/accepts root writes as satisfying package checks, or that classifies pip thrash as ENVIRONMENT repair, or a verifier hole that wastes budget / rubber-stamps |
| actual | Checks stay package-joined. Actions stay model-proposed (no path remap). Root pollution is leftover disk, not a false DONE and not a failed package contract. Pip `-r` missing is still TOOL / action-noise when verify runs; live RW-081 never reached verify (budget stop). Successful pip is a real tool call, not a classifier hole |
| notes | Theme-3 measured win this live run: mkdir File-exists action-noise **live Y** (v0.4.4). Premature-test ENVIRONMENT **not live-hit** (v0.4.5 unit RW-080 remains). Multi-step checkpoint is **SCOPED / PLANNED** as theme 3 slice E (Cycle 17 / ROADMAP; not built). Needle off. Caps unchanged. Live 11B text_analyzer@12 **not** claimed PASS |

Reproduction:

```
python3 -m pytest -q tests/test_pip_root_pollution_investigation.py
# root write ≠ package VERIFIED; echo redirect not joined; pip -r ≠ ENVIRONMENT; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **519 passed** in 11.05s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw081-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw081-gate/acceptance/20260918-171326_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw081-rw/realworld/20260918-171327_realworld.json`) |
| Package | **0.4.5** (no bump) |
| RW-058–080 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim for RW-081 |

## Scope — Gen3 theme 3 slice E multi-step checkpoint (docs only) — 2026-09-18

Docs-only scope on `16b41553` / v0.4.5 after PR #30. No product patch. Package
stays **0.4.5**. Needle **OFF**. Caps **not** raised. RW-058–082 facts are
**not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed. A1 not reopened.
Thrash Class A chase **paused** after F-44 **NOT CONFIRMED**.

Crash-resume already ships (`CheckpointManager`, `rad objective resume`). The
measured gap is intra-run: later independent READY work still gets no attempt
when an early task burns remaining tools (RW-081: first task VERIFIED, second
RUNNING pip/echo, Write-test PENDING, tools 12/12). Slice E is **strengthen /
use** that checkpoint + `Scheduler` path, not a new persistence stack.

Recommended first **v0.4.6** candidate **E1** (task-boundary yield /
leftover-budget dispatch) is listed in [ROADMAP.md](ROADMAP.md) — **not
accepted**, **not implemented**. E2/E3 remain candidates. Next product work
waits for a written accept.

| gate | result |
|---|---|
| `python3 -m pytest -q` | **519 passed** in 11.70s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-slicee-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-slicee-gate/acceptance/20260918-172927_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-slicee-rw/realworld/20260918-172928_realworld.json`) |
| Package | **0.4.5** (no bump; no v0.4.6) |
| Product code | unchanged |
| Slice E | **SCOPED / PLANNED** |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim |

### F-20260918-45 — task-boundary yield / leftover-budget dispatch (E1)

| field | value |
|---|---|
| class | **A** (drive loop stayed on an in-flight task until leftover tools hit 0, so later independent READY work never ran under the same `--max-tools` cap). Capability (Gen3 theme 3 slice E1). Not a re-open of RW-081 live 11B artifact quality |
| status | **fixed** in v0.4.6 |
| found in | RW-081 / F-43 live `needs_user` @ 12/12; Cycle 17 scope |
| fixed in | **v0.4.6** (this change) |
| lane | deterministic / scripted (MUST). Live NIM not re-run; not a live PASS claim |
| objective / test | `tests/test_task_boundary_yield.py` (RW-083) |
| disk | `first.txt` + `later.txt` present; `stuck.txt` / `missing.json` absent; checkpoint `digest` intact |
| expected | t1 VERIFIED; t2 would exhaust remaining tools if allowed; t3 independent `file_exists` still gets ≥1 attempt under the same tool cap; unmet checks not VERIFIED; false DONE 0 |
| actual | sequential `objective_parallel=1`, `--max-tools` 4: t1 VERIFIED, t2 yielded `RETRYING`, t3 VERIFIED, objective not VERIFIED (missing JSON); chained `depends_on` t3 stays PENDING (E2 not claimed) |
| notes | Strengthens `CheckpointManager` + `Scheduler`; no new persistence format. Needle OFF. Caps 16/60 unchanged. Path-align / multifile / ASCII-tree / pip/DONE / mkdir File-exists / premature-test preserved. Thrash Class A chase paused. Live 11B text_analyzer@12 **not** claimed PASS |

| gate | result |
|---|---|
| `python3 -m pytest -q` | **530 passed** in 9.93s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-e1-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-e1-gate/acceptance/20260918-174516_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-e1-rw/realworld/20260918-174520_realworld.json`) |
| Package | **0.4.6** |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED** (no NVIDIA keys) — not a live PASS claim |

## Live NIM retest of v0.4.6 (RW-084) — 2026-09-19

Operator production `rad objective run` on package **0.4.6** (tag **v0.4.6**,
`8f09be5839e25c236349121a4ec77606d0d5ed2d`). Needle **OFF**. Caps **not**
raised. RW-058–083 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay
closed. A1 is **not reopened**. E1 remains **shipped / scripted** (RW-083 /
F-45). Live E1 gate **deferred**. Live NIM loop **paused / Class C blocked**.
Package stays **0.4.6**. No product patch.

Authoritative facts: operator report `obj_a8118606` /
`/tmp/rad_prod_rw084_3d9cc3ac`. This agent did not re-run NIM. No keys printed
or committed.

### F-20260919-46 — live 11B text_analyzer on v0.4.6 **BLOCKED Class C** (RW-084)

| field | value |
|---|---|
| class | **C** (NVIDIA NIM inference unauthorized). Key loads; `GET /v1/models` **200** (catalog lists `meta/llama-3.2-11b-vision-instruct`); all probed `POST /v1/chat/completions` return **403** `Authorization failed`. Not a RAD product defect observable this run. Class A/B / E1: **not live-hit** |
| status | **BLOCKED** — live **FAIL / BLOCKED Class C** (`needs_user`; 0 tools). E1 leftover-budget yield **not live-tested**. Package stays **0.4.6**. Live NIM loop **paused** |
| found in | post-v0.4.6 production use (RW-084), rad v0.4.6 / `8f09be58`, 2026-09-19 IST 08:34:20–08:34:22 |
| fixed in | — not a RAD hole. Refresh a NIM key with `chat/completions` entitlement before any E1 live retest. Do **not** keep retrying keys that list models but fail chat |
| lane | live NVIDIA NIM `meta/llama-3.2-11b-vision-instruct` (intended 11B; Needle OFF) |
| objective / test | `obj_a8118606` — RW-081 shape ASCII-tree `text_analyzer/` layout; exact 3-line input intended; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **empty**; `text_analyzer/` **absent**. `input.txt` / `summary.json` / code / tests / README all **absent**. Root pollution **N**. No tools ran |
| expected | working inference so the E1 live gate can run; `VERIFIED` only from machine checks; no false DONE |
| actual | status `needs_user` / **BLOCKED Class C** — **NOT DONE**, 0 tool calls. Pre-run `rad doctor` providers READY (1 usable: nvidia). `GET /v1/models` **200**. All `chat/completions` **403**. Other listed instruct models (granite, mistral, nemotron, …) **403**. EOL probe `meta/llama-3.1-8b-instruct` **410** Gone. RAD error: `all providers failed: nvidia: HTTP 403 … Authorization failed`. `PLAN_CREATED` **source=`fallback`** (LLM plan unavailable), 4 tasks carved from goal newlines (not a real coding plan), then NEEDS_USER. t_ad22c64b **NEEDS_USER** (`MODEL_FAILURE`; 3 attempts; HTTP 403); t_e74ab370 / t_5cb4bd78 / t_bf095942 **BLOCKED** (unmet prereq). Tools **0/12**. Model calls **3.0/80** (all failed). Retries **2.0/6** (retry×2 then replan → no usable plan). Wall ~1.5s / usage `seconds≈0.91`. Process exit 2. Verification **none**. objective_checks package-joined at create (`json_valid text_analyzer/summary.json`; `shell_ok python3 text_analyzer/test_analyzer.py`) — **never executed**. 0 ENVIRONMENT repair. 0 TaskYield. 0 leftover-budget dispatch. False DONE **0** |
| notes | vs RW-081: **cannot compare E1 live** — RW-081 ran tools 12/12 on working NIM; RW-084 stopped at HTTP 403 (0 tools). Residual Class **C** (not B). E1 code is present on tag `v0.4.6` / `8f09be58` (scripted RW-083 remains unit evidence). Prior Class A paths (mkdir / premature-test / pip / invented DONE) **not hit**. Operator decision (2026-09-19): **pause** live NIM loop until inference-entitled credentials work on integrate.api. Caps unchanged. Needle OFF. Stay **0.4.6** |

Reproduction (redacted; live NIM; operator home):

```
RAD_HOME=/tmp/rad_prod_rw084_3d9cc3ac rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_a8118606 → needs_user; tools 0/12; PLAN_CREATED source=fallback
# chat/completions HTTP 403 Authorization failed; GET /v1/models 200
# E1 leftover-budget yield not live-tested; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **530 passed** in 10.76s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw084-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw084-gate/acceptance/20260919-031510_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw084-rw/realworld/20260919-031511_realworld.json`) |
| Package | **0.4.6** (no bump) |
| Product code | unchanged |
| RW-058–083 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live NIM this patch | **BLOCKED Class C** (RW-084 recorded; loop **paused**) — not a live PASS claim |

## Live OpenRouter retest of v0.4.6 (RW-085) — 2026-09-19

Operator production `rad objective run` on package **0.4.6** (tag **v0.4.6**,
`8f09be5839e25c236349121a4ec77606d0d5ed2d`). Needle **OFF**. Caps **not**
raised. RW-058–084 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay
closed. A1 is **not reopened**. E1 remains **shipped / scripted** (RW-083 /
F-45). Live E1 **not confirmed**. Class C vs RW-084 **cleared** by provider
switch (OpenRouter HTTP 200 / tools 11/12 / `$0`). Residual Class **B** plus
Class A `xxd` ENVIRONMENT (F-48). This change bumps **0.4.6 → 0.4.7**.

Authoritative facts: operator report `obj_3181e63d` /
`/tmp/rad_prod_rw085_15d26f58`. This agent did not re-run the live objective.
No keys printed or committed.

### F-20260919-47 — live OpenRouter free text_analyzer on v0.4.6 **FAIL** (RW-085)

| field | value |
|---|---|
| class | **B** residual (fallback PLAN; free-model quality; missing README; wrong `summary.json` schema; failing tests; later tasks 0 attempts) **+** Class A `xxd` ENVIRONMENT (F-48). Class C vs RW-084 **cleared**. Theme E1 live: **N** |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). Theme 1 ASCII-tree obj-checks **Y**. E1 **not live**. Package on the live run **0.4.6**; this branch **0.4.7** |
| found in | post-v0.4.6 production use (RW-085), rad v0.4.6 / `8f09be58`, 2026-09-19 IST 09:34:38–09:57:47 |
| fixed in | live artifact quality **not** claimed fixed. `xxd` ENVIRONMENT is F-48 / v0.4.7. Default max-tools / max-tasks **not** raised |
| lane | live OpenRouter `nvidia/nemotron-3.5-lightning:free` (free-only; `free_lock=true`; NIM unset). Needle `existing` / off |
| objective / test | `obj_3181e63d` — RW-081-shape ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present, valid JSON, alt schema** (`word_count=13`, `char_count=76`, `letter_frequency`; missing classic `lines`). `analyzer.py` stdlib 846 B. `test_analyzer.py` 1127 B; post-hoc `python3 text_analyzer/test_analyzer.py` **exit 1**. `README.md` **absent** |
| expected | required layout under `text_analyzer/`; exact 3-line input; valid package `summary.json` with correct counts; tests that assert exact counts; README; `VERIFIED` only from machine checks; no false DONE; missing optional `xxd` must not insert Repair-prerequisite |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. `PLAN_CREATED` **source=`fallback`**, **attempts=2**, 4 tasks carved from goal newlines (not a real coding plan), `fit=true`, `compacted=false`, `estimated_tools=8`. Path-aligned writes **Y**. Objective checks **all package-joined** (2 checks; 0 bare: `json_valid text_analyzer/summary.json`, `shell_ok python3 text_analyzer/test_analyzer.py`). First task **FAILED** — actions `ok=false` (5 actions, **1 error**: `xxd: not found` exit 127); `file_nonempty` input.txt OK. t_07ad6720 **BLOCKED** (depends on repair; attempts=1). t_cdb9c8e2 / t_9b2837e2 / t_a51bef19 **BLOCKED** (unmet prereq; **attempts=0**). t_1dfa6d3f Repair prerequisite **NEEDS_USER** (attempts=2; UNVERIFIED both times). Recovery: **ENVIRONMENT_FAILURE** → repair; then VALIDATION_FAILURE retry_with_hint; then replan → NEEDS_USER. Tools **11/12** (events: `run_shell` 8, `write_file` 4, `run_python` 2, `read_file` 2, `list_dir` 2). Model calls **14.0/80** (provider=`openrouter`). Retries **2.0/6**. Wall START 2026-09-19 09:34:38 IST → END 09:57:47 IST (~1389s event span; usage `seconds≈928.8`). Process exit 2. Money **`$0.00`**. 0 TaskYield. 0 leftover-budget dispatch. False DONE **0** |
| notes | vs RW-081: still FAIL `needs_user`; tools **11/12** vs 12/12; package-joined / `bf69eb73…` / 0 invented DONE held; brain **nvidia NIM → openrouter free**; E1 leftover-budget yield **not live**. vs RW-084: **Class C cleared** (OpenRouter HTTP 200 / tools 11/12 / `$0`). Caps unchanged. Needle OFF. |

Reproduction (redacted; live OpenRouter; operator home):

```
RAD_HOME=/tmp/rad_prod_rw085_15d26f58 rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_3181e63d → needs_user; tools 11/12; PLAN_CREATED source=fallback attempts=2
# objective_checks package-joined; input.txt sha256 bf69eb73… (3-line); xxd ENVIRONMENT repair
# E1 leftover-budget yield not live; false DONE 0
```

## Gen3 / v0.4.7 — Optional checksum-utility ENVIRONMENT (RW-086) — 2026-09-19

Generation 3 autonomous-agent maturity, **theme 3 slice F**. Package
**0.4.6 → 0.4.7**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–085 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**. E1 TaskYield is
**preserved**.

Product: missing optional hex/checksum binaries (`xxd`, `hexdump`, `sha256sum`
and close variants) used only for inspection theater are **not** ENVIRONMENT
(no Repair-prerequisite insert). They still record as tool errors (honesty)
but do **not** fail a task whose explicit file checks passed, so later
independent tasks can still run. Genuine `python` / `pip` / `gcc` / unknown
`command not found` stay ENVIRONMENT. `cat` no-such-file stays ENVIRONMENT
(F-18). `sha256sum: file: No such file` (binary exists, argument missing)
stays ENVIRONMENT. mkdir File-exists / pip `-r` / premature-test action noise
are preserved. The verifier still evaluates stored paths honestly. A model
`DONE:` is never completion. Does **not** claim live text_analyzer@12 now PASS.

### F-20260919-48 — missing optional `xxd` classified ENVIRONMENT

| field | value |
|---|---|
| class | **A** (`xxd text_analyzer/input.txt` not found / exit 127 classified ENVIRONMENT and burned leftover tools on Repair prerequisite even though `file_nonempty` input.txt already passed). Capability (Gen3 theme 3 slice F). Not a re-open of RW-085 live artifact quality |
| status | **shipped in v0.4.7** |
| found in | RW-085 / F-20260919-47 (v0.4.6 live OpenRouter text_analyzer); investigate-first on `54fc739` |
| fixed in | **v0.4.7** — `is_missing_optional_checksum_utility` skip in `classify()`; same helper in `is_first_task_thrash_noise` (verifier actions); PLAN_PROMPT no xxd/hexdump for stdlib coding. Check *kinds* not remapped (F-26). Fallback *tasks* stay check-less (F-17). Genuine `python`/`pip`/`gcc` command-not-found still ENVIRONMENT (F-18). mkdir / pip `-r` / premature-test still **not** ENVIRONMENT |
| lane | deterministic / scripted (MUST). Live OpenRouter / NIM not re-run |
| objective / test | `tests/test_xxd_environment.py`; RW-086 |
| disk | scripted: write_file creates `text_analyzer/input.txt` then `xxd` not found → first task **VERIFIED**; later `analyzer.py` task runs; no Repair prerequisite; empty JSON still **not** VERIFIED. No workspace-root pollution |
| expected | Missing optional `xxd` does not spend remaining tools on ENVIRONMENT repair; does not fail a check-passing file task; later package tasks can still run; false DONE **0**; path-aligned / multifile / ASCII-tree / pip-DONE / mkdir-File-exists / premature-test / E1 TaskYield preserved |
| actual | `xxd: not found` / exit 127 is TOOL not ENVIRONMENT; treated as action noise when file checks can still pass; F-18 command-not-found / ModuleNotFoundError / cat no-such-file / sha256sum-missing-file ENVIRONMENT preserved; empty JSON still FAILED |
| notes | Live RW-085 remains Class B on free-model quality, fallback PLAN, and tools=12. This PR does **not** claim that live text_analyzer would now PASS. A1 not reopened. E1 live still **not confirmed**. Needle off. Caps unchanged. |

Reproduction:

```
python3 -m pytest -q tests/test_xxd_environment.py
# missing xxd ≠ ENVIRONMENT; ≠ fail check-passing task; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **547 passed** in 12.22s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw085-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw085-gate/acceptance/20260919-043709_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw085-rw/realworld/20260919-043710_realworld.json`) |
| Package | **0.4.7** |
| RW-058–085 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live this patch | **not re-run** — not a live PASS claim for RW-085 |

## Live OpenRouter retest of v0.4.7 (RW-086) — 2026-09-19

Operator production `rad objective run` on package **0.4.7** (tag **v0.4.7**,
`850aaf9c3a931a5ba119bdbb6ec73ae4a6fa73e9`). Needle **OFF**. Caps **not**
raised. RW-058–085 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay
closed. A1 is **not reopened**. Scripted RW-086 / F-48 remains the positive
xxd-classifier unit evidence. E1 remains **shipped / scripted** (RW-083 /
F-45). Live E1 **not confirmed**. xxd Class A ENVIRONMENT thrash vs RW-085
**CLEARED** (0 `xxd`/`hexdump`; 0 ENVIRONMENT; 0 repair-insert). Residual
Class **B+C** (fallback PLAN / incomplete package + late HTTP **429**
`free-models-per-day`). Package stays **0.4.7**. No product patch. No version
bump.

Authoritative facts: operator report `obj_e1949b8f` /
`/tmp/rad_prod_rw086_81609c3b`. This agent did not re-run the live objective.
No keys printed or committed.

Operator decision (2026-09-19): **pause** live OpenRouter free runs until the
`free-models-per-day` rate limit resets. Live NIM loop remains **paused**
(Class C).

### F-20260919-49 — live OpenRouter free text_analyzer on v0.4.7 **FAIL** (RW-086)

| field | value |
|---|---|
| class | **B+C** — Class B (fallback PLAN; incomplete package: no `test_analyzer.py` / `README.md`; odd `summary.json` schema; chained fallback tasks) **+** late Class C (HTTP **429** `free-models-per-day`). xxd Class A bug live: **N**. Theme E1 Class A live: **N** |
| status | documented — live **FAIL** (`needs_user`; not VERIFIED). xxd Class A thrash **CLEARED**. E1 **not live**. Package stays **0.4.7**. Live OpenRouter free-model loop **paused** until rate limit resets |
| found in | post-v0.4.7 production use (live RW-086), rad v0.4.7 / `850aaf9c`, 2026-09-19 IST 10:13:07–10:23:22 |
| fixed in | live artifact quality **not** claimed fixed. xxd thrash **cleared this trajectory** (absence of thrash vs RW-085; not a positive “classified as approach-noise” observation). Default max-tools / max-tasks **not** raised. Do **not** treat further free-model retries as product Class B until rate clears |
| lane | live OpenRouter `nvidia/nemotron-3.5-lightning:free` (free-only; `free_lock=true`; NIM unset). Needle `existing` / off |
| objective / test | `obj_e1949b8f` — RW-085-shape ASCII-tree `text_analyzer/` layout; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`; Needle `existing` / off |
| disk | workspace root **only** `text_analyzer/` (no root pollution). `text_analyzer/input.txt` YES **correct 3-line** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present, valid JSON, alt schema** (`sha256`, `word_count=13`, `char_freq`, `text_length=76`; not classic lines/words/chars). `analyzer.py` stdlib 1256 B. `test_analyzer.py` **absent**. `README.md` **absent** |
| expected | required layout under `text_analyzer/`; exact 3-line input; valid package `summary.json` with correct counts; tests that assert exact counts; README; `VERIFIED` only from machine checks; no false DONE; missing optional `xxd` must not insert Repair-prerequisite |
| actual | status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete. Tool-call budget 12 exhausted; task2 left **RETRYING** after MODEL_FAILURE (429). `PLAN_CREATED` **source=`fallback`**, **attempts=2**, 4 tasks carved from goal newlines (not a real coding plan), `fit=true`, `compacted=false`, `estimated_tools=8`. Path-aligned writes **Y**. Objective checks **all package-joined** under `text_analyzer/` (`json_valid text_analyzer/summary.json`; `shell_ok python3 text_analyzer/test_analyzer.py`) — not executed to PASS. t_febc5d2d Create package **COMPLETED** (attempts=1; VERIFIED on actions + nonempty input). t_dc4db802 **RETRYING** (attempts=1; wrote analyzer.py + summary.json; then openrouter HTTP **429**). t_1ca60866 / t_a4f4c8a6 **PENDING** (deps unmet; **attempts=0**). Recovery: **MODEL_FAILURE** → retry another brain; then tool budget exhausted. Tools **12/12** (`run_shell` 8, `write_file` 3, `read_file` 1 — **0** invented `DONE`). Model calls **7.0/80** (provider=`openrouter`). Retries **1.0/6**. Wall START 2026-09-19 10:13:07 IST → END 10:23:22 IST (~615s wall; usage `seconds≈417.8`). Process exit 2. Money **`$0.00`**. 0 `xxd`/`hexdump`. 0 ENVIRONMENT_FAILURE. 0 repair-insert. 0 TaskYield. 0 leftover-budget dispatch. False DONE **0**. Host still lacks `xxd`/`hexdump`; model used `sha256sum` + `hashlib` / `cat -A` |
| notes | vs RW-085: still FAIL `needs_user`; tools **12/12** vs **11/12**; **xxd Class A ENVIRONMENT thrash gone** (RW-085: `xxd: not found` → ENVIRONMENT → repair; RW-086: 0 ENVIRONMENT / 0 xxd); task1 **COMPLETED** + task2 **attempts=1** (vs RW-085 later tasks attempts=0 after repair burn); E1 leftover-budget yield **not live** (0 TaskYield; sequential task2 after task1, not leftover-budget yield of an independent READY sibling). **429 new.** Residual **B+C**. Caveat: this trajectory did not emit a live missing-`xxd` exit-127 for the v0.4.7 classifier to re-label — evidence is **absence of thrash** vs RW-085; scripted RW-086 / PR #34 remains the positive unit evidence. Auth was OK earlier (HTTP 200 smoke + successful MODEL_CALLED). Class C is **rate**, not missing key. Caps unchanged. Needle OFF. Stay **0.4.7**. |

Reproduction (redacted; live OpenRouter; operator home):

```
RAD_HOME=/tmp/rad_prod_rw086_81609c3b rad objective run "<ASCII-tree text_analyzer goal>" --auto --max-tasks 8 --max-tools 12
# obj_e1949b8f → needs_user; tools 12/12; PLAN_CREATED source=fallback attempts=2
# objective_checks package-joined; input.txt sha256 bf69eb73… (3-line); 0 xxd / 0 ENVIRONMENT / 0 repair
# task1 COMPLETED; task2 RETRYING after HTTP 429 free-models-per-day; E1 not live; false DONE 0
```

| gate | result |
|---|---|
| `python3 -m pytest -q` | **547 passed** in 10.97s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw086-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw086-gate/acceptance/20260919-045809_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw086-rw/realworld/20260919-045810_realworld.json`) |
| Package | **0.4.7** (no bump) |
| Product code | unchanged |
| RW-058–085 | preserved |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Live OpenRouter this patch | **FAIL** recorded; free-model loop **paused** until `free-models-per-day` resets — not a live PASS claim |
| Live NIM this patch | **BLOCKED Class C** (RW-084; loop remains **paused**) |

## Gen3 / v0.4.8 — Independent later package files (RW-087) — 2026-09-19

Generation 3 autonomous-agent maturity, **theme 3 slice E2**. Package
**0.4.7 → 0.4.8**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–086 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**. E1 TaskYield and xxd
Class A (v0.4.7) are **preserved**.

Product: fallback clause-split no longer linearly chains independent later
file-write clauses. Those tasks get empty `depends_on` so `graph.ready()` /
E1 leftover reserve can dispatch them while an early task is stuck under a
tight `--max-tools` budget. Run / verify / read consume steps still chain.
Explicit LLM `depends_on` chains are not rewritten. Fallback *tasks* stay
check-less (F-17). A model `DONE:` is never completion. Does **not** claim
live text_analyzer@12 now PASS.

### F-20260919-50 — fallback linear `depends_on` starves later independent files

| field | value |
|---|---|
| class | **capability** (Gen3 theme 3 slice E2). Investigate-first: control-plane hole in fallback *emission*, not a missing scheduler primitive. E1 leftover reserve is 0 when later tasks wait on the in-flight one. `optional` only unblocks after FAILED/BLOCKED/CANCELLED, not RETRYING. Not a re-open of live RW-086 artifact quality |
| status | **shipped in v0.4.8** |
| found in | RW-085 / F-20260919-47 and live RW-086 / F-20260919-49 (`source=fallback` chain; later package files 0 attempts); ROADMAP E2 candidate (PR #31) |
| fixed in | **v0.4.8** — `independent_file_clause` + empty `depends_on` on distinct fallback file writes in `_fallback`. Consume/verify/read still chains. F-17 check-less / cap 7 / goal-only split preserved. Explicit LLM chains unchanged |
| lane | scripted planner + controller (no NIM / no OpenRouter) |
| objective / test | `tests/test_independent_later_files.py`; RW-087 |
| disk | scripted: `first.txt` + `later.txt` on disk while early consume thrashes; later fallback file ≥1 attempt; missing JSON still **not** VERIFIED |
| expected | later independent file task can run while an early fallback task is stuck under the same `--max-tools` cap; false DONE **0** |
| actual | fallback later file is READY (`depends_on=[]`); E1 yield parks the stuck task; later file VERIFIED on its own `write_file`; objective not VERIFIED without remaining contracts |
| notes | Live RW-086 remains Class B+C on free-model quality, fallback PLAN, and late **429**. This PR does **not** claim that live text_analyzer would now PASS. A1 not reopened. E1 live still **not confirmed**. Needle off. Caps unchanged. |

```
# scripted RW-087 — later independent fallback file still gets ≥1 attempt
python3 -m pytest -q tests/test_independent_later_files.py
```

| gate | this PR |
|---|---|
| `python3 -m pytest -q` | **559 passed** in 10.41s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw087-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw087-gate/acceptance/20260919-050812_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw087-rw/realworld/20260919-050809_realworld.json`) |
| Package | **0.4.8** |
| Live this patch | **not re-run** — not a live PASS claim for RW-085 / RW-086 |

## Gen3 / v0.4.9 — Budget-aware retry stop (RW-088) — 2026-09-19

Generation 3 autonomous-agent maturity, **theme 3 slice E3**. Package
**0.4.8 → 0.4.9**. Control plane preserved (models propose / RAD decides). Needle
**OFF**. Caps **not** raised (`max_plan_tasks` 16, `Budget.tool_calls` 60).
RW-058–087 facts are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.
A1 (budget→needs_user as Class A) is **not reopened**. E1 TaskYield, E2
independent later files, and xxd Class A (v0.4.7) are **preserved**.

Product: after a failed first attempt, do not start a retry or insert a
repair when remaining tools are below leftover reserve plus
`TOOLS_PER_TASK`. Yield to the E1 leftover-dispatch path so a later
independent READY task still gets ≥1 attempt. Executor `reserve_tools`
stays 1 per later READY (first-attempt charging unchanged). Solo tasks
with no later READY still retry. Unlimited budgets do not yield. A model
`DONE:` is never completion. Does **not** claim live text_analyzer@12 now
PASS.

### F-20260919-51 — leftover-eating retry/repair after a failed first attempt

| field | value |
|---|---|
| class | **capability** (Gen3 theme 3 slice E3). Investigate-first: E1 `TaskYield` already stops mid-think when `rem <= reserve`. The hole is the retry/repair decision when `rem = reserve + 1` — recovery started another stuck-task attempt and spent the spare tool E1 reserved for later READY work. Not a re-open of live RW-086 artifact quality |
| status | **shipped in v0.4.9** |
| found in | RW-085 / F-20260919-47 and live RW-086 / F-20260919-49 (early-task retry / repair / shell thrash); ROADMAP E3 candidate (PR #31) |
| fixed in | **v0.4.9** — `should_yield_for_leftover` (`rem < leftover_tool_reserve + TOOLS_PER_TASK`) at `_should_yield` / RETRYING dispatch. Same E1 leftover reserve; no parallel estimator. F-17 check-less / caps unchanged |
| lane | scripted planner + controller (no NIM / no OpenRouter) |
| objective / test | `tests/test_budget_aware_retry_stop.py`; RW-088 |
| disk | scripted: `first.txt` + `later.txt` on disk; stuck task not retried/repaired before later runs; missing JSON still **not** VERIFIED |
| expected | retries / repair loops stop when leftover headroom is below `TOOLS_PER_TASK`; later independent READY task still gets ≥1 attempt; false DONE **0** |
| actual | after one failed stuck attempt (`rem=2`, reserve=1) RAD yields; later file VERIFIED on its own `write_file`; no repair insert; objective not VERIFIED without remaining contracts |
| notes | Live RW-086 remains Class B+C on free-model quality, fallback PLAN, and late **429**. This PR does **not** claim that live text_analyzer would now PASS. A1 not reopened. E1/E2 live still **not confirmed**. Needle off. Caps unchanged. |

```
# scripted RW-088 — retry/repair stop; later independent file still gets ≥1 attempt
python3 -m pytest -q tests/test_budget_aware_retry_stop.py
```

| gate | this PR |
|---|---|
| `python3 -m pytest -q` | **569 passed** in 14.44s |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR (`RAD_HOME=/tmp/rad-rw088-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-rw088-gate/acceptance/20260919-052039_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED; `/tmp/rad-rw088-rw/realworld/20260919-052035_realworld.json`) |
| Package | **0.4.9** |
| Live this patch | **not re-run** — not a live PASS claim for RW-085 / RW-086 |

## How to add a finding

1. Reproduce with disk checks (file exists / hash / contents). Quote status + verification, not model prose.
2. Classify A/B/C using the table above. If unsure: **C** until a second run with a working brain.
3. Append an `F-*` entry. Redact keys.
4. Class A only: smallest controller/adapter/tool fix + a regression in `tests/`. Bump `0.2.x`.
   Do not expand architecture. Do not make Needle default. Do not ship `v0.3.0` from a ledger patch.
5. Re-run `python -m pytest -q`, `rad doctor --offline`, `rad acceptance`, `rad realworld`.

## Recommended use → patch loop

1. `rad doctor --offline` then (with a vaulted NIM key) `rad doctor`.
2. Bounded live objective: `--auto --max-tasks 3 --max-tools 8` and a file-on-disk criterion.
3. One unconstrained objective of the same shape. If file-on-disk + `needs_user`, log **B** (model)
   unless the verifier was never consulted — that is **A** (see F-20260918-03).
4. `rad realworld` after any controller change.
5. Patch Class A only; leave B/C in this file.
