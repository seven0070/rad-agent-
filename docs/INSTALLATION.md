# Installation

## Requirements

* **Python 3.9+** (3.11 or 3.12 recommended). Nothing else — the core has **no runtime
  dependencies**; `dependencies = []` in `pyproject.toml` is enforced by the acceptance gate.
* A brain: any one of
  * a local engine (Edge0 / Ollama / LM Studio / vLLM on your machine),
  * a free cloud key (`rad keys add groq <key>`, `rad keys add nvidia <nvapi-…>`, …),
  * any OpenAI-compatible endpoint (`rad provider add`).
* Optional extras, each installed only when you want the feature:
  `pip install "playwright"` (real browser driving + screenshots), `kuzu` (graph mirror for the
  world model), `autogen` (team backend), `pypdf`/`python-docx` (document reading).

## Install

```bash
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
python3 -m venv .venv && . .venv/bin/activate
pip install -e .                 # or: pip install -e ".[dev]" for the test suite
rad version
rad doctor                       # READY / WARNING / OPTIONAL / ERROR — 23 checks
```

`rad` works without a key, without a local engine and without network access: it will tell you
plainly when it has no brain (`rad providers`), and every control-plane test in the acceptance gate
runs offline.

## Where RAD keeps state

Everything lives under **`~/.rad`** (override with `RAD_HOME`) as plain JSON/markdown — no
database, no daemon:

```
~/.rad/
  rad.json             settings (rad config show / rad config path)
  keys/keys.env        0600, RAD's own secrets (capability `credentials` = DENY)
  workspace/           the hands: files RAD may read/write/run in (default; override with rad config set workspace)
  memory/long/…        episodic · semantic · procedural (markdown + front-matter)
  objectives/<id>/     objective.json · tasks.json · events.jsonl · observations/ · artifacts.json
  events.jsonl         the global event stream (rad events)
  audit.jsonl          every permission decision (rad audit)
  policy.json          capability defaults + rules
  experience/lessons.json
  world/graph.json     world model
  agents/, skills/, dna.json, schema.json, backups/, lab/runs/, acceptance/, realworld/
```

Upgrading, backing up and moving a home are covered in [MIGRATION.md](MIGRATION.md); health checks
and repairs in [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## First run

```bash
rad chat                          # talk to Rad (routes to the best free brain first)
rad objective run "write hello.py and prove it runs"   # one autonomous goal, verified end to end
rad inspect last                  # plan → tasks → evidence for what just happened
rad status                        # objectives, memory, brain, jobs, schema on one screen
```

## Verify the install

```bash
rad doctor                # 0 = healthy, 1 = something needs attention (each finding has a fix)
rad regression --quick    # security + agent test groups + a live benchmark sample
rad acceptance --area runtime,control
```

`rad install <part>` bootstraps optional pieces (Edge0 on Apple Silicon, helper binaries such as
ffmpeg/piper) and prints exactly what it would fetch first.

## Uninstall

`pip uninstall rad-agent` removes the code; delete `~/.rad` (after `rad storage snapshot`) to remove
state. Nothing is installed outside those two places: no service, no system-wide config.
