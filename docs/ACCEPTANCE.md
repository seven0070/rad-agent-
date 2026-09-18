# The acceptance gate

`rad acceptance` runs **50 requirements** against a throw-away RAD home, so a used
machine gives the same verdict as a fresh one. Every item *executes* the real thing — a live
objective through the control plane, a crash and resume, an MCP handshake, an HTTP request over
a real socket, a local browser server, a budget stop — and returns the evidence it produced.
Structural claims name where to look; behavioural claims run the code and grade the disk.

```bash
rad acceptance                 # all items, ~12s offline, writes <home>/acceptance/<ts>_gate.json
rad acceptance --area control  # one area (reported honestly as a partial run)
rad acceptance --json          # machine-readable, with per-item evidence
rad acceptance --full          # wider benchmark sample (slower, more scenarios)
```

Exit code is 0 only if every item passes and the whole gate ran. A failing item prints what was
expected, what happened, and the command that reproduces it — the gate doubles as a to-do list,
and it is how this repository decides whether the architecture is actually finished.

## Items

### Runtime & install

| # | requirement | reproduce |
|---|---|---|
| 1 | No mandatory infrastructure — A plain install runs locally with no database, no service and no third-party runtime dependency | `rad status` |
| 2 | v1 compatibility — Every v1 command still exists and works | `rad --help` |
| 3 | Health checks — rad doctor covers python/deps/config/models/keys/runtimes/storage/MCP/browser/voice/filesystem/permissions/corrupt state with actionable output | `rad doctor` |

### Control plane

| # | requirement | reproduce |
|---|---|---|
| 4 | Objectives — id/goal/criteria/constraints/priority/deadline/budget/status/timestamps + lifecycle ops | `rad objective list` |
| 5 | Tasks — 11 explicit statuses, legal transitions, full history | `rad inspect last` |
| 6 | Task graph — sequential+parallel, dependencies, blocked tasks, retries, optional branches | `rad inspect last` |
| 7 | Planner — goal→criteria→decompose→deps→capabilities→graph→budgets→verification reqs; planning separate from execution | `rad objective run` |
| 8 | Replanning — failure → replan; superseded work is recorded, never silently dropped | `rad realworld --only failure` |
| 9 | Executor — one path for side effects: action→policy→permission→budget→tool→observation | `rad lab run --suite bank:recovery --ids recovery_006_fam6` |
| 10 | Observer — structured observation per significant action | `rad realworld --only coding` |
| 11 | Verifier — independent verification layer; model statements never the sole criterion | `rad realworld --only research` |
| 12 | Recovery taxonomy — 10 failure classes, 10 strategies, bounded retries | `rad trace last` |
| 13 | Budgets — token/money/time/tool-call/retry/agent budgets enforced by the control plane | `rad objective run --max-tools 2` |

### State, events, provenance

| # | requirement | reproduce |
|---|---|---|
| 14 | Crash-safe state — checkpoint + lock + restore + safe resume after a crash | `rad realworld --only failure` |
| 15 | Event stream — persistent typed events for the whole lifecycle | `rad events -n 20` |
| 16 | Trace & replay — trace/inspect/replay/events + re-verification of past runs | `rad replay last --verify` |
| 17 | Provenance — CLAIM→EVIDENCE→SOURCE→TOOL→AGENT→TIMESTAMP; 'why do you believe this?' | `rad why <artifact>` |
| 18 | Artifacts — first-class records with hash/version/lineage and rollback | `rad why doubled.txt` |

### Memory & models

| # | requirement | reproduce |
|---|---|---|
| 19 | Memory layers — working/episodic/semantic/procedural | `rad memory` |
| 20 | Memory trust — provenance/confidence/importance/verification/decay on every entry | `rad memory --json` |
| 21 | Contradictions — detected, surfaced and correctable | `rad memory` |
| 22 | Generated ≠ truth — model-generated memories are stored but never auto-verified | `rad recall` |
| 23 | User model — inspectable and correctable | `rad user` |
| 24 | World model — entity/relation graph separating fact/observation/inference/assumption | `rad world show` |

### Agents

| # | requirement | reproduce |
|---|---|---|
| 25 | Agent registry — planner/researcher/coder/tester/reviewer/writer/analyst/security with capabilities | `rad agents list` |
| 26 | Agent runtime — lifecycle/scheduler/bus/memory scope/evaluation | `rad agents runs` |
| 27 | Delegation via the control plane — agent tasks execute under the controller and leave run records | `rad realworld --only multi_agent` |
| 28 | Independent verification — a different agent verifies the work under its own envelope | `rad realworld --only multi_agent` |

### Security & permissions

| # | requirement | reproduce |
|---|---|---|
| 29 | Capability permissions — ALLOW/ASK/DENY/LIMITED per capability on every sensitive action | `rad policy show` |
| 30 | Hard limits — non-overridable refusals (sudo, pipe-to-sh, rm -rf, keys, private hosts) | `rad policy test` |
| 31 | Secret isolation — credentials denied by default, scoped per provider, redacted everywhere | `rad keys list` |
| 32 | Audit log — every permission decision recorded with reason | `rad audit --effect DENY` |
| 33 | Prompt-injection defence — web content is untrusted data; injection is detected, recorded, never obeyed | `rad lab run --suite bank:adversarial` |
| 34 | Sandbox — workspace jail, timeouts, output caps, URL grants, narrower agent caps | `rad lab run --suite bank:adversarial` |

### Routing, evaluation, learning

| # | requirement | reproduce |
|---|---|---|
| 35 | Model selection — requirements→selection→cost/latency/quality→fallback with free-first ordering | `rad providers` |
| 36 | Evaluation battery — reasoning/coding/planning/tools/memory/long-context/structured/research/instruction/safety/recovery coverage | `rad evaluate tasks` |
| 37 | Promotion gate — no promotion on one impressive response; regressions and floors block it | `rad evaluate gate` |
| 38 | Experience learning + evolution — objective→outcome→lesson→procedural memory; staged, gated, rollbackable evolution | `rad evolve list` |

### Operations (background, browser, storage, API)

| # | requirement | reproduce |
|---|---|---|
| 39 | Background runtime — scheduled/file/web/api/event/maintenance triggers run through the control plane | `rad jobs` |
| 40 | Browser actions — action→observe→verify expected state; downloads/uploads/screenshots under capability | `rad browse <url>` |
| 41 | Storage & migrations — structured persistence, migrations, integrity, backup/restore | `rad storage integrity` |
| 42 | Skills & MCP — declarative manifests in the same permission + lifecycle model | `rad skills audit` |
| 43 | Local API — authenticated API for objectives/tasks/agents/memory/world/tools/events/benchmarks/status | `rad serve` |

### Benchmarks

| # | requirement | reproduce |
|---|---|---|
| 44 | Lab banks — ≥100 deterministic tasks for each of the nine categories | `rad benchmark bank --category all --sample 5` |
| 45 | Benchmark results — the banks actually pass, with safety and honesty intact | `rad benchmark bank --sample 90` |
| 46 | Long-horizon benchmark — 20–50 action objectives with the full metric set | `rad benchmark long --sample 6` |
| 47 | Regression system — unit/integration/security/agent/benchmark-subset on every major change | `rad regression` |

### Operability & docs

| # | requirement | reproduce |
|---|---|---|
| 48 | Docs & operability — accurate docs plus install/config/upgrade/backup/restore/crash-recovery/versioning | `docs/README.md` |
| 49 | Operational commands — doctor/install/upgrade/rollback/backup/health all reachable from the CLI | `rad doctor` |
| 50 | The whole loop — understand→criteria→plan→execute→observe→verify→done on a fresh goal | `rad objective run '<goal>'` |

## What the gate is not

* It is not a capability score: `rad benchmark`, `rad lab`, `rad benchmark long` and
  `rad realworld` measure how well RAD performs; the gate proves the *system* is wired
  correctly and does not lie about its own state (false-completion must stay 0).
* It is not a substitute for the test suite: `python -m pytest -q` covers units and edge
  cases (288 tests, offline); the gate covers end-to-end behaviour and re-runs on every change.
* It does not need a model provider or a network: the same run works on a laptop with no keys.
  Provider-dependent items report honestly when no key is present instead of pretending.

