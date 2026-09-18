# v0.2.3 validation cycle — closeout (finish-line execution)

**Date:** 2026-09-18
**Package:** **0.2.3** (start and end — not re-cut, no 0.2.x bump) · `main` tip `aecfbae`
**Architecture:** **FROZEN** · **Router:** `existing` · **Needle:** **OFF** · 16-task cap: **UNCHANGED** · default tool budget: **60 UNCHANGED**

**Mission.** Obtain enough trustworthy evidence to close the v0.2.3 validation cycle and
determine whether v0.2.3 remains frozen as the production baseline. Not a redesign.
No v0.2.4 or v0.3.0 unless a genuine Class A defect or a demonstrated architectural
capability gap requires it.

---

## Phase 1 — Provider gate (result: **BLOCKED**)

Rule: require **BOTH** `available_count ≥ 1` **AND** `actual_chat_check = SUCCESS`.

Every supported RAD provider / local-engine path was exercised exactly once (no repeats):

| path | method (RAD's own code) | result |
|---|---|---|
| edge0 (local, 127.0.0.1:8000) | `rad models` / `probe_local` | **not running** |
| ollama (local, 127.0.0.1:11434) | `rad models` / `probe_local` | **not running** |
| lmstudio (local, 127.0.0.1:1234) | `rad models` / `probe_local` | **not running** |
| groq, cerebras, gemini, openrouter, nvidia (free cloud) | `rad keys list` — vault → env → `.env` | **no key** |
| openai, anthropic, mistral, grok (paid cloud) | same | **no key** |
| `.env` files (cwd, `~/.env`, `~/.rad/keys/.env`) | filesystem check | **absent** |
| Rad key vault (`~/.rad`) | `rad keys list` | **empty** (no `~/.rad` pre-existing) |
| router chain | `RouterState(home).build_chain()` | **available_count = 0**, chain empty |

**Gate: FAILED** on the first condition (`available_count = 0`); the chat check has no
candidate to test, so it cannot be SUCCESS.

Recorded, per plan: **Provider status: BLOCKED · Classification: Class C · RAD defect: NO
· Patch: NO.** Live workload execution stopped. **No objective created. RAD not modified.
Probes not repeated.** External provider configuration (a key or a local engine) is the
**only blocking dependency** for any further live workload.

Ledger entry: **F-20260918-22** (same environmental family as F-20260918-08 / -13 / -14).

## Phase 2 — RW-063R

**Not run** — the gate failed. No objective created, no tools used.
If a provider becomes available, it proceeds unchanged:

```
RAD_TOOL_ROUTER=existing rad objective run "<csv_report objective>" \
    --max-tasks 6 --max-tools 16 --auto        # fresh workspace; Needle OFF
```

## Phase 3 — Independent verification

Not applicable this cycle (no live workload executed). The **fresh offline invariant
evidence below** is the independent confirmation for this exact checkout, in this
environment, on `aecfbae`. Model claims were not treated as verification anywhere.

| gate | result |
|---|---|
| `rad version` | **v0.2.3** |
| `python -m pytest -q` | **345 passed** in 10.12s (fresh venv, `.[dev]`) |
| `rad doctor --offline` | **20 READY · 0 WARNING · 3 OPTIONAL · 0 ERROR** — verdict READY, exit 0 (`/tmp/rad-c5-gate`) |
| `rad acceptance` | **50/50 PASSED** — evidence `/tmp/rad-c5-gate/acceptance/20260918-122413_gate.json` |
| `rad realworld` | **10 passed / 1 BLOCKED / 0 failed** — `live_nim` Class C (no NVIDIA key); `false_success` / `needs_user` / `no_loop` ended `needs_user`, **not** VERIFIED — evidence `/tmp/rad-c5-gate/realworld/20260918-122353_realworld.json` |

## Phase 4 — Additional workloads (A: JSON transform · B: log analysis · C: documentation/filesystem)

**Not run** — the finish plan allows them only when a provider is actually available.
They are blocked by the same single external dependency as RW-063R.

## Phase 5 — Classification of all live evidence

| workload | lane | outcome | false DONE | class |
|---|---|---|---|---|
| RW-058 | live NIM 11B, coding (`--max-tools 12`) | `needs_user` / FAIL — incomplete layout, budget 12/12 exhausted; verifier did **not** rubber-stamp | **0** | **B** (F-20260918-15) |
| RW-059 | live NIM 11B, coding (`--max-tools 24`) | `needs_user` / FAIL — all paths present but invalid JSON / wrong counts / tests FAIL `13!=6`; budget 24/24 | **0** | **B** (F-20260918-16 / -19) |
| RW-060 | live NIM 11B, research + artifact (`--max-tools 16`) | `needs_user` / FAIL — 162 B stub, sections 3–9 FAIL; budget 16/16 | **0** | **B** (F-20260918-20) |
| RW-061 | scripted investigation (no model) | Scenarios A/B/C + F-17/F-18: path proven correct | **0** | **NONE** (F-20260918-21) |
| RW-062 | live (historical) | trace **unavailable** | n/a | **UNAVAILABLE FOR AUDIT** |
| RW-063 | provider gate (no live run) | BLOCKED — provider unavailable; no objective | **0** | **C** |
| RW-063R | provider gate (retry; no live run) | **BLOCKED at gate** — `available_count = 0` (F-20260918-22); no objective, no tools | **0** | **C** |

**No new Class A defect is demonstrated.** Model-quality failures (bad code, over-
decomposition, wrong counts) are Class B, not Class A — RAD correctly refused completion
every time.

## Phase 6 — RW-062

Historical trace **not recoverable** in this environment. Marked:

**RW-062 = UNAVAILABLE FOR AUDIT.** No further effort spent reconstructing missing data,
per the finish plan. Missing RW-062 evidence does not block the rest of the release.

## Phase 7 — F-20260918-17

Status: **NOT CONFIRMED** · Patch: **NO**. The deterministic investigation
(F-20260918-21, `tests/test_class_a_budget_investigation.py`, 17 passed) established:
malformed raw LLM responses are rejected, and the fallback planner operates on the
original objective — it splits on clause markers, **not** on newlines in raw model
responses. RW-058/059/060 had a live brain, so their planner source was `llm`, not
fallback. Do not reopen without new evidence showing different behavior.

## Phase 8 — Finish decision

| # | condition | met | evidence |
|---|---|---|---|
| 1 | RW-063R executed with a real provider, **OR** environment demonstrably unable to provide one and the blocker explicitly recorded | **YES** (second branch) | gate run this cycle: `available_count = 0`; F-20260918-22 |
| 2 | all available live evidence classified | **YES** | table in Phase 5 — every row B / C / NONE / unavailable |
| 3 | no unresolved Class A defect demonstrated | **YES** | none; F-17 / F-18 investigated, not confirmed, no patch |
| 4 | false completion remains 0 | **YES** | every live row false DONE 0; honesty cases `needs_user`, not VERIFIED |
| 5 | no budget/permission/verification invariant violated | **YES** | fresh gates: 345 pytest · doctor READY · 50/50 acceptance · realworld 10/1/0; live runs stopped at budgets; verifier never rubber-stamped; workspace jail held |
| 6 | remaining failures are Class B, C, or known limitations | **YES** | B = 11B model quality; C = provider availability; known = 16-task cap (2 hits / 0 useful-work failures) |

**Decision: the v0.2.3 validation cycle is CLOSED.** The provider-unavailable condition
is an environment blocker, not a reason to keep rerunning the same experiment.

## Final state

```
RAD v0.2.3
VALIDATION CYCLE: CLOSED
ARCHITECTURE: FROZEN
PRODUCTION BASELINE: v0.2.3
FALSE COMPLETION: 0
CLASS A DEFECT: NONE DEMONSTRATED
F-20260918-17: NOT CONFIRMED
RW-062: UNAVAILABLE FOR HISTORICAL AUDIT
PROVIDER BLOCK: ENVIRONMENTAL (0 providers available at closeout)
```

No v0.2.4 was created. No v0.3.0 was started. No feature was added to increase a
progress percentage.

## v0.3.0 (post-close)

Separate evidence-only review: `docs/V030_CAPABILITY_GAP.md`. No capability from this
campaign's real use meets the evidence bar → **v0.3.0 remains undefined**. The next
development cycle must begin from an evidence-backed capability gap, not from an
arbitrary desire to add features.
