# Real-world task matrix

Factual rows from maturation cycles on disk-checked evidence.
Architecture frozen. Needle stays experimental / off. Not AGI.
Operating spine: [ROADMAP.md](ROADMAP.md). Gen1 complete on 0.2.3; **Gen2 complete**
on 0.3.0–0.3.2. Verified coding loop is **implemented as v0.3.0** (RW-064). Live NIM
retest of that loop is **RW-065**. Plan-timeout resilience is **implemented as v0.3.1**
(scripted RW-066 / F-27) and **used** (live RW-066). Budget-aware planning is
**implemented as v0.3.2** (RW-067). Live NIM use of v0.3.2 is **RW-068** (PASS) and
**RW-069** (FAIL). Path-aligned checks are **implemented as v0.4.0** (RW-070). Live
NIM retest of v0.4.0 is **RW-071** (FAIL; theme 1 live-confirmed). Multi-file
contracts under tight budgets are **implemented as v0.4.1** (RW-072). Live
NIM retest of v0.4.1 is **RW-073** (FAIL; theme 1/2 live-confirmed; ASCII-tree
obj-checks bare). ASCII-tree `package_dir` is **implemented as v0.4.2**
(RW-074; theme-1 follow-up / Gen3 theme 3 slice A). Live NIM retest of v0.4.2
is **RW-075** (FAIL; ASCII-tree obj-checks **package-joined** live-confirmed).
First-task thrash is **implemented as v0.4.3** (RW-076; Gen3 theme 3 slice B).
Live NIM retest of v0.4.3 is **RW-077** (FAIL; pip/DONE Class A **live-consistent**;
mkdir File-exists action noise confirmed Class A). mkdir already-exists action
noise is **implemented as v0.4.4** (RW-078; Gen3 theme 3 slice C). Live NIM retest
of v0.4.4 is **RW-079** (FAIL; mkdir File-exists **not live-hit**; premature-test
ENVIRONMENT confirmed Class A). Premature-test ENVIRONMENT is **implemented as
v0.4.5** (RW-080; Gen3 theme 3 slice D). Live NIM retest of v0.4.5 is **RW-081**
(FAIL; mkdir File-exists **live Y**; premature-test ENVIRONMENT **not live-hit**;
pip/echo + root pollution residual). Pip thrash + root pollution Class A is
**NOT CONFIRMED** (RW-082; stay **0.4.5**). Gen3 theme 3 slice E1 (task-boundary
yield / leftover-budget dispatch) is **implemented as v0.4.6** (RW-083). Live
NIM retest of v0.4.6 is **RW-084 BLOCKED Class C** (HTTP 403 on
`chat/completions`; E1 **not live-tested**). Live OpenRouter free retest of
v0.4.6 is **RW-085 FAIL** (tools **11/12**; `xxd` ENVIRONMENT repair; E1
**not live**). Optional checksum-utility ENVIRONMENT is **implemented as
v0.4.7** (scripted RW-086). Live OpenRouter free retest of v0.4.7 is
**RW-086 FAIL** (tools **12/12**; xxd Class A thrash **CLEARED**; E1 **not
live**; late HTTP **429** `free-models-per-day`). Live OpenRouter free-model
loop **paused** until `free-models-per-day` rate limit resets. Historical
live NIM **11B** loop remains **paused** (RW-084 Class C). Live NIM
`z-ai/glm-5.3` on v1.0.1 is **RW-104 PASS**. Independent later package files is
**implemented as v0.4.8** (scripted RW-087). Budget-aware retry stop is
**implemented as v0.4.9** (scripted RW-088). Gen3 is
**complete (scripted)**; live E1–E3 confirmation is **deferred** until a
provider recovers. Gen4 **G4-1** is **implemented as v0.5.0** (scripted
RW-089). **G4-2** (live-gate resume / provider health) is **implemented
as v0.5.1** (scripted RW-090 / RW-091). **G4-3** (live-use campaign /
operator workflow) is **implemented as v0.5.2** (scripted RW-092 / RW-093).
**Version 5 pack** is GitHub Release **Version 5** / tag **v0.5.5**
(0.5.0–0.5.5). **G4-5**
(fallback / LLM plan quality) is **implemented as v0.5.3** (scripted
RW-094 / RW-095). **G4-7** (coding artifact completeness / named
package-file contracts) is **implemented as v0.5.4** (scripted RW-096 /
RW-097). **G4-6** (cost/budget reporting) is **implemented as v0.5.5**
(scripted RW-098 / RW-099). Gen4 is **complete (scripted)**; **G4-4
parked** (no measured hole). **Version 5 pack** is GitHub Release
**Version 5** / tag **v0.5.5** (0.5.0–0.5.5). Package on the 1.0 line is
**1.0.0**. First Gen5 theme **G5-1** (public / product-grade 1.0 baseline)
is **accepted and implemented as v1.0.0** (scripted RW-100 / RW-101).
**Version 1 pack SHIPPED** as GitHub Release **Version 1** / tag **v1.0.0**
(wheel + sdist; PR #52). Proven Class A on the 1.0 line is **implemented
as v1.0.1** (scripted RW-102 / RW-103). Package **1.0.1**. Live NIM
`z-ai/glm-5.3` soak of v1.0.1 is **RW-104 PASS** (`completed` /
**VERIFIED**; RW-102 / RW-103 live-cleared). Package stays **1.0.1**.
**No G5-2 product theme.** Next: **hold / soak**. **No GitHub Release /
tag** in this change. Do not rewrite RW-058–103.

Every `VERIFIED` / `completed` cell is from the control-plane verifier **and** a disk
check (file exists / contents / hash). A model `DONE:` line is never enough.

Status vocabulary: **PASS** | **FAIL** | **BLOCKED** | **NOT TESTED**.

Live NIM glm-5.3 soak of v1.0.1 (RW-104) is at the top (**PASS** /
**VERIFIED**; not text_analyzer@12), then
scripted v1.0.1 Class A (RW-102 / RW-103) (**PASS**; pinned
model health ping; json_field English glue not a key; live-cleared by
RW-104), then
scripted G5-1 (RW-100 / RW-101) (**PASS**; public 1.0
install / docs honesty / honesty bar; no live PASS required), then
scripted G4-6 (RW-098 / RW-099) (**PASS**; persisted
`Usage` rollup on `rad cost`; remaining-quota not invented; no live
PASS required), then
scripted G4-7 (RW-096 / RW-097) (**PASS**; named
`file_exists` / `json_field` objective contracts; empty `{}` and missing
README not VERIFIED; no live PASS required), then
scripted G4-5 (RW-094 / RW-095) (**PASS**; near-JSON recover / compact
coding retry; F-17 check-less fallback), then
scripted G4-3 (RW-092 / RW-093) (**PASS**; doctor skip-blocked;
`rad health` wait/rotate/resume/run; playbook; no live PASS required), then
scripted G4-2 (RW-090 / RW-091) (**PASS**; catalog ≠ inference; last Class C
persists; resume live-gated; 429 Retry-After visible), then
scripted G4-1 (RW-089) (**PASS**; 403/429 → Class C
`needs_user`; free rotation; no paid under free_lock; no Class A), then
scripted E3 (RW-088) (**PASS**; retry/repair stop; later
independent file ≥1 attempt), then scripted E2 (RW-087) (**PASS**; later
independent fallback file ≥1 attempt), then live OpenRouter retest of v0.4.7 (RW-086) (**FAIL**; xxd
Class A thrash **CLEARED**; E1 not live; late **429** `free-models-per-day`;
free-model loop **paused**), then live OpenRouter RW-085 (**FAIL**; Class C
cleared; xxd ENVIRONMENT Class A **CONFIRMED**), then scripted RW-086
(v0.4.7), then live NIM RW-084 (**BLOCKED Class C**), then scripted RW-083.
G4-3 is **shipped** as v0.5.2 (scripted); **Version 5 pack** is tag
**v0.5.5** (0.5.0–0.5.5).
G4-5 is **shipped** as v0.5.3 (scripted RW-094 / RW-095). **G4-7** is
**shipped** as v0.5.4 (scripted RW-096 / RW-097). **G4-6** is
**shipped** as v0.5.5 (scripted RW-098 / RW-099). Gen4 is
**complete (scripted)**; G4-4 **parked**. **G5-1** is **shipped** as
v1.0.0 (scripted RW-100 / RW-101). **No GitHub Release / tag** in that
change. **v1.0.1** is proven Class A (scripted RW-102 / RW-103) and
**used** live (RW-104 **PASS**).
RW-058–103 are **not rewritten**.

# Live NIM glm-5.3 soak of v1.0.1 (RW-104) — PASS

Lane: operator production `rad objective run` on **v1.0.1** (`806bdbd`,
PR #54). Provider **nvidia** / `z-ai/glm-5.3`. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60** (this soak
used a **40**-tool bound and exhausted it). RW-058–103 are **not
rewritten**. Package stays **1.0.1** (no bump). **No GitHub Release /
tag.** **Not** a live text_analyzer@12 PASS.

Authoritative live facts: operator report for `obj_72b050a0` /
`RAD_HOME=/tmp/rad-v101-nim-soak-c5b63bf7` / workspace
`/tmp/rad-v101-nim-ws-c5b63bf7`. This agent did not re-run NIM.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-104 | 2026-09-19 IST afternoon | coding (live NIM) — v1.0.1 text_analyzer glm-5.3 soak | production `text_analyzer/` (README, analyzer.py, test_analyzer.py, summary.json, sample.txt); Needle `existing` / off | `PLAN_CREATED` **source=fallback** **attempts≈2** (NIM plan timeouts then fallback) | tools **40/40**; model **46/80**; retries **3/6**; wall ~1120s | 40/40 exhausted | **PASS** (`completed` / **VERIFIED** / `verified complete`; `needs_user=no`) | objective **VERIFIED**: `json_valid`, `shell_ok` tests, `json_field` **`lines`**, README / analyzer `file_exists`. **No** bogus key `on`. Host `python text_analyzer/test_analyzer.py` **OK** | Task6 **CANCELLED** after budget. Resume `--max-tools 70` did **not** raise stored budget (evidence only). xxd/hexdump `TOOL_FAILURE` noise burned tools (not ENVIRONMENT). Empty `llm_judge` non-blocking under overall VERIFIED | **B** residual (fallback PLAN / provider timeout quality / budget UX / TOOL_FAILURE noise). RW-102 / RW-103 **live-cleared**. Class A this record **NO** | Provider **nvidia** / `z-ai/glm-5.3`. Home `/tmp/rad-v101-nim-soak-c5b63bf7`; workspace `/tmp/rad-v101-nim-ws-c5b63bf7`; `obj_72b050a0`. Disk: full `text_analyzer/` — `summary.json` `{lines:2,words:4,characters:20}`; `sample.txt` YES. Doctor/health: nvidia **inference-entitled** under pinned glm-5.3. False DONE **0**. Caps unchanged. Needle OFF. Stay **1.0.1**. Do not claim text_analyzer@12 PASS. |

### RW-104 vs prior 1.0 soaks (context)

| | v1.0.0 OpenRouter DeepSeek flash (RW-102 pointer) | v1.0.0 NIM glm-5.3 (RW-103 pointer) | RW-104 (v1.0.1 NIM glm-5.3) |
|---|---|---|---|
| package | **1.0.0** | **1.0.0** | **1.0.1** (`806bdbd` / PR #54) |
| brain | openrouter / `deepseek/deepseek-v4-flash-0731:free` | nvidia / `z-ai/glm-5.3` | nvidia / `z-ai/glm-5.3` |
| chat / doctor | chat **200**; doctor pinged stale llama:free **404** | entitled enough to write disk | doctor/health **inference-entitled** on the pin (RW-102 **live-cleared**) |
| PLAN | fallback | (soak; plan not the Class A hole) | **fallback** attempts≈2 (NIM plan timeouts) |
| disk `text_analyzer/` | never VERIFIED | **PASS** (package on disk) | **PASS** — README, analyzer.py, test_analyzer.py, `summary.json` `{lines:2,words:4,characters:20}`, sample.txt; host tests **OK** |
| control plane | never VERIFIED; then **429** `free-models-per-day` | **FAIL** `needs_user` + bogus json_field **`on`** | **PASS** `completed` / **VERIFIED** / `needs_user=no` |
| json_field `on` | n/a (doctor-pin hole) | **YES** (blocked VERIFIED) | **NO** (RW-103 **live-cleared**) |
| tools | (soak; then 429) | (soak) | **40/40**; model 46/80; retries 3/6; ~1120s |
| residual | Class C 429 + RW-102 Class A (fixed v1.0.1) | RW-103 Class A (fixed v1.0.1) | **Class B** only (fallback PLAN; Task6 cancelled; resume `--max-tools 70` did not raise stored budget; xxd/hexdump TOOL_FAILURE noise; empty llm_judge non-blocking) |
| false DONE | **0** | **0** | **0** |

# Scripted pinned-model health ping + json_field glue (RW-102 / RW-103)

Lane: scripted doctor + health + planner + verifier (no NIM / no OpenRouter)
on **v1.0.1**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

Soak pointers (2026-09-19): OpenRouter free — `force_provider=openrouter`,
`model=deepseek/deepseek-v4-flash-0731:free`; chat HTTP **200**; doctor pinged
stale `meta-llama/llama-3.3-70b-instruct:free` HTTP **404**; NVIDIA 403 Class C
noise. NIM glm-5.3 — `text_analyzer/` artifacts on disk; objective never
VERIFIED; bogus json_field key **`on`**. Live-cleared by **RW-104**.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-102 | 2026-09-19 | ops (scripted) — doctor/health ping uses pinned `cfg.model` (OpenRouter soak shape) | force_provider=openrouter; model=deepseek/deepseek-v4-flash-0731:free; stale default llama:free 404; pin 200 | n/a | probe_inference + scan + doctor | none (1-token ping mocked) | **PASS** (pin entitled; llama default not pinged; nvidia 403 stays Class C) | n/a; false DONE **0** | **N** | **A CONFIRMED** (v1.0.1; F-20260919-59) | Tests `test_pinned_model_health_probe.py`. Needle OFF. Caps unchanged. No live PASS claim. No GitHub Release / tag. |
| RW-103 | 2026-09-19 | verify (scripted) — json_field does not invent key `on` (NIM glm-5.3 soak shape) | ASCII-tree `summary.json (… on a sample)` / `JSON keys on a sample` | merged objective contracts | infer + scripted write | remaining=20 | **PASS** (`on`/`sample` not contracted; classic keys still fail `{}`; complete package **VERIFIED**) | named keys contracted; glue dropped; false DONE **0** | **N** | **A CONFIRMED** (v1.0.1; F-20260919-60) | Tests `test_json_field_english_glue.py`. Needle OFF. Caps unchanged. F-17 stays closed. No live PASS claim. |

# Scripted public 1.0 baseline (RW-100 / RW-101)

Lane: scripted docs + packaging (no NIM / no OpenRouter) on **v1.0.0**.
Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-100 | 2026-09-19 | install (scripted) — public 1.0 path + first-run docs match `rad version` 1.0.0 | QUICKSTART no longer prints 0.4.1; Version 1 wheel URL documented; wheel/sdist buildable without credentials | n/a (docs + PEP 517) | pip wheel + python -m build --sdist | default **60** unchanged | **PASS** (`rad version` v1.0.0; QUICKSTART `prints 1.0.0`; wheel `rad_agent-1.0.0-*.whl`) | `docs/QUICKSTART.md` / `docs/INSTALLATION.md` / `dist/` | **N** | capability (Gen5 G5-1; no PyPI token; no release in this PR) | Tests `test_public_1_0_baseline.py`. Needle OFF. Caps unchanged. No live PASS claim. |
| RW-101 | 2026-09-19 | honesty (scripted) — 1.0 bar locked (false DONE 0, Needle OFF, caps 16/60, Class C, F-17) | ROADMAP / README lock public 1.0 invariants; fallback *tasks* stay check-less | n/a | Planner._fallback + docs | remaining=n/a | **PASS** (Needle `existing`; max_plan_tasks 16; Budget.tool_calls 60; 7 check-less fallback tasks; remaining-quota not invented) | ROADMAP G5-1 ACCEPTED + IMPLEMENTED as v1.0.0; no GitHub Release in this PR | **N** | capability (Gen5 G5-1; F-17 stays closed) | Tests `test_public_1_0_baseline.py`. Needle OFF. Caps unchanged. No live PASS claim. |

# Scripted cost/budget reporting (RW-098 / RW-099)

Lane: scripted objective store + `rad cost` (no NIM / no OpenRouter) on
**v0.5.5**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-098 | 2026-09-19 | report (scripted) — persist Usage rolls up (Cycle 24 / RW-086 shape) | two offline `objective.json` records with tools/model/money/tokens | n/a (records already on disk) | store.save + rollup | default **60** unchanged | **PASS** (totals 15 tools / 6 model / $0.02 / 950 tokens) | `~/.rad/objectives/<id>/objective.json`; remaining-quota **not** a field | **N** | capability (Gen4 G4-6; G4-2 last Class C untouched) | Tests `test_cost_budget_report.py`. Needle OFF. Caps unchanged. No live PASS claim. |
| RW-099 | 2026-09-19 | report (scripted) — `rad cost` surfaces rollup without a live provider | one offline completed objective (tools 12 / $0) | n/a | `rad cost` | remaining=n/a | **PASS** (paid 14-day section + objective rollup; remaining-quota not invented; last Class C / Retry-After preserved) | persisted Usage + `provider_health.json` unchanged | **N** | capability (Gen4 G4-6; no remaining-quota API) | Tests `test_cost_budget_report.py`. Needle OFF. Caps unchanged. No live PASS claim. |

# Scripted coding artifact completeness (RW-096 / RW-097)

Lane: scripted planner + verifier + controller (no NIM / no OpenRouter) on
**v0.5.4**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-096 | 2026-09-19 | verify (scripted) — named package-file `file_exists` (RW-081/085/086 shape) | ASCII-tree `text_analyzer/` names README.md + analyzer.py | merged objective contracts | infer + scripted write | default **60** unchanged; scripted remaining=20 | **PASS** (missing README / analyzer **not VERIFIED**; complete package **VERIFIED**) | README.md / analyzer.py contracted; false DONE **0** | **N** | capability (Gen4 G4-7; F-17 stays closed) | Tests `test_coding_artifact_completeness.py`. Needle OFF. Caps unchanged. No live PASS claim. |
| RW-097 | 2026-09-19 | verify (scripted) — named JSON `json_field` (RW-081/086 shape) | ASCII-tree `summary.json (accurate lines/words/characters)` | merged objective contracts | infer + scripted write | remaining=20 | **PASS** (`{}` + alt-schema **not VERIFIED**; classic keys **VERIFIED**; empty `{}` still `json_valid`) | named keys contracted; false DONE **0** | **N** | capability (Gen4 G4-7; F-17 stays closed) | Tests `test_coding_artifact_completeness.py`. Needle OFF. Caps unchanged. No live PASS claim. |

# Scripted LLM plan quality (RW-094 / RW-095)

Lane: scripted planner + controller (no NIM / no OpenRouter) on
**v0.5.3**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-094 | 2026-09-19 | plan (scripted) — near-JSON recovered as llm (RW-085/086 shape) | text_analyzer/ 4-clause coding goal; fenced / trailing-comma / tasks-array JSON | 3 coding tasks with checks | parse recover | default **60** unchanged; scripted remaining=12 | **PASS** (`source=llm` attempts=1; checks kept; not clause-carve) | n/a (plan-time); false DONE **0** | **N** | capability (Gen4 G4-5; F-17 stays closed) | Tests `test_llm_plan_quality.py`. Needle OFF. Caps unchanged. No live PASS claim. |
| RW-095 | 2026-09-19 | plan (scripted) — compact coding retry after a miss | Same RW-085-shaped goal; timeout then valid JSON | 3 coding tasks with checks | 2 plan attempts | remaining=12 | **PASS** (`source=llm` attempts=2; `PLAN_CODING_RETRY` used; exhausted still 4 check-less fallback tasks) | n/a (plan-time); `DONE:` not VERIFIED; false DONE **0** | **N** | capability (Gen4 G4-5; F-17 stays closed) | Tests `test_llm_plan_quality.py`. Needle OFF. Caps unchanged. No live PASS claim. |

# Scripted live-use campaign / operator workflow (RW-092 / RW-093)

Lane: scripted doctor + health + CLI (no NIM / no OpenRouter) on
**v0.5.2**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-092 | 2026-09-19 | ops (scripted) — doctor skip-blocked chat (RW-086 quota shape) | Last Class C 429 still blocking; online doctor / scan must not re-hit chat | n/a | persist; doctor; --force re-probe; Retry-After expiry | none (health ping only) | **PASS** (unknown key_fp still skips; `--force` pings; expired Retry-After pings; scan default skips) | n/a; false DONE **0** | **N** | capability (Gen4 G4-3; Class C stays C) | Tests `test_live_use_campaign.py`. Needle OFF. Caps unchanged. No live PASS claim. |
| RW-093 | 2026-09-19 | ops (scripted) — campaign / operator workflow | Pause then `rad health` next-action; playbook; entitled → resume | 1 task | Class C pause; operator_status; CLI --json | default **60** unchanged | **PASS** (429 → wait, no chat; 403 pause → resume when entitled; playbook names E1–E3 / no live PASS required; free_lock drops paid) | hello.txt **absent** on pause; false DONE **0** | **N** | capability (Gen4 G4-3; Class C stays C) | Tests `test_live_use_campaign.py`. Needle OFF. Caps unchanged. No live PASS claim. |

# Scripted live-gate / provider health (RW-090 / RW-091)

Lane: scripted doctor + controller + health (no NIM / no OpenRouter) on
**v0.5.1**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-090 | 2026-09-19 | ops (scripted) — catalog-alive ≠ inference-entitled (RW-084 shape) | Doctor a pin whose GET /v1/models is 200 and chat/completions is 403 | n/a | catalog probe + 1-token chat ping | none (health ping only) | **PASS** (catalog 200 + chat 403 → doctor WARNING, not READY; last Class C persisted) | n/a; false DONE **0** | **N** | capability (Gen4 G4-2; Class C stays C) | Tests `test_provider_health_resume.py`. Needle OFF. Caps unchanged. No live PASS claim. |
| RW-091 | 2026-09-19 | ops (scripted) — last Class C persist + resume live-gate (RW-086 shape) | 403 pause then resume; 429 + Retry-After; resume after entitled brain recovers | 1 task | persist; resume gate; no second chat | default **60** unchanged | **PASS** (last Class C survives new RouterState; resume stays needs_user / no re-burn; 429 Retry-After visible; resume proceeds when entitled brain exists; free_lock drops paid) | hello.txt **absent** on gated resume; present after entitled resume; false DONE **0** | **N** | capability (Gen4 G4-2; Class C stays C) | Tests `test_provider_health_resume.py`. Needle OFF. Caps unchanged. No live PASS claim. |

# Scripted Class C provider doctrine (RW-089)

Lane: scripted planner + controller + router (no NIM / no OpenRouter) on
**v0.5.0**. Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-089 | 2026-09-19 | ops (scripted) — 403/429 Class C pause + free-first rotation | Write hello.txt; provider returns HTTP 403 or HTTP 429 | 1 task | raise ProviderError; recover; no retry | default **60** unchanged | **PASS** (403 → AUTH ask_user; 429 → RATE_LIMIT ask_user; attempts=1; 0 Repair; free 429 rotates; free_lock never calls paid; 503 still retries) | hello.txt **absent** on Class C pause; false DONE **0** | **N** | capability (Gen4 G4-1; Class C stays C) | Tests `test_provider_class_c.py`. Needle OFF. Caps unchanged. F-17 / E1–E3 / xxd / path-align / thrash Class A preserved. No live PASS claim. |

# Scripted budget-aware retry stop (RW-088)

Lane: scripted planner + controller (no NIM / no OpenRouter) on **v0.4.9**.
Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-088 | 2026-09-19 | coding (scripted) — stop leftover-eating retry/repair under tight max-tools | Write first.txt then later.txt; do not retry stuck work into leftover reserve | 3 tasks; later file independent of stuck | write first; one failed stuck attempt; yield; write later | default **60** unchanged; scripted cap **4** | **PASS** (stuck task not retried/repaired before later runs; later file ≥1 attempt + on disk; missing JSON still **not** VERIFIED) | `first.txt` + `later.txt` on disk; false DONE **0** | **N** | capability (Gen3 theme 3 slice E3; live quality stays **B**) | Tests `test_budget_aware_retry_stop.py`. Needle OFF. Caps unchanged. F-17 / F-26 / E1 / E2 / xxd / pip/DONE/mkdir/premature-test preserved. No live PASS claim. |

# Scripted independent later files (RW-087)

Lane: scripted planner + controller (no NIM / no OpenRouter) on **v0.4.8**.
Needle `existing` / off. Caps unchanged. **Not** a live PASS.

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-087 | 2026-09-19 | coding (scripted) — later independent fallback file under tight max-tools | Write first.txt and then burn leftover tools. Write later.txt. | fallback 3 tasks; later file `depends_on=[]` | write first; thrash consume; write later | default **60** unchanged; scripted cap **4** | **PASS** (later fallback file ≥1 attempt + on disk; early consume not COMPLETED; missing JSON still **not** VERIFIED) | `first.txt` + `later.txt` on disk; false DONE **0** | **N** | capability (Gen3 theme 3 slice E2; live quality stays **B**) | Tests `test_independent_later_files.py`. Needle OFF. Caps unchanged. F-17 / F-26 / E1 / xxd / pip/DONE/mkdir/premature-test preserved. Explicit LLM chains not rewritten. No live PASS claim. |

# Live OpenRouter retest of v0.4.7 (RW-086) — FAIL

Lane: operator production `rad objective run` on **v0.4.7** (tag `v0.4.7`,
`850aaf9c3a931a5ba119bdbb6ec73ae4a6fa73e9`). Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60** (this run used
`--max-tasks 8 --max-tools 12`). RW-058–085 are **not rewritten**. **Not** an
end-to-end PASS. Package **0.4.7** on the live run **and** this branch (no
bump). E1 remains shipped/scripted (RW-083). Live E1 **not confirmed**. xxd
Class A ENVIRONMENT thrash vs RW-085 **CLEARED**. Residual **B+C**. Live
OpenRouter free-model loop **paused** until `free-models-per-day` resets.
Live NIM loop remains **paused** (Class C).

Authoritative live facts: operator report for `obj_e1949b8f` /
`/tmp/rad_prod_rw086_81609c3b`. This agent did not re-run the live objective.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-086 | 2026-09-19 IST 10:13:07–10:23:22 | coding (live OpenRouter free) — v0.4.7 text_analyzer retest vs RW-085 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=`fallback`**, **attempts=2**, 4 tasks carved from goal newlines, `fit=true`, `compacted=false`, `estimated_tools=8`; t_febc5d2d Create package **COMPLETED** (attempts=1; VERIFIED); t_dc4db802 **RETRYING** (attempts=1; HTTP 429); t_1ca60866 / t_a4f4c8a6 **PENDING** (attempts=0) | tools **12/12** (`run_shell` 8, `write_file` 3, `read_file` 1 — **0** invented `DONE`); model calls **7.0/80** (provider=`openrouter`); retries **1.0/6**; wall ~615s / usage `seconds≈417.8`; process exit 2; money **`$0`** | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | task1 **VERIFIED** — actions ok (5 actions, 0 errors); `file_nonempty` input.txt OK (weak task checks). Objective checks **all package-joined** under `text_analyzer/` (not executed to PASS) | **MODEL_FAILURE** (HTTP **429** `free-models-per-day`) → retry another brain; then tool budget exhausted. 0 `xxd`/`hexdump`. 0 ENVIRONMENT. 0 repair-insert. 0 TaskYield. 0 leftover-budget dispatch | **B+C** — Class B (fallback PLAN / incomplete package / odd summary / chained fallback) + late Class C (429). xxd Class A live **N**. E1 live **N** | Provider **openrouter** / `nvidia/nemotron-3.5-lightning:free`. Home `/tmp/rad_prod_rw086_81609c3b`; `obj_e1949b8f`. Disk: workspace root **only** `text_analyzer/`. `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` present, alt schema. `test_analyzer.py` **absent**. README **absent**. Host still missing `xxd`/`hexdump`; model used `sha256sum` + `hashlib` / `cat -A`. False DONE **0**. Caps unchanged. Needle OFF. Stay **0.4.7**. Free-model loop **paused**. |

### RW-086 vs RW-085 / RW-081 / RW-084

| | RW-081 (v0.4.5 NIM) | RW-084 (v0.4.6 NIM) | RW-085 (v0.4.6 OpenRouter free) | RW-086 (v0.4.7 OpenRouter free) |
|---|---|---|---|---|
| home | `/tmp/rad_prod_rw081_5a76b128` | `/tmp/rad_prod_rw084_3d9cc3ac` | `/tmp/rad_prod_rw085_15d26f58` | `/tmp/rad_prod_rw086_81609c3b` |
| objective id | `obj_b6d32fcc` | `obj_a8118606` | `obj_3181e63d` | `obj_e1949b8f` |
| package | 0.4.5 | **0.4.6** | **0.4.6** | **0.4.7** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off | `existing` / off | `existing` / off |
| Status | `needs_user` @ 12/12 | `needs_user` @ **0/12** | `needs_user` @ **11/12** | `needs_user` @ **12/12** |
| Brain | nvidia / llama-3.2-11b-vision | nvidia **403** | **openrouter / nemotron-3.5-lightning:free** | **openrouter / nemotron-3.5-lightning:free** |
| PLAN | llm attempts=2 | fallback (provider fail) | **fallback** attempts=2 | **fallback** attempts=2 |
| `input.txt` sha256 | `bf69eb73…` OK | absent | `bf69eb73…` OK | `bf69eb73…` OK |
| `summary.json` | `{}` empty | absent | present, alt schema | present, alt schema |
| README | present | absent | **absent** | **absent** |
| `test_analyzer.py` | present (SyntaxError) | absent | present (exit 1) | **absent** |
| objective_checks | package-joined Y | package-joined Y (create only) | package-joined Y | package-joined Y |
| Root pollution | Y (root analyzer.py) | N/A | **N** | **N** |
| Recovery | none | MODEL_FAILURE | **ENVIRONMENT → repair** (`xxd`) | **MODEL_FAILURE** (429); 0 ENVIRONMENT |
| E1 leftover-budget yield | N/A (pre-E1) | not live-tested | **not live** (0 yields) | **not live** (0 TaskYield; task2 sequential) |
| Fake DONE | 0 | 0 | 0 | 0 |
| Residual class | **B** | **C** | **B** (+ Class A xxd → v0.4.7) | **B+C** (429) |

| metric | value |
|---|---|
| Package (live run) | **0.4.7** (tag `v0.4.7` / `850aaf9c3a931a5ba119bdbb6ec73ae4a6fa73e9`) |
| xxd Class A thrash | **CLEARED** — 0 `xxd`/`hexdump`; 0 ENVIRONMENT; 0 repair-insert. Host still missing `xxd`; model avoided it. Caveat: absence of thrash vs RW-085, not a positive classifier observation. Scripted RW-086 remains unit evidence |
| E1 live | **N** — task1 completed normally; 0 TaskYield / leftover-budget events. Scripted RW-083 remains unit evidence |
| vs RW-085 | xxd ENVIRONMENT thrash **gone**; task1 COMPLETED + task2 attempts=1; tools **12/12** vs **11/12**; **429 new** |
| Residual | **Class B+C** — fallback PLAN; incomplete package (no tests / README); odd `summary.json`; late HTTP **429** `free-models-per-day` |
| Operator decision (2026-09-19) | **pause** live OpenRouter free runs until `free-models-per-day` resets; NIM still Class C **paused** |
| RW-058–085 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. xxd Class A thrash cleared this trajectory. E1 not live. Pause free-model loop. Stay **0.4.7**. Do not claim live PASS. |

# Live OpenRouter retest of v0.4.6 (RW-085) — FAIL

Lane: operator production `rad objective run` on **v0.4.6** (tag `v0.4.6`,
`8f09be5839e25c236349121a4ec77606d0d5ed2d`). Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60** (this run used
`--max-tasks 8 --max-tools 12`). RW-058–084 are **not rewritten**. **Not** an
end-to-end PASS. Package **0.4.6** on the live run; this branch bumps to
**0.4.7** for optional checksum-utility ENVIRONMENT. E1 remains
shipped/scripted (RW-083). Live E1 **not confirmed**. Class C vs RW-084
**cleared**.

Authoritative live facts: operator report for `obj_3181e63d` /
`/tmp/rad_prod_rw085_15d26f58`. This agent did not re-run the live objective.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-085 | 2026-09-19 IST 09:34:38–09:57:47 | coding (live OpenRouter free) — v0.4.6 text_analyzer retest vs RW-081 / RW-084 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=`fallback`**, **attempts=2**, 4 tasks carved from goal newlines, `fit=true`, `compacted=false`, `estimated_tools=8`; t_07ad6720 Create package **BLOCKED** (depends on repair; verify FAILED); t_cdb9c8e2 / t_9b2837e2 / t_a51bef19 **BLOCKED** (attempts=0); t_1dfa6d3f Repair prerequisite **NEEDS_USER** (attempts=2) | tools **11/12** (`run_shell` 8, `write_file` 4, `run_python` 2, `read_file` 2, `list_dir` 2 — **0** invented `DONE`); model calls **14.0/80** (provider=`openrouter`); retries **2.0/6**; wall ~1389s event / usage `seconds≈928.8`; process exit 2; money **`$0`** | 11/12 | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task actions **ok=false** (5 actions, **1 error**: `xxd: not found` exit 127); `file_nonempty` input.txt OK. Objective checks **all package-joined** under `text_analyzer/` (2 checks; 0 bare) | **ENVIRONMENT_FAILURE** → `repair` (`xxd`); then VALIDATION retry; then replan → NEEDS_USER. 0 TaskYield. 0 leftover-budget dispatch | **B** residual (fallback PLAN / free-model quality / missing README / alt summary / failing tests / later tasks 0 attempts) + Class A `xxd` ENVIRONMENT (F-48 / v0.4.7). Class C **cleared**. E1 live **N** | Provider **openrouter** / `nvidia/nemotron-3.5-lightning:free`. Home `/tmp/rad_prod_rw085_15d26f58`; `obj_3181e63d`. Disk: workspace root **only** `text_analyzer/`. `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` present, alt schema. README **absent**. False DONE **0**. Caps unchanged. Needle OFF. |

### RW-085 vs RW-081 / RW-084

| | RW-081 (v0.4.5 NIM) | RW-084 (v0.4.6 NIM) | RW-085 (v0.4.6 OpenRouter free) |
|---|---|---|---|
| home | `/tmp/rad_prod_rw081_5a76b128` | `/tmp/rad_prod_rw084_3d9cc3ac` | `/tmp/rad_prod_rw085_15d26f58` |
| objective id | `obj_b6d32fcc` | `obj_a8118606` | `obj_3181e63d` |
| package | 0.4.5 | **0.4.6** | **0.4.6** (live) / **0.4.7** (this branch) |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off | `existing` / off |
| Status | `needs_user` @ 12/12 | `needs_user` @ **0/12** | `needs_user` @ **11/12** |
| Brain | nvidia / llama-3.2-11b-vision | nvidia **403** | **openrouter / nemotron-3.5-lightning:free** |
| PLAN | llm attempts=2 | fallback (provider fail) | **fallback** attempts=2 |
| `input.txt` sha256 | `bf69eb73…` OK | absent | `bf69eb73…` OK |
| `summary.json` | `{}` empty | absent | present, alt schema |
| README | present | absent | **absent** |
| objective_checks | package-joined Y | package-joined Y (create only) | package-joined Y |
| Root pollution | Y (root analyzer.py) | N/A | **N** |
| Recovery | none | MODEL_FAILURE | **ENVIRONMENT → repair** (`xxd`) |
| E1 leftover-budget yield | N/A (pre-E1) | not live-tested | **not live** (0 yields) |
| Fake DONE | 0 | 0 | 0 |
| Residual class | **B** | **C** | **B** (+ Class A xxd → v0.4.7) |

| metric | value |
|---|---|
| Package (live run) | **0.4.6** (tag `v0.4.6` / `8f09be5839e25c236349121a4ec77606d0d5ed2d`) |
| E1 live | **N** — fallback chain + ENVIRONMENT repair; 0 TaskYield. Scripted RW-083 remains unit evidence |
| vs RW-084 Class C | **cleared** — OpenRouter HTTP 200 / tools 11/12 / `$0` |
| Residual | **Class B** — fallback PLAN; wrong summary; missing README; failing tests; later tasks 0 attempts. Class A `xxd` ENVIRONMENT **CONFIRMED** (this patch) |
| RW-058–084 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. Class C cleared. E1 not live. Confirm Class A on `xxd` → v0.4.7. Do not claim live PASS. |

# Scripted optional checksum ENVIRONMENT (RW-086)

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-086 | 2026-09-19 | coding (scripted) — missing `xxd` ≠ ENVIRONMENT | RW-085 shape: ASCII-tree `text_analyzer/`; write input then `xxd` exit 127 | 2 planned (LLM) | write input + xxd noise; write analyzer | default **60** unchanged; scripted cap **12** | **PASS** (t1 VERIFIED despite xxd; t2 VERIFIED; no Repair prerequisite; empty JSON still **not** VERIFIED) | `text_analyzer/input.txt` + `analyzer.py` on disk; no root pollution; false DONE **0** | **N** — TOOL / action-noise, not Repair-prerequisite | **A** (Gen3 theme 3 slice F; live quality stays **B**) | Tests `test_xxd_environment.py`. Needle OFF. Caps unchanged. F-17 / F-26 / E1 / pip/DONE/mkdir/premature-test preserved. No live PASS claim. |

# Live NIM retest of v0.4.6 (RW-084) — BLOCKED Class C

Lane: operator production `rad objective run` on **v0.4.6** (tag `v0.4.6`,
`8f09be5839e25c236349121a4ec77606d0d5ed2d`). Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60** (this run used
`--max-tasks 8 --max-tools 12`). RW-058–083 are **not rewritten**. **Not** an
end-to-end PASS. Package **0.4.6** on the live run **and** this branch (no
bump). E1 remains shipped/scripted (RW-083). Live E1 gate **deferred**. Live
NIM loop **paused / Class C blocked**.

Authoritative live facts: operator report for `obj_a8118606` /
`/tmp/rad_prod_rw084_3d9cc3ac`. This agent did not re-run NIM.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-084 | 2026-09-19 IST 08:34:20–08:34:22 | coding (live NIM) — v0.4.6 text_analyzer retest vs RW-081 | production ASCII-tree `text_analyzer/` layout (analyzer.py, exact 3-line input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off; NIM 11B intended | `PLAN_CREATED` **source=`fallback`** (LLM plan unavailable), 4 tasks carved from goal newlines; t_ad22c64b Create layout **NEEDS_USER** (`MODEL_FAILURE`; 3 attempts; HTTP 403); t_e74ab370 / t_5cb4bd78 / t_bf095942 **BLOCKED** (unmet prereq) | tools **0/12** (none); model calls **3.0/80** (all nvidia HTTP 403); retries **2.0/6**; wall ~1.5s / usage `seconds≈0.91`; process exit 2 | 0/12 unused | **BLOCKED Class C** (`needs_user`); **NOT DONE**; 0 tool calls | none — no task reached verify. objective_checks package-joined at create (`json_valid text_analyzer/summary.json`; `shell_ok python3 text_analyzer/test_analyzer.py`) — **never executed** | retry×2 (`MODEL_FAILURE`, another brain) then replan → no usable plan → NEEDS_USER. 0 ENVIRONMENT. 0 TaskYield. 0 leftover-budget dispatch | **C** (NVIDIA NIM inference unauthorized). E1 **not live-tested**. Class A/B **not live-hit** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw084_3d9cc3ac`; `obj_a8118606`. `GET /v1/models` **200**; all `chat/completions` **403 Authorization failed**. Workspace empty; `text_analyzer/` absent. False DONE **0**. Caps unchanged. Needle OFF. Stay **0.4.6**. Live NIM **paused**. |

### RW-084 vs RW-081 (E1 live comparison **N**)

| | RW-081 (v0.4.5) | RW-084 (v0.4.6) |
|---|---|---|
| home | `/tmp/rad_prod_rw081_5a76b128` | `/tmp/rad_prod_rw084_3d9cc3ac` |
| objective id | `obj_b6d32fcc` | `obj_a8118606` |
| package | 0.4.5 | **0.4.6** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| Status | `needs_user` @ 12/12 tools | `needs_user` @ **0/12** tools (`MODEL_FAILURE`) |
| NIM | worked (9 model calls) | **403** inference (`/v1/models` **200**) |
| E1 leftover-budget yield | N/A (pre-E1) | **not live-tested** |
| `input.txt` sha256 | `bf69eb73…` OK | **absent** |
| objective_checks | package-joined Y (executed path) | package-joined Y (create only; never executed) |
| Residual class | **B** | **C** |
| Fake DONE | 0 | 0 |

| metric | value |
|---|---|
| Package (live run) | **0.4.6** (tag `v0.4.6` / `8f09be5839e25c236349121a4ec77606d0d5ed2d`) |
| E1 live | **N** — Class C blocked the gate. Scripted RW-083 remains unit evidence |
| vs RW-081 E1 | **cannot compare** — RW-081 had working inference |
| Residual | **Class C** — refresh NIM inference credentials; do not invent a product fix |
| Prior Class A (mkdir / premature-test / pip / invented DONE) | **not hit** |
| Operator decision (2026-09-19) | **pause** live NIM loop until inference-entitled credentials work on integrate.api; do not keep retrying keys that list models but fail chat |
| RW-058–083 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **BLOCKED Class C**. Stay **0.4.6**. Live NIM **paused**. Do not claim E1 live. |

# Scripted E1 leftover-budget dispatch (RW-083)

| id | date | task | goal (short) | plan | steps | tools | result | disk / verify | ENVIRONMENT? | class | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-083 | 2026-09-18 | coding (scripted) — task-boundary yield / leftover-budget dispatch | t1 writes `first.txt`; t2 thrashes pip/echo and would burn remaining tools; t3 independent `later.txt` | 3 planned (LLM): t3 depends on t1 only | t1 write, t2 10× echo, t3 write | default **60** unchanged; scripted cap **4** | **PASS** (t1 VERIFIED; t2 yielded RETRYING; t3 VERIFIED ≥1 attempt; missing JSON still **not** VERIFIED; chained later file stays PENDING) | `first.txt` + `later.txt` on disk; `stuck.txt` absent; checkpoint intact; false DONE **0** | n/a (budget yield, not ENVIRONMENT) | **A** (Gen3 theme 3 slice E1; live 11B quality stays **B**) | Tests `test_task_boundary_yield.py`. Needle OFF. Caps unchanged. No new checkpoint format. Live NIM not required. RW-081 Class B live facts preserved. |

# Live NIM retest of v0.4.5 (RW-081)

Lane: operator production `rad objective run` on **v0.4.5** (tag `v0.4.5`,
`32e9fe87`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 8 --max-tools 12`).
RW-058–080 are **not rewritten**. **Not** an end-to-end PASS. Package **0.4.5**
on the live run **and** this branch (no bump; pip/root-pollution Class A **NOT
CONFIRMED**). Does **not** claim live 11B text_analyzer@12 now PASS.

Authoritative live facts: operator report for `obj_b6d32fcc` /
`/tmp/rad_prod_rw081_5a76b128`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-081 | 2026-09-18 IST 22:28:43–22:30:12 | coding (live NIM) — v0.4.5 text_analyzer retest vs RW-079 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=2** (4 tasks, **no repair**, `fit=true`, `compacted=false`, `estimated_tools=8`); t_930abfbd Create directory+input **COMPLETED / VERIFIED**; t_99bd2247 Write analyzer.py **RUNNING** at stop; Write test **PENDING**; README **COMPLETED** (already-satisfied) | tools 12/12 (`write_file`×6, `run_shell`×6 — **0** invented `DONE`; pip `-r` **attempted**×1 error); model calls 9/80; retries 0/6; wall ~89s / spent ≈41.5s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task machine checks **passed**; actions **ok=true** despite 1 mkdir File-exists error (8 actions, 1 error) → **VERIFIED**. Objective checks **all package-joined** under `text_analyzer/` (3 checks; 0 bare). Second task never reached verify | **none** (retries=0). No ENVIRONMENT_FAILURE. No Repair-prerequisite. pip `-r` error present but budget stop before verify | **B** residual (11B/budget / second-task pip+echo). Theme 1 ASCII-tree obj-checks **Y**. Theme 2 **Y**. mkdir File-exists Class A **live: Y**. Premature-test ENVIRONMENT Class A **live: N**. Pip/root-pollution Class A **NOT CONFIRMED** (F-44 / RW-082) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw081_5a76b128`; `obj_b6d32fcc`. Disk: workspace root `text_analyzer/` **+** stray **`analyzer.py`** (echo redirect). `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **`{}` valid, empty**. `test_analyzer.py` **SyntaxError**. README 393 B. False DONE **0**. Caps unchanged. Needle OFF. |

### RW-081 vs RW-079 (same 11B / tools=12 control)

| | RW-079 (v0.4.4) | RW-081 (v0.4.5) |
|---|---|---|
| home | `/tmp/rad_prod_rw079_803109d5` | `/tmp/rad_prod_rw081_5a76b128` |
| objective id | `obj_a0781a42` | `obj_b6d32fcc` |
| package | 0.4.4 | **0.4.5** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** attempts **1** (5 tasks + **repair**) | **llm** attempts **2** (4 tasks, **no repair**) |
| Path-alignment (disk/tasks) | **Y** | **Y** |
| Objective checks | **all package-joined** `text_analyzer/…` (6; 0 bare) | **all package-joined** `text_analyzer/…` (3; 0 bare) |
| mkdir File-exists | **N** — mkdir **succeeded** (path not exercised) | **Y** → action-noise → **VERIFIED** |
| Recovery | **ENVIRONMENT_FAILURE** → **repair** (premature test) | **none** (retries=0) |
| Root pollution | NO | **Y** (root `analyzer.py` from `echo >`) |
| `input.txt` | correct 3-line `bf69eb73…` | **same** correct 3-line `bf69eb73…` |
| Package `summary.json` | valid JSON, wrong counts | **`{}` valid, empty** |
| tools | 12/12 (`write_file`×6, `run_shell`×6; **0** pip, **0** invented DONE) | 12/12 (`write_file`×6, `run_shell`×6; pip `-r`×1 error; **0** invented DONE) |
| false DONE | **0** | **0** |
| Theme 1 | PASS signal (disk/tasks/obj-checks) | **PASS signal (disk/tasks/obj-checks)** |
| Theme 2 | contracts hold; pip/DONE still **0** | contracts hold; 0 invented DONE; pip `-r` attempted, no ENVIRONMENT repair |
| Residual class | **B** (+ premature-test ENVIRONMENT Class A → v0.4.5) | **B** (pip/echo thrash + quality; mkdir live Y; premature-test live N) |

| metric | value |
|---|---|
| Package (live run) | **0.4.5** (tag `v0.4.5` / `32e9fe87`) |
| Theme 1 (path-aligned checks) | **Y** on disk + task checks **and** merged objective_checks (ASCII-tree `package_dir` **still Y**) |
| Theme 2 (multi-file contracts) | **Y** — package-joined checks; correct 3-line input |
| Residual | **Class B** — pip/echo budget burn under tools=12; root `analyzer.py` pollution; empty `summary.json`; SyntaxError test; analyzer task starved |
| Class A pip/DONE first-task thrash | **live-consistent** (0 invented DONE). pip `-r` attempted×1; **no** ENVIRONMENT→repair (budget stop before verify). Do not re-litigate v0.4.3 |
| Class A mkdir File-exists actions | **live Y** — first live confirm in this series. Task **VERIFIED** despite File-exists action error (v0.4.4 win) |
| Class A premature-test ENVIRONMENT | **not live-hit** (no early `python …/test_*.py`; 0 ENVIRONMENT repair). Unit RW-080 remains the evidence. Do not regress |
| Class A pip thrash + root pollution | **NOT CONFIRMED** (RW-082 / F-44). Stay **0.4.5**. No product bump |
| RW-058–080 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. mkdir File-exists **live-confirmed**. Do not claim live 11B@12 PASS. Pip/root-pollution is Class B. Multi-step checkpoint stays planned. |

# Investigation — pip thrash + root pollution (RW-082)

Lane: deterministic / scripted on **v0.4.5**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–081 are
**not rewritten**. Package stays **0.4.5** (no bump). Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-082 | 2026-09-18 | investigation (scripted; no NIM) | RW-081 shape: ASCII-tree `text_analyzer/`; root `echo > analyzer.py` vs package checks; pip `-r` missing; mkdir File-exists | 2 planned (LLM) | write package + mkdir noise; pip `-r` + echo root; root-only write counterfactual | default **60** unchanged | **no RAD defect**; pip/root-pollution Class A **NOT CONFIRMED** | package checks **not** satisfied by root `analyzer.py`; package file **unchanged** when echo lands at root; empty `{}` + missing json_field **not** VERIFIED; mkdir File-exists still VERIFIED | pip `-r` missing → TOOL **not** Repair prerequisite; budget stop mid-pip/echo → `needs_user` without ENVIRONMENT repair | **NONE** (not A) | Tests `test_pip_root_pollution_investigation.py`. False DONE **0**. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree, pip/DONE, mkdir, premature-test preserved. Needle OFF. Caps unchanged. **No patch. No v0.4.6.** |

# Live NIM retest of v0.4.4 (RW-079)

Lane: operator production `rad objective run` on **v0.4.4** (tag `v0.4.4`,
`acb61997`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 8 --max-tools 12`).
RW-058–078 are **not rewritten**. **Not** an end-to-end PASS. Package **0.4.4**
on the live run; this change bumps to **0.4.5** for premature-test ENVIRONMENT
(does **not** claim live 11B text_analyzer@12 now PASS).

Authoritative live facts: operator report for `obj_a0781a42` /
`/tmp/rad_prod_rw079_803109d5`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-079 | 2026-09-18 IST 22:07:24–22:09:09 | coding (live NIM) — v0.4.4 text_analyzer retest vs RW-077 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=1** (5 tasks + 1 repair, `fit=true`, `compacted=false`, `estimated_tools=10`); t_452be0d3 Create directory **RETRYING** (waiting on repair); Write input.txt **COMPLETED**; analyzer / test **PENDING**; README **COMPLETED**; repair t_eae607b4 **RUNNING** at stop | tools 12/12 (`write_file`×6, `run_shell`×6 — **0** pip, **0** invented `DONE`); model calls 9/80; retries 1/6; wall ~105s / spent ≈67.2s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task machine `file_exists` directory **passed**; all produced artifacts nonempty **passed**; overall **FAILED** on **actions** (8 actions / 1 error: premature `python text_analyzer/test_analyzer.py` No such file). **Not** mkdir File-exists. Objective checks **all package-joined** under `text_analyzer/` (6 checks; 0 bare) | Attempt 1 **ENVIRONMENT_FAILURE** → `repair` (premature test No-such-file). **Not** mkdir File-exists; **not** pip-requirements | **B** residual (11B/budget / first-task + ENVIRONMENT repair). Theme 1 ASCII-tree obj-checks **Y**. Theme 2 **Y**. mkdir File-exists Class A **live: N**. Premature-test ENVIRONMENT is Class A (F-42 / v0.4.5) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw079_803109d5`; `obj_a0781a42`. Disk: workspace root **only** `text_analyzer/` (no root pollution). `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **valid JSON, wrong counts** (`lines=3, words=7, characters=39` vs true 3 / 13 / 76). `analyzer.py` stdlib. `test_analyzer.py` **wrong oracles** (`words==9` / `chars==51`). README 166 B. False DONE **0**. Caps unchanged. Needle OFF. |

### RW-079 vs RW-077 (same 11B / tools=12 control)

| | RW-077 (v0.4.3) | RW-079 (v0.4.4) |
|---|---|---|
| home | `/tmp/rad_prod_rw077_0a8393f8` | `/tmp/rad_prod_rw079_803109d5` |
| objective id | `obj_3da359c5` | `obj_a0781a42` |
| package | 0.4.3 | **0.4.4** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** attempts **1** (5 tasks) | **llm** attempts **1** (5 tasks + **repair**) |
| Path-alignment (disk/tasks) | **Y** | **Y** |
| Objective checks | **all package-joined** `text_analyzer/…` (0 bare) | **all package-joined** `text_analyzer/…` (0 bare) |
| mkdir File-exists | **Y** — TOOL_FAILURE retry | **N** — mkdir **succeeded** (path not exercised) |
| Recovery | TOOL_FAILURE → retry_with_hint | **ENVIRONMENT_FAILURE** → **repair** (premature test) |
| Root pollution | NO | NO |
| `input.txt` | correct 3-line `bf69eb73…` | **same** correct 3-line `bf69eb73…` |
| Package `summary.json` | present but empty/invalid | **valid JSON, wrong counts** |
| tools | 12/12 (`write_file`×4, `run_shell`×8; **0** pip, **0** fake DONE) | 12/12 (`write_file`×6, `run_shell`×6; **0** pip, **0** invented DONE) |
| false DONE | **0** | **0** |
| Theme 1 | PASS signal (disk/tasks/obj-checks) | **PASS signal (disk/tasks/obj-checks)** |
| Theme 2 | contracts hold; pip/DONE Class A **gone** | contracts hold; pip/DONE still **0** |
| Residual class | **B** (+ mkdir File-exists actions Class A → v0.4.4) | **B** (+ premature-test ENVIRONMENT Class A → v0.4.5) |

| metric | value |
|---|---|
| Package (live run) | **0.4.4** (tag `v0.4.4` / `acb61997`) |
| Theme 1 (path-aligned checks) | **Y** on disk + task checks **and** merged objective_checks (ASCII-tree `package_dir` **still Y**) |
| Theme 2 (multi-file contracts) | **Y** — package-joined checks; correct 3-line input |
| Residual | **Class B** — wrong summary counts, weak tests, tools 12/12 on first-task + ENVIRONMENT repair before later package tasks completed as tasks |
| Class A pip/DONE first-task thrash | **live-consistent** (absent this run). 0× pip; 0× invented DONE |
| Class A mkdir File-exists actions | **not live-hit** (mkdir succeeded). Unit RW-078 remains the evidence. Do not regress |
| Class A premature-test ENVIRONMENT | **confirmed** (deterministic); patched as v0.4.5. Directory `file_exists` passed; actions FAILED; ENVIRONMENT repair burned tools=12 |
| RW-058–078 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. v0.4.4 mkdir File-exists **not live-confirmed**. Do not claim live 11B@12 PASS. Theme 3 slice D ships as v0.4.5 (premature-test ENVIRONMENT). Multi-step checkpoint stays planned. |

# Gen3 — v0.4.5 premature-test ENVIRONMENT (RW-080)

Lane: deterministic / scripted on **v0.4.5**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–079 are
**not rewritten**. Package **0.4.4 → 0.4.5**. Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-080 | 2026-09-18 | coding (scripted) — premature-test ENVIRONMENT | RW-079 shape: ASCII-tree `text_analyzer/`; first task `write_file` creates the tree then `python3 text_analyzer/test_analyzer.py` can't-open-file; later task writes `analyzer.py` | 2 planned (LLM) | write input + premature test fail, then write analyzer | default **60** unchanged | **PASS** (premature python test **not** ENVIRONMENT; no Repair prerequisite; first task VERIFIED from directory check; later task runs; empty JSON still **not** VERIFIED) | first-task directory check **VERIFIED** despite premature-test noise; objective not rubber-stamped when JSON invalid; no workspace-root pollution | python can't-open-file → TOOL **not** Repair prerequisite; treated as action noise when checks passed | **A** (Gen3 theme 3 slice D; live 11B quality stays **B**) | Tests `test_premature_test_env.py`. False DONE **0**. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree, pip/DONE, mkdir File-exists preserved. Needle OFF. Caps unchanged. Live NIM not required. RW-079 Class B live facts preserved. |

# Live NIM retest of v0.4.3 (RW-077)

Lane: operator production `rad objective run` on **v0.4.3** (tag `v0.4.3`,
`99099b8a`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 8 --max-tools 12`).
RW-058–076 are **not rewritten**. **Not** an end-to-end PASS. Package **0.4.3**
on the live run; this change bumps to **0.4.4** for mkdir already-exists
action noise (does **not** claim live 11B text_analyzer@12 now PASS).

Authoritative live facts: operator report for `obj_3da359c5` /
`/tmp/rad_prod_rw077_0a8393f8`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-077 | 2026-09-18 IST 21:45:54–21:47:37 | coding (live NIM) — v0.4.3 text_analyzer retest vs RW-075 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=1** (5 tasks, `fit=true`, `compacted=false`, `estimated_tools=10`); t_00a0b182 Create directory **RUNNING** at stop (retry); Write input.txt **COMPLETED**; analyzer / test / README **PENDING** | tools 12/12 (`write_file`×4, `run_shell`×8 — **0** pip, **0** fake `DONE`); model calls 9/80; retries 1/6; wall ~103s / spent ≈55.9s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task machine `file_exists` directory **passed**; overall **FAILED** on **actions** (8 actions / 1 error: `mkdir text_analyzer` File exists after `write_file` already created the tree). Objective checks **all package-joined** under `text_analyzer/` (4 checks; 0 bare) | Attempt 1 **TOOL_FAILURE** → `retry_with_hint` (mkdir File exists). **Not** ENVIRONMENT. **No** Repair-prerequisite insert | **B** residual (11B/budget / first-task mkdir thrash). Theme 1 ASCII-tree obj-checks **Y**. Theme 2 **Y**. v0.4.3 pip/DONE Class A **live-consistent** (absent). mkdir File-exists failing a check-passing task is Class A (F-40 / v0.4.4) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw077_0a8393f8`; `obj_3da359c5`. Disk: workspace root **only** `text_analyzer/` (no root pollution). `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present but empty/invalid** (0 bytes). `analyzer.py` stdlib. `test_analyzer.py` unittest **wrong oracles** (`words==6` / `chars==31` vs 13 / 76). README 16 B (`# text_analyzer`). False DONE **0**. Caps unchanged. Needle OFF. |

### RW-077 vs RW-075 (same 11B / tools=12 control)

| | RW-075 (v0.4.2) | RW-077 (v0.4.3) |
|---|---|---|
| home | `/tmp/rad_prod_rw075_c2d7abdd` | `/tmp/rad_prod_rw077_0a8393f8` |
| objective id | `obj_476d5f0e` | `obj_3da359c5` |
| package | 0.4.2 | **0.4.3** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** attempts **1** (4 tasks) | **llm** attempts **1** (**5 tasks**) |
| Path-alignment (disk/tasks) | **Y** | **Y** |
| Objective checks | **all package-joined** `text_analyzer/…` (0 bare) | **all package-joined** `text_analyzer/…` (0 bare) |
| mkdir / ENVIRONMENT thrash | **Y** — ENVIRONMENT on pip/`requirements.txt` → Repair prerequisite | **N** — TOOL_FAILURE only (mkdir File exists); **no** ENVIRONMENT; **no** Repair-prerequisite |
| Root pollution | NO | NO |
| `input.txt` | correct 3-line `bf69eb73…` | **same** correct 3-line `bf69eb73…` |
| Package `summary.json` | missing | **present but empty/invalid** |
| tools | 12/12 (`write_file`×6, pip×4, fake DONE×2) | 12/12 (`write_file`×4, `run_shell`×8; **0** pip, **0** fake DONE) |
| false DONE | **0** | **0** |
| Theme 1 | PASS signal (disk/tasks/obj-checks) | **PASS signal (disk/tasks/obj-checks)** |
| Theme 2 | contracts hold; pip ENVIRONMENT misclass | contracts hold; pip/DONE Class A **gone** |
| Residual class | B (+ pip ENVIRONMENT Class A → v0.4.3) | **B** (+ mkdir File-exists actions Class A → v0.4.4) |

| metric | value |
|---|---|
| Package (live run) | **0.4.3** (tag `v0.4.3` / `99099b8a`) |
| Theme 1 (path-aligned checks) | **Y** on disk + task checks **and** merged objective_checks (ASCII-tree `package_dir` **still Y**) |
| Theme 2 (multi-file contracts) | **Y** — package-joined checks; correct 3-line input; mkdir not ENVIRONMENT |
| Residual | **Class B** — empty/invalid `summary.json`, weak tests, thin README, tools 12/12 on first-task mkdir retry before later package tasks |
| Class A pip/DONE first-task thrash | **live-consistent** (absent this run). 0× pip; 0× fake DONE; 0× ENVIRONMENT |
| Class A mkdir File-exists actions | **confirmed** (deterministic); patched as v0.4.4. Directory `file_exists` passed; actions FAILED; TOOL_FAILURE retry burned tools=12 |
| RW-058–076 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. v0.4.3 pip/DONE fix **holds**. Do not claim live 11B@12 PASS. Theme 3 slice C ships as v0.4.4 (mkdir already-exists action noise). Multi-step checkpoint stays planned. |

# Gen3 — v0.4.4 mkdir already-exists action noise (RW-078)

Lane: deterministic / scripted on **v0.4.4**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–077 are
**not rewritten**. Package **0.4.3 → 0.4.4**. Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-078 | 2026-09-18 | coding (scripted) — mkdir already-exists action noise | RW-077 shape: ASCII-tree `text_analyzer/`; first task `write_file` creates the tree then `mkdir text_analyzer` File exists; later task writes `analyzer.py` | 2 planned (LLM) | write input + mkdir fail, then write analyzer | default **60** unchanged | **PASS** (mkdir File-exists **not** ENVIRONMENT; no Repair prerequisite; first task VERIFIED from directory check; later task runs; empty JSON still **not** VERIFIED) | first-task directory check **VERIFIED** despite mkdir File-exists noise; objective not rubber-stamped when JSON invalid; no workspace-root pollution | mkdir File exists → TOOL **not** Repair prerequisite; treated as action noise when checks passed | **A** (Gen3 theme 3 slice C; live 11B quality stays **B**) | Tests `test_mkdir_already_exists_actions.py`. False DONE **0**. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree, pip/DONE thrash preserved. Needle OFF. Caps unchanged. Live NIM not required. RW-077 Class B live facts preserved. |

# Live NIM retest of v0.4.2 (RW-075)

Lane: operator production `rad objective run` on **v0.4.2** (tag `v0.4.2`,
`feb8a4ec`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 8 --max-tools 12`).
RW-058–074 are **not rewritten**. **Not** an end-to-end PASS. Package **0.4.2**
on the live run; this change bumps to **0.4.3** for first-task thrash
(does **not** claim live 11B text_analyzer@12 now PASS).

Authoritative live facts: operator report for `obj_476d5f0e` /
`/tmp/rad_prod_rw075_c2d7abdd`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-075 | 2026-09-18 IST 21:20:12–21:21:38 | coding (live NIM) — v0.4.2 text_analyzer retest vs RW-073 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=1** (4 tasks, `fit=true`, `compacted=false`, `estimated_tools=8`); first task RETRYING (waiting on repair); analyzer/tests PENDING; README COMPLETED; repair RUNNING at stop | tools 12/12 (`write_file`×6, `run_shell`×4 pip fails, fake `DONE`×2); model calls 12/80; retries 2/6; wall ~87s / spent ≈53.6s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task machine checks **passed** (`file_line_count` + `file_contains` under `text_analyzer/`); overall FAILED on **actions** (4 shell errors, then fake `DONE` tool errors on repair). Objective checks **all package-joined** under `text_analyzer/` (8 checks; 0 bare) | Attempt 1 **ENVIRONMENT_FAILURE** → `repair` (4× `pip install -r …requirements.txt` file-not-found → “missing dependency/file”). Attempt 2 **TOOL_FAILURE** → `retry_with_hint` (unknown tool `DONE: …`) | **B** residual (11B/budget / first-task thrash). Theme 1 ASCII-tree obj-checks **Y** (Class A **live-confirmed**). Theme 2 **Y**. New/residual ENVIRONMENT misclass on missing `requirements.txt` is Class A (F-38 / v0.4.3) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw075_c2d7abdd`; `obj_476d5f0e`. Disk: workspace root **only** `text_analyzer/` (no root pollution). `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **missing**. `analyzer.py` stdlib. `test_analyzer.py` unittest **wrong oracles** (`words==6` / `characters==31` vs 13 / 76). README 247 B. False DONE **0**. Caps unchanged. Needle OFF. |

### RW-075 vs RW-073 (same 11B / tools=12 control)

| | RW-073 (v0.4.1) | RW-075 (v0.4.2) |
|---|---|---|
| home | `/tmp/rad_prod_rw073_46da6971` | `/tmp/rad_prod_rw075_c2d7abdd` |
| objective id | `obj_d8bd898a` | `obj_476d5f0e` |
| package | 0.4.1 | **0.4.2** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** attempts **2** (4 tasks) | **llm** attempts **1** (**4 tasks**) |
| Path-alignment (disk/tasks) | **Y** | **Y** |
| Objective checks | contracts merged but inferred paths **bare** | **all package-joined** `text_analyzer/…` (0 bare) |
| mkdir / ENVIRONMENT thrash | **N** — PERMISSION after `rm -rf` block | **Y** — ENVIRONMENT on pip/`requirements.txt` → Repair prerequisite |
| Root pollution | NO | NO |
| `input.txt` | correct 3-line `bf69eb73…` | **same** correct 3-line `bf69eb73…` |
| Package `summary.json` | missing | **missing** |
| tools | 12/12 | 12/12 |
| false DONE | **0** | **0** |
| Theme 1 | PASS signal (disk/tasks); obj-checks bare | **PASS signal (disk/tasks/obj-checks)** |
| Theme 2 | contracts + mkdir-class **live** | contracts hold; pip ENVIRONMENT is a new misclass |
| Residual class | B | **B** (+ pip ENVIRONMENT Class A → v0.4.3) |

| metric | value |
|---|---|
| Package (live run) | **0.4.2** (tag `v0.4.2` / `feb8a4ec`) |
| Theme 1 (path-aligned checks) | **Y** on disk + task checks **and** merged objective_checks (ASCII-tree `package_dir` **live-confirmed**) |
| Theme 2 (multi-file contracts) | **Y** — `json_valid` / `file_line_count` / `shell_ok` package-joined; correct 3-line input |
| Residual | **Class B** — missing `summary.json`, weak tests, tools 12/12 on pip + fake `DONE` before later package tasks |
| Class A ASCII-tree package_dir | **live-confirmed** (bare residual **closed**). Did **not** cause this live stop (budget cut before objective gate) |
| Class A first-task thrash | **confirmed** (deterministic); patched as v0.4.3. pip-missing-requirements was ENVIRONMENT repair; DONE-as-tool failed a check-passing task |
| RW-058–074 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. ASCII-tree join **holds**. Do not claim live 11B@12 PASS. Theme 3 slice B ships as v0.4.3 (first-task thrash). Multi-step checkpoint stays planned. |

# Gen3 — v0.4.3 first-task thrash (RW-076)

Lane: deterministic / scripted on **v0.4.3**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–075 are
**not rewritten**. Package **0.4.2 → 0.4.3**. Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-076 | 2026-09-18 | coding (scripted) — first-task thrash | RW-075 shape: ASCII-tree `text_analyzer/`; first task writes 3-line `input.txt` then `pip install -r` missing requirements + unknown tool `DONE:`; later task writes `analyzer.py` | 2 planned (LLM) | write input + pip fail + DONE tool, then write analyzer | default **60** unchanged | **PASS** (pip-missing-requirements **not** ENVIRONMENT; no Repair prerequisite; first task VERIFIED from file checks; later task runs; missing-artifact DONE is **not** VERIFIED) | first-task file checks **VERIFIED** despite pip/DONE noise; objective not rubber-stamped when files absent; no workspace-root pollution | pip -r missing file → TOOL/VALIDATION **not** Repair prerequisite; invented DONE is protocol noise when checks passed | **A** (Gen3 theme 3 slice B; live 11B quality stays **B**) | Tests `test_first_task_thrash_*`. False DONE **0**. F-17 / F-26 preserved. Path-aligned, multifile, ASCII-tree preserved. Needle OFF. Caps unchanged. Live NIM not required. RW-075 Class B live facts preserved. |

# Live NIM retest of v0.4.1 (RW-073)

Lane: operator production `rad objective run` on **v0.4.1** (tag `v0.4.1`,
`387bd83a`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 8 --max-tools 12`).
RW-058–072 are **not rewritten**. **Not** an end-to-end PASS. Package **0.4.1**
on the live run; this change bumps to **0.4.2** for ASCII-tree `package_dir`
(does **not** claim live 11B text_analyzer@12 now PASS).

Authoritative live facts: operator report for `obj_d8bd898a` /
`/tmp/rad_prod_rw073_46da6971`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-073 | 2026-09-18 IST 20:39:05–20:41:06 | coding (live NIM) — v0.4.1 text_analyzer retest vs RW-071 | production ASCII-tree `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=2** (4 tasks, `fit=true`, `compacted=false`, `estimated_tools=8`); t_d4defdf3 RUNNING at stop (retry 3); later package tasks PENDING | tools 12/12 (`write_file` dominant; `run_shell` mkdir/`rm -rf`; unknown tool `DONE`); model calls 14/80; retries 2/6; wall ~63s reported / ~121s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task machine checks **passed** (`file_exists` + `file_line_count` under `text_analyzer/`); overall FAILED on **actions** (shell error/block, then `DONE` tool error). Objective inferred checks **bare** (`json_valid summary.json`, `file_line_count input.txt`, `shell_ok python3 test_analyzer.py`) + LLM `file_min_bytes text_analyzer/README.md` | **PERMISSION_FAILURE** → `retry_with_hint` (mkdir already-exists then **`rm -rf` blocked**; not ENVIRONMENT / no Repair prerequisite). Attempt 2 sticky PERMISSION + fake tool `DONE` → `unknown tool: DONE`; machine checks still ✓. Attempt 3 cut mid-task at budget | **B** residual (11B/budget). Theme 1 disk/tasks **Y**; obj-checks **partial/bare** (ASCII-tree `package_dir` miss). Theme 2 **Y**. ASCII-tree Class A closed as v0.4.2 | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw073_46da6971`; `obj_d8bd898a`. Disk: workspace root **only** `text_analyzer/` (no root pollution). `input.txt` **PASS** 3-line sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **missing**. `analyzer.py` stdlib with import-time side effect. `test_analyzer.py` unittest **no count assertions**. README ~479 B. False DONE **0**. Caps unchanged. Needle OFF. |

### RW-073 vs RW-071 (same 11B / tools=12 control)

| | RW-071 (v0.4.0) | RW-073 (v0.4.1) |
|---|---|---|
| home | `/tmp/rad_prod_rw071_7811425c` | `/tmp/rad_prod_rw073_46da6971` |
| objective id | `obj_d662224b` | `obj_d8bd898a` |
| package | 0.4.0 | **0.4.1** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** attempts **1** (6 tasks) | **llm** attempts **2** (**4 tasks**) |
| Path-alignment (disk/tasks) | **Y** | **Y** |
| Objective checks | path-aligned LLM paths | contracts **merged** (`json_valid` / `file_line_count` / `shell_ok`) but inferred paths **bare** |
| mkdir / ENVIRONMENT thrash | **Y** — ENVIRONMENT → Repair prerequisite | **N** — PERMISSION after `rm -rf` block; **no** repair-insert thrash |
| Root pollution | NO | NO |
| `input.txt` | wrong 1-line `9bf9660f…` | **correct 3-line `bf69eb73…`** |
| Package `summary.json` | present, empty/invalid | **missing** |
| tools | 12/12 | 12/12 |
| false DONE | **0** | **0** |
| Theme 1 | PASS signal | PASS signal (disk/tasks); objective infer bare |
| Theme 2 | (pre-patch baseline) | contracts + mkdir-class fix **live** |
| Residual class | B | **B** |

| metric | value |
|---|---|
| Package (live run) | **0.4.1** (tag `v0.4.1` / `387bd83a`) |
| Theme 1 (path-aligned checks) | **Y** on disk + task checks; **partial** on merged objective_checks (ASCII-tree `infer_package_dir` → None) |
| Theme 2 (multi-file contracts) | **Y** — `json_valid` / `file_line_count` / `shell_ok` present; mkdir already-exists is PERMISSION not ENVIRONMENT; correct 3-line input |
| Residual | **Class B** — missing `summary.json`, weak tests, tools 12/12 on permission retries + fake `DONE` |
| Class A ASCII-tree package_dir | **confirmed** (deterministic); patched as v0.4.2. Did **not** cause this live stop (budget cut before objective gate) |
| RW-058–072 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. Theme 1/2 hold. Do not claim live 11B@12 PASS. Theme 3 scoped; slice A ships as v0.4.2 (ASCII-tree `package_dir`). Remaining longer-horizon slices stay planned. |

# Gen3 — v0.4.2 ASCII-tree package_dir (RW-074)

Lane: deterministic / scripted on **v0.4.2**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–073 are
**not rewritten**. Package **0.4.1 → 0.4.2**. Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-074 | 2026-09-18 | coding (scripted) — ASCII-tree `package_dir` | RW-073 shape: ASCII-tree `text_analyzer/` + `├── file`; LLM plan has prefixed task checks + `file_min_bytes` README; inferred contracts would have been bare `summary.json` / `input.txt` | 1 planned (LLM) | n/a (plan-time alignment) | default **60** unchanged | **PASS** (inferred objective contracts join to `text_analyzer/`; LLM root-only checks joined; dash-list / `docs/` / single child / word_counter unchanged) | objective checks **path-aligned** `text_analyzer/summary.json`, `text_analyzer/input.txt`, `python3 text_analyzer/test_analyzer.py`; fallback *tasks* still check-less (F-17) | n/a (plan-time; not ENVIRONMENT) | **A** (theme-1 follow-up / Gen3 theme 3 slice A; live 11B quality stays **B**) | Tests `test_ascii_tree_package_dir_*`. False DONE **0**. Check *kinds* not remapped (F-26). Needle OFF. Caps unchanged. Live NIM not required. RW-073 Class B live facts preserved. |

# Live NIM retest of v0.4.0 (RW-071)

Lane: operator production `rad objective run` on **v0.4.0** (tag `v0.4.0`,
`a8aac8ae`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 8 --max-tools 12`).
RW-058–070 are **not rewritten**. **Not** an end-to-end PASS. Package **0.4.0**
on the live run; this change bumps to **0.4.1** for theme 2 (does **not** claim
live 11B text_analyzer@12 now PASS).

Authoritative live facts: operator report for `obj_d662224b` /
`/tmp/rad_prod_rw071_7811425c`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-071 | 2026-09-18 IST 20:18:41–20:20:53 | coding (live NIM) — v0.4.0 text_analyzer retest vs RW-069 | production `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=1** (6 tasks, `fit=true`); t_9e88e690 RETRYING; t_05a32ab3 COMPLETED (skipped model on budget); analyzer/summary/tests/README PENDING; repair t_2d3f39f4 RUNNING at stop | tools 12/12 (`write_file` 11, `run_shell` 1); model calls 9/80; retries 1/6; wall ~95s reported / ~132s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | First task `Create text_analyzer directory` FAILED; objective checks path-aligned `text_analyzer/analyzer.py`, `text_analyzer/summary.json`. `file_nonempty` on package `summary.json` failed (empty) | Gen2 **YES** — `ENVIRONMENT_FAILURE` → `repair` (“Repair prerequisite”) on mkdir-already-exists + empty `summary.json` among action/shell check noise; repair rewrote README/analyzer/input/test, did not fill empty summary before budget cut | **B** residual (11B/budget). Theme 1 path-alignment **Y** (Class A path-misalignment **not** reproduced) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw071_7811425c`; `obj_d662224b`. Disk: workspace root **only** `text_analyzer/` (no root pollution). `input.txt` **FAIL** 1-line sha256 `9bf9660fcac9d5a1cd5906dd8a8d42e4a9aedaa25847d6412ad53abf517d41aa` ≠ expected 3-line `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`. Package `summary.json` **present, 0 bytes, invalid JSON**. `analyzer.py` stdlib, never ran as `__main__`. `test_analyzer.py` unittest expects lines=3 vs 1-line input (`1 != 3`). README present. False DONE **0**. Caps unchanged. Needle OFF. |

### RW-071 vs RW-069 (same 11B / tools=12 control)

| | RW-069 (v0.3.2) | RW-071 (v0.4.0) |
|---|---|---|
| home | `/tmp/rad_prod_rw069_89512dd9` | `/tmp/rad_prod_rw071_7811425c` |
| objective id | `obj_1d8cc7ed` | `obj_d662224b` |
| package | 0.3.2 | **0.4.0** |
| `--max-tasks` / `--max-tools` | 8 / 12 | 8 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** attempts **1** | **llm** attempts **1** |
| Checks | **root-only** misaligned | **path-aligned under `text_analyzer/`** |
| Root pollution | YES | **NO** |
| `input.txt` | wrong 1-line `9bf9660f…` | **same** wrong 1-line `9bf9660f…` |
| Package `summary.json` | missing (RAD) | **present, empty/invalid** |
| Repair | retry_with_hint VALIDATION | ENVIRONMENT → Repair prerequisite (mkdir already exists + empty JSON noise) |
| tools | 12/12 | 12/12 |
| false DONE | **0** | **0** |
| Theme 1 (path-aligned checks) | FAIL (A2) | **PASS signal (live-confirmed)** |
| Residual class | B (+ path-misalignment A) | **B** (A path theme closed for this shape) |

| metric | value |
|---|---|
| Package (live run) | **0.4.0** (tag `v0.4.0` / `a8aac8ae`) |
| Theme 1 (path-aligned checks) | **live-confirmed** — checks under `text_analyzer/`; no root pollution |
| Residual | **Class B** — 1-line input `9bf9660f…`, empty `summary.json`, tools 12/12, ENVIRONMENT mkdir thrash |
| Class A path-misalignment | **not reproduced** |
| RW-058–070 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 8 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. Theme 1 holds. Do not claim live 11B@12 PASS. Theme 2 ships as v0.4.1 (contracts + already-exists not ENVIRONMENT); live 11B quality remains Class B. |

# Gen3 — v0.4.1 multi-file contracts under tight budgets (RW-072)

Lane: deterministic / scripted on **v0.4.1**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–071 are
**not rewritten**. Package **0.4.0 → 0.4.1**. Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-072 | 2026-09-18 | coding (scripted) — multi-file contracts / already-exists | RW-071 shape: package `text_analyzer/`; LLM plan emits weak `file_exists` / first-sentence contains; disk is 1-line `input.txt` + empty `summary.json`; mkdir File-exists mixed with no-such-file noise | 1 planned (LLM) | write weak package files once | default **60** unchanged | **PASS** (weak artifacts **not** VERIFIED; already-exists **not** ENVIRONMENT) | objective **FAILED** from merged `json_valid` + `file_line_count` + `shell_ok`; 3-line + valid JSON + tests still **VERIFIED**; no root pollution | mkdir already-exists + empty JSON → TOOL/VALIDATION **coding repair**, not Repair prerequisite | **A** (Gen3 theme 2; live 11B quality stays **B**) | Tests `test_multifile_tight_budget_*`. False DONE **0**. Fallback tasks still have no checks (F-17); check *kinds* not remapped (F-26). Path-aligned checks preserved. Needle OFF. Caps unchanged. Live NIM not required. RW-071 Class B live facts preserved. |

# Gen3 — v0.4.0 path-aligned checks (RW-070)

Lane: deterministic / scripted on **v0.4.0**. Needle `existing` / off.
`max_plan_tasks` **16**. Default `Budget.tool_calls` **60**. RW-058–069 are
**not rewritten**. Package **0.3.2 → 0.4.0**. Live NIM not re-run.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-070 | 2026-09-18 | coding (scripted) — path-aligned checks | production-shaped `text_analyzer/` layout; LLM plan emits root-only `file_exists input.txt` + `json_valid summary.json`; scripted writes land under `text_analyzer/` | 1 planned (LLM) | write package files once | default **60** unchanged | **PASS** (aligned checks VERIFIED; no root pollution) | objective **VERIFIED** from package paths; workspace-root `input.txt` / `summary.json` **absent** | none (first attempt VERIFIED; no VALIDATION retry thrash; not ENVIRONMENT) | **A** (Gen3 theme 1) | Tests `test_path_aligned_checks_*`. False DONE **0**. Fallback tasks still have no checks (F-17); check *kinds* not remapped (F-26). Word_counter root paths unchanged. Single `pkg/foo.py` is not a layout. Needle OFF. Caps unchanged. Live NIM not required. RW-069 Class B live facts preserved. |

# Live NIM use of v0.3.2 (RW-068 / RW-069)

Lane: operator production `rad objective run` on **v0.3.2** (tag `v0.3.2`,
`387776dc`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60**. RW-058–067 are **not rewritten**. Package stays
**0.3.2** (no bump). **No v0.4.0.**

Authoritative live facts: operator v0.3.2 use campaign for `obj_794fb0b3` /
`/tmp/rad_prod_rw068_09177c89` and `obj_1d8cc7ed` /
`/tmp/rad_prod_rw069_89512dd9`. This agent did not re-run NIM.

## RW-068 word_counter (control vs RW-066) — PASS

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-068 | 2026-09-18 IST 19:46:33–19:48:01 | coding (live NIM) — v0.3.2 word_counter vs RW-066 | word_counter.py (hello world → 2) + result.json `{"words": 2}` + test_word_counter.py asserting 2; run tests; no DONE pollution; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=1** (4 tasks with per-task checks) | tools 12/12; model calls 9/80; wall ~88s / spent 51.2s; process exit 0 | 12/12 exhausted | **PASS** (`completed` / **VERIFIED**) | objective **VERIFIED**; valid `result.json` words=2; host tests **OK** (1 test) | Gen2 **YES** — `ENVIRONMENT_FAILURE` → `repair`. First task verify FAILED (actions errors + mis-applied `json_valid` on `.py`); budget exhausted mid-repair; leftover tasks CANCELLED because objective checks already satisfied | **B** residual (11B@12 tools exhausted mid-repair). Planning path **improved** vs RW-066 | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw068_09177c89`; `obj_794fb0b3`. Disk: `word_counter.py` YES (`split()` / `len(words)` → 2 for `hello world`); `result.json` **valid** `{"words": 2}`; `test_word_counter.py` YES; host `python3 -m unittest test_word_counter.py` **OK**; DONE-named files **NONE**. Agent attempted `write_file` path `DONE: …`; **tool refused**. False DONE **0**. vs RW-066: **llm/1** vs fallback/2. Caps unchanged. Needle OFF. **No v0.4.0.** |

### RW-068 vs RW-066 (same 11B / tools=12 control)

| | RW-066 (v0.3.1 live) | RW-068 (v0.3.2 live) |
|---|---|---|
| home | `/tmp/rad_prod_rw066_0b0bb188` | `/tmp/rad_prod_rw068_09177c89` |
| objective id | `obj_e74d9fad` | `obj_794fb0b3` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` / `--max-tools` | 4 / 12 | 4 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **fallback** | **llm** |
| PLAN attempts | **2** | **1** |
| Plan shape | 1 clause-collapsed mega-task (0 task checks) | **4 tasks** with per-task checks |
| Gen2 repair insert | **YES** | **YES** (`ENVIRONMENT_FAILURE` → `repair`) |
| `result.json` | valid `{"words": 2}` | valid `{"words": 2}` |
| Tests (host) | **OK** (2 tests) | **OK** (1 test) |
| DONE pollution | NO | NO (tool refused `DONE:` path) |
| false DONE | **0** | **0** |
| final status | `completed` / VERIFIED | `completed` / VERIFIED |
| end-to-end PASS | Yes | **Yes** |
| class | **B** residual (11B@12) | **B** residual (11B@12); **better plan path** |

| metric | value |
|---|---|
| Package (live run) | **0.3.2** (tag `v0.3.2` / `387776dc`) |
| Theme 1 (verified coding loop) | **used** — repair YES; valid JSON; tests OK; no DONE pollution |
| Theme 2 (plan-timeout resilience) | **used** — live plan succeeded on **first LLM attempt** (no fallback) |
| Residual | **Class B** — tools 12/12 mid-repair; objective already VERIFIED so leftovers CANCELLED (not false DONE) |
| RW-058–067 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 4 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **PASS**. Simple verified coding loop is **stable** on v0.3.2. Do not claim multi-file Class B is solved. |

## RW-069 text_analyzer (vs RW-058 / RW-059 family) — FAIL

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-069 | 2026-09-18 IST 19:48:29–19:51:22 | coding (live NIM) — v0.3.2 text_analyzer vs RW-058 family | production `text_analyzer/` layout (analyzer.py, **exact 3-line** input.txt, summary.json, test_analyzer.py, README.md); stdlib only; real tests; `--max-tasks 8 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** **attempts=1** | tools 12/12; spent 117.3s; wall ~173s; process exit 2 | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED (task verify FAILED; objective stopped) | **retry_with_hint** (`VALIDATION_FAILURE`) — not Gen2 `repair` insert | **B** (same family as RW-058 / RW-059). A2 path-vs-write **watch**, **not proven Class A** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw069_89512dd9`; `obj_1d8cc7ed`. 24-tool follow-up **not run**. Disk at stop (RAD-produced): `text_analyzer/analyzer.py` YES (buggy `str.split('\\s+')`; writes `chars` not `characters`); `text_analyzer/input.txt` YES **wrong** (1 line, not 3); `text_analyzer/summary.json` **NO**; `text_analyzer/test_analyzer.py` YES (weak `assertGreater`; import assumes CWD); `text_analyzer/README.md` YES; root `input.txt` / `README.md` / `summary.json` YES (retry thrash). input.txt sha256 **actual** `9bf9660fcac9d5a1cd5906dd8a8d42e4a9aedaa25847d6412ad53abf517d41aa` ≠ expected 3-line `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` (no trailing NL) / `5c376e468fe70a63e0d5341908cc7b1b283b7508458fd988d3f4f79a54ea3ec6` (trailing NL). Root `summary.json` `{"lines": 13, "words": 13, "characters": 76}` — valid JSON, **wrong counts** for the required 3-line input. Host post-run unittest under `text_analyzer/` reported OK only because tests are non-assertive and created `summary.json` as a side effect — **not** campaign PASS. False DONE **0**. Caps unchanged. Needle OFF. **No v0.4.0.** |

### RW-069 vs RW-058 / RW-059 (text_analyzer family)

| | RW-058 (v0.2.3) | RW-059 (v0.2.3, tools=24) | RW-069 (v0.3.2) |
|---|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw069_89512dd9` |
| objective id | `obj_4e219224` | `obj_e1419520` | `obj_1d8cc7ed` |
| package | 0.2.3 | 0.2.3 | **0.3.2** |
| `--max-tasks` / `--max-tools` | 8 / **12** | 8 / **24** | 8 / **12** |
| Needle | `existing` / off | `existing` / off | `existing` / off |
| PLAN source | llm (5 planned) | llm | **llm** attempts **1** |
| Repair | user chose stop | budget exhausted | **retry_with_hint** (VALIDATION_FAILURE) |
| tools used | 12/12 exhausted | 24/24 exhausted | 12/12 exhausted |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** |
| `input.txt` | **PASS** sha256 `bf69eb73…` (exact 3-line) | same PASS `bf69eb73…` | **FAIL** 1-line `9bf9660f…` |
| package `summary.json` | **MISSING** (correct counts at workspace root, wrong path) | present, **invalid JSON** + wrong counts | **MISSING** (RAD); root file counts do not match 3-line input |
| layout | pollution at workspace root | five files under `text_analyzer/` | package files + **root pollution** (retry flattened) |
| class | **B** | **B** (Case B on tool-budget) | **B** (same family); planning healthier; artifact quality still fail |

| metric | value |
|---|---|
| Package (live run) | **0.3.2** — no bump; **no v0.4.0** |
| Planning | healthier (llm/1) vs historical thrash; **not** enough for package completion |
| Residual | **Class B** — wrong newlines, missing package `summary.json`, weak tests, layout thrash at tools=12 |
| A2 (check path vs write path) | **watch** — checks at workspace-root vs writes under package dir → false VALIDATION_FAILURE → retry thrash. **Not proven Class A** |
| A1 budget→needs_user | **do not reopen** without new proof (honest stop at 12/12) |
| Optional tools=24 follow-up | **not run** (B2; warranted later as a Gen3 baseline) |
| RW-058–067 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **FAIL**. Multi-file coding under tools=12 remains Class B. Scope Gen3 from this gap; do not implement v0.4.0 here. |

# Live NIM retest of v0.3.1 (RW-066)

Lane: operator production `rad objective run` on **v0.3.1** (tag `v0.3.1`,
`50d98e26`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 4 --max-tools 12`).
RW-058–065 are **not rewritten**. Scripted theme-2 ship evidence remains the
existing RW-066 planning row (F-27) below. This section records the live
production retest the operator labeled RW-066.

Authoritative live facts: operator report for `obj_e74d9fad` /
`/tmp/rad_prod_rw066_0b0bb188`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-066 | 2026-09-18 IST 19:17:44–19:19:18 | coding (live NIM) — v0.3.1 word_counter retest vs RW-065 | word_counter.py + result.json (`words==2`) + test_word_counter.py + tests pass; no DONE: pollution; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=fallback** **attempts=2** (1 mega-task, 0 task checks); t_8e202435 CANCELLED; repair t_4f398815 CANCELLED | tools 12/12; model calls 9/80; retries 1/6; wall ~94s event / spent 41.8s | 12/12 exhausted | **PASS** vs success criteria (`completed` / **VERIFIED**); disk matched | objective **VERIFIED** (`json_valid` result.json; `shell_ok` python3 test_word_counter.py, 2 tests OK). Task verify FAILED then cancelled: “objective machine checks already satisfied (budget exhausted)” | Gen2 **YES** — `RECOVERY_DECISION` `strategy=repair` `failure_class=ENVIRONMENT_FAILURE`; repair wrote fixed `word_counter.py` + valid `result.json`; budget cut mid further writes | **B** residual (11B plan/coding@12). Theme 2 **live-confirmed**. Low-urgency CANCELLED+VERIFIED UX when objective checks already satisfied | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw066_0b0bb188`; `obj_e74d9fad`. Disk: `word_counter.py` YES (space-count+1 → 2); `result.json` **valid** `{"words": 2}`; `test_word_counter.py` YES; host tests **PASS** (2 OK); DONE pollution **NONE**. False DONE **0**. vs RW-065: **better E2E** (065 `needs_user` / tests FAIL). Caps unchanged. Needle OFF. Theme 3 still relevant (tools exhausted mid-repair). |

### RW-066 vs RW-065 (same 11B / tools=12 control)

| | RW-065 (v0.3.0) | RW-066 (v0.3.1 live) |
|---|---|---|
| home | `/tmp/rad_prod_rw065_ab0919b2` | `/tmp/rad_prod_rw066_0b0bb188` |
| objective id | `obj_efed5285` | `obj_e74d9fad` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` / `--max-tools` | 4 / 12 | 4 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **llm** (4 tasks w/ checks) | **fallback** (1 mega-task, 0 task checks) |
| PLAN attempts | *(field absent)* | **2** then fallback |
| Gen2 repair insert | **YES** | **YES** |
| `result.json` | valid `{"words": 2}` | valid `{"words": 2}` |
| Tests (host) | **FAIL** (NameError / broken counter) | **PASS** (2 OK) |
| DONE pollution | NO | NO |
| false DONE | **0** | **0** |
| final status | `needs_user` / FAIL | **`completed` / VERIFIED** |
| end-to-end PASS | No | **Yes** |
| class | **B** (F-25); json_valid-on-.py **NOT CONFIRMED** (F-26) | **B** residual (11B@12); theme 2 live-confirmed |

| metric | value |
|---|---|
| Package (live run) | **0.3.1** (tag `v0.3.1` / `50d98e26`) |
| Theme 2 (plan-timeout resilience) | **used / live-confirmed** — `attempts=2` then `source=fallback` |
| Theme 1 (verified coding loop) | **used** — repair YES; valid JSON; tests PASS; no DONE pollution |
| Residual | **Class B** — 11B plan/coding@12; tools 12/12 mid-repair; CANCELLED+VERIFIED when objective checks already satisfied (low urgency; not false DONE) |
| RW-058–065 | preserved (not rewritten) |
| Scripted RW-066 (F-27) | preserved (theme 2 ship evidence) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 4 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | Record **PASS**. Theme 3 (budget-aware planning) still relevant; do not raise caps. |

# Gen2 — v0.3.2 budget-aware planning (RW-067)

Lane: Cloud Agent, deterministic/scripted. Live NIM optional (BLOCKED if no key).
Package **0.3.1 → 0.3.2**. Needle `existing` / off. `max_plan_tasks` **16**.
Default `Budget.tool_calls` **60**. Default plan retries **1** (hard cap 3).
F-17 fallback contract **unchanged** (goal-only clause split, cap 7, no checks).
F-21 leftover-work contract **unchanged** (≤3-task LLM graphs are not compacted).
Does **not** claim live 11B Class B coding is solved. Does **not** reopen F-17 / F-26.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-067 | 2026-09-18 | planning (scripted) — budget-aware planning | Fat 8-task LLM plan vs remaining N=6 tools; fallback 7-clause vs N=4 | fat→fit: 2 llm tasks with checks (estimated 4 ≤ 6); fallback compact: 2 tasks, no checks | plan only (plus bounded drive for false-DONE) | default **60** unchanged | **PASS** fat-then-fit is selected; two fat plans pick cheaper; fallback compact fits N; small 3-task LLM plan with remaining=1 stays 3 (F-21); default-60 fallback stays 7 | LLM path keeps checks; compacted fallback UNVERIFIED; objective not VERIFIED without checks | n/a (plan-time select/compact, not recovery) | capability (Gen2 theme 3) | Tests `tests/test_budget_aware_planning.py`. Needle OFF. Caps unchanged. False DONE **0**. F-17 / F-21 / F-26 preserved. Live NIM not required. |

| metric | value |
|---|---|
| Package | **0.3.2** |
| Theme | Gen2 #3 budget-aware planning |
| Needle | **OFF** (`existing`) |
| `max_plan_tasks` | **16** unchanged |
| Default tool budget | **60** unchanged |
| Default plan retries | **1** (hard cap **3**) |
| False completion | **0** |
| RW-058–065 | preserved (not rewritten) |
| Scripted RW-066 (F-27) | preserved |
| Live RW-066 | preserved (PASS; residual Class B) |
| Live NIM this patch | **BLOCKED** if no key — not a live PASS claim for theme 3 |
| Claim all Class B coding solved | **NO** |

# Gen2 — v0.3.1 plan-timeout resilience (RW-066)


Lane: Cloud Agent, deterministic/scripted. Live NIM optional (BLOCKED if no key).
Package **0.3.0 → 0.3.1**. Needle `existing` / off. `max_plan_tasks` **16**.
Default `Budget.tool_calls` **60**. Default plan retries **1** (hard cap 3).
F-17 fallback contract **unchanged** (goal-only clause split, cap 7, no checks).
Does **not** claim RW-062 / RW-065 live 11B would now PASS.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-066 | 2026-09-18 | planning (scripted) — plan-timeout resilience | First plan call TimeoutError / empty / malformed; second call valid JSON with checks | timeout→JSON: 2 llm tasks with checks; exhausted: 7 fallback, no checks | plan only (plus bounded drive for false-DONE) | default **60** unchanged | **PASS** timeout-then-JSON is `source=llm`; exhausted is `source=fallback` F-17; first-try JSON still 1 attempt | LLM path keeps checks; fallback UNVERIFIED; objective not VERIFIED without checks | n/a (plan-time retry, not recovery) | capability (Gen2 theme 2) | Tests `tests/test_plan_timeout_resilience.py`. Needle OFF. Caps unchanged. False DONE **0**. F-17 preserved. Live NIM not required. |

| metric | value |
|---|---|
| Package | **0.3.1** |
| Theme | Gen2 #2 plan-timeout resilience |
| Needle | **OFF** (`existing`) |
| `max_plan_tasks` | **16** unchanged |
| Default tool budget | **60** unchanged |
| Default plan retries | **1** (hard cap **3**) |
| False completion | **0** |
| RW-058–065 | preserved (not rewritten) |
| Live NIM | **BLOCKED** (no `NVIDIA_NIM_API_KEY`) |
| Claim RW-062/065 live PASS | **NO** |

# Gen2 — v0.3.0 verified coding loop (RW-064)

Lane: Cloud Agent, deterministic/scripted. Live NIM optional (BLOCKED if no key).
Package **0.2.3 → 0.3.0**. Needle `existing` / off. `max_plan_tasks` **16**.
Default `Budget.tool_calls` **60**. Control plane unchanged in shape
(PLAN→PERMISSION→BUDGET→EXECUTE→OBSERVE→VERIFY→RECOVER).

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-064 | 2026-09-18 | coding (scripted) — verified coding loop | word_counter-like: `result.json` + `test_word_counter.py`; first write is invalid `{` / words `6`; repair must fix to `words==2` | 1 planned + 1 repair | write → json_valid/shell fail → repair → retry | default **60** unchanged | **PASS** (repair path VERIFIED); persistent-bad **PASS** (not VERIFIED) | repair path **VERIFIED** from disk; persistent `{` / `DONE:` pollution **not** VERIFIED | VALIDATION/TOOL → **repair** with concrete failure (not ENVIRONMENT); missing `file_exists` still retry_with_hint | capability (Gen2) | Tests `test_verified_coding_loop_*`. False DONE **0**. Fallback tasks still have no checks (F-17); coding goals infer *objective* `json_valid` + test `shell_ok`. Needle OFF. Caps unchanged. Live NIM not required. RW-058/062 Class B live facts preserved. |

| metric | value |
|---|---|
| Package | **0.3.0** |
| Theme | Gen2 #1 verified coding loop |
| Needle | **OFF** (`existing`) |
| `max_plan_tasks` | **16** unchanged |
| Default tool budget | **60** unchanged |
| False completion | **0** |
| RW-058–063 | preserved (not rewritten) |
| Live NIM | **BLOCKED** (no `NVIDIA_NIM_API_KEY`) |

# Live NIM retest of v0.3.0 (RW-065)

Lane: operator production `rad objective run` on **v0.3.0** (tag `v0.3.0`,
`183ff611`). Needle `existing` / off. `max_plan_tasks` **16**. Default
`Budget.tool_calls` **60** (this run used `--max-tasks 4 --max-tools 12`).
RW-058–064 are **not rewritten**. **Not** an end-to-end PASS. Package stays
**0.3.0** (json_valid-on-.py Class A **NOT CONFIRMED**; no 0.3.1).

Authoritative live facts: operator report for `obj_efed5285` /
`/tmp/rad_prod_rw065_ab0919b2`.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-065 | 2026-09-18 IST 18:46:10–18:47:36 | coding (live NIM) — v0.3.0 word_counter retest vs RW-062 | word_counter.py + result.json (`words==2`) + test_word_counter.py + tests pass; no DONE: pollution; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=llm** (4 tasks); t_8ca54965 RETRYING; t_1c465c51 COMPLETED/VERIFIED; tests+run PENDING; repair t_6b2926a5 RUNNING at stop | tools 12/12; model calls 9/80; retries 1/6; wall ~86s event / spent 66.7s | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED on first task (actions errors + `json_valid` on `.py`); objective `json_min_len` on `result.json` registered, not VERIFIED | Gen2 **YES** — `RECOVERY_DECISION` `strategy=repair` `failure_class=ENVIRONMENT_FAILURE` (“missing dependency/file”); repair cut off by tool budget | **B** primary (11B/budget); json_valid-on-.py Class A **NOT CONFIRMED** (F-20260918-26) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw065_ab0919b2`; `obj_efed5285`. Disk: `word_counter.py` YES (broken `s.split().count()` TypeError); `result.json` **valid** `{"words": 2}`; `test_word_counter.py` YES (NameError, no import); DONE pollution **NONE**. Tests **FAIL**. False DONE **0**. vs RW-062: **improved** (llm plan, Gen2 repair, valid JSON, no DONE pollution) but not E2E PASS. Caps unchanged. Needle OFF. **No v0.3.1.** |

### RW-065 vs RW-062 (same 11B / tools=12 control)

| | RW-062 (v0.2.3) | RW-065 (v0.3.0) |
|---|---|---|
| home | `/tmp/rad_prod_rw062_6ede431b` | `/tmp/rad_prod_rw065_ab0919b2` |
| objective id | `obj_7a020865` | `obj_efed5285` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` / `--max-tools` | 4 / 12 | 4 / 12 |
| Needle | `existing` / off | `existing` / off |
| PLAN source | **fallback** (7 clause-split tasks) | **llm** (4 coherent tasks) |
| Gen2 repair insert | No | **YES** (`RECOVERY_DECISION` → `t_6b2926a5`) |
| `result.json` | invalid `{` | **valid `{"words": 2}`** |
| Tests | FAIL `6 != 2` | FAIL `NameError` / broken counter |
| DONE pollution | YES (`DONE:` fake path) | **NO** |
| false DONE | **0** | **0** |
| final status | `needs_user` / FAIL | `needs_user` / FAIL |
| end-to-end PASS | No | No |
| class | **B** (F-22) | **B** (F-25); json_valid-on-.py **NOT CONFIRMED** (F-26) |

| metric | value |
|---|---|
| Package | **0.3.0** — no bump; **no v0.3.1** |
| Theme 1 (verified coding loop) | **used** — repair fired; valid JSON; no DONE pollution |
| Residual | **Class B** — 11B + tools=12 exhausted mid-repair; tests FAIL; not E2E PASS |
| Class A json_valid-on-.py | **NOT CONFIRMED** — see ledger F-20260918-26 / `tests/test_json_valid_py_investigation.py` |
| RW-058–064 | preserved (not rewritten) |
| Default max-tools / max-tasks | **unchanged** (this run used `--max-tasks 4 --max-tools 12` only) |
| Needle | **OFF** (`existing`) |
| False completion | **0** |
| Recommendation | **stay 0.3.0** — document live use; do not claim coding PASS on 11B@12 |

# Cycle 2 (post-v0.2.1 → package **0.2.2**)

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `f7160c14cc5e9905a5c2e0689bbcc2465a20b45c` (Merge PR #7).
Release tag `v0.2.1` → `705954010b4835f8d6bfc445f49bafb80add5dee`.

## Scripted `rad realworld` suite

Command: `RealWorldSuite(home).run()` (isolated `/tmp/rad_rw_suite_*`). Evidence:
`/tmp/rad_rw_suite_kw6po5nj/realworld/20260918-064637_realworld.json`.

| id | area | actions (approx) | disk | status | verified | result | class | notes |
|---|---|---|---|---|---|---|---|---|
| RW-001 | research | ~3 tasks + network fault | `report.json` sha256 `0a45c9e59ae640f3` (1053 B); both prices 42 and 57; conflict recorded | completed | VERIFIED | **PASS** | — | Independent disk checks 9/9. Lab grader `json_field{key}` was a false negative before F-20260918-09 |
| RW-002 | coding | inspect → naive fix → repair | `pkg/stats.py` sha256 `68c46b7e404d7117`; `tests/check_stats.py` hash unchanged; stdout `ALL TESTS PASSED` | completed | VERIFIED | **PASS** | — | Injected `run_shell` fault recovered. Lab grader `shell_output{contains}` was a false negative before F-20260918-09 |
| RW-003 | multi-agent | researcher / writer / reviewer | `answer.md` sha256 `3e80d1d8f8e934c0`; readings 42, 39, 12; no invented 500 | completed | VERIFIED | **PASS** | — | Reviewer is a different agent; machine checks complete |
| RW-004 | recovery | injected faults + crash-resume | `summary.json` sha256 `d1bd5d677ce9ed65`; count=4 mean=33.75; four `out/stepN.txt` after resume | completed | VERIFIED | **PASS** | — | Checkpoint restore; finished work kept |
| RW-005 | filesystem | nested write + copy + jail | `nest/a/note.txt` and `nest/b/note.txt` sha256 `b6a98d9ce9a2d914` (`alpha`); `../escape.txt` absent | completed | VERIFIED | **PASS** | — | Workspace jail held |
| RW-006 | multi-step | A→B→C | `stepA.txt`/`stepB.txt`/`stepC.txt` hashes `559aead0` / `df7e70e5` / `6b23c0d5` | completed | VERIFIED | **PASS** | — | Three dependent artifacts |
| RW-007 | false completion | `DONE:` without write | `honest.txt` **absent** | needs_user | (not VERIFIED) | **PASS** | — | DONE semantics held |
| RW-008 | needs_user | missing staging host | `published.txt` **absent** | needs_user | (not VERIFIED) | **PASS** | — | Escalated; no invented publish |
| RW-009 | no_loop | persistent false DONE | `missing.txt` **absent** | needs_user | (not VERIFIED) | **PASS** | — | Retry budget respected |
| RW-010 | overdecompose | extra README/backup tasks; tool budget 1 | `live_hello.txt` sha256 `5891b5b522d5df08` contains `hello` | completed | VERIFIED | **PASS** | A (already fixed v0.2.1) | Completes from machine checks, not a DONE claim |
| RW-011 | live NIM | live `objective run` | — | blocked | — | **BLOCKED** | **C** | Both NVIDIA env vars absent |

Suite: **10 passed / 1 BLOCKED / 0 failed**.

## Action ramp (1 → 3 → 5 → 10 → 20)

Sequential `write_file` through the real control plane. Disk-verified each index file.

| id | planned | actions on disk | status | verified | result | class | notes |
|---|---|---|---|---|---|---|---|
| RW-012 | 1 task / 1 write | `steps/s01.txt` = `1` | completed | VERIFIED | **PASS** | — | |
| RW-013 | 3 tasks / 3 writes | `s01`–`s03` correct | completed | VERIFIED | **PASS** | — | |
| RW-014 | 5 tasks / 5 writes | `s01`–`s05` correct | completed | VERIFIED | **PASS** | — | |
| RW-015 | 10 tasks / 10 writes | `s01`–`s10` correct | completed | VERIFIED | **PASS** | — | |
| RW-016 | 20 **tasks** / 20 writes | **16** files (`s01`–`s16`); `s17`–`s20` absent | failed | FAILED | **FAIL** (expected cap) | — | Planner `max_plan_tasks` default **16** silently drops the rest. Not raised this cycle (architecture frozen; prompt says never more than 16). See limitations |
| RW-017 | 1 task / **20 writes** | `acts/a01.txt` … `acts/a20.txt` (20/20); `a20` sha256 `5378796307535df3` | completed | VERIFIED | **PASS** | — | Twenty *actions* fit under the 16-task guard |
| RW-018 | 5 tasks + injected `write_file` fault, retry-aware script | 5/5 files; 1 tool error; 2 recoveries | completed | VERIFIED | **PASS** | — | Naive script (no replay line) ended `needs_user` — campaign script, not a RAD hole |

## Extra campaign (same VM)

| id | area | disk | status | verified | result | class | notes |
|---|---|---|---|---|---|---|---|
| RW-019 | filesystem (deeper nest) | `data/raw/a.txt` + `data/curated/a.txt` contain `alpha`; `../escape.txt` absent | completed | VERIFIED | **PASS** | — | Jail held |
| RW-020 | research (two-source price) | `cmp.json` claims 10 and 12, both sourced; `conflicts` present | completed | VERIFIED | **PASS** | A (F-20260918-09) | Before the fix, lab grader `json_field{key}` → `grader error: 'field'` while disk + verifier were already correct |
| RW-021 | coding (`twice.py`) | `python3 check.py` → `ALL TESTS PASSED`; `check.py` hash unchanged | completed | VERIFIED | **PASS** | A (F-20260918-09) | Before the fix, lab grader `shell_output{contains}` → `grader error: 'expect'` |
| RW-022 | false DONE | `proof.txt` absent | needs_user | (not VERIFIED) | **PASS** | — | DONE semantics held |
| RW-023 | live NIM Class A retest | — | blocked | — | **BLOCKED** | **C** | Same missing keys as RW-011. Offline reconstruction remains `overdecompose` / `false_success` |

## Metrics (this cycle, honest)

| metric | value |
|---|---|
| Suite runnable PASS | 10/10 (plus 1 BLOCKED live NIM) |
| False completion (VERIFIED without the artifact) | **0** |
| Independent lab-grader false negatives on RW-020 / RW-021 (pre-fix) | **2** (Class A; **fixed** — post-fix `rad realworld` research/coding graders all `ok`) |
| 20 sequential *actions* | **VERIFIED** (RW-017) |
| 20 sequential *planned tasks* at default cap | **FAILED** at 16 (RW-016) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |

Do not add rows without a disk check or an honest BLOCKED/NOT TESTED mark.

---

# Cycle 3 (post-v0.2.2 → package **0.2.3**)

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `8d9e196aa730c7bfeae7e501f44004078f080b61` (PR #8 / Release `v0.2.2`).
Needle stays experimental / off. Not AGI. No v0.3.0. Planner cap left at 16.

Evidence: `/tmp/rad-c3-evidence/campaign.json`. Control-plane verifier **and** a disk check for every `VERIFIED` cell.

## Production campaign (genuine useful work)

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-024 | 2026-09-18 | coding | `pkg/avg.py` `mean_by_region` + `tests/check_avg.py` | 2 | 2 | write_file, run_shell | **PASS** | VERIFIED | none | — | `pkg/avg.py` sha256 `111ed94abb1bce8f`; tests hash `616a5feda63b6489` unchanged; stdout `ALL TESTS PASSED` |
| RW-025 | 2026-09-18 | research | two lab notebooks → `compare.json` with sourced pH conflict | 2 | 3 | read_file, write_file | **PASS** | VERIFIED | none | A (F-20260918-11) | `compare.json` sha256 `3b8f1e6a8b43a214`; both 6.8 and 8.1 sourced. Pre-fix `json_valid` grader `unknown grader`; post-fix `ok` |
| RW-026 | 2026-09-18 | filesystem | sort inbox into `docs/` + `data/` + index; jail | 3 | 4 | run_shell, write_file | **PASS** | VERIFIED | none | — | `data/index.txt` sha256 `2e6256058b614820`; `../escape.txt` absent |
| RW-027 | 2026-09-18 | multi-step | `app.log` → `counts.json` (error=3) → `summary.md` | 2 | 4 | read_file, write_file | **PASS** | VERIFIED | none | — | `counts.json` sha256 `25e1d36b1f2772ea`; `summary.md` sha256 `343bf41f1bf64c71` |
| RW-028 | 2026-09-18 | recovery | write `config/settings.json` with injected `write_file` fault | 1 | 2 | write_file | **PASS** | VERIFIED | 1 tool error, 2 recoveries | A (F-20260918-11) | sha256 `2b3a56a5f55ff76f`; pre-fix `json_valid` grader unknown; post-fix `ok` |
| RW-035 | 2026-09-18 | recovery | `DONE:` without writing `proof.txt` | 1 | 0 | (none) | **PASS** | (not VERIFIED) | retry then escalate | — | status `needs_user`; file **absent** |
| RW-036 | 2026-09-18 | recovery | crash after `pipe/p1.txt`, restore, resume p2–p3 | 3 | crash+resume | write_file | **PASS** | VERIFIED | checkpoint restore | — | hashes `5509d3b83b2db7d3` / `a652f5bf7a9c5936` / `6153dd17d3a9573f` |
| RW-037 | 2026-09-18 | live NIM | live `objective run` | 0 | 0 | — | **BLOCKED** | — | — | **C** | both NVIDIA env vars absent |
| RW-038 | 2026-09-18 | coding | `inventory.json` object; advertised `json_min_len{n=2}` + `json_valid` | 1 | 1 | write_file | **PASS** (post-fix) | VERIFIED | none | **A** (F-20260918-11) | sha256 `31d4c9f7af644d06`. Pre-fix: verifier ok, grader `json_min_len` list-only + `json_valid` unknown. Post-fix: graders agree |
| RW-039 | 2026-09-18 | needle | default router | 0 | 0 | — | **PASS** | n/a | — | — | `RAD_TOOL_ROUTER` unset; `resolve_tool_router` = `existing`. Router **NOT TESTED** |

## Action ramp (1 → 3 → 5 → 10 → 20)

Sequential inventory SKU `write_file` through the real control plane. Disk-verified each index file.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-029 | 2026-09-18 | multi-step | 1 SKU file | 1 | 1 | write_file | **PASS** | VERIFIED | none | — | `inv/s01.txt` sha256 `2da4679aa46b0db3` |
| RW-030 | 2026-09-18 | multi-step | 3 SKU files | 3 | 3 | write_file | **PASS** | VERIFIED | none | — | `inv/s03.txt` sha256 `8db9ba36bc13ec3a` |
| RW-031 | 2026-09-18 | multi-step | 5 SKU files | 5 | 5 | write_file | **PASS** | VERIFIED | none | — | `inv/s05.txt` sha256 `907e3cb7bc73ebc2` |
| RW-032 | 2026-09-18 | multi-step | 10 SKU files | 10 | 10 | write_file | **PASS** | VERIFIED | none | — | `inv/s10.txt` sha256 `db9b15433ec51d25` |
| RW-033 | 2026-09-18 | filesystem | 20 writes in **one** planned task | 1 | 20 | write_file | **PASS** | VERIFIED | none | — | 20/20; `inv/s20.txt` sha256 `14e88a9299fed78c` |
| RW-034 | 2026-09-18 | multi-step | 20 **planned tasks** / 20 writes | 16 | 16 | write_file | **FAIL** (expected cap) | FAILED | none | — | 16/20 files (`s01`–`s16`); `s17`–`s20` absent. `max_plan_tasks` default **16**. Not raised |

## Cycle 3 metrics (honest)

| metric | value |
|---|---|
| Suite runnable PASS | 10/10 (plus 1 BLOCKED live NIM) |
| Campaign PASS / FAIL / BLOCKED | **14 / 1 / 1** (the FAIL is RW-034 expected cap) |
| False completion (VERIFIED without the artifact) | **0** |
| Independent grader false negatives (pre-fix json_valid / json_min_len) | **Class A; fixed** — post-fix RW-025 / RW-028 / RW-038 / suite research graders all `ok` |
| 20 sequential *actions* | **VERIFIED** (RW-033) |
| 20 sequential *planned tasks* at default cap | **FAILED** at 16 (RW-034) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |

---

# Cycle 4 (post-v0.2.3 release verification → package **0.2.3**, no bump)

Lane: Cloud Agent VM, **no** `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`.
Baseline: `origin/main` `d121c3f8875cb01e816bb5f7df66e62ee26e1eba` (Merge PR #9 / GitHub Release `v0.2.3`).
**Release: PASS** — tag `v0.2.3` peels to that SHA; `pyproject.toml` / `rad.__version__` = `0.2.3`; release URL live. Not re-cut. Not retagged. Not v0.3.0.
Needle stays experimental / off. Planner cap left at **16**.

Evidence: `/tmp/rad-c4-evidence/campaign.json`. Control-plane verifier **and** a disk check for every `VERIFIED` cell.

## Production campaign (genuine useful work)

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-040 | 2026-09-18 | coding | `pkg/tally.py` `tally_by_sku` + `tests/check_tally.py` | 2 | 2 | write_file, run_shell | **PASS** | VERIFIED | none | — | `pkg/tally.py` sha256 `5e3aedff9a7dec82`; tests hash `aae8b0ad78917a3d` unchanged; stdout `ALL TESTS PASSED` |
| RW-041 | 2026-09-18 | research | two warehouse counts → `stock.json` with sourced on-hand conflict | 2 | 3 | read_file, run_shell | **PASS** | VERIFIED | none | — | `stock.json` sha256 `14911ec4fb461f3c`; both 120 and 87 sourced; `conflicts` present; `json_valid` / `json_min_len` graders `ok` |
| RW-042 | 2026-09-18 | filesystem | sort `inbox/` into `archive/notes/` + `archive/tables/` + manifest; jail | 2 | 3 | run_shell, write_file | **PASS** | VERIFIED | none | — | `archive/manifest.txt` sha256 `bdd78a6b815e36e1`; `../escape.txt` absent |
| RW-043 | 2026-09-18 | multi-step | `access.log` → `status.json` (errors=3) → `digest.md` | 2 | 3 | read_file, run_shell | **PASS** | VERIFIED | none | — | `status.json` sha256 `bbbaa1a0d9ee991c`; `digest.md` sha256 `3a443b870c3810dd` |
| RW-044 | 2026-09-18 | recovery | write `config/limits.json` with injected `write_file` fault | 1 | 2 | write_file | **PASS** | VERIFIED | 1 tool error, 2 recoveries | — | sha256 `f96a9e62d8b15f53`; retry-aware script; graders `ok` |
| RW-045 | 2026-09-18 | recovery | `DONE:` without writing `receipt.txt` | 1 | 0 | (none) | **PASS** | (not VERIFIED) | retry then escalate | — | status `needs_user`; file **absent** |
| RW-046 | 2026-09-18 | recovery | crash after `stage/s1.txt`, restore, resume s2–s3 | 3 | crash+resume | write_file | **PASS** | VERIFIED | checkpoint restore | — | hashes `5509d3b83b2db7d3` / `a652f5bf7a9c5936` / `6153dd17d3a9573f` |
| RW-047 | 2026-09-18 | live NIM | live `objective run` | 0 | 0 | — | **BLOCKED** | — | — | **C** | both NVIDIA env vars absent |
| RW-048 | 2026-09-18 | needle | default router | 0 | 0 | — | **PASS** | n/a | — | — | `RAD_TOOL_ROUTER` unset; `resolve_tool_router` = `existing`. Router **NOT TESTED** |
| RW-057 | 2026-09-18 | coding | lab grader vs verifier parity on advertised disk check kinds | 0 | 0 | — | **PASS** | n/a | — | — | `file_exists` / `file_min_bytes` / `file_contains` / `json_*` / `shell_*` all agree. No new Class A |

## Action ramp (1 → 3 → 5 → 10 → 20)

Sequential lot-SKU `write_file` through the real control plane. Disk-verified each index file.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-049 | 2026-09-18 | multi-step | 1 lot file | 1 | 1 | write_file | **PASS** | VERIFIED | none | — | `lot/l01.txt` sha256 `589763d29bd18d85` |
| RW-050 | 2026-09-18 | multi-step | 3 lot files | 3 | 3 | write_file | **PASS** | VERIFIED | none | — | `lot/l03.txt` sha256 `ff2178359cc8e165` |
| RW-051 | 2026-09-18 | multi-step | 5 lot files | 5 | 5 | write_file | **PASS** | VERIFIED | none | — | `lot/l05.txt` sha256 `77a02b0c67fbd5ac` |
| RW-052 | 2026-09-18 | multi-step | 10 lot files | 10 | 10 | write_file | **PASS** | VERIFIED | none | — | `lot/l10.txt` sha256 `d8434e146b2020bb` |
| RW-053 | 2026-09-18 | filesystem | 20 writes in **one** planned task | 1 | 20 | write_file | **PASS** | VERIFIED | none | — | 20/20; `lot/l20.txt` sha256 `94b5d8fbf6758812` |
| RW-054 | 2026-09-18 | multi-step | 20 **planned tasks** / 20 writes | 16 | 16 | write_file | **FAIL** (expected cap) | FAILED | none | — | 16/20 files (`l01`–`l16`); `l17`–`l20` absent. `max_plan_tasks` default **16**. Not raised |

## `max_plan_tasks=16` evidence-test

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-055 | 2026-09-18 | multi-step | 16-bin warehouse labels (exactly the cap) | 16 | 16 | write_file | **PASS** | VERIFIED | none | — | 16/16; `bins/b16.txt` sha256 `201ffddc49fb2261`. Cap is **not** a blocker at exactly 16 |
| RW-056 | 2026-09-18 | multi-step | 17-bin warehouse labels (one past the cap) | 16 | 16 | write_file | **FAIL** (expected cap) | FAILED | none | — | 16/17; `bins/b17.txt` **absent**. Planner silently kept `items[:16]`. Useful work blocked only as one-file-per-task; bundling (RW-053) writes 20 files under 1 task |

### Planner hit 16 vs useful-work failure because of the cap

| | count | rows |
|---|---|---|
| Planner **hit** 16 (tasks 17+ dropped before the graph) | **2** | RW-054, RW-056 |
| Useful work **failed because of** the cap | **0** | coding/research/fs/multi-step/recovery all used 1–3 tasks and **VERIFIED**; 20 *actions* in 1 task **VERIFIED** (RW-053); exactly-16 labels **VERIFIED** (RW-055) |

Do not raise `max_plan_tasks`. A cap *encounter* is not a product failure.

## Cycle 4 metrics (honest)

| metric | value |
|---|---|
| GitHub Release `v0.2.3` | **PASS** (already live on `d121c3f`; not re-cut) |
| Suite runnable PASS | 10/10 (plus 1 BLOCKED live NIM) |
| Campaign PASS / FAIL / BLOCKED | **15 / 2 / 1** (the FAILs are RW-054 and RW-056 expected cap) |
| False completion (VERIFIED without the artifact) | **0** |
| New Class A | **none** — grader/verifier advertised disk kinds still agree (RW-057) |
| 20 sequential *actions* | **VERIFIED** (RW-053) |
| 16 sequential planned tasks | **VERIFIED** (RW-055) |
| 17 / 20 sequential planned tasks at default cap | **FAILED** at 16 (RW-056 / RW-054) — documented limit |
| Live NIM | **BLOCKED** |
| Needle | **NOT TESTED** as default (stays `existing` / off) |
| Package / architecture | **0.2.3** frozen; **not v0.3.0** |
| Planner-cap encounters vs useful-work failures | **2 encounters / 0 useful-work failures** |
| Recommendation | **Outcome A — continue 0.2.x** (not B: no Class A patch; not C: no proven v0.3.0 gap) |

### Decision gate (this cycle only)

| # | question | answer |
|---|---|---|
| A | v0.2.3 stable? | **YES** |
| B | Recurring Class A? | **NO** this cycle |
| C | Cap prevents useful work? | **NO** (2 planner hits; 0 useful-work failures) |
| D | 11B still model limitation? | **NOT TESTED** this cycle (NIM BLOCKED) |
| E | Needle earned default? | **NO** |
| F | NIM | **BLOCKED** |
| G | Proven architectural gap? | **NO** |
| H | v0.3.0 justified? | **NO** |

---

# Production use (post-Cycle 4) — package **0.2.3**, no bump

Lane: operator production `rad objective run` on **v0.2.3**. Architecture frozen. Needle stays
experimental / off. Planner cap left at **16**. Not v0.3.0. **No 0.2.x bump.**

These rows are **not** Cycle 4 campaign evidence. Cycle 4 live NIM remained **BLOCKED** on the
Cloud Agent VM (no keys). This is a later operator run.

RW-058 remains historical evidence and is not rewritten. RW-059 is a controlled
`--max-tools 24` follow-up of the same text_analyzer objective (default max-tools **not**
raised). RW-060 is a separate research + artifact objective on the same 11B NIM
lane (not a rewrite of RW-058/059). RW-061 is the scripted Class A investigation
(PR #14). RW-062 is a live Simple Coding + Verification control on the same 11B
NIM lane (not a rewrite of RW-058–061). Default max-tools / max-tasks **not** raised.

## Production campaign (text_analyzer)

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-058a | 2026-09-18 | live NIM (no brain) | production text_analyzer (earlier attempt) | 7 planned / 1 attempted / 0 completed | 0 | 0/12 | **BLOCKED** | — | — | **C** | Home `/tmp/rad_prod_text_analyzer_f3cc7950`; `obj_442301c7`; rad v0.2.3. `MODEL_FAILURE` — no NVIDIA/other keys / no local engine. Workspace empty. False DONE **0**. Same condition family as F-20260918-08 / F-20260918-13 |
| RW-058 | 2026-09-18 IST ~13:39–13:41 | coding (live NIM) | `text_analyzer/{analyzer.py,input.txt,summary.json,test_analyzer.py,README.md}`; exact 3-line input; stdlib; `--max-tasks 8 --max-tools 12` | 5 planned; 1 attempted (verification FAILED, 2 attempts); 4 PENDING | tools 12/12; model calls 7/80; wall ~103s | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | user chose stop; no resume | **B** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct` (NIM key present; Class C closed for this attempt). Home `/tmp/rad_prod_text_analyzer_live_a787512c`; `obj_4e219224`. Disk: `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b`; `analyzer.py` computes counts; `test_analyzer.py` byte-identical to `analyzer.py` (0 tests); README present; `text_analyzer/summary.json` **MISSING**; workspace-root `summary.json` had correct counts `{lines:3,words:13,characters:76}` (wrong path); layout pollution at workspace root. 11B tool spam / incomplete layout / duplicated "tests" / path confusion. **Not Class A**: RAD stopped at tool budget; false DONE **0**; verifier did not rubber-stamp. Bounded `--max-tasks 8 --max-tools 12`. No architecture change |
| RW-059 | 2026-09-18 IST ~14:02–14:04 | coding (live NIM) — controlled tool-budget | same text_analyzer layout as RW-058; stdlib; `--max-tasks 8 --max-tools 24`; Needle `existing` / off | max-tasks 8 | tools 24/24 (`write_file` 19, `run_shell` 5); model calls 25/80; wall ~106s | 24/24 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | budget exhausted | **B** (tool-budget hypothesis **Case B**); Class A candidates **open/investigate**, **not patched** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw059_b48e7b56`; `obj_e1419520`. Disk: all five files present under `text_analyzer/`; `text_analyzer/input.txt` **PASS** sha256 `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` (same as RW-058); `summary.json` **invalid JSON** + wrong counts; tests **FAIL** `13!=6`. False DONE **0**. Doubling 12→24 did not complete the objective. Default max-tools **not** raised. No architecture change. **No v0.2.4.** |

## Production metrics (honest)

| metric | value |
|---|---|
| Package / architecture | **0.2.3** frozen; **not v0.3.0**; **no v0.2.4** (no Class A) |
| Attempt 1 (no brain) | **BLOCKED** Class C (RW-058a) |
| Attempt 2 (live NIM 11B) | **FAIL** Class B (RW-058) — `needs_user`; success criteria unmet |
| False completion (VERIFIED without the artifact) | **0** |
| Class A | **none** |
| Live NIM (this operator run) | Attempt 1 Class C; attempt 2 key present (Class C closed for that attempt) and incomplete vs layout |
| 11B model limitation | **documented live** — tool budget exhausted; incomplete layout (F-20260918-15) |
| Needle | stays `existing` / off; **not measured** this run |
| `max_plan_tasks` | **16** unchanged (this run used `--max-tasks 8`) |
| Recommendation | **Outcome A — continue 0.2.x** (not B: no Class A patch; not C: no proven v0.3.0 gap) |

## Controlled tool-budget experiment (RW-059 vs RW-058)

RW-058 is left unchanged as historical evidence. RW-059 is the same production
text_analyzer objective with **only** `--max-tools` doubled (12 → 24). Default
max-tools is **not** raised. Package stays **0.2.3**.

| | RW-058 (historical) | RW-059 (this experiment) |
|---|---|---|
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` |
| objective id | `obj_4e219224` | `obj_e1419520` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same |
| `--max-tasks` | 8 | 8 |
| `--max-tools` | **12** | **24** (run only; default unchanged) |
| Needle | `existing` / off | `existing` / off |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 |
| tools used | 12/12 exhausted | 24/24 exhausted (`write_file` 19, `run_shell` 5) |
| model calls | 7/80 | 25/80 |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** |
| disk | 4/5 under `text_analyzer/`; `summary.json` **MISSING** (root file had correct counts, wrong path) | all five files under `text_analyzer/`; `summary.json` invalid JSON + wrong counts; tests **FAIL** `13!=6` |
| `input.txt` sha256 | `bf69eb737ca6f3949b5626701cb8472a2fc683e6b05e3101744eccd49dab629b` | same |

| metric | value |
|---|---|
| Tool-budget hypothesis | **Case B** — 24 did **not** suffice (both runs exhausted budget; both `needs_user` / FAIL) |
| Class A this experiment | **not patched.** Suspected candidates **open/investigate** (F-20260918-17, F-20260918-18). Do not treat as fixed |
| Class B remaining | invalid JSON `summary.json`; wrong counts; tests FAIL `13!=6` (F-20260918-19) |
| Default max-tools | **unchanged** |
| Package | **0.2.3** — **no v0.2.4** unless a later confirmed Class A fix |
| Recommendation | **Outcome A — continue 0.2.x** |

## Research + artifact (RW-060)

RW-058 / RW-059 stay as historical text_analyzer evidence above. RW-060 is a
different production objective (research + written artifact) on the same 11B NIM
lane. Docs-only. Default max-tools / max-tasks **not** raised. Package stays
**0.2.3**. Class A candidates from RW-059 remain parked (not this record).

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-060 | 2026-09-18 IST ~14:25–14:27 | research (live NIM) | Real-World Research + Artifact — pathlib reference (`pathlib_reference.md` + `pathlib_reference/README.md`); `--max-tasks 8 --max-tools 16`; Needle `existing` / off | max-tasks 8 | tools 16/16; model calls 18/80; wall ~110s | 16/16 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | budget exhausted | **B** | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw060_eb0192`; `obj_b114afd4`. Disk: `pathlib_reference/README.md` **EXISTS** sha256 `48f0d39b…`; `pathlib_reference.md` **EXISTS** but **162 B stub** — sections 3–9 **FAIL**, 0 examples; no docs.python.org fetch. False DONE **0**. **Not Class A**; **not Class C**. Pattern generalizes vs RW-058/059: a research workload also fails under 11B+tool budget before a substantive deliverable. Default max-tools / max-tasks **not** raised. No architecture change. **No v0.2.4.** |

### RW-060 vs text_analyzer runs (RW-058 / RW-059)

| | RW-058 | RW-059 | RW-060 |
|---|---|---|---|
| category | coding (live NIM) | coding (live NIM) — controlled tool-budget | research + artifact (live NIM) |
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw060_eb0192` |
| objective id | `obj_4e219224` | `obj_e1419520` | `obj_b114afd4` |
| model | NIM 11B `meta/llama-3.2-11b-vision-instruct` | same | same |
| `--max-tasks` | 8 | 8 | 8 |
| `--max-tools` | **12** | **24** (run only; default unchanged) | **16** (run only; default unchanged) |
| Needle | `existing` / off | `existing` / off | `existing` / off |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 | ~110s IST ~14:25–14:27 |
| tools used | 12/12 exhausted | 24/24 exhausted | 16/16 exhausted |
| model calls | 7/80 | 25/80 | 18/80 |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** |
| disk | 4/5 under `text_analyzer/`; `summary.json` **MISSING** | all five files under `text_analyzer/`; `summary.json` invalid JSON + wrong counts; tests **FAIL** `13!=6` | `pathlib_reference/README.md` EXISTS sha256 `48f0d39b…`; `pathlib_reference.md` EXISTS, **162 B stub**; sections 3–9 **FAIL**; 0 examples; no docs.python.org fetch |
| class | **B** | **B** (Case B on tool-budget) | **B** (not A, not C) |

| metric | value |
|---|---|
| Pattern | **generalizes** — coding (RW-058/059) *and* research (RW-060) fail under 11B+tool budget before a substantive deliverable |
| Class A this record | **none** (parked F-20260918-17 / F-20260918-18 stay open/investigate; **not this PR**) |
| Class C | **none** (NIM key present) |
| Default max-tools / max-tasks | **unchanged** |
| Package | **0.2.3** — **no v0.2.4** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Class A investigation (budget exhaustion → needs_user)

RW-058 / RW-059 / RW-060 rows above are **not rewritten**. This is a deterministic
control-plane investigation of those `needs_user` outcomes (parked F-20260918-17 /
F-20260918-18). No live NIM. No default max-tools / max-tasks raise. Cap **16**
unchanged. Needle `existing` / off. Package stays **0.2.3**.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-061 | 2026-09-18 | investigation (scripted; no NIM) | Class A probe of tool-budget → `needs_user` on v0.2.3 (`a40a544`); Scenarios A/B/C + F-17/F-18 | n/a (injected plans) | injected tool counts | default **60** unchanged (not a live `--max-tools`) | **no RAD defect**; live RW-058/059/060 remain **FAIL** Class B | Scenario A `VERIFIED`; B/C `needs_user` when checks unmet | B: checkpoint + resume continues; C: not recoverable without more budget/work | **NONE** (suspects not confirmed) | Tests `tests/test_class_a_budget_investigation.py` **17 passed**; full pytest **345 passed**; `rad doctor --offline` READY; `rad acceptance` 50/50; `rad realworld` 10 passed / 1 BLOCKED (`live_nim`). False DONE **0**. F-17 newline split **not** in fallback. F-18 ENV misclass **not** the live path. **No patch. No v0.2.4.** Architecture frozen. |

### Investigation vs live 11B rows

| | RW-058 | RW-059 | RW-060 | RW-061 (this investigation) |
|---|---|---|---|---|
| kind | live NIM coding | live NIM coding, extra tools | live NIM research | scripted controller, no model |
| status | `needs_user` / FAIL | `needs_user` / FAIL | `needs_user` / FAIL | no product run; path proven correct |
| false DONE | **0** | **0** | **0** | **0** |
| class | **B** (preserved) | **B** (preserved) | **B** (preserved) | **NONE** — Class A **not proven** |
| F-17 / F-18 | parked | parked | parked | **investigated / not Class A** |

| metric | value |
|---|---|
| RAD defect demonstrated | **NO** |
| Patch required | **NO** |
| 16-task cap | **UNCHANGED** |
| Default tool budget | **UNCHANGED** (60) |
| Needle | **OFF** (`existing`) |
| Package | **0.2.3** — **no v0.2.4** |
| Recommendation | **Outcome A — continue 0.2.x** |

## Simple Coding + Verification control (RW-062)

RW-058 / RW-059 / RW-060 / RW-061 rows above are **not rewritten**. RW-062 is a
live **Simple Coding + Verification** control on the same 11B NIM lane: a simpler
coding workload than text_analyzer, still with disk-checked files + tests.
Docs-only. Default max-tools / max-tasks **not** raised. Package stays **0.2.3**.
No Class A patch. PR #14 (RW-061) closed F-17 as not-confirmed from a
deterministic test; this live run is additional evidence, not a product fix.

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-062 | 2026-09-18 IST ~15:41–15:47 | coding (live NIM) — Simple Coding + Verification control | Simple Coding + Verification; `--max-tasks 4 --max-tools 12`; Needle `existing` / off | `PLAN_CREATED` **source=fallback** after nvidia plan timeout; **7** newline-split spurious tasks | tools 12/12; wall ~383s | 12/12 exhausted | **FAIL** vs success criteria (`needs_user`); **NOT DONE**, **not VERIFIED** complete | FAILED | budget exhausted | **B** primary; F-17 evidence **strengthened** (not patched) | Provider nvidia / `meta/llama-3.2-11b-vision-instruct`. Home `/tmp/rad_prod_rw062_6ede431b`; `obj_7a020865`. Disk: five files exist; `result.json` as-left **INVALID** `{`; tests **FAIL** `6!=2`; pollution `DONE:` fake path. False DONE **0**. **Not Class C** (NIM key present). Simple workload also fails similarly → Class B is **not** limited to complex objectives. Default max-tools / max-tasks **not** raised. No architecture change. **No v0.2.4.** |

### RW-062 vs prior production rows (RW-058–061)

| | RW-058 | RW-059 | RW-060 | RW-061 | RW-062 (this control) |
|---|---|---|---|---|---|
| kind | live NIM coding | live NIM coding, extra tools | live NIM research | scripted controller, no model | live NIM **simple** coding + verification |
| home | `/tmp/rad_prod_text_analyzer_live_a787512c` | `/tmp/rad_prod_rw059_b48e7b56` | `/tmp/rad_prod_rw060_eb0192` | n/a (pytest) | `/tmp/rad_prod_rw062_6ede431b` |
| objective id | `obj_4e219224` | `obj_e1419520` | `obj_b114afd4` | Scenarios A/B/C | `obj_7a020865` |
| `--max-tasks` | 8 | 8 | 8 | n/a (injected plans) | **4** (run only; default unchanged) |
| `--max-tools` | **12** | **24** | **16** | default **60** unchanged | **12** (run only; default unchanged) |
| Needle | `existing` / off | `existing` / off | `existing` / off | `existing` / off | `existing` / off |
| wall | ~103s IST ~13:39–13:41 | ~106s IST ~14:02–14:04 | ~110s IST ~14:25–14:27 | n/a | ~383s IST ~15:41–15:47 |
| planner | llm (5 planned) | llm | llm | injected | **fallback** after nvidia plan timeout; 7 newline-split spurious tasks |
| tools used | 12/12 exhausted | 24/24 exhausted | 16/16 exhausted | injected counts | 12/12 exhausted |
| final status | `needs_user` / **FAIL** | `needs_user` / **FAIL** | `needs_user` / **FAIL** | no product run; path proven correct | `needs_user` / **FAIL** |
| false DONE | **0** | **0** | **0** | **0** | **0** |
| disk | 4/5 under `text_analyzer/`; `summary.json` **MISSING** | five paths; invalid JSON + wrong counts; tests **FAIL** `13!=6` | pathlib stub; sections 3–9 **FAIL** | n/a | five files exist; `result.json` as-left INVALID `{`; tests **FAIL** `6!=2`; pollution `DONE:` fake path |
| class | **B** (preserved) | **B** (preserved) | **B** (preserved) | **NONE** — Class A **not proven** (PR #14) | **B** primary; F-17 **reopened** as live evidence (no patch) |

| metric | value |
|---|---|
| Pattern | **generalizes further** — complex coding (RW-058/059), research (RW-060), **and simple coding+verification (RW-062)** fail under 11B+tool budget before a passing, verifiable result. Class B is not complexity-limited |
| F-17 | PR #14 / RW-061: deterministic newline-only goal → 1 fallback task; live RW-058/059/060 were **llm**. **RW-062:** `PLAN_CREATED` source=**fallback**; 7 tasks (then labeled newline-split). **Later (RW-063 / F-23):** timeout path uses `obj.goal` only; 7 = clause split of the user goal (`[:7]`), not model-output parse, not `\n` split. Class A **NOT CONFIRMED**. **No product fix** |
| Class A this record | **none patched** |
| Class C | **none** (NIM key present) |
| Default max-tools / max-tasks | **unchanged** |
| Package | **0.2.3** — **no v0.2.4** |
| Recommendation | **Outcome A — continue 0.2.x** |

## F-17 timeout / prose investigation (RW-063)

RW-058 / RW-059 / RW-060 / RW-061 / RW-062 rows above are **not rewritten**.
RW-063 is a scripted (no NIM) investigation of the planner timeout → fallback
path after PR #15 (`d15af713`). Architecture frozen. Needle OFF. Cap 16 and
default max-tools **UNCHANGED**. Package stays **0.2.3**. **No product patch.**

| id | Date | Category | Objective | #tasks | #actions | Tools | Result | Verification | Recovery | Failure class | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| RW-063 | 2026-09-18 | investigation (scripted; no NIM) | F-17: does fallback convert model output after planner timeout? Scenarios A–D + PR #14 vs RW-062 | A: llm 2 tasks; B: fallback 7 (goal clauses); C: fallback 3 (prose *goal*); D: fallback ≤7 | n/a (plan + bounded drive) | default **60** unchanged | **no RAD defect**; F-17 **NOT CONFIRMED** | fallback tasks UNVERIFIED; objective not VERIFIED without checks | n/a | **NONE** | Timeout/empty/malformed/non-JSON LLM discarded; `_fallback(obj)` splits `obj.goal` on clause markers, not newlines, cap `[:7]`. One-sentence goal + 7-line model prose → 1 task. `--max-tasks 4` drives ≤4 of 7 planned. False DONE **0**. Needle OFF. Cap 16 UNCHANGED. **No patch. No v0.2.4.** |

| metric | value |
|---|---|
| Trigger | nvidia plan timeout (RW-062) → `PLAN_CREATED` source=fallback |
| Fallback path | `Planner.plan` `except` / no JSON / empty graph → `_fallback(obj)` — **never** the LLM `raw` string |
| Parser behavior | `re.split(r"\b(?:and then|then|;|, and)\b|\.(?=\s|$)", obj.goal)` then `[:7]` |
| PR #14 vs RW-062 | newline-only → 1 task (PR #14 true). 7 tasks = period/clause split of a seven-sentence **goal** (RW-062 count), not `\n` split of model output |
| Spurious model-output tasks | **0** |
| Tool/Budget impact | up to 7 no-check tasks after timeout; drive `--max-tasks` can stop earlier; default tools **60**; not unbounded to 16 |
| Class A | **NO** |
| Patch / Regression (product) | **NO** / investigation tests only |
| Package | **0.2.3** — **no v0.2.4** |
| Gates | pytest **364 passed**; `rad doctor --offline` READY; `rad acceptance` 50/50; `rad realworld` 10 passed / 1 BLOCKED (`live_nim`) |
| Recommendation | **Outcome A — continue 0.2.x** |
