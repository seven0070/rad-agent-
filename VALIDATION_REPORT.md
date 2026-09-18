# RAD Agent v0.2.0 — Validation Report

**Date:** 2026-09-18  
**Baseline:** `arena/01a0b09e-rad-agent` (open PR #3 / RAD v2 RC) at `b9e6abd`  
**This branch:** `cursor/rad-ship-validation-2763`  
**Standard:** RAD_SHIP_VALIDATION_MASTER_PROMPT — DISTANCE TO DONE. No AGI/ASI claims.  
**Architecture:** frozen. Changes are bugs, integrations, reliability, security, tests, packaging, docs, release readiness only.

## Verdict

**Shippable as v0.2.0 for offline / control-plane use.** A user can `pip install -e .`, run `rad doctor` (READY with OPTIONAL providers), run the 50-item acceptance gate, and execute verified objectives through the control plane without a model.

**Live LLM chat / `rad evaluate` against a real provider: BLOCKED in this environment** — no API keys and no local engine were present. Those paths refuse honestly; they were not faked.

Do not merge a “fully autonomous personal agent with a live brain” claim until a human configures one provider and re-runs the live items below.

## Baseline choice

| branch | evidence |
|---|---|
| `main` (`ef175e3`) | PR #2: phases 1–10, no 50-item gate, no 900-scenario banks, no regression CLI |
| `arena/01a0b09e-rad-agent` (PR #3) | control plane + lab + regression + acceptance 50; **more complete** |

PR #3’s *offline* claims were reproduced, then hardened. Prefer this RC over `main`.

## Release gate (actually run)

| gate | claimed (PR #3) | this run | notes |
|---|---|---|---|
| Clean install `pip install -e .` | implied | **PASS** | two fresh venvs; core install has `dependencies = []` (pytest not pulled) |
| `rad version` | — | **0.2.0** | was 0.1.0 despite v2 docs |
| `rad doctor` (no keys) | 22 checks; fail on missing brain | **23 checks, exit 0, verdict READY** | missing provider is OPTIONAL, not ERROR |
| `rad doctor --offline` | — | **exit 0, schema v3 (current)** | first-run schema used to print `v0 (current)` |
| `python -m pytest -q` | 289 passed | **299 passed** in 8.23s | +ship-readiness tests; 0 failed |
| `rad acceptance` | 50/50 | **50/50** | evidence: per-item JSON under `$RAD_HOME/acceptance/` |
| `rad regression` | PASS 289 / security 48 / agent 77 / integration 49 / real-world 4/4 | **PASS unit 299 · security 50 · agent 77 · integration 49 · real-world 4/4** · lab honesty/safety 1.0 · long-horizon completion 1.0 · false-completion 0.0 | |
| `rad lab run --suite bank --sample 20` | claimed; **command actually failed** (`suite must be one of …`) | **PASS** score=100 success=1.0 honesty=1.0 safety=1.0 (20/20) | `bank` is now an alias for `banks` |
| `rad benchmark long --sample 6` | completion 1.0, 33.8 actions, false-completion 0.0 | **same: completion 1.0 · correctness 1.0 · verification 1.0 · recovery 1.0 · 33.83 actions/obj · false-completion 0.0** | |
| `rad realworld` | 4/4 | **4/4 VERIFIED** (research, coding, multi_agent, failure+crash-resume) | |
| Real LLM provider | not run (no key) | **BLOCKED** | no `*_API_KEY` / vault / `.env` / local engine in this environment |
| Clean install again | — | **PASS** | second venv, `rad doctor --offline` READY |
| GitHub Actions CI (3.10, 3.12) | none on RC | **PASS** (this PR) | install + doctor --offline + pytest + acceptance |

### Doctor (fresh home, no keys, network on)

```
18 READY · 0 WARNING · 5 OPTIONAL · 0 ERROR
verdict: READY — optional capabilities missing; core still works
exit 0
workspace = $RAD_HOME/workspace   (not the git clone)
schema v3 (current)
sandbox: hard layer active
```

OPTIONAL: skills, providers, local-engines, mcp, voice. None of these fail the command.

### Acceptance 50/50

All ten areas passed (runtime, control, state, memory, agents, security, routing, ops, benchmarks, docs). The gate still fails if docs mention a command that does not exist, if verification is model-word-only, or if false-completion appears on deterministic items.

### Lab sample (advertised command)

`rad lab run --suite bank --sample 20` → 20 PASS, honesty=1.0, safety=1.0, score=100. Three memory scenarios completed `UNVERIFIED` (no disk graders on those scripts); they did **not** claim verified success. False-completion on the long-horizon sample remains 0.0.

## Fixes applied on this branch (not a redesign)

1. **Missing provider is OPTIONAL** — clean `rad doctor` no longer exits 1 without a key. Labels: READY / WARNING / OPTIONAL / ERROR.
2. **Schema stamp vs report** — doctor now stamps a fresh home then reports `v3 (current)`, not `v0`.
3. **Default workspace** is `$RAD_HOME/workspace`, not process CWD (clone-and-run no longer writes into the repo).
4. **`rad lab run --suite bank`** — documented command actually runs (alias of `banks`).
5. **`rad --home <dir> <cmd>`** — global `--home` before a subcommand used to be rewritten into `chat` and fail.
6. **`rad config set` validates** — unknown keys and out-of-range values are refused (as the docs already claimed).
7. **Local-engine probe** uses `probe_local()` (no `/v1/v1/models` on Edge0/LM Studio URLs).
8. **Sandbox check** added to doctor (sudo + keys hard-deny + workspace jail).
9. **Version synced to 0.2.0** (`rad/__init__.py`, `pyproject.toml`, MCP clientInfo, banner).
10. **CI** — `.github/workflows/ci.yml` (Python 3.10 & 3.12: install, doctor --offline, pytest, acceptance). Both matrix jobs on this PR completed **success**.
11. **Docs** match reality: `rad.json` not `config.json`, 23 doctor checks, Python 3.9+, `bank` suite, hidden `watcher`, [QUICKSTART](docs/QUICKSTART.md).
12. **Snapshot restore** uses `tarfile` `filter="data"` on Python that supports it.

## Live provider (BLOCKED)

This environment had **no** `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY`, `NVIDIA_API_KEY`, `XAI_API_KEY`, `MISTRAL_API_KEY`, no `~/.rad` vault, no project `.env`, and no Ollama/LM Studio/Edge0 listener.

**How the user unblocks it (do not skip doctor after):**

```bash
rad keys add groq gsk_…          # or: export GROQ_API_KEY=…
# or: ollama serve && ollama pull llama3.2
rad providers
rad doctor
rad chat                         # live loop
rad evaluate                     # live model battery (refuses without a brain)
```

Until that is done, **do not treat chat quality, native tool-calling against a real model, or live `rad evaluate` as passed.** Offline scripted sessions, lab banks, and the control plane *are* passed.

## Remaining issues

### CRITICAL
None found in the offline/deterministic gate.

### HIGH
- **No live provider in CI/this sandbox.** Real-user chat, streaming, fallback across paid/free keys, and live `rad evaluate` are unproven here. Configure a key (see above) before calling the product “a working personal agent with a brain.”
- **Playwright is optional.** `browser_screenshot` / JS-heavy pages refuse when the driver is absent (`rad doctor` reports urllib-only). Not a silent fake.

### MEDIUM
- **kuzu / autogen / cryptography / voice extras** remain optional; core stays `dependencies = []`. World Cypher mirror and AutoGen team backend are experimental until those extras are installed.
- **Lab memory-bank scenarios** can complete `UNVERIFIED` when they have no file/shell graders. Honesty stays 1.0; do not read UNVERIFIED as VERIFIED.
- **`docs/CLI.md` is still hand-maintained** (watcher row removed). The acceptance gate checks that named `rad <cmd>` exist; it does not regenerate the table.
- **Integration regression group** still lists `test_api.py` / `test_cli.py` / `test_skills.py` which are not in the tree; those files are skipped, coverage lives in `test_interfaces.py` + `test_ship.py`.

### LOW
- Doctor column alignment is ragged under ANSI colors.
- Edge0 remains Mac/MLX-only (documented).
- No typechecker/linter configured; CI does not run mypy/ruff.
- `accept_unverified_done` defaults to `true` (UNVERIFIED tasks may complete; recorded as such).

## User quickstart

See [docs/QUICKSTART.md](docs/QUICKSTART.md):

```bash
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
python3 -m venv .venv && . .venv/bin/activate   # Debian: apt install python3-venv
pip install -e .
rad version
rad doctor
rad keys add groq gsk_…     # optional until you want chat
rad objective run "Write hello.py that prints hello, then prove it runs" --auto
rad inspect last
pip install -e ".[dev]" && python -m pytest -q && rad acceptance
```

## Release recommendation

**Release v0.2.0** as a **personal control-plane agent** that is honest about brains:

- Install, doctor, tests, acceptance 50/50, regression, lab banks, long-horizon, real-world, crash-resume: **PASS** (numbers above, rerun in this report).
- Deterministic false-completion rate on the long-horizon sample: **0.0**.
- Hard security layer (sudo, keys, private hosts) exercised by doctor + acceptance.
- **Do not** advertise “works with your LLM out of the box” without a key. Advertise: *stdlib core, optional brain, verified tools/control plane.*

If a maintainer adds a Groq/OpenAI/Ollama brain and `rad evaluate` + a live `rad chat` objective succeed, promote the live-provider row from BLOCKED to PASS in a follow-up. Until then this is an evidence-backed **0.2.0 RC with one honest gap**.
