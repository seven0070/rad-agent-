# Configuration

RAD reads one JSON file (`~/.rad/config.json`, override with `RAD_HOME`) plus environment
variables. `rad config show` prints the effective values, `rad config get <key>`,
`rad config set <key> <value>` and `rad config unset <key>` change them; invalid values are
rejected with a reason instead of being written (`rad doctor` re-checks the whole file and
`rad doctor --fix` repairs what is safe).

## Keys

| key | default | what it does |
|---|---|---|
| `workspace` | `null` | where the hands work (files, shells) — a boundary, not just a default |
| `free_lock` | `false` | true = paid providers are never used, no matter what falls over |
| `auto` | `false` | true = stop asking for confirmation (hard-blocked patterns stay blocked regardless) |
| `force_provider` | `null` | pin one provider for every call |
| `model` | `null` | pin a model id (otherwise each provider's default is used) |
| `edge0_url` | `"http://127.0.0.1:8000/v1"` | local Edge0 endpoint (default http://127.0.0.1:8000) |
| `edge0_tier` | `"10b"` | which Edge0 tier to talk to |
| `ollama_url` | `"http://127.0.0.1:11434"` | local Ollama endpoint |
| `lmstudio_url` | `"http://127.0.0.1:1234/v1"` | local LM Studio endpoint |
| `vision_order` | `null` | preferred vision providers, in order |
| `tts` | `"auto"` | text-to-speech engine (piper, say, …) |
| `stt` | `"auto"` | speech-to-text engine (whisper, …) |
| `max_tool_rounds` | `8` | tool-call rounds per model turn |
| `max_context_chars` | `24000` | context budget for prompts |
| `memory_k` | `5` | how many memories are auto-recalled per turn |
| `sleep_threshold_hours` | `24` | idle hours before memory consolidation |
| `drive_folder` | `"RadAgent"` | Google Drive folder for the cloud mind |
| `watch_every_min` | `30` | default interval for page watchers |
| `custom_providers` | `[]` | user-added OpenAI-compatible endpoints (`rad provider add`) |
| `allow_outside_workspace` | `false` | true = absolute paths outside the workspace are allowed (default false) |
| `allow_localhost_web` | `false` | true = web/browser tools may reach loopback (local dev servers); metadata endpoints stay blocked |
| `plan_infer_done` | `false` | let the planner infer completion from the observation stream |
| `objective_parallel` | `2` | how many tasks of one objective may run at once |
| `accept_unverified_done` | `true` | accept a task that finished without machine verification (off by default: an unproven task is not "done") |
| `evolution_require_approval` | `false` | evolution candidates need explicit approval before promotion |
| `evolution_suite` | `"smoke"` | benchmark suite used to gate an evolution candidate |
| `allow_api_fix` | `false` | allow `GET /v1/doctor?fix=1` to repair state |
| `api_port` | `7331` | default port for `rad serve` |

## Environment variables

* `RAD_HOME` — state directory (beats the default `~/.rad`).
* Provider keys — `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`, `NVIDIA_API_KEY`,
  `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`, … are
  auto-detected. Precedence: RAD's vault (`rad keys add`) → environment → `.env`.

## Permissions are configuration too

`rad policy show` lists the capability defaults (see [TOOLS.md](TOOLS.md)) and
`rad policy allow|ask|deny|limit <capability> [pattern]` edits them. The **hard layer**
is code, not settings: dangerous shell patterns, protected paths, private/metadata hosts
and credentials-in-URL are refused even with `auto = true` and a wildcard ALLOW rule.
The two opt-ins that do widen reach are `allow_outside_workspace` (files) and
`allow_localhost_web` (local dev servers) — nothing else can be widened from config, and
neither of them unblocks metadata endpoints or credential paths.

## A few recipes

```bash
rad config set free_lock true              # never spend money, ever
rad config set workspace ~/code            # point the hands at a project
rad config set allow_localhost_web true    # let the browser tools hit local dev servers
rad policy deny web '*'                    # cut the network from agent actions
rad policy limit shell --limits '{"timeout": 30}'   # cap how long a shell command may run
```

Every write is validated: `rad config set objective_parallel 99` is refused with the range,
and `rad doctor` reports a config key whose type or range drifted (with the value it would set).
