# CLI reference

Every command below exists in this build — this file is generated from the argument parser
and the acceptance gate fails if a command disappears. `rad <cmd> -h` shows the full flags.

Global: `--home <dir>` (or `RAD_HOME`), `--quiet`, `--json` where noted.

## Everyday

| command | what it does |
|---|---|
| `rad chat` | talk to Rad (default) |
| `rad say` | speak text (TTS) |
| `rad listen` | record + transcribe mic |
| `rad see` | vision: look at an image |
| `rad search` | search the public web |
| `rad browse` | scrape a public page |
| `rad watch` | watch a public page for changes |
| `rad remind` | rad remind <in 5m / 2h / tomorrow 9am / 14:30> <task> |
| `rad drive` | Google Drive cloud mind |
| `rad status` | one screen: objectives, memory, brain, jobs, background, schema |
| `rad version` | version |

## Brains & providers

| command | what it does |
|---|---|
| `rad providers` | show detected providers + chain |
| `rad keys` | API key vault |
| `rad use` | pin a provider |
| `rad provider` | custom providers (open door) |
| `rad models` | local engine models |
| `rad cost` | paid spend so far |
| `rad install` | install optional parts |

## Autonomy (control plane)

| command | what it does |
|---|---|
| `rad objective` | autonomous objectives: plan → execute → verify → recover |
| `rad inspect` | objective + task graph + verification (default: last) |
| `rad trace` | event trail of an objective (default: last) |
| `rad events` | recent control-plane events across objectives |
| `rad replay` | replay an objective: prompts, tool calls, results; --verify re-checks now |
| `rad why` | provenance: rad why <claim / artifact path> |
| `rad plan` | goal planning: decompose, track, drive, RUN |
| `rad agents` | scoped sub-agents: registry, capabilities, runs, blackboard |
| `rad team` | multi-agent cognition — specialists + synthesis |
| `rad jobs` | list/cancel jobs |

## Memory & world

| command | what it does |
|---|---|
| `rad memory` | memory layers |
| `rad remember` | pin a fact to long-term memory |
| `rad recall` | search long-term memory |
| `rad sleep` | consolidate memory now |
| `rad user` | the user model — what Rad believes about you (inspect / correct) |
| `rad world` | world model — Rad's picture of your world |
| `rad dna` | Rad's identity |
| `rad corpus` | experience → training data |

## Security

| command | what it does |
|---|---|
| `rad policy` | capability permissions: show/allow/ask/deny/limit/default/test |
| `rad audit` | permission decisions log |
| `rad security` | enforcement layers, capability defaults, hard limits, audit |
| `rad tools` | tools RAD can call + the capability each one needs |
| `rad skills` | connected skills: list / audit / approve <name> [allow/ask/deny] / declare / manifest |
| `rad connect` | self-build + connect any MCP skill from a link |
| `rad drop` | disconnect a skill |

## Evaluation & evolution

| command | what it does |
|---|---|
| `rad lab` | agent benchmark lab: whole objectives through the control plane, graded on disk |
| `rad benchmark` | capability battery — is Rad smarter? now it's a number |
| `rad evaluate` | model evaluation battery: planning/memory/long-context/research/instruction/safety/recovery + history + promotion gate |
| `rad regression` | unit/integration/security/agent tests + live agent and long-horizon benchmark subset, with a pass/fail verdict |
| `rad realworld` | end-to-end acceptance tests: research, coding, multi-agent, failure recovery |
| `rad acceptance` | the 50-item acceptance gate: every requirement demonstrated by running code, with per-item evidence |
| `rad evolve` | gated evolution: rad evolve <direction> / list / approve/reject/rollback <id> / verify / from-lab |
| `rad brain` | brain candidates + promotion protocol (verified evolution) |
| `rad train` | weight evolution: corpus → trainer backends |

## Operations

| command | what it does |
|---|---|
| `rad doctor` | health check of RAD; --fix repairs what is safe |
| `rad storage` | schema/migrations/integrity/snapshots of ~/.rad |
| `rad config` | show/get/set/unset RAD configuration |
| `rad workspace` | show/set the hands workspace |
| `rad serve` | local JSON API over the control plane (loopback, bearer token) |

## Command groups

Several commands take a sub-action as their first argument:

| command | sub-actions |
|---|---|
| `rad agents` | list, define, remove, run, runs, caps, board |
| `rad benchmark` | run, bank, long, history, compare |
| `rad brain` | add, list, current, promote, rollback |
| `rad config` | show, get, set, unset, path |
| `rad corpus` | show, export |
| `rad dna` | show, rollback, reset |
| `rad drive` | connect, push, pull |
| `rad evaluate` | run, history, gate, tasks |
| `rad keys` | add, rm, list |
| `rad lab` | list, run, history, show, compare |
| `rad memory` | show, prune, conflicts, forget, verify, dispute, correct |
| `rad objective` | run, create, list, inspect, resume, pause, cancel, delete |
| `rad plan` | status, done, clear, run |
| `rad policy` | show, allow, ask, deny, limit, default, rm, web-allow, reset, test |
| `rad provider` | add |
| `rad regression` | run, history, show, compare |
| `rad skills` | list, audit, approve, declare, manifest |
| `rad storage` | status, migrate, check, snapshot, snapshots, restore |
| `rad team` | run, roles, history |
| `rad user` | show, set, add, forget, reset |
| `rad world` | show, query, add, learn, sync, cypher, retract, confirm, disputes |

## Exit codes

* `0` success (including `rad doctor` when nothing is ERROR — OPTIONAL capabilities do not fail)
* `1` usage/validation error or `rad doctor` ERROR, `2` a check failed (`rad regression`, `rad realworld`,
  `rad acceptance`, `rad evaluate gate`) — usable directly in CI.

