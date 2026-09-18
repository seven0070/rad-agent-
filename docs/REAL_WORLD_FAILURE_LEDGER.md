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
