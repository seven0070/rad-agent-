# Benchmarks, evaluation and regression

RAD measures itself at four levels. All of them run offline by default (scripted agents, real tools,
real verification) and all of them are graded on **what is on disk**, never on what a model said.

| level | command | what it answers |
|---|---|---|
| capability battery | `rad benchmark` | how well does the current brain handle math/logic/code/tools/JSON/style? |
| agent lab | `rad lab run --suite bank:<category>` | can RAD finish whole objectives, safely and honestly? |
| long horizon | `rad benchmark long` | can RAD run 20–50 action objectives without losing the thread? |
| whole goals | `rad realworld` | research, coding, multi-agent and failure-recovery end to end |
| regression | `rad regression` | did anything get worse since last time? |
| acceptance | `rad acceptance` | is every architectural requirement still satisfied? |

## 1. Capability battery — `rad benchmark`

```bash
rad benchmark --sample 20 --cats reasoning,code        # live model grading (needs a brain)
rad benchmark history -n 8
```

Deterministic graders (exact match, regex, JSON parse, numeric tolerance), 16 categories: math,
logic, code, tool, json, summarize, style, planning, memory, long_context, structured, research,
instruction, safety, recovery, vision. A single impressive answer proves nothing: scores are
comparable across days and stored in history.

## 2. The agent lab — 900 scenarios, 9 categories

```bash
rad lab run --suite bank --sample 20            # 900-task bank (9 × 100)
rad lab run --suite bank:adversarial --sample 50
rad lab run --suite bank:recovery --ids recovery_006_fam6
rad lab history -n 5
```

| category | scenarios | what it stresses |
|---|---|---|
| reasoning, tool_use, coding, research, planning, memory | 100 each | normal competence across the task types RAD is for |
| long_horizon | 100 | objectives with 12–47 real tool actions |
| recovery | 100 | injected tool / network / model / invalid-output / failing-test faults |
| adversarial | 100 | dishonest models, canary files, prompt injection, budget attacks |

Every scenario runs a full objective through the control plane (planner → graph → executor →
policy → tools → observer → verifier) in a throw-away home with its own workspace, then grades the
filesystem. Reported per run: success, verified rate, honesty (did RAD ever claim more than the
graders found), safety (canaries touched, hard denials), tool calls, retries, cost, latency.

## 3. Long-horizon benchmark

```bash
rad benchmark long --sample 6
```

Same bank, focused metrics: objective/task completion, correctness, verification accuracy, recovery
rate, human-intervention rate, tool-failure rate, retries, cost, latency, **false-completion rate**
(a task marked done that the graders reject must be 0).

## 4. Whole-goal acceptance tests — `rad realworld`

```bash
rad realworld                    # all four, ~1s offline
rad realworld --only research,coding --json
```

* **research** — multi-source gathering with a conflicting figure (42 vs 57), cross-checking,
  single-source claims flagged, structured report with citations, verified by re-reading artifacts.
* **coding** — a broken package: inspect, repair, run the tests, diagnose the remaining failure,
  repair again, verify with the test file's hash unchanged.
* **multi_agent** — researcher / reviewer / writer delegated as control-plane tasks; the reviewer is
  a different agent with a read-only envelope whose verdict comes from reading the artifact.
* **failure** — injected tool, network, provider and invalid-output faults plus a crash/restart:
  RAD recovers, preserves finished work, and the checkpoint restores cleanly.

## 5. Regression system — `rad regression`

```bash
rad regression                # unit + security + agent + integration groups, live agent sample, long-horizon subset
rad regression --quick        # security + agent groups, 4 benchmark scenarios (~1 s)
rad regression history -n 5
rad regression compare        # what changed between the last two runs
```

A run records each group's pass/fail plus a live lab sample and a long-horizon sample, then produces
a verdict. A drop in any of them — or honesty/safety below 1.0 — fails the verdict and blocks
promotion (`rad evolve`, `rad brain promote`).

## 6. Acceptance gate — `rad acceptance`

```bash
rad acceptance                 # 50 items, per-item evidence, ~8s
rad acceptance --area security
rad acceptance --json > gate.json
rad acceptance --full          # wider benchmark sample
```

The gate is the definition of "finished" for this repository: 50 requirements, each demonstrated by
running the real thing (a live objective, a crash and resume, an MCP handshake, an API request, a
local browser server, a budget stop). See [ACCEPTANCE.md](ACCEPTANCE.md) for the item list and the
evidence each one produces.
