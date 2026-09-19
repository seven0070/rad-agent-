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

## Public 1.0 install (product path)

Package **1.0.0**. `rad version` prints **1.0.0**. Needle stays **OFF**. Caps
(`max_plan_tasks` **16**, default `Budget.tool_calls` **60**) unchanged. False
`DONE:` **0**. Class C (NIM 403 / OpenRouter 429) is **unblock the environment**,
not a product patch. Do **not** invent remaining-quota. Live text_analyzer@12 is
**not** claimed PASS.

The public install is a **wheel or sdist from GitHub Release Version 1 /
tag `v1.0.0`**. That release is **not** created in the G5-1 implementation PR —
Sanath packs Version 1 after merge (see [Version 1 packing](#version-1-packing-sanath)
below). Until those assets exist, use the [contributor checkout](#contributor-checkout).

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install https://github.com/seven0070/rad-agent-/releases/download/v1.0.0/rad_agent-1.0.0-py3-none-any.whl
rad version          # prints 1.0.0
rad doctor --offline
```

sdist equivalent (same tag, after the pack):

```bash
pip install https://github.com/seven0070/rad-agent-/releases/download/v1.0.0/rad_agent-1.0.0.tar.gz
```

From the annotated tag (no wheel required; still after Sanath tags `v1.0.0`):

```bash
pip install "rad-agent @ git+https://github.com/seven0070/rad-agent-.git@v1.0.0"
```

PyPI `pip install rad-agent` is **not** claimed. `pyproject.toml` is PyPI-ready
(classifiers, URLs, empty runtime deps). Publishing to PyPI needs a token Sanath
owns — this tree does **not** store that token.

`rad` works without a key, without a local engine and without network access: it will tell you
plainly when it has no brain (`rad providers`), and every control-plane test in the acceptance gate
runs offline.

## Contributor checkout

Source checkout remains the path for development and for installs **before**
Version 1 assets exist:

```bash
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
python3 -m venv .venv && . .venv/bin/activate
pip install -e .                 # or: pip install -e ".[dev]" for the test suite
rad version                      # prints 1.0.0
rad doctor                       # READY / WARNING / OPTIONAL / ERROR — 23 checks
```

## Version 1 packing (Sanath)

**Do not** cut the GitHub Release or tag from a G5-1 implementation PR. After
that PR merges to `main`, pack **one Version 1 / 1.0** at tag **v1.0.0**:

1. Checkout the merge commit on `main`. Confirm `rad version` prints `v1.0.0`.
2. Build installable assets (no secrets; `dist/` is gitignored):

   ```bash
   python3 -m venv .venv-pack && . .venv-pack/bin/activate
   pip install -U pip build
   python -m build
   ls dist/
   # rad_agent-1.0.0-py3-none-any.whl
   # rad_agent-1.0.0.tar.gz
   ```

3. Create GitHub Release **Version 1**, tag **`v1.0.0`**, target = that merge
   commit. Attach **both** files from `dist/`. Do **not** upload API keys,
   vault files, `.env`, or tokens.
4. Optional later: `twine upload dist/*` to PyPI with Sanath’s token. Not
   required for Version 1; the GitHub Release assets are the public install
   path.

`pip install -e ".[pack]"` installs `build` only.

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
