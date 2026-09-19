# RAD development roadmap

This is the **operating spine** for RAD: five generations, one loop, evidence in / evidence out.
It is not a product-idea backlog (that list stays in the README) and it is not a license to
redesign the control plane.

**Status (2026-09-19):** Generation 1 is **complete**. Generation 2 is
**complete** (v0.3.0–v0.3.2). Generation 3 is **complete (scripted)** on
v0.4.0–v0.4.9. Theme 1 — **path-aligned checks / package layout** — shipped
as **v0.4.0** and **live-confirmed** (RW-071; RW-073 disk/tasks; RW-075
obj-checks). Theme 2 — **multi-file coding under tight budgets** — shipped
as **v0.4.1** and **live-confirmed** (RW-073 contracts + mkdir class). Theme
3 — **longer-horizon / multi-step reliability** — slices A–D shipped as
**v0.4.2–v0.4.5** (ASCII-tree **live-confirmed**; mkdir File-exists
**live-confirmed** RW-081); E1/E2/E3 shipped as **v0.4.6 / v0.4.8 / v0.4.9**
(scripted RW-083 / RW-087 / RW-088). Slice F (xxd ENVIRONMENT) shipped as
**v0.4.7** (scripted RW-086; live RW-086 thrash **CLEARED**). Live E1–E3
confirmation is **deferred** until a provider recovers (NIM **Class C
paused** RW-084 HTTP 403; OpenRouter free **paused** RW-086 HTTP 429
`free-models-per-day`). Live text_analyzer@12 still **FAIL** `needs_user`
historically; false DONE **0**; Needle **OFF**; caps **16/60**. Residual
Class B: fallback PLAN quality, incomplete package artifacts, free-model
thrash. Generation 4 is **planned / scoped** (not started as a build).
Recommended first **v0.5.0** candidate **G4-1** (live multi-provider /
free-provider production doctrine) is **listed, not accepted**. Package
stays **0.4.9**. Generation 5 is **not started**.

```
build → test → validate → release → use → discover gaps → build the next version
```

Never skip a generation. Never invent a `v0.3.x` feature without an evidence row.
Stability with no code change is a valid result.

---

## Current status

| item | value |
|---|---|
| Generation in production | **Gen3 complete (scripted)** — **v0.4.9**; last live-use with **working inference** is **RW-086** on tag `v0.4.7` @ `850aaf9c` (OpenRouter free; then **429**); prior working-inference row is RW-085 on tag `v0.4.6` @ `8f09be58`; v0.4.6 live NIM attempt is RW-084 **BLOCKED Class C**; last NIM working-inference row remains RW-081 on `v0.4.5` @ `32e9fe87`; v0.4.4 is tagged `v0.4.4` @ `acb61997`; v0.4.3 is tagged `v0.4.3` @ `99099b8a`; v0.4.2 is tagged `v0.4.2` @ `feb8a4ec`; v0.4.1 is tagged `v0.4.1` @ `387bd83a`; v0.4.0 is tagged `v0.4.0` @ `a8aac8ae`; Gen2 complete on `387776dc` / tag `v0.3.2`; Gen1 baseline remains tagged `v0.2.3` @ `d121c3f` |
| Package / tag on `main` | **0.4.9** (this change — **no bump**). Tag `v0.4.9` @ `05ea0df302aa6bfd15eccfb84341aeed75d6e1d0` (merge PR #37) is E3. Tag `v0.4.8` @ `f5cda30dcbb6a2ff96465ea20997f384a5f53f4a` is E2. Tag `v0.4.7` @ `850aaf9c3a931a5ba119bdbb6ec73ae4a6fa73e9` remains the live RW-086 run |
| This change | **docs / scope only** — mark Gen3 **complete (scripted)** with live E1–E3 confirmation **deferred**; scope Gen4 v0.5.x as **planned / scoped**; stay **0.4.9** |
| Generation 2 | **COMPLETE** — theme 1 **v0.3.0** (used RW-065 / RW-068); theme 2 **v0.3.1** (used live RW-066 / RW-068); theme 3 **v0.3.2** (scripted RW-067; used RW-068 / RW-069) |
| Latest use (RW-086) | Live OpenRouter free text_analyzer on v0.4.7 **FAIL** `needs_user` @ tools **12/12**: provider **openrouter** / `nvidia/nemotron-3.5-lightning:free`; `$0`; PLAN `source=fallback` attempts=2; task1 **COMPLETED** + task2 attempts=1; E1 **not live** (0 TaskYield). xxd Class A ENVIRONMENT thrash **CLEARED** (0 xxd / 0 ENVIRONMENT / 0 repair). Residual Class **B+C** (fallback plan, missing tests/README, odd summary + late HTTP **429** `free-models-per-day`). False DONE **0** |
| Live OpenRouter free loop | **PAUSED** until `free-models-per-day` rate limit resets (RW-086). Do not treat further free-model retries as product Class B until rate clears |
| Live NIM loop | **PAUSED / Class C blocked** (RW-084). E1 live gate still **not confirmed**. Scripted RW-083 remains unit evidence |
| Generation 3 | **COMPLETE (scripted)** — theme 1 **implemented** (v0.4.0) **used** (RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 / RW-085 / RW-086); theme 2 **implemented** (v0.4.1) **used** (RW-073 / RW-075 / RW-077 / RW-079 / RW-081 / RW-085 / RW-086); theme 3 slices A–D **v0.4.2–v0.4.5** **used** (RW-075 / RW-077 / RW-079 / RW-081; mkdir live Y on RW-081); slice E1 **v0.4.6** **implemented** (scripted RW-083; live **not confirmed** on RW-084/085/086); slice F **v0.4.7** **implemented** (xxd ENVIRONMENT; scripted RW-086; live RW-086 thrash **CLEARED**); slice E2 **v0.4.8** **implemented** (scripted RW-087; live **not confirmed**); slice E3 **v0.4.9** **implemented** (scripted RW-088; live **not confirmed**). Live E1–E3 confirmation **deferred** until a provider recovers |
| Generation 4 | **PLANNED / SCOPED** — not started as a build. Recommended first **v0.5.0** candidate **G4-1** listed, **not accepted** |
| Generation 5 | **NOT STARTED** |
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
| **4** | Production Scale | v0.5.x | **PLANNED / SCOPED** (not started; first v0.5.0 candidate **G4-1** listed, not accepted) |
| **5** | 1.0 | v1.0.0 | **NOT STARTED** |

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
recovers. Gen4 is **planned / scoped** (not started as a build). Gen5
stays closed until Gen4 has been released and used.

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

## Generation 4 — Production Scale — PLANNED / SCOPED (v0.5.x)

Operational robustness, extensibility, integrations, larger workloads —
after Gen3 maturity themes have measured (scripted) wins.

**Status:** **planned / scoped.** **Not started** as a build. Package
stays **0.4.9**. Do **not** implement v0.5.0 in this change. Same loop.
Same A/B/C rules. Same gates. Needle stays **OFF**. Caps (`max_plan_tasks`
**16**, default `Budget.tool_calls` **60**) unchanged unless a proven
product need is documented.

Live E1–E3 confirmation is **deferred**, not a license to invent the
next executor slice. Class B rows are input to a theme decision. They
do not start the generation by themselves — a theme must be **accepted**.

### Entry criteria (how Gen4 opens)

Gen4 **build** starts only when **all** of the following are true:

1. **Gen3 complete (scripted) on 0.4.0–0.4.9 — DONE** (this change).
   Themes 1–2 live-confirmed. Theme 3 slices A–E3 + F shipped. Live
   E1–E3 confirmation **deferred** until a provider recovers — that
   deferral is a **caveat**, not a missing Gen3 theme.
2. Sanath **accepts a first v0.5.0 theme** — not implied by a
   `needs_user` / FAIL / 429 / 403 row. **Not done.** Recommended
   first candidate **G4-1** is listed below — **not accepted**.
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

What is already in tree vs the measured production-scale gap. This is
**strengthen / use / doctrine**, not invent a second control plane.

| already in tree | role | gap vs measured Gen3-use |
|---|---|---|
| `rad/router.py` free-first chain | local → free round-robin → paid (unless free-lock); 401/403 skip to next | Live RW runs **pin** one free brain (`rad use` / force). RW-084 403 and RW-086 429 did not rotate to another free path before the loop paused |
| `rad/control/recovery.py` | HTTP 429 → TRANSIENT/NETWORK; HTTP 403 → AUTH; `switch_model` exists | Mid-run 429 still spent tools as MODEL_FAILURE retry (RW-086). Doctrine today is **pause the loop**, not a product Class A |
| `rad cost` / `RouterState.cost_report` | paid 14-day token spend | Free-tier quota / 429 is invisible. Per-objective tool/model budgets are not a production rollup |
| `rad events` / `trace` / `inspect` / `replay` / `why` | per-objective observability | Enough for one run; not a production cost/budget report across free providers |
| `Planner._fallback` (F-17) + E2 empty `depends_on` | goal clause-split, cap 7, no checks on fallback *tasks* | Live RW-085 / RW-086: `source=fallback` attempts=2 — not a coding plan. Residual Class B after E1–E3 |
| `rad connect` / skills / MCP gate; `rad provider add` | MCP + any OpenAI-compatible endpoint already first-class | No measured production row says MCP or custom-provider *absence* is the hole. Acceptance already handshakes MCP |

### Candidate themes (evidence-backed; not accepted)

Grounded in RW-084 / RW-085 / RW-086 and the residual Class B after
E1–E3. Do **not** treat a FAIL row as an automatic architecture
rewrite. Do **not** invent fantasy integrations.

| id | theme | live providers? | status |
|---|---|---|---|
| **G4-1** | Live multi-provider / free-provider production doctrine | **Yes** (or a second usable free path) | **recommended first v0.5.0 candidate — not accepted** |
| **G4-2** | Fallback / LLM plan quality under tight budgets | Scripted possible; live confirmation needs a recovered brain | candidate |
| **G4-3** | Operational scale: longer workloads, observability, cost/budget reporting | Longer-horizon live needs a recovered provider; reporting can be scripted | candidate |
| **G4-4** | Extensibility / integrations (MCP, custom providers) | No — already partially in tree | **not a first theme** (no measured hole) |

#### G4-1 — Live multi-provider / free-provider production doctrine

| field | value |
|---|---|
| Status | **CANDIDATE**. Recommended first **v0.5.0**. **Not accepted. Not implemented.** |
| Problem | Production free-first use is **paused**. NIM chat/completions **403** (RW-084 Class C; `/v1/models` 200). OpenRouter free **429** `free-models-per-day` (RW-086 Class C rate, after working inference). Live text_analyzer@12 never recovered a second free brain inside the run. Class C is being paused correctly; there is no written production doctrine for rotate / pause / do-not-invent-Class-A, so 403/429 keep looking like product work |
| Entry | A provider recovers **or** a second usable free path is unpaused. Sanath accepts G4-1 as v0.5.0. Grounded in RW-084 / RW-086, not in a new catalog. Class C stays Class C |
| Non-goals | Inventing a product Class A for 403/429. Raising caps as the fix. Needle on. Claiming live text_analyzer@12 now PASS. Treating router failover that already exists as missing. A control-plane rewrite |
| Needs live providers | **Yes.** Scripted router tests already exist; accepting this theme without a recovered path is process-only |
| What it is not | Not Gen3 theme 4. Not “wait forever.” Not a license to pin paid spend under free-lock |

#### G4-2 — Fallback / LLM plan quality under tight budgets

| field | value |
|---|---|
| Status | **CANDIDATE**. Not accepted. Not the first v0.5.0 recommendation |
| Problem | After E1–E3, live coding still dies on a weak plan. RW-085 / RW-086: PLAN `source=fallback` attempts=2, clause-split from the goal, not a real coding graph. Residual Class B: incomplete package, odd summary, missing README/tests. F-17 is **closed** (do not add checks to fallback *tasks*) |
| Entry | Accepted written theme that names the evidence (RW-085 / RW-086 fallback) and the invariant that must not move (F-17; false DONE 0; caps). Investigate-first: LLM-plan success vs fallback *structure* for coding goals — not “add checks to `_fallback` tasks” |
| Non-goals | Reopening F-17 / F-21 / F-26. Rubber-stamp VERIFIED. Cap raise as the primary fix. Claiming 11B quality is solved. Remapping `write_file` / `echo >` (F-44) |
| Needs live providers | Scripted possible (same pattern as E1–E3). Live confirmation needs a recovered brain |
| What it is not | Not a Gen3 leftover theme number. Not an automatic accept because fallback appeared twice |

#### G4-3 — Operational scale (longer workloads, observability, cost/budget)

| field | value |
|---|---|
| Status | **CANDIDATE**. Not accepted |
| Problem | Production use needs to see tool/model/free-quota spend, not only paid `rad cost`. Longer workloads still sit on E1–E3 (scripted, not live). Default caps 16/60 are **not** raised without a measured product need (A1 / F-21 stay closed) |
| Entry | Accepted theme naming the report or workload gap. Do not raise default `Budget.tool_calls` because text_analyzer@12 failed |
| Non-goals | Cap raise as the theme. A new telemetry stack. SQLite. Claiming live long-horizon PASS while E1–E3 are unconfirmed |
| Needs live providers | Reporting can be scripted. Longer-horizon *use* needs a recovered provider |
| What it is not | Not “raise max-tools to 24 and call it scale.” RW-059 already showed 12→24 still exhausted |

#### G4-4 — Extensibility / integrations (MCP, custom providers)

| field | value |
|---|---|
| Status | **NOT a first theme.** Already partially in tree |
| Problem | None measured. `rad connect` + skill manifests + capability/audit gate ship; acceptance handshakes MCP. `rad provider add` accepts any OpenAI-compatible endpoint. README backlog “remote-MCP hardening” is an **idea**, not an evidence row |
| Entry | A named production row that MCP/custom-provider *absence or drift* blocked a real objective. Until then: do not invent |
| Non-goals | Fantasy connector marketplace. Enabling Needle. Per-agent OS sandboxes (already documented as not done on AGENTS.md — not a Gen4 start) |
| Needs live providers | No |
| What it is not | Not Production Scale just because MCP exists in the tree |

### Recommended first v0.5.0 — G4-1 (candidate, not accepted)

**G4-1** (live multi-provider / free-provider production doctrine) is the
recommended first slice. It is **listed, not accepted, not implemented**.

Why this one first: Gen4 is Production Scale. Both live free paths are
**paused** (RW-084 Class C; RW-086 Class C rate). E1–E3 cannot be
live-confirmed, and Class C keeps getting re-read as product work, until
there is a doctrine for recover / rotate / pause. G4-2 (plan quality) is
the residual Class B and a later candidate — it can be scripted, but it
is not the production-scale gate. G4-3 waits on that gate for live
longer-horizon use. G4-4 has no measured hole.

Next product work waits for a written accept. Stay **0.4.9**.

### Accepting a first v0.5.0 theme

A short written decision that names the theme, the evidence rows, the
invariant that must not move (Needle off; caps unchanged unless proven;
models propose / RAD decides; false DONE **0**; Class C is not a product
patch), and the 0.5.x change. Do not start v0.5.0 from this scope PR.

---

## Generation 5 — 1.0 — NOT STARTED (v1.0.0)

Stable public / product-grade baseline.

Enter **after Gen4**. 1.0 is a generation, not a marketing tag: it still requires the
loop (build → test → validate → release → use → discover that the remaining gaps are
acceptable for a public baseline).

---

## Related documents

| doc | role |
|---|---|
| [MATURATION_CYCLE_REPORT.md](MATURATION_CYCLE_REPORT.md) | Cycle-by-cycle evidence and decisions |
| [REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md) | Disk-checked task rows (do not rewrite RW-058–088) |
| [REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md) | A/B/C findings |
| [ADR-001-NEEDLE-TOOL-ROUTER.md](ADR-001-NEEDLE-TOOL-ROUTER.md) | Needle stays optional / off |
| [CONTROL-PLANE.md](CONTROL-PLANE.md) | Shipped control-plane behaviour |
| [DEVELOPMENT.md](DEVELOPMENT.md) | How to change the tree without breaking the invariants |
| [ACCEPTANCE.md](ACCEPTANCE.md) | 50-item release gate |
