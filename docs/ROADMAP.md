# RAD development roadmap

This is the **operating spine** for RAD: five generations, one loop, evidence in / evidence out.
It is not a product-idea backlog (that list stays in the README) and it is not a license to
redesign the control plane.

**Status (2026-09-18):** Generation 1 is **complete**. Production baseline is **v0.2.3**.
Generation 2 is **not started**. Package stays **0.2.3**. Needle stays off by default.
Caps stay where Gen1 locked them.

```
build → test → validate → release → use → discover gaps → build the next version
```

Never skip a generation. Never invent a `v0.3.0` feature without an evidence row.
Stability with no code change is a valid result.

---

## Current status

| item | value |
|---|---|
| Generation in production | **Gen1 — Foundation — COMPLETE** |
| Package / tag | **0.2.3** / annotated tag `v0.2.3` @ `d121c3f` |
| `origin/main` vs the tag | may be ahead with **docs/tests only** (through PR #17) |
| Generation 2 | **NOT STARTED** (no theme accepted) |
| Generations 3–5 | **NOT STARTED** |
| Needle | optional / **off** (`tool_router=existing`; ADR-001) |
| `max_plan_tasks` | **16** (unchanged) |
| Default `Budget.tool_calls` | **60** (unchanged) |
| False `DONE:` → `VERIFIED` | **0** (invariant) |

Cycle evidence, not this file: [MATURATION_CYCLE_REPORT.md](MATURATION_CYCLE_REPORT.md),
[REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md),
[REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md).

---

## Generations

| Gen | Name | Versions | Status |
|---|---|---|---|
| **1** | Foundation | v0.2.0, v0.2.1, v0.2.2, **v0.2.3** | **COMPLETE** |
| **2** | Capability Expansion | v0.3.x | **NOT STARTED** |
| **3** | Autonomous Agent Maturity | v0.4.x | **NOT STARTED** |
| **4** | Production Scale | v0.5.x | **NOT STARTED** |
| **5** | 1.0 | v1.0.0 | **NOT STARTED** |

Enter the next generation only after the previous one has been **released, used, and has
measured gaps**. Class B rows are the input to that decision. They do not start the
generation by themselves.

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
generation skip**. They do not contradict this roadmap. They also do **not** start Gen2.

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
tests (merged after the tag; currently through PR #17) without a package bump.

What Gen1 locked:

| invariant | lock |
|---|---|
| Control plane | Models propose / RAD decides. The executor is the only way to act |
| Needle | Off by default. Optional adapter only. Not a 0.3.0 capability unless a gold set wins (ADR-001) |
| Planner cap | `max_plan_tasks` default **16** |
| Tool budget | Default `Budget.tool_calls` **60** |
| Honesty | False `DONE:` (claim without the artifact) **= 0** |
| Completion | `VERIFIED` only via independent machine checks — never the model’s own word |

Gen1 also shipped the evidence loop: ledger, task matrix, maturation reports, `rad realworld`,
and the A/B/C classification. That loop continues on 0.2.3 until a Gen2 theme is accepted.

Remaining 0.2.x work, if any, is **Class A only** (smallest patch + regression, still 0.2.x).
Class B stays on the ledger. Class C stays BLOCKED. Do not raise caps. Do not enable Needle.

---

## Generation 2 — Capability Expansion — NOT STARTED (v0.3.x)

Evidence-backed capability additions **on top of** the Gen1 control plane.

- Do **not** redesign the control plane.
- Do **not** enable Needle by default without a gold-set win (`rad needle-eval`).
- Do **not** raise `max_plan_tasks` or default tool budget without a measured product need.
- Do **not** claim Gen2 started because RW-058–062 exist.

### Entry criteria

Gen2 starts only when **all** of the following are true:

1. Gen1 invariants still hold on the production baseline (0.2.3 or a later 0.2.x Class A patch).
2. At least one **Class B theme is accepted** as a product theme — an explicit decision, not
   implied by a `needs_user` / FAIL row.
3. That theme is grounded in **live Gen1 production evidence** (the F-22 family below), not in
   a reconstructed offline story and not in a closed non-gate.
4. Release gates are green (pytest, `rad doctor --offline`, `rad acceptance`, `rad realworld`).

Until then: stay on 0.2.x. Record evidence. Do not bump to 0.3.0.

### Candidate themes (from live Class B evidence)

Grounded in RW-058 / RW-059 / RW-060 / RW-062 and the F-22 family
(F-20260918-15 / 16 / 19 / 20 / 22). These are **candidates**. None is accepted.
None is a v0.3.0 design.

| # | theme | what the evidence showed | rows |
|---|---|---|---|
| 1 | **Verified coding loop** | Write → run tests → repair until **disk checks** pass. Live runs left invalid `result.json` / `summary.json`, failing tests (`13!=6`, `6!=2`), duplicated “tests”, wrong paths, and pollution `DONE:` fake paths. RAD stopped at the budget; verifier did **not** rubber-stamp. False DONE **0**. | RW-058, RW-059, RW-062 |
| 2 | **Plan-timeout resilience** | Retry / re-ask for a JSON plan **before** falling back to no-check goal clause-split. RW-062: nvidia plan timeout → `PLAN_CREATED` `source=fallback` → clause-split of the user goal (later shown **not** to be a parser hole). | RW-062 (timeout path); RW-063 closed the Class A reading |
| 3 | **Budget-aware planning** | Plan that fits the tool budget. RW-059 Case B: doubling tools **12→24** still exhausted the budget and did **not** complete. Default max-tools was **not** raised. | RW-059 vs RW-058; RW-060 / RW-062 also budget-stop |

The F-22 family is the same pattern on coding **and** research **and** a simpler
coding+verification control: 11B + tool budget, success criteria unmet, `needs_user`,
not VERIFIED. Class B is **not** complexity-limited. It is also **not** a missing
control-plane stage.

### Closed non-gates (not Gen2 themes)

These were investigated and are **not** product themes for v0.3.x:

| id | claim | result |
|---|---|---|
| F-17 | Fallback planner splits newlines / converts model prose into spurious tasks | **NOT CONFIRMED.** PR #14 / RW-061: newline-only goal → 1 fallback task. RW-063: timeout/empty/malformed/non-JSON LLM is discarded; `_fallback` splits `obj.goal` on clause markers, cap `[:7]`. No product patch. No v0.2.4. |
| F-18 / budget → `needs_user` | Budget exhaustion is a RAD defect | **Path is correct** (PR #14 / RW-061). Unmet checks → `needs_user` + checkpoint; satisfied checks → `VERIFIED`. False DONE **0**. |

Do not reopen those as Gen2 work unless new disk evidence changes the class.

### What would *accept* a theme

A short written decision that names the theme, the evidence rows, the invariant that must
not move, and the first 0.3.x change. Until that exists, Gen2 remains **not started**.

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
| [REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md) | Disk-checked task rows (do not rewrite RW-058–063) |
| [REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md) | A/B/C findings |
| [ADR-001-NEEDLE-TOOL-ROUTER.md](ADR-001-NEEDLE-TOOL-ROUTER.md) | Needle stays optional / off |
| [CONTROL-PLANE.md](CONTROL-PLANE.md) | Shipped control-plane behaviour |
| [DEVELOPMENT.md](DEVELOPMENT.md) | How to change the tree without breaking the invariants |
| [ACCEPTANCE.md](ACCEPTANCE.md) | 50-item release gate |
