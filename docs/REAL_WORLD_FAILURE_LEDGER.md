# Real-world failure ledger

Living log of **measured** RAD failures found in live or reconstructed use.
Architecture is frozen. Needle stays experimental and off by default. This is not AGI/ASI.
Operating spine: [ROADMAP.md](ROADMAP.md) (adopted 2026-09-18). Gen1 complete on 0.2.3; Gen2 in progress. Verified coding loop is **implemented as v0.3.0** in this change (F-20260918-24 / RW-064). This ledger is evidence. Do not rewrite RW-058–063.

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
