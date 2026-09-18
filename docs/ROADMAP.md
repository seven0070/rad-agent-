# RAD development roadmap

This is the **operating spine** for RAD: five generations, one loop, evidence in / evidence out.
It is not a product-idea backlog (that list stays in the README) and it is not a license to
redesign the control plane.

**Status (2026-09-18):** Generation 1 is **complete**. Generation 2 is
**complete** (v0.3.0–v0.3.2). Theme 1 — **verified coding loop** — shipped as
**v0.3.0** and **used** (RW-065; RW-068). Theme 2 — **plan-timeout
resilience** — shipped as **v0.3.1** and **used** (live RW-066 **PASS**;
RW-068 llm/1). Theme 3 — **budget-aware planning** — shipped as **v0.3.2**.
v0.3.2 use campaign is **done** (RW-068 **PASS**, RW-069 **FAIL**). Generation 3
theme 1 — **path-aligned checks / package layout** — is **implemented as
v0.4.0** and **live-confirmed** (RW-071; RW-073 disk/tasks; RW-075 obj-checks).
Theme 2 — **multi-file coding under tight budgets** — is **implemented as
v0.4.1** and **live-confirmed** (RW-073 contracts + mkdir class). Theme 3 —
**longer-horizon / multi-step reliability** — is **planned / scoped**; slice A
(ASCII-tree `package_dir`) is **implemented as v0.4.2** and **used** (RW-075);
slice B (first-task thrash) is **implemented as v0.4.3** and **used**
(RW-077); slice C (mkdir already-exists action noise) is **implemented as
v0.4.4** (**live-confirmed** RW-081); slice D (premature-test
ENVIRONMENT) is **implemented as v0.4.5** and **used** (RW-081; premature-test
path **not live-hit**; mkdir File-exists **live Y**). Pip thrash + root
pollution Class A is **NOT CONFIRMED** (RW-082). Stay **0.4.5**. Needle stays off.
Caps unchanged. This patch does **not** claim live 11B RW-081 would now PASS.
Generations 4–5 are **not started**.

```
build → test → validate → release → use → discover gaps → build the next version
```

Never skip a generation. Never invent a `v0.3.x` feature without an evidence row.
Stability with no code change is a valid result.

---

## Current status

| item | value |
|---|---|
| Generation in production | **Gen3 in progress** — **v0.4.5**; tagged `v0.4.5` @ `32e9fe87`; v0.4.4 is tagged `v0.4.4` @ `acb61997`; v0.4.3 is tagged `v0.4.3` @ `99099b8a`; v0.4.2 is tagged `v0.4.2` @ `feb8a4ec`; v0.4.1 is tagged `v0.4.1` @ `387bd83a`; v0.4.0 is tagged `v0.4.0` @ `a8aac8ae`; Gen2 complete on `387776dc` / tag `v0.3.2`; Gen1 baseline remains tagged `v0.2.3` @ `d121c3f` |
| Package / tag on `main` | **0.4.5** / annotated tag `v0.4.5` @ `32e9fe87` (this branch stays **0.4.5** — no bump) |
| This change | **RW-081 record** + pip/root-pollution Class A **NOT CONFIRMED** (investigation tests; stay 0.4.5) |
| Generation 2 | **COMPLETE** — theme 1 **v0.3.0** (used RW-065 / RW-068); theme 2 **v0.3.1** (used live RW-066 / RW-068); theme 3 **v0.3.2** (scripted RW-067; used RW-068 / RW-069) |
| Latest use (RW-081) | Live NIM 11B text_analyzer on v0.4.5: **FAIL** `needs_user` @ 12/12; theme 1 **Y**; theme 2 **Y**; mkdir File-exists Class A **live Y**; premature-test ENVIRONMENT **not live-hit**; residual **Class B** (pip/echo thrash, root `analyzer.py` pollution, empty `summary.json`, SyntaxError test under tools=12) |
| Generation 3 | **IN PROGRESS** — theme 1 **implemented** (v0.4.0) **used** (RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081); theme 2 **implemented** (v0.4.1) **used** (RW-073 / RW-075 / RW-077 / RW-079 / RW-081); theme 3 **planned / scoped**, slice A **v0.4.2** **used** (RW-075 / RW-077 / RW-079 / RW-081), slice B **v0.4.3** **used** (RW-077 / RW-079 / RW-081), slice C **v0.4.4** **used** (RW-081 mkdir live Y), slice D **v0.4.5** **used** (RW-081; premature-test path not live-hit) |
| Generations 4–5 | **NOT STARTED** |
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
| **3** | Autonomous Agent Maturity | v0.4.x | **IN PROGRESS** (theme 1 → **v0.4.0** used RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081; theme 2 → **v0.4.1** used RW-073 / RW-075 / RW-077 / RW-079 / RW-081; theme 3 planned / scoped, slice A → **v0.4.2** used RW-075 / RW-077 / RW-079 / RW-081, slice B → **v0.4.3** used RW-077 / RW-079 / RW-081, slice C → **v0.4.4** used RW-081, slice D → **v0.4.5** used RW-081) |
| **4** | Production Scale | v0.5.x | **NOT STARTED** |
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
(v0.4.5) and **used** (RW-081; premature-test path not live-hit).
Gen4–5 stay closed until Gen3 has been released and used.

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

## Generation 3 — Autonomous Agent Maturity — IN PROGRESS (v0.4.x)

More reliable multi-step execution, recovery, planning, and long-horizon work.

**Status:** **in progress.** Theme 1 — **path-aligned checks / package layout** —
is **implemented as v0.4.0** and **live-confirmed** (RW-071; RW-073 disk/tasks;
RW-075 obj-checks; RW-081). Theme 2 — **multi-file coding under tight budgets** — is
**implemented as v0.4.1** and **live-confirmed** (RW-073; RW-081). Theme 3 —
**longer-horizon / multi-step reliability** — is **planned / scoped**. Slice A
(ASCII-tree `package_dir`) is **implemented as v0.4.2** and **used** (RW-075 /
RW-077 / RW-079 / RW-081). Slice B (first-task thrash) is **implemented as v0.4.3** and **used**
(RW-077 / RW-079 / RW-081). Slice C (mkdir already-exists action noise) is **implemented as
v0.4.4** and **live-confirmed** (RW-081). Slice D (premature-test
ENVIRONMENT) is **implemented as v0.4.5** and **used** (RW-081; premature-test
path **not live-hit**). Package stays **0.4.5**. Live RW-081
Class B (pip/echo thrash, root `analyzer.py` pollution, empty `summary.json`, SyntaxError test) is **not**
claimed fixed. Pip/root-pollution Class A is **NOT CONFIRMED** (RW-082).

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

### Theme 3 — planned / scoped (longer-horizon); slice A v0.4.2; slice B v0.4.3; slice C v0.4.4; slice D v0.4.5

| field | value |
|---|---|
| Status | **PLANNED / SCOPED**. Slice A **IMPLEMENTED** as v0.4.2. Slice B **IMPLEMENTED** as v0.4.3. Slice C **IMPLEMENTED** as v0.4.4 (**used** RW-081). Slice D **IMPLEMENTED** as v0.4.5 (**used** RW-081; premature-test path not live-hit) |
| Theme | **Longer-horizon / multi-step reliability** |
| Version | Theme 3 itself is **not** a full v0.4.x redesign. Slice A is **v0.4.2**. Slice B is **v0.4.3**. Slice C is **v0.4.4**. Slice D is **v0.4.5**. This cycle stays **0.4.5** |
| Loop (slice D, preserved) | premature `python …/test_*.py` (interpreter cannot open a `.py` script the agent has not written) is not ENVIRONMENT and does not fail a task whose explicit directory/file checks passed |
| Evidence | RW-081 / F-20260918-43 (live FAIL; mkdir File-exists **live Y**; premature-test ENVIRONMENT **not live-hit**; pip/echo + root pollution residual); deterministic RW-082 / F-20260918-44 (**NOT CONFIRMED**) |
| What it is not | Not a control-plane rewrite. Not Needle-as-default. Not a cap raise. Not a claim that live 11B RW-081 now PASS. Not multi-step checkpoint redesign. Not a remap of check *kinds* (F-26). Fallback *tasks* stay check-less (F-17). Not a PLAN_PROMPT-only bump for pip/root writes. |

**Entry rule:** themes 1–2 are measured (done). Slice A shipped as v0.4.2
(ASCII-tree `package_dir`; **used** RW-075 / RW-077 / RW-079 / RW-081). Slice B shipped as v0.4.3
(first-task pip/DONE thrash; **used** RW-077 / RW-079 / RW-081). Slice C shipped as v0.4.4
(mkdir already-exists action noise; **live-confirmed** RW-081). Slice D shipped as v0.4.5
(premature-test ENVIRONMENT; **used** RW-081, path **not live-hit**). Remaining candidate
sub-theme stays **planned**, not built:

1. Multi-step checkpoint so later files still get attempts when an early task
   burns retries (not this patch).

Do **not** invent a long-horizon redesign from Class B budget/quality rows.
Pip thrash + root `echo > analyzer.py` pollution on RW-081 is **NOT CONFIRMED**
as Class A (RW-082) — stay **0.4.5**.

### Themes (evidence-backed; priority order)

Grounded in RW-068 / RW-069 / RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 and the residual RW-058 / RW-059
family (F-20260918-15 / 16 / 19 / 31 / 33 / 35 / 37 / 39 / 41 / 43). Simple coding **PASS** on
v0.3.2 is **not** a Gen3 hole (B3).

| # | theme | status | what the evidence showed | rows |
|---|---|---|---|---|
| 1 | **Path-aligned checks / package layout** | **IMPLEMENTED** — v0.4.0; **used** RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 | Task checks required workspace-root `input.txt` while first successful writes were under `text_analyzer/` → VALIDATION_FAILURE → retry flattened files to root → layout thrash. Confirmed as planner/infer emission + LLM-check acceptance (not just 11B). Live RW-081: path-alignment **Y** on disk/tasks **and** objective_checks (ASCII-tree join live). Root `echo > analyzer.py` leftover is Class B, not check-path flattening. | RW-069; RW-070 (scripted); RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 (live use); RW-074 (scripted ASCII-tree); related path confusion on RW-058 |
| 2 | **Multi-file coding under tight budgets** | **IMPLEMENTED** — v0.4.1; **used** RW-073 / RW-075 / RW-077 / RW-079 / RW-081 | `text_analyzer` @ tools=**12** still FAIL on live 11B. RW-081: contracts **package-joined**; correct 3-line `bf69eb73…`; mkdir File-exists **live Y**. Residual: empty `summary.json`, SyntaxError test, pip/echo budget. Does not raise default max-tools. | RW-071; RW-072 (scripted); RW-073 / RW-075 / RW-077 / RW-079 / RW-081 (live use); RW-069; RW-058 / RW-059 family (F-15 / F-16 / F-19) |
| 3 | **Longer-horizon / multi-step reliability** | **PLANNED / SCOPED** — slice A **v0.4.2** **used** RW-075 / RW-077 / RW-079 / RW-081; slice B **v0.4.3** **used** RW-077 / RW-079 / RW-081; slice C **v0.4.4** **used** RW-081; slice D **v0.4.5** **used** RW-081 (premature-test path not live-hit) | RW-081 burns remaining tools on second-task pip/echo after first task VERIFIED (mkdir noise). Slice C **live Y**. Slice D not live-hit. Pip/root-pollution Class A **NOT CONFIRMED**. Remaining: multi-step checkpoint. No long-horizon redesign. | RW-081; RW-082 (scripted NOT CONFIRMED); RW-079; RW-080 (scripted slice D); RW-077; RW-078 (scripted slice C); RW-075; RW-076 (scripted slice B); RW-074 (scripted slice A) |

### Closed / not automatic Gen3 work

These are **not** a license to raise caps or enable Needle from this change:

| id | claim | result |
|---|---|---|
| A1 | Reopen budget→`needs_user` as Class A | **Do not reopen** without new proof. RW-069 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 exhausted 12 tools with incomplete work; same honest stop as historical Class B investigations (F-21). |
| A2 | Check path vs write path (root vs package dir) | **Class A confirmed** as v0.4.0. **Live-confirmed** on RW-071 / RW-073 / RW-075 / RW-077 / RW-079 / RW-081 disk+task **checks** (path-alignment Y). RW-081 has extra root `echo > analyzer.py` leftover — that is model action pollution (F-44 **NOT CONFIRMED**), not RAD flattening files to satisfy root checks. Live 11B artifact quality remains Class B. |
| A4 | ASCII-tree `infer_package_dir` miss | **Class A confirmed** as v0.4.2 (theme-1 follow-up / theme 3 slice A). **Live-confirmed** on RW-075 / RW-077 / RW-079 / RW-081 (objective_checks all package-joined; 0 bare). |
| A5 | First-task thrash (pip-missing-requirements ENVIRONMENT + DONE-as-tool) | **Class A confirmed** as v0.4.3 (theme 3 slice B). **Live-consistent** on RW-077 / RW-079 / RW-081 (0 invented DONE; pip `-r` attempted on RW-081 without ENVIRONMENT repair). Do not re-litigate. |
| A6 | mkdir File-exists failing a check-passing task | **Class A confirmed** as v0.4.4 (theme 3 slice C). Unit RW-078. **Live-confirmed** on RW-081 (task VERIFIED despite File-exists action error). Do not regress. |
| A7 | Premature `python …/test_*.py` No-such-file → ENVIRONMENT | **Class A confirmed** as v0.4.5 (theme 3 slice D). Unit RW-080. **Not live-hit** on RW-081 (no early python test; 0 ENVIRONMENT repair). Do not regress. |
| A8 | Pip thrash + root `echo > analyzer.py` pollution under known `package_dir` | **NOT CONFIRMED.** Checks already join to `package_dir`. Actions are model-proposed (no write/redirect remap). Root file does not satisfy package checks (false DONE 0). Joining echo redirects would clobber a good package file. PLAN_PROMPT already forbids pip for stdlib-only; ingest-reject still charges tools. Stay **0.4.5**. See RW-082 / F-44. |
| A3 | DONE pollution refuse | **Already works** for `DONE:` *paths*. RW-081 invented-tool `DONE` **0**; slice B still stops it from failing check-passing tasks. |
| B3 | Simple verified coding loop | **Stable PASS** on v0.3.2 (RW-068 llm plan@1). Not a Gen3 hole. |
| F-17 / F-18 / F-21 / F-26 | Prior closed non-gates | **Stay closed.** This cycle does not add checks to fallback *tasks* (F-17) and does not remap check *kinds* (F-26). Genuine `command not found` / `ModuleNotFoundError` stay ENVIRONMENT (F-18). `cat` no-such-file stays ENVIRONMENT. mkdir already-exists still **not** ENVIRONMENT (v0.4.1). |

This cycle is **not** a claim that live 11B text_analyzer now completes under
tools=12. Residual is **Class B** capacity/quality (11B under the historical
12-tool bound; RW-081 pip/echo thrash, empty `summary.json`, SyntaxError test,
root leftover). Theme-3 measured win: mkdir File-exists action-noise **live Y**.

### Accepting a further v0.4.x theme

A short written decision that names the theme, the evidence rows, the invariant
that must not move (Needle off; caps unchanged unless proven; models propose /
RAD decides; false DONE **0**), and the 0.4.x change. Theme 2 is implemented
(v0.4.1). Theme 3 is **planned / scoped**; slice A shipped (v0.4.2) and used
(RW-075 / RW-077 / RW-079 / RW-081); slice B shipped (v0.4.3) and used (RW-077 / RW-079 / RW-081);
slice C shipped (v0.4.4) and used (RW-081); slice D shipped (v0.4.5) and used (RW-081;
premature-test path not live-hit). Remaining theme-3 slice
(multi-step checkpoint) still needs that decision — do not invent a long-horizon
redesign from Class B budget rows. Pip/root-pollution on RW-081 is **NOT CONFIRMED**
as Class A — stay **0.4.5**.

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
| [REAL_WORLD_TASK_MATRIX.md](REAL_WORLD_TASK_MATRIX.md) | Disk-checked task rows (do not rewrite RW-058–072) |
| [REAL_WORLD_FAILURE_LEDGER.md](REAL_WORLD_FAILURE_LEDGER.md) | A/B/C findings |
| [ADR-001-NEEDLE-TOOL-ROUTER.md](ADR-001-NEEDLE-TOOL-ROUTER.md) | Needle stays optional / off |
| [CONTROL-PLANE.md](CONTROL-PLANE.md) | Shipped control-plane behaviour |
| [DEVELOPMENT.md](DEVELOPMENT.md) | How to change the tree without breaking the invariants |
| [ACCEPTANCE.md](ACCEPTANCE.md) | 50-item release gate |
