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

## Not yet (later phases)
Parallel execution of ready tasks (graph supports it; executor is sequential) · provenance
chains for claims · capability-based permissions · sandbox · SQLite store · replay of model
decisions (events record prompts' purpose but not full prompts yet).
