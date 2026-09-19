# Maturation cycle reports

Models propose; RAD decides. Needle stays optional/off.
`max_plan_tasks` default remains **16** unless a measured product need requires a documented config key.
Default `Budget.tool_calls` remains **60**.

---

# Cycle 37 — Scope G5-1 public / product-grade 1.0 baseline; stay 0.5.5 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `08cf33893d309981c5f75bef260bca87f5c47d29` (merge PR #50; package **0.5.5**; GitHub Release **Version 5** / tag **v0.5.5** covers 0.5.0–0.5.5)
**Package at start:** `0.5.5`
**This branch:** `cursor/gen5-first-theme-908a` — package **0.5.5** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–099 are **not rewritten**.
**Release:** **none**. Do **not** cut v1.0.0. Version 5 pack is already tag **v0.5.5**.

## Why this cycle

Gen4 is **complete (scripted)** on v0.5.0–v0.5.5 (Cycle 36 / PR #50).
**Version 5 pack** is GitHub Release **Version 5** / tag **v0.5.5**
(0.5.0–0.5.5). G4-4 remains **parked** (no measured hole). Live NIM /
OpenRouter free stay **paused**. Live E1–E3 and Version 5 / G4-5 / G4-7 /
G4-6 confirmation is **deferred**. F-17 / F-26 stay closed. Cycle 24’s
remaining *product* Class B list is **closed scripted**. Remaining 11B
incompleteness without a contract hole is evidence, not a theme.

Investigate-first after closeout: the highest-leverage step toward a
stable public / product-grade **1.0** is **not** live confirmation as a
package theme (G4-3 playbook already ships; Cycle 36 refused G4-8),
**not** unparking MCP, **not** a cap raise, **not** an 11B-quality
grab-bag, and **not** a v0.5.6. Gen5’s named purpose is the public
baseline. Measured gap vs that definition: install is git clone +
`pip install -e .`; the Version 5 GitHub Release has no installable
assets; QUICKSTART still says `rad version` prints **0.4.1** while the
package is **0.5.5**. Live soak remains the loop’s `use` step and a
Gen5 entry *caveat* / remaining-gaps input — not G5-1 itself. Scope
**G5-1** (public / product-grade 1.0 baseline) as proposed **v1.0.0**,
listed not accepted. Stay **0.5.5**.

## Alternatives considered

| candidate | decision |
|---|---|
| Public / product-grade 1.0 baseline (G5-1) | **Recommended first.** Evidence-backed vs Gen5’s named purpose + INSTALLATION / QUICKSTART vs packed 0.5.5. Scriptable/docs without a recovered brain. Remaining-gaps judgment is the accept, not a second theme. Proposed **v1.0.0** only when accepted |
| Live confirmation / production soak of Version 5 path | Highest *loop* leverage. **Not** the product slice. G4-3 playbook ships. Gates paused. Operator work when a provider recovers. Cycle 36 refused this as a package theme. Entry *caveat* / remaining-gaps input, not G5-1 |
| Unpark G4-4 MCP | No measured hole. Already first-class. **Parked** |
| Cap policy / longer-horizon *product* | E1–E3 shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted |
| Residual Class B after G4-5 / G4-6 / G4-7 | Contract holes closed scripted. Remaining 11B incompleteness without a contract hole is evidence, not a theme |
| Stability / false-DONE gates as a standalone theme | False DONE already 0. Gates already green. Part of G5-1’s honesty bar, not a second slice |
| A v0.5.6 docs-only bump | No product change. Stay **0.5.5** |

## Decision

| item | value |
|---|---|
| Package | **0.5.5** (no 0.5.6; no 1.0.0) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **COMPLETE (scripted)**. **Version 5 pack** tag **v0.5.5** (0.5.0–0.5.5). **G4-4 parked** |
| Gen5 | **NOT STARTED**. Entry listed, not accepted |
| Recommended first v1.0.0 candidate | **G5-1** — public / product-grade 1.0 baseline (see ROADMAP). **Not** accepted here |
| Packing | When G5-1 is accepted and shipped: **one Version 1 / 1.0 pack** at tag **v1.0.0**. This PR cuts **no** release |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; F-17 / F-26 stay closed; remaining-quota not invented |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g51-scope-gate` (doctor, acceptance) and `/tmp/rad-g51-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.5 |
| `python3 -m pytest -q` | **PASS** 646 passed in 14.13s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g51-scope-gate/acceptance/20260919-080144_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g51-scope-rw/realworld/20260919-080144_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.5** (no bump) |
| Release / tag | **none** |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. Version 5 / G4-5 / G4-7 / G4-6 have not been live-confirmed together.
4. G5-1 is listed, not accepted. Gen5 is not started. No v1.0.0.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 complete (scripted).**
Recommended next **G5-1** listed, not accepted. Stay **0.5.5**. Gen5 is
not started.

---

# Cycle 36 — Scope Gen4 closeout / Gen5 entry; stay 0.5.5 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `91810955fb5cec2494e481b485ff0a5f893012a5` (merge PR #49; package **0.5.5**)
**Package at start:** `0.5.5`
**This branch:** `cursor/gen4-closeout-gen5-entry-a949` — package **0.5.5** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–099 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks. GitHub Release **Version 5** / tag **v0.5.2** still covers G4-1–G4-3 only.

## Why this cycle

**G4-6** shipped as **v0.5.5** (PR #49; scripted RW-098 / RW-099). Version 5
pack remains GitHub Release **v0.5.2** (G4-1 / G4-2 / G4-3). G4-1 closed
pause. G4-2 closed safe resume. G4-3 closed the operator-use path. G4-5
closed plan-*structure*. G4-7 closed named-file / JSON-field *objective*
contracts. G4-6 closed spend visibility (`rad cost` rollup of persisted
`Usage`). Both live free paths remain **paused**. Live E1–E3 and Version 5
/ G4-5 / G4-7 / G4-6 confirmation is **deferred**. F-17 / F-26 stay closed.

Investigate-first after G4-6: the highest-leverage next step is **not**
MCP, not another “wait for live confirmation” package theme, not a
residual Class B grab-bag, and not a v0.5.6. Cycle 24’s remaining
*product* Class B list (fallback PLAN, incomplete packages) is **closed
scripted**. The Production Scale leftover (spend visibility) is **closed
scripted**. Remaining 11B incompleteness without a contract hole is
evidence, not a theme. G4-3 already shipped the campaign playbook.
Running it is operator work when a provider recovers — not a package bump
while NIM / OpenRouter free stay paused. **G4-4 parked** (no hole). Do
**not** invent G4-8. Do **not** invent remaining-quota. Mark Gen4
**complete (scripted)** with the same live-confirmation caveat Gen3 used.
Scope **Gen5 entry criteria** (listed, not accepted). Stay **0.5.5**.

## Alternatives considered

| candidate | decision |
|---|---|
| Gen4 closeout / Gen5 entry (docs) | **Recommended next.** Evidence-backed: Cycle 24 remaining product Class B closed scripted (G4-5 / G4-7); Production Scale leftover closed scripted (G4-6); G4-4 still no hole; live confirmation is G4-3 operator work while gates paused. Stay **0.5.5**. No v0.5.6. Gen5 not started |
| Extensibility / MCP (G4-4) | No measured hole. Already first-class. **Parked.** Do not force-build |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted |
| Live confirmation of Version 5 / G4-5 / G4-7 / G4-6 path | G4-3 playbook already ships. Gates remain paused. Operator campaign when a provider recovers — not a new product theme |
| Residual Class B after G4-5 + G4-6 + G4-7 | Contract holes closed scripted. Remaining 11B incompleteness without a contract hole is evidence, not a theme. Do not invent G4-8 |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A patched or F-44 **NOT CONFIRMED**. 429 is Class C |
| A v0.5.6 docs-only bump | No product change. Stay **0.5.5**. Pack again only when Sanath asks |

## Code findings (lightweight; no patch)

| existing | role | gap vs post-G4-6 residual |
|---|---|---|
| `infer_coding_checks` | named-file `file_exists` + `json_field` (cap 8) | **Closed** scripted (RW-096 / RW-097). Live confirmation deferred |
| G4-5 `_json_obj` + `PLAN_CODING_RETRY` | near-JSON recover / compact retry | **Closed** scripted (RW-094 / RW-095). Live confirmation deferred |
| `Planner._fallback` (F-17) | clause-split, cap 7, no checks | Do not add checks to fallback *tasks* |
| `rad health` + CAMPAIGN_PLAYBOOK | operator wait/rotate/resume/run | Closed for G4-3. Residual live campaign is operator work |
| `rad connect` / MCP | already first-class | No measured hole (**G4-4 parked**) |
| `rad cost` / `ObjectiveStore.usage_rollup` | paid 14-day + persisted Usage rollup | **Closed** scripted (RW-098 / RW-099). Remaining-quota not invented |
| E1 / E2 / E3 | leftover dispatch / independent files / retry stop | Scripted. Live confirmation waits on Class C recovery |

## Decision

| item | value |
|---|---|
| Package | **0.5.5** (no 0.5.6) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **COMPLETE (scripted)**. **G4-6 shipped** as **v0.5.5**. **Version 5 pack** still **v0.5.2** (G4-1–G4-3). **G4-4 parked** (no hole) |
| Recommended next | **Gen5 entry criteria** (see ROADMAP). **Not** accepted here. Gen5 **not started** |
| Other candidates | G4-4 extensibility (parked — no hole). Do not invent G4-8 |
| Next product work | Waits for proven Class A on 0.5.5, or an accepted v1.0.0 theme after Gen4-use / remaining-gaps judgment |
| Packing | Merge-only. **No per-slice GitHub Release.** Pack again only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; F-17 / F-26 stay closed; remaining-quota not invented |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g4-closeout-gate` (doctor, acceptance) and `/tmp/rad-g4-closeout-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.5 |
| `python3 -m pytest -q` | **PASS** 646 passed in 11.71s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g4-closeout-gate/acceptance/20260919-075122_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g4-closeout-rw/realworld/20260919-075123_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.5** (no bump) |
| Release / tag | **none** — Version 5 packing doctrine |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. Version 5 / G4-5 / G4-7 / G4-6 have not been live-confirmed together.
4. Gen5 entry is listed, not accepted. Gen5 is not started.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 complete (scripted).**
Recommended next **Gen5 entry** listed, not accepted. Stay **0.5.5**. Gen5 is
not started.

---

# Cycle 35 — G4-6 cost/budget reporting; v0.5.5 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `639a6d61c251e336c4ab61bfc6d41a833fd651ec` (merge PR #48; package **0.5.4**)
**Package at start:** `0.5.4`
**This branch:** `cursor/g4-6-cost-budget-report-7432` — package **0.5.5**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — G4-6 accepted + implemented. RW-058–097 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

## Why this cycle

G4-6 was scoped on Cycle 34 / PR #48 and **accepted**. G4-7 closed named-file
/ JSON-field *objective* contracts (v0.5.4 / RW-096 / RW-097). Version 5
pack remains GitHub Release **v0.5.2** (G4-1–G4-3). The remaining measured
Production Scale leftover was spend visibility: `rad cost` /
`RouterState.cost_report` reported paid 14-day tokens only; per-objective
`Usage` already persisted on `objective.json` and was not rolled up.
Free remaining-quota is not in the API until 429 — not invented. G4-2
last Class C + Retry-After is not re-done. F-17 stays closed.

## Decision

| item | value |
|---|---|
| Package | **0.5.4 → 0.5.5** |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-6 ACCEPTED + IMPLEMENTED** as **v0.5.5** |
| Evidence | scripted **RW-098** / **RW-099** / F-20260919-57 |
| Release / tag | **none** — Version 5 pack later only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; remaining-quota not invented; F-17 fallback *tasks* stay check-less |

## What shipped

- `ObjectiveStore.usage_rollup` sums persisted `tool_calls` / `model_calls` / `money_usd` / `tokens` (RW-098)
- `rad cost` prints that rollup under the existing paid 14-day section (RW-099)
- Remaining-quota is **not** a field; G4-2 last Class C + Retry-After is untouched

## Quality gates (this branch)

Isolated homes `/tmp/rad-g46-gate` (doctor, acceptance) and `/tmp/rad-g46-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.5 |
| `python3 -m pytest -q` | **PASS** 646 passed in 11.81s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g46-gate/acceptance/20260919-073423_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g46-rw/realworld/20260919-073426_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16 / `Budget.tool_calls` 60 |
| False DONE | **0** |
| Release / tag | **none** |

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-6 implemented as v0.5.5.** **No GitHub Release / tag.** Gen5 is not started.

---

# Cycle 34 — Scope G4-6 cost/budget reporting; stay 0.5.4 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `3e9f313966e0ff07a6eb246f02716fb803d52308` (merge PR #47; package **0.5.4**)
**Package at start:** `0.5.4`
**This branch:** `cursor/g4-6-cost-budget-scope-d57f` — package **0.5.4** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–097 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks. GitHub Release **Version 5** / tag **v0.5.2** still covers G4-1–G4-3 only.

## Why this cycle

**G4-7** shipped as **v0.5.4** (PR #47; scripted RW-096 / RW-097). Version 5
pack remains GitHub Release **v0.5.2** (G4-1 / G4-2 / G4-3). G4-1 closed
pause. G4-2 closed safe resume. G4-3 closed the operator-use path. G4-5
closed plan-*structure*. G4-7 closed named-file / JSON-field *objective*
contracts. Both live free paths remain **paused**. Live E1–E3 confirmation
is **deferred**. F-17 stays closed.

Investigate-first after G4-7: the highest-leverage **Production Scale**
gap is not MCP, not another “wait for live confirmation” theme, and not
a residual Class B grab-bag. G4-3 already shipped the campaign playbook.
Running it is operator work when a provider recovers — not a package bump
while NIM / OpenRouter free stay paused. Cycle 24’s remaining *product*
Class B list (fallback PLAN, incomplete packages) is **closed scripted**.
Remaining 11B incompleteness without a contract hole is evidence, not a
theme. Cycles 30–32 deferred **G4-6** as “wait for Version 5 live-use
data” so G4-5 / G4-7 could ship. That was a **priority deferral**, not a
missing API. Per-objective `Usage` already persists; `rad cost` is
paid-14-day only. Scripted/offline runs already write those records.
**G4-4 id kept** (no hole). **G4-6 id kept** (do not invent G4-8 for the
same work).

## Alternatives considered

| candidate | decision |
|---|---|
| Cost/budget reporting | **Recommended next (G4-6 / v0.5.5).** Evidence-backed (Cycle 24 `rad cost` paid-only; RW-086 `$0` / tools 12/12; existing `Objective.usage` not rolled up). Scriptable without a recovered brain. Do not invent remaining-quota. Does not invent Class A for 403/429 |
| Extensibility / MCP (G4-4) | No measured hole. Already first-class. **Id kept** |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted |
| Live confirmation of Version 5 / G4-5 / G4-7 path | G4-3 playbook already ships. Gates remain paused. Operator campaign when a provider recovers — not a new product theme |
| Residual Class B after G4-5 + G4-7 (plan quality + artifact contracts) | G4-5 / G4-7 closed those contract holes scripted. Remaining 11B incompleteness without a contract hole is evidence, not a theme. Do not invent G4-8 |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A patched or F-44 **NOT CONFIRMED**. 429 is Class C |

## Code findings (lightweight; no patch)

| existing | role | gap vs post-G4-7 residual |
|---|---|---|
| `infer_coding_checks` | named-file `file_exists` + `json_field` (cap 8) | **Closed** scripted (RW-096 / RW-097). Live confirmation deferred |
| G4-5 `_json_obj` + `PLAN_CODING_RETRY` | near-JSON recover / compact retry | **Closed** scripted (RW-094 / RW-095). Live confirmation deferred |
| `Planner._fallback` (F-17) | clause-split, cap 7, no checks | Do not add checks to fallback *tasks* |
| `rad health` + CAMPAIGN_PLAYBOOK | operator wait/rotate/resume/run | Closed for G4-3. Residual live campaign is operator work |
| `rad connect` / MCP | already first-class | No measured hole (G4-4) |
| `rad cost` / `RouterState.cost_report` | paid 14-day token spend | **G4-6 hole.** Free remaining-quota not in API until 429. Per-objective `Usage` persists, not rolled up |
| `Objective.usage` | tools / model / money / tokens on `objective.json` | One-run banner / `rad inspect` only. No production rollup |

## Decision

| item | value |
|---|---|
| Package | **0.5.4** (no 0.5.5) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-7 shipped** as **v0.5.4**. **Version 5 pack** still **v0.5.2** (G4-1–G4-3). **G4-6 listed, not accepted** |
| Recommended next v0.5.5 candidate | **G4-6** — cost/budget reporting (see ROADMAP). **Not** accepted here |
| Other candidates | G4-4 extensibility (not next — no hole) |
| Next product work | Waits for an accepted v0.5.5 theme |
| Packing | Merge-only. **No per-slice GitHub Release.** Pack again only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; F-17 stays closed |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g46-scope-gate` (doctor, acceptance) and `/tmp/rad-g46-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.4 |
| `python3 -m pytest -q` | **PASS** 641 passed in 11.58s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g46-scope-gate/acceptance/20260919-072716_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g46-scope-rw/realworld/20260919-072717_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.4** (no bump) |
| Release / tag | **none** — Version 5 packing doctrine |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-6 is scoped so a later accept can roll up existing per-objective spend — not a live PASS, not remaining-quota.
4. G4-6 is listed, not accepted.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-7 implemented as v0.5.4.** Recommended next **G4-6** listed, not
accepted. Stay **0.5.4**. Gen5 is not started.

---

# Cycle 33 — G4-7 coding artifact completeness; v0.5.4 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `0865f58c74391c39b83dcd71454e4ea7d5d6979e` (merge PR #46; package **0.5.3**)
**Package at start:** `0.5.3`
**This branch:** `cursor/g4-7-artifact-completeness-4e19` — package **0.5.4**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — G4-7 accepted + implemented. RW-058–095 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

## Why this cycle

G4-7 was scoped on Cycle 32 / PR #46 and **accepted**. G4-5 closed plan
*structure* (v0.5.3 / RW-094 / RW-095). Version 5 pack remains GitHub
Release **v0.5.2** (G4-1–G4-3). The remaining measured Class B on a
working product path was incomplete packages: RW-081 empty `{}`
`summary.json` still passed `json_valid`; RW-085 / RW-086 missing
README.md / tests + alt-schema summary. `infer_coding_checks` already
added `json_valid` / test `shell_ok` / `file_line_count` — not named
README.md / analyzer.py `file_exists`, not `json_field` for required
keys. F-17 stays closed (do not add checks to fallback *tasks*).

## Decision

| item | value |
|---|---|
| Package | **0.5.3 → 0.5.4** |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-7 ACCEPTED + IMPLEMENTED** as **v0.5.4** |
| Evidence | scripted **RW-096** / **RW-097** / F-20260919-56 |
| Release / tag | **none** — Version 5 pack later only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; F-17 fallback *tasks* stay check-less |

## What shipped

- `infer_coding_checks` adds `file_exists` for named README.md / main-module `.py` (RW-096)
- `infer_coding_checks` adds `json_field` for keys the goal names so empty `{}` / alt-schema is not VERIFIED (RW-097)
- PLAN_PROMPT / PLAN_CODING_RETRY ask for the same contracts
- Infer cap 6→8 / merge cap 8→10 so the new contracts fit
- Exhausted retries still `_fallback(obj)` — goal-only, cap 7, no checks (F-17)

## Quality gates (this branch)

Isolated homes `/tmp/rad-g47-gate` (doctor, acceptance) and `/tmp/rad-g47-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.4 |
| `python3 -m pytest -q` | **PASS** 641 passed in 13.03s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g47-gate/acceptance/20260919-071646_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g47-rw/realworld/20260919-071646_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16 / `Budget.tool_calls` 60 |
| False DONE | **0** |
| Release / tag | **none** |

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-7 implemented as v0.5.4.** **No GitHub Release / tag.** Gen5 is not started.

---

# Cycle 32 — Scope G4-7 coding artifact completeness; stay 0.5.3 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `b8b67a43a00a8bdba164b5a4c7e250a35db30122` (merge PR #45; package **0.5.3**)
**Package at start:** `0.5.3`
**This branch:** `cursor/g4-7-artifact-completeness-scope-f6ee` — package **0.5.3** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–095 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks. GitHub Release **Version 5** / tag **v0.5.2** still covers G4-1–G4-3 only.

## Why this cycle

**G4-5** shipped as **v0.5.3** (PR #45; scripted RW-094 / RW-095). Version 5
pack remains GitHub Release **v0.5.2** (G4-1 / G4-2 / G4-3). G4-1 closed
pause. G4-2 closed safe resume. G4-3 closed the operator-use path. G4-5
closed plan-*structure* (near-JSON recover + compact coding retry). Both
live free paths remain **paused**. Live E1–E3 confirmation is **deferred**.
F-17 stays closed.

Investigate-first after G4-5: the highest-leverage **product** gap is
not MCP, not a cost dashboard, and not another “wait for live
confirmation” theme. G4-3 already shipped the campaign playbook. Running
it is operator work when a provider recovers — not a package bump while
NIM / OpenRouter free stay paused. Cycle 24 residual Class B after
fallback PLAN is **incomplete package artifacts** (RW-081 empty `{}`
summary + SyntaxError test; RW-085 / RW-086 missing README/tests +
alt-schema summary). `infer_coding_checks` already contracts
`json_valid` / test `shell_ok` / `file_line_count` — not named
README.md / analyzer.py `file_exists`, not `json_field` for required
keys. Empty `{}` is valid JSON. False DONE **0**. G4-4 / G4-6 **ids
kept** (no hole / no live-use data). New id **G4-7**.

## Alternatives considered

| candidate | decision |
|---|---|
| Coding artifact completeness / named package-file contracts | **Recommended next (G4-7 / v0.5.4).** Evidence-backed (RW-081 / RW-085 / RW-086). Scriptable without a recovered brain. F-17 stays closed. Does not invent Class A for 403/429 |
| Extensibility / MCP (G4-4) | No measured hole. Already first-class. **Id kept** |
| Cost/budget reporting (G4-6) | Dashboard without Version 5 live-use data. G4-2 already surfaces last Class C + Retry-After. Free remaining-quota not in API until 429. **Id kept** |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted |
| Live confirmation of Version 5 / G4-5 path | G4-3 playbook already ships. Gates remain paused. Operator campaign when a provider recovers — not a new product theme |
| Residual Class B “11B quality / free-model thrash” as a grab-bag | Thrash Class A patched or F-44 **NOT CONFIRMED**. G4-7 is the contract slice, not “make 11B pass” |

## Code findings (lightweight; no patch)

| existing | role | gap vs post-G4-5 residual |
|---|---|---|
| `infer_coding_checks` | `json_valid` / test `shell_ok` / `file_line_count` (cap 6) | Named README.md / analyzer.py get no `file_exists`; named summary keys get no `json_field` |
| `codingloop` repair | broken JSON / failing tests insert one repair | `{}` is valid JSON — odd schema (RW-081 / RW-086) does not trip `json_valid` |
| `Planner._fallback` (F-17) | clause-split, cap 7, no checks | Do not add checks to fallback *tasks* |
| G4-5 `_json_obj` + `PLAN_CODING_RETRY` | near-JSON recover / compact retry | **Closed** scripted (RW-094 / RW-095). Live confirmation deferred |
| `rad health` + CAMPAIGN_PLAYBOOK | operator wait/rotate/resume/run | Closed for G4-3. Residual live campaign is operator work |
| `rad connect` / MCP | already first-class | No measured hole (G4-4) |
| `rad cost` | paid 14-day spend | No live use data (G4-6) |

## Decision

| item | value |
|---|---|
| Package | **0.5.3** (no 0.5.4) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-5 shipped** as **v0.5.3**. **Version 5 pack** still **v0.5.2** (G4-1–G4-3). **G4-7 listed, not accepted** |
| Recommended next v0.5.4 candidate | **G4-7** — coding artifact completeness / named package-file contracts (see ROADMAP). **Not** accepted here |
| Other candidates | G4-4 extensibility (not next — no hole); G4-6 cost/budget (waits on live use data) |
| Next product work | Waits for an accepted v0.5.4 theme |
| Packing | Merge-only. **No per-slice GitHub Release.** Pack again only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; F-17 stays closed |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g47-scope-gate` (doctor, acceptance) and `/tmp/rad-g47-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.3 |
| `python3 -m pytest -q` | **PASS** 624 passed in 12.24s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g47-scope-gate/acceptance/20260919-070854_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g47-scope-rw/realworld/20260919-070855_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.3** (no bump) |
| Release / tag | **none** — Version 5 packing doctrine |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-7 is scoped so a later accept can strengthen named-file / JSON-field *objective* contracts — not a live PASS.
4. G4-7 is listed, not accepted.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-5 implemented as v0.5.3.** **G4-7 implemented as v0.5.4.** Stay
**0.5.4**. Gen5 is not started.

---

# Cycle 31 — G4-5 fallback / LLM plan quality; v0.5.3 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `1fa2320d97d30488c9740666821662df53adf5ef` (merge PR #44; package **0.5.2**)
**Package at start:** `0.5.2`
**This branch:** `cursor/g4-5-llm-plan-quality-bdee` — package **0.5.3**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — G4-5 accepted + implemented. RW-058–093 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

## Why this cycle

G4-5 was scoped on Cycle 30 / PR #44 and **accepted**. Version 5 pack
closed pause / resume / operator-use (G4-1–G4-3 as v0.5.0–v0.5.2). The
remaining measured gap on a working product path was Class B PLAN
`source=fallback` (RW-085 / RW-086: attempts=2, clause-carved tasks, not
a coding graph). F-17 stays closed (do not add checks to fallback
*tasks*). Investigate-first: `_json_obj` greedy `{.*}` discarded fenced /
trailing-comma / tasks-array / extra-brace near-JSON; coding-goal retry
re-sent the full `PLAN_PROMPT`.

## Decision

| item | value |
|---|---|
| Package | **0.5.2 → 0.5.3** |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-5 ACCEPTED + IMPLEMENTED** as **v0.5.3** |
| Evidence | scripted **RW-094** / **RW-095** / F-20260919-55 |
| Release / tag | **none** — Version 5 pack later only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; F-17 fallback *tasks* stay check-less |

## What shipped

- `_json_obj` recovers markdown-fenced JSON, trailing commas, a top-level tasks array, and the first balanced object (RW-094)
- Coding-goal retries use compact `PLAN_CODING_RETRY` instead of the full planner prompt (RW-095)
- Exhausted retries still `_fallback(obj)` — goal-only, cap 7, no checks (F-17)

## Quality gates (this branch)

Isolated homes `/tmp/rad-g45-gate` (doctor, acceptance) and `/tmp/rad-g45-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.3 |
| `python3 -m pytest -q` | **PASS** 624 passed in 11.46s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g45-gate/acceptance/20260919-070010_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g45-rw/realworld/20260919-070011_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.3** |
| Release / tag | **none** — Version 5 packing doctrine |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-5 is scripted plan-quality, not a live PASS.
4. G4-4 / G4-6 remain later candidates.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-1** as v0.5.0. **G4-2** as v0.5.1. **G4-3** as v0.5.2.
**G4-5 implemented as v0.5.3.** **No GitHub Release / tag.** Gen5 is not started.

---

# Cycle 30 — Scope G4-5 fallback / LLM plan quality; stay 0.5.2 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `d534bd30384e9f582ca6c08562a6b2cd555fb793` (merge PR #43; package **0.5.2**; GitHub Release **Version 5** / tag **v0.5.2**)
**Package at start:** `0.5.2`
**This branch:** `cursor/g4-5-plan-quality-scope-7793` — package **0.5.2** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–093 are **not rewritten**.
**Release:** **none** — Version 5 packing doctrine: merge-only; pack again only when Sanath asks.

## Why this cycle

**Version 5 pack** shipped as GitHub Release **v0.5.2** (title **Version 5**;
tip `d534bd3`; G4-1 / G4-2 / G4-3). G4-1 closed pause (v0.5.0 / RW-089).
G4-2 closed safe resume (v0.5.1 / RW-090 / RW-091). G4-3 closed the
operator-use path (v0.5.2 / RW-092 / RW-093). Both live free paths remain
**paused**. Live E1–E3 confirmation is **deferred**. Cycle 29 left G4-4 /
G4-5 / G4-6 as later candidates.

Investigate-first after the pack: the highest-leverage **product** gap is
not MCP, not a cost dashboard, and not another “wait for live
confirmation” theme. G4-3 already shipped the campaign playbook. Running
it is operator work when a provider recovers — not a package bump while
NIM / OpenRouter free stay paused. The remaining measured gap on a
working product path is Class B PLAN `source=fallback` (RW-085 / RW-086
attempts=2, newline-carved tasks, not a coding graph). Cycle 24 listed
this first among residual Class B; Cycles 26–28 deferred it so
production-scale Class C doctrine could ship. That pack is done. F-17
stays closed (do not add checks to fallback *tasks*).

## Alternatives considered

| candidate | decision |
|---|---|
| Fallback / LLM plan quality | **Recommended next (G4-5 / v0.5.3).** Evidence-backed (RW-085 / RW-086). Scriptable without a recovered brain. F-17 stays closed. Does not invent Class A for 403/429 |
| Extensibility / MCP (G4-4) | No measured hole. Already first-class (`rad connect`, skill manifests, acceptance handshake). README remote-MCP hardening is an idea, not a row |
| Cost/budget reporting (G4-6) | Dashboard without Version 5 live-use data. G4-2 already surfaces last Class C + Retry-After. Free remaining-quota not in API until 429 |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). RW-059 showed 12→24 still exhausted |
| Live confirmation of Version 5 path | G4-3 playbook already ships. Gates remain paused. Operator campaign when a provider recovers — not a new product theme |

## Code findings (lightweight; no patch)

| existing | role | gap vs post-Version-5 pack |
|---|---|---|
| `Planner.plan` retries | JSON nudge then `_fallback` (default 2 attempts) | Live RW-085/086: `attempts=2` `source=fallback` — LLM never produced a coding graph |
| `Planner._fallback` (F-17) + E2 | clause-split, cap 7, no checks; independent files unchained | Still not a coding plan. Do not add checks to fallback *tasks* |
| `infer_coding_checks` | objective-level contracts | Fallback *tasks* stay check-less; execution dies on weak clause tasks |
| `rad health` + CAMPAIGN_PLAYBOOK | operator wait/rotate/resume/run | Closed for G4-3. Residual live campaign is operator work, not this theme |
| `rad connect` / MCP | already first-class | No measured hole (G4-4) |
| `rad cost` | paid 14-day spend | No live use data (G4-6) |

## Decision

| item | value |
|---|---|
| Package | **0.5.2** (no 0.5.3) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **Version 5 pack shipped** (G4-1 / G4-2 / G4-3 as v0.5.0 / v0.5.1 / v0.5.2). **G4-5 listed, not accepted** |
| Recommended next v0.5.3 candidate | **G4-5** — fallback / LLM plan quality under tight budgets (see ROADMAP). **Not** accepted here |
| Other candidates | G4-4 extensibility (not next — no hole); G4-6 cost/budget (waits on live use data) |
| Next product work | Waits for an accepted v0.5.3 theme |
| Packing | Merge-only. **No per-slice GitHub Release.** Pack again only when Sanath asks |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g45-scope-gate` (doctor, acceptance) and `/tmp/rad-g45-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.2 |
| `python3 -m pytest -q` | **PASS** 608 passed in 11.67s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g45-scope-gate/acceptance/20260919-065055_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g45-scope-rw/realworld/20260919-065056_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.2** (no bump) |
| Release / tag | **none** — Version 5 packing doctrine |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-5 is scoped so a later accept can strengthen LLM-plan vs fallback *structure* — not a live PASS.
4. G4-5 is listed, not accepted.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**Version 5 pack** shipped (G4-1 / G4-2 / G4-3). Recommended next
**G4-5** listed, not accepted. Stay **0.5.2**. Gen5 is not started.

---

# Cycle 29 — G4-3 live-use campaign / operator workflow; v0.5.2 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `2eb3450a4288097a4938d42704105f353ebef1c7` (merge PR #42; package **0.5.1**)
**Package at start:** `0.5.1`
**This branch:** `cursor/g4-3-live-use-campaign-323a` — package **0.5.2**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — G4-3 accepted + implemented. RW-058–091 are **not rewritten**.
**Release:** **none** — Version 5 packs later as one release. Do not tag `v0.5.2`.

## Why this cycle

G4-3 was scoped on Cycle 28 / PR #42 and **accepted**. G4-1 closed pause
(v0.5.0 / RW-089). G4-2 closed safe resume (v0.5.1 / RW-090 / RW-091).
Production still had not **used** that path: last working-inference live
row is RW-086 on v0.4.7; E1–E3 and G4-1/G4-2 never live-confirmed
together. Leftover hole: online `rad doctor` re-pinged chat while last
Class C still blocked (OpenRouter `free-models-per-day`).

## Decision

| item | value |
|---|---|
| Package | **0.5.1 → 0.5.2** |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-3 ACCEPTED + IMPLEMENTED** as **v0.5.2** |
| Evidence | scripted **RW-092** / **RW-093** / F-20260919-54 |
| Release / tag | **none** — Version 5 pack later |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; `free_lock` never silent paid |

## What shipped

- Online `rad doctor` / `scan_provider_health` skip chat while last Class C blocks (unknown `key_fp` included)
- `rad doctor --force` / `rad health --force` to re-probe after a believed recovery
- `rad health`: wait / rotate / resume / run next-action + campaign playbook
- Controller Class C persist keeps key fingerprint / Retry-After

## Quality gates (this branch)

Isolated homes `/tmp/rad-g43-gate` (doctor, acceptance) and `/tmp/rad-g43-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.2 |
| `python3 -m pytest -q` | **PASS** 608 passed in 11.12s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g43-gate/acceptance/20260919-064217_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g43-rw/realworld/20260919-064218_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.2** |
| Release / tag | **none** |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-3 is the *operator path to try*, not a live PASS.
4. G4-4 / G4-5 / G4-6 remain later candidates.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-1** as v0.5.0. **G4-2** as v0.5.1. **G4-3 implemented as v0.5.2.**
**No GitHub Release / tag.** Gen5 is not started.

---

# Cycle 28 — Scope G4-3 live-use campaign / operator workflow; stay 0.5.1 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `2d4c8b6dd2e75b191a33913b93eb7d77acd3be6b` (merge PR #41; package **0.5.1**, tag **v0.5.1**)
**Package at start:** `0.5.1`
**This branch:** `cursor/g4-3-live-use-campaign-f0df` — package **0.5.1** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–091 are **not rewritten**.

## Why this cycle

G4-2 shipped as **v0.5.1** (scripted RW-090 / RW-091): doctor READY only
for inference-entitled brains; last Class C persists; resume live-gates
403/429 until an entitled brain recovers. G4-1 remains **v0.5.0**
(scripted RW-089). Both live free paths remain **paused**. Live E1–E3
confirmation is **deferred**. Cycle 27 left G4-3 / G4-4 / G4-5 as
unnamed later candidates.

Investigate-first after G4-2: the highest-leverage **production-scale**
gap is not residual Class B plan quality, not MCP, and not a cost
dashboard. G4-1 closed **pause**. G4-2 closed **safe resume**. The
operating loop’s next step is **use**. Last working-inference live row
is RW-086 on **v0.4.7**. E1–E3 and G4-1/G4-2 have never been
live-confirmed together. Leftover operator-workflow hole: `rad doctor`
(online) re-pings chat while last Class C still blocks; resume already
skips that re-burn (RW-091). On OpenRouter the ping would count against
`free-models-per-day` (RW-086).

Cycle 26’s G4-3 grab-bag (longer workloads + cost/budget) splits:
longer-horizon *use* takes **G4-3**; cost/budget reporting parks as
**G4-6**.

## Alternatives considered

| candidate | decision |
|---|---|
| Live-use campaign / operator workflow | **Recommended next (G4-3 / v0.5.2).** Evidence-backed. Doctor skip-blocked is scriptable. Live E1–E3 confirmation needs an entitled brain. Does not invent Class A for 403/429 |
| Larger workload / longer-horizon *product* | E1–E3 already shipped scripted. Caps 16/60 stay closed (A1 / F-21). *Use* is G4-3, not a new executor |
| Extensibility / MCP (G4-4) | No measured hole. Already first-class |
| Fallback / LLM plan quality (G4-5) | Residual Class B. Not the production-scale gate. Needs the recovered brain G4-3 is meant to use |
| Cost/budget reporting (now G4-6) | Dashboard without use data. G4-2 already surfaces last Class C + Retry-After |

## Code findings (lightweight; no patch)

| existing | role | gap vs post-G4-2 |
|---|---|---|
| `Doctor.c_providers` | READY only if inference-entitled | Online scan does not pass `skip_blocked_inference`. Doctor re-pings chat while last Class C blocks |
| `evaluate_live_gate` | resume skip-blocked | Closed for resume (RW-091). Never live-used on v0.5.1 |
| E1 / E2 / E3 | scripted leftover dispatch | Live not confirmed (RW-084/085/086). Missing **use**, not a missing slice |
| `rad cost` | paid 14-day spend | Free remaining-quota not in API until 429 (G4-6) |
| `Planner._fallback` (F-17) | clause-split, no checks | Residual Class B (G4-5), not this theme |

## Decision

| item | value |
|---|---|
| Package | **0.5.1** (no 0.5.2) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-1 shipped** as **v0.5.0**. **G4-2 shipped** as **v0.5.1**. **G4-3 listed, not accepted** |
| Recommended next v0.5.2 candidate | **G4-3** — live-use campaign / operator workflow (see ROADMAP). **Not** accepted here |
| Other candidates | G4-4 extensibility (not next — no hole); G4-5 fallback plan quality; G4-6 cost/budget (was Cycle 26 G4-3 reporting half) |
| Next product work | Waits for an accepted v0.5.2 theme |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g43-scope-gate` (doctor, acceptance) and `/tmp/rad-g43-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.1 |
| `python3 -m pytest -q` | **PASS** 596 passed in 12.03s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g43-scope-gate/acceptance/20260919-062646_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g43-scope-rw/realworld/20260919-062643_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.1** (no bump) |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-3 is scoped so a later accept can run the live campaign and close the doctor re-ping hole — not a live PASS.
4. G4-3 is listed, not accepted.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-1** as v0.5.0. **G4-2 implemented as v0.5.1.** Recommended next
**G4-3** listed, not accepted. Stay **0.5.1**. Gen5 is not started.

---

# Cycle 27 — G4-2 live-gate resume / provider health; v0.5.1 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `d67917a76f9a9926f097bb7a168cf466a1385036` (merge PR #40; package **0.5.0**)
**Package at start:** `0.5.0`
**This branch:** `cursor/g4-2-live-gate-resume-2449` — package **0.5.1**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — G4-2 accepted + implemented. RW-058–089 are **not rewritten**.

## Why this cycle

G4-2 was scoped on Cycle 26 / PR #40 and **accepted**. G4-1 closed pause
(v0.5.0 / RW-089). Production still had no safe live-use path: RW-084
doctor READY on catalog-alive + chat 403; RW-086 429 with no durable
last-Class-C / Retry-After surface; resume would re-hit the same 403.

## Decision

| item | value |
|---|---|
| Package | **0.5.0 → 0.5.1** |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-2 ACCEPTED + IMPLEMENTED** as **v0.5.1** |
| Evidence | scripted **RW-090** / **RW-091** / F-20260919-53 |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim; `free_lock` never silent paid |

## What shipped

- `rad/health.py`: catalog vs inference probe; last Class C persist; live-gate
- Doctor READY only for inference-entitled brains (RW-084 shape)
- `rad objective resume` refuses to re-burn the same 403/429 (RW-086 shape)
- Retry-After in `class_c_next_steps` / `provider_health.json` when present

## Quality gates (this branch)

Isolated homes `/tmp/rad-g42-gate` (doctor, acceptance) and `/tmp/rad-g42-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.1 |
| `python3 -m pytest -q` | **PASS** 596 passed in 11.22s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g42-gate/acceptance/20260919-061250_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g42-rw/realworld/20260919-061257_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.1** |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-2 is the *safe path to try*, not a live PASS.
4. G4-3 / G4-4 / G4-5 remain later candidates.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-1** as v0.5.0. **G4-2 implemented as v0.5.1.** Gen5 is not started.

---

# Cycle 26 — Scope G4-2 live-gate resume / provider health; stay 0.5.0 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `d194b8ffc763fc00ad58273e5dd8f0203442041d` (merge PR #39; package **0.5.0**, tag **v0.5.0**)
**Package at start:** `0.5.0`
**This branch:** `cursor/g4-2-live-gate-scope-8c56` — package **0.5.0** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–089 are **not rewritten**.

## Why this cycle

G4-1 shipped as **v0.5.0** (scripted RW-089): Class C before MODEL;
`needs_user` pause; free-first rotation; `free_lock` never silent paid.
Both live free paths remain **paused**. Live E1–E3 confirmation is
**deferred**. Cycle 25 left G4-2 / G4-3 as unnamed later candidates.

Investigate-first after G4-1: the highest-leverage **production-scale**
gap is not residual Class B plan quality and not runbook copy. RW-084
pre-run `rad doctor` providers **READY** (`1 usable: nvidia`) while
`GET /v1/models` **200** and every `chat/completions` **403**. RW-086
worked then died on HTTP **429** `free-models-per-day` with no durable
last-Class-C / retry-after surface. `RouterState.failures` is
in-process only. `rad objective resume` will re-hit the same 403 if
the operator guesses. G4-1 closed **pause**; production still has no
**safe live-use path**.

## Alternatives considered

| candidate | decision |
|---|---|
| Live-gate resume / provider health observability | **Recommended next (G4-2 / v0.5.1).** Evidence-backed. Scriptable. Does not invent Class A for 403/429 |
| Operational runbooks / `needs_user` UX polish | G4-1 already shipped pause text. Residual is copy, not a measured hole |
| Larger workload / longer-horizon (G4-3) | Waits on a recovered inference-entitled brain. Caps 16/60 stay closed |
| Extensibility / MCP (G4-4) | No measured hole. Already first-class |
| Fallback / LLM plan quality (Cycle 24 G4-2 → now G4-5) | Residual Class B. Not the production-scale gate. Needs the recovered brain G4-2 is meant to surface |

## Code findings (lightweight; no patch)

| existing | role | gap vs post-G4-1 |
|---|---|---|
| `Doctor.c_providers` | chain from key / local probe | RW-084 READY on a 403-chat pin. Catalog ≠ inference |
| `probe_local` | local reachable + model list | No cloud inference-health probe |
| `RouterState.failures` | skip Class C this process | Gone after CLI exit |
| `class_c_next_steps` | pause copy | Resume *check* missing |
| `Planner._fallback` (F-17) | clause-split, no checks | Residual Class B (G4-5), not this theme |

## Decision

| item | value |
|---|---|
| Package | **0.5.0** (no 0.5.1) |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-1 shipped** as **v0.5.0**. **G4-2 listed, not accepted** |
| Recommended next v0.5.1 candidate | **G4-2** — live-gate resume / provider health observability (see ROADMAP). **Not** accepted here |
| Other candidates | G4-3 longer workload / cost; G4-4 extensibility (not next — no hole); G4-5 fallback plan quality (was Cycle 24 G4-2) |
| Next product work | Waits for an accepted v0.5.1 theme |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch; no live PASS claim |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g42-scope-gate` (doctor, acceptance) and `/tmp/rad-g42-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.0 |
| `python3 -m pytest -q` | **PASS** 583 passed in 13.19s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g42-scope-gate/acceptance/20260919-060115_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g42-scope-rw/realworld/20260919-060115_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.5.0** (no bump) |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. G4-2 is scoped so a later accept can add a safe resume/health path — not a live PASS.
4. G4-2 is listed, not accepted.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-1 implemented as v0.5.0.** Recommended next **G4-2** listed, not
accepted. Stay **0.5.0**. Gen5 is not started.

---

# Cycle 25 — G4-1 live multi-provider Class C doctrine; v0.5.0 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `ffd02a2c13d40cfd189327a72e588d1dfc164ac1` (merge PR #38; package **0.4.9**)
**Package at start:** `0.4.9`
**This branch:** `cursor/g4-1-provider-doctrine-c2b7` — package **0.5.0**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — smallest Class C / free-first doctrine. RW-058–088 are **not rewritten**.

## Why this cycle

PR #38 scoped Gen4 and listed G4-1 as the recommended first v0.5.0
candidate (not accepted). Sanath accepted G4-1 as a real build: Class C
403/429 was being re-read as product work (RW-084 MODEL retries; RW-086
429 tool burn). Investigate-first confirmed router failover and AUTH
ask_user already existed; the hole was classify order (MODEL before
403), 429 as TRANSIENT retry, and no written rotate/pause doctrine.

## Decision

| item | value |
|---|---|
| Package | **0.4.9 → 0.5.0** |
| Gen3 | **COMPLETE (scripted)** (unchanged). Live E1–E3 **deferred** |
| Gen4 | **IN PROGRESS**. **G4-1 ACCEPTED + IMPLEMENTED** |
| Evidence | scripted **RW-089** / F-20260919-52 |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a Class A patch; no silent paid under free_lock; no live PASS claim |

## Quality gates (this branch)

Isolated homes `/tmp/rad-g41-gate` (doctor, acceptance) and `/tmp/rad-g41-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.5.0 |
| `python3 -m pytest -q` | **PASS** 583 passed in 11.33s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-g41-gate/acceptance/20260919-055207_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-g41-rw/realworld/20260919-055207_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| Package | **0.5.0** |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**. Scripted 403/429 is the G4-1 gate.
4. G4-2 / G4-3 remain candidates.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 4 in progress.**
**G4-1 implemented as v0.5.0.** Gen5 is not started.

---

# Cycle 24 — Scope Gen4 v0.5.x; Gen3 complete (scripted); stay 0.4.9 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `05ea0df302aa6bfd15eccfb84341aeed75d6e1d0` (merge PR #37; package **0.4.9**, tag **v0.4.9**)
**Package at start:** `0.4.9`
**This branch:** `cursor/gen4-v05-scope-450a` — package **0.4.9** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–088 are **not rewritten**.

## Why this cycle

Gen3 themes 1–3 have measured wins on 0.4.x (themes 1–2 live-confirmed;
theme 3 slices A–D used / live-confirmed as recorded; E1/E2/E3 scripted
RW-083 / RW-087 / RW-088; slice F live xxd thrash **CLEARED**). Live
E1–E3 confirmation is **deferred** (NIM Class C paused RW-084; OpenRouter
free paused RW-086 429). Residual Class B remains (fallback PLAN,
incomplete package, free-model thrash). Gen4 had been a one-line
“Production Scale / not started”. This cycle **scopes** it as **planned /
scoped** (not started as a build) and marks Gen3 **complete (scripted)**
with the live-confirmation caveat.

## Code findings (lightweight; no patch)

| existing | role | gap vs measured Gen3-use |
|---|---|---|
| `rad/router.py` free-first chain | local → free RR → paid; 401/403 skip | Live runs pin one free brain; 403/429 paused the loop instead of a written rotate/pause doctrine |
| `recovery.py` 429/403 classes | TRANSIENT/NETWORK vs AUTH; `switch_model` exists | Mid-run 429 still burned tools (RW-086). Class C stays Class C |
| `rad cost` | paid 14-day spend | Free-tier quota invisible; no production rollup of tool/model budgets |
| `Planner._fallback` (F-17) + E2 | clause-split, no checks on fallback *tasks* | Live RW-085/086 `source=fallback` — residual Class B after E1–E3 |
| MCP + `rad provider add` | already first-class; acceptance handshakes MCP | No measured hole. Not a first theme |

## Decision

| item | value |
|---|---|
| Package | **0.4.9** (no 0.5.0) |
| Gen3 | **COMPLETE (scripted)**. Live E1–E3 confirmation **deferred** |
| Gen4 | **PLANNED / SCOPED**. Not accepted. Not implemented |
| Recommended first v0.5.0 candidate | **G4-1** — live multi-provider / free-provider production doctrine (see ROADMAP). **Not** accepted here |
| Other candidates | G4-2 fallback/LLM plan quality; G4-3 operational scale; G4-4 extensibility (not first — already in tree) |
| Next product work | Waits for an accepted v0.5.0 theme |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; Class C is not a product patch |

## Quality gates (this branch)

Isolated homes `/tmp/rad-gen4-scope-gate` (doctor, acceptance) and `/tmp/rad-gen4-scope-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.9 |
| `python3 -m pytest -q` | **PASS** 569 passed in 11.62s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-gen4-scope-gate/acceptance/20260919-053618_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-gen4-scope-rw/realworld/20260919-053622_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| Package | **0.4.9** (no bump) |
| Live this patch | not re-run; suite `live_nim` **BLOCKED** (Class C) |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1/E2/E3 are scripted only. Live confirmation **deferred**.
3. Both live free paths remain **paused**.
4. G4-1 is listed, not accepted.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 complete (scripted).**
**Generation 4 planned / scoped.** Stay **0.4.9**. Gen5 is not started.

---

# Cycle 23 — Budget-aware retry stop (E3); v0.4.9 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `f5cda30dcbb6a2ff96465ea20997f384a5f53f4a` (merge PR #36; package **0.4.8**, tag **v0.4.8**)
**Package at start:** `0.4.8`
**This branch:** `cursor/e3-budget-aware-retry-stop-ac23` — package **0.4.9**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — Gen3 theme 3 slice E3. RW-058–087 are **not rewritten**.

## Why this cycle

E1 leftover reserve + E2 independent later files already exist. After a
failed first attempt, when remaining tools were `reserve + 1`, recovery
still started a retry or inserted a repair of the stuck task and spent
the spare tool E1 was holding for later READY work (RW-085/086-style
thrash).

Investigate-first: E1 `TaskYield` already stops mid-think when
`rem <= reserve`. The hole is the retry/repair *decision*, not a missing
executor check and not “E1 already covers this.” Smallest patch:
`should_yield_for_leftover` (`rem < leftover_tool_reserve + TOOLS_PER_TASK`)
on the existing `_should_yield` / RETRYING-dispatch boundary. Solo tasks
still retry. Unlimited budgets do not yield. Executor reserve stays
1-per-later-task.

## What changed

| piece | change |
|---|---|
| `should_yield_for_leftover` (`budgetplan.py`) | Stop retry/repair when leftover headroom is below `TOOLS_PER_TASK` |
| `Controller._should_yield` / RETRYING start | Reuse that helper; yield instead of another stuck-task attempt |
| Package | **0.4.8 → 0.4.9** |

## Decision

| item | value |
|---|---|
| Package | **0.4.9** |
| E3 | **ACCEPTED + IMPLEMENTED** (scripted RW-088) |
| E1 / E2 live | **N** — not confirmed on RW-084/085/086 |
| Live text_analyzer@12 | **not** claimed PASS |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign |

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw088-gate` (doctor, acceptance) and `/tmp/rad-rw088-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.9 |
| `python3 -m pytest -q` | **PASS** 569 passed in 14.44s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw088-gate/acceptance/20260919-052039_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw088-rw/realworld/20260919-052035_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.4.9** |
| Live this patch | **not re-run** — not a live PASS claim |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL (fallback plan, incomplete package, tools=12).
2. E1 leftover-budget yield is still **not live-confirmed**.
3. E2 / E3 are scripted only (RW-087 / RW-088). Live fallback chain not re-run (OpenRouter free loop paused; NIM paused).
4. Live OpenRouter free-model loop is **paused** (HTTP 429 `free-models-per-day`).
5. Live NIM loop remains **paused** (RW-084 Class C).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice E3 **IMPLEMENTED** as **v0.4.9** (scripted RW-088). E1/E2 remain scripted.
Package is **0.4.9**. Gen4–5 are not started.

---

# Cycle 22 — Independent later package files (E2); v0.4.8 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `3607678a5d82fa2c80a03a256a8d57afa7c1fc86` (merge PR #35; package **0.4.7**)
**Package at start:** `0.4.7`
**This branch:** `cursor/e2-independent-later-files-889b` — package **0.4.8**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product — Gen3 theme 3 slice E2. RW-058–086 are **not rewritten**.

## Why this cycle

Live RW-085/086: PLAN `source=fallback` carved the goal into a linear
`depends_on` chain. Later package-file tasks stayed PENDING (0 attempts)
while an early task burned leftover tools. E1 leftover reserve is 0 when
later tasks wait on the in-flight one. `optional` only unblocks after
FAILED/BLOCKED/CANCELLED, not while RETRYING.

Investigate-first: the hole is fallback *emission* (`depends_on=[prev]` on
every clause), not a missing scheduler primitive and not “E1 already covers
this.” Smallest patch: empty `depends_on` on independent file-write clauses.
Consume/verify/read still chains. Explicit LLM chains are not rewritten.
F-17 stays closed (goal-only split, cap 7, no checks).

## What changed

| piece | change |
|---|---|
| `independent_file_clause` (`planner.py`) | Distinct file-write clauses vs run/verify/read consume |
| `Planner._fallback` | Empty `depends_on` on independent later file writes |
| `PLAN_PROMPT` | Independent package-file writes must use empty `depends_on` |
| Package | **0.4.7 → 0.4.8** |

## Decision

| item | value |
|---|---|
| Package | **0.4.8** |
| E2 | **ACCEPTED + IMPLEMENTED** (scripted RW-087) |
| E1 live | **N** — not confirmed on RW-084/085/086 |
| Live text_analyzer@12 | **not** claimed PASS |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign |

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw087-gate` (doctor, acceptance) and `/tmp/rad-rw087-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.8 |
| `python3 -m pytest -q` | **PASS** 559 passed in 10.41s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw087-gate/acceptance/20260919-050812_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw087-rw/realworld/20260919-050809_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.4.8** |
| Live this patch | **not re-run** — not a live PASS claim |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL (fallback plan, incomplete package, tools=12).
2. E1 leftover-budget yield is still **not live-confirmed**.
3. E2 is scripted only (RW-087). Live fallback chain not re-run (OpenRouter free loop paused; NIM paused).
4. Live OpenRouter free-model loop is **paused** (HTTP 429 `free-models-per-day`).
5. Live NIM loop remains **paused** (RW-084 Class C).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice E2 **IMPLEMENTED** as **v0.4.8** (scripted RW-087). E1 remains scripted.
E3 stays a candidate. Package is **0.4.8**. Gen4–5 are not started.

---

# Cycle 21 — Record live OpenRouter RW-086; pause free-model loop; stay 0.4.7 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `850aaf9c3a931a5ba119bdbb6ec73ae4a6fa73e9` (merge PR #34; package **0.4.7**, tag **v0.4.7**)
**Package at start:** `0.4.7`
**This branch:** `cursor/rw086-live-docs-89ad` — package **0.4.7** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs only (live RW-086 + pause pointers). No product code. RW-058–085 are **not rewritten**.

## Why this cycle

Live gate after v0.4.7 / scripted RW-086 (xxd ENVIRONMENT Class A). Operator
retested RW-085-shape ASCII-tree `text_analyzer/` at `--max-tasks 8
--max-tools 12`, Needle **OFF**, on **openrouter** /
`nvidia/nemotron-3.5-lightning:free` (tag **v0.4.7** / `850aaf9c`). Run
**FAIL** `needs_user` @ tools **12/12**, `$0`. xxd Class A ENVIRONMENT thrash
from RW-085 **CLEARED** (0 `xxd`/`hexdump`; 0 ENVIRONMENT; 0 repair-insert;
host still missing `xxd`; model used `sha256sum` + `hashlib` / `cat -A`).
E1 leftover-budget yield **not live** (0 TaskYield; task1 COMPLETED; task2
attempts=1 sequential, not leftover-budget yield). Residual Class **B+C**
(fallback PLAN / incomplete package + late HTTP **429**
`free-models-per-day`).

Caveat: this trajectory did not emit a live missing-`xxd` exit-127 for the
v0.4.7 classifier to re-label. Evidence is **absence of thrash** vs RW-085;
scripted RW-086 / PR #34 remains the positive unit evidence.

Operator decision (2026-09-19): **pause** live OpenRouter free runs until
`free-models-per-day` resets. Live NIM loop remains **paused** (Class C).

## What changed

| piece | change |
|---|---|
| Ledger / matrix | live RW-086 **FAIL** recorded (F-20260919-49); scripted RW-086 / F-48 preserved |
| ROADMAP / README | last live-use → RW-086; OpenRouter free-model loop **paused**; NIM still Class C paused |
| Package | **0.4.7** (no bump) |
| Product code | **unchanged** |

## Decision

| item | value |
|---|---|
| Package | **0.4.7** (no bump) |
| xxd Class A thrash | **CLEARED** this trajectory (not live) |
| E1 live | **N** — not confirmed on live RW-086 |
| Residual | **B+C** (fallback PLAN / incomplete package + 429) |
| Live OpenRouter free loop | **PAUSED** until `free-models-per-day` resets |
| Live NIM loop | remains **paused** (RW-084 Class C) |
| Live text_analyzer@12 | **not** claimed PASS |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; stay 0.4.7 |

## Live facts (operator report only)

| item | value |
|---|---|
| Home / obj | `/tmp/rad_prod_rw086_81609c3b` / `obj_e1949b8f` |
| Provider / model | **openrouter** / `nvidia/nemotron-3.5-lightning:free` |
| Status | `needs_user` — tool budget 12 exhausted; task2 RETRYING after MODEL_FAILURE (429) |
| Tools / models / retries | **12/12** / **7.0/80** / **1.0/6** |
| PLAN | `source=fallback` attempts=2; 4 newline-carved tasks |
| Money | **`$0`** |
| Disk | `text_analyzer/` only; input sha256 `bf69eb73…`; `test_analyzer.py` absent; README absent; summary alt schema |
| Wall | 2026-09-19 IST 10:13:07–10:23:22 (~615s wall; usage `seconds≈417.8`); exit 2 |
| False DONE | **0** |
| xxd / ENVIRONMENT / repair | **0 / 0 / 0** |

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw086-gate` (doctor, acceptance) and `/tmp/rad-rw086-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.7 |
| `python3 -m pytest -q` | **PASS** 547 passed in 10.97s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw086-gate/acceptance/20260919-045809_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw086-rw/realworld/20260919-045810_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.4.7** (no bump) |
| Live this patch | **not re-run** — live RW-086 recorded from operator report; not a live PASS claim |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL (fallback plan, incomplete package, tools=12).
2. E1 leftover-budget yield is still **not live-confirmed** (RW-084 Class C; RW-085/086 fallback chain).
3. Live OpenRouter free-model loop is **paused** (HTTP 429 `free-models-per-day`).
4. Live NIM loop remains **paused** (RW-084 Class C).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice F **IMPLEMENTED** as **v0.4.7** (scripted RW-086; live RW-086 xxd thrash
**CLEARED**). E1 remains scripted. Package stays **0.4.7**. Gen4–5 are not started.

---

# Cycle 20 — Record live OpenRouter RW-085; xxd ENVIRONMENT Class A CONFIRMED; v0.4.7 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `54fc739` (merge PR #33; package **0.4.6**, docs SHA after RW-084)
**Package at start:** `0.4.6`
**This branch:** `cursor/rw085-xxd-environment-40c4` — package **0.4.7**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs (RW-085) + product patch (optional checksum ENVIRONMENT). RW-058–084 are **not rewritten**.

## Why this cycle

Live gate after RW-084 Class C. Operator retested RW-081-shape ASCII-tree
`text_analyzer/` at `--max-tasks 8 --max-tools 12`, Needle **OFF**, on
**openrouter** / `nvidia/nemotron-3.5-lightning:free` (tag **v0.4.6** /
`8f09be58`). Run **FAIL** `needs_user` @ tools **11/12**, `$0`. Class C vs
RW-084 **cleared**. E1 leftover-budget yield **not live** (0 TaskYield;
fallback PLAN attempts=2; later tasks 0 attempts). Residual Class **B**
(fallback plan, wrong summary, missing README, failing tests) plus live
`xxd: not found` exit 127 classified **ENVIRONMENT_FAILURE → repair**.

Investigate-first: missing optional `xxd` is the same family as pip `-r`
file-not-found and premature-test No-such-file — model/tool-choice on a
working python host, not a broken RAD environment. **Class A CONFIRMED.**

## What changed

| piece | change |
|---|---|
| `is_missing_optional_checksum_utility` (`codingloop.py`) | Tight helper: `xxd` / `hexdump` / `sha256sum` (and close variants) not-found / exit 127 |
| `classify()` (`recovery.py`) | Skip ENVIRONMENT for that helper; genuine `python`/`pip`/`gcc` command-not-found stays ENVIRONMENT |
| `is_first_task_thrash_noise` | Same helper — verifier does not fail a check-passing task |
| `PLAN_PROMPT` | Do not call xxd/hexdump for stdlib coding; use hashlib |
| Package | **0.4.6 → 0.4.7** |

## Decision

| item | value |
|---|---|
| Package | **0.4.7** |
| Class A `xxd` ENVIRONMENT | **CONFIRMED** (theme 3 slice F) |
| E1 live | **N** — not confirmed on RW-085 |
| Class C vs RW-084 | **cleared** (OpenRouter) |
| Live text_analyzer@12 | **not** claimed PASS |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign |

## Live facts (operator report only)

| item | value |
|---|---|
| Home / obj | `/tmp/rad_prod_rw085_15d26f58` / `obj_3181e63d` |
| Provider / model | **openrouter** / `nvidia/nemotron-3.5-lightning:free` |
| Status | `needs_user` — ENVIRONMENT repair exhausted → replan → NEEDS_USER |
| Tools / models / retries | **11/12** / **14.0/80** / **2.0/6** |
| PLAN | `source=fallback` attempts=2; 4 newline-carved tasks |
| Money | **`$0`** |
| Disk | `text_analyzer/` only; input sha256 `bf69eb73…`; README absent; tests exit 1 |
| Wall | 2026-09-19 IST 09:34:38–09:57:47 (~1389s event; usage `seconds≈928.8`); exit 2 |
| False DONE | **0** |

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw085-gate` (doctor, acceptance) and `/tmp/rad-rw085-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.7 |
| `python3 -m pytest -q` | **PASS** 547 passed in 12.22s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw085-gate/acceptance/20260919-043709_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw085-rw/realworld/20260919-043710_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.4.7** |
| Live this patch | **not re-run** — not a live PASS claim |

## Remaining limitations

1. Live text_analyzer@12 remains Class B FAIL (fallback plan, quality, tools=12).
2. E1 leftover-budget yield is still **not live-confirmed** (RW-084 Class C; RW-085 fallback chain).
3. Live NIM loop remains **paused** (RW-084 Class C).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice F **IMPLEMENTED** as **v0.4.7**. E1 remains scripted. Gen4–5 are not started.

---

# Cycle 19 — Record live NIM RW-084 Class C; pause live NIM; stay 0.4.6 (2026-09-19)

**Date:** 2026-09-19
**Baseline:** `origin/main` `8f09be5839e25c236349121a4ec77606d0d5ed2d` (merge PR #32; package **0.4.6**, tag **v0.4.6**)
**Package at start:** `0.4.6`
**This branch:** `cursor/rw084-class-c-docs-9f8b` — package **0.4.6** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs only. No `rad/` product change. RW-058–083 are **not rewritten**.

## Why this cycle

Intended live gate for E1 on tag **v0.4.6**. Operator ran RW-081-shape ASCII-tree
`text_analyzer/` at `--max-tasks 8 --max-tools 12`, Needle **OFF**, NIM 11B
intended. Run **BLOCKED Class C** before any tool: HTTP **403 Authorization
failed** on all `chat/completions`; `/v1/models` **200**; tools **0/12**. E1
leftover-budget yield **not live-tested**. Cannot compare E1 vs RW-081 (RW-081
had working inference). False DONE **0**.

## Decision

| item | value |
|---|---|
| Package | **0.4.6** (no bump) |
| Class | **C** — provider/key; not a RAD product defect this run |
| E1 | remains **shipped / scripted** (RW-083). Live gate **deferred** |
| Live NIM loop | **PAUSED** until inference-entitled credentials work on integrate.api. Do not keep retrying keys that list models but fail chat |
| Next live | RW-085 (or next) only after a key that can `chat/completions` |
| Invariants | Needle OFF; caps 16/60; false DONE 0; stay 0.4.6 |

## Live facts (operator report only)

| item | value |
|---|---|
| Home / obj | `/tmp/rad_prod_rw084_3d9cc3ac` / `obj_a8118606` |
| Status | `needs_user` — MODEL_FAILURE → retry×2 → replan → NEEDS_USER |
| Tools / models / retries | **0/12** / **3.0/80** (all 403) / **2.0/6** |
| PLAN | `source=fallback` (LLM plan unavailable); 4 newline-carved tasks |
| Disk | workspace empty; `text_analyzer/` absent |
| Wall | 2026-09-19 IST 08:34:20–08:34:22 (~1.5s; usage `seconds≈0.91`); exit 2 |

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw084-gate` (doctor, acceptance) and `/tmp/rad-rw084-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.6 |
| `python3 -m pytest -q` | **PASS** 530 passed in 10.76s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw084-gate/acceptance/20260919-031510_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw084-rw/realworld/20260919-031511_realworld.json` |
| Needle default | **PASS** (`existing`) — unchanged |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — unchanged |
| Package | **0.4.6** (no bump) |
| Live NIM this patch | **BLOCKED Class C** (RW-084 recorded; loop **paused**) |

## Remaining limitations

1. Live 11B text_analyzer@12 E1 confirmation is **deferred** (Class C).
2. Last working-inference live row remains RW-081 Class B FAIL @ 12/12.
3. Scripted RW-083 remains the E1 unit evidence.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice E1 **IMPLEMENTED** as **v0.4.6** (scripted). Live NIM **paused / Class C
blocked**. Stay **0.4.6**. Gen4–5 are not started.

---

# Cycle 18 — v0.4.6 Gen3 theme 3 slice E1 (task-boundary yield) (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `e8172cca` (merge PR #31; package **0.4.5**)
**Package at start:** `0.4.5`
**This branch:** `cursor/e1-task-boundary-yield-37ad` — package **0.4.6**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** product patch + scripted evidence. RW-058–082 are **not rewritten**.

## Why this cycle

Slice E was **SCOPED / PLANNED** on Cycle 17. This cycle **accepts and implements
E1**: yield a stuck in-flight task at a task boundary and dispatch leftover
tools to later independent READY work via existing `CheckpointManager` +
`Scheduler`. Driver: RW-081 (first task VERIFIED; second burned remaining
tools; later file PENDING; `needs_user` @ 12/12).

## What changed

| piece | change |
|---|---|
| `TaskYield` (`rad/control/budgets.py`) | Distinct from `BudgetExceeded`: leftover tools remain |
| `leftover_tool_reserve` (`budgetplan.py`) | 1 tool per later independent unattempted READY task |
| `Executor.reserve_tools` | Raise `TaskYield` before charging a reserved leftover tool |
| `Controller._drive` / `_yield_task` | Sequential tasks reserve leftover; park `RETRYING` + checkpoint |
| `Scheduler.runnable` | Prefer non-yielded READY work so leftover reaches later files |
| Persistence | Existing `checkpoint.json` / `tasks.json` (`verification.yielded`). No new format |

## Decision

| item | value |
|---|---|
| Package | **0.4.6** |
| Slice E1 | **ACCEPTED + IMPLEMENTED** |
| E2 / E3 | still candidates (linear `depends_on` unchanged) |
| Thrash Class A chase | **Paused** after RW-081 NOT CONFIRMED |
| Live 11B text_analyzer@12 | **not** claimed PASS |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; no cap raise as the fix |

## Quality gates (this branch)

Isolated homes `/tmp/rad-e1-gate` (doctor, acceptance) and `/tmp/rad-e1-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.6 |
| `python3 -m pytest -q` | **PASS** 530 passed in 9.93s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-e1-gate/acceptance/20260918-174516_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-e1-rw/realworld/20260918-174520_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| Package | **0.4.6** |
| Live NIM this patch | not re-run; suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live 11B text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. E1 does not rewrite linear `depends_on` (E2). Chained later files stay unready.
3. Premature-test ENVIRONMENT Class A remains unit-confirmed (RW-080), not live-hit.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice E1 **IMPLEMENTED** as **v0.4.6**. Gen4–5 are not started.

---

# Cycle 17 — Scope Gen3 theme 3 slice E (multi-step checkpoint); stay 0.4.5 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `16b41553` (merge PR #30; package **0.4.5**, tag **v0.4.5** @ `32e9fe87`)
**Package at start:** `0.4.5`
**This branch:** `cursor/gen3-multistep-checkpoint-scope-0f75` — package **0.4.5** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**Kind:** docs / scope only. No `rad/` product change. RW-058–082 are **not rewritten**.

## Why this cycle

Thrash Class A slices A–D shipped (v0.4.2–v0.4.5). Live RW-081 still **FAIL**
`needs_user` @ 12/12; pip/root-pollution Class A **NOT CONFIRMED** (RW-082).
Multi-step checkpoint had been a one-line “planned / later”. This cycle
**scopes** it as Gen3 theme 3 **slice E** (theme-3 remainder, not a new Gen3
theme and not Gen4).

## Code findings (lightweight; no patch)

Crash-resume already exists. Slice E is strengthen/use, not invent:

| existing | role | gap vs live RW-081 |
|---|---|---|
| `rad/control/checkpoints.py` `CheckpointManager` | Save after every task/loop/finish | Does not yield an in-flight stuck task before tools hit 0 |
| `Controller.resume` / restore | Crash and `needs_user` continue; completed tasks never re-run | Human resume (often raised budget) is not the 12-tool intra-run loop |
| `_on_budget` + `_close_already_satisfied` | Honest stop; already-passing OPEN tasks close (RW-081 README) | PENDING later files not yet on disk stay PENDING |
| `Scheduler` + `TaskGraph` (`optional`, `alternatives`, `block_doomed`) | Ready-set after the current task returns | Drive loop stays in `_run_task` until budget death; planner often linear-chains `depends_on` |
| Gen2 v0.3.2 budget-aware planning | Fit the *plan* at PLAN time | No mid-run “this retry consumes the rest; try independent READY work” |

## Decision

| item | value |
|---|---|
| Package | **0.4.5** (no 0.4.6) |
| Slice E | **SCOPED / PLANNED**. Not accepted. Not implemented |
| Recommended first v0.4.6 candidate | **E1** — task-boundary yield / leftover-budget dispatch (see ROADMAP). **Not** accepted here |
| Other candidates | E2 independent later-file `depends_on`; E3 budget-aware retry stop |
| Thrash Class A chase | **Paused** after RW-081 NOT CONFIRMED |
| Next product work | Waits for an accepted checkpoint slice |
| Invariants | Needle OFF; caps 16/60; false DONE 0; no redesign; no cap raise as primary fix; no Class B quality claim |

## Quality gates (this branch)

Isolated homes `/tmp/rad-slicee-gate` (doctor, acceptance) and `/tmp/rad-slicee-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.5 |
| `python3 -m pytest -q` | **PASS** 519 passed in 11.70s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-slicee-gate/acceptance/20260918-172927_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-slicee-rw/realworld/20260918-172928_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| Package | **0.4.5** (no bump) |
| Live NIM this patch | not re-run; suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live 11B text_analyzer@12 remains Class B FAIL. This cycle does not change that.
2. Slice E is scoped only. E1/E2/E3 are candidates.
3. Premature-test ENVIRONMENT Class A remains unit-confirmed (RW-080), not live-hit.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 3 in progress.** Theme 3
slice E **SCOPED / PLANNED**. Stay **0.4.5**. Gen4–5 are not started.

---

# Cycle 16 — RW-081 live v0.4.5 retest + pip/root-pollution Class A **NOT CONFIRMED** (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `32e9fe87` (tag **v0.4.5**, package **0.4.5**)
**Package at start:** `0.4.5`
**This branch:** `cursor/rw081-pip-root-pollution-4319` — package **0.4.5** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–080 are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

## Part A — live use (RW-081)

Live NVIDIA NIM 11B text_analyzer on v0.4.5 (`obj_b6d32fcc`, home
`/tmp/rad_prod_rw081_5a76b128`, `--max-tasks 8 --max-tools 12`, Needle off).
Authoritative facts from the operator report. This agent did not re-run NIM.

| item | value |
|------|--------|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-079 | Still FAIL. Package-joined / `bf69eb73…` / 0 invented DONE held. ENVIRONMENT repair **gone**. mkdir File-exists **live Y**. Premature-test ENVIRONMENT **not live-hit**. Residual → pip/echo + root pollution |
| Disk | 3-line `input.txt` sha256 `bf69eb73…`; package `summary.json` **`{}` valid, empty**; tests **SyntaxError**; README 393 B; **root `analyzer.py`** from `echo >` |
| Repair | **none** (retries=0). First task VERIFIED despite mkdir File-exists. Second task never verified (budget) |
| False DONE | **0** |
| Class | **B** residual (11B/budget). mkdir File-exists Class A **live: Y**. Premature-test ENVIRONMENT **live: N**. Pip/root-pollution Class A **NOT CONFIRMED** |

## Part B — investigate-first (pip thrash + root pollution)

Question: with known `package_dir`, does RAD emit/accept root writes that
disagree with package checks, is there a verifier/recovery hole, and is pip
thrash under stdlib-only goals a control-plane defect beyond PLAN_PROMPT +
v0.4.3?

| probe | result |
|---|---|
| `infer_package_dir` / inferred + LLM objective checks | Still **`text_analyzer/`**; all joined (0 bare). Theme 1 / slice A hold |
| `align_shell_command` on `echo … > analyzer.py` / `pip install -r` | **Unchanged** — only bare `test_*.py` in *check* commands is rewritten |
| `write_file("analyzer.py")` / `echo > analyzer.py` | Lands at **workspace root**. Executor does not remap action paths (models propose) |
| Root `analyzer.py` vs check `text_analyzer/analyzer.py` | **FAILED** — does not satisfy. False DONE **0** |
| Package file present + root echo leftover | Package check **VERIFIED**; package content **unchanged**; leftover is extra disk |
| Hypothetical join of echo redirect into `package_dir` | Would **overwrite** a good package `analyzer.py` with the broken stub. Anti-patch |
| pip `-r` file-not-found classify | Still **not ENVIRONMENT** (v0.4.3). Live RW-081 never reached verify |
| Successful `pip install jsonschema` | Not ENVIRONMENT; not action-noise. Real tool call; ingest-reject still charges budget |
| PLAN_PROMPT | Already **must not pip install** for stdlib-only (v0.4.3). Cosmetic prompt-only is not a bump |
| mkdir File-exists | Still action-noise; **live Y** this run |
| Premature `python …/test_*.py` | Helper still holds; **not live-hit** |
| empty `{}` + missing `json_field` | Still **not VERIFIED** |
| Live RW-081 remaining | pip/echo budget, empty summary, SyntaxError test, root leftover — **Class B** |

**NOT CONFIRMED.** No product patch. Stay **0.4.5**. Tests:
`tests/test_pip_root_pollution_investigation.py`. Ledger F-20260918-43 (B) /
F-20260918-44 (not A). Theme-3 measured win: mkdir File-exists **live Y**.

## What did not change

- Package **0.4.5** (no 0.4.6)
- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–080 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS
- Path-aligned checks (v0.4.0), multi-file contracts (v0.4.1), ASCII-tree
  package_dir (v0.4.2), pip/DONE thrash (v0.4.3), mkdir File-exists (v0.4.4),
  premature-test ENVIRONMENT (v0.4.5) preserved
- Multi-step checkpoint **not** built
- No PLAN_PROMPT-only bump; no action-path remap

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **none proven.** F-20260918-44 pip/root-pollution **NOT CONFIRMED**. |
| **B** | **F-20260918-43** — RW-081 live 11B incompleteness (pip/echo budget, empty summary, SyntaxError test, root leftover). |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw081-gate` (doctor, acceptance) and `/tmp/rad-rw081-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.5 |
| `python3 -m pytest -q` | **PASS** 519 passed in 11.05s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw081-gate/acceptance/20260918-171326_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw081-rw/realworld/20260918-171327_realworld.json` |
| Needle default | **PASS** (`existing`) — asserted in tests |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — asserted in tests |
| False DONE | **PASS** (scripted 0) — asserted in tests |
| Package | **0.4.5** |
| Live NIM this patch | not re-run; RW-081 facts from the operator report. Suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget) on
   text_analyzer@12. This cycle records that mkdir File-exists action-noise is
   live, and that pip/echo + root pollution is not a new control-plane hole.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Multi-step checkpoint is Gen3 theme 3 **slice E**, **SCOPED / PLANNED** in
   Cycle 17 / [ROADMAP.md](ROADMAP.md) (not built; not this patch).
4. Premature-test ENVIRONMENT Class A remains unit-confirmed (RW-080) and was
   **not live-hit** on RW-081.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **v0.4.0** (used through RW-081);
multi-file contracts **v0.4.1** (used through RW-081); theme 3 **planned /
scoped**, slice A **v0.4.2**, slice B **v0.4.3**, slice C **v0.4.4** (**live
Y** RW-081), slice D **v0.4.5** (used RW-081; premature-test path not live-hit),
slice E **SCOPED / PLANNED** (Cycle 17). Stay **0.4.5**. Gen4–5 are not started.

---

# Cycle 15 — RW-079 live v0.4.4 retest + Gen3 theme 3 slice D premature-test ENVIRONMENT / v0.4.5 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `acb61997` (tag **v0.4.4**, package **0.4.4**)
**Package at start:** `0.4.4`
**This branch:** `cursor/rw079-premature-test-env-bc5d` — package **0.4.5**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–078 are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

## Part A — live use (RW-079)

Live NVIDIA NIM 11B text_analyzer on v0.4.4 (`obj_a0781a42`, home
`/tmp/rad_prod_rw079_803109d5`, `--max-tasks 8 --max-tools 12`, Needle off).
Authoritative facts from the operator report. This agent did not re-run NIM.

| item | value |
|------|--------|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-077 | Theme 1 **Y**. Theme 2 **Y**. pip/DONE still **0**. mkdir File-exists **not live-hit** (mkdir succeeded). Same Class B stop. Residual thrash → premature `python …/test_analyzer.py` ENVIRONMENT_FAILURE → repair |
| Disk | 3-line `input.txt` sha256 `bf69eb73…`; package `summary.json` **valid JSON, wrong counts**; tests wrong oracles (`words==9` / `chars==51` vs 13 / 76); README 166 B |
| Repair | ENVIRONMENT_FAILURE → `repair` (premature test No-such-file while directory checks already passed). **Not** mkdir File-exists |
| False DONE | **0** |
| Class | **B** residual (11B/budget). mkdir File-exists Class A **live: N**. Premature-test ENVIRONMENT is Class A (Part C) |

## Part B — investigate-first (premature-test ENVIRONMENT)

Question: should premature `python …/test_*.py` No-such-file be ENVIRONMENT
“missing dependency/file” repair, and should that shell error fail a task
whose explicit directory `file_exists` already passed?

| probe | result |
|---|---|
| classify premature `python3 …/test_analyzer.py` can't-open-file | Pre-patch: `_ENV` matches `no such file` → **ENVIRONMENT_FAILURE** → Repair prerequisite. Matches live RW-079 |
| Recovery | `repair` (“missing dependency/file”) when verifier reports FAILED |
| Pre-patch verifier | directory `file_exists` **passed**; actions **FAILED** (1 premature-test error among write_file successes) → overall **FAILED**. `is_first_task_thrash_noise` did **not** cover python can't-open-file (only DONE + pip-missing-req + mkdir File-exists) |
| Genuine `command not found` / `ModuleNotFoundError` | Still ENVIRONMENT (F-18). Must stay |
| `cat: summary.json: No such file` | Still ENVIRONMENT (F-18 designed path). Must stay |
| Nested `FileNotFoundError` inside a running script | Not this signal (`can't open file '….py'` only). Must stay a real error |
| mkdir File-exists | Still TOOL, still action noise (v0.4.4 / RW-078). Must not regress |
| empty/invalid `summary.json` | Still not VERIFIED (false DONE **0**) |
| Live RW-079 remaining | wrong summary counts, weak tests, tools 12/12 — **Class B** residual |

**Class A confirmed** for premature-test ENVIRONMENT. Running a missing
script is sequencing/model error, not a broken host environment (python
exists; the file is agent-authored). Same family as v0.4.3 pip `-r`
file-not-found ENVIRONMENT and v0.4.4 mkdir/DONE action-noise. Live 11B
quality stays Class B. Prompt-only 11B quality is **not** the patch.
Multi-step checkpoint stays planned.

## Part C — product (slice D)

Smallest recovery/verifier patch: skip ENVIRONMENT when CPython cannot
open a `.py` script argument; treat that observation as first-task thrash
noise on the actions check so explicit file/dir checks can still VERIFIED.
PLAN_PROMPT: do not run tests before writing them. Check *kinds* unchanged
(F-26). Fallback *tasks* stay check-less (F-17). Genuine `command not found`
/ `ModuleNotFoundError` still ENVIRONMENT (F-18). mkdir File-exists still
action noise (v0.4.4). Label: **Gen3 theme 3 slice D**.

Does **not** raise `Budget.tool_calls` (60) or `max_plan_tasks` (16). Does
**not** claim live 11B text_analyzer@12 now PASS.

## What changed

- Product: `rad/control/codingloop.py`, `rad/control/recovery.py`,
  `rad/control/verifier.py`, `rad/control/planner.py`
- Tests: `tests/test_premature_test_env.py`
- Docs: ROADMAP Gen3 theme 3 slice D **implemented**; ledger F-41 / F-42;
  matrix RW-079 / RW-080; this cycle
- Package **0.4.4 → 0.4.5**

## What did not change

- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–078 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS
- Path-aligned checks (v0.4.0), multi-file contracts (v0.4.1), ASCII-tree
  package_dir (v0.4.2), pip/DONE thrash (v0.4.3), mkdir File-exists (v0.4.4)
  preserved
- Multi-step checkpoint **not** built

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **F-20260918-42** — premature python test No-such-file classified ENVIRONMENT. Patched. |
| **B** | **F-20260918-41** — RW-079 live 11B incompleteness (wrong summary counts, weak tests, tools=12). |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-v045-gate` (doctor, acceptance) and `/tmp/rad-v045-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.5 |
| `python3 -m pytest -q` | **PASS** 500 passed in 10.64s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v045-gate/acceptance/20260918-165029_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v045-rw/realworld/20260918-165030_realworld.json` |
| Needle default | **PASS** (`existing`) — asserted in tests |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — asserted in tests |
| False DONE | **PASS** (scripted 0) — asserted in tests |
| Package | **0.4.5** |
| Live NIM this patch | not re-run; RW-079 facts from the operator report. Suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget) on
   text_analyzer@12. This release stops premature python test invoke from
   classifying ENVIRONMENT and from failing a check-passing task; it does
   not make 11B complete the package under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Multi-step checkpoint remains a Gen3 theme 3 planned slice (not this patch).
4. mkdir File-exists Class A remains unit-confirmed (RW-078) and was **not
   live-hit** on RW-079.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **v0.4.0** (used RW-071 / RW-073 /
RW-075 / RW-077 / RW-079); multi-file contracts **v0.4.1** (used RW-073 / RW-075 /
RW-077 / RW-079); theme 3 **planned / scoped**, slice A **v0.4.2** (used RW-075 /
RW-077 / RW-079), slice B **v0.4.3** (used RW-077 / RW-079), slice C **v0.4.4**,
slice D **implemented as v0.4.5**.
Gen4–5 are not started.

---

# Cycle 14 — RW-077 live v0.4.3 retest + Gen3 theme 3 slice C mkdir already-exists action noise / v0.4.4 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `99099b8a` (tag **v0.4.3**, package **0.4.3**)
**Package at start:** `0.4.3`
**This branch:** `cursor/rw077-mkdir-file-exists-6e88` — package **0.4.4**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–076 are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

## Part A — live use (RW-077)

Live NVIDIA NIM 11B text_analyzer on v0.4.3 (`obj_3da359c5`, home
`/tmp/rad_prod_rw077_0a8393f8`, `--max-tasks 8 --max-tools 12`, Needle off).
Authoritative facts from the operator report. This agent did not re-run NIM.

| item | value |
|------|--------|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-075 | Theme 1 **Y**. Theme 2 **Y**. Class A pip-ENVIRONMENT + fake-DONE thrash **gone** (0× pip, 0× DONE, no Repair-prerequisite). Same Class B stop. Residual thrash → mkdir File-exists TOOL_FAILURE |
| Disk | 3-line `input.txt` sha256 `bf69eb73…`; package `summary.json` **empty/invalid**; tests wrong oracles (`words==6` / `chars==31` vs 13 / 76); README 16 B |
| Repair | TOOL_FAILURE → `retry_with_hint` (`mkdir text_analyzer` File exists after `write_file` created the tree). **No** ENVIRONMENT. **No** Repair-prerequisite |
| False DONE | **0** |
| Class | **B** residual (11B/budget). v0.4.3 pip/DONE Class A **live-consistent**. mkdir File-exists actions is Class A (Part C) |

## Part B — investigate-first (mkdir File-exists actions)

Question: should `mkdir` File-exists fail a task whose explicit directory
`file_exists` already passed, forcing TOOL_FAILURE retry?

| probe | result |
|---|---|
| classify mkdir File-exists | **TOOL_FAILURE** (v0.4.1 `_ALREADY_EXISTS` skip). **Not** ENVIRONMENT. **No** Repair-prerequisite. Matches live RW-077 |
| Recovery | `retry_with_hint` when verifier reports FAILED |
| Pre-patch verifier | directory `file_exists` **passed**; actions **FAILED** (1 mkdir error among write_file successes) → overall **FAILED**. `is_first_task_thrash_noise` did **not** cover mkdir File-exists (only DONE + pip-missing-req) |
| Genuine `command not found` / `ModuleNotFoundError` | Still ENVIRONMENT (F-18). Must stay |
| mkdir Permission denied | Still a real action error. Must stay |
| empty/invalid `summary.json` | Still not VERIFIED (false DONE **0**) |
| Live RW-077 remaining | empty `summary.json`, weak tests, thin README, tools 12/12 — **Class B** residual |

**Class A confirmed** for mkdir already-exists action noise. Same family as
v0.4.3 DONE/pip noise: RAD must not fail a check-passing task on an
idempotent create error. Live 11B quality stays Class B. Prompt-only 11B
quality is **not** the patch. Multi-step checkpoint stays planned.

## Part C — product (slice C)

Smallest verifier patch: treat mkdir/create already-exists as first-task
thrash noise on the actions check so explicit file/dir checks can still
VERIFIED. PLAN_PROMPT: do not mkdir a path write_file already created.
Check *kinds* unchanged (F-26). Fallback *tasks* stay check-less (F-17).
mkdir already-exists still **not** ENVIRONMENT (v0.4.1). Label: **Gen3
theme 3 slice C**.

Does **not** raise `Budget.tool_calls` (60) or `max_plan_tasks` (16). Does
**not** claim live 11B text_analyzer@12 now PASS.

## What changed

- Product: `rad/control/codingloop.py`, `rad/control/recovery.py`,
  `rad/control/verifier.py`, `rad/control/planner.py`
- Tests: `tests/test_mkdir_already_exists_actions.py`
- Docs: ROADMAP Gen3 theme 3 slice C **implemented**; ledger F-39 / F-40;
  matrix RW-077 / RW-078; this cycle
- Package **0.4.3 → 0.4.4**

## What did not change

- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–076 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS
- Path-aligned checks (v0.4.0), multi-file contracts (v0.4.1), ASCII-tree
  package_dir (v0.4.2), pip/DONE thrash (v0.4.3) preserved
- Multi-step checkpoint **not** built

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **F-20260918-40** — mkdir File-exists failing a check-passing task. Patched. |
| **B** | **F-20260918-39** — RW-077 live 11B incompleteness (empty summary.json, weak tests, tools=12). |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-v044-gate` (doctor, acceptance) and `/tmp/rad-v044-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.4 |
| `python3 -m pytest -q` | **PASS** 484 passed in 9.12s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v044-gate/acceptance/20260918-163149_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v044-rw/realworld/20260918-163146_realworld.json` |
| Needle default | **PASS** (`existing`) — asserted in tests |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — asserted in tests |
| False DONE | **PASS** (scripted 0) — asserted in tests |
| Package | **0.4.4** |
| Live NIM this patch | not re-run; RW-077 facts from the operator report. Suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget) on
   text_analyzer@12. This release stops mkdir File-exists from failing a
   check-passing task; it does not make 11B complete the package under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Multi-step checkpoint remains a Gen3 theme 3 planned slice (not this patch).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **v0.4.0** (used RW-071 / RW-073 /
RW-075 / RW-077); multi-file contracts **v0.4.1** (used RW-073 / RW-075 /
RW-077); theme 3 **planned / scoped**, slice A **v0.4.2** (used RW-075 /
RW-077), slice B **v0.4.3** (used RW-077), slice C **implemented as v0.4.4**.
Gen4–5 are not started.

---

# Cycle 13 — RW-075 live v0.4.2 retest + Gen3 theme 3 slice B first-task thrash / v0.4.3 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `feb8a4ec` (tag **v0.4.2**, package **0.4.2**)
**Package at start:** `0.4.2`
**This branch:** `cursor/rw075-first-task-thrash-3a1c` — package **0.4.3**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–074 are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

## Part A — live use (RW-075)

Live NVIDIA NIM 11B text_analyzer on v0.4.2 (`obj_476d5f0e`, home
`/tmp/rad_prod_rw075_c2d7abdd`, `--max-tasks 8 --max-tools 12`, Needle off).
Authoritative facts from the operator report. This agent did not re-run NIM.

| item | value |
|------|--------|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-073 | Theme 1 **Y** (disk/tasks **and** obj-checks package-joined; no root pollution). Theme 2 **Y**. Same Class B stop. Recovery flipped PERMISSION → ENVIRONMENT (pip) |
| Disk | 3-line `input.txt` sha256 `bf69eb73…`; package `summary.json` **missing**; tests wrong oracles (`words==6` / `characters==31` vs 13 / 76) |
| Repair | ENVIRONMENT → Repair prerequisite (4× `pip install -r` missing `requirements.txt`); then TOOL unknown `DONE:`. Budget gone before analyzer/summary tasks |
| False DONE | **0** |
| Class | **B** residual (11B/budget). ASCII-tree obj-check join **live-confirmed**. First-task pip/DONE is Class A (Part C) |

## Part B — investigate-first (first-task thrash)

Question: should missing `requirements.txt` from `pip install -r` be
ENVIRONMENT “missing dependency” repair, and should an invented tool named
`DONE` fail a task whose machine checks already passed?

| probe | result |
|---|---|
| `pip install -r text_analyzer/requirements.txt` file-not-found | Pre-patch: `_ENV` matches `No such file` → ENVIRONMENT → Repair prerequisite. Same family as RW-071 mkdir already-exists |
| Genuine `command not found` / `ModuleNotFoundError` | Still ENVIRONMENT (F-18). Must stay |
| mkdir already-exists mixed noise | Still **not** ENVIRONMENT (v0.4.1) |
| `cat: summary.json: No such file` | Still ENVIRONMENT (F-18 designed path) |
| Unknown tool `DONE` / `DONE: …` | Already errors (`unknown tool`); false DONE **0**. Pre-patch: actions check fails even when `file_line_count` passed → first task FAILED → later tasks starve |
| Live RW-075 remaining | missing `summary.json`, weak tests, tools 12/12 — **Class B** residual |

**Class A confirmed** for first-task thrash. RAD should not treat
stdlib-only pip-missing-requirements as an environment prerequisite, and
should not fail a check-passing task on a protocol DONE tool. Live 11B
quality stays Class B. Prompt-only 11B quality is **not** the patch.
Multi-step checkpoint stays planned.

## Part C — product (slice B)

Smallest recovery/verifier patch: skip ENVIRONMENT when pip could not open
the requirements file; ignore invented DONE tools and pip-requirements noise
on the actions check so explicit file/json/shell checks can still VERIFIED.
PLAN_PROMPT: no pip-requirements for stdlib-only; DONE is not a tool.
Check *kinds* unchanged (F-26). Fallback *tasks* stay check-less (F-17).
Label: **Gen3 theme 3 slice B**.

Does **not** raise `Budget.tool_calls` (60) or `max_plan_tasks` (16). Does
**not** claim live 11B text_analyzer@12 now PASS.

## What changed

- Product: `rad/control/codingloop.py`, `rad/control/recovery.py`,
  `rad/control/verifier.py`, `rad/control/planner.py`, `rad/tools.py`
- Tests: `tests/test_first_task_thrash.py`
- Docs: ROADMAP Gen3 theme 3 slice B **implemented**; ledger F-37 / F-38;
  matrix RW-075 / RW-076; this cycle
- Package **0.4.2 → 0.4.3**

## What did not change

- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–074 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS
- Path-aligned checks (v0.4.0), multi-file contracts (v0.4.1), ASCII-tree
  package_dir (v0.4.2) preserved
- Multi-step checkpoint **not** built

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **F-20260918-38** — first-task thrash (pip-missing-requirements ENVIRONMENT + DONE-as-tool). Patched. |
| **B** | **F-20260918-37** — RW-075 live 11B incompleteness (missing summary.json, weak tests, tools=12). |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-v043-gate` (doctor, acceptance) and `/tmp/rad-v043-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.3 |
| `python3 -m pytest -q` | **PASS** 472 passed in 11.30s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v043-gate/acceptance/20260918-160450_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v043-rw/realworld/20260918-160457_realworld.json` |
| Needle default | **PASS** (`existing`) — asserted in tests |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — asserted in tests |
| False DONE | **PASS** (scripted 0) — asserted in tests |
| Package | **0.4.3** |
| Live NIM this patch | not re-run; RW-075 facts from the operator report. Suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget) on
   text_analyzer@12. This release stops first-task pip/DONE thrash; it does
   not make 11B complete the package under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Multi-step checkpoint remains a Gen3 theme 3 planned slice (not this patch).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **v0.4.0** (used RW-071 / RW-073 /
RW-075); multi-file contracts **v0.4.1** (used RW-073 / RW-075); theme 3
**planned / scoped**, slice A **v0.4.2** (used RW-075), slice B **implemented
as v0.4.3**. Gen4–5 are not started.

---

# Cycle 12 — RW-073 live v0.4.1 retest + Gen3 theme 3 scoped + ASCII-tree package_dir / v0.4.2 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `387bd83a` (tag **v0.4.1**, package **0.4.1**)
**Package at start:** `0.4.1`
**This branch:** `cursor/rw073-theme3-5ac1` — package **0.4.2**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–072 are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

## Part A — live use (RW-073)

Live NVIDIA NIM 11B text_analyzer on v0.4.1 (`obj_d8bd898a`, home
`/tmp/rad_prod_rw073_46da6971`, `--max-tasks 8 --max-tools 12`, Needle off).
Authoritative facts from the operator report. This agent did not re-run NIM.

| item | value |
|------|--------|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-071 | Theme 1 **Y** (disk/tasks; no root pollution). Theme 2 **Y** (contracts + PERMISSION not ENVIRONMENT; correct 3-line `bf69eb73…`). Same Class B stop |
| Disk | 3-line `input.txt` sha256 `bf69eb73…`; package `summary.json` **missing**; tests lack count assertions |
| Repair | PERMISSION → `retry_with_hint` (mkdir exists then `rm -rf` blocked; fake `DONE` tool). **No** ENVIRONMENT Repair-prerequisite insert |
| False DONE | **0** |
| Class | **B** residual (11B/budget). ASCII-tree obj-check paths are Class A (Part C), not this live stop |

## Part B — Gen3 theme 3 plan (docs)

Update ROADMAP Gen3 theme 3 from not-started / later to **planned / scoped**:

- Longer-horizon / multi-step reliability under tight budgets
- Evidence: RW-073 burns 12 tools on first-task retries (permission / DONE tool)
  before later package tasks run
- Candidate sub-themes: (1) progress past first-task thrash without wasting
  budget on blocked `rm -rf` / unknown DONE tool; (2) ASCII-tree `package_dir`
  for objective inferred checks (slice A — Class A, this change); (3)
  multi-step checkpoint so later files still get attempts when early task
  burns retries

Entry rule: themes 1–2 measured (done). Build only with an accepted first
slice. Remaining slices (1) and (3) stay planned — do **not** invent a
long-horizon redesign.

## Part C — investigate-first (ASCII-tree `infer_package_dir`)

Question: should RAD join objective inferred checks the same way as task
checks for ASCII-tree layouts (`text_analyzer/` + `├── file`)?

| probe | result |
|---|---|
| `infer_package_dir` on RW-073 ASCII tree | **None** (pre-patch). Needs `under text_analyzer/` or two+ `text_analyzer/foo` mentions |
| `infer_coding_checks` on that tree | **emitted** bare `summary.json` + `input.txt` lines=3 + `python3 test_analyzer.py` (pre-patch) |
| Same goal with `under text_analyzer/` | `text_analyzer/`; contracts already package-prefixed |
| LLM RW-073 plan (prefixed task checks + `file_min_bytes` README) | merge added **bare** inferred contracts next to prefixed LLM objective checks (pre-patch) |
| word_counter / single `pkg/foo.py` / `sources/` + root `answer.md` / dash-list / `docs/` tree | still **None** (must stay None) |
| Live RW-073 remaining | missing `summary.json`, weak tests, tools 12/12 on permission / fake DONE — **Class B** residual |

**Class A confirmed** for ASCII-tree package-layout detection. RAD should
join inferred (and LLM root-only) objective checks the same way as
`under pkg/`. Live 11B quality / first-task thrash stay Class B (remaining
theme-3 slices, later). Prompt-only 11B quality is **not** the patch.

## Part D — product (slice A)

Smallest detector expansion in `infer_package_dir`: `pkg/` on its own line
followed by two or more box-drawing / `|--` children. Join uses the existing
`align_checks` path. Check *kinds* unchanged (F-26). Fallback *tasks* stay
check-less (F-17). Label: **theme-1 follow-up / Gen3 theme 3 slice A**.

Does **not** raise `Budget.tool_calls` (60) or `max_plan_tasks` (16). Does
**not** claim live 11B text_analyzer@12 now PASS.

## What changed

- Product: `rad/control/codingloop.py` (`_ascii_tree_package_dir`)
- Tests: `tests/test_ascii_tree_package_dir.py`
- Docs: ROADMAP Gen3 theme 3 **planned / scoped**, slice A **implemented**;
  ledger F-35 / F-36; matrix RW-073 / RW-074; this cycle
- Package **0.4.1 → 0.4.2**

## What did not change

- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–072 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS
- Path-aligned checks (v0.4.0) and multi-file contracts (v0.4.1) preserved
- Remaining theme-3 slices (first-task thrash, checkpoint) **not** built

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **F-20260918-36** — ASCII-tree `infer_package_dir` miss. Patched. |
| **B** | **F-20260918-35** — RW-073 live 11B incompleteness (missing summary.json, weak tests, tools=12 on permission / fake DONE). |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-v042-gate` (doctor, acceptance) and `/tmp/rad-v042-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.2 |
| `python3 -m pytest -q` | **PASS** 457 passed in 9.45s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v042-gate/acceptance/20260918-152358_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v042-rw/realworld/20260918-152404_realworld.json` |
| Needle default | **PASS** (`existing`) — asserted in tests |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 — asserted in tests |
| False DONE | **PASS** (scripted 0) — asserted in tests |
| Package | **0.4.2** |
| Live NIM this patch | not re-run; RW-073 facts from the operator report. Suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget) on
   text_analyzer@12. This release joins ASCII-tree objective checks; it does
   not make 11B complete the package under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Longer-horizon first-task thrash and multi-step checkpoint remain Gen3
   theme 3 planned slices (not this patch).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **v0.4.0** (used RW-071 / RW-073);
multi-file contracts **v0.4.1** (used RW-073); theme 3 **planned / scoped**,
slice A **implemented as v0.4.2**. Gen4–5 are not started.

---

# Cycle 11 — RW-071 live v0.4.0 retest + Gen3 theme 2 multi-file contracts / v0.4.1 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `a8aac8ae` (tag **v0.4.0**, package **0.4.0**)
**Package at start:** `0.4.0`
**This branch:** `cursor/rw071-theme2-multifile-ad3c` — package **0.4.1**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–070 are **not rewritten**. F-17 / F-18 / F-21 / F-26 stay closed.

## Part A — live use (RW-071)

Live NVIDIA NIM 11B text_analyzer on v0.4.0 (`obj_d662224b`, home
`/tmp/rad_prod_rw071_7811425c`, `--max-tasks 8 --max-tools 12`, Needle off).
Authoritative facts from the operator report. This agent did not re-run NIM.

| item | value |
|------|--------|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-069 | Theme 1 **live-confirmed** — path-aligned checks under `text_analyzer/`; **no root pollution**. Same Class B stop |
| Disk | 1-line `input.txt` sha256 `9bf9660f…` (expected 3-line `bf69eb73…`); package `summary.json` present **empty/invalid**; tests `1 != 3` |
| Repair | ENVIRONMENT → Repair prerequisite (mkdir already exists + empty JSON among check noise); 11 `write_file` + 1 `run_shell` |
| False DONE | **0** |
| Class | **B** residual (11B/budget). Path-misalignment Class A **not reproduced** |

## Part B — product (theme 2)

Help multi-file coding objectives fail earlier with useful structure under
tight `--max-tools` without weakening VERIFIED / false DONE=0. Smallest
control-plane addition:

- Merge omitted `json_valid` / `file_line_count` / test `shell_ok` into LLM
  `objective_checks` (kinds never remapped; fallback *tasks* stay check-less)
- `mkdir` / create **already exists** is not ENVIRONMENT — mixed File-exists +
  no-such-file noise gets TOOL/VALIDATION coding repair, not Repair prerequisite
- PLAN_PROMPT: no standalone mkdir; prefer write+verify; exact N-line uses
  `file_line_count`

Does **not** raise `Budget.tool_calls` (60) or `max_plan_tasks` (16). Does
**not** claim live 11B text_analyzer@12 now PASS.

## What changed

- Product: `rad/control/codingloop.py`, `rad/control/planner.py`,
  `rad/control/recovery.py`, `rad/control/verifier.py`
- Tests: `tests/test_multifile_tight_budget.py`
- Docs: ROADMAP Gen3 theme 2 **implemented**; ledger F-33 / F-34; matrix
  RW-071 / RW-072; this cycle
- Package **0.4.0 → 0.4.1**

## What did not change

- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–070 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS
- Path-aligned checks (v0.4.0) preserved

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **F-20260918-34** — weak `file_exists` contracts + already-exists ENVIRONMENT thrash. Patched. |
| **B** | **F-20260918-33** — RW-071 live 11B incompleteness (wrong input, empty summary.json, tools=12). |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-v041-gate` (doctor, acceptance) and `/tmp/rad-v041-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.1 |
| `python3 -m pytest -q` | **PASS** 446 passed in 9.01s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v041-gate/acceptance/20260918-150234_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v041-rw/realworld/20260918-150234_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (scripted 0; suite `false_success` / `needs_user` / `no_loop`) |
| Package | **0.4.1** |
| Live NIM this patch | not re-run; RW-071 facts from the operator report. Suite `live_nim` **BLOCKED** (no keys here) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget) on
   text_analyzer@12. This release strengthens contracts and already-exists
   classification; it does not make 11B complete the package under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Longer-horizon / multi-step reliability is Gen3 theme 3 (later).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **v0.4.0** (used RW-071); multi-file
contracts **implemented as v0.4.1**. Gen4–5 are not started.

---

# Cycle 10 — Gen3 theme 1 path-aligned checks / v0.4.0 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `3f59f8b5` (after PR #23; package **0.3.2**)
**Package at start:** `0.3.2`
**This branch:** `cursor/path-aligned-checks-93f8` — package **0.4.0**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–069 are **not rewritten**. F-17 / F-21 / F-26 stay closed.

## Part A — investigate-first (RW-069 A2)

Question: does RAD incorrectly emit or accept machine checks whose paths
disagree with the planned write layout for multi-file/package objectives?

| probe | result |
|---|---|
| `infer_coding_checks` on `under text_analyzer/` / brace-list | **emitted** root `summary.json` + `python3 test_analyzer.py` (pre-patch) |
| `TEST_FILE_RE` on `text_analyzer/test_analyzer.py` | dropped the package prefix (pre-patch) |
| LLM plan with root `input.txt` + package writes | accepted as written (F-26-style); verifier honestly failed the root path → VALIDATION `retry_with_hint` |
| Verifier cwd / path join | workspace-relative only; no package-dir guess at check time |
| Live RW-069 remaining | wrong 1-line input, missing package `summary.json`, weak tests, tools 12/12 — **Class B** residual |

**Class A confirmed** for emission + acceptance of root-only checks on a named
package layout. Wrong 1-line input / missing summary.json / tools=12 stay
Class B (Gen3 theme 2, later). Prompt-only 11B quality is **not** the patch.

## Part B — product

Join bare check paths (and bare `test_*.py` in `shell_ok`) to the package
directory named by `under pkg/`, `pkg/{…}`, or two-or-more files sharing one
non-`tests` prefix. LLM ingest uses the same join. Check *kinds* unchanged
(F-26). Fallback *tasks* stay check-less (F-17). A single `pkg/foo.py` mention
is not a layout (realworld coding / multi_agent).

## What changed

- Product: `rad/control/codingloop.py`, `rad/control/planner.py`
- Tests: `tests/test_path_aligned_checks.py`
- Docs: ROADMAP Gen3 theme 1 **implemented**; ledger F-32; matrix RW-070; this cycle
- Package **0.3.2 → 0.4.0**

## What did not change

- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–069 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**
- Live 11B text_analyzer **not** claimed PASS

## Class A / B / C (this cycle)

| class | this record |
|---|---|
| **A** | **F-20260918-32** — root-only checks vs package write layout. Patched. |
| **B** | RW-069 residual (wrong input, missing package summary.json, weak tests, tools=12). Theme 2 later. |
| **C** | none proven. `live_nim` may BLOCKED. |

## Quality gates (this branch)

Isolated homes `/tmp/rad-v040-gate` (doctor, acceptance) and `/tmp/rad-v040-rw` (realworld).

| gate | result |
|------|--------|
| `rad version` | **PASS** v0.4.0 |
| `python3 -m pytest -q` | **PASS** 435 passed in 8.60s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v040-gate/acceptance/20260918-144259_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v040-rw/realworld/20260918-144303_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (scripted 0; suite `false_success` / `needs_user` / `no_loop`) |
| Package | **0.4.0** |
| Live NIM this patch | not re-run; RW-069 facts preserved. Suite `live_nim` **BLOCKED** (no keys here) |

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2). **Generation 3
is in progress:** path-aligned checks **implemented as v0.4.0**. Gen4–5 are
not started.

---

# Cycle 9 — RW-068/069 v0.3.2 use campaign + Gen3 v0.4.x scope (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `387776dc` (tag **v0.3.2**, package **0.3.2**)
**Package at start:** `0.3.2`
**This branch:** `cursor/rw068-069-gen3-scope-fa28` — package **0.3.2** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
**No product code. No v0.4.0 implementation.** RW-058–067 are **not rewritten**.

## Part A — live use (RW-068 / RW-069)

Live NVIDIA NIM 11B on v0.3.2. Authoritative facts: operator campaign (this
agent did not re-run NIM). Needle off. Homes isolated per run.

### RW-068 word_counter — PASS

`obj_794fb0b3`, home `/tmp/rad_prod_rw068_09177c89`, `--max-tasks 4 --max-tools 12`.

| item | value |
|---|---|
| Verdict | **PASS** — `completed` / **VERIFIED**. Disk matched; host tests OK (1 test) |
| vs RW-066 | **better plan path** — llm attempts **1** vs fallback attempts **2** |
| PLAN | **source=llm** **attempts=1** (4 tasks with per-task checks) |
| Repair | Gen2 **YES** (`ENVIRONMENT_FAILURE` → `repair`); budget exhausted mid-repair; leftovers CANCELLED because objective checks already satisfied |
| Disk | `word_counter.py` YES; `result.json` valid `{"words": 2}`; `test_word_counter.py` YES; DONE pollution none (tool refused `DONE:` path) |
| Tools | 12/12 exhausted |
| False DONE | **0** |
| Class | **B** residual (11B@12). Simple verified coding loop **stable** on v0.3.2 |

### RW-069 text_analyzer — FAIL

`obj_1d8cc7ed`, home `/tmp/rad_prod_rw069_89512dd9`, `--max-tasks 8 --max-tools 12`.
24-tool follow-up **not run**.

| item | value |
|---|---|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** VERIFIED |
| vs RW-058/059 | Planning healthier (llm/1); **artifact quality still Class B fail** |
| PLAN | **source=llm** **attempts=1** |
| Repair | **retry_with_hint** (`VALIDATION_FAILURE`) — not Gen2 `repair` insert |
| Disk (RAD-at-stop) | package `analyzer.py` / `input.txt` / `test_analyzer.py` / `README.md` YES; package `summary.json` **NO**; wrong 1-line input sha256 `9bf9660f…` (expected 3-line `bf69eb73…`); root layout pollution |
| Tools | 12/12 exhausted |
| False DONE | **0** |
| Class | **B** (same family as RW-058/059). A2 check-path vs write-path **watch**, not proven Class A |

Host re-running package tests can create missing files — report **RAD-at-stop**
tree only (C3). Do not treat the post-run unittest OK as campaign PASS.

## Part B — Gen3 scope (docs only)

Gen3 = Autonomous Agent Maturity (v0.4.x) — more reliable multi-step execution,
recovery, planning, and long-horizon work.

**Status:** **planned / scoped** from this campaign. **Not started** as a build.
Do **not** implement v0.4.0 in this change.

Proposed themes (evidence-backed; priority order):

1. **Path-aligned checks / package layout** — A2 candidate: checks at workspace-root vs writes under package dir (RW-069)
2. **Multi-file coding under tight budgets** — Class B: text_analyzer@12 still fails; optional tools=24 baseline later; efficiency / stronger artifact contracts
3. **Longer-horizon / multi-step reliability** — roadmap Gen3 intent; only after themes 1–2 have measured wins

Entry rules: Gen2 complete (0.3.0–0.3.2) — **DONE**. Enter Gen3 **build** only
after Sanath accepts a first v0.4.0 theme. Class A only when proven; Class B is
not an automatic architecture rewrite. Needle OFF; caps unchanged unless proven
need. Operating loop unchanged.

## What changed

- Docs: RW-068 **PASS** + RW-069 **FAIL** in matrix, ledger (F-30 / F-31), this cycle
- ROADMAP: Gen2 **complete**; Gen3 **planned / scoped** from measured gaps
- Package **unchanged** at **0.3.2**

## What did not change

- Product code
- Package version (no 0.3.3, no 0.4.0)
- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–067 ledger/matrix rows
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- F-17 / F-18 / F-21 / F-26 closed; A1 budget→needs_user **not reopened**

## Class A / B / C (this campaign)

| class | this record |
|---|---|
| **A** | **none proven.** A1 do not reopen. A2 watch (root vs package check paths). A3 DONE refuse already works (RW-068). |
| **B** | **F-20260918-31** — text_analyzer@12 still FAIL (wrong input, missing package summary.json, layout thrash). RW-068 residual tools 12/12 mid-repair. |
| **C** | none (NIM key present on the live lane). |

Ship blocker: **no** Class A ship-blocker proven. Residual is **Class B**
capacity/quality. Highest-value Gen3 entry themes: (1) package-layout /
path-aligned checks, (2) coding efficiency under tight tool budgets or a
calibrated higher bound for multi-file, (3) stronger test/artifact contracts
for multi-file objectives.

## Quality gates (this branch)

Isolated homes `/tmp/rad-rw068-gate` (doctor, acceptance) and `/tmp/rad-rw068-rw` (realworld).

| gate | result |
|---|---|
| `rad version` | **PASS** v0.3.2 |
| `python3 -m pytest -q` | **PASS** 415 passed in 9.10s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance --area docs` | **PASS** 3/3 — `/tmp/rad-rw068-gate/acceptance/20260918-142903_gate.json` |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw068-gate/acceptance/20260918-142912_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw068-rw/realworld/20260918-142913_realworld.json` |
| Live NIM this patch | not re-run; RW-068/069 facts taken from the operator campaign. Suite `live_nim` **BLOCKED** (no keys here) |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (campaign 0; suite `false_success` / `needs_user` / `no_loop`) |
| Package | **0.3.2** — no bump |
| Product code | **unchanged** |

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete**
(v0.2.0–v0.2.3). **Generation 2 is complete** (v0.3.0–v0.3.2; v0.3.2 use
campaign done). **Generation 3 is planned / scoped** (v0.4.x) — not started as
a build. Gen4–5 are not started.

---

# Cycle 8 — RW-066 live NIM + Gen2 / v0.3.2 budget-aware planning (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `50d98e26` (tag **v0.3.1**, package **0.3.1**)
**Package at start:** `0.3.1`
**This branch:** `cursor/rw066-theme3-budget-aware-dcb1` — package **0.3.2**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–065 are **not rewritten**. Scripted theme-2 RW-066 (F-27) is preserved.

## Part A — live use (RW-066)

Live NVIDIA NIM 11B word_counter on v0.3.1 (`obj_e74d9fad`, home
`/tmp/rad_prod_rw066_0b0bb188`, `--max-tasks 4 --max-tools 12`, Needle off).
Authoritative facts: operator report (this agent did not re-run NIM).

| item | value |
|---|---|
| Verdict | **PASS** — `completed` / **VERIFIED**. Disk matched; host tests OK |
| vs RW-065 | **better E2E** — 065 was `needs_user` / tests FAIL |
| PLAN | **source=fallback** **attempts=2** (theme 2 live-confirmed) |
| Repair | Gen2 **YES**; wrote valid `result.json` `{"words": 2}` + counter; budget cut mid further writes |
| Disk | `word_counter.py` YES; `result.json` valid words=2; tests **PASS** (2 OK); pollution none |
| Tools | 12/12 exhausted |
| False DONE | **0** |
| Class | **B** residual (11B plan/coding@12). CANCELLED+VERIFIED when objective checks already satisfied (low urgency; not false DONE) |

## Part B — product (theme 3)

Budget-aware planning: remaining `Budget.tool_calls` is passed into the planner.
A *fat* plan (more tasks than fit at 2 tools/task, **and** more than 3 tasks)
is retried with a JSON budget nudge; the cheaper graph is selected. Exhausted
fallback graphs that are still fat are compacted. LLM graphs are **not**
silently compacted (F-21 leftover-work). A model `DONE:` is never completion.

## Why (evidence cited, not rewritten)

- **RW-059 Case B** — doubling max-tools 12→24 did not complete text_analyzer
- **RW-065 / RW-066** — tools 12/12 exhausted; 066 still VERIFIED via objective checks but cancelled mid-repair
- Theme 3 accepted so plans fit the tool budget rather than thrashing until exhaustion

## What changed

- `rad/control/budgetplan.py` — cost model (`TOOLS_PER_TASK=2`), fat vs small, fallback compact
- `Planner.plan(tool_budget=)` prompt + fat-plan retry (`PLAN_BUDGET_NUDGE`) + cheapest select
- Fallback compact when still fat; F-17 tasks stay check-less
- `PLAN_CREATED` records `tool_budget` / `estimated_tools` / `compacted` / `fit`
- Tests `tests/test_budget_aware_planning.py`
- Package **0.3.1 → 0.3.2**

## What did not change

- F-17 `_fallback(obj)` (goal only, cap 7, no checks; never parses model `raw`)
- F-21 leftover-work (≤3-task LLM graphs may exceed remaining tools)
- F-18 / F-26 closed
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–065 ledger/matrix rows; scripted RW-066 (F-27)
- Live 11B Class B incompleteness is **not** claimed solved
- Intra-task write/test thrash (RW-059 19× `write_file`) is **not** an executor redesign
- Planning LLM calls still not charged to `Budget.model_calls`

## Quality gates (actually run)

Isolated homes `/tmp/rad-v032-gate` (doctor, acceptance) and `/tmp/rad-v032-rw` (realworld).

| gate | result |
|---|---|
| `rad version` | **PASS** v0.3.2 |
| `python3 -m pytest -q` | **PASS** 415 passed in 9.02s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v032-gate/acceptance/20260918-140012_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v032-rw/realworld/20260918-140035_realworld.json` |
| Live NIM this patch | **BLOCKED** (no `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`) — RW-066 live facts taken from the operator report |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (scripted compacted fallback not VERIFIED + suite `false_success` / `needs_user` / `no_loop`) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / intra-task thrash). This release selects a plan that fits N tools; it does not make 11B complete every coding goal under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**. Default plan retries is **1**.
3. RW-066 CANCELLED+VERIFIED UX when objective checks already pass is low-urgency; not patched here.

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete** (v0.2.0–v0.2.3). **Generation 2 is in progress:** verified coding loop **v0.3.0**; plan-timeout resilience **v0.3.1** (used RW-066); budget-aware planning **v0.3.2**. Gen3–5 are not started.

---

# Cycle 7 — Gen2 / v0.3.1 plan-timeout resilience (2026-09-18)


**Date:** 2026-09-18
**Baseline:** `origin/main` `76376a86` (PR #20 merge; package **0.3.0**)
**Package at start:** `0.3.0`
**This branch:** `cursor/plan-timeout-resilience-b79b` — package **0.3.1**
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–065 are **not rewritten**.

## Product

Plan-timeout resilience: a transient LLM plan failure (timeout, empty, malformed,
non-JSON, empty task graph) is retried once (default; hard cap 3) with a
JSON-only nudge **before** `_fallback(obj)`. A recovered plan keeps machine
checks (`source=llm`). Exhausted retries still split `obj.goal` only (F-17:
cap 7, no checks). First-try valid JSON is unchanged (one attempt). A model
`DONE:` is never completion.

## Why (evidence cited, not rewritten)

- **RW-062 / F-22** — nvidia plan timeout → `PLAN_CREATED` `source=fallback` → 7 no-check clause tasks
- **RW-063 / F-17** — fallback is goal clause-split, not model-prose parse (Class A NOT CONFIRMED; contract preserved)
- Theme 2 accepted to reduce how often a *transient* plan failure hits bare fallback

## What changed

- `Planner.plan` bounded retry (`DEFAULT_PLAN_RETRIES=1`, `MAX_PLAN_RETRIES=3`) + `PLAN_RETRY_NUDGE`
- `PLAN_CREATED` records `attempts`
- `plan_retries` readable from `home.cfg` (not in DEFAULTS; same pattern as `max_plan_tasks`)
- Tests `tests/test_plan_timeout_resilience.py`
- Package **0.3.0 → 0.3.1**

## What did not change

- F-17 `_fallback(obj)` (goal only, cap 7, no checks; never parses model `raw`)
- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–065 ledger/matrix rows
- Live 11B Class B incompleteness is **not** claimed fixed
- Budget-aware planning (theme 3) not started
- Planning LLM calls still not charged to `Budget.model_calls` (execution metering unchanged)

## Quality gates (actually run)

Isolated homes `/tmp/rad-v031-gate` (doctor, acceptance) and `/tmp/rad-v031-rw` (realworld).

| gate | result |
|---|---|
| `rad version` | **PASS** v0.3.1 |
| `python3 -m pytest -q` | **PASS** 402 passed in 8.20s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v031-gate/acceptance/20260918-134136_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v031-rw/realworld/20260918-134142_realworld.json` |
| Live NIM | **BLOCKED** (no `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`) |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (scripted fallback after retries not VERIFIED + suite `false_success` / `needs_user` / `no_loop`) |

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model / budget). This release retries a transient plan failure; it does not make 11B complete coding under tools=12.
2. Default planner cap is **16**. Default tool budget is **60**. Default plan retries is **1**.
3. Budget-aware planning is Gen2 theme 3 (later).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete** (v0.2.0–v0.2.3). **Generation 2 is in progress:** verified coding loop **v0.3.0**; plan-timeout resilience **v0.3.1**. Gen3–5 are not started.

---

# Cycle 6 — RW-065 live NIM retest of v0.3.0 + json_valid-on-.py (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `183ff611` (tag **v0.3.0**, package **0.3.0**)
**This branch:** `cursor/rw065-json-valid-class-a-364e` — package **0.3.0** (no bump)
**Architecture:** control plane preserved. Needle stays off. Caps unchanged.
RW-058–064 are **not rewritten**.

## Product use (live)

Live NVIDIA NIM 11B word_counter on v0.3.0 (`obj_efed5285`, home
`/tmp/rad_prod_rw065_ab0919b2`, `--max-tasks 4 --max-tools 12`, Needle off).

| item | value |
|---|---|
| Verdict | **FAIL** — `needs_user` (tools 12/12). **Not** E2E PASS |
| vs RW-062 | **improved** — plan source **llm** (not fallback); Gen2 **repair fired**; valid `result.json` `{"words": 2}`; **no DONE pollution** |
| Disk | `word_counter.py` broken (`TypeError`); `result.json` valid words=2; tests FAIL `NameError`; pollution none |
| False DONE | **0** |
| Class | **B** residual (11B/budget). json_valid-on-.py Class A **NOT CONFIRMED** |

## Class A investigation

Question: planner/control plane incorrectly accept or emit `json_valid` on `.py`
→ false FAILED verify → ENVIRONMENT_FAILURE repair noise?

| # | claim | result |
|---|---|---|
| A | json_valid on `.json` | **OK** (valid) / fail (invalid) |
| B | json_valid on `.py` | fails as not-JSON (honest); isolated recovery **VALIDATION** coding repair, **not** ENVIRONMENT |
| C | inferred coding checks | `json_valid` only on `.json`; `shell_ok` for tests — never json_valid on `.py` |
| Emit | RAD emits json_valid on `.py` | **NO** |
| Accept | LLM json_valid-on-.py kept | **YES** (models propose; no silent remap) |
| Live ENV | caused by json_valid-on-.py | **NO** — shell `No such file` observations (F-18 designed path) |

**NOT CONFIRMED.** No product patch. Stay **0.3.0**. Tests:
`tests/test_json_valid_py_investigation.py`. Ledger F-20260918-25 (B) /
F-20260918-26 (not A).

## What did not change

- Package **0.3.0** (no 0.3.1)
- Needle default `existing` / off
- `max_plan_tasks` **16**
- `Budget.tool_calls` **60**
- False completion **0**
- RW-058–064 rows
- No claim that live 11B word_counter now PASSes

## Quality gates (actually run)

Isolated homes `/tmp/rad-rw065-gate` (doctor, acceptance) and `/tmp/rad-rw065-rw` (realworld).

| gate | result |
|---|---|
| `rad version` | **PASS** v0.3.0 |
| `python3 -m pytest -q` | **PASS** 385 passed in 8.74s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-rw065-gate/acceptance/20260918-133056_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-rw065-rw/realworld/20260918-133057_realworld.json` |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (investigation + suite `false_success` / `needs_user` / `no_loop`) |
| Live NIM this investigation | not re-run; RW-065 facts taken from the operator report. `live_nim` suite item **BLOCKED** (no keys here) |

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). Gen2 theme 1 **used** (RW-065). Residual
Class B. Class A candidate closed **NOT CONFIRMED**. Plan-timeout and budget-aware
planning stay candidates.

---

# Cycle 5 — Gen2 / v0.3.0 verified coding loop (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `02ef2f0c` (PR #18 roadmap; package 0.2.3)
**Package at start:** `0.2.3`
**This branch:** `cursor/verified-coding-loop-e794` — package **0.3.0**
**Architecture:** control plane preserved. No AGI/ASI. Needle stays off.
`docs/ROADMAP.md` is the Gen1–Gen5 operating spine from PR #18; this change implements
the accepted v0.3.0 verified coding loop and updates that file’s status.

## Product

Verified coding loop: coding/verification-shaped objectives drive
write → independent disk checks (`json_valid`, pytest/`shell_ok`) → repair
with the concrete failure until checks pass, or budgets force `needs_user` /
fail honestly. A model `DONE:` is never completion. `DONE:` pollution paths
and files whose body is only a `DONE:` claim are not artifacts.

## Why (evidence cited, not rewritten)

- **RW-058 / F-15 family** — text_analyzer under NIM 11B: tools exhausted, incomplete/invalid artifacts, Class B
- **RW-062 / F-22** — simple word_counter: five files exist but `result.json` invalid `{`; tests FAIL (`6!=2`); pollution `DONE:` fake path; tools 12/12; `needs_user`; false DONE 0
- Class A F-17 fallback and F-18 ENV misclass stay closed (not the product theme)

## What changed

- `rad/control/codingloop.py` — coding-goal detection, pollution helpers, inferred objective checks, broken-artifact repair hints
- Recovery: `json_valid` / `json_field` / `json_min_len` / `shell_ok` / `shell_output` failures insert **one** repair step with stderr / expected vs actual (not ENVIRONMENT; missing `file_exists` still `retry_with_hint`)
- Repair tasks copy the failed task's machine checks and cannot spawn repair-of-repair
- Planner: coding goals get `json_valid` / test `shell_ok` as *objective_checks* when the LLM/fallback emitted none. Fallback **tasks** still have no checks (F-17)
- Tools/verifier/observer refuse `DONE:` pollution paths; pollution-only file bodies are not `file_nonempty` evidence
- Package **0.2.3 → 0.3.0**

## What did not change

- Control plane shape PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER
- Needle default `existing` / off
- `max_plan_tasks` default **16**
- `Budget.tool_calls` default **60**
- False completion remains **0**
- RW-058–063 ledger/matrix rows
- Live 11B Class B incompleteness is **not** claimed fixed

## Quality gates (actually run)

Isolated homes `/tmp/rad-v030-gate2` (doctor, acceptance) and `/tmp/rad-v030-rw2` (realworld). Re-run after rebase onto `origin/main` `02ef2f0` (PR #18 roadmap).

| gate | result |
|---|---|
| `rad version` | **PASS** v0.3.0 |
| `python3 -m pytest -q` | **PASS** 373 passed in 8.37s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v030-gate2/acceptance/20260918-130429_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v030-rw2/realworld/20260918-130429_realworld.json` |
| Live NIM | **BLOCKED** (no `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`) |
| Needle default | **PASS** (`existing`) |
| Caps | **PASS** `max_plan_tasks` 16; `Budget.tool_calls` 60 |
| False DONE | **PASS** (scripted persistent bad + suite `false_success` / `needs_user` / `no_loop`) |

## NIM status

**BLOCKED.** `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent. Live word_counter-like objective was **not** run. Do not fake live results. Offline reconstruction: `test_verified_coding_loop_*` plus `rad realworld --only coding,false_success`.

## Remaining limitations

1. Live NVIDIA NIM on 11B may still fail Class B (model limitation). This release ships the loop, not a stronger brain.
2. Default planner cap is **16**. Default tool budget is **60**.
3. Plan-timeout resilience and budget-aware planning are Gen2 themes 2–3 (later).

## Roadmap pointer

Operating spine: [ROADMAP.md](ROADMAP.md). **Generation 1 is complete** (v0.2.0–v0.2.3). **Generation 2 is in progress:** the verified coding loop is **implemented as v0.3.0** in this change. Gen3–5 are not started. Cycle sections below that record “Evidence for v0.3.0: none” still stand as **control-plane** findings: those rows are not a missing stage; they are the Class B evidence that fed the accepted coding-loop theme.

---

# Cycle 4 — v0.2.3 already live (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` (Merge PR #9 / GitHub Release `v0.2.3`)
**Package at start:** `0.2.3` (`rad/__init__.py`, `pyproject.toml`)
**This branch:** `cursor/cycle4-post-023-7298` — package **0.2.3** (no bump)
**Architecture:** frozen. No AGI/ASI. Needle stays optional/off. Not v0.3.0.

## Release verification

| item | evidence |
|---|---|
| GitHub Release URL | https://github.com/seven0070/rad-agent-/releases/tag/v0.2.3 — **exists**, published 2026-09-18, not draft |
| `origin/main` HEAD | `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` |
| Annotated tag `v0.2.3` | object `4ebb12b` peels to `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` |
| PR #9 | merged (closed) onto main at that SHA |
| `rad.__version__` / `pyproject` | **0.2.3** |
| Verdict | **Release: PASS** — did **not** re-cut, retag, or bump |

## Baseline (re-checked)

| item | evidence |
|---|---|
| Docs on main | `REAL_WORLD_FAILURE_LEDGER.md`, `REAL_WORLD_TASK_MATRIX.md` (through RW-039), `MATURATION_CYCLE_REPORT.md` Cycle 3, ADR-001 |
| NVIDIA keys | **ABSENT** — live NIM **BLOCKED** |
| `RAD_TOOL_ROUTER` | unset; `tool_router` default `existing` |
| `max_plan_tasks` | not in `DEFAULTS`; controller / planner fallback **16** |
| `python -m pytest -q` on this SHA | **328 passed** in 9.01s |

## Tasks executed

See `docs/REAL_WORLD_TASK_MATRIX.md` cycle-4 rows (RW-040–RW-057). Evidence: `/tmp/rad-c4-evidence/campaign.json`.

- Production campaign (control plane, real tools, disk checks): coding (`pkg/tally.py`), two-source research, filesystem sort+jail, log→JSON→digest multi-step, injected `write_file` recovery, crash-resume, false DONE
- Action ramp: 1, 3, 5, 10 planned lot-SKU tasks; 20 sequential *actions* in one task; 20 planned tasks (cap)
- Cap evidence-test: 16-bin labels (fits); 17-bin labels (truncated)
- Grader/verifier parity probe on advertised disk check kinds
- Live NIM probe; Needle default probe
- Scripted `rad realworld` suite re-run as a gate

## Successful / Verified / Failures

| set | result |
|---|---|
| `rad realworld` suite | **10 PASS / 1 BLOCKED / 0 FAIL** |
| Campaign coding / research / filesystem / multi-step | **VERIFIED**, files on disk match hashes |
| Ramp 1 / 3 / 5 / 10 tasks | **VERIFIED** (`lot/lNN.txt` SKU files) |
| Ramp 20 *actions* (one task, 20 `write_file`) | **VERIFIED**, 20/20 (`lot/l20.txt` sha256 `94b5d8fbf6758812`) |
| Ramp 20 *tasks* at default planner cap | **FAIL** — 16/20 files; `max_plan_tasks` default 16. Documented; **not patched** |
| 16 sequential bin labels | **VERIFIED** (RW-055) — cap is not a blocker at exactly 16 |
| 17 sequential bin labels | **FAIL** — 16/17; `bins/b17.txt` absent (RW-056) |
| Injected-fault recovery | **VERIFIED**, 1 tool error, 2 recoveries (`config/limits.json` sha256 `f96a9e62d8b15f53`) |
| Crash-resume | **VERIFIED**, `stage/s1.txt`–`s3.txt` after checkpoint restore |
| False DONE | `needs_user`, `receipt.txt` **absent**, **not** VERIFIED |
| Grader/verifier parity | **PASS** — advertised disk kinds agree |

False completion (VERIFIED without the artifact): **0**.

## Class A / B / C

| class | this cycle |
|---|---|
| **A** | **none.** Advertised disk check kinds (`file_exists`, `file_min_bytes`, `file_contains`, `json_valid`, `json_field`, `json_min_len`, `shell_ok`, `shell_output`) still agree between `Lab._run_grader` and `Verifier.run_check` (RW-057). No 0.2.x bump. |
| **B** | none new. 11B over-decompose remains F-20260918-04. Planner cap at 16 remains a documented architecture guard (RW-054, RW-056), not a product-evidence raise. Needle stays off (F-20260918-06). |
| **C** | **F-20260918-13** — live NIM **BLOCKED** (no `NVIDIA_*` keys). Same condition as F-20260918-07 / F-20260918-10 / F-20260918-12. |

## Fixes

None. Architecture frozen. DONE / VERIFIED rules unchanged. `max_plan_tasks` left at 16. Needle default unchanged. Package stays **0.2.3**.

## `max_plan_tasks=16` findings (evidence-test)

| question | this cycle |
|---|---|
| How often hit? | **2/18** campaign rows: RW-054 (20 planned lot files) and RW-056 (17 planned bin cards). **0/10** useful-work rows (coding, research, filesystem, multi-step, recovery, false DONE, crash-resume, grader probe). |
| Does it block useful work? | **Not for the product-shaped work this cycle.** Tally implementation, two-source stock conflict, inbox sort, log→JSON→digest all used **2 tasks**. Exactly-16 sequential labels **VERIFIED** (RW-055). 17 one-file-per-task labels truncate (RW-056) — that is planner *granularity*, not missing capability: 20 *actions* in one task **VERIFIED** (RW-053). PLAN_PROMPT already says typically 2–6, never more than 16. |
| Planner vs architecture? | Cap is `Planner.max_tasks` (`items[:self.max_tasks]` in `_graph_from`) plus controller `home.cfg.get("max_plan_tasks", 16)`. It is **not** in `DEFAULTS`. Silent drop of tasks 17+ is a runaway-plan guard, not a config product. Raising it would be a convenience, not a measured need. |
| Decision | **Unchanged at 16.** Do not raise without a live-brain objective that cannot be expressed in ≤16 tasks *and* cannot bundle actions. |

## Regression tests

No new code. Full gate commands below were actually run on this branch against package 0.2.3.

## NIM status

**BLOCKED.** `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent. Live Class A retest (artifact-exists → VERIFIED; artifact-missing → not VERIFIED) was **not** run. Offline reconstruction: `overdecompose` + `false_success`. Do not reconstruct from offline.

## Needle status

**Off.** `RAD_TOOL_ROUTER` unset; default `tool_router=existing`. ADR-001 unchanged. Not measured this cycle (no new Needle evidence; previous gold set did not beat existing).

## Security

- Workspace jail held on RW-042 (`../escape.txt` not created).
- No secrets committed or printed.
- Tests still strip `*_API_KEY` / `*_NIM_API_KEY` / `RAD_TOOL_ROUTER`.
- Grep of the tree found only fixture placeholders (`sk-test`, docs `nvapi-…`) and env-var *names*.

## Remaining limitations

1. Live NVIDIA NIM is untested on this VM (Class C).
2. Default planner cap is **16 tasks**. A 17+ sequential one-file-per-task plan is truncated; 20 *actions* inside fewer tasks succeed. Do not raise the default without a measured product need.
3. 11B over-decomposition remains Class B; bounded `--max-tasks` / `--max-tools` is still the mitigation.
4. No OS-level shell sandbox (unchanged).

## Quality gates (actually run)

Isolated home `/tmp/rad-c4-gate`. Only items actually run are marked PASS.

| gate | result |
|---|---|
| GitHub Release `v0.2.3` | **PASS** on `d121c3f` — not re-cut |
| `rad version` | **PASS** v0.2.3 |
| `python -m pytest -q` | **PASS** 328 passed in 9.01s |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-c4-gate/acceptance/20260918-072850_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-c4-gate/realworld/20260918-072856_realworld.json` |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Class A hunt (grader vs verifier) | **PASS** — no new mismatch (RW-057) |
| Secrets in git | **PASS** (inspected; only fixture placeholders in tests) |
| DONE semantics | **PASS** (RW-045, suite `false_success` / `needs_user` / `no_loop`) |
| Architecture freeze | **PASS** |
| `max_plan_tasks` | **PASS** left at 16 (evidence-tested; not raised) |

## Action ramp 1 / 3 / 5 / 10 / 20 (this cycle)

| planned | row | on disk | verified | result | cap hit? | useful-work failure? |
|---|---|---|---|---|---|---|
| 1 task / 1 write | RW-049 | 1/1 `lot/l01.txt` | VERIFIED | **PASS** | no | no |
| 3 tasks / 3 writes | RW-050 | 3/3 | VERIFIED | **PASS** | no | no |
| 5 tasks / 5 writes | RW-051 | 5/5 | VERIFIED | **PASS** | no | no |
| 10 tasks / 10 writes | RW-052 | 10/10 | VERIFIED | **PASS** | no | no |
| 20 *actions* / 1 task | RW-053 | 20/20 `lot/l20.txt` | VERIFIED | **PASS** | no | no |
| 20 *planned tasks* | RW-054 | **16/20** (`l17`–`l20` absent) | FAILED | **FAIL** (expected cap) | **yes** | **no** — stress of one-file-per-task, not a product path |

## Planner hit 16 vs useful work failed because of the cap

These are **not** the same failure.

| | planner hit 16 | useful work failed *because of* the cap |
|---|---|---|
| meaning | `Planner._graph_from` kept `items[:16]`; tasks 17+ never entered the graph | a genuine coding/research/fs/multi-step/recovery objective could not complete unless the cap were raised |
| this cycle | **2 encounters:** RW-054 (20 lot files as 20 tasks), RW-056 (17 bin cards as 17 tasks) | **0** |
| counter-evidence | RW-055: 16 sequential labels **VERIFIED**. RW-053: 20 writes in **one** task **VERIFIED**. RW-040–RW-046: useful work used **1–3 tasks** and **VERIFIED** | no product-shaped row needed >16 tasks or failed for lack of task slots |

Cap encounters: **2**. Actual useful-work failures caused by the cap: **0**. Cap **not raised**.

## Capability gaps (this cycle only)

| gap | class | status |
|---|---|---|
| Live NVIDIA NIM Class A (artifact-exists → VERIFIED; missing → not VERIFIED) | C | **BLOCKED** — no keys (F-20260918-13). Not a RAD hole. |
| 11B over-decomposition | B | **NOT TESTED** live this cycle (same missing keys). Prior F-20260918-04 remains documented; bounded `--max-tasks` / `--max-tools` still the mitigation. |
| Needle as default router | B | **not earned** — default `existing`; not measured this cycle; prior gold set lost to heuristic (F-20260918-06 / ADR-001). |
| `max_plan_tasks=16` truncation of 17+ one-file-per-task plans | architecture guard | encountered; **did not** fail useful work. Leave at 16. |
| False completion | — | **0**. Invariant held (RW-045 + suite `false_success` / `needs_user` / `no_loop`). |
| New controller / verifier / adapter defect | A | **none**. |

No OS-level shell sandbox (unchanged; not newly proven this cycle).

## Final decision gate (this cycle's evidence only)

| # | question | answer |
|---|---|---|
| **A** | Is v0.2.3 stable? | **YES.** Release verified on `d121c3f`. Gates 328 pytest / 50/50 acceptance / 10 realworld PASS + 1 BLOCKED. Campaign useful work **VERIFIED**. False completion **0**. No Class A. Package stays 0.2.3. |
| **B** | Recurring Class A? | **NO this cycle.** Zero new Class A. Prior grader Class A (F-20260918-09, F-20260918-11) stayed fixed (RW-057 parity **PASS**). |
| **C** | Does the 16-task cap prevent useful real-world work? | **NO.** Planner *hit* 16 twice (RW-054, RW-056). Useful work did **not** fail because of the cap. Coding/research/fs/multi-step/recovery used 1–3 tasks. 20 actions in one task **VERIFIED**. |
| **D** | Is 11B still a model limitation? | **NOT TESTED this cycle** (NIM keys absent). Do not treat offline reconstruction as a live 11B result. Prior Class B F-20260918-04 remains on the ledger only. |
| **E** | Has Needle earned reconsidering default? | **NO.** Default `existing`. Not measured. Prior gold set did not beat existing. ADR-001 unchanged. |
| **F** | NIM complete or BLOCKED? | **BLOCKED.** Both `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` absent. Live success/failure Class A not run. |
| **G** | Proven architectural capability gap? | **NO.** Cap-hit ≠ architecture gap. No missing control-plane stage. Models still propose; RAD still decides. |
| **H** | Is v0.3.0 justified yet? | **NO.** Evidence for v0.3.0: **none**. |

## Recommendation

**Outcome A — continue 0.2.x.** Not Outcome B (no Class A patches this cycle). Not Outcome C (no proven gap that justifies designing v0.3.0).

1. Keep shipping and using **v0.2.3** as-is. Do not re-cut the release.
2. Supply `NVIDIA_NIM_API_KEY` before claiming live 11B Class A or closing F-20260918-13.
3. Leave `max_plan_tasks` at **16**.
4. Keep Needle off until a gold-set win on RAD tools.
5. Do **not** start v0.3.0 from this loop.

## Evidence for v0.3.0

**None.** No new validated capability was integrated. Needle stays off. The 16-task cap is an existing architecture guard, not a v0.3.0 gap. Stay on 0.2.x.

---

# Production use (post-Cycle 4) — 2026-09-18

**Date:** 2026-09-18 (IST ~13:39–13:41 for the live-NIM attempt)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.

These runs are operator production evidence **after** Cycle 4. They do not rewrite Cycle 4's
Cloud Agent gates (that VM still had no NIM keys; F-20260918-13 remains the cycle-4 BLOCKED
live-NIM retest).

## What was run

Two `rad objective run` attempts of a production text_analyzer layout on v0.2.3.

1. **RW-058a** — no brain. Home `/tmp/rad_prod_text_analyzer_f3cc7950`, `obj_442301c7`.
   **BLOCKED** Class C (`MODEL_FAILURE`: no NVIDIA/other keys / no local engine).
   7 planned / 1 attempted / 0 completed; tools 0/12; workspace empty; false DONE **0**.
   Same condition family as F-20260918-08 / F-20260918-13.
2. **RW-058** — live NIM. Home `/tmp/rad_prod_text_analyzer_live_a787512c`, `obj_4e219224`.
   Provider nvidia / `meta/llama-3.2-11b-vision-instruct` (NIM key present; Class C closed
   for this attempt). Objective: `text_analyzer/{analyzer.py,input.txt,summary.json,test_analyzer.py,README.md}`;
   exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12`. Status `needs_user` /
   **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete.

## Disk (attempt 2)

- `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`
- `analyzer.py` computes counts
- `test_analyzer.py` byte-identical to `analyzer.py` (0 tests)
- README present
- `text_analyzer/summary.json` **MISSING**
- workspace-root `summary.json` had correct counts `{lines:3,words:13,characters:76}` (wrong path)
- layout pollution at workspace root

Attempt 2: plan 5 tasks; 1 attempted (verification FAILED, 2 attempts), 4 PENDING;
tools 12/12 exhausted; model calls 7/80; wall ~103s.

## Class A / B / C

| class | this production use |
|---|---|
| **A** | **none.** RAD stopped at the tool budget; false DONE **0**; verifier did not rubber-stamp. No 0.2.x patch. Package stays 0.2.3. |
| **B** | **F-20260918-15** (RW-058) — 11B limitation: tool spam / incomplete layout / duplicated "tests" / path confusion. Same family as F-20260918-04, now live production evidence. User chose stop; no resume. Bounded `--max-tasks 8 --max-tools 12`. |
| **C** | **F-20260918-14** (RW-058a) — no brain. Same missing-key / no-engine family as F-20260918-08 / F-20260918-13. Closed for attempt 2 (key present). |

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- `max_plan_tasks` cap **16** unchanged (this run used `--max-tasks 8`).
- **No v0.2.4** from this (no Class A fix).
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** Live 11B incompleteness is Class B (model), not a missing control-plane stage.

---

# Controlled tool-budget experiment — RW-059 vs RW-058 (2026-09-18)

**Date:** 2026-09-18 (IST ~14:02–14:04 for RW-059)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Docs-only record. No RAD code change. RW-058 is preserved exactly as historical
evidence (incomplete layout at `--max-tools 12`).

## Controlled comparison

Same production text_analyzer objective; same 11B NIM model; same `--max-tasks 8`;
Needle `existing` / off. The independent variable is `--max-tools` 12 vs 24.

| | RW-058 | RW-059 |
|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` |
| objective | `obj_4e219224` | `obj_e1419520` |
| `--max-tools` | 12 | 24 |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 |
| tools | 12/12 | 24/24 (`write_file` 19, `run_shell` 5) |
| model calls | 7/80 | 25/80 |
| status | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** |
| disk | `summary.json` missing under `text_analyzer/` (correct counts at workspace root, wrong path) | all five files under `text_analyzer/`; `summary.json` invalid JSON + wrong counts; tests FAIL `13!=6` |
| `input.txt` | sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` | same |

Interpretation: tool-budget hypothesis **Case B** — 24 did **not** suffice. Both
runs exhausted the budget. Extra tools got the five paths onto disk but not a
passing result.

## Class A / B / C

| class | this experiment |
|---|---|
| **A** | **not patched.** Suspected candidates **open/investigate** only: fallback planner splitting multiline objective newlines into spurious tasks (F-20260918-17); recovery `ENVIRONMENT_FAILURE` misclassification burning tool budget (F-20260918-18). Do **not** claim fixed. No v0.2.4 from this record. |
| **B** | **F-20260918-16** (12→24 still FAIL); **F-20260918-19** (invalid JSON summary, wrong counts, tests `13!=6`). RW-058 **F-20260918-15** remains the historical 12-tool layout failure. |
| **C** | none new (NIM key present for both live attempts). |

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- Default max-tools **unchanged** (24 was this run’s `--max-tools` only).
- Cap **16** unchanged.
- **No v0.2.4** unless a later confirmed Class A fix.
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** Case B on the tool-budget hypothesis is not a missing control-plane stage
and does not justify designing v0.3.0.

---

# Research + artifact — RW-060 vs text_analyzer (2026-09-18)

**Date:** 2026-09-18 (IST ~14:25–14:27 for RW-060)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Docs-only record. No RAD code change. RW-058 / RW-059 are preserved exactly as
historical text_analyzer evidence. Class A candidates from RW-059 stay parked
(not this record).

## Short comparison

Same 11B NIM model (`meta/llama-3.2-11b-vision-instruct`); same `--max-tasks 8`;
Needle `existing` / off. RW-060 is a **research + artifact** objective, not a
coding layout. Tool budget for this run was `--max-tools 16` (not a default raise).

| | RW-058 (coding) | RW-059 (coding, extra tools) | RW-060 (research + artifact) |
|---|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw060_eb0192` |
| objective | `obj_4e219224` | `obj_e1419520` | `obj_b114afd4` |
| `--max-tools` | 12 | 24 | 16 |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 | ~110s IST ~14:25–14:27 |
| tools | 12/12 | 24/24 | 16/16 |
| model calls | 7/80 | 25/80 | 18/80 |
| status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** |
| disk | incomplete `text_analyzer/` layout; `summary.json` missing under the dir | five paths present; invalid JSON + wrong counts; tests `13!=6` | `pathlib_reference/README.md` EXISTS sha256 `48f0d39b…`; `pathlib_reference.md` 162 B stub; sections 3–9 FAIL; 0 examples; no docs.python.org fetch |

Interpretation: the 11B+tool-budget failure is **not coding-only**. Research also
stops at the budget with a thin placeholder instead of a sourced, sectioned
deliverable. Same Class B family as F-20260918-04 / F-20260918-15 / F-20260918-16.

## Class A / B / C

| class | this record |
|---|---|
| **A** | **none this PR.** Parked suspects F-20260918-17 / F-20260918-18 remain **open/investigate**. Do **not** claim fixed. No v0.2.4. |
| **B** | **F-20260918-20** — pathlib reference stub; sections 3–9 FAIL; 0 examples; no docs.python.org fetch; tools 16/16; `needs_user`. Pattern generalizes vs RW-058/059. |
| **C** | none new (NIM key present). |

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- Default max-tools / max-tasks **unchanged**.
- Cap **16** unchanged.
- **No v0.2.4** (no Class A fix).
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** A second live 11B Class B on a research workload is not a missing
control-plane stage and does not justify designing v0.3.0.

---

# Class A investigation — budget exhaustion → needs_user (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `a40a5446885c443c7c8fb3a975ed5af0f4bca30d` (RW-060 evidence; package **0.2.3**)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **UNCHANGED** (60).

Investigate-first after live NIM 11B RW-058 / RW-059 / RW-060 all `needs_user` /
FAIL with false DONE **0**. Parked suspects F-20260918-17 / F-20260918-18.
No live NIM on this VM (optional after deterministic proof; not required).

RW-058 / RW-059 / RW-060 rows are **not rewritten**.

## Budget exhaustion path (from code)

`Executor.run_action` charges then raises `BudgetExceeded` → `_drive` →
`Controller._on_budget` (`rad/control/controller.py`):

1. Does the controller check if the objective is already satisfiable? **Yes** —
   `_objective_already_satisfied` re-runs `objective_checks` via `Verifier.run_check`.
2. Inspect pending objective checks? **Yes** — `_close_already_satisfied` completes
   OPEN tasks whose machine checks already pass (no model call, no DONE claim).
3. Attempt verification? **Yes** if the graph is complete or objective checks pass
   → fall through to `_verify_objective`. Otherwise **no** — `needs_user`.
4. Attempt legitimate recovery at the budget boundary? **No extra recovery spend.**
   Per-task recovery already ran during `_run_task`. With no remaining tool budget,
   recovery cannot continue; that is not a skip of a still-affordable retry.
5. Checkpoint correctly? **Yes** — `_finish` → `CheckpointManager.save` (`finish needs_user`).
6. Distinguish budget exhausted vs incomplete vs potentially complete? **Yes** —
   graph complete → verify; objective checks pass → supersede leftovers + verify;
   else `needs_user`.
7. Prematurely terminate recoverable state? **No** — status is `needs_user` not
   `failed`; Scenario B resume with a raised budget continues remaining tasks.
8. Does `needs_user` accurately represent state? **Yes** when checks are unmet.
   When checks are met, status is `COMPLETED` / `VERIFIED` (Scenario A / F-20260918-03).

## Parked suspects

| id | claim | result |
|---|---|---|
| F-20260918-17 | fallback splits multiline objective **newlines** into spurious tasks | **Not confirmed.** `_fallback` splits on clause markers, not newlines. Live RW runs used the **llm** planner (brain present). |
| F-20260918-18 | `ENVIRONMENT_FAILURE` misclass burns tool budget | **Not confirmed as Class A.** Unmet checks without env-tokens → VALIDATION/TOOL → `retry_with_hint`. `command not found` → ENVIRONMENT repair **by design**. RW-058 (2 attempts, 4 PENDING, no repair task) matches VALIDATION retry. |

## Deterministic scenarios (no NIM)

| scenario | setup | observed |
|---|---|---|
| **A** | multi-task; some complete; leftover planned work; tool budget dies; objective checks pass | `COMPLETED` / `VERIFIED`; leftovers `CANCELLED`; not `needs_user` solely because budget hit |
| **B** | some complete; remaining checks unmet; budget dies | `needs_user` + checkpoint; **not** `failed`; resume after raising budget → `VERIFIED` |
| **C** | budget dies; checks unmet or artifact invalid; model claims `DONE:` | `needs_user`; **not** `VERIFIED`; false DONE **0** |

Tests: `tests/test_class_a_budget_investigation.py` (17). Full suite **345 passed**.

## Class A / B / C

| class | this investigation |
|---|---|
| **A** | **not proven. no patch.** F-17 / F-18 closed as not-confirmed. No v0.2.4. |
| **B** | live RW-058/059/060 remain Class B (11B + tool budget, success criteria unmet). |
| **C** | none new. Live NIM retest on this VM **BLOCKED** (no NVIDIA keys); not required after deterministic proof. |

## Decision

- **RAD defect demonstrated: NO**
- **Patch required: NO**
- Needle **OFF**. Cap **16** unchanged. Default tool budget **UNCHANGED**.
- **Outcome A continues.** Not v0.3.0.

## Evidence for v0.3.0

**None.** Closing parked Class A suspects without a control-plane hole is not a
v0.3.0 gap.

Later (not this investigation): RW-062 live Simple Coding + Verification reopened
F-17 with additional fallback evidence. See the RW-062 section below. F-21
Scenarios A/B/C and F-18 remain as written. No product fix.

---

# Simple Coding + Verification — RW-062 (2026-09-18)

**Date:** 2026-09-18 (IST ~15:41–15:47 for RW-062)
**Baseline:** `origin/main` `aecfbae` (PR #14 / RW-061 Class A investigation; package **0.2.3**)
**Package:** `0.2.3` — **no bump**. Not v0.2.4. Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Docs-only record. No RAD code change. RW-058 / RW-059 / RW-060 / RW-061 are
preserved exactly. No Class A patch. **Outcome A.**

## What was run

Live NIM 11B `rad objective run` of a **Simple Coding + Verification** control
on v0.2.3. Tighter bound than RW-058: `--max-tasks 4 --max-tools 12`. Needle
`existing` / off.

- Home `/tmp/rad_prod_rw062_6ede431b`, `obj_7a020865`
- Provider nvidia / `meta/llama-3.2-11b-vision-instruct` (NIM key present; not Class C)
- Wall ~383s IST ~15:41–15:47
- Tools 12/12 exhausted
- Status `needs_user` / **FAIL** vs success criteria — **NOT DONE**, **not VERIFIED** complete
- False DONE **0**

Planner: nvidia plan **timeout** → `PLAN_CREATED` **source=fallback**; **7**
newline-split spurious tasks (matches `_fallback` `[:7]` step cap).

## Disk

- five files exist
- `result.json` as-left **INVALID** `{`
- tests **FAIL** `6!=2`
- pollution `DONE:` fake path

## F-17 vs PR #14

PR #14 / RW-061 closed F-17 as **not-confirmed**: deterministic newline-only
multiline goal → **1** fallback task; live RW-058/059/060 used the **llm**
planner. That investigation is **not** a product fix.

RW-062 is the first live row where the planner source is **fallback** (after
nvidia plan timeout) and **7** newline-split spurious tasks were observed.
Ledger F-17 is **reopened / additional live evidence**. This PR does **not**
claim a confirmed Class A defect and does **not** ship a patch.

## Class A / B / C

| class | this record |
|---|---|
| **A** | **none patched.** F-17 evidence **strengthened** (live fallback path). Do **not** claim a product fix. No v0.2.4. |
| **B** | **F-20260918-22** — simple coding+verification: invalid `result.json`, tests `6!=2`, pollution `DONE:` fake path, tools 12/12, `needs_user`. Same family as F-20260918-15 / F-20260918-16 / F-20260918-19 / F-20260918-20. |
| **C** | none (NIM key present). |

Interpretation: a **simple** workload also fails similarly. Class B is **not**
limited to complex objectives.

## Decision

- **Outcome A continues** — stay on 0.2.x.
- Needle stays **off**.
- Default max-tools / max-tasks **unchanged**.
- Cap **16** unchanged.
- **No v0.2.4** (no Class A fix).
- No architecture change. Not v0.3.0.

## Evidence for v0.3.0

**None.** A third live 11B Class B on a *simpler* coding+verification workload
is not a missing control-plane stage and does not justify designing v0.3.0.

Later (not this record): RW-063 investigated the F-17 timeout/prose claim on
`d15af713` and closed it as **NOT CONFIRMED**. See the section below. RW-062
Class B facts are unchanged.

---

# F-17 timeout / prose fallback — RW-063 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `d15af713` (PR #15 / RW-062; package **0.2.3**)
**Package:** `0.2.3` — **no bump**. **No v0.2.4.** Not v0.3.0.
**Architecture:** frozen. Needle stays optional/off. `max_plan_tasks` left at **16**.
Default max-tools **not** raised.

Investigate-first. No RAD product code change. RW-058–062 preserved.
**Outcome A.**

## Question

When the LLM planner fails or times out, is RAD's fallback parser incorrectly
converting ambiguous model output into executable tasks?

## Trace (source)

`Controller.plan` → `Planner.plan` → `self.llm(PLAN_PROMPT)` → `_json_obj(raw)`
→ `_graph_from` (**source=llm**) or any exception / empty task list →
`_fallback(obj)` (**source=fallback**).

Intended LLM output: JSON `{tasks, objective_checks}` with machine checks;
“Reply ONLY with JSON”.

Fallback acceptance: split `obj.goal` on clause markers
(`and then` / `then` / `;` / `, and` / period+space-or-end), keep parts
longer than 3 chars, cap **7**, **no checks**. Valid task = non-empty clause
of the user goal. Ordinary prose in the *goal* (“RAD verifies its results.”)
becomes a clause task **by this contract**. Model prose is **not** an input
to `_fallback`.

## Feeds (task counts)

| input | tasks |
|---|---|
| seven period sentences (“Create the project.” … “Verify the result.”) | **7** |
| eight period sentences | **7** (`[:7]` cap) |
| “RAD is a personal agent. / RAD executes useful work. / RAD verifies its results.” | **3** |
| “Plan: 1. Create files. 2. Implement… 3. Run tests. 4. Verify…” | **5** (period after `1.` etc.) |
| same seven lines **without** periods (PR #14) | **1** |

## Scenarios A–D

| scenario | expected | actual |
|---|---|---|
| A valid structured JSON plan | llm source, JSON tasks | **llm**, 2 tasks, checks kept |
| B timeout + fallback-compatible (7-sentence) goal | fallback on **goal** | **fallback**, 7 clause tasks, no checks |
| C timeout + ordinary prose; LLM returns 7-line plan prose | must not use model text | **fallback** on goal (3 sentences → 3 tasks). One-sentence goal + same model prose → **1** task |
| D malformed / empty LLM | safe fallback, not uncontrolled | **fallback** on goal, **≤7**, not 16 |

Spurious tasks from model output: **0**.

## Tool / budget impact

Fallback can turn a planning *failure* into up to **7** executable no-check
tasks (the user goal's clauses). `--max-tasks 4` (RW-062 run bound) stops the
drive after 4 of those; it does not change the planner. Default
`Budget.tool_calls` remains **60**. `max_plan_tasks` remains **16**. This is
bounded clause-split, not runaway multiplication. Live RW-062 tool exhaustion
(12/12) remains Class B execution quality, not a parser hole.

## Class A / B / C

| class | this record |
|---|---|
| **A** | **NO.** Parser does not violate the intended contract. Timeout does not parse model output. Newlines do not split. |
| **B** | none new. RW-062 / F-20260918-22 stays B. |
| **C** | none (no live NIM this investigation). |

Root cause of the PR #14 vs RW-062 contradiction: different *goals*. PR #14
fed a bullet/newline goal without clause markers → 1 task. RW-062's 7 tasks
match a period-separated user goal hitting `[:7]`, observed after nvidia
timeout forced the fallback path. The operator label “newline-split” does
not match `Planner._fallback`.

## Decision

- **RAD defect demonstrated: NO**
- **Patch required: NO**
- **Regression (product): NO** — investigation tests only
- Needle **OFF**. Cap **16** unchanged. Default tools **UNCHANGED**.
- False completion **0**.
- **No v0.2.4.**
- **Outcome A continues.** Not v0.3.0.

## Quality gates (this branch)

| gate | result |
|---|---|
| `python -m pytest -q` | **364 passed** in 8.30s (345 prior + 19 investigation) |
| `rad doctor --offline` | READY — 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR |
| `rad acceptance` | **50/50 PASSED** |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** (`live_nim` BLOCKED) |
| Architecture | frozen — no planner/controller product change |
| Version | **0.2.3** — **no v0.2.4** |

## Evidence for v0.3.0

**None.** Closing F-17 without a control-plane hole is not a v0.3.0 gap.

---

# Cycle 3 — v0.2.3 (2026-09-18)

**Date:** 2026-09-18
**Baseline:** `origin/main` `8d9e196aa730c7bfeae7e501f44004078f080b61` (PR #8 / GitHub Release `v0.2.2`)
**Package at start:** `0.2.2` (`rad/__init__.py`, tag `v0.2.2` → `8d9e196aa730c7bfeae7e501f44004078f080b61`)
**This branch:** `cursor/post-v022-maturation-d297` — package **0.2.3**
**Architecture:** frozen. No AGI/ASI. Needle stays optional/off. Not v0.3.0.

## Baseline (re-checked)

| item | evidence |
|---|---|
| `origin/main` HEAD | `8d9e196aa730c7bfeae7e501f44004078f080b61` |
| `__version__` on main | `0.2.2` |
| GitHub Release | `v0.2.2` → `8d9e196aa730c7bfeae7e501f44004078f080b61` |
| Docs on main | `REAL_WORLD_FAILURE_LEDGER.md`, `REAL_WORLD_TASK_MATRIX.md`, `MATURATION_CYCLE_REPORT.md`, ADR-001 |
| NVIDIA keys | **ABSENT** — live NIM **BLOCKED** |
| `RAD_TOOL_ROUTER` | unset; `tool_router` default `existing` |
| `max_plan_tasks` | not in `DEFAULTS`; controller fallback **16** |

Pytest collected on this SHA after the Class A patch: **328 passed**.

## Tasks executed

See `docs/REAL_WORLD_TASK_MATRIX.md` cycle-3 rows (RW-024–RW-039). Evidence: `/tmp/rad-c3-evidence/campaign.json`.

- Production campaign (control plane, real tools, disk checks): coding (`pkg/avg.py`), two-source research, filesystem sort+jail, log→JSON→summary multi-step, injected `write_file` recovery, crash-resume, false DONE
- Action ramp: 1, 3, 5, 10 planned SKU tasks; 20 sequential *actions* in one task; 20 planned tasks (cap)
- Class A probe: advertised `json_valid` / `json_min_len` grader vs verifier on an object report
- Live NIM probe; Needle default probe
- Scripted `rad realworld` suite re-run as a gate

## Successful / Verified / Failures

| set | result |
|---|---|
| `rad realworld` suite | **10 PASS / 1 BLOCKED / 0 FAIL** (research independent graders now include `json_valid` + `json_min_len`, all `ok`) |
| Campaign coding / research / filesystem / multi-step | **VERIFIED**, files on disk match hashes |
| Ramp 1 / 3 / 5 / 10 tasks | **VERIFIED** (`inv/sNN.txt` SKU files) |
| Ramp 20 *actions* (one task, 20 `write_file`) | **VERIFIED**, 20/20 (`inv/s20.txt` sha256 `14e88a9299fed78c`) |
| Ramp 20 *tasks* at default planner cap | **FAIL** — 16/20 files; `max_plan_tasks` default 16. Documented; **not patched** |
| Injected-fault recovery | **VERIFIED**, 1 tool error, 2 recoveries (`config/settings.json` sha256 `2b3a56a5f55ff76f`) |
| Crash-resume | **VERIFIED**, `pipe/p1.txt`–`p3.txt` after checkpoint restore |
| False DONE | `needs_user`, `proof.txt` **absent**, **not** VERIFIED |
| json_min_len / json_valid probe | pre-fix independent grader **FAIL**; post-fix **PASS** (agrees with verifier) |

False completion (VERIFIED without the artifact): **0**.

## Class A / B / C

| class | this cycle |
|---|---|
| **A** | **F-20260918-11** — `Lab._run_grader` did not implement advertised `json_valid` (`unknown grader`) and treated `json_min_len` as list-only while the verifier uses `len(doc)` for list/dict/string. Independent scores disagreed with disk + verifier. Smallest fix + regression. Bump **0.2.3**. |
| **B** | none new. 11B over-decompose remains F-20260918-04. Planner cap at 16 remains a documented limit (RW-034), not a product-evidence raise. Needle stays off (F-20260918-06). |
| **C** | **F-20260918-12** — live NIM **BLOCKED** (no `NVIDIA_*` keys). Same condition as F-20260918-07 / F-20260918-10. |

## Fixes

- `rad/lab.py` `_run_grader`: `json_valid` parses the file; `json_min_len` uses `len(doc)` like `Verifier.run_check`.
- Real-world `research` graders now include those kinds so the suite encodes the failure mode.
- Regression: `test_grader_json_valid_and_json_min_len_match_verifier`.
- Version: `0.2.2` → `0.2.3` (`rad/__init__.py`, `pyproject.toml`, ship tests, README banner, QUICKSTART).

No controller rewrite. No Needle default. DONE / VERIFIED rules unchanged (`false_success` still `needs_user`). `max_plan_tasks` left at 16.

## Regression tests

Pinned in `tests/test_lab.py`. Full gate commands below were actually run on this branch.

## NIM status

**BLOCKED.** `NVIDIA_NIM_API_KEY` and `NVIDIA_API_KEY` both absent. Live Class A retest (artifact-exists → VERIFIED; artifact-missing → not VERIFIED) was **not** run. Offline reconstruction: `overdecompose` + `false_success`.

## Needle status

**Off.** `RAD_TOOL_ROUTER` unset; default `tool_router=existing`. ADR-001 unchanged. Not measured this cycle (no new Needle evidence; previous gold set did not beat existing).

## Security

- Workspace jail held on RW-026 (`../escape.txt` not created).
- No secrets committed or printed.
- Tests still strip `*_API_KEY` / `*_NIM_API_KEY` / `RAD_TOOL_ROUTER`.

## Remaining limitations

1. Live NVIDIA NIM is untested on this VM (Class C).
2. Default planner cap is **16 tasks**. A 20-task sequential plan is truncated; 20 *actions* inside fewer tasks succeed. Do not raise the default without a measured product need.
3. 11B over-decomposition remains Class B; bounded `--max-tasks` / `--max-tools` is still the mitigation.
4. No OS-level shell sandbox (unchanged).

## Quality gates (actually run)

Isolated home `/tmp/rad-v023-gate`. Only items actually run are marked PASS.

| gate | result |
|---|---|
| `rad version` | **PASS** v0.2.3 |
| `python -m pytest -q` | **PASS** 328 passed in 8.73s (327 on v0.2.2 + 1 json grader regression) |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v023-gate/acceptance/20260918-072009_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v023-gate/realworld/20260918-072010_realworld.json`. Research graders `json_valid` / `json_min_len` `ok` |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Class A json grader probe | **PASS** after fix: object `json_min_len{n=2}` and `json_valid` agree with verifier |
| Secrets in git | **PASS** (inspected; only fixture placeholders in tests) |
| DONE semantics | **PASS** (RW-035, suite `false_success` / `needs_user` / `no_loop`) |
| Architecture freeze | **PASS** |
| `max_plan_tasks` | **PASS** left at 16 |

## Recommended next action

1. Supply `NVIDIA_NIM_API_KEY` and retest live Class A: file-on-disk → VERIFIED; missing file → not VERIFIED; one unconstrained 11B write (log B if `needs_user` after the file exists and the verifier *was* consulted).
2. Leave `max_plan_tasks` at 16 unless a measured product need requires a documented config key.
3. Keep Needle off until a gold-set win on RAD tools.
4. Do not ship v0.3.0 from this loop.

---

# Cycle 2 — v0.2.2 (2026-09-18)

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

Isolated home `/tmp/rad-v022-gate`. Only items actually run are marked PASS.

| gate | result |
|---|---|
| `rad version` | **PASS** v0.2.2 |
| `python -m pytest -q` | **PASS** 327 passed in 8.13s (326 on v0.2.1 + 1 grader regression) |
| `rad doctor --offline` | **PASS** 20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR, verdict READY, exit 0 |
| `rad acceptance` | **PASS** 50/50 — `/tmp/rad-v022-gate/acceptance/20260918-064950_gate.json` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED — `/tmp/rad-v022-gate/realworld/20260918-064950_realworld.json`. Research/coding `graders=` now all `ok` |
| Live NIM Class A | **BLOCKED** |
| Needle default | **PASS** (still `existing`) |
| Class A grader probe | **PASS** `{key}` and `{contains}` score `ok: True`; `{expect}` still works |
| Secrets in git | **PASS** (inspected) |
| DONE semantics | **PASS** (RW-007, RW-009, RW-022) |
| Architecture freeze | **PASS** |

## Recommended next action

1. Supply `NVIDIA_NIM_API_KEY` and retest live Class A: file-on-disk → VERIFIED; missing file → not VERIFIED; one unconstrained 11B write (log B if `needs_user` after the file exists and the verifier *was* consulted).
2. Leave `max_plan_tasks` at 16 unless a measured product need requires a documented config key.
3. Keep Needle off until a gold-set win on RAD tools.
4. Do not ship v0.3.0 from this loop.
