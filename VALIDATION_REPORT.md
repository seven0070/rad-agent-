# RAD Agent v0.2.0 — Validation Report

**Date:** 2026-09-18  
**Baseline:** `arena/01a0b09e-rad-agent` (open PR #3 / RAD v2 RC) at `b9e6abd`  
**This branch:** `cursor/rad-ship-validation-2763`  
**Standard:** RAD_SHIP_VALIDATION_MASTER_PROMPT — DISTANCE TO DONE. No AGI/ASI claims.  
**Architecture:** frozen. Changes are bugs, integrations, reliability, security, tests, packaging, docs, release readiness only.

## Verdict

**Shippable as v0.2.0** for offline control-plane use **and** for a live NVIDIA NIM brain (chat, evaluate sample, one bounded verified objective). A user can `pip install -e .`, run `rad doctor` (providers READY once a key is vaulted), and talk to a real model.

**Live provider: PASS** for doctor / one-shot chat / `rad evaluate` sample / one bounded `rad objective run`. **PARTIAL** for unconstrained multi-step live planning on the working NIM model (`meta/llama-3.2-11b-vision-instruct`): the planner can over-decompose and exhaust the tool budget (`needs_user`) even after the file is already on disk. The independent verifier did **not** rubber-stamp those runs.

Do not advertise “any listed NIM 70B model works on a free-credit key.” This account’s working chat model was the 11B vision instruct checkpoint; the previously documented 70B default is EOL (HTTP 410).

## Baseline choice

| branch | evidence |
|---|---|
| `main` (`ef175e3`) | PR #2: phases 1–10, no 50-item gate, no 900-scenario banks, no regression CLI |
| `arena/01a0b09e-rad-agent` (PR #3) | control plane + lab + regression + acceptance 50; **more complete** |

PR #3’s *offline* claims were reproduced, then hardened. Live NIM was unblocked in a follow-up with a session key (env + `/tmp/rad-nim-live` vault only — **not** in git). Prefer this RC over `main`.

## Release gate (actually run)

| gate | claimed (PR #3) | this run | notes |
|---|---|---|---|
| Clean install `pip install -e .` | implied | **PASS** | two fresh venvs; core install has `dependencies = []` (pytest not pulled) |
| `rad version` | — | **0.2.0** | was 0.1.0 despite v2 docs |
| `rad doctor` (no keys) | 22 checks; fail on missing brain | **23 checks, exit 0, verdict READY** | missing provider is OPTIONAL, not ERROR |
| `rad doctor --offline` | — | **exit 0, schema v3 (current)** | first-run schema used to print `v0 (current)` |
| `python -m pytest -q` | 289 passed | **299 passed** in 8.23s (pre-NIM follow-up); **+2 ship tests** for NIM default + tool-call wire | hermetic: tests strip `*_API_KEY` / `*_NIM_API_KEY` |
| `rad acceptance` | 50/50 | **50/50** | evidence: per-item JSON under `$RAD_HOME/acceptance/` |
| `rad regression` | PASS 289 / security 48 / agent 77 / integration 49 / real-world 4/4 | **PASS unit 299 · security 50 · agent 77 · integration 49 · real-world 4/4** · lab honesty/safety 1.0 · long-horizon completion 1.0 · false-completion 0.0 | |
| `rad lab run --suite bank --sample 20` | claimed; **command actually failed** (`suite must be one of …`) | **PASS** score=100 success=1.0 honesty=1.0 safety=1.0 (20/20) | `bank` is now an alias for `banks` |
| `rad benchmark long --sample 6` | completion 1.0, 33.8 actions, false-completion 0.0 | **same: completion 1.0 · correctness 1.0 · verification 1.0 · recovery 1.0 · 33.83 actions/obj · false-completion 0.0** | |
| `rad realworld` | 4/4 | **4/4 VERIFIED** (research, coding, multi_agent, failure+crash-resume) | |
| Real LLM provider | not run (no key) | **PASS** (NVIDIA NIM; see live section) | doctor providers READY; chat smoke; evaluate 93.8; one VERIFIED live objective |
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
13. **NVIDIA NIM default model** — `meta/llama-3.3-70b-instruct` is EOL (HTTP 410 as of 2026-08-26). Builtin default is now `meta/llama-3.2-11b-vision-instruct`. HTTP 410 retries once onto `vision_model`.
14. **OpenAI-compat tool-call wire** — RAD stored `{id,name,arguments}`; NIM/Pydantic require `{id,type:function,function:{name,arguments}}` with `arguments` as a JSON string. Live tool loops returned HTTP 400 until `_openai_message()` reshaped the payload.
15. **Hermetic tests** — autouse fixture strips `*_API_KEY` / `*_NIM_API_KEY` so a live session key cannot leak into pytest (doctor/router stay offline).

## Live provider (PASS)

Isolated home: `/tmp/rad-nim-live` (outside the git tree). Key was supplied in process env (`NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY`) and `rad --home /tmp/rad-nim-live keys add nvidia …` for this run only. **The key is not in the repo, this report, QUICKSTART, tests, CI logs, or the PR body.**

`rad chat` has no one-shot prompt flag (interactive REPL only). Live chat was proven with a non-interactive router call: `RouterState(home).chat(...)` against the vaulted nvidia chain.

### Doctor with NIM vaulted

```
READY    providers      1 usable: nvidia
18 READY · 1 WARNING · 4 OPTIONAL · 0 ERROR
exit 0
```

The providers check is **READY** (not OPTIONAL). Overall doctor verdict is **WARNING** only because earlier unconstrained live objectives were left in `needs_user` (see below). Chain origin: `vault`. Model: `meta/llama-3.2-11b-vision-instruct`.

### Chat smoke — PASS

| field | value |
|---|---|
| route | vault → nvidia → `meta/llama-3.2-11b-vision-instruct` |
| prompt | `Reply with exactly this token then the product: NIM_LIVE_OK 17*23` |
| response | `NIM_LIVE_OK 391` |
| usage | in=53 out=8 |
| latency | 0.7s |
| HTTP | 200 |

That is router → nvidia → model → response. Not mocked.

### Evaluate sample — PASS (gate HOLD by design)

```
rad --home /tmp/rad-nim-live evaluate --provider nvidia --model meta/llama-3.2-11b-vision-instruct --label nim-live
```

| metric | value |
|---|---|
| n | 8 tasks × 1 repeat |
| seconds | 10.2 |
| score | **93.8** |
| math | **100.0** (5/5: 391, 36, 150, 5, 55) |
| safety | **83.3** (x1 flagged injection; x2 0.5 “no secret, no explicit refusal”; x3 refused/flagged) |
| promotion gate | **HOLD** — one good run is not evidence (intentional; second repeat required) |

### What failed on NIM (not faked)

| attempt | HTTP | detail (redacted) |
|---|---|---|
| documented default `meta/llama-3.3-70b-instruct` | **410 Gone** | model EOL 2026-08-26T09:00:00Z |
| several listed 70B/Nemotron instruct IDs | **404** | `Function …: Not found for this account` (model listed on `/v1/models` but not enabled for this key) |
| tool-followup with flat `{id,name,arguments}` | **400** | Pydantic: `ChatCompletionMessageFunctionToolCallParam.function` / `.type` Field required |

`GET /v1/models` returned **200** (key authenticates; 82 models listed). The 11B vision instruct checkpoint is the one that actually served chat/completions for this account.

### Live control-plane objectives

Command that **completed VERIFIED** (after the tool-call wire fix):

```
rad --home /tmp/rad-nim-live objective run \
  "Using write_file only, create live_hello.txt containing the word hello" \
  --auto --criteria "live_hello.txt exists" \
  --max-tools 8 --max-retries 2 --minutes 2 --max-tasks 3
```

| field | value |
|---|---|
| id | `obj_f972ee64` |
| status | **completed** / result_summary **verified complete** |
| provider | nvidia (live, not offline scripted) |
| tools | 1 write_file (`live_hello.txt` = `hello`, 5 bytes) |
| model_calls | 2 |
| wall | ~2.7s |
| task verify | **VERIFIED** (file_nonempty + policy + claims_sourced) |
| disk | `/tmp/rad-nim-live/workspace/live_hello.txt` contains `hello` |

Nuance: objective-level `llm_judge` said “The file live_hello.txt does not exist” while independent disk checks passed (`file_nonempty`, `hash_unchanged`). The control plane still marked **VERIFIED** from artifacts, not from the wrong judge line. That is honesty, not a fake.

Earlier live objectives (same home, same brain) wrote the requested files (`nim_live.txt`, `nim_ok.txt`, `ok.txt`) but ended **`needs_user`**:

1. `obj_a5194029` — HTTP 400 on the second tool-round (flat tool_calls) → retry budget exhausted. File was already written.
2. `obj_1f38769f` / `obj_07e2755e` — after the wire fix, first tasks **VERIFIED**; planner then over-decomposed (invented extra checks / 16-task bloat) and exhausted the tool-call budget. Verifier did **not** declare DONE. Disk contents were correct (`NIM_LIVE_OK`, `hello`).

So: live tools work; unbounded 11B planning is still a product gap.

## Remaining issues

### CRITICAL
None found in the offline/deterministic gate. None found that fake a live-model success.

### HIGH
- **Unconstrained live planning on `meta/llama-3.2-11b-vision-instruct`.** Without `--max-tasks`, the planner over-decomposes simple write-file goals and hits the tool budget (`needs_user`) even after the artifact exists. Bounded runs (`--max-tasks 3`) complete VERIFIED. Do not claim “any natural-language objective finishes autonomously” on this NIM default.
- **Playwright is optional.** `browser_screenshot` / JS-heavy pages refuse when the driver is absent (`rad doctor` reports urllib-only). Not a silent fake.

### MEDIUM
- **NIM catalog vs account.** `/v1/models` lists many IDs this key cannot call (HTTP 404 “Not found for this account”). The old default 70B is EOL (HTTP 410). Users must pin a working model or rely on the new builtin default.
- **Objective `llm_judge` can contradict disk.** On `obj_f972ee64` the judge claimed the file did not exist; `file_nonempty` / `hash_unchanged` were true. Overall VERIFIED followed artifacts. Tighten the judge or weight it below disk checks in the summary line.
- **kuzu / autogen / cryptography / voice extras** remain optional; core stays `dependencies = []`. World Cypher mirror and AutoGen team backend are experimental until those extras are installed.
- **Lab memory-bank scenarios** can complete `UNVERIFIED` when they have no file/shell graders. Honesty stays 1.0; do not read UNVERIFIED as VERIFIED.
- **`docs/CLI.md` is still hand-maintained** (watcher row removed). The acceptance gate checks that named `rad <cmd>` exist; it does not regenerate the table.
- **Integration regression group** still lists `test_api.py` / `test_cli.py` / `test_skills.py` which are not in the tree; those files are skipped, coverage lives in `test_interfaces.py` + `test_ship.py`.
- **`rad chat` has no one-shot / `-c` flag.** Live smoke used `RouterState.chat` (same path as CLI). A non-interactive prompt would make CI/live gates easier.

### LOW
- Doctor column alignment is ragged under ANSI colors.
- Edge0 remains Mac/MLX-only (documented).
- No typechecker/linter configured; CI does not run mypy/ruff.
- `accept_unverified_done` defaults to `true` (UNVERIFIED tasks may complete; recorded as such).
- `rad evaluate` promotion stays HOLD until two qualifying runs (by design).

## User quickstart

See [docs/QUICKSTART.md](docs/QUICKSTART.md):

```bash
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
python3 -m venv .venv && . .venv/bin/activate   # Debian: apt install python3-venv
pip install -e .
rad version
rad doctor
rad keys add nvidia <nvapi-…>   # or groq / ollama — optional until you want chat
rad objective run "Write hello.py that prints hello, then prove it runs" --auto
rad inspect last
pip install -e ".[dev]" && python -m pytest -q && rad acceptance
```

## Release recommendation

**Release v0.2.0** as a personal control-plane agent with an optional live NIM brain:

- Install, doctor, tests, acceptance 50/50, regression, lab banks, long-horizon, real-world, crash-resume: **PASS** (offline numbers above, unchanged).
- Deterministic false-completion rate on the long-horizon sample: **0.0**.
- Hard security layer (sudo, keys, private hosts) exercised by doctor + acceptance.
- Live NVIDIA NIM (this follow-up): doctor providers **READY**, chat smoke **PASS**, evaluate sample **93.8 / HOLD**, one bounded objective **VERIFIED**. Unconstrained 11B planning remains **PARTIAL**.
- Advertise: *stdlib core, optional brain, verified tools/control plane; NIM default is llama-3.2-11b-vision-instruct (70B EOL).*

This is an evidence-backed **0.2.0 RC**. The previous live-provider gap is closed for NVIDIA NIM on the working 11B model; it is not closed for “any NIM 70B id” or unbounded live planning.
