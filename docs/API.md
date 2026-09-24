# Local API (`rad serve`)

`rad serve [--port 7331]` starts a stdlib HTTP server on **127.0.0.1** exposing the control plane
as JSON. Binding to any other host requires `--host … --i-know-this-exposes-rad`.

**Auth:** every request needs `Authorization: Bearer <token>`. The token is created on first
start (0600 at `~/.rad/api.token`, printed once; `--rotate-token` replaces it). Wrong/missing
token → 401 for every route, including `/health`.

**Same gates as the CLI.** Requests never carry file paths or commands; they create objectives
and the Controller, policy layer and hard layer do the rest. Because HTTP cannot answer
confirmation prompts, `POST /objectives` only *starts* work when config `auto=true`; otherwise
the objective is created `PENDING` (201) for `rad objective run`, unless the authority
profile's confirmation policy is already `never` (AUTONOMOUS / UNRESTRICTED). `/chat` is one
Jerry turn with session `auto=false` (ASK-level tools are declined unless the profile
converts ASK→ALLOW; ALLOW-level tools work). Desktop uses these routes; it cannot run tools.

Bodies ≤ 256 KB, JSON objects only. Every request is logged to `~/.rad/logs/api.jsonl`
(method, path, status, ms, peer — no bodies).

| method | path | notes |
|---|---|---|
| GET | `/v1/health` | version, schema, running objectives |
| GET | `/v1/doctor` | findings; `?fix=1` honoured only with config `allow_api_fix` |
| GET | `/v1/objectives?active=1` | |
| POST | `/v1/objectives` | `{goal, criteria?, constraints?, budget?, run?}` → 202 started / 201 pending |
| GET | `/v1/objectives/{id}` | objective + tasks |
| POST | `/v1/objectives/{id}/resume\|pause\|cancel` | resume → 409 when `auto=false`; a crashed objective (task left `RUNNING` on disk) is crash-restored on resume (`CRASH_DETECTED` + `CHECKPOINT_RESTORED` events, completed tasks never re-run) |
| POST | `/v1/objectives/{id}/run` | plan + start a `PENDING` objective (202); 409 when `auto=false` |
| GET | `/v1/objectives/{id}/events?kind=&since_seq=` | event log |
| GET | `/v1/objectives/{id}/trace` | tasks + verification |
| GET | `/v1/objectives/{id}/plan` | current plan (version, source, attempts, replans) + tasks with machine checks |
| GET | `/v1/objectives/{id}/recovery` | recovery decisions, failed tasks, retry budget used |
| GET | `/v1/objectives/{id}/live?since_seq=` | live view for the dashboard: status, tasks by status, current task, budget account, verification, recent events (paginated by `seq`) |
| GET | `/v1/objectives/{id}/artifacts` | artifact registry: id, location, sha256, version chain |
| GET | `/v1/objectives/{id}/artifact-content?ref=<id\|path\|filename>` | redacted text preview of a **registered** artifact only — 404 if not registered, 403 if outside workspace/home, 415 if binary; secrets redacted |
| GET | `/v1/objectives/{id}/observations?task=` | tool observations (args, redacted output, status, duration) |
| GET | `/v1/objectives/{id}/why?q=<artifact or claim>` | provenance — an artifact ref returns the full chain (`artifact`, `versions`, `action`, `task`, `evidence`); claim text returns a scored verdict with `trusted:false` on web-sourced support |
| GET | `/v1/usage` | rollup of real recorded usage only (count, tool_calls, model_calls, tokens, money); the remaining-quota note is a pointer, never an invented quota |
| GET | `/v1/memory?layer=&n=` · POST `/v1/memory {text, layer?}` | memories by layer (working/episodic/semantic/procedural); API writes are USER_PROVIDED, source `api` |
| GET | `/v1/memory/recall?q=&k=` | ranked recall |
| GET | `/v1/user` · `/v1/policy` · `/v1/audit?n=` · `/v1/lab/history` · `/v1/evolve/candidates` | read-only views |
| POST | `/v1/chat {text}` | one Jerry turn (`via: jerry`) |
| POST | `/v1/triage {text, kind?}` | advisory auto/escalate classifier (offline-fallback = `escalate`; never gates execution) |
| GET | `/v1/authority` | profile, conceptual capabilities, scopes, confirmation, existing budgets |
| PUT | `/v1/authority` | `{profile, confirm_unrestricted?, capabilities?, scopes?, confirmation?}`. UNRESTRICTED → 409 without `confirm_unrestricted` |
| GET / PUT | `/v1/settings` | safe config subset. Cannot raise budgets, change Needle, or set `--auto` |

Not provided on purpose: policy rule edits, key management, evolution promotion, file access,
arbitrary shell — those stay CLI-only (or do not exist). Desktop has no `/v1/shell`.
