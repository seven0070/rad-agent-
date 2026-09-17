# Security model (`rad/policy.py`)

Every tool call — from the REPL, the control plane, or a sub-agent — passes through **one**
gate inside `run_tool`: `Policy.decide(capability, resource) → HARD_DENY | DENY | ASK | LIMITED | ALLOW`.

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
- `--auto` only turns **ASK → ALLOW**; DENY/LIMITED/hard are untouched

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
rad audit
```

## Not covered (honest)
No OS-level sandbox: shell still runs as your user with workspace as cwd. Hard patterns are
regexes and can be evaded by a determined model (e.g. base64 tricks); the workspace boundary,
env scrubbing and redaction reduce blast radius but do not replace containers.
