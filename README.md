# Rad Agent

> **Rad is the door, not the room.** Brain, engine, tools, memory, voice, face — all swappable at runtime.

Rad is an open, **self-evolving, free-first** personal AI agent that lives in your terminal.
It auto-detects the AI providers available on your machine, routes to the best **free** brain first,
falls back automatically, remembers like a human, talks, sees, browses the public web,
runs commands with your confirmation, and **teaches itself new skills from a single link**.

```
      _    ____  _        _
  __ / \  |  _ \/ |      / \
 / _` __ \| |_) | | /\/\ / _ \
 \__,_||_|____/|_|/__/__\_/ \_\
   v0.5.0 — open door, free first, self-evolving
```

---

## The six sockets (Open Door architecture)

| Socket | What plugs in | Default |
|---|---|---|
| 🧠 **Brain** | Any LLM — every OpenAI-compatible endpoint, Anthropic, Gemini | auto-detected keys |
| ⚙️ **Engine** | Any local runtime — **Edge0** (MLX), Ollama, LM Studio, vLLM | best available |
| 🧩 **Tools** | Any MCP server + custom skills, even ones Rad writes itself | hands + `rad connect` |
| 🧬 **Memory** | Portable markdown/JSON — local disk, Google Drive, … | disk + Drive |
| 🗣️ **Voice** | Any TTS/STT engine | Piper + Whisper (free, offline) |
| 👤 **Face** | CLI now; web/phone later — same brain, different door | terminal |

Nothing is a closed list. `rad provider add` accepts **any** OpenAI-compatible endpoint and it
behaves like a first-class provider.

## Built-in brain: Edge0

Rad's never-fails fallback is [Edge0](https://github.com/Edge0-AI/Edge0) — a 35B/10B MoE that
streams from your SSD on Apple Silicon. 0 cost, offline, no key.

```bash
rad install edge0        # Mac only — clones + guides setup
# Rad auto-detects it at 127.0.0.1:8000 (config: edge0_url / edge0_tier)
```

On other machines the engine socket takes Ollama / LM Studio / vLLM instead — same interface.

**NVIDIA NIM** (build.nvidia.com) is a first-class free-tier brain:
`rad keys add nvidia <nvapi-…>` — default model `meta/llama-3.2-11b-vision-instruct`
(NIM free-credit; `meta/llama-3.3-70b-instruct` reached end-of-life on 2026-08-26).

## Routing (free-first, auto-fallback)

```
local engines → free cloud tiers (round-robin) → paid (unless free-lock)
  Edge0 → Ollama → Groq free → Cerebras free → Gemini free → OpenRouter free
      → NVIDIA NIM free-credit → OpenAI / Claude / Mistral / Grok / …
```

* Keys are **auto-fetched**: Rad vault → environment → `.env` (project & home).
* Any provider failing (rate limit, quota, network) → Rad **auto-falls-back** and tells you.
* Free tiers **rotate** so one rate limit never walls you off.
* `rad use <provider>` pins one; **free-lock mode** makes paid spend impossible;
  `rad cost` shows exactly what any paid fallback cost.
* Everything is reported: `rad [groq] …`
* Optional experimental tool router: `RAD_TOOL_ROUTER=needle` lets [Needle](https://github.com/cactus-compute/needle)
  *propose* tool names/args. Default remains `existing`. Needle never executes tools, never
  bypasses permission/sandbox/budget/verification, and stays **off** in v0.5.0
  (`RAD_TOOL_ROUTER=existing`). `rad needle-eval` is the measurement path; it is not a default.

## Human-inspired memory

> v0.2: every memory carries origin (user / observed / inferred / model-generated), confidence and
> verification state; contradictions are linked not merged; a structured **user model** (`rad user`) and a
> **temporal world model** (`rad world`) sit beside raw memories. Details: `docs/MEMORY.md`.

```
sensory (RAM, this turn) → working (RAM, this task)
→ short-term (disk, days, decays)
→ long-term:  episodic (events) · semantic (facts) · procedural (skills)
```

* Every long-term memory has a **strength**: used = stronger, unused = fades → **archived** (never deleted).
* **`rad sleep`** (and auto-sleep) consolidates short-term → long-term, prunes, and syncs to Drive.
* Relevant memories are **auto-recalled** into context each turn; `rad recall` / `rad remember` for manual.

## Evolution 2.0 — verified weight/model evolution

The DNA loop evolves *who Rad is*. This loop evolves *how smart the brain is* —
with the law that **nothing goes live without winning a benchmark battle**.

```
rad corpus                    # mine sessions + 👍/👎/corrections → training pairs (JSONL)
rad corpus export             # the raw material for any trainer
rad train --plan              # backends here (MLX-LM/Unsloth/PEFT) + Route B:
                              # train anywhere (your Mac / rented GPU), bring the adapter back
rad brain add trained-1 --provider edge0 --model <m> --adapter ./rad-adapter/adapter.pt
rad brain promote trained-1   # A/B benchmark battle vs current brain — promote only if it WINS
rad brain list | current | rollback
rad benchmark                 # the Capability Battery: math·logic·code·tool·json·summarize·style
                              # → 0-100, per-category, saved history + trend (▲/▼)
rad plan <goal>               # goal decomposition (LLM-backed, deterministic fallback)
rad plan status | done <n> | clear
```

**The promotion protocol** (the safety core of self-improvement):
1. Candidate = provider+model, tuned settings, or a staged **weight adapter**
2. Both candidate and current brain run the identical Capability Battery
3. Candidate promoted only if `score ≥ current + margin` — then it's pinned as the live brain
4. Every promotion is a **generation** with parent pointer — `rad brain rollback` always

The battery is built-in, deterministic, and dependency-free — it scores *any* brain through
the provider socket (local engine, free tier, paid, or a trained adapter). It is also a plug
socket: a heavier external harness (lm-evaluation-harness, etc.) can be added later without
touching the promotion loop.

## Evolution 3.0 — parallel minds, a world model, hands that act

Evolution 2.0 gave Rad a *smarter* brain. Evolution 3.0 gives it **teammates**, a
**picture of the world**, and the ability to **run its own plans** with its hands.

```
rad team run "pick a db for my api" [--mode solo|debate] [--roles a,b] [--n 3]
    A team of specialists (coder·reviewer·planner·researcher·writer — each an
    instance of the SAME brain with a role grown from the DNA) tackles the problem,
    then a writer synthesizes one final answer.  --mode debate adds a reviewer
    cross-critique round.  --backend autogen runs a real AutoGen agent graph when
    autogen-agentchat is installed; builtin is always available.
rad team roles | history

rad world show | query <term> | add <sentence> | learn [--path file]
    The world model: an entity/relation graph ("X works at Y", "Z is my server",
    "A depends on B") mined from chat, memory and manual facts.  Extraction is
    brain-assisted when online, heuristic when offline.  Relevant facts are
    auto-injected into context when the topic comes up — prediction, not recall.
rad world sync | cypher <query>
    Mirrors the graph into an embedded Kuzu graph DB (the engine Graphiti runs on) —
    query it in Cypher, serverless, no key needed.

rad plan run [--auto] [--max N]
    Rad EXECUTES the current plan with its hands — full brain loop + tools,
    confirm-gated unless --auto.  Each step ends in DONE: <note> or BLOCKED: <why>;
    a BLOCKED step stops execution and hands control back to a human.
```

Mid-chat, the brain can also **delegate**: the `spawn_agents` tool lets Rad itself
convene a team when a problem benefits from multiple perspectives.

The OSS consumed here (behind Rad's sockets, so they stay swappable):
* **AutoGen** (`autogen-agentchat`) — real multi-agent orchestration backend.
* **Graphiti / Kuzu** — the knowledge-graph layer; Rad drives Kuzu (embedded) directly
  and its extraction is brain-backed, so no separate LLM server is required.

## The Evolver (who Rad is)

DNA (identity: persona, style, lessons) is separate from memory (knowledge).

* **Auto**: every session distills lessons into the DNA.
* **Directed**: `rad evolve reply shorter and more casual` rewrites the self (LLM-backed, or
  deterministic when offline).
* Every change is a **generation**: `rad dna show | rollback | reset`.
* Safety law: the evolver only rewrites behavior files — **never code**.

## Hands, eyes, internet, voice

* **Hands** — shell + file tools. Confirm-first by default (`y` per command), `rad --auto` for
  autonomy, and a **hard blocklist** (sudo, `rm -rf /`, pipes to sh, …) that even auto mode can't cross.
* **Eyes** — `rad see <image> [question]` routes through the best available vision brain.
* **Internet** — `rad browse <url>` (any public page), `rad search <query>` (keyless DuckDuckGo
  scraping). Mid-chat, Rad fetches on its own when it needs fresh info. Scraped content is always
  wrapped as **UNTRUSTED data** — prompt-injection defense.
* **Voice** — `rad chat --voice`: speak + listen. Local Piper TTS + Whisper STT (free, offline);
  provider TTS/STT when keys exist. `rad say`, `rad listen` standalone.

## Skills: connect ANY MCP server from one link

```bash
rad connect https://github.com/someone/mcp-foo      # repo → clone + detect + install
rad connect @modelcontextprotocol/server-filesystem # npm → npx
rad connect ./my-local-skill                        # local folder
rad connect some-pypi-mcp-package                   # PyPI
rad connect docker.io/ghcr.io/some/mcp-server:1     # docker
rad connect https://remote.example.com/mcp          # remote MCP endpoint
rad skills          # what's connected + its tools
rad drop <name>     # disconnect
```

Rad detects the server type, installs what's missing (venvs for Python, npx for JS, docker build),
performs the MCP handshake, and **asks you to approve the tool list** before anything runs.
Connected tools appear to the brain as first-class tools (`mcp__foo__bar`) with the same confirm gate.

## Cloud mind: Google Drive (5 TB)

Drive is the **mind in the cloud** — not the inference disk (Drive's latency can't do expert
streaming). It holds long-term memory, DNA generations, model bundles, and the faded archive.
One Rad on many machines: pull the mind, boot, work, sync back on sleep.

```bash
rad install cloud
rad drive connect --client-id <id> --client-secret <secret>
rad drive push | pull | status
```

## Scheduler

```bash
rad remind in 5m "take out the trash"
rad remind tomorrow 9am "standup notes"
rad watch https://example.com/changelog --every 30
rad jobs | rad jobs cancel <id>
```

Watchers are detached processes; notifications land in `~/.rad/notifications.md`.

## Install

Requires Python 3.9+ (3.11 or 3.12 recommended). No mandatory dependencies (stdlib-only core).

```bash
git clone https://github.com/seven0070/rad-agent- && cd rad-agent-
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# optional layers:
pip install -e ".[vault]"    # Fernet-encrypted key vault
pip install -e ".[cloud]"    # Google Drive cloud mind
pip install -e ".[voice]"    # faster-whisper + sounddevice + piper
pip install -e ".[agi]"      # multi-agent backends (AutoGen) + world graph (Kuzu)
rad install edge0            # Mac: the built-in MoE brain
rad install voice|cloud|vault|dev   # same, via rad
```

First run:

```bash
rad                          # just talk
rad keys add groq gsk_…      # or: export GROQ_API_KEY=…  (auto-detected)
rad chat --voice             # talk to it out loud
```

## Objectives — the control plane (v0.3)

`rad objective run <goal>` is the autonomous path. Unlike chat or `rad plan run`, RAD
itself owns the state; the model only proposes.

```
Objective → Planner → Task graph (DAG, machine-checkable checks per task)
         → Executor (the normal brain loop, every tool call observed + budgeted)
         → Verifier (files / shell / regex — never the model's own word)
         → Recovery (retry with feedback · repair step · replan · ask user · abort)
         → Objective verification → COMPLETED | NEEDS_USER | FAILED
```

Coding/verification goals drive **write → independent disk checks → repair** until
`json_valid` / tests pass (or the budget forces `needs_user` / fail honestly). A model
`DONE:` line is never completion. A planner timeout / empty / malformed JSON is retried
once for a structured JSON plan before the F-17 goal-only fallback. A fat plan that
would burn more than the remaining tool budget is retried; the cheaper graph that
fits is selected (fallback graphs that are still fat are compacted). Needle stays off.
Default `max_plan_tasks` remains 16; default `Budget.tool_calls` remains 60.

```
rad objective run "Write three facts about X to facts.md, then summarise into summary.txt" \
    --criteria "facts.md has 3 facts" --criteria "summary.txt exists" --auto
rad objective list | inspect [id] | resume [id] | pause | cancel
rad trace [id] [--kind TOOL_RESULT] [--json]     # full event trail
rad replay [id] --verify                          # prompts → tools → results; re-check the world now
rad why report.md | rad why "<claim>"             # provenance: creator, lineage, evidence (or none)
rad events                                        # recent events across objectives
```

What you get that the chat loop cannot give you:

* A model that says "DONE: wrote report.md" without writing it is **caught**, told exactly which
  check failed, and retried. After bounded retries it replans; after that it asks you.
* Tasks with no plannable checks complete as `UNVERIFIED`, and the final report says so.
* Crash or Ctrl-C mid-run → `rad objective resume` continues from the checkpoint; completed
  tasks are not re-run.
* Budgets (tool calls, model calls, retries, time) stop runaway loops.
* Every file written or produced by a shell command is a versioned artifact with a sha256.

State lives in `~/.rad/objectives/<id>/` (objective.json, tasks.json, events.jsonl,
observations/, artifacts.json) — plain files, like everything else.

## Every command

```
rad                          # chat (default)
rad objective run <goal>     # autonomous: plan → execute → verify → recover (see above)
rad objective list|inspect|resume|pause|cancel
rad trace [id] · rad inspect [id] · rad replay [id] --verify · rad why <x> · rad events
rad chat --voice --auto --use <p> --free-lock --model <m> --workspace <dir>

rad keys add <provider> <key> | list | rm <provider>
rad providers                # detected brains + chain
rad use <provider>           # pin
rad cost                     # paid spend

rad see <image> [question]   # vision
rad browse <url>             # scrape public page
rad search <query>           # keyless web search

rad remember <text> [--layer episodic|semantic|procedural]
rad recall <query>
rad memory show | prune
rad sleep                    # consolidate memory (+ drive sync)

rad evolve <direction>       # directed self-evolution
rad dna show | rollback | reset

rad connect <link> [--yes]   # self-build + connect any MCP skill
rad skills | rad drop <name>

rad drive connect|push|pull|status
rad remind <in 5m|2h|tomorrow 9am|14:30> <task>
rad watch <url> [--every N]
rad jobs | rad jobs cancel <id>

rad say <text> | rad listen [--seconds N]
rad models                   # local engine models

rad corpus show | export [--out file]     # experience → training data
rad benchmark [--provider P] [--model M] [--cats …]   # capability battery, 0-100
rad brain add|list|current|promote|rollback           # verified-evolution protocol
rad train [--plan] [--run --model M --out D]          # weight training backends
rad plan <goal> | status | done <n> | run [--auto] | clear   # plan + self-execution
rad team run <problem> [--mode solo|debate] [--roles …] [--backend builtin|autogen]
rad team roles | history                              # multi-agent specialists
rad world show|query|add|learn|sync|cypher            # world model (entity/relation graph)
rad provider add <name> <url> [--key K] [--tier local|free|paid] [--model M]
rad workspace [path]
rad install vault|cloud|voice|dev|edge0
rad version
```

Inside chat: `/help /good /bad /remember /recall /evolve /use /free /auto /cost /sleep /dna /skills /exit`

## Security model

* **Key vault**: Fernet-encrypted (`pip install cryptography`); falls back to 0600 files with a loud warning.
* **UNTRUSTED data**: all scraped web content is marked as data, never instructions.
* **Permission gate**: writes, shell, and MCP tools confirm first; `--auto` skips confirmation but
  the hard blocklist (sudo, destructive rm, pipes-to-shell, dd, …) still blocks.
* **Supply chain**: every MCP skill must pass a handshake **and** your tool-list approval.
* **Free-lock + cost**: paid spend is optional, visible, and can be made impossible.
* **Privacy**: memory/DNA are local files you own; Drive sync is opt-in and private-folder only.

## State (all human-readable, all yours)

```
~/.rad/
├── rad.json            # config
├── keys/vault.enc      # encrypted key vault
├── memory/{short,long/{episodic,semantic,procedural},archive}/
├── dna/gen*.json       # identity generations + current
├── skills/registry.json
├── cost.json · jobs.json · notifications.md
└── logs/ · downloads/ · models/
```

## Windows

Rad runs on Windows (10/11) out of the box — `python -m venv .venv`, `pip install -e .`, done.

* **Local engine**: `winget install Ollama.Ollama` — Ollama on Windows uses your **NVIDIA GPU**
  automatically. `ollama pull llama3.2:3b` and Rad picks it up at boot. LM Studio works too.
  (Edge0 itself stays Mac/MLX-only; on Windows your built-in brain is Ollama or a free cloud tier.)
* **Free brains without a local GPU**: NVIDIA NIM (`rad keys add nvidia …`), Groq, Cerebras,
  Gemini, OpenRouter — all key-in, auto-routed.
* **Voice**: `rad install voice` gives faster-whisper + sounddevice; TTS needs Piper
  (Linux) — on Windows provider TTS (OpenAI key) or text-only mode.
* **MCP skills**: Python skills get a per-skill venv (`~/.rad/venvs/…/Scripts/`), npm skills use
  `npx`, everything else falls through the same detection as on any OS.

## Development

```bash
pip install -e ".[dev]"
python -m pytest -q         # offline tests
rad regression --quick      # security + agent groups + a live benchmark sample
rad acceptance              # the 50-item acceptance gate, with per-item evidence
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the layout, the rules the codebase follows
(the model proposes / the executor decides; verification is independent; failures are observations)
and how to add a tool, a scenario or a migration.

## Roadmap

Operating spine (Gen1–Gen5, the build → test → validate → release → use → discover gaps loop): [docs/ROADMAP.md](docs/ROADMAP.md). Gen1 complete on 0.2.3; Gen2 complete on 0.3.0–0.3.2; Gen3 **complete (scripted)** on 0.4.0–0.4.9; Gen4 **in progress** — **G4-1** live multi-provider / free-provider production doctrine **implemented as v0.5.0** (scripted RW-089: 403/429 → Class C `needs_user`; free-first rotation; no silent paid under `free_lock`; no Class A invented). Live E1–E3 confirmation **deferred**; live text_analyzer@12 **not** claimed PASS; NIM Class C paused (RW-084); OpenRouter free paused (RW-086 429). Needle **OFF**. Caps **16/60**. The list below is a product-idea backlog, not a generation commitment.

LoRA fine-tune of Rad's personality into Edge0 weights · expert pruning/distillation for lighter
35b · web/phone face · remote-MCP tool execution hardening · multi-user sessions ·
full Graphiti temporal pipeline (LLM extraction over episodes) when a graph server is present ·
SWE-bench / AgentBench bootstrap data wired to the corpus miner.

## License

See [LICENSE](LICENSE).

## Measuring the agent
900 graded scenarios (9 categories × 100) plus long-horizon, model-evaluation, regression and
real-world tests (research, coding, filesystem, multi-step, failure, honesty, optional live NIM) —
all graded on disk state, never on what a model claims. `rad lab run --suite bank --sample 20`,
`rad benchmark long --sample 6`, `rad realworld`, `rad needle-eval`, `rad regression`, `rad acceptance`.
Success, honesty (no over-claiming), safety (no canary touched), verified-rate, recovery rate,
retries, cost and false-completion rate are all reported.
See [docs/BENCHMARKS.md](docs/BENCHMARKS.md) and [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).

## Autonomy: the control plane (v2)

`rad objective run "<goal>"` is the whole loop, and every part of it is inspectable:

```
understand → success criteria → plan → task graph → execute → observe → verify → done
      ▲                                                              │
      └──────────── diagnose → recover → replan  ◄──── fail ──────────┘
```

* **Objectives own the work.** id, goal, success criteria, constraints, priority, deadline, budget,
  status, timestamps and the plan generation (`plan_version`). `rad objective list|run|pause|resume|
  cancel|retry|expire|verify`.
* **Tasks never vanish.** 11 explicit statuses with legal transitions and full history; every task
  belongs to an objective; a superseded task is recorded as CANCELLED, never deleted.
* **The executor is the only way to act.** capability → sandbox → permission → budget → tool →
  observation → events; the model (or a sub-agent, or a plugin) cannot bypass it.
* **Verification is independent.** `rad/control/verifier.py` checks files, JSON fields and shell
  commands; a model's sentence is never the completion criterion. Advisors (`agent_review`,
  `llm_judge`) are advisory only.
* **Recovery is a taxonomy, not a hope.** 10 failure classes → 10 strategies (retry, switch tool,
  switch model, rollback, repair, replan, spawn specialist, ask) with bounded attempts and budgets;
  checkpoints survive crashes, restarts and provider failures (`rad realworld --only failure`).
* **Everything is answerable.** `rad trace | inspect | replay | events`, artifacts with hashes,
  versions, lineage and rollback, and `rad why <claim|file>` for CLAIM→EVIDENCE→SOURCE→TOOL→AGENT→TIME.
* **Budgets and events are enforced** (token/money/time/tool-call/retry/agent) and persisted as a
  typed stream per objective; `rad replay <id> --verify` re-checks a past run against today's disk.

## Documentation map
[QUICKSTART](docs/QUICKSTART.md) · [INSTALLATION](docs/INSTALLATION.md) · [CONFIGURATION](docs/CONFIGURATION.md) · [CLI](docs/CLI.md) ·
[ARCHITECTURE](docs/ARCHITECTURE.md) · [CONTROL-PLANE](docs/CONTROL-PLANE.md) · [MEMORY](docs/MEMORY.md) ·
[WORLD-MODEL](docs/WORLD-MODEL.md) · [AGENTS](docs/AGENTS.md) · [SECURITY](docs/SECURITY.md) ·
[TOOLS](docs/TOOLS.md) · [SKILLS](docs/SKILLS.md) · [MCP](docs/MCP.md) · [LAB](docs/LAB.md) ·
[BENCHMARKS](docs/BENCHMARKS.md) · [EVOLUTION](docs/EVOLUTION.md) · [API](docs/API.md) ·
[OPERATIONS](docs/OPERATIONS.md) · [TROUBLESHOOTING](docs/TROUBLESHOOTING.md) ·
[MIGRATION](docs/MIGRATION.md) · [DEVELOPMENT](docs/DEVELOPMENT.md) · [ACCEPTANCE](docs/ACCEPTANCE.md) ·
[ROADMAP](docs/ROADMAP.md) · [AUDIT-2026-09](docs/AUDIT-2026-09.md) · [ADR-001 Needle tool-router](docs/ADR-001-NEEDLE-TOOL-ROUTER.md).

Every document describes shipped behaviour: `docs/CLI.md` is generated from the argument parser and
the acceptance gate fails if the docs mention a command that does not exist.

Quick health check: `rad doctor` · first run: [quickstart](docs/QUICKSTART.md) · local API: `rad serve` · is it finished? `rad acceptance`.
