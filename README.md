<p align="center">
  <img src="IMG_8021.ico" width="96" alt="RAD Agent" />
</p>

<h1 align="center">RAD Agent</h1>

<p align="center">
  <strong>Open · Self-Evolving · Free-First · Personal AI Agent</strong><br/>
  <sub>v1.0.1 — MIT License</sub>
</p>

<p align="center">
  <a href="https://github.com/seven0070/rad-agent-/releases"><img alt="Release" src="https://img.shields.io/github/v/release/seven0070/rad-agent-?style=flat-square&color=6366f1" /></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-10b981?style=flat-square" /></a>
  <a href="#install"><img alt="Python" src="https://img.shields.io/badge/python-3.9%2B-f59e0b?style=flat-square" /></a>
</p>

---

RAD is an open, **self-evolving, free-first** personal AI agent that lives in your terminal — and now has a desktop app. It auto-detects the AI providers on your machine, routes to the best **free** brain first, falls back automatically, remembers like a human, talks, sees, browses the web, runs commands with your confirmation, and **teaches itself new skills from a single link**.

> **RAD is the door, not the room.** Brain, engine, tools, memory, voice, face — all swappable at runtime.

---

## ✨ Highlights

- 🧠 **Any LLM** — OpenAI, Anthropic, Gemini, Groq, Cerebras, Mistral, Grok, NVIDIA NIM, or local (Ollama / LM Studio / Edge0)
- 💸 **Free-first routing** — local engines → free cloud tiers (round-robin) → paid (optional)
- 🧬 **Human-inspired memory** — sensory → working → short-term → long-term (episodic · semantic · procedural)
- 🎯 **Autonomous objectives** — plan → execute → verify → recover, with checkpoints and budgets
- 🧩 **MCP skill system** — connect any MCP server from a URL, repo, npm package, or Docker image
- 🔬 **Self-evolution** — DNA identity system + verified weight/model evolution with benchmark battles
- 🖥️ **Desktop app** — Tauri-based 3-panel interface with bundled backend sidecar
- 🗣️ **Voice** — speak + listen with local Piper TTS + Whisper STT (free, offline)
- 👁️ **Vision** — image understanding via the best available vision model
- 🌐 **Web** — browse pages + keyless DuckDuckGo search with prompt-injection defense
- ☁️ **Cloud mind** — Google Drive sync for cross-machine memory continuity
- 🔒 **Security** — encrypted vault, permission gates, hard blocklist, untrusted-data marking

---

## 🏗️ Architecture — The Six Sockets

RAD is built on an **Open Door** architecture — every capability is a swappable socket:

| Socket | What plugs in | Default |
|---|---|---|
| 🧠 **Brain** | Any LLM — OpenAI-compatible, Anthropic, Gemini | Auto-detected keys |
| ⚙️ **Engine** | Local runtime — Edge0 (MLX), Ollama, LM Studio, vLLM | Best available |
| 🧩 **Tools** | Any MCP server + custom skills | Built-in + `rad connect` |
| 🧬 **Memory** | Portable markdown/JSON — local disk, Google Drive | Disk + Drive |
| 🗣️ **Voice** | Any TTS/STT engine | Piper + Whisper (free, offline) |
| 👤 **Face** | CLI or RAD Desktop (Tauri + bundled sidecar) | Terminal + Desktop |

---

## 📦 Install

**Requires:** Python 3.9+ (3.11 or 3.12 recommended). Zero mandatory dependencies (stdlib-only core).

### From Release

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install https://github.com/seven0070/rad-agent-/releases/download/v1.0.0/rad_agent-1.0.0-py3-none-any.whl
rad version
```

### From Source

```bash
git clone https://github.com/seven0070/rad-agent- && cd rad-agent-
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

### Optional Layers

```bash
pip install -e ".[vault]"     # Fernet-encrypted key vault
pip install -e ".[cloud]"     # Google Drive cloud mind
pip install -e ".[voice]"     # faster-whisper + sounddevice + piper
pip install -e ".[agi]"       # Multi-agent (AutoGen) + world graph (Kuzu)
pip install -e ".[dev]"       # pytest
```

### First Run

```bash
rad                           # just talk
rad keys add groq gsk_…       # or: export GROQ_API_KEY=… (auto-detected)
rad chat --voice              # talk to it out loud
```

---

## 🔀 Routing — Free-First, Auto-Fallback

```
local engines → free cloud tiers (round-robin) → paid (unless free-lock)

Edge0 → Ollama → Groq → Cerebras → Gemini → OpenRouter
     → NVIDIA NIM → OpenAI / Claude / Mistral / Grok / …
```

- Keys auto-fetched from vault → environment → `.env`
- Provider failures → automatic fallback with notification
- Free tiers rotate so one rate limit never walls you off
- `rad use <provider>` pins one · `rad cost` shows spend · free-lock makes paid impossible

---

## 🧬 Memory

```
sensory (RAM, this turn) → working (RAM, this task)
  → short-term (disk, days, decays)
  → long-term:  episodic (events) · semantic (facts) · procedural (skills)
```

- Every memory has a **strength** — used = stronger, unused = fades → archived (never deleted)
- **`rad sleep`** consolidates short-term → long-term, prunes, and syncs to Drive
- Memories carry origin, confidence, and verification state
- Auto-recalled into context each turn · `rad recall` / `rad remember` for manual

---

## 🎯 Autonomous Objectives

`rad objective run <goal>` is the autonomous control plane:

```
Objective → Planner → Task Graph (DAG)
         → Executor (brain loop, every tool call observed + budgeted)
         → Verifier (files / shell / regex — never the model's own word)
         → Recovery (retry · repair · replan · ask user · abort)
         → COMPLETED | NEEDS_USER | FAILED
```

```bash
rad objective run "Write facts to facts.md, summarise into summary.txt" \
    --criteria "facts.md has 3 facts" --criteria "summary.txt exists" --auto

rad objective list | inspect [id] | resume [id] | pause | cancel
rad trace [id]          # full event trail
rad replay [id] --verify  # re-check a past run against today's disk
rad why report.md       # provenance: creator → evidence → source → tool → agent → time
```

**What you get:**
- A model that says "DONE" without actually writing a file is **caught** and retried
- Crash or Ctrl-C mid-run → `rad objective resume` continues from checkpoint
- Budgets (tool calls, model calls, retries, time) stop runaway loops
- Every file produced is a versioned artifact with SHA-256

---

## 🧩 Skills — Connect Any MCP Server

```bash
rad connect https://github.com/someone/mcp-foo        # repo → clone + detect + install
rad connect @modelcontextprotocol/server-filesystem    # npm → npx
rad connect ./my-local-skill                           # local folder
rad connect some-pypi-mcp-package                      # PyPI
rad connect docker.io/ghcr.io/some/mcp-server:1        # Docker
rad connect https://remote.example.com/mcp             # remote endpoint

rad skills              # list connected tools
rad drop <name>         # disconnect
```

RAD detects the server type, installs dependencies, performs the MCP handshake, and asks you to **approve the tool list** before anything runs.

---

## 🧪 Self-Evolution

### DNA (Identity)

DNA (persona, style, lessons) is separate from memory (knowledge).

- **Auto:** every session distills lessons into the DNA
- **Directed:** `rad evolve reply shorter and more casual`
- Every change is a **generation** with rollback: `rad dna show | rollback | reset`
- The evolver only rewrites behavior files — **never code**

### Verified Model Evolution

```bash
rad corpus                       # mine sessions → training pairs (JSONL)
rad train --plan                 # configure training backend
rad brain add trained-1 …       # register candidate
rad brain promote trained-1     # A/B benchmark battle — promote only if it WINS
rad benchmark                   # Capability Battery: math · logic · code · tool · json · summarize
```

---

## 🤝 Multi-Agent Teams

```bash
rad team run "pick a db for my api" --mode debate --roles coder,reviewer,planner
rad world show | query <term>    # entity/relation knowledge graph
rad world sync | cypher <query>  # embedded Kuzu graph DB
```

---

## 🖥️ RAD Desktop

<p align="center">
  <img src="https://raw.githubusercontent.com/seven0070/rad-agent-/main/desktop/screenshot.png" width="800" alt="RAD Desktop" />
</p>

A **3-panel desktop interface** built with React + TypeScript + Tauri, following the Hermes Agent Desktop design system (rebranded to RAD):

| Panel | Purpose |
|---|---|
| **Left Sidebar** | Brand mark, `+ New Objective`, 9 navigation views, session history |
| **Center Panel** | Chat-first agent surface — objectives, thinking, tool cards, artifact cards, verification banners, composer with slash commands |
| **Right Inspector** | 5-tab drawer (Files · Code · Verif · Checkpoints · Stats) with artifact preview + SHA-256 |
| **Bottom Bar** | Connection status, authority profile, model, budgets, focused objective |

The desktop bundles the Python core as a `rad-backend` sidecar (loopback-only, Bearer token) — **no Python, no Node, no `rad serve` required** for end users.

```bash
cd desktop && npm install && npm run dev     # development
npm run build                                 # production build
```

Installers: [.github/workflows/desktop.yml](.github/workflows/desktop.yml) · Details: [docs/DESKTOP.md](docs/DESKTOP.md)

---

## 🛡️ Security

| Layer | How |
|---|---|
| **Key vault** | Fernet-encrypted (`pip install cryptography`); fallback to `0600` files |
| **Untrusted data** | All scraped web content marked as data, never instructions |
| **Permission gate** | Writes, shell, MCP tools confirm first; `--auto` skips but hard blocklist remains |
| **Hard blocklist** | `sudo`, `rm -rf /`, pipes-to-shell, `dd`, … — even auto mode can't cross |
| **Supply chain** | Every MCP skill requires handshake + your tool-list approval |
| **Privacy** | All state is local files you own; Drive sync is opt-in |

---

## 📂 State — All Human-Readable, All Yours

```
~/.rad/
├── rad.json                       # config
├── api.token                      # sidecar auth token
├── keys/vault.enc                 # encrypted key vault
├── memory/
│   ├── short/                     # short-term (decays)
│   └── long/
│       ├── episodic/              # events
│       ├── semantic/              # facts
│       └── procedural/            # skills
├── dna/gen*.json                  # identity generations
├── objectives/<id>/               # objective state
│   ├── objective.json
│   ├── tasks.json
│   ├── events.jsonl
│   ├── observations/
│   └── artifacts.json
├── skills/registry.json
├── cost.json · jobs.json
└── logs/ · downloads/ · models/
```

---

## 🖥️ Windows

RAD runs on Windows 10/11 out of the box:

- **Local engine:** `winget install Ollama.Ollama` — uses NVIDIA GPU automatically
- **Free brains without GPU:** NVIDIA NIM, Groq, Cerebras, Gemini, OpenRouter
- **Voice:** `rad install voice` (TTS needs provider key on Windows)
- **MCP skills:** Python skills get per-skill venvs, npm skills use `npx`

---

## 📋 Every Command

```
rad                                              # chat (default)
rad chat --voice --auto --use <p> --free-lock     # options

rad objective run <goal> [--criteria …] [--auto]  # autonomous
rad objective list | inspect | resume | pause | cancel
rad trace [id] · rad inspect [id] · rad replay [id] --verify
rad why <claim|file> · rad events

rad keys add <provider> <key> | list | rm         # providers
rad providers · rad use <p> · rad cost

rad see <image> [question]                        # vision
rad browse <url> · rad search <query>             # web

rad remember <text> · rad recall <query>          # memory
rad memory show | prune · rad sleep

rad evolve <direction>                            # evolution
rad dna show | rollback | reset
rad corpus · rad benchmark · rad brain …
rad train · rad plan <goal> | run

rad connect <link> · rad skills · rad drop <name> # skills
rad team run <problem> · rad world show           # agents

rad drive connect | push | pull | status          # cloud
rad remind <when> <task> · rad watch <url>        # scheduler
rad say <text> · rad listen · rad models          # voice

rad provider add <name> <url>                     # custom provider
rad workspace [path] · rad install … · rad version
```

**In-chat:** `/help /good /bad /remember /recall /evolve /use /free /auto /cost /sleep /dna /skills /exit`

---

## 🧪 Testing & Measurement

```bash
pip install -e ".[dev]"
python -m pytest -q                  # offline unit tests
rad regression --quick               # security + agent groups + benchmark sample
rad acceptance                       # 50-item acceptance gate with per-item evidence
rad benchmark                        # capability battery: 0–100 per category
rad lab run --suite bank --sample 20 # graded scenario bank
```

900 graded scenarios across 9 categories, plus long-horizon, real-world, and regression tests — all graded on **disk state**, never on what a model claims.

Details: [docs/BENCHMARKS.md](docs/BENCHMARKS.md) · [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)

---

## 📚 Documentation

| Doc | Topic |
|---|---|
| [QUICKSTART](docs/QUICKSTART.md) | First-run guide |
| [INSTALLATION](docs/INSTALLATION.md) | Full install instructions |
| [CONFIGURATION](docs/CONFIGURATION.md) | Config reference |
| [CLI](docs/CLI.md) | Command reference |
| [ARCHITECTURE](docs/ARCHITECTURE.md) | System design |
| [CONTROL-PLANE](docs/CONTROL-PLANE.md) | Objectives, tasks, verification |
| [MEMORY](docs/MEMORY.md) | Memory system |
| [WORLD-MODEL](docs/WORLD-MODEL.md) | Entity/relation graph |
| [AGENTS](docs/AGENTS.md) | Multi-agent teams |
| [SECURITY](docs/SECURITY.md) | Security model |
| [TOOLS](docs/TOOLS.md) | Built-in tools |
| [SKILLS](docs/SKILLS.md) | MCP skill system |
| [EVOLUTION](docs/EVOLUTION.md) | DNA + model evolution |
| [API](docs/API.md) | Local API reference |
| [DESKTOP](docs/DESKTOP.md) | Desktop app |
| [DEVELOPMENT](docs/DEVELOPMENT.md) | Contributing guide |
| [ROADMAP](docs/ROADMAP.md) | Future plans |

---

## 📄 License

[MIT](LICENSE) — Copyright © 2026 Sanath S Patil

---

<p align="center">
  <sub>Built with 🤖 by <a href="https://github.com/seven0070">seven0070</a></sub>
</p>
