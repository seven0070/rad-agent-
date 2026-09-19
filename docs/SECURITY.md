# Security model (`rad/policy.py`)

Every tool call — from the REPL, the control plane, a sub-agent, Jerry, or the desktop UI — passes through **one**
gate inside `run_tool`: `Policy.decide(capability, resource) → HARD_DENY | DENY | ASK | LIMITED | ALLOW | SCOPE_VIOLATION | UNAUTHORIZED`.

## Authority profiles (`rad/authority.py`)

User → **authority profile** → capability / scope / confirmation → **existing** `Policy.decide` → executor → tool.

Profiles (persisted in `~/.rad/authority.json`; STANDARD if the file is missing or corrupt):

| profile | meaning |
|---|---|
| **SAFE** | confirmation-heavy, narrow grants (read/memory; write/shell/packages/mcp/spawn/py/paid denied), workspace-only scope |
| **STANDARD** | default compatibility — existing RAD defaults; no extra grant/scope layer |
| **AUTONOMOUS** | confirmation policy = never (ASK→ALLOW) inside the granted set; budgets and hard layer stay on |
| **UNRESTRICTED** | explicitly user-authorized autonomy (`--i-authorize-unrestricted` / `confirm_unrestricted`). Broad grants, confirmation never, user-defined scopes. **Not a bypass** of Policy.decide, the executor, budgets, audit, provenance or verification |
| **CUSTOM** | per-capability effects you set |

`--auto` is confirmation policy = never for that session. It still cannot turn DENY / LIMITED / hard / SCOPE_VIOLATION / UNAUTHORIZED into ALLOW.

Conceptual capabilities (`filesystem.read`, `shell.execute`, `network.request`, `browser.access`, `mcp.use`, `skills.install`, `package.install`, `process.spawn`, `model.free`, `model.paid`) map onto the existing policy names. `credentials` stays denied in every profile.

Jerry (`rad/jerry.py`) is an operator layer: chat and propose objectives. It has no tool runner.

## Two layers

**Hard layer (code, not configurable, not affected by `--auto`, rules, or the model):**
- destructive shell: `sudo`, `rm -rf /|~`, `mkfs`, `dd if=`, fork bombs, `curl|sh`, `shutdown`, `git push --force`, …
- secret paths: `~/.rad/keys`, `.vault.key`, `~/.ssh`, `.git-credentials`, `.netrc`, `.aws/credentials`, `/etc/shadow`, `.git/config`
- the policy and audit files themselves (the model cannot loosen its own permissions)
- web egress to loopback / RFC1918 / link-local / cloud-metadata hosts; only `http(s)`; no credentials in URLs
- **secret redaction** on every tool output (`sk-…`, `ghp_…`, AKIA, Slack, bearer tokens, private keys, `key=…`)
- shell children get an env with `*KEY*`, `*SECRET*`, `*TOKEN*`, `*PASSWORD*` variables stripped

**Soft layer (`~/.rad/policy.json`, edited with `rad policy`):**
- per-capability defaults: `fs.read ALLOW · fs.write ASK · shell ASK · web ALLOW · vision ALLOW · agents.spawn ASK · mcp ASK`
- ordered rules `capability + glob → effect [+ limits]`; first match wins
- `LIMITED` limits are enforced: shell `timeout`, write `max_bytes`, read/fetch `max_chars`
- optional `web_allow` domain allowlist
- `--auto` / confirmation=never only turns **ASK → ALLOW**; DENY/LIMITED/hard/SCOPE_VIOLATION/UNAUTHORIZED are untouched

Sub-agents carry a **capability envelope** (`ToolCtx.agent_caps`) that can only narrow: checked
inside the gate, in addition to the agent runtime's wrapper.

## Audit
Every decision is appended to `~/.rad/audit.jsonl` with actor (`user`, `control:<obj>`, `agent:<id>`),
tool, redacted resource, effect, deciding layer, reason and outcome (`allowed`, `user approved`,
`user declined`, `denied`, `blocked`). `rad audit [-n N] [--effect DENY]`.

## Commands
```
rad policy                              # show effective policy
rad policy deny shell "git push*"       # rule
rad policy limit shell "pytest*" --limits '{"timeout":60}'
rad policy ask fs.write "*.py" · rad policy allow web
rad policy default shell DENY · rad policy rm <n> · rad policy web-allow example.com docs.python.org
rad policy test shell "sudo ls" [--auto] # dry-run a decision
rad authority                            # show profile / capabilities / scopes
rad authority set SAFE
rad authority set UNRESTRICTED --i-authorize-unrestricted
rad audit
```

## Desktop & sidecar (`desktop/`, `rad/sidecar.py`)

The packaged desktop bundles the Python core as `rad-backend` (Tauri `bundle.externalBin`).
Its security properties, with the tests that pin them (`tests/test_security_desktop.py`,
`tests/test_desktop_api.py`, `tests/test_desktop_surface.py`):

- **Loopback only.** The sidecar refuses any non-`127.0.0.1` bind (exit 1, JSON error). It
  serves exactly the existing `/v1/*` API; a wrong/missing Bearer token → 401 on every
  route. The token is ≥32 random bytes, written `0600` at `~/.rad/api.token`, rotatable.
- **Fixed argv, no shell.** The Tauri shell spawns the sidecar with a hard-coded argument
  vector (`serve --host 127.0.0.1 --port <n> [--home <dir>]`); no user string ever reaches
  a command line, and Tauri capabilities are limited to the seven `backend_*` lifecycle
  commands. There is no `tauri-plugin-shell`/`fs`, no `sh -c`, and no shell/tools/exec
  route in the HTTP API or the frontend (the frontend holds no authority state — no
  localStorage/sessionStorage/indexedDB).
- **Credential paths are never grantable.** `credentials` is in the never-granted set:
  granting it via the API is coerced to `DENY`, and credential-looking paths are denied in
  every profile, UNRESTRICTED included.
- **Artifact content is registry-gated.** `GET /v1/objectives/{id}/artifact-content`
  resolves only artifacts registered by *that* objective: 404 otherwise, 403 when the
  location leaves workspace/home, 415 for non-text; text is redacted and capped.
- **Stale-process handling is explicit.** Before start, a foreign or stale listener on the
  port is probed (401-with-bearer ⇒ stale RAD, reported as such); starts that fail to
  become healthy within 20 s are killed and the backend log tail is surfaced — nothing
  fails silently.
- **UNRESTRICTED via the desktop still needs the explicit authorization flag** (409
  without it), and profiles never bypass the layers above.

## Not covered (honest)
No OS-level sandbox: shell still runs as your user with workspace as cwd. Hard patterns are
regexes and can be evaded by a determined model (e.g. base64 tricks); the workspace boundary,
env scrubbing and redaction reduce blast radius but do not replace containers. The desktop's
Rust shell and per-platform installers are compile-checked/frozen by CI
(`.github/workflows/desktop.yml`), not by this workspace (no Rust toolchain here); the
clean-machine install pass is a release-checklist item (docs/DESKTOP.md), not a claim.
