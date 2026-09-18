# RAD development roadmap

This is the **operating spine** for RAD: five generations, one loop, evidence in / evidence out.
It is not a product-idea backlog (that list stays in the README) and it is not a license to
redesign the control plane.

**Status (2026-09-18):** Generation 1 is **complete**. Generation 2 is **in
progress**. Theme 1 — **verified coding loop** — shipped as **v0.3.0** and
**used** (RW-065). Theme 2 — **plan-timeout resilience** — shipped as **v0.3.1**
and **used** (live RW-066 **PASS**). Theme 3 — **budget-aware planning** — is
**implemented as v0.3.2** in this change. Needle stays off. Caps unchanged.
Generations 3–5 are **not started**. This patch does **not** claim all Class B
coding is solved.

```
build → test → validate → release → use → discover gaps → build the next version
```

Never skip a generation. Never invent a `v0.3.x` feature without an evidence row.
Stability with no code change is a valid result.

---

## Current status

| item | value |
|---|---|
| Generation in production | **Gen2** — v0.3.1 on `main` (`50d98e26` / tag `v0.3.1`); this change is **v0.3.2**; Gen1 baseline remains tagged `v0.2.3` @ `d121c3f` |
| Package / tag on `main` | **0.3.1** / annotated tag `v0.3.1` @ `50d98e26` (this branch bumps the package to **0.3.2**) |
| This change | **v0.3.2** — budget-aware planning (Gen2 theme 3) |
| Generation 2 | **IN PROGRESS** — theme 1 **implemented** (v0.3.0) and **used** (RW-065); theme 2 **implemented** (v0.3.1) and **used** (live RW-066 PASS); theme 3 **implemented** (v0.3.2) |
| Latest use (RW-066) | Live NIM 11B word_counter: **PASS** `completed` / VERIFIED; plan fallback attempts=2; Gen2 repair YES; residual **Class B** (11B@12) |
| Generations 3–5 | **NOT STARTED** |
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
| **2** | Capability Expansion | v0.3.x | **IN PROGRESS** (theme 1 → **v0.3.0**; theme 2 → **v0.3.1** used RW-066; theme 3 budget-aware planning → **v0.3.2**) |
| **3** | Autonomous Agent Maturity | v0.4.x | **NOT STARTED** |
| **4** | Production Scale | v0.5.x | **NOT STARTED** |
| **5** | 1.0 | v1.0.0 | **NOT STARTED** |

Enter the next generation only after the previous one has been **released, used, and has
measured gaps**. Class B rows are the input to that decision. They do not start the
generation by themselves — a theme must be **accepted**. The verified coding loop is the
first accepted Gen2 theme and the first v0.3.0 build. Plan-timeout resilience is the
second accepted theme (**v0.3.1**, used live RW-066). Budget-aware planning is the
third accepted theme (**v0.3.2**). Gen3–5 stay
closed until Gen2 has been released and used.

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

## Generation 2 — Capability Expansion — IN PROGRESS (v0.3.x)

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
| Status | **IMPLEMENTED** in this change (package **0.3.2**) |
| Theme | **Budget-aware planning** |
| Version | **v0.3.2** |
| Loop | remaining tool budget → plan prompt; fat graph (over 2-tools/task fit **and** >3 tasks) → **one bounded retry** with a cheaper JSON plan → select the cheaper graph; fat fallback → compact. LLM graphs not silently compacted (F-21) |
| Evidence | RW-059 Case B (12→24 tools still exhausted); RW-065 / live RW-066 tools 12/12; deterministic RW-067 / F-20260918-29 |
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
| 1 | **Verified coding loop** | **IMPLEMENTED** — v0.3.0; **used** RW-065 | Write → run tests → repair until **disk checks** pass. Live 11B still Class B under tools=12; loop helps and does not clear every bound. | RW-058, RW-059, RW-062; RW-064 (scripted); RW-065 (live use) |
| 2 | **Plan-timeout resilience** | **IMPLEMENTED** — v0.3.1; **used** live RW-066 | Retry / re-ask for a JSON plan **before** falling back to no-check goal clause-split. Live RW-066: `attempts=2` then `source=fallback`; objective still VERIFIED. F-17 fallback contract preserved. | RW-062 (timeout path); RW-063 closed the Class A reading; scripted RW-066 (F-27); live RW-066 (F-28) |
| 3 | **Budget-aware planning** | **IMPLEMENTED** — v0.3.2 | Plan that fits the tool budget. RW-059 Case B: doubling tools **12→24** still exhausted the budget and did **not** complete. Default max-tools was **not** raised. | RW-059 vs RW-058; RW-060 / RW-062 / RW-065 / live RW-066 also budget-stop; RW-067 (scripted) |

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

A short written decision that names the theme, the evidence rows, the invariant that must
not move, and the 0.3.x (or later) change. Do not treat this budget-aware
implementation as a blanket v0.3.x redesign.

---

## Generation 3 — Autonomous Agent Maturity — NOT STARTED (v0.4.x)

More reliable multi-step execution, recovery, planning, and long-horizon work.

Enter **only after Gen2 has been released and used**, and only for gaps that Gen2 use
discovers. Do not pre-design Gen3 from Gen1 Class B rows. Do not skip Gen2.

---

## Generation 4 — Production Scale — NOT STARTED (v0.5.x)

Operational robustness, extensibility, integrations, larger workloads.

Enter **after Gen3**. Same loop. Same A/B/C rules. Same gates.

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
| [REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md) | Disk-checked task rows (do not rewrite RW-058–065) |
| [REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md) | A/B/C findings |
| [ADR-001-NEEDLE-TOOL-ROUTER.md](ADR-001-NEEDLE-TOOL-ROUTER.md) | Needle stays optional / off |
| [CONTROL-PLANE.md](CONTROL-PLANE.md) | Shipped control-plane behaviour |
| [DEVELOPMENT.md](DEVELOPMENT.md) | How to change the tree without breaking the invariants |
| [ACCEPTANCE.md](ACCEPTANCE.md) | 50-item release gate |
