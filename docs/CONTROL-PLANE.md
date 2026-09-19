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
| `planner.py` | LLM → task graph *with checks*; bounded retry (default 1) on timeout/empty/malformed JSON *before* fallback; fat plans retried/selected to fit remaining tool budget; deterministic fallback without a brain (goal clause-split, no checks — F-17; compacted when still fat; independent later file-write clauses get empty `depends_on` — E2 / RW-087); coding goals infer `json_valid` / test `shell_ok` / exact `file_line_count` as *objective* checks and merge them into LLM plans that omitted them (fallback *tasks* stay check-less); package-layout goals get check paths joined to the named directory including ASCII-tree `pkg/` layouts (RW-069 / RW-073) |
| `budgetplan.py` | budget-aware planning helpers: remaining tools, 2-tools/task estimate, fat vs small (F-21), fallback compact; leftover-tool reserve for intra-run yield (E1); E2 empty `depends_on` on independent fallback file clauses so those tasks can enter the READY set |
| `codingloop.py` | verified coding loop helpers: coding-goal detection, DONE: pollution, broken-artifact repair hints, package-dir path alignment, merge of omitted json/line-count/test contracts |
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
* A `DONE:` path or a file whose body is only a `DONE:` claim is pollution, not an artifact.

## Recovery policy (deterministic)
| class | strategy |
|---|---|
| AUTH / PERMISSION | ask_user |
| MODEL ("no brain") | ask_user; other model errors → retry (router falls back) |
| TRANSIENT / NETWORK | retry while attempts remain |
| ENVIRONMENT (not found / no module) | insert a **repair task** once, then retry_with_hint, then ask_user. `mkdir` / create **already exists** is **not** ENVIRONMENT (RW-071) — mixed File-exists + no-such-file noise uses TOOL/VALIDATION so remaining tools are not spent on Repair-prerequisite thrash. `pip install -r` when the requirements file is missing is **not** ENVIRONMENT (RW-075) — that is TOOL/VALIDATION, not a missing-env repair. Premature `python …/test_*.py` (interpreter `can't open file` a `.py` script the agent has not written) is **not** ENVIRONMENT (RW-079) — sequencing, not a missing host dependency. Invented tool `DONE` / `DONE: …` is a protocol mistake: it errors, but does not fail a task whose explicit machine checks passed |
| VALIDATION / TOOL with **broken artifacts** (`json_valid`, `json_field`, `json_min_len`, `shell_ok`, `shell_output`) | insert a **repair task** once with the concrete failure (stderr / invalid JSON / expected vs actual), then retry_with_hint → replan once → ask_user. Models propose; RAD decides. A `DONE:` line is never an artifact path. |
| VALIDATION / TOOL / UNKNOWN (missing file, `file_exists` fail, other) | retry_with_hint (explicit failed-check feedback) → replan once → ask_user |

When a tool or retry budget is exhausted the controller does **not** treat a model `DONE:` as success. If the graph is already complete, or remaining tasks / objective_checks are already proven by machine checks, it falls through to `_verify_objective` (the 11B over-decompose case where the file is on disk). Otherwise the objective ends `needs_user`. Unmet checks still cannot become `VERIFIED`.

## Persistence / resume
Checkpoint after every task: `objective.json`, `tasks.json`, `CHECKPOINT` event. `resume()`
moves tasks left in RUNNING/OBSERVING/VERIFYING back to RETRYING, reopens NEEDS_USER/BLOCKED
tasks, and continues. Completed tasks are never re-run. Budget exhaustion with unmet
work is `needs_user` plus that same checkpoint; OPEN tasks whose machine checks
already pass can close without a model call.

Crash-resume is **shipped** (`CheckpointManager`, `rad objective resume`;
acceptance gate 14). Intra-run yield so later independent READY tasks still get
≥1 attempt when an early sequential task would burn remaining tools is
**implemented as v0.4.6** (theme 3 slice E1; `TaskYield` + leftover-tool
reserve + `Scheduler` skip of yielded tasks). Same `checkpoint.json` format.
Linear fallback `depends_on` for independent later file-write clauses is
empty as of **v0.4.8** (theme 3 slice E2; scripted RW-087) so those tasks
can enter the E1 READY set. Explicit LLM chains are not rewritten.
Missing optional `xxd` / hexdump / `sha256sum` (checksum theater) is
**not** ENVIRONMENT as of **v0.4.7** (theme 3 slice F). Do not treat
crash-resume with a raised budget as that gap, and do not invent a
second persistence stack.

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
