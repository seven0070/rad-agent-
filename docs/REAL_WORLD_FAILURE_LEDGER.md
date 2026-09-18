# Real-world failure ledger

Living log of **measured** RAD failures found in live or reconstructed use.
Architecture is frozen. Needle stays experimental and off by default. This is not AGI/ASI.

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
| class | A (suspected; **not confirmed** — investigated) |
| status | **investigated / not Class A** — do **not** claim a product fix; no patch |
| found in | post-Cycle 4 production use (RW-059 investigation candidates), rad v0.2.3 |
| fixed in | — **not a defect.** No patch. No v0.2.4. See F-20260918-21 |
| lane | live production `objective run` (planner path) + deterministic planner unit tests |
| objective / test | production text_analyzer multiline objective (RW-058 / RW-059); `test_fallback_planner_does_not_split_on_newlines` |
| disk | n/a — suspected planning defect, not a disk-hash finding |
| expected | one coherent plan for a single multiline objective; no spurious tasks from newline wrapping |
| actual | **Not reproduced.** `Planner._fallback` splits on clause markers (`and then` / `then` / `;` / `, and` / period+space), **not** on newlines. A production-shaped multiline goal with required-file bullets is **one** fallback task. RW-058/059/060 had a live brain, so the planner source is **llm** (5 planned tasks on RW-058), not fallback. |
| notes | Parked suspect closed by investigation. Clause-marker split remains by design (`test_planner_fallback_without_brain`). Not a lifecycle or budget-boundary defect. |

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
| notes | Live NIM 11B FAIL on RW-058/059/060 stays **Class B**: tool budget exhausted with success criteria unmet. RAD did not rubber-stamp. False DONE **0**. Default `Budget.tool_calls` remains **60**; `max_plan_tasks` remains **16**; Needle `existing`. |

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

## Finish-line provider gate (2026-09-18, closeout — closing the v0.2.3 validation cycle)

Environment: Cloud Agent VM (fresh), **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`, no other
provider keys (vault / env / `.env` all empty), no local engine running. `main` tip
`aecfbae` (Class A investigation, no v0.2.4). Package **0.2.3** at start **and** at end —
**not re-cut, no 0.2.x bump**. Architecture frozen. Needle `existing` / off. Cap **16**
unchanged. Default tool budget **60** unchanged. Not AGI. Not v0.3.0.
Finish plan: provider gate → (blocked) → classify all live evidence → close or keep open.

### F-20260918-22 — finish-line provider gate: no usable provider / local engine

| field | value |
|---|---|
| class | C |
| status | **BLOCKED** |
| found in | finish-line execution, rad v0.2.3, `aecfbae` |
| fixed in | — not a RAD hole; external provider configuration is the only blocking dependency |
| lane | provider gate — all supported RAD provider / local-engine paths, one pass each |
| objective / test | none — gate failed **before** objective creation (by design: do not create an objective) |
| disk | n/a — no objective created, no tools used, workspace untouched |
| expected | `available_count ≥ 1` AND `actual_chat_check = SUCCESS` to run RW-063R |
| actual | `RouterState.build_chain()` → **available_count = 0**; edge0 / ollama / lmstudio **not running** (`rad models`, `probe_local`); 9 cloud providers **no key** (`rad keys list`: vault → env → .env all empty; no `.env` in cwd, home, or `~/.rad/keys`); chat check has **no candidate to test** → not SUCCESS |
| notes | Each detection path was exercised exactly once; not repeated. Same environmental family as F-20260918-08 / F-20260918-13 / F-20260918-14. Per the finish plan, live workload execution stops here: RW-063R remains **BLOCKED** (Class C), no RAD defect demonstrated, no patch. If a key is added or a local engine is started, the gate is re-run and RW-063R proceeds unchanged: `RAD_TOOL_ROUTER=existing --max-tasks 6 --max-tools 16 --auto`, Needle OFF, fresh workspace. |

Reproduction (redacted):

```
RAD_HOME=/tmp/rad-c5-provider-gate  # fresh home; no keys anywhere; no local engine
python3 -m rad providers            # 12 specs — all "no key" / "not running"
python3 -m rad models               # edge0 / ollama / lmstudio: not running
python3 -m rad keys list            # 9 cloud providers: no key (vault → env → .env)
RouterState(home).build_chain()     # available_count = 0; chain empty
```

| gate | result |
|---|---|
| `rad version` | **v0.2.3** |
| `python -m pytest -q` | **345 passed** in 10.12s (fresh venv, `.[dev]`) |
| `rad doctor --offline` | **20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR**, verdict READY, exit 0 (`/tmp/rad-c5-gate`) |
| `rad acceptance` | **50/50 PASSED** (`/tmp/rad-c5-gate/acceptance/20260918-122413_gate.json`) |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` Class C — no NVIDIA key); `false_success` / `needs_user` / `no_loop` → `needs_user`, **not** VERIFIED (`/tmp/rad-c5-gate/realworld/20260918-122353_realworld.json`) |
| Provider gate | **BLOCKED** — `available_count = 0`, chat check no candidate (F-20260918-22) |
| RW-063R | **not run** — gate failed; no objective created; no tools used |
| New Class A | **none** |
| False completion | **0** |
| 16-task cap / default tool budget / Needle | **UNCHANGED (16) / UNCHANGED (60) / OFF** |
| Recommendation | **close the v0.2.3 validation cycle** — `docs/V023_VALIDATION_CLOSEOUT.md` |

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
