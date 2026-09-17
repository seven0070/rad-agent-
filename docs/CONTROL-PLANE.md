# Agent Control Plane (`rad/control/`)

## Why
The chat loop (`session.py`) lets the LLM orchestrate itself: it decides when it is
done, nothing checks, nothing survives a crash. The control plane inverts that:
**RAD owns state, plans, budgets, verification and recovery; the LLM proposes.**

## Modules
| file | role |
|---|---|
| `objectives.py` | `Objective` (goal, criteria, budget/usage, status) + `ObjectiveStore` (disk) |
| `tasks.py` | `Task` with explicit state machine, `Check` (machine-verifiable condition) |
| `graph.py` | `TaskGraph` DAG: ready-set, doom propagation, optional branches, cycle check |
| `planner.py` | LLM → task graph *with checks*; deterministic fallback without a brain |
| `controller.py` | lifecycle: create / plan / run / resume / pause / cancel; the drive loop |
| `observer.py` | `Observation` per tool call, `Artifact` registry (sha256, versions, lineage) |
| `verifier.py` | tool → checks → artifacts → objective; result is `VERIFIED` / `FAILED` / `UNVERIFIED` |
| `recovery.py` | failure classification + bounded strategy (retry_with_hint / repair / replan / ask_user / abort) |
| `events.py` | append-only JSONL event log per objective (`rad trace`) |
| `cli.py` | `rad objective …`, `rad trace`, `rad inspect`, `rad events` |

## Execution
The Controller reuses the existing `Session` (DNA + memory + tools + router) — it does
not duplicate the brain loop. It injects `session.tool_runner` to wrap every tool call
with budget enforcement and observation, and sets `_rad_current_task` so observations
attach to the right task.

## Task state machine
```
PENDING → READY → RUNNING → OBSERVING → VERIFYING → COMPLETED
                     │                      │
                     ▼                      ▼
                  FAILED ──► RETRYING ──► READY
                     │
          BLOCKED / NEEDS_USER / CANCELLED
```
Illegal transitions raise. Every transition is on `task.history` and in the event log.

## Verification policy
* `VERIFIED` requires at least one machine check to pass and none to fail.
* `UNVERIFIED` = no checks were available. A task may still complete as UNVERIFIED if the
  model claimed `DONE:` and no tool errored — this is recorded on the task and surfaced in
  the objective's final report. Set `accept_unverified_done: false` to forbid it.
* `llm_judge` checks are stored with `machine: false` and can never produce `VERIFIED`.

## Recovery policy (deterministic)
| class | strategy |
|---|---|
| AUTH / PERMISSION | ask_user |
| MODEL ("no brain") | ask_user; other model errors → retry (router falls back) |
| TRANSIENT / NETWORK | retry while attempts remain |
| ENVIRONMENT (not found / no module) | insert a **repair task** once, then retry_with_hint, then ask_user |
| VALIDATION / TOOL / UNKNOWN | retry_with_hint (explicit failed-check feedback) → replan once → ask_user |

Bounded by `task.max_attempts` (3), one repair/replan per task, and the objective's retry budget.

## Persistence / resume
Checkpoint after every task: `objective.json`, `tasks.json`, `CHECKPOINT` event. `resume()`
moves tasks left in RUNNING/OBSERVING/VERIFYING back to RETRYING, reopens NEEDS_USER/BLOCKED
tasks, and continues. Completed tasks are never re-run.

## Parallelism (Phase 3)
Ready tasks with satisfied dependencies run concurrently up to `objective_parallel`
(default 2) — **only with `--auto`**, since confirmations are interactive. Each task gets
its own `Session`; budget counters, the event log and the artifact registry are
lock-protected. Set `objective_parallel: 1` for strictly sequential runs.

## Replay & provenance (Phase 3)
* Every attempt records a `TRANSCRIPT` event: exact prompt, reply, provider, error.
* `rad replay [id] [--prompts] [--verify]` reconstructs each attempt (prompt → tools →
  results → verification → recovery). `--verify` re-runs all checks against the *current*
  workspace and flags **drift** (verified then, failing now).
* `rad why <artifact>` — creator action, task/attempt, sha256 lineage across versions,
  and the evidence (files read / pages fetched) consulted in that task *before* creation.
* `rad why <claim>` — token-overlap search over recorded observations; `UNSUPPORTED`
  means RAD produced the claim without consulting anything (i.e. from model priors).
  Web sources are labelled `untrusted-web`. No model is involved in answering.

## Not yet (later phases)
Capability-based permissions · sandbox · SQLite store · deterministic re-execution of
side effects (replay is inspect + re-verify, not re-run).
