# RAD development roadmap

This is the **operating spine** for RAD: five generations, one loop, evidence in / evidence out.
It is not a product-idea backlog (that list stays in the README) and it is not a license to
redesign the control plane.

**Status (2026-09-19):** Generation 1 is **complete**. Generation 2 is
**complete** (v0.3.0–v0.3.2). Generation 3 is **complete (scripted)** on
v0.4.0–v0.4.9. Generation 4 is **complete (scripted)** on v0.5.0–v0.5.5.
Live E1–E3 and Version 5 / G4-5 / G4-7 / G4-6 confirmation is **deferred**
until a provider recovers (NIM **Class C paused** RW-084 HTTP 403;
OpenRouter free **paused** RW-086 HTTP 429 `free-models-per-day`). Live
text_analyzer@12 still **FAIL** `needs_user` historically; false DONE **0**;
Needle **OFF**; caps **16/60**. Residual Class B: live G4-5 / G4-7
confirmation deferred, free-model thrash (Class A patched or F-44
**NOT CONFIRMED**; 429 is Class C). **G4-1** (live multi-provider /
free-provider production doctrine) is **accepted and implemented as
v0.5.0** (scripted RW-089). **G4-2** (live-gate resume / provider health
observability) is **accepted and implemented as v0.5.1** (scripted
RW-090 / RW-091). **G4-3** (live-use campaign / operator workflow) is
**accepted and implemented as v0.5.2** (scripted RW-092 / RW-093).
**G4-5** (fallback / LLM plan quality under tight budgets) is **accepted
and implemented as v0.5.3** (scripted RW-094 / RW-095). **G4-7** (coding
artifact completeness / named package-file contracts) is **accepted and
implemented as v0.5.4** (scripted RW-096 / RW-097). **G4-6** (operational
scale: cost/budget reporting) is **accepted and implemented as v0.5.5**
(scripted RW-098 / RW-099). **G4-4** (MCP / extensibility) is **parked**
(no measured hole). **Version 5 pack** is GitHub Release **Version 5** /
tag **v0.5.5** @ `08cf33893d309981c5f75bef260bca87f5c47d29` (covers
**0.5.0–0.5.5** / G4-1–G4-3 + G4-5–G4-7 + G4-6). Tag **v0.5.2** remains
the earlier G4-1–G4-3 pack. Generation 5 is **in progress**. Theme
**G5-1** (public / product-grade 1.0 baseline) is **accepted and
implemented as v1.0.0** (scripted RW-100 / RW-101). Package **1.0.0**.
**Version 1 pack is SHIPPED** as GitHub Release **Version 1** / tag
**v1.0.0** @ `9ff184e0d071784bc8820a1258a3d40daf7f1193` (wheel + sdist;
PR #52). Proven Class A on the 1.0 line is **implemented as v1.0.1**
(scripted RW-102 / RW-103): doctor/health ping honors pinned `cfg.model`;
G4-7 `json_field` does not invent English-glue key `on`. **No GitHub
Release / tag in this PR** — Sanath packs 1.0.1 later only if he asks.
Do **not** claim live text_analyzer@12 PASS. F-17 / F-26 stay closed.
Class C is not a product patch. Remaining-quota not invented.

```
build → test → validate → release → use → discover gaps → build the next version
```

Never skip a generation. Never invent a `v0.3.x` feature without an evidence row.
Stability with no code change is a valid result.

---

## Current status

| item | value |
|---|---|
| Generation in production | **Gen5 in progress** — **v1.0.1** (G5-1 **shipped + packed** as **v1.0.0**; proven Class A **v1.0.1** RW-102 / RW-103). Next: **hold / soak** (no G5-2). Gen4 remains **complete (scripted)** on 0.5.0–0.5.5 (G4-6 **v0.5.5**; G4-7 **v0.5.4**; G4-5 **v0.5.3**; G4-3 **v0.5.2**; G4-2 **v0.5.1**; G4-1 **v0.5.0**). Gen3 remains **complete (scripted)** on 0.4.0–0.4.9. Last live-use with **working inference** is **RW-086** on tag `v0.4.7` @ `850aaf9c` (OpenRouter free; then **429**); prior working-inference row is RW-085 on tag `v0.4.6` @ `8f09be58`; v0.4.6 live NIM attempt is RW-084 **BLOCKED Class C**; last NIM working-inference row remains RW-081 on `v0.4.5` @ `32e9fe87`; Gen2 complete on `387776dc` / tag `v0.3.2`; Gen1 baseline remains tagged `v0.2.3` @ `d121c3f` |
| Package / tag on `main` | **1.0.1** (this change). **Version 1 pack** remains GitHub Release **Version 1** / tag `v1.0.0` @ `9ff184e0d071784bc8820a1258a3d40daf7f1193` (wheel + sdist; merge PR #52). **No GitHub Release / tag in this PR.** Version 5 pack remains GitHub Release **Version 5** / tag `v0.5.5` @ `08cf33893d309981c5f75bef260bca87f5c47d29` (0.5.0–0.5.5). Tag `v0.5.2` @ `d534bd30384e9f582ca6c08562a6b2cd555fb793` remains the earlier G4-1–G4-3 pack. Tag `v0.5.1` @ `2d4c8b6dd2e75b191a33913b93eb7d77acd3be6b` (merge PR #41) is G4-2. Tag `v0.5.0` @ `d194b8ffc763fc00ad58273e5dd8f0203442041d` (merge PR #39) is G4-1. Tag `v0.4.9` @ `05ea0df302aa6bfd15eccfb84341aeed75d6e1d0` is E3. Tag `v0.4.7` @ `850aaf9c3a931a5ba119bdbb6ec73ae4a6fa73e9` remains the live RW-086 run |
| This change | **v1.0.1 proven Class A** (scripted RW-102 / RW-103). Package **1.0.0 → 1.0.1**. **No GitHub Release / tag.** Not **v1.1.0**. Not a live PASS |
| Generation 2 | **COMPLETE** — theme 1 **v0.3.0** (used RW-065 / RW-068); theme 2 **v0.3.1** (used live RW-066 / RW-068); theme 3 **v0.3.2** (scripted RW-067; used RW-068 / RW-069) |
| Latest use (RW-086) | Live OpenRouter free text_analyzer on v0.4.7 **FAIL** `needs_user` @ tools **12/12**: provider **openrouter** / `nvidia/nemotron-3.5-lightning:free`; `$0`; PLAN `source=fallback` attempts=2; task1 **COMPLETED** + task2 attempts=1; E1 **not live** (0 TaskYield). xxd Class A ENVIRONMENT thrash **CLEARED** (0 xxd / 0 ENVIRONMENT / 0 repair). Residual Class **B+C** (fallback plan, missing tests/README, odd summary + late HTTP **429** `free-models-per-day`). False DONE **0** |
| Live OpenRouter free loop | **PAUSED** until `free-models-per-day` rate limit resets (RW-086). Do not treat further free-model retries as product Class B until rate clears |
| Live NIM loop | **PAUSED / Class C blocked** (RW-084). E1 live gate still **not confirmed**. Scripted RW-083 remains unit evidence |
| Generation 3 | **COMPLETE (scripted)** — theme 1 **implemented** (v0.4.0) **used** (RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 / RW-085 / RW-086); theme 2 **implemented** (v0.4.1) **used** (RW-073 / RW-075 / RW-077 / RW-079 / RW-081 / RW-085 / RW-086); theme 3 slices A–D **v0.4.2–v0.4.5** **used** (RW-075 / RW-077 / RW-079 / RW-081; mkdir live Y on RW-081); slice E1 **v0.4.6** **implemented** (scripted RW-083; live **not confirmed** on RW-084/085/086); slice F **v0.4.7** **implemented** (xxd ENVIRONMENT; scripted RW-086; live RW-086 thrash **CLEARED**); slice E2 **v0.4.8** **implemented** (scripted RW-087; live **not confirmed**); slice E3 **v0.4.9** **implemented** (scripted RW-088; live **not confirmed**). Live E1–E3 confirmation **deferred** until a provider recovers |
| Generation 4 | **COMPLETE (scripted)** — **G4-1** as **v0.5.0** (scripted RW-089); **G4-2** as **v0.5.1** (scripted RW-090 / RW-091); **G4-3** as **v0.5.2** (scripted RW-092 / RW-093); **Version 5 pack** shipped; **G4-5** as **v0.5.3** (scripted RW-094 / RW-095); **G4-7** as **v0.5.4** (scripted RW-096 / RW-097); **G4-6** as **v0.5.5** (scripted RW-098 / RW-099). **G4-4 parked** (no measured hole). Live confirmation **deferred** |
| Generation 5 | **IN PROGRESS** — **G5-1** as **v1.0.0** (scripted RW-100 / RW-101); Version 1 pack **SHIPPED** (tag **v1.0.0**). Proven Class A **v1.0.1** (scripted RW-102 / RW-103). **Next: hold / soak** (no G5-2). **No GitHub Release / tag in this PR.** |
| Needle | optional / **off** (`tool_router=existing`; ADR-001) |
| `max_plan_tasks` | **16** (unchanged) |
| Default `Budget.tool_calls` | **60** (unchanged) |
| Default plan retries | **1** (hard cap 3) |
| False `DONE:` → `VERIFIED` | **0** (invariant) |

Cycle evidence, not this file: [MATURATION_CYCLE_REPORT.md](MATURATION_CYCLE_REPORT.md),
[REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md),
[REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md).

---

## Generations

| Gen | Name | Versions | Status |
|---|---|---|---|
| **1** | Foundation | v0.2.0, v0.2.1, v0.2.2, **v0.2.3** | **COMPLETE** |
| **2** | Capability Expansion | v0.3.x | **COMPLETE** (theme 1 → **v0.3.0**; theme 2 → **v0.3.1** used RW-066/068; theme 3 → **v0.3.2**; use campaign RW-068 PASS / RW-069 FAIL) |
| **3** | Autonomous Agent Maturity | v0.4.x | **COMPLETE (scripted)** (theme 1 → **v0.4.0**; theme 2 → **v0.4.1**; theme 3 slices A–D → **v0.4.2–v0.4.5**; slice E1 → **v0.4.6**; slice F → **v0.4.7**; slice E2 → **v0.4.8**; slice E3 → **v0.4.9**; live E1–E3 **deferred**) |
| **4** | Production Scale | v0.5.x | **COMPLETE (scripted)** (G4-1 → **v0.5.0**; G4-2 → **v0.5.1**; G4-3 → **v0.5.2** Version 5 pack; G4-5 → **v0.5.3**; G4-7 → **v0.5.4**; G4-6 → **v0.5.5**; G4-4 parked; live confirmation deferred) |
| **5** | 1.0 | v1.0.0–**v1.0.1** | **IN PROGRESS** (G5-1 → **v1.0.0** packed; proven Class A → **v1.0.1**; **next: hold / soak**; no G5-2) |

Enter the next generation only after the previous one has been **released, used, and has
measured gaps**. Class B rows are the input to that decision. They do not start the
generation by themselves — a theme must be **accepted**. Gen2 themes 1–3 shipped and
were used (v0.3.2 campaign). Gen3 theme 1 is **accepted and implemented**
(v0.4.0) and **used** (RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081). Gen3 theme 2 is **accepted and
implemented** (v0.4.1) and **used** (RW-073 / RW-075 / RW-077 / RW-079 / RW-081). Gen3 theme 3 is **planned /
scoped**; slice A (ASCII-tree `package_dir`) is **implemented** (v0.4.2) and
**used** (RW-075 / RW-077 / RW-079 / RW-081); slice B (first-task thrash) is **implemented** (v0.4.3)
and **used** (RW-077 / RW-079 / RW-081); slice C (mkdir already-exists action noise) is
**implemented** (v0.4.4) and **used** (RW-081 mkdir live Y); slice D (premature-test ENVIRONMENT) is **implemented**
(v0.4.5) and **used** (RW-081; premature-test path not live-hit). Slice E1
(task-boundary yield / leftover-budget dispatch) is **accepted and implemented**
(v0.4.6; scripted RW-083). Live NIM retest of v0.4.6 is **RW-084 BLOCKED
Class C**. Live OpenRouter retest of v0.4.6 is **RW-085 FAIL**; E1 **not
live**. Slice F (optional `xxd` ENVIRONMENT) is **Class A CONFIRMED** as
**v0.4.7**. Live OpenRouter retest of v0.4.7 is **RW-086 FAIL**; xxd Class A
thrash **CLEARED**; E1 **not live**; late **429**. Live OpenRouter free-model
loop **paused**. Live NIM loop **paused**. Slice E2 is **accepted and
implemented** as **v0.4.8** (scripted RW-087). Slice E3 is **accepted and
implemented** as **v0.4.9** (scripted RW-088). Gen3 is **complete
(scripted)**. Live E1–E3 confirmation is **deferred** until a provider
recovers. Gen4 is **complete (scripted)**. G4-1 is **accepted and implemented**
as **v0.5.0**. **G4-2** (live-gate resume / provider health
observability) is **accepted and implemented** as **v0.5.1**.
**G4-3** (live-use campaign / operator workflow) is **accepted and
implemented** as **v0.5.2**. **Version 5 pack** shipped (GitHub Release
**v0.5.2**). **G4-5** (fallback / LLM plan quality) is **accepted and
implemented** as **v0.5.3** (scripted RW-094 / RW-095). **G4-7**
(coding artifact completeness / named package-file contracts) is
**accepted and implemented** as **v0.5.4** (scripted RW-096 / RW-097).
**G4-6** (cost/budget reporting) is **accepted and implemented** as
**v0.5.5** (scripted RW-098 / RW-099). **G4-4 parked** (no measured
hole). **Version 5 pack** is GitHub Release **Version 5** / tag
**v0.5.5** (0.5.0–0.5.5). Remaining measured gaps on 0.5.x are operator
live-use or proven Class A, not a G4-8. First Gen5 theme **G5-1**
(public / product-grade 1.0 baseline) is **accepted and implemented as
v1.0.0** (scripted RW-100 / RW-101). **Version 1 pack SHIPPED** (GitHub
Release **Version 1** / tag **v1.0.0**). **No further Gen5 product theme**
until soak / proven Class A / a written accept. **No GitHub Release /
tag** in this docs PR. Stay **1.0.0**.

---

## Operating loop (every version)

```
build → test → validate → release → use → discover gaps → build the next version
```

### Per-cycle rules (maturation doctrine)

| rule | meaning |
|---|---|
| Classify A / B / C | Every failure gets a class before it gets a patch or a theme |
| **Class A** | RAD defect. Smallest patch + regression on the **current minor line** while still in that generation |
| **Class B** | Model / planner limitation on a working product path. **Evidence only** until a generation theme is accepted |
| **Class C** | Environment / keys / provider / catalog. Unblock the environment. Do **not** invent a product fix |
| Stability is valid | A cycle that finds no Class A and does not bump is a success |
| No generation skip | Do not jump to v0.3.x / v0.4.x / v1.0.0 because a FAIL row exists |
| No invented features | Do not design a v0.3.0 capability without a named evidence row |
| Invariants hold | Models propose / RAD decides. Needle off by default. Caps unchanged unless a measured product need is documented |

Cycle reports that say “Evidence for v0.3.0: none” mean **no control-plane hole and no
generation skip**. They do not contradict this roadmap. The accepted Gen2 theme is a
**capability** addition on the existing control plane, not a missing stage.

### Gates before any release

Run all of these. `live_nim` may honestly **BLOCKED** (Class C). That is not a FAIL.

| gate | command |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` |

A model `DONE:` line is never a gate. `VERIFIED` is independent disk / shell / JSON checks only.

---

## Generation 1 — Foundation — COMPLETE

Shipped: **v0.2.0**, **v0.2.1**, **v0.2.2**, **v0.2.3**.

Current production baseline: **v0.2.3** (GitHub Release / annotated tag `v0.2.3` at
`d121c3f8875cb01e816bb5f7df66e62ee26e1eba`). Main may carry later docs and investigation
tests (merged after the tag; through PR #18) without a package bump. This change bumps
the package to **0.3.0**.

What Gen1 locked:

| invariant | lock |
|---|---|
| Control plane | Models propose / RAD decides. The executor is the only way to act |
| Needle | Off by default. Optional adapter only. Not enabled in 0.3.0 (ADR-001) |
| Planner cap | `max_plan_tasks` default **16** |
| Tool budget | Default `Budget.tool_calls` **60** |
| Honesty | False `DONE:` (claim without the artifact) **= 0** |
| Completion | `VERIFIED` only via independent machine checks — never the model’s own word |

Gen1 also shipped the evidence loop: ledger, task matrix, maturation reports, `rad realworld`,
and the A/B/C classification. That loop continues.

Remaining 0.2.x work, if any after this ships, is none on this theme. Class B that is not
an accepted theme stays on the ledger. Class C stays BLOCKED. Do not raise caps. Do not
enable Needle.

---

## Generation 2 — Capability Expansion — COMPLETE (v0.3.x)

Evidence-backed capability additions **on top of** the Gen1 control plane.

- Do **not** redesign the control plane.
- Do **not** enable Needle by default without a gold-set win (`rad needle-eval`).
- Do **not** raise `max_plan_tasks` or default tool budget without a measured product need.

### Accepted first build — verified coding loop (v0.3.0)

| field | value |
|---|---|
| Status | **IMPLEMENTED** in this change (package **0.3.0**) |
| Theme | **Verified coding loop** |
| Version | **v0.3.0** |
| Loop | write → run tests / checks → repair until **disk checks** pass |
| Evidence | RW-058, RW-059, RW-062 (F-20260918-15 / 16 / 19 / 22); deterministic RW-064 / F-20260918-24; live use RW-065 / F-20260918-25 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not plan-timeout (that is v0.3.1) or budget-aware planning (that is v0.3.2). Not a claim that live 11B Class B runs now pass. |

Live Gen1 coding runs left invalid `result.json` / `summary.json`, failing tests (`13!=6`,
`6!=2`), duplicated “tests”, wrong paths, and pollution `DONE:` fake paths. RAD stopped at
the budget; the verifier did **not** rubber-stamp. False DONE **0**. The 0.3.0 work keeps
going through write → test → repair until independent disk checks pass, without weakening
`DONE:` / `VERIFIED`.

A model `DONE:` is never completion. `DONE:` pollution paths are refused. Fallback *tasks*
stay check-less (F-17); coding goals infer *objective* `json_valid` / test `shell_ok`.
Broken artifacts (`json_valid`, failing tests) insert one repair step with the concrete
failure; missing `file_exists` still `retry_with_hint`.

### Accepted second build — plan-timeout resilience (v0.3.1)

| field | value |
|---|---|
| Status | **IMPLEMENTED** in this change (package **0.3.1**) |
| Theme | **Plan-timeout resilience** |
| Version | **v0.3.1** |
| Loop | timeout / empty / malformed / non-JSON plan → **one bounded retry** for structured JSON with checks → else `_fallback(obj)` |
| Evidence | RW-062 (nvidia plan timeout → `source=fallback`); RW-063 / F-17 (fallback is goal clause-split, not model-prose parse); deterministic RW-066 / F-20260918-27; live use RW-066 / F-20260918-28 |
| What it is not | Not a rewrite of F-17. Not Needle-as-default. Not a cap raise. Not budget-aware planning (theme 3, v0.3.2). Not a claim that live 11B Class B coding is solved. |

When the LLM planner times out or returns empty/malformed/non-JSON once, RAD retries
(default **1**, hard cap **3**) with a “Reply ONLY with JSON” nudge for a structured plan
that keeps machine checks. Exhausted retries still `_fallback(obj)`: goal-only clause
split, cap 7, no checks (F-17 unchanged). First-try valid JSON is unchanged (one attempt,
`source=llm`). Planning LLM calls are **not** charged to `Budget.model_calls` (the
controller meters model calls on task execution, as before).

### Accepted third build — budget-aware planning (v0.3.2)

| field | value |
|---|---|
| Status | **IMPLEMENTED** (package **0.3.2**) |
| Theme | **Budget-aware planning** |
| Version | **v0.3.2** |
| Loop | remaining tool budget → plan prompt; fat graph (over 2-tools/task fit **and** >3 tasks) → **one bounded retry** with a cheaper JSON plan → select the cheaper graph; fat fallback → compact. LLM graphs not silently compacted (F-21) |
| Evidence | RW-059 Case B (12→24 tools still exhausted); RW-065 / live RW-066 tools 12/12; deterministic RW-067 / F-20260918-29; live use RW-068 / RW-069 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not an executor thrash limiter (RW-059 19× write_file stays Class B). Not a claim that live 11B Class B coding is solved. Not a re-open of F-17 / F-26. |

When remaining `Budget.tool_calls` / `--max-tools` is known, RAD asks for a plan
that fits (each task estimated at 2 tool calls). A fat LLM plan is retried with
a budget nudge; the cheaper candidate is kept. Fallback graphs that are still
fat are compacted (F-17: still no checks on tasks). Graphs of 3 tasks or fewer
may exceed remaining tools — that is leftover work (F-21), not a fat plan.
Default `max_plan_tasks` **16** and default `Budget.tool_calls` **60** are
unchanged. Planning LLM calls are still not charged to `Budget.model_calls`.

### Entry criteria (how Gen2 opened)

Gen2 starts only when **all** of the following are true. They are true for this theme:

1. Gen1 invariants still hold on the production baseline (0.2.3).
2. At least one **Class B theme is accepted** as a product theme — an explicit decision, not
   implied by a `needs_user` / FAIL row. **Done:** verified coding loop, 2026-09-18 (PR #18).
3. That theme is grounded in **live Gen1 production evidence** (the F-22 family), not in a
   reconstructed offline story and not in a closed non-gate.
4. Release gates are green (pytest, `rad doctor --offline`, `rad acceptance`,
   `rad realworld`). `live_nim` may be BLOCKED.

### Themes (from live Class B evidence)

Grounded in RW-058 / RW-059 / RW-060 / RW-062 and the F-22 family
(F-20260918-15 / 16 / 19 / 20 / 22).

| # | theme | status | what the evidence showed | rows |
|---|---|---|---|---|
| 1 | **Verified coding loop** | **IMPLEMENTED** — v0.3.0; **used** RW-065 / RW-068 | Write → run tests → repair until **disk checks** pass. Live 11B word_counter is **PASS** on v0.3.2 (RW-068). Multi-file still Class B under tools=12. | RW-058, RW-059, RW-062; RW-064 (scripted); RW-065 / RW-068 (live use) |
| 2 | **Plan-timeout resilience** | **IMPLEMENTED** — v0.3.1; **used** live RW-066 / RW-068 | Retry / re-ask for a JSON plan **before** falling back to no-check goal clause-split. Live RW-066: `attempts=2` then `source=fallback`. Live RW-068: `llm` attempts **1**. F-17 fallback contract preserved. | RW-062 (timeout path); RW-063 closed the Class A reading; scripted RW-066 (F-27); live RW-066 (F-28); RW-068 |
| 3 | **Budget-aware planning** | **IMPLEMENTED** — v0.3.2; **used** this campaign | Plan that fits the tool budget. RW-059 Case B: doubling tools **12→24** still exhausted the budget and did **not** complete. Default max-tools was **not** raised. RW-069 still FAIL at tools=12. | RW-059 vs RW-058; RW-060 / RW-062 / RW-065 / live RW-066 also budget-stop; RW-067 (scripted); RW-068 / RW-069 (live use) |

The F-22 family is the same pattern on coding **and** research **and** a simpler
coding+verification control: 11B + tool budget, success criteria unmet, `needs_user`,
not VERIFIED. Class B is **not** complexity-limited. It is also **not** a missing
control-plane stage. Accepting the coding loop does **not** accept the research stub
(RW-060 / F-20) as a v0.3.0 theme.

### Closed non-gates (not Gen2 themes)

These were investigated and are **not** product themes for v0.3.x:

| id | claim | result |
|---|---|---|
| F-17 | Fallback planner splits newlines / converts model prose into spurious tasks | **NOT CONFIRMED.** PR #14 / RW-061: newline-only goal → 1 fallback task. RW-063: timeout/empty/malformed/non-JSON LLM is discarded; `_fallback` splits `obj.goal` on clause markers, cap `[:7]`. No product patch. No v0.2.4. |
| F-18 / budget → `needs_user` | Budget exhaustion is a RAD defect | **Path is correct** (PR #14 / RW-061). Unmet checks → `needs_user` + checkpoint; satisfied checks → `VERIFIED`. False DONE **0**. |
| F-26 / json_valid-on-.py | LLM `json_valid` on `.py` is a RAD hole that causes false FAILED → ENVIRONMENT_FAILURE | **NOT CONFIRMED.** RAD does not emit json_valid on `.py`. Isolated json_valid-on-.py is honest not-JSON + VALIDATION repair. Live RW-065 ENVIRONMENT matches shell `No such file` (F-18 path). No product patch. Stay 0.3.0. |

Do not reopen those as Gen2 work unless new disk evidence changes the class.

### Accepting a further theme

Gen2 themes 1–3 are **complete**. Remaining measured gaps are **Gen3
candidates**, not further 0.3.x work, unless a **proven Class A** appears on
0.3.2 (patch on the current minor line). Do not treat v0.3.2 as a blanket
redesign, and do not start v0.4.0 without an accepted first theme.

---

## Generation 3 — Autonomous Agent Maturity — COMPLETE (scripted) (v0.4.x)

More reliable multi-step execution, recovery, planning, and long-horizon work.

**Status:** **complete (scripted).** Theme 1 — **path-aligned checks / package layout** —
is **implemented as v0.4.0** and **live-confirmed** (RW-071; RW-073 disk/tasks;
RW-075 obj-checks; RW-081). Theme 2 — **multi-file coding under tight budgets** — is
**implemented as v0.4.1** and **live-confirmed** (RW-073; RW-081). Theme 3 —
**longer-horizon / multi-step reliability** — is **complete (scripted)**. Slice A
(ASCII-tree `package_dir`) is **implemented as v0.4.2** and **used** (RW-075 /
RW-077 / RW-079 / RW-081). Slice B (first-task thrash) is **implemented as v0.4.3** and **used**
(RW-077 / RW-079 / RW-081). Slice C (mkdir already-exists action noise) is **implemented as
v0.4.4** and **live-confirmed** (RW-081). Slice D (premature-test
ENVIRONMENT) is **implemented as v0.4.5** and **used** (RW-081; premature-test
path **not live-hit**). Slice E1 (task-boundary yield / leftover-budget
dispatch) is **accepted and implemented as v0.4.6**. Slice F (optional
checksum/hex utility ENVIRONMENT) is **implemented as v0.4.7**. Slice E2
(independent later package files) is **accepted and implemented as
v0.4.8**. Slice E3 (budget-aware retry stop) is **accepted and
implemented as v0.4.9**. Package is **0.4.9**. Live RW-084 is **BLOCKED Class C** (HTTP
403; E1 **not live-tested**). Live RW-085 is **FAIL** on OpenRouter free
(tools 11/12; E1 **not live**; xxd ENVIRONMENT **CONFIRMED**). Live RW-086
is **FAIL** on OpenRouter free (tools 12/12; xxd Class A thrash
**CLEARED**; E1 **not live**; late HTTP **429** `free-models-per-day`).
Live OpenRouter free-model loop is **paused**. Live NIM loop is
**paused**. Live E1–E3 confirmation is **deferred** until a provider
recovers. Live artifact quality (incomplete package, odd summary,
missing README/tests) is **not** claimed fixed. Pip/root-pollution Class A
is **NOT CONFIRMED** (RW-082). Remaining measured gaps are **Gen4
candidates**, not further 0.4.x themes, unless a **proven Class A**
appears on 0.4.9.

Do not pre-design Gen3 from Gen1 Class B rows alone. Do not skip Gen2 (Gen2 is
now complete). Do not treat a FAIL row as an automatic architecture rewrite.

### Entry criteria (how Gen3 opened)

Gen3 **build** starts only when **all** of the following are true. They are true
for this theme:

1. **Gen2 complete (0.3.0–0.3.2) — DONE.** Verified coding loop (v0.3.0),
   plan-timeout resilience (v0.3.1), budget-aware planning (v0.3.2) shipped.
   v0.3.2 use campaign recorded (RW-068 **PASS**, RW-069 **FAIL**).
2. Sanath **accepts a first v0.4.0 theme** — **Done:** path-aligned checks /
   package layout (Gen3 theme 1).
3. That theme is grounded in **measured Gen2-use gaps** (RW-069 A2 watch), not in
   a reconstructed offline story and not in a closed non-gate.
4. **Class A only when proven.** Investigate-first confirmed RAD emits and
   accepts root-only machine checks that disagree with a named package layout.
5. Needle stays **OFF**. Caps (`max_plan_tasks` **16**, default
   `Budget.tool_calls` **60**) unchanged unless a proven product need is
   documented.
6. Operating loop unchanged:
   `build → test → validate → release → use → discover gaps`.

Release gates must still be green (pytest, `rad doctor --offline`,
`rad acceptance`, `rad realworld`). `live_nim` may be BLOCKED.

### Accepted first build — path-aligned checks / package layout (v0.4.0)

| field | value |
|---|---|
| Status | **IMPLEMENTED** in this change (package **0.4.0**) |
| Theme | **Path-aligned checks / package layout** |
| Version | **v0.4.0** |
| Loop | package-layout goal → bare check paths joined to that directory; LLM root-only checks remapped the same way; verifier still evaluates the stored path honestly |
| Evidence | RW-069 / F-20260918-31 (A2 watch); deterministic RW-070 / F-20260918-32; live use RW-071 / F-20260918-33 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not Gen3 theme 2 (that is v0.4.1). Not a claim that live 11B RW-069 / RW-071 now PASS. Not a remap of check *kinds* (F-26). Fallback *tasks* stay check-less (F-17). |

A package-layout goal (`under text_analyzer/`, `text_analyzer/{…}`, two or
more files sharing one non-`tests` directory prefix, or an ASCII / box-drawing
tree `text_analyzer/` + `├── file`) is the source of truth for layout. RAD
joins bare `file_exists` / `json_valid` / … paths and bare `test_*.py` in
`shell_ok` commands to that directory so first writes under the package can
verify without a false VALIDATION retry that flattens files to the workspace
root. Directed paths (`pkg/foo.json`, `tests/check_stats.py`) are kept. A
single `pkg/foo.py` mention is not a layout. Markdown dash lists are not a
tree. The verifier does **not** guess a package dir at check time. ASCII-tree
recognition shipped as **v0.4.2** (RW-073 / RW-074).

### Accepted second build — multi-file contracts under tight budgets (v0.4.1)

| field | value |
|---|---|
| Status | **IMPLEMENTED** in this change (package **0.4.1**) |
| Theme | **Multi-file coding under tight budgets** |
| Version | **v0.4.1** |
| Loop | package/coding goal → merge omitted `json_valid` / `file_line_count` / test `shell_ok` into objective checks; mkdir/create already-exists is not ENVIRONMENT |
| Evidence | RW-071 / F-20260918-33 (theme 1 live-confirmed; Class B residual + ENVIRONMENT mkdir thrash); deterministic RW-072 / F-20260918-34 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live 11B RW-071 now PASS. Not a remap of check *kinds* (F-26). Fallback *tasks* stay check-less (F-17). Path-aligned checks preserved. |

When a coding goal names a package layout (and exact N-line / `.json` / tests),
RAD **adds** the omitted machine contracts to `objective_checks` so a weak
`file_exists` plan cannot VERIFIED an empty `summary.json` or a collapsed
1-line `input.txt`. `mkdir` / create **already exists** mixed with no-such-file
check noise is TOOL/VALIDATION coding repair — not Repair-prerequisite
ENVIRONMENT thrash. Genuine `command not found` stays ENVIRONMENT. The
verifier still evaluates the stored path honestly.

### Theme 3 — COMPLETE (scripted) (longer-horizon); slices A–E3 shipped

| field | value |
|---|---|
| Status | **COMPLETE (scripted)**. Slice A **IMPLEMENTED** as v0.4.2. Slice B **IMPLEMENTED** as v0.4.3. Slice C **IMPLEMENTED** as v0.4.4 (**used** RW-081). Slice D **IMPLEMENTED** as v0.4.5 (**used** RW-081; premature-test path not live-hit). Slice E1 **ACCEPTED + IMPLEMENTED** as v0.4.6 (scripted RW-083; live **not confirmed** on RW-084/085/086). Slice F **IMPLEMENTED** as v0.4.7 (xxd ENVIRONMENT; scripted RW-086; live RW-086 thrash **CLEARED**). Slice E2 **ACCEPTED + IMPLEMENTED** as v0.4.8 (scripted RW-087; live **not confirmed**). Slice E3 **ACCEPTED + IMPLEMENTED** as v0.4.9 (scripted RW-088; live **not confirmed**). Live E1–E3 confirmation **deferred** |
| Theme | **Longer-horizon / multi-step reliability** |
| Version | Theme 3 itself is **not** a full v0.4.x redesign. Slice A is **v0.4.2**. Slice B is **v0.4.3**. Slice C is **v0.4.4**. Slice D is **v0.4.5**. Slice E1 is **v0.4.6**. Slice F is **v0.4.7**. Slice E2 is **v0.4.8**. Slice E3 is **v0.4.9** |
| Loop (slice E3) | failed attempt of a stuck task → remaining tools below leftover reserve plus `TOOLS_PER_TASK` → yield (no retry / no repair insert) → E1 leftover dispatch runs later independent READY work |
| Evidence | RW-081 / F-20260918-43 (live FAIL; later package tasks PENDING while tools 12/12); deterministic RW-082 / F-20260918-44 (**NOT CONFIRMED**); scripted RW-083 / F-20260918-45 (E1: later independent `file_exists` still gets ≥1 attempt); live RW-084 / F-20260919-46 (**BLOCKED Class C**; E1 not live-tested); live RW-085 / F-20260919-47 (**FAIL** OpenRouter; E1 not live; xxd ENVIRONMENT live); scripted RW-086 / F-20260919-48 (xxd ≠ ENVIRONMENT); live RW-086 / F-20260919-49 (**FAIL** OpenRouter; xxd thrash **CLEARED**; E1 not live; late **429**; later fallback tasks 0 attempts); scripted RW-087 / F-20260919-50 (E2: later independent fallback file still gets ≥1 attempt); scripted RW-088 / F-20260919-51 (E3: retry/repair stop before leftover reserve is spent; later file ≥1 attempt) |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live 11B RW-081 now PASS. Not a new persistence layer. Not a remap of check *kinds* (F-26). Fallback *tasks* stay check-less (F-17). Not remapping `write_file` / `echo >` action paths (F-44). Not rewriting explicit LLM `depends_on` chains. |

**Entry rule:** themes 1–2 are measured (done). Slice A shipped as v0.4.2
(ASCII-tree `package_dir`; **used** RW-075 / RW-077 / RW-079 / RW-081). Slice B shipped as v0.4.3
(first-task pip/DONE thrash; **used** RW-077 / RW-079 / RW-081). Slice C shipped as v0.4.4
(mkdir already-exists action noise; **live-confirmed** RW-081). Slice D shipped as v0.4.5
(premature-test ENVIRONMENT; **used** RW-081, path **not live-hit**). Thrash Class A
chase is **paused** after RW-081 pip/root-pollution **NOT CONFIRMED**. Slice E1
is **accepted and implemented**. Slice E2 is **accepted and implemented**.
Slice E3 is **accepted and implemented**.
Do **not** invent a long-horizon redesign from Class B budget/quality rows.

### Theme 3 slice E1 — ACCEPTED + IMPLEMENTED (task-boundary yield)

Stay on **theme 3** (longer-horizon remainder). This is **not** Gen3 theme 4
and **not** Gen4. Naming: **slice E1**. Status: **ACCEPTED + IMPLEMENTED**.

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** in this change (package **0.4.6**) |
| Theme | **Task-boundary yield / leftover-budget dispatch** — later independent READY work still gets ≥1 attempt when an early task would burn remaining tools |
| Version | **v0.4.6** |
| Loop | remaining tools ≤ reserved leftover for unattempted independent READY tasks → `TaskYield` at the executor / retry-verify boundary → `CheckpointManager.save` (`RETRYING`, `verification.yielded`) → `Scheduler` prefers non-yielded READY work |
| Evidence | RW-081 / F-20260918-43 (driver); deterministic RW-083 / F-20260918-45; live RW-084 / F-20260919-46 (**BLOCKED Class C**; E1 not live-tested) |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live 11B RW-081 now PASS. Not a new checkpoint format. Not remapping `write_file` / `echo >` (F-44). Not rubber-stamping unmet checks. Fallback *tasks* stay check-less (F-17). Not E2 (chained later files stay unready). E3 strengthens this leftover boundary at retry/repair time (v0.4.9) |

When a sequential in-flight task is about to consume the last reserved tool
calls, RAD **yields at a task boundary**: the stuck task is checkpointed as
`RETRYING` (existing `CheckpointManager` / `tasks.json`), and leftover tools
are spent on later independent READY work via `Scheduler.next_batch` /
`graph.ready()`. Unmet checks stay not `VERIFIED`. False DONE **0**. Linear
fallback file-write `depends_on` is emptied by E2 (v0.4.8). Unlimited tool
budgets do not yield.

#### Problem statement (unchanged driver)

Longer-horizon coding still fails under tight budgets **after** thrash Class A
fixes. Live RW-081 still stops `needs_user` @ 12/12 with later package files
never attempted: the drive loop stayed on the current task until the tool
budget died. Persistence already shipped (`CheckpointManager`, `resume`,
`_on_budget`). E1 strengthens that path **inside one tight-budget run**.

#### Candidates remaining

| id | candidate | status |
|---|---|---|
| **E1** | Task-boundary yield / leftover-budget dispatch | **IMPLEMENTED** v0.4.6 (scripted RW-083; live **not confirmed** on RW-084/085/086) |
| **E2** | Independent later package files (optional / empty `depends_on`) | **IMPLEMENTED** v0.4.8 (scripted RW-087; live **not confirmed**) |
| **E3** | Budget-aware retry stop (2-tools/task at retry time) | **IMPLEMENTED** v0.4.9 (scripted RW-088; live **not confirmed**) |
| **F** | Optional checksum/hex utility (`xxd`) ENVIRONMENT | **IMPLEMENTED** v0.4.7 (scripted RW-086; live RW-085 confirmed; live RW-086 thrash **CLEARED**) |

E1 + E2 + E3 do **not** claim live RW-081 / RW-086 would PASS (Class B quality
remains). E1/E2/E3 are scripted only.

#### Non-goals

- Needle **on**, or Needle-as-default
- Raising `max_plan_tasks` **16** or default `Budget.tool_calls` **60** as the
  primary fix (A1 / F-21 stay closed)
- Claiming Class B 11B coding quality (empty `summary.json`, SyntaxError tests,
  pip/echo, root leftover) is solved
- New checkpoint file format, SQLite, or a second resume protocol
- Remapping model-proposed `write_file` / `echo >` paths into `package_dir`
  (F-44 anti-patch)
- Rubber-stamp `VERIFIED` / `DONE:` when machine checks are unmet
- Reopening F-17 / F-18 / F-21 / F-26, or another thrash Class A chase
- Treating `rad objective resume` with a **raised** budget as the product fix

### Theme 3 slice E2 — ACCEPTED + IMPLEMENTED (independent later files)

Stay on **theme 3** (longer-horizon remainder). This is **not** Gen3 theme 4
and **not** Gen4. Naming: **slice E2**. Status: **ACCEPTED + IMPLEMENTED**.

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** in this change (package **0.4.8**) |
| Theme | **Independent later package files** — later file-write fallback clauses stay READY (`depends_on=[]`) so Scheduler / E1 leftover reserve can run them while an early task is stuck |
| Version | **v0.4.8** |
| Loop | fallback clause-split → `independent_file_clause` → empty `depends_on` on distinct file writes; run/verify/read consume steps still chain; E1 yield can then dispatch the later file under the same `--max-tools` cap |
| Evidence | live RW-085 / RW-086 (fallback chain; later tasks 0 attempts); scripted RW-087 / F-20260919-50 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live text_analyzer@12 now PASS. Not a new graph format (`optional` / `alternatives` / `depends_on` already exist). Not adding checks to fallback *tasks* (F-17). Not rewriting explicit LLM `depends_on` chains. E3 is a leftover-boundary strengthen at retry/repair time, not a second graph format |

Investigate-first: E1 leftover reserve is already 0 when later tasks wait
on the in-flight one (`graph.ready()`). `optional` only unblocks after
FAILED / BLOCKED / CANCELLED, not while RETRYING. The hole is fallback
emission (`depends_on=[prev]` on every clause), not a missing scheduler
primitive. Smallest patch: empty `depends_on` on independent file-write
clauses. Consume/verify/read stays chained. False DONE **0**.

### Theme 3 slice E3 — ACCEPTED + IMPLEMENTED (budget-aware retry stop)

Stay on **theme 3** (longer-horizon remainder). This is **not** Gen3 theme 4
and **not** Gen4. Naming: **slice E3**. Status: **ACCEPTED + IMPLEMENTED**.

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** in this change (package **0.4.9**) |
| Theme | **Budget-aware retry stop** — retries and repair inserts on a stuck task stop when remaining tools cannot cover leftover reserve plus `TOOLS_PER_TASK`, yielding to the E1 path so later independent READY work still gets ≥1 attempt |
| Version | **v0.4.9** |
| Loop | failed first attempt → `should_yield_for_leftover` (`rem < leftover_tool_reserve + TOOLS_PER_TASK`) → `_yield_task` (no `retry` / `repair`) → Scheduler prefers later READY → E1 leftover dispatch |
| Evidence | live RW-085 / RW-086 (early-task retry / repair / shell thrash burns tools); scripted RW-088 / F-20260919-51 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live text_analyzer@12 now PASS. Not a parallel retry estimator. Not a change to executor `reserve_tools` (still 1 per later READY). Not rewriting E2 `depends_on`. Unlimited budgets do not yield. Solo tasks with no later READY still retry. |

Investigate-first: E1 `TaskYield` already stops mid-think when `rem <= reserve`.
The hole is the **retry / repair decision** after a failed attempt: when
`rem = reserve + 1`, recovery still started another attempt of the stuck
task and spent the spare tool E1 was holding for later READY work.
Smallest patch: reuse leftover reserve + `TOOLS_PER_TASK` at that
boundary (and refuse to start a `RETRYING` dispatch that would burn it).
False DONE **0**.

### Themes (evidence-backed; priority order)

Grounded in RW-068 / RW-069 / RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 and the residual RW-058 / RW-059
family (F-20260918-15 / 16 / 19 / 31 / 33 / 35 / 37 / 39 / 41 / 43). Simple coding **PASS** on
v0.3.2 is **not** a Gen3 hole (B3).

| # | theme | status | what the evidence showed | rows |
|---|---|---|---|---|
| 1 | **Path-aligned checks / package layout** | **IMPLEMENTED** — v0.4.0; **used** RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 | Task checks required workspace-root `input.txt` while first successful writes were under `text_analyzer/` → VALIDATION_FAILURE → retry flattened files to root → layout thrash. Confirmed as planner/infer emission + LLM-check acceptance (not just 11B). Live RW-081: path-alignment **Y** on disk/tasks **and** objective_checks (ASCII-tree join live). Root `echo > analyzer.py` leftover is Class B, not check-path flattening. | RW-069; RW-070 (scripted); RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 (live use); RW-074 (scripted ASCII-tree); related path confusion on RW-058 |
| 2 | **Multi-file coding under tight budgets** | **IMPLEMENTED** — v0.4.1; **used** RW-073 / RW-075 / RW-077 / RW-079 / RW-081 | `text_analyzer` @ tools=**12** still FAIL on live 11B. RW-081: contracts **package-joined**; correct 3-line `bf69eb73…`; mkdir File-exists **live Y**. Residual: empty `summary.json`, SyntaxError test, pip/echo budget. Does not raise default max-tools. | RW-071; RW-072 (scripted); RW-073 / RW-075 / RW-077 / RW-079 / RW-081 (live use); RW-069; RW-058 / RW-059 family (F-15 / F-16 / F-19) |
| 3 | **Longer-horizon / multi-step reliability** | **COMPLETE (scripted)** — slices A–D **IMPLEMENTED** (v0.4.2–v0.4.5); slice E1 **IMPLEMENTED** as v0.4.6 (scripted RW-083; live **not confirmed**). Slice F **IMPLEMENTED** as v0.4.7. Slice E2 **IMPLEMENTED** as v0.4.8 (scripted RW-087). Slice E3 **IMPLEMENTED** as v0.4.9 (scripted RW-088). Live E1–E3 **deferred** | Live RW-086: xxd ENVIRONMENT thrash **CLEARED**; still FAIL `needs_user` @ 12/12 on fallback PLAN + late **429**. E1 did not fire (fallback chain). E2 unchains later independent fallback files (scripted). E3 stops a leftover-eating retry/repair (scripted). Does **not** claim live PASS. | RW-088 (scripted E3); RW-087 (scripted E2); live RW-086 (OpenRouter FAIL; xxd thrash cleared); RW-086 (scripted slice F); RW-085 (live OpenRouter FAIL); RW-084 (live Class C); RW-083 (scripted E1); RW-081; RW-082 (scripted NOT CONFIRMED); RW-079; RW-080 (scripted slice D); RW-077; RW-078 (scripted slice C); RW-075; RW-076 (scripted slice B); RW-074 (scripted slice A) |

### Closed / not automatic Gen3 work

These are **not** a license to raise caps or enable Needle from this change:

| id | claim | result |
|---|---|---|
| A1 | Reopen budget→`needs_user` as Class A | **Do not reopen** without new proof. RW-069 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 exhausted 12 tools with incomplete work; same honest stop as historical Class B investigations (F-21). |
| A2 | Check path vs write path (root vs package dir) | **Class A confirmed** as v0.4.0. **Live-confirmed** on RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 disk+task **checks** (path-alignment Y). RW-081 has extra root `echo > analyzer.py` leftover — that is model action pollution (F-44 **NOT CONFIRMED**), not RAD flattening files to satisfy root checks. Live 11B artifact quality remains Class B. |
| A4 | ASCII-tree `infer_package_dir` miss | **Class A confirmed** as v0.4.2 (theme-1 follow-up / theme 3 slice A). **Live-confirmed** on RW-075 / RW-077 / RW-079 / RW-081 (objective_checks all package-joined; 0 bare). |
| A5 | First-task thrash (pip-missing-requirements ENVIRONMENT + DONE-as-tool) | **Class A confirmed** as v0.4.3 (theme 3 slice B). **Live-consistent** on RW-077 / RW-079 / RW-081 (0 invented DONE; pip `-r` attempted on RW-081 without ENVIRONMENT repair). Do not re-litigate. |
| A6 | mkdir File-exists failing a check-passing task | **Class A confirmed** as v0.4.4 (theme 3 slice C). Unit RW-078. **Live-confirmed** on RW-081 (task VERIFIED despite File-exists action error). Do not regress. |
| A7 | Premature `python …/test_*.py` No-such-file → ENVIRONMENT | **Class A confirmed** as v0.4.5 (theme 3 slice D). Unit RW-080. **Not live-hit** on RW-081 / RW-085. Do not regress. |
| A8 | Pip thrash + root `echo > analyzer.py` pollution under known `package_dir` | **NOT CONFIRMED.** Checks already join to `package_dir`. Actions are model-proposed (no write/redirect remap). Root file does not satisfy package checks (false DONE 0). Joining echo redirects would clobber a good package file. PLAN_PROMPT already forbids pip for stdlib-only; ingest-reject still charges tools. Stay paused. See RW-082 / F-44. |
| A9 | Missing optional `xxd` / checksum utility → ENVIRONMENT + Repair-prerequisite | **Class A confirmed** as v0.4.7 (theme 3 slice F). Live RW-085: `xxd: not found` exit 127 classified ENVIRONMENT while `file_nonempty` input.txt passed. Scripted RW-086. Live RW-086: xxd Class A thrash **CLEARED** (0 xxd / 0 ENVIRONMENT / 0 repair; host still missing `xxd`; model avoided it — absence of thrash, not a positive classifier observation). Genuine `python`/`pip`/`gcc` command-not-found stays ENVIRONMENT (F-18). Do not regress. |
| A3 | DONE pollution refuse | **Already works** for `DONE:` *paths*. RW-081 invented-tool `DONE` **0**; slice B still stops it from failing check-passing tasks. |
| B3 | Simple verified coding loop | **Stable PASS** on v0.3.2 (RW-068 llm plan@1). Not a Gen3 hole. |
| F-17 / F-18 / F-21 / F-26 | Prior closed non-gates | **Stay closed.** This cycle does not add checks to fallback *tasks* (F-17) and does not remap check *kinds* (F-26). Genuine `python`/`pip`/`gcc`/`mkreport_*` `command not found` / `ModuleNotFoundError` stay ENVIRONMENT (F-18). Optional `xxd`/hexdump/`sha256sum` not-found is **not** ENVIRONMENT (v0.4.7 / A9). `cat` no-such-file stays ENVIRONMENT. mkdir already-exists still **not** ENVIRONMENT (v0.4.1). |

This cycle is **not** a claim that live 11B text_analyzer now completes under
tools=12. Residual is **Class B** capacity/quality (11B under the historical
12-tool bound; RW-081 pip/echo thrash, empty `summary.json`, SyntaxError test,
root leftover; RW-086 fallback quality + late **429**). Theme-3 measured win
this patch: a stuck task's retry/repair stops when leftover headroom is
below `TOOLS_PER_TASK`, so later independent READY work still gets ≥1
attempt (RW-088). Live RW-084
**BLOCKED Class C**. Live RW-085 **FAIL** OpenRouter (E1 **not live**; xxd
ENVIRONMENT **CONFIRMED** → v0.4.7). Live RW-086 **FAIL** OpenRouter (xxd
thrash **CLEARED**; E1 **not live**; late **429**). Live OpenRouter
free-model loop **paused**. Live NIM loop **paused**.

### Further 0.4.x work

Gen3 themes 1–3 are **complete (scripted)**. Further 0.4.x is **Class A
only when proven** on the current minor line. Remaining measured gaps
(fallback PLAN quality, incomplete package artifacts, free-model thrash,
paused Class C providers, E1–E3 not live-confirmed together) are **Gen4
candidates**, not a fourth Gen3 theme. Do not invent a long-horizon
redesign from Class B budget rows. Pip/root-pollution on RW-081 is
**NOT CONFIRMED** as Class A. Missing optional `xxd` ENVIRONMENT on
RW-085 **is** Class A (v0.4.7). Live RW-086 xxd thrash **CLEARED**.

---

## Generation 4 — Production Scale — COMPLETE (scripted) (v0.5.x)

Operational robustness, extensibility, integrations, larger workloads —
after Gen3 maturity themes have measured (scripted) wins.

**Status:** **complete (scripted).** Theme **G4-1** — **live multi-provider /
free-provider production doctrine** — is **accepted and implemented as
v0.5.0** (scripted RW-089). Theme **G4-2** (live-gate resume / provider
health observability) is **accepted and implemented as v0.5.1**
(scripted RW-090 / RW-091). Theme **G4-3** (live-use campaign / operator
workflow) is **accepted and implemented as v0.5.2** (scripted RW-092 /
RW-093). Theme **G4-5** (fallback / LLM plan quality under tight budgets) is
**accepted and implemented as v0.5.3** (scripted RW-094 / RW-095).
Theme **G4-7** (coding artifact completeness / named package-file
contracts) is **accepted and implemented as v0.5.4** (scripted RW-096 /
RW-097). Theme **G4-6** (cost/budget reporting) is **accepted and
implemented as v0.5.5** (scripted RW-098 / RW-099). **G4-4** (MCP /
extensibility) is **parked** — still no measured hole; do **not**
force-build it. **Version 5 pack** is GitHub Release **Version 5** /
tag **v0.5.5** @ `08cf338` (covers **0.5.0–0.5.5**). Tag **v0.5.2**
remains the earlier G4-1–G4-3 pack. Package on the 1.0 line is **1.0.0**
(G5-1).
Gen4 slices were merge-only until Sanath packed. Same loop. Same A/B/C
rules. Same gates. Needle stays **OFF**. Caps (`max_plan_tasks` **16**,
default `Budget.tool_calls` **60**) unchanged.
Do **not** claim live text_analyzer@12 PASS. Live NIM/OpenRouter success
is **not** a gate. Do **not** invent a Class A patch for 403/429. F-17
and F-26 stay closed. Do **not** invent remaining-quota. Do **not**
invent G4-8.

Live E1–E3 and Version 5 / G4-5 / G4-7 / G4-6 confirmation is
**deferred**, not a license to invent the next executor slice or a
package theme while gates stay paused. Class B rows are input to a
theme decision. They do not start the generation by themselves — a
theme must be **accepted**. Remaining 11B incompleteness without a
contract hole is evidence, not a missing Gen4 theme.

### Entry criteria (how Gen4 opens)

Gen4 **build** starts only when **all** of the following are true:

1. **Gen3 complete (scripted) on 0.4.0–0.4.9 — DONE** (Cycle 24).
   Themes 1–2 live-confirmed. Theme 3 slices A–E3 + F shipped. Live
   E1–E3 confirmation **deferred** until a provider recovers — that
   deferral is a **caveat**, not a missing Gen3 theme.
2. Sanath **accepts a first v0.5.0 theme** — not implied by a
   `needs_user` / FAIL / 429 / 403 row. **Done:** G4-1 (live
   multi-provider / free-provider production doctrine).
3. That theme is grounded in **measured Gen3-use gaps** (RW-084 /
   RW-085 / RW-086 and the residual Class B after E1–E3), not in a
   reconstructed offline story and not in a closed non-gate.
4. **Class A only when proven.** Class C (NIM 403, OpenRouter 429
   `free-models-per-day`) is **unblock the environment**, not a
   product patch.
5. Needle stays **OFF**. Caps unchanged unless a proven product need
   is documented.
6. Operating loop unchanged:
   `build → test → validate → release → use → discover gaps`.

Release gates must still be green (pytest, `rad doctor --offline`,
`rad acceptance`, `rad realworld`). `live_nim` may be BLOCKED.

### Code findings (lightweight; no patch)

What is already in tree vs the measured gap after **G4-6** (v0.5.5 /
RW-098 / RW-099). Named package-file / JSON-field *objective* contracts
are closed scripted. Cycle 24’s remaining *product* Class B list
(fallback PLAN, incomplete packages) is closed scripted. Per-objective
`Usage` now rolls up on `rad cost`. Do not invent a second control plane,
do not reopen F-17, do not invent MCP, and do not invent remaining-quota.

| already in tree | role | gap vs measured post-G4-5 residual |
|---|---|---|
| `rad/router.py` free-first chain | local → free round-robin → paid (unless free-lock); Class C skip + rotate preferred (v0.5.0) | **Closed for pause doctrine** (RW-089). Live pin + singleton key still cannot invent a second brain — honest pause |
| `rad/control/recovery.py` | HTTP 429 → `RATE_LIMIT` ask_user; HTTP 403 → AUTH ask_user; Class C before MODEL (v0.5.0) | **Closed for pause doctrine** (RW-089). Mid-run 429 no longer retries as TRANSIENT/MODEL |
| `Doctor.c_providers` | READY only for inference-entitled brains (v0.5.1 / RW-090); skip-blocked chat (v0.5.2 / RW-092) | **Closed for catalog vs chat and doctor re-ping.** Online scan defaults `skip_blocked_inference=True`. `--force` re-probes after a believed recovery |
| `rad/health.py` `evaluate_live_gate` | resume denies Class C until an entitled brain recovers | **Closed for resume** (RW-091). Live confirmation still deferred. Last working-inference row remains RW-086 on **v0.4.7** |
| `rad health` + CAMPAIGN_PLAYBOOK | pause / resume / wait / rotate / run next-action (v0.5.2 / RW-093) | **Closed for operator workflow.** Residual live campaign is **operator work** when an entitled brain recovers (honest FAIL / BLOCKED still valid) — not a new product theme while NIM/OpenRouter stay paused |
| `Planner.plan` retries + `_json_obj` | timeout / empty / malformed / non-JSON → recover near-JSON (fences, trailing commas, tasks array) or compact coding retry then `_fallback` (default 2 attempts) | **Closed for scripted G4-5** (RW-094 / RW-095). Live RW-085 / RW-086 still historically `source=fallback` attempts=2. Live confirmation deferred. F-17 fallback *tasks* stay check-less |
| `PLAN_PROMPT` + `PLAN_CODING_RETRY` | JSON tasks with checks; compact coding retry after a miss; named `file_exists` / `json_field` (v0.5.4) | Scripted near-JSON and compact retry keep a coding graph. Named-file / JSON-field contracts inferred (RW-096 / RW-097). Live 11B quality **not** claimed solved |
| `Planner._fallback` (F-17) + E2 empty `depends_on` | goal clause-split, cap 7, no checks on fallback *tasks* | Exhausted LLM still carves the goal. **Do not add checks to fallback tasks** (F-17 closed) |
| `infer_coding_checks` | objective-level `json_valid` / test `shell_ok` / exact `file_line_count` plus named-file `file_exists` and `json_field` for keys the goal names (cap 8); merge into omitted LLM plans | **Closed for scripted G4-7** (RW-096 / RW-097). Live RW-081 `{}` / RW-085/086 missing README + alt-schema remain historical Class B; live confirmation deferred. False DONE **0**. F-17 fallback *tasks* stay check-less |
| `codingloop` repair | broken `json_valid` / `json_field` / `shell_ok` insert one repair | **Closed for scripted G4-7** on named keys (empty `{}` fails `json_field`). Repair still cannot invent keys the goal never named. Live confirmation deferred |
| E1 / E2 / E3 (`TaskYield`, empty fallback `depends_on`, leftover retry stop) | scripted RW-083 / RW-087 / RW-088 | Live **not confirmed**. Not a missing executor slice — live confirmation waits on Class C recovery (G4-3 playbook) |
| `rad cost` / `RouterState.cost_report` + `ObjectiveStore.usage_rollup` | paid 14-day token spend **and** persisted per-objective `Usage` rollup (v0.5.5 / RW-098 / RW-099) | **Closed for scripted G4-6.** Free-tier quota remaining is not in the API until 429 — still not invented. G4-2 last Class C + Retry-After preserved |
| `rad connect` / skills / MCP gate; `rad provider add` | MCP + any OpenAI-compatible endpoint already first-class | No measured production row says MCP or custom-provider *absence* is the hole. Acceptance already handshakes MCP (**G4-4 parked**) |

### Candidate themes (evidence-backed)

Grounded in RW-084 / RW-085 / RW-086, scripted RW-089 / RW-090 / RW-091,
and the residual Class B after E1–E3. Do **not** treat a FAIL row as an
automatic architecture rewrite. Do **not** invent fantasy integrations.
Do **not** invent a Class A patch for 403/429.

Cycle 24 listed fallback/LLM plan quality as **G4-2**. After G4-1
shipped, that residual Class B was **not** the production-scale next
step. Cycle 26 reassigned **G4-2** to live-gate resume / health
(now **shipped** as v0.5.1). Fallback plan quality stayed **G4-5**.

Cycle 26 listed **G4-3** as “operational scale: longer workloads,
cost/budget reporting.” After G4-2 shipped, that grab-bag split:
longer-horizon *use* took **G4-3** (now **shipped** as v0.5.2);
cost/budget reporting parked as **G4-6**. Do **not** raise caps as
“scale” (A1 / F-21; RW-059 12→24 still exhausted).

**Version 5 pack** (GitHub Release **v0.5.2**) closed the production-scale
operational stack (pause / resume / operator-use path). **G4-5** closed
the residual Class B PLAN `source=fallback` hole as **v0.5.3** (scripted
RW-094 / RW-095; not in the pack release). **G4-7** closed the residual
Class B incomplete-package contract hole as **v0.5.4** (scripted RW-096 /
RW-097; merge-only). After G4-7, Cycle 24’s remaining *product* Class B
list is closed scripted. Live confirmation of the Version 5 / G4-5 /
G4-7 path remains **operator campaign** work when a provider recovers
(G4-3 playbook) — not a new package theme while NIM / OpenRouter free
stay paused. Residual “11B quality / free-model thrash” without a
contract hole is evidence, not a theme (thrash Class A patched or
F-44 **NOT CONFIRMED**; 429 is Class C). G4-4 (MCP) still has no
measured hole and is **parked**. Do **not** invent G4-8. Occupying a
new id would bury the closeout: Cycle 24’s remaining *product* Class B
list and the Production Scale leftover (spend visibility) are closed
scripted.

Cycles 30–32 deferred **G4-6** as “wait for Version 5 live-use data.”
That was a **priority deferral** while measured Class B product holes
were higher leverage — not a missing API. Those holes are now closed
scripted. Per-objective `Usage` records already exist from scripted /
offline runs. That was enough to **build** the rollup. Do **not** invent
remaining-quota. Do **not** stall Gen4 on Class C. **G4-6** is now
**accepted and implemented** as **v0.5.5** (scripted RW-098 / RW-099).
Investigate-first after G4-6: there is **no** remaining measured
product hole that is a Gen4 theme. **Gen4 closeout / Gen5 entry**
shipped (Cycle 36 / PR #50). **Version 5 pack** updated as GitHub
Release **Version 5** / tag **v0.5.5** (0.5.0–0.5.5). First Gen5 theme
**G5-1** is **accepted and implemented as v1.0.0**. **No GitHub Release
/ tag** in that change.

| id | theme | live providers? | status |
|---|---|---|---|
| **G4-1** | Live multi-provider / free-provider production doctrine | Scripted 403/429 is enough for the doctrine; live confirmation needs a recovered path | **ACCEPTED + IMPLEMENTED** as **v0.5.0** (scripted RW-089); **Version 5 pack** |
| **G4-2** | Live-gate resume / provider health observability | Scripted catalog-vs-inference + last-Class-C surface is enough to scope/build; live confirmation still deferred | **ACCEPTED + IMPLEMENTED** as **v0.5.1** (scripted RW-090 / RW-091); **Version 5 pack** |
| **G4-3** | Live-use campaign / operator workflow | Live E1–E3 confirmation needs an entitled brain; doctor skip-blocked / campaign playbook is scripted | **ACCEPTED + IMPLEMENTED** as **v0.5.2** (scripted RW-092 / RW-093); **Version 5 pack** |
| **G4-4** | Extensibility / integrations (MCP, custom providers) | No — already partially in tree | **parked** (no measured hole; not a missing Gen4 theme) |
| **G4-5** | Fallback / LLM plan quality under tight budgets | Scripted possible; live confirmation needs a recovered brain | **ACCEPTED + IMPLEMENTED** as **v0.5.3** (scripted RW-094 / RW-095); Version 5 pack merge-only |
| **G4-6** | Operational scale: cost/budget reporting | Reporting can be scripted from existing `Objective.usage` records; free-quota *remaining* is not in the API until 429 | **ACCEPTED + IMPLEMENTED** as **v0.5.5** (scripted RW-098 / RW-099); Version 5 pack merge-only |
| **G4-7** | Coding artifact completeness / named package-file contracts | Scripted possible; live confirmation needs a recovered brain | **ACCEPTED + IMPLEMENTED** as **v0.5.4** (scripted RW-096 / RW-097); Version 5 pack merge-only |

#### G4-1 — ACCEPTED + IMPLEMENTED (live multi-provider / free-provider production doctrine)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v0.5.0** (PR #39; scripted RW-089) |
| Theme | **Live multi-provider / free-provider production doctrine** |
| Version | **v0.5.0** |
| Loop | 401/403/429 / inference-forbidden → **Class C** (`AUTH_FAILURE` / `RATE_LIMIT`) → router rotates to the next usable **free** brain → if none remain, **ask_user / pause** with rotate-key / wait-quota / `rad use` text. `free_lock` never silently spends paid. No Class A repair/replan for 403/429 |
| Evidence | RW-084 / F-20260919-46 (NIM HTTP 403; 3 MODEL_FAILURE retries); live RW-086 / F-20260919-49 (OpenRouter HTTP 429 burned tools); scripted **RW-089** / F-20260919-52 |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live text_analyzer@12 now PASS. Not treating existing router failover as missing. Not inventing a Class A patch for 403/429. Not a license to pin paid spend under free-lock |

**Problem (unchanged driver):** Production free-first use is **paused**. NIM
chat/completions **403** (RW-084 Class C; `/v1/models` 200). OpenRouter free
**429** `free-models-per-day` (RW-086 Class C rate, after working inference).
Live text_analyzer@12 never recovered a second free brain inside the run.
Class C was being retried as MODEL/TRANSIENT product work.

**What shipped:** `class_c_kind` / `class_c_next_steps` on `ProviderError`;
recovery classifies Class C **before** MODEL so “all providers failed:
nvidia: HTTP 403” is `ask_user`, not retry/replan; HTTP 429 is `RATE_LIMIT`
not TRANSIENT; router skips recently Class-C-failed brains and rotates
preferred free; exhausted Class C raises an actionable pause; doctor
surfaces the doctrine; `free_lock` still drops paid.

#### G4-2 — ACCEPTED + IMPLEMENTED (live-gate resume / provider health observability)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v0.5.1** (scripted RW-090 / RW-091) |
| Theme | **Live-gate resume / provider health observability** |
| Version | **v0.5.1** |
| Problem | G4-1 closed the **pause**. Production still has no **safe live-use path**. RW-084: `rad doctor` providers **READY** (`1 usable: nvidia`) while `GET /v1/models` **200** and every `chat/completions` **403**. RW-086: working inference then late **429** `free-models-per-day` with no retry-after / last-Class-C surface — operator folklore paused the loop. `RouterState.failures` is in-process only. `rad objective resume` reopens NEEDS_USER and will re-hit the same 403 if the operator guesses. Live E1–E3 confirmation stays **deferred** until a provider is known inference-entitled, not merely catalog-alive |
| Entry | G4-1 shipped (v0.5.0 / RW-089) — **DONE**. Sanath accepts G4-2 as v0.5.1. Grounded in RW-084 (catalog ≠ chat; doctor READY) / RW-086 (working then 429) / Cycle 25 remaining #3, not in a new catalog. Class C stays Class C. Scripted catalog-vs-inference + last-Class-C / resume-safe surface is enough to **build**; live NIM/OpenRouter success is **not** required |
| Non-goals | Inventing a product Class A for 403/429. Auto-retry until chat works. Spending paid under `free_lock`. Treating `/v1/models` **200** as inference entitlement. Raising caps. Needle on. Claiming live text_analyzer@12 PASS. Full paid+free cost/budget rollup (that remains G4-6). Fallback plan quality (that is G4-5). A new telemetry stack / SQLite. A control-plane rewrite |
| Needs live providers | **No** for the scripted gate (same pattern as RW-089). Live confirmation of E1–E3 still waits on a recovered inference-entitled brain — G4-2 is the *safe path to try*, not a live PASS claim |
| What it is not | Not Gen3 theme 4. Not “wait forever.” Not runbook-copy polish of G4-1 `class_c_next_steps`. Not a license to pin paid spend under free-lock. Not a second router |

**Why this one next (investigated alternatives):**

| alternative | why not G4-2 |
|---|---|
| Operational runbooks / `needs_user` UX polish | G4-1 already shipped pause text (`class_c_next_steps`, OPERATIONS, TROUBLESHOOTING, doctor doctrine). Residual is copy, not a measured hole. The measured hole is doctor **READY** on a 403-chat provider (RW-084) |
| Larger workload / longer-horizon (then G4-3) | E1–E3 are scripted, not live. Caps 16/60 stay closed (A1 / F-21). Longer-horizon *use* waits on a recovered provider — which was the G4-2 hole; after G4-2 that *use* is G4-3 |
| Extensibility / MCP (G4-4) | No measured production row. Already first-class in tree |
| Fallback / LLM plan quality (now G4-5) | Residual Class B (RW-085 / RW-086 `source=fallback`). Cycle 24 already called this **not** the production-scale gate. Live confirmation needs the recovered brain G4-2 is meant to surface safely. F-17 stays closed |

**Acceptance gates (when accepted — not this change):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Scripted health | catalog-alive (`/v1/models` 200) **≠** inference-entitled (`chat/completions` 403) — RW-084 shape; doctor must **not** READY that provider as a live brain |
| Scripted resume surface | last Class C kind / status / next-steps survive process exit; `rad objective resume` does not silently re-burn the same 403 as MODEL |
| Scripted 429 | rate-limit / `free-models-per-day` visible without a tool-burning retry (RW-086 shape) |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; `free_lock` never silent paid; no Class A invented for 403/429; no live PASS claim |

#### G4-3 — ACCEPTED + IMPLEMENTED (live-use campaign / operator workflow)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v0.5.2** (scripted RW-092 / RW-093). **Version 5 pack** shipped as GitHub Release **v0.5.2** |
| Theme | **Live-use campaign / operator workflow** |
| Version | **v0.5.2** |
| Problem | G4-1 closed **pause**. G4-2 closed the **safe resume / health** path. Production still has not **used** that path. Last working-inference live row is **RW-086** on tag `v0.4.7` (then 429). E1–E3 remain scripted only (RW-083 / RW-087 / RW-088). G4-1 / G4-2 themselves are scripted (RW-089 / RW-090 / RW-091) — never live-confirmed together. The operating loop’s next step is **use**, not another executor slice and not a cost dashboard. Leftover operator-workflow hole vs G4-2: `rad doctor` (online) called `scan_provider_health` **without** `skip_blocked_inference`, so a health probe re-hit chat while last Class C still blocked — resume already skipped that re-burn (RW-091). On OpenRouter that ping would count against `free-models-per-day` (RW-086) |
| Entry | G4-1 shipped (v0.5.0 / RW-089) — **DONE**. G4-2 shipped (v0.5.1 / RW-090 / RW-091) — **DONE**. Sanath accepts G4-3 as v0.5.2. Grounded in deferred live E1–E3 (RW-084 Class C; RW-085/086 fallback chain, 0 TaskYield) and the doctor re-ping vs resume skip (`rad/health.py` / `rad/doctor.py`), not in a new catalog. An inference-entitled brain is required for the *live campaign*; the doctor skip-blocked slice is **scripted** without it (RW-092 / RW-093). Class C stays Class C. Live NIM/OpenRouter **PASS** is **not** required to ship; honest FAIL / BLOCKED is a valid campaign result |
| Non-goals | Inventing a product Class A for 403/429. Auto-retry until chat works. Spending paid under `free_lock`. Raising caps (`max_plan_tasks` **16**, default `Budget.tool_calls` **60**). Needle on. Claiming live text_analyzer@12 PASS as a gate. A new executor slice (E4) without live evidence. Reopening F-17 / fallback plan quality (that is G4-5). MCP marketplace (that is G4-4). Full paid+free cost/budget rollup (that is G4-6). A new telemetry stack / SQLite. A control-plane rewrite. Treating `/v1/models` **200** as inference entitlement. A GitHub Release / tag for this sub-version |
| Needs live providers | **Yes** for E1–E3 live confirmation. **No** for the scripted doctor skip-blocked / campaign-playbook gate |
| What it is not | Not Gen3 theme 4. Not “wait forever.” Not runbook-copy polish of G4-2 TROUBLESHOOTING. Not “raise max-tools to 24 and call it scale.” Not a second health probe that re-burns 429 |

**Why this one (investigated alternatives):**

| alternative | why not G4-3 |
|---|---|
| Larger workload / longer-horizon *product* (Cycle 26 G4-3) | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Longer-horizon *use* **is** this campaign, not a new executor |
| Extensibility / MCP (G4-4) | No measured production row. Already first-class in tree |
| Fallback / LLM plan quality (G4-5) | Residual Class B (RW-085 / RW-086 `source=fallback`). Cycle 24 / 26 already called this **not** the production-scale gate. Live confirmation needs the recovered brain this campaign is meant to use. F-17 stays closed |
| Cost/budget reporting (now G4-6) | `rad cost` is paid-only; G4-2 already surfaces last Class C + Retry-After. A dashboard without a use campaign is inventing telemetry. Wait for use data |
| Operational runbooks / `needs_user` UX polish | G4-2 already shipped TROUBLESHOOTING / OPERATIONS resume text. Residual copy is not a measured hole. The leftover is doctor re-ping vs resume skip, plus the unused live path |

**Acceptance gates (this change):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Scripted operator loop | last Class C still blocking → `rad doctor` / health scan does **not** re-burn chat (RW-086 quota shape); resume skip preserved (RW-091); `free_lock` never silent paid |
| Live campaign (when an entitled brain exists) | one bounded objective recorded as an RW row; E1–E3 live **Y / N / BLOCKED** recorded honestly; G4-1 pause + G4-2 resume used if Class C hits mid-run. **Not required to ship this slice** |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; Class C is not a product patch; no live PASS claim unless disk checks actually pass |

**What shipped:** skip-blocked doctor / `rad health`; campaign playbook; controller persist keeps key / Retry-After.

#### G4-4 — Extensibility / integrations (MCP, custom providers) — PARKED

| field | value |
|---|---|
| Status | **PARKED.** Already partially in tree. Still **not** a next theme after G4-6 |
| Problem | None measured. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. `rad provider add` accepts any OpenAI-compatible endpoint. README backlog “remote-MCP hardening” is an **idea**, not an evidence row |
| Entry | A named production row that MCP/custom-provider *absence or drift* blocked a real objective. Until then: do not invent. If such a row appears later, it can be Class A on 0.5.x (if proven RAD defect) or a Gen5 theme (if accepted as 1.0 capability) — not a forced G4-8 |
| Non-goals | Fantasy connector marketplace. Enabling Needle. Per-agent OS sandboxes (already documented as not done on AGENTS.md — not a Gen4 start). Force-building MCP because the id exists |
| Needs live providers | No |
| What it is not | Not Production Scale just because MCP exists in the tree. Not a missing Gen4 theme. Not a Gen5 start |

#### G4-5 — ACCEPTED + IMPLEMENTED (fallback / LLM plan quality under tight budgets)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v0.5.3** (scripted RW-094 / RW-095). Cycle 24 id was **G4-2** — kept as **G4-5** so production-scale slices could occupy G4-2 / G4-3. Version 5 pack shipped; this slice merge-only |
| Theme | **Fallback / LLM plan quality under tight budgets** |
| Version | **v0.5.3** |
| Loop | near-JSON LLM plan (fences / trailing commas / tasks array / extra braces) → recover as `source=llm` with checks; coding-goal miss → compact `PLAN_CODING_RETRY`; exhausted → `_fallback(obj)` goal-only, cap 7, no checks (F-17) |
| Evidence | live RW-085 / RW-086 (`source=fallback` attempts=2; 4 clause-carved tasks); scripted **RW-094** / **RW-095** / F-20260919-55 |
| Problem | After E1–E3 and the Version 5 operational pack, live coding still died on a weak plan. RW-085 / RW-086: PLAN `source=fallback` attempts=2, clause-split from the goal, not a real coding graph. Residual Class B: incomplete package, odd summary, missing README/tests. F-17 is **closed** (do not add checks to fallback *tasks*) |
| Entry | Version 5 pack shipped (G4-1 / G4-2 / G4-3 @ **0.5.2**) — **DONE**. Sanath accepts G4-5 as v0.5.3. Grounded in RW-085 / RW-086 fallback and the invariant that must not move (F-17; false DONE 0; caps 16/60; Needle OFF). Investigate-first: LLM-plan success vs fallback *structure* for coding goals — not “add checks to `_fallback` tasks”. Scripted possible without a recovered brain. Live confirmation prefers a recovered brain (G4-3 playbook) but is **not** required to ship. Class C stays Class C |
| Non-goals | Reopening F-17 / F-21 / F-26. Adding checks to fallback *tasks*. Rubber-stamp VERIFIED. Cap raise as the primary fix. Claiming 11B quality is solved. Remapping `write_file` / `echo >` (F-44). Inventing a product Class A for 403/429. MCP marketplace (that is G4-4). Full paid+free cost/budget rollup (that is G4-6). A new executor slice (E4). A new telemetry stack / SQLite. A control-plane rewrite. Needle on. A GitHub Release / tag for this sub-version |
| Needs live providers | **No** for the scripted gate. Live confirmation needs a recovered brain and is **not** a live PASS claim |
| What it is not | Not a Gen3 leftover theme number. Not an automatic accept because fallback appeared twice. Not “wait forever” for Class C. Not live confirmation of Version 5 as a product theme |

**Why this one (investigated alternatives):**

| alternative | why not G4-5 |
|---|---|
| Extensibility / MCP (G4-4) | No measured production row. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. README “remote-MCP hardening” is an idea, not an evidence row |
| Cost/budget reporting (G4-6) | `rad cost` is paid-only; G4-2 already surfaces last Class C + Retry-After. Free remaining-quota is not in the API until 429. Version 5 live-use data still does not exist. A dashboard without that data is inventing telemetry |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Not a missing executor |
| Live confirmation of Version 5 path (campaign execution) | G4-3 already shipped the playbook (`rad health --campaign`). NIM / OpenRouter free remain **paused**. Running that campaign is operator work when a provider recovers, recorded as an RW row — not a package bump. Honest FAIL / BLOCKED remains valid. Do not stall Gen4 on Class C |
| Operational runbooks / `needs_user` UX polish | G4-1 / G4-2 / G4-3 already shipped pause / resume / skip-blocked doctor / `rad health`. Residual copy is not a measured hole |

**Acceptance gates (this change):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Scripted plan quality | coding-goal near-JSON / compact retry → `source=llm` coding graph (RW-094 / RW-095); exhausted still `_fallback` check-less / cap 7 / goal-only (F-17); false DONE **0** |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; Class C is not a product patch; no live PASS claim; **no per-slice GitHub Release** (Version 5 packing doctrine) |

**What shipped:** `_json_obj` recovers fenced JSON, trailing commas, a top-level tasks array, and the first balanced object; coding-goal retries use `PLAN_CODING_RETRY`; `_fallback` unchanged (F-17).

#### G4-6 — ACCEPTED + IMPLEMENTED (operational scale: cost/budget reporting)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v0.5.5** (scripted RW-098 / RW-099). Cycle 26 id was **G4-3** (reporting half of a grab-bag with longer workloads) — kept as **G4-6** so live-use could occupy G4-3. Cycles 30–32 deferred this as “wait for Version 5 live-use data” while G4-5 / G4-7 product holes were higher leverage. Those holes are closed scripted. Version 5 pack shipped; this slice merge-only |
| Theme | **Operational scale: cost/budget reporting** |
| Version | **v0.5.5** |
| Problem | After G4-7 closed named-file / JSON-field *objective* contracts, Cycle 24’s remaining *product* Class B list is closed scripted. Production Scale leftover is spend visibility. `rad cost` / `RouterState.cost_report` reports **paid 14-day token spend** only (“no paid usage recorded (you're on free/local)”). Per-objective `Usage` (`tool_calls` / `model_calls` / `money_usd` / `tokens`) already persists on `~/.rad/objectives/<id>/objective.json` (Cycle 24 / `rad/control/objectives.py`). `rad inspect` and the run banner print **one** objective. There is no production rollup across objectives. Free-tier *remaining* quota is not in the API until HTTP 429 (RW-086) — do **not** invent a counter. G4-2 already persists last Class C + Retry-After — do **not** re-do. Default caps 16/60 are **not** raised (A1 / F-21 stay closed). RW-086 recorded `$0` + tools **12/12** with no spend rollup beyond the one-run banner |
| Entry | G4-7 shipped (v0.5.4 / RW-096 / RW-097) — **DONE**. Sanath accepts G4-6 as v0.5.5. Grounded in Cycle 24 `rad cost` paid-only gap, RW-086 (`$0` / tools 12/12 / late 429 with no remaining-quota API), and existing per-objective `Usage` that is not rolled up. Scripted/offline objectives already write those records (acceptance, realworld, unit) — enough to **build** a rollup without Version 5 *live* inference. Investigate-first: roll up records that exist — not “invent remaining-quota”, not “raise caps”, not a new telemetry stack. Live confirmation prefers a recovered brain (G4-3 playbook) but is **not** required to ship. Class C stays Class C |
| Non-goals | Reopening F-17 / F-21 / F-26. Adding checks to fallback *tasks*. Rubber-stamp VERIFIED. Cap raise as the theme. Inventing a remaining-quota counter the provider does not expose. Claiming 11B quality is solved. Remapping `write_file` / `echo >` (F-44). Inventing a product Class A for 403/429. MCP marketplace (that is G4-4). A new executor slice (E4). A new telemetry stack / SQLite. A control-plane rewrite. Needle on. Re-doing G4-2 catalog-vs-inference / last Class C. Re-doing G4-3 live-use playbook. A GitHub Release / tag for this sub-version |
| Needs live providers | **No** for the scripted gate. Interpreting free-quota *remaining* needs a provider that exposes it — out of scope. Live confirmation of Version 5 / G4-5 / G4-7 is **not** this theme |
| What it is not | Not “raise max-tools to 24 and call it scale.” RW-059 already showed 12→24 still exhausted. Not a Gen3 leftover theme number. Not “wait forever” for Class C. Not live confirmation of Version 5 as a product theme. Not inventing telemetry from a reconstructed story — the records already exist |

**Why this one next (investigated alternatives):**

| alternative | why not G4-6 |
|---|---|
| Extensibility / MCP (G4-4) | No measured production row. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. README “remote-MCP hardening” is an idea, not an evidence row. **Id kept** |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Not a missing executor |
| Live confirmation of Version 5 / G4-5 / G4-7 path (campaign execution) | G4-3 already shipped the playbook (`rad health --campaign`). NIM / OpenRouter free remain **paused**. Running that campaign is operator work when a provider recovers, recorded as an RW row — not a package bump. Honest FAIL / BLOCKED remains valid. Do not stall Gen4 on Class C |
| Residual Class B after G4-5 + G4-7 (plan quality + artifact contracts) | G4-5 closed plan-*structure* (RW-094 / RW-095). G4-7 closed named-file / JSON-field *objective* contracts (RW-096 / RW-097). Remaining 11B incompleteness without a contract hole is evidence, not a theme. Do not invent G4-8 to re-open F-17 or “make 11B pass” |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A paths are patched or F-44 **NOT CONFIRMED**. 429 is Class C. Not a theme |
| Operational runbooks / `needs_user` UX polish | G4-1 / G4-2 / G4-3 already shipped pause / resume / skip-blocked doctor / `rad health`. Residual copy is not a measured hole |

**Acceptance gates (this change):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Scripted spend rollup | per-objective `Usage` (tools / model / paid) already on disk is visible as a production rollup — not paid-14-day-only `rad cost`; free remaining-quota is **not** invented; G4-2 last Class C / Retry-After preserved; false DONE **0** |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; Class C is not a product patch; no live PASS claim; **no per-slice GitHub Release** (Version 5 packing doctrine) |

**What shipped:** `ObjectiveStore.usage_rollup` sums persisted `Usage` (`tool_calls` / `model_calls` / `money_usd` / `tokens`) across `~/.rad/objectives/<id>/objective.json`. `rad cost` prints that rollup under the existing paid 14-day section. Remaining-quota is **not** invented. G4-2 last Class C + Retry-After is untouched.

#### G4-7 — ACCEPTED + IMPLEMENTED (coding artifact completeness / named package-file contracts)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v0.5.4** (scripted RW-096 / RW-097). New id — G4-4 / G4-6 kept. Version 5 pack shipped; this slice merge-only |
| Theme | **Coding artifact completeness / named package-file contracts** |
| Version | **v0.5.4** |
| Problem | After G4-5 closed plan-*structure*, live coding still died with an incomplete package. Cycle 24 residual Class B list after fallback PLAN: **incomplete package artifacts**. RW-081 (LLM plan): `summary.json` `{}`; SyntaxError `test_analyzer.py`; analyzer starved. RW-085 / RW-086 (fallback): missing README / tests; alt-schema `summary.json`. `infer_coding_checks` (v0.4.1) added `json_valid` / test `shell_ok` / `file_line_count` only — named README.md / analyzer.py got no `file_exists`; named summary keys got no `json_field` (kind already existed). Empty `{}` is valid JSON, so `json_valid` did not catch odd schema. False DONE **0** (honesty holds). F-17 is **closed** (do not add checks to fallback *tasks*) |
| Entry | G4-5 shipped (v0.5.3 / RW-094 / RW-095) — **DONE**. Sanath accepts G4-7 as v0.5.4. Grounded in RW-081 / RW-085 / RW-086 incomplete package (empty / alt-schema summary; missing README/tests) and the invariant that must not move (F-17; F-26 check *kinds* not remapped; false DONE 0; caps 16/60; Needle OFF). Investigate-first: omitted *objective* contracts for named package files / JSON fields — not “add checks to `_fallback` tasks”, not “11B quality is solved”, not a cap raise. Scripted possible without a recovered brain (same pattern as v0.4.1 / G4-5). Live confirmation prefers a recovered brain (G4-3 playbook) but is **not** required to ship. Class C stays Class C |
| Non-goals | Reopening F-17 / F-21 / F-26. Adding checks to fallback *tasks*. Rubber-stamp VERIFIED. Cap raise as the primary fix. Claiming 11B quality is solved. Remapping `write_file` / `echo >` (F-44). Inventing a product Class A for 403/429. MCP marketplace (that is G4-4). Full paid+free cost/budget rollup (that is G4-6). A new executor slice (E4). A new telemetry stack / SQLite. A control-plane rewrite. Needle on. A GitHub Release / tag for this sub-version |
| Needs live providers | **No** for the scripted gate. Live confirmation needs a recovered brain and is **not** a live PASS claim |
| What it is not | Not a Gen3 leftover theme number. Not an automatic accept because a package was incomplete. Not “wait forever” for Class C. Not live confirmation of Version 5 / G4-5 as a product theme. Not a re-open of A1 |

**Why this one next (investigated alternatives):**

| alternative | why not G4-7 |
|---|---|
| Extensibility / MCP (G4-4) | No measured production row. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. README “remote-MCP hardening” is an idea, not an evidence row. **Id kept** |
| Cost/budget reporting (G4-6) | `rad cost` is paid-only; G4-2 already surfaces last Class C + Retry-After. Free remaining-quota is not in the API until 429. Version 5 live-use data still does not exist (last working inference: RW-086 on **v0.4.7**). A dashboard without that data is inventing telemetry. **Id kept** — do not occupy G4-6 with artifact work |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Not a missing executor |
| Live confirmation of Version 5 / G4-5 path (campaign execution) | G4-3 already shipped the playbook (`rad health --campaign`). NIM / OpenRouter free remain **paused**. Running that campaign is operator work when a provider recovers, recorded as an RW row — not a package bump. Honest FAIL / BLOCKED remains valid. Do not stall Gen4 on Class C |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A paths are patched or F-44 **NOT CONFIRMED**. Remaining 11B incompleteness without a contract hole is evidence, not a theme. G4-7 is the *contract* slice (named files / JSON fields), not “make 11B pass” |
| Operational runbooks / `needs_user` UX polish | G4-1 / G4-2 / G4-3 already shipped pause / resume / skip-blocked doctor / `rad health`. Residual copy is not a measured hole |

**Acceptance gates:**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Scripted artifact contracts | coding-goal named package files / JSON fields that `infer_coding_checks` previously omitted are *objective* contracts (RW-096 / RW-097); F-17 check-less / cap 7 / goal-only split preserved; F-26 check *kinds* not remapped; false DONE **0** |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; Class C is not a product patch; no live PASS claim; **no per-slice GitHub Release** (Version 5 packing doctrine) |

**What shipped:** `infer_coding_checks` adds `file_exists` for named README.md / main-module `.py` and `json_field` for keys the goal names (parenthetical after `.json`, `key X`, `keys: a, b`). Empty `{}` and alt-schema summaries fail when keys are named. Fallback *tasks* stay check-less (F-17). Infer cap 6→8 / merge cap 8→10 so the new contracts fit. PLAN_PROMPT / PLAN_CODING_RETRY ask for the same contracts.

### First v0.5.0 — G4-1 (accepted + implemented)

**G4-1** (live multi-provider / free-provider production doctrine) is the
first Gen4 slice. It is **accepted and implemented as v0.5.0**.

Why this one first: Gen4 is Production Scale. Both live free paths are
**paused** (RW-084 Class C; RW-086 Class C rate). E1–E3 cannot be
live-confirmed, and Class C keeps getting re-read as product work, until
there is a doctrine for recover / rotate / pause. Scripted RW-089 is the
unit evidence. Live NIM/OpenRouter success is **not** required for this
gate. Do **not** claim live text_analyzer@12 PASS.

### v0.5.1 — G4-2 (accepted + implemented)

**G4-2** (live-gate resume / provider health observability) is
**accepted and implemented as v0.5.1**.

Why this one: G4-1 closed **pause**. Production still could not
**safely resume**. RW-084 proved catalog-alive ≠ inference-entitled and
doctor **READY** on a 403-chat pin. RW-086 proved a working free path
can die mid-run on 429 with no durable last-Class-C / retry-after
surface. Scripted RW-090 / RW-091 is the unit evidence. Live
NIM/OpenRouter success is **not** required. Do **not** claim live
text_analyzer@12 PASS.

**What shipped:** `rad/health.py` catalog vs inference probe;
`~/.rad/provider_health.json` last Class C (kind / status / next-steps /
Retry-After); doctor READY only for inference-entitled brains;
`rad objective resume` live-gate refuses to re-burn the same 403/429
until an entitled brain recovers; `free_lock` still drops paid.

### v0.5.2 — G4-3 (accepted + implemented)

**G4-3** (live-use campaign / operator workflow) is **accepted and
implemented as v0.5.2**. **Version 5 pack** shipped as GitHub Release
**v0.5.2** (title **Version 5**; tip
`d534bd30384e9f582ca6c08562a6b2cd555fb793`; covers G4-1 / G4-2 / G4-3).

Why this one: G4-1 closed **pause**. G4-2 closed **safe resume**. The
operating loop’s next step is **use**. E1–E3 and G4-1/G4-2 have never
been live-confirmed together. The leftover product hole was quota-safe
operator workflow (doctor re-ping vs resume skip). Scripted RW-092 /
RW-093 is the unit evidence. Live NIM/OpenRouter success is **not**
required. Do **not** claim live text_analyzer@12 PASS.

**What shipped:** online `rad doctor` / health scan skip chat while last
Class C still blocks (unknown `key_fp` included; `--force` to re-probe);
`rad health` pause / resume / wait / rotate / run surface; campaign
playbook for when NIM or OpenRouter free recovers; controller persist
keeps key / Retry-After; `free_lock` still drops paid.

Live E1–E3 confirmation still waits on a recovered brain (operator
campaign via the G4-3 playbook — not a new product theme while gates
stay paused).

### v0.5.3 — G4-5 (accepted + implemented)

**G4-5** (fallback / LLM plan quality under tight budgets) is
**accepted and implemented as v0.5.3**. **No GitHub Release / tag** —
Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

Why this one: **Version 5 pack** closed pause / resume / operator-use
path as **v0.5.0–v0.5.2**. The remaining measured gap on a working product
path was Class B PLAN `source=fallback` (RW-085 / RW-086). Cycle 24
originally listed this first among residual Class B; Cycles 26–28
deferred it so production-scale Class C doctrine could ship. That pack
is done. Scripted RW-094 / RW-095 is the unit evidence. Live
NIM/OpenRouter success is **not** required. Do **not** invent Class A
for 403/429. Do **not** claim live text_analyzer@12 PASS. F-17 stays
closed.

**What shipped:** `_json_obj` recovers near-JSON (fences, trailing commas,
tasks array, first balanced object); coding-goal retries use a compact
JSON skeleton (`PLAN_CODING_RETRY`); exhausted retries still
`_fallback(obj)` with no checks on fallback *tasks*.

**Version 5 packing doctrine (as shipped):** this slice **merged only**.
Sanath later packed G4-1–G4-6 as GitHub Release **Version 5** / tag
**v0.5.5** (0.5.0–0.5.5). Tag **v0.5.2** remains the earlier G4-1–G4-3
pack.

### v0.5.4 — G4-7 (accepted + implemented)

**G4-7** (coding artifact completeness / named package-file contracts)
is **accepted and implemented as v0.5.4**. **No GitHub Release / tag** —
Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

Why this one: **G4-5** closed plan-*structure* as **v0.5.3**. Cycle 24’s
remaining measured Class B on a working product path was incomplete
package artifacts (RW-081 empty / odd summary + starved later files;
RW-085 / RW-086 missing README/tests + alt-schema summary).
`infer_coding_checks` already contracted JSON-parse / tests / line-count
— not named README / module files, not `json_field` for required keys.
Scripted RW-096 / RW-097 is the unit evidence. Live NIM/OpenRouter
success is **not** required. Do **not** invent Class A for 403/429. Do
**not** claim live text_analyzer@12 PASS. F-17 stays closed.

**What shipped:** named package files (README.md, analyzer.py / main
module) become `file_exists` *objective* contracts; named JSON keys
become `json_field` so empty `{}` / alt-schema is not VERIFIED; fallback
*tasks* stay check-less.

**Version 5 packing doctrine (as shipped):** this slice **merged only**.
Sanath later packed G4-1–G4-6 as GitHub Release **Version 5** / tag
**v0.5.5** (0.5.0–0.5.5). Tag **v0.5.2** remains the earlier G4-1–G4-3
pack.

### v0.5.5 — G4-6 (accepted + implemented)

**G4-6** (operational scale: cost/budget reporting) is
**accepted and implemented as v0.5.5**. **No GitHub Release / tag** —
Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

Why this one: **G4-7** closed named-file / JSON-field *objective*
contracts as **v0.5.4**. Cycle 24’s remaining *product* Class B list
(fallback PLAN, incomplete packages) is closed scripted. The remaining
measured Production Scale leftover was spend visibility: `rad cost` was
paid-14-day only; per-objective `Usage` already persisted and was not
rolled up. Cycles 30–32 deferred this so G4-5 / G4-7 could ship. Those
are done. Scripted/offline `Usage` records were enough to **build**; live
NIM/OpenRouter success is **not** required. Do **not** invent remaining-quota.
Do **not** invent Class A for 403/429. Do **not** claim live
text_analyzer@12 PASS. Do **not** raise caps. F-17 stays closed.

**What shipped:** `ObjectiveStore.usage_rollup` sums persisted
`tool_calls` / `model_calls` / `money_usd` / `tokens`; `rad cost`
prints that rollup under paid 14-day tokens. Remaining-quota is not
invented. G4-2 last Class C + Retry-After is untouched.

**Version 5 packing doctrine (as shipped):** this slice **merged only**.
Sanath later packed G4-1–G4-6 as GitHub Release **Version 5** / tag
**v0.5.5** (0.5.0–0.5.5). Tag **v0.5.2** remains the earlier G4-1–G4-3
pack.

### Gen4 closeout / Gen5 entry — SHIPPED (docs; stay 0.5.5)

| field | value |
|---|---|
| Status | **SHIPPED** as docs (Cycle 36 / PR #50). Gen4 is **complete (scripted)**. Not a product theme |
| Theme | **Gen4 closeout / Gen5 entry criteria** |
| Version | **none.** Stay **0.5.5**. Not **v0.5.6**. First Gen5 theme is **v1.0.0** only when accepted |
| Problem | After G4-6, Cycle 24’s remaining *product* Class B list (fallback PLAN, incomplete packages) and the Production Scale leftover (spend visibility) are **closed scripted**. G4-4 still has **no measured hole**. Live confirmation of Version 5 / G4-5 / G4-7 / G4-6 / E1–E3 is operator campaign work (G4-3 playbook) while NIM / OpenRouter free stay **paused**. Inventing G4-8, MCP, remaining-quota, a cap raise, or a live PASS claim would violate investigate-first |
| Entry | G4-6 shipped (v0.5.5 / RW-098 / RW-099) — **DONE**. Sanath records Gen4 complete (scripted) in this scope. Gen5 **build** still waits for a written accept of a first v1.0.0 theme (see Generation 5). Grounded in Cycle 24 remaining list closed scripted, G4-4 no hole (RW-089–099 + acceptance MCP handshake already in tree), and live confirmation deferred (RW-084 Class C; RW-085/086 FAIL; last working inference RW-086 on **v0.4.7**). Class C stays Class C |
| Non-goals | Inventing G4-8. Force-building MCP (G4-4). Reopening F-17 / F-21 / F-26. Adding checks to fallback *tasks*. Rubber-stamp VERIFIED. Cap raise as the theme (`max_plan_tasks` **16**, default `Budget.tool_calls` **60**). Inventing remaining-quota. Claiming 11B quality is solved. Remapping `write_file` / `echo >` (F-44). Inventing a product Class A for 403/429. A new executor slice (E4). A new telemetry stack / SQLite. A control-plane rewrite. Needle on. A GitHub Release / tag. A **v0.5.6** bump. Starting Gen5 from this scope PR. Treating `/v1/models` **200** as inference entitlement. Treating live confirmation as a package theme while gates stay paused |
| Needs live providers | **No** for this docs closeout. Live confirmation still needs a recovered brain and is **not** a live PASS claim |
| What it is not | Not a product slice. Not “wait forever” for Class C. Not a claim that Version 5 has been **used** live. Packing Version 5 as tag **v0.5.5** (0.5.0–0.5.5) happened after this closeout |

**Why this one next (investigated alternatives):**

| alternative | why not next |
|---|---|
| Extensibility / MCP (G4-4) | No measured production row. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. README “remote-MCP hardening” is an idea, not an evidence row. **Parked.** Do not force-build |
| Live confirmation of Version 5 / G4-5 / G4-7 / G4-6 path | G4-3 already shipped the playbook (`rad health --campaign`). NIM / OpenRouter free remain **paused**. Running that campaign is operator work when a provider recovers, recorded as an RW row — not a package bump. Honest FAIL / BLOCKED remains valid. Do not stall closeout on Class C |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Not a missing executor |
| Residual Class B after G4-5 / G4-6 / G4-7 | G4-5 closed plan-*structure* (RW-094 / RW-095). G4-7 closed named-file / JSON-field *objective* contracts (RW-096 / RW-097). G4-6 closed spend rollup (RW-098 / RW-099). Remaining 11B incompleteness without a contract hole is evidence, not a theme. Do not invent G4-8 to re-open F-17 or “make 11B pass” |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A paths are patched or F-44 **NOT CONFIRMED**. 429 is Class C. Not a theme |
| Operational runbooks / `needs_user` UX polish | G4-1 / G4-2 / G4-3 already shipped pause / resume / skip-blocked doctor / `rad health`. Residual copy is not a measured hole |
| A v0.5.6 docs-only package bump | No product change. Stay **0.5.5**. Version 5 is packed at tag **v0.5.5** |

**Acceptance gates (this change — docs):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; Class C is not a product patch; no live PASS claim; F-17 / F-26 stay closed; remaining-quota not invented; **no per-slice GitHub Release**; package stays **0.5.5** |

### Further 0.5.x work

Gen4 themes G4-1 / G4-2 / G4-3 / G4-5 / G4-7 / G4-6 are **complete
(scripted)**. G4-4 is **parked** (no measured hole). Further 0.5.x is
**Class A only when proven** on the current minor line. Remaining
measured gaps (paused Class C providers, E1–E3 and Version 5 / G4-5 /
G4-7 / G4-6 not live-confirmed together, historical 11B incompleteness
without a contract hole) are **Gen5 remaining gaps or operator campaign
work**, not a G4-8 and **not** a G5-2. Do not invent a long-horizon
redesign from Class B budget rows. Do not invent remaining-quota. Do not
invent Class A for 403/429. Further 0.5.x is Class A only when proven.
Gen5 **G5-1** is **accepted, implemented, and packed as v1.0.0**. Next
Gen5 step is **hold / soak** (see Generation 5).

---

## Generation 5 — 1.0 — IN PROGRESS (v1.0.0)

Stable public / product-grade baseline.

**Status:** **in progress — hold / soak.** Theme **G5-1** (public /
product-grade 1.0 baseline) is **accepted and implemented as v1.0.0**
(scripted RW-100 / RW-101). Package **1.0.0**. **Version 1 pack is
SHIPPED** as GitHub Release **Version 1** / tag **v1.0.0** @
`9ff184e0d071784bc8820a1258a3d40daf7f1193` (wheel + sdist; PR #52).
**No G5-2 product theme.** Live confirmation of Version 1 / Version 5
remains the loop’s **use** step and a remaining-gaps input, not a missing
control-plane hole. This docs PR stays **1.0.0**. **No GitHub Release /
tag in this PR.**

1.0 is a generation, not a marketing tag: it still requires the loop
(`build → test → validate → release → use → discover that the remaining
gaps are acceptable for a public baseline`).

### Entry criteria (how Gen5 opens)

Gen5 **build** starts only when **all** of the following are true:

1. **Gen4 complete (scripted) on 0.5.0–0.5.5 — DONE** (Cycle 36).
   **Version 5 pack** is GitHub Release **Version 5** / tag **v0.5.5**
   (covers **0.5.0–0.5.5** / G4-1–G4-3 + G4-5–G4-7 + G4-6). Tag
   **v0.5.2** remains the earlier G4-1–G4-3 pack. G4-4 **parked**. Live
   confirmation of Version 5 / G4-5 / G4-7 / G4-6 / E1–E3 **deferred**
   until a provider recovers — that deferral is a **caveat**, not a
   missing Gen4 theme and **not** a missing Gen5 product slice. Version 5
   **live use** has not happened (last working-inference row remains
   **RW-086** on **v0.4.7**).
2. Sanath **accepts a first v1.0.0 theme** — not implied by a
   `needs_user` / FAIL / 429 / 403 row, and not implied by the scope PR.
   **Done:** G5-1 (public / product-grade 1.0 baseline).
3. That theme is grounded in **measured Gen4-use gaps** after the
   Version 5 path has been used, **or** in an explicit decision that
   remaining gaps are acceptable for a public baseline. Scripted
   RW-089–099 are Gen4 *build* evidence, not live Gen4 *use*. Do not
   reconstruct a 1.0 theme from a closed non-gate. Prefer the G4-3
   campaign when a provider recovers; live **PASS** is **not** required
   to accept remaining gaps (honest FAIL / BLOCKED is valid use).
4. **Class A only when proven.** Class C (NIM 403, OpenRouter 429
   `free-models-per-day`) is **unblock the environment**, not a
   product patch. Further 0.5.x remains available for proven Class A
   on the current minor line.
5. Needle stays **OFF**. Caps unchanged unless a proven product need
   is documented.
6. Operating loop unchanged:
   `build → test → validate → release → use → discover gaps`.

Release gates must still be green (pytest, `rad doctor --offline`,
`rad acceptance`, `rad realworld`). `live_nim` may be BLOCKED.

### What Gen5 is not

- Not a v0.5.6. Not packing Version 5 again.
- Not force-building MCP (G4-4 parked).
- Not raising caps 16/60 as “1.0 scale.”
- Not a live text_analyzer@12 PASS claim.
- Not inventing remaining-quota or Class A for 403/429.
- Not reopening F-17 / F-26.
- Not stalling a *package theme* on Class C (live confirmation is operator
  work via the G4-3 playbook — remaining-gaps *input* / **hold / soak**,
  not G5-1 and **not** a G5-2).
- Not a **v1.0.1** without proven Class A. Not a **v1.1.0** without a
  written accept of a new theme after soak.

### Version 1 / 1.0 packing

Gen4 used **Version 5 packing**: merge-only sub-versions (`0.5.0`–
`0.5.5`) until Sanath asked to pack. That pack is now GitHub Release
**Version 5** / tag **v0.5.5** (0.5.0–0.5.5). Version 5 GitHub Releases
have **no installable assets**.

Gen5 / the 1.0 line is different because **v1.0.0 is the public
baseline**, not another production-scale series:

| rule | meaning |
|---|---|
| First theme **is** the pack | **DONE.** G5-1 shipped as package **1.0.0**. Sanath cut **one Version 1 / 1.0 pack** at tag **v1.0.0** after PR #52 merge, with wheel + sdist assets. Do not start a merge-only `1.0.1` / `1.0.2` / … series as a substitute for soak |
| G5-1 implementation PR (#52) | Package **1.0.0**. **No GitHub Release / tag in that PR.** Pack landed after merge |
| This 1.0.1 PR | Package **1.0.1**. **No GitHub Release / tag.** Do **not** upload secrets. Do **not** cut **v1.0.1** or **v1.1.0** GitHub Release |
| Further 1.0.x | **Class A only when proven** on the 1.0 line. **v1.0.1** is this change (RW-102 / RW-103). Merge those; pack into Version 1 later only when Sanath asks |
| Next Gen5 *theme* (G5-2 or equivalent) | Only after soak / a measured hole / a written accept. Proposed line **v1.1.0** (or similar) — **not accepted here** |
| Not | A GitHub Release from this PR. A v1.0.1 “docs bump.” Treating 1.0.0 as marketing while remaining gaps are unjudged. Inventing a PyPI token. Inventing G5-2 |

Exact asset steps **done** (Sanath, after PR #52): `python -m build` → attach
`dist/rad_agent-1.0.0-py3-none-any.whl` and `dist/rad_agent-1.0.0.tar.gz`
to GitHub Release **Version 1** / tag **v1.0.0**. Users
`pip install` the wheel URL. PyPI upload remains optional later; not claimed.
**No GitHub Release / tag in this PR.**

### Code findings (closed by G5-1)

What was already in tree vs a **public / product-grade 1.0 baseline**,
and what this change closed. Do not invent a second control plane, do
not unpark MCP, do not raise caps, and do not invent Class A for 403/429.

| already in tree | role | gap vs public 1.0 |
|---|---|---|
| GitHub Release **Version 5** / tag **v0.5.5** | Gen4 pack (0.5.0–0.5.5) | **Closed for Gen4 packing.** Release has **no installable assets**. Version 1 pack **SHIPPED** (wheel + sdist at tag **v1.0.0**) |
| `INSTALLATION.md` / `QUICKSTART.md` | git clone + `pip install -e .` | **Closed for 1.0 honesty (RW-100).** Public path is the Version 1 wheel (tag **v1.0.0**, assets attached); QUICKSTART prints **1.0.0**; contributor checkout remains for dev. Pre-pack “after Sanath packs” prose is a remaining docs residual — not a G5-2 |
| Release gates | pytest, `rad doctor --offline`, `rad acceptance` (50), `rad realworld` | **Locked as the public 1.0 honesty bar (RW-101):** false DONE **0**, Needle OFF, caps 16/60, no live PASS claim, Class C is not a product patch, F-17 / F-26 stay closed |
| G4-3 `rad health` + CAMPAIGN_PLAYBOOK | pause / resume / wait / rotate / run | **Closed for operator workflow.** Residual live campaign is **hold / soak** when a provider recovers — not G5-1 and **not** a G5-2 |
| G4-5 / G4-7 / G4-6 | plan structure, named-file contracts, spend rollup | **Closed scripted** (RW-094–099). Live confirmation deferred. Remaining 11B incompleteness without a contract hole is evidence, not a 1.0 theme |
| `rad connect` / MCP | already first-class; acceptance handshakes | No measured hole (**G4-4 parked**) |
| Caps 16/60 | planner / tool budget | A1 / F-21 closed. RW-059 12→24 still exhausted. Not a 1.0 raise |

### Candidate themes (evidence-backed)

Grounded in Cycle 38 remaining-gaps language, G5-1 closeout, Version 1 pack
**v1.0.0**, Gen5 entry criterion 3, and the residual after Version 5 / Version 1
(live confirmation deferred; historical 11B Class B without a contract hole;
G4-4 no hole; PyPI optional). Do **not** treat a FAIL row as an automatic
architecture rewrite. Do **not** invent fantasy integrations. Do **not**
invent a Class A patch for 403/429. Do **not** invent G5-2 without a
measured product hole.

| id | theme | live providers? | status |
|---|---|---|---|
| **G5-1** | Public / product-grade 1.0 baseline (install, docs, honesty bar) | **No** for the scripted/docs gate | **ACCEPTED + IMPLEMENTED** as **v1.0.0** (scripted RW-100 / RW-101). **Version 1 pack SHIPPED** (tag **v1.0.0**). **No GitHub Release / tag** in the implementation PR |
| **Hold / soak** | Operator live-use of Version 1 / Version 5 path (G4-3 playbook) when NIM / OpenRouter free recover | **Yes** when a brain recovers. Live PASS is **not** required | **RECOMMENDED NEXT** — **not a product theme**, not G5-2, not a package bump. Stay **1.0.0** |
| Unpark G4-4 MCP | No | **not a theme** (no measured hole) |
| PyPI publish / distribution polish | No | **not a theme**. GitHub wheel is the public 1.0 path. Metadata is PyPI-ready. No token in tree. Optional later, not a G5-2 |
| Cap policy / longer-horizon product | No | **not a theme** (A1 / F-21; E1–E3 shipped; RW-059) |
| Residual 11B quality / free-model thrash grab-bag | Live confirmation deferred | **not a theme** (no contract hole; F-44 **NOT CONFIRMED**; 429 is Class C) |
| Stability / false-DONE gates as a standalone slice | No | **part of G5-1’s honesty bar**, not a second theme. False DONE already **0** |
| INSTALLATION / QUICKSTART pre-pack wording | No | **remaining gap, not a theme.** Public wheel URL is live. G5-1-era “after Sanath packs” prose remains. Not **v1.0.1** unless Sanath asks for a Class A honesty pass |

#### G5-1 — ACCEPTED + IMPLEMENTED (public / product-grade 1.0 baseline)

| field | value |
|---|---|
| Status | **ACCEPTED + IMPLEMENTED** as **v1.0.0** (scripted RW-100 / RW-101). **Version 1 pack SHIPPED** after merge (GitHub Release **Version 1** / tag **v1.0.0**). **No GitHub Release / tag** in the implementation PR |
| Theme | **Public / product-grade 1.0 baseline** — install, first-run / docs honesty, 1.0 honesty gates, Version 1 pack at **v1.0.0** |
| Version | **v1.0.0** |
| Problem | Gen4 product contract holes are **closed scripted** (G4-5 / G4-7 / G4-6). Version 5 is **packed** at tag **v0.5.5** (0.5.0–0.5.5). 1.0 is defined as a **stable public / product-grade baseline**, not another executor slice. Measured gap vs that definition: install is git clone + editable pip (`INSTALLATION.md`); the Version 5 GitHub Release has no installable assets; QUICKSTART still claims `rad version` prints **0.4.1**; the 0.5.x honesty gates are not yet locked as a public 1.0 bar. Live confirmation of the Version 5 path has not happened (last working inference **RW-086** on **v0.4.7**) — that is the loop’s **use** step and a Gen5 entry *caveat*, not a missing control-plane hole |
| Entry | Gen4 complete (scripted) on 0.5.0–0.5.5 — **DONE**. Version 5 pack tag **v0.5.5** — **DONE**. Sanath accepts G5-1 as v1.0.0, including an explicit remaining-gaps judgment for a public baseline (deferred live confirmation as caveat; historical 11B Class B without a contract hole stays evidence). Prefer the G4-3 campaign when a provider recovers; live **PASS** is **not** required to ship. Grounded in Gen5’s named purpose, INSTALLATION / QUICKSTART vs the packed line, Cycle 36 closeout (no G4-8), Cycle 37 scope (PR #51), and entry criterion 3 — not in a FAIL row as automatic rewrite. Class C stays Class C. F-17 / F-26 stay closed |
| Non-goals | Inventing a product Class A for 403/429. Remaining-quota. Unparking MCP (G4-4). Raising caps (`max_plan_tasks` **16**, default `Budget.tool_calls` **60`) as “1.0 scale.” Claiming live text_analyzer@12 PASS. Reopening F-17 / F-21 / F-26. Adding checks to fallback *tasks*. Rubber-stamp VERIFIED. Remapping `write_file` / `echo >` (F-44). A new executor slice (E4). A new telemetry stack / SQLite. A control-plane rewrite. Needle on. A **v0.5.6** bump. A GitHub Release / tag in this PR. Treating `/v1/models` **200** as inference entitlement. Making live confirmation itself the product theme while gates stay paused |
| Needs live providers | **No** for the scripted/docs gate. Live soak prefers a recovered brain (G4-3 playbook) and is **not** a live PASS claim |
| What it is not | Not Gen4 leftover numbering. Not “wait forever” for Class C. Not inventing a PyPI token. Not a second health probe. Not packing Version 5 again. Not a live PASS claim |

**Why this one first (investigated alternatives):**

| alternative | why not G5-1 |
|---|---|
| Live confirmation / production soak of Version 5 path | Highest *loop* leverage (`use`), and entry criterion 3 names it. **Not** the product slice: G4-3 already shipped `rad health --campaign`. NIM / OpenRouter free remain **paused**. Cycle 36 already refused this as G4-8 / a package theme. Running the campaign is operator work when a provider recovers, recorded as an RW row. Honest FAIL / BLOCKED remains valid. Remains **hold / soak** after G5-1, not G5-1 itself and **not** a G5-2. Do not stall 1.0 on Class C |
| Unpark G4-4 MCP | No measured production row. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. README “remote-MCP hardening” is an idea, not an evidence row. **Parked** |
| Cap policy / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Not a missing executor and not a 1.0 raise |
| Residual Class B after G4-5 / G4-6 / G4-7 | Plan-*structure*, named-file / JSON-field contracts, and spend rollup are **closed scripted**. Remaining 11B incompleteness without a contract hole is evidence, not a theme. Do not invent G5-n to re-open F-17 or “make 11B pass” |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A paths are patched or F-44 **NOT CONFIRMED**. 429 is Class C. Not a theme |
| Stability / regression / false-DONE gates as a standalone theme | False DONE already **0**. Release gates already green on 0.5.5. Locking that bar for a public baseline is **part of G5-1**, not a second product slice |
| Operational runbooks / `needs_user` UX polish | G4-1 / G4-2 / G4-3 already shipped pause / resume / skip-blocked doctor / `rad health`. Residual copy is not a measured hole |

**Acceptance gates (this change):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Public install / docs | first-run path matches package **1.0.0**; QUICKSTART / INSTALLATION do not advertise a stale `rad version`; no live PASS claim in public docs (RW-100) |
| Honesty bar | Needle **OFF**; caps **16/60** unless a proven product need is documented; false DONE **0**; Class C is not a product patch; F-17 / F-26 stay closed (RW-101) |
| Packing | package **1.0.0**; **no GitHub Release / tag in the G5-1 PR** — Sanath packed **one Version 1 / 1.0** at tag **v1.0.0** after merge |
| Invariants | no live PASS claim; remaining-quota not invented; MCP not force-built; no cap raise as the theme |

**What shipped:** package **1.0.0**; PyPI-ready metadata (`classifiers`,
URLs, `pack` extra for `build`); QUICKSTART / INSTALLATION / README
public wheel path + contributor checkout; Version 1 packing steps for
Sanath (wheel + sdist; no secrets); 1.0 honesty bar locked in ROADMAP /
README / gates narrative; scripted RW-100 / RW-101. **Version 1 pack
SHIPPED** after merge (tag **v1.0.0**, wheel + sdist attached).

### v1.0.1 — proven Class A (RW-102 / RW-103)

| field | value |
|---|---|
| Status | **IMPLEMENTED** as **v1.0.1** (scripted RW-102 / RW-103). **No GitHub Release / tag** — pack later only when Sanath asks |
| Theme | Proven Class A on the 1.0 line (not a G5-2) |
| Version | **v1.0.1** |
| Problem | Two live-measured holes on **v1.0.0**. **A CONFIRMED:** `rad doctor` / `rad health` ignored pinned `cfg.model` and pinged OpenRouter `default_model` `meta-llama/llama-3.3-70b-instruct:free` (HTTP 404) while direct chat to `deepseek/deepseek-v4-flash-0731:free` returned 200. NVIDIA 403 is separate Class C. **B CONFIRMED:** G4-7 `json_field` inference tokenized English (“keys on a sample” / parenthetical “on a sample”) into a bogus key `on`, so a disk-complete `text_analyzer/` package never VERIFIED |
| Non-goals | Inventing Class A for 403/429. Remaining-quota. Reopening F-17 / F-26. Cap raise. Needle on. A GitHub Release / tag. A **v1.1.0** theme. Live PASS claim |
| Needs live providers | **No** for the scripted gate. Soak pointers recorded; no live PASS required to ship |

**What shipped:** `inference_probe_model` + doctor/health ping the pin; `JSON_KEY_STOP` drops English glue (`on`, `sample`, …); scripted RW-102 / RW-103. Caps **16/60**. Needle **OFF**. False DONE **0**.

### G5 hold / soak — SHIPPED (docs; stay 1.0.0)

| field | value |
|---|---|
| Status | **SHIPPED** as docs (Cycle 39). Not a product theme. **No G5-2** |
| Theme | **Hold / soak** — operator live-use of Version 1 / Version 5; remaining gaps recorded |
| Version | **none.** Stay **1.0.0**. Not **v1.0.1**. Not **v1.1.0** |
| Problem | G5-1’s public baseline is **shipped and packed**. The operating loop’s next *use* step has not happened on this line (last working inference **RW-086** on **v0.4.7**; NIM **403** paused; OpenRouter free **429** paused). Cycle 36 already refused live confirmation as a package theme. G4-3 already shipped `rad health --campaign`. There is **no measured product hole** for MCP, caps, remaining-quota, PyPI upload, or residual 11B without a contract. Inventing G5-2 would violate investigate-first |
| Entry | G5-1 shipped as **v1.0.0** (RW-100 / RW-101) — **DONE**. Version 1 pack tag **v1.0.0** — **DONE**. Sanath records hold / soak instead of accepting a second 1.0 product slice. Grounded in Cycle 38 remaining limitations, G4-3 playbook already in tree, G4-4 no hole, paused Class C gates, and packing doctrine (further 1.0.x = Class A only). Class C stays Class C. F-17 / F-26 stay closed |
| Non-goals | Inventing G5-2. Force-building MCP (G4-4). Reopening F-17 / F-21 / F-26. Adding checks to fallback *tasks*. Rubber-stamp VERIFIED. Cap raise as the theme (`max_plan_tasks` **16**, default `Budget.tool_calls` **60**). Inventing remaining-quota. Claiming 11B quality is solved. Remapping `write_file` / `echo >` (F-44). Inventing a product Class A for 403/429. A new executor slice (E4). A new telemetry stack / SQLite. A control-plane rewrite. Needle on. A GitHub Release / tag. A **v1.0.1** / **v1.1.0** bump. Treating `/v1/models` **200** as inference entitlement. Treating live confirmation as a package theme while gates stay paused. Inventing a PyPI token |
| Needs live providers | **No** for this docs hold. Soak itself needs a recovered brain and is **not** a live PASS claim |
| What it is not | Not “wait forever” for Class C. Not a claim that Version 1 has been **used** live. Not packing Version 1 again. **No GitHub Release / tag in this PR** |

**Why hold / soak next (investigated alternatives):**

| alternative | why not next |
|---|---|
| Live confirmation / production soak of Version 1 / Version 5 path **as a package theme (G5-2)** | Highest *loop* leverage (`use`). **Not** a product slice: G4-3 already shipped `rad health --campaign`. NIM / OpenRouter free remain **paused**. Cycle 36 refused this as G4-8. Cycle 37 kept it as G5-1’s entry caveat, not G5-1 itself. Running the campaign is operator work when a provider recovers, recorded as an RW row. Honest FAIL / BLOCKED remains valid. **Recommended as hold / soak**, not as G5-2 / **v1.1.0** |
| Unpark G4-4 MCP | No measured production row. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. README “remote-MCP hardening” is an idea, not an evidence row. **Parked.** Do not force-build |
| PyPI publish / distribution polish | Public 1.0 path is the Version 1 GitHub wheel (tag **v1.0.0**, assets attached). `pyproject.toml` is already PyPI-ready. No token in tree. Upload is operator/distribution work Sanath may do later — not a Gen5 theme and not **v1.0.1** |
| Cap policy / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted. Not a missing executor and not a 1.0 raise |
| Residual Class B after G4-5 / G4-6 / G4-7 / G5-1 | Plan-*structure*, named-file / JSON-field contracts, spend rollup, and the public 1.0 baseline are **closed scripted**. Remaining 11B incompleteness without a contract hole is evidence, not a theme. Do not invent G5-2 to re-open F-17 or “make 11B pass” |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A paths are patched or F-44 **NOT CONFIRMED**. 429 is Class C. Not a theme |
| INSTALLATION / QUICKSTART “after Sanath packs” wording | Public wheel URL is live. Pre-pack prose is a **docs residual**, not a control-plane hole. Not a G5-2. Class A honesty pass (**v1.0.1**) only if Sanath asks |
| A v1.0.1 docs-only package bump | No proven Class A. Stay **1.0.0**. Version 1 is already packed at tag **v1.0.0** |
| A v1.1.0 “next theme” bump | No measured product hole and no written accept. **v1.1.0** is the *line* for a future Gen5 theme after soak — not this cycle |

**Remaining gaps (not themes):**

1. Live text_analyzer@12 remains historical Class B FAIL (`needs_user`). False DONE **0**.
2. E1 / E2 / E3 and Version 5 / G4-5 / G4-7 / G4-6 / Version 1 are scripted (or packed) only. Live confirmation **deferred** until a provider recovers.
3. Live NIM loop **paused** (RW-084 HTTP 403). Live OpenRouter free loop **paused** (RW-086 HTTP 429 `free-models-per-day`). Class C is unblock the environment.
4. G4-4 MCP still has **no measured hole**.
5. PyPI `pip install rad-agent` is **not** claimed (no token in tree).
6. INSTALLATION / QUICKSTART / README still include G5-1-era “after Sanath packs” / contributor-until-assets prose; the Version 1 wheel URL is the public path.
7. Open GitHub issues: **none** (as of this scope).

**Entry criteria for a later G5-2 / v1.1.0 (or v1.0.1):**

| later work | when | proposed version |
|---|---|---|
| Proven Class A on the 1.0 line | A named RAD defect with disk evidence | **v1.0.1** — pack later only when Sanath asks |
| New Gen5 *theme* | Soak / operator use produces a measured capability hole, **or** Sanath accepts remaining gaps as a new 1.0 slice | **v1.1.0** (or similar) — listed then accepted in a later scope |
| Unpark G4-4 | A named production row that MCP / custom-provider *absence or drift* blocked a real objective | Class A on 1.0.x **or** a Gen5 theme — not forced now |
| Live campaign execution | A recovered entitled brain | Operator RW row via G4-3; **not** a package theme by itself |

**Acceptance gates (this change — docs):**

| gate | meaning |
|---|---|
| Offline tests | `python -m pytest -q` |
| Doctor | `rad doctor --offline` |
| Acceptance | `rad acceptance` |
| Real-world suite | `rad realworld` (`live_nim` may stay BLOCKED) |
| Invariants | Needle **OFF**; caps **16/60**; false DONE **0**; Class C is not a product patch; no live PASS claim; F-17 / F-26 stay closed; remaining-quota not invented; **no GitHub Release / tag in this PR**; package stays **1.0.0** |

### Accepting a further v1.0.x / v1.1.0 theme

A short written decision that names the theme, the evidence rows, the
invariant that must not move (Needle off; caps unchanged unless proven;
models propose / RAD decides; false DONE **0**; Class C is not a product
patch; F-17 / F-26 closed), and the version line. **G5-1** is shipped and
packed as **v1.0.0**. Further **1.0.x** is **Class A only when proven**
(**v1.0.1**). A new Gen5 theme after soak is **v1.1.0** only when
accepted. **No GitHub Release / tag in this PR.** Stay **1.0.0**.

---

## Related documents

| doc | role |
|---|---|
| [MATURATION_CYCLE_REPORT.md](MATURATION_CYCLE_REPORT.md) | Cycle-by-cycle evidence and decisions |
| [REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md) | Disk-checked task rows (do not rewrite RW-058–101; RW-102 / RW-103 are v1.0.1 Class A) |
| [REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md) | A/B/C findings |
| [ADR-001-NEEDLE-TOOL-ROUTER.md](ADR-001-NEEDLE-TOOL-ROUTER.md) | Needle stays optional / off |
| [CONTROL-PLANE.md](CONTROL-PLANE.md) | Shipped control-plane behaviour |
| [DEVELOPMENT.md](DEVELOPMENT.md) | How to change the tree without breaking the invariants |
| [ACCEPTANCE.md](ACCEPTANCE.md) | 50-item release gate |
