# RFC-001: Remote-MCP Tool Execution Hardening

**Status:** PROPOSED · **Tier:** Security / Gen5 candidate
**Law:** the executor is the only way to act; a model's word is never a boundary.

## 1. Problem
`rad connect https://remote...` approves a *tool list*, not code running on
someone else's machine. Results are attacker-controlled context; args are
egress; tool lists can drift after approval; names can shadow core tools.

## 2. Threat model
| ID | Threat |
|----|--------|
| T1 | Exfiltration via args/results |
| T2 | Prompt injection via results |
| T3 | Tool identity attacks (shadowing) |
| T4 | Resource abuse (size/context starvation) |
| T5 | Credential mishandling |
| T6 | Silent scope creep (toolset drift) |
| T7 | Unencrypted transport / MITM |

## 3. Trust tiers (skills registry)
```json
{"name": "...", "origin": "https://...", "trust_tier": "remote",
 "toolset_digest": "sha256:...", "egress_allowlist": ["host"],
 "budget": {"calls_per_minute": 10, "max_result_bytes": 65536, "timeout_s": 30},
 "status": "active|suspended|pending-reapproval"}
```
| Gate | local | community | remote |
|---|---|---|---|
| Confirm per call | on | on | on (even `--auto`, configurable default false) |
| Result cap | – | 1 MB | 64 KB |
| Toolset drift | warn | warn | **hard re-approval** |

## 4. Mechanisms
- **Toolset pinning:** `digest = sha256(canonical_json(sorted([(name, input_schema)])))`.
  Mismatch at session start → pending-reapproval, tools unregistered, diff shown. Never silent.
- **Namespace reservation:** reserved prefixes (`rad_`, `builtin_`, `jerry_`) rejected; remote tools only as `mcp__<server>__<name>`.
- **Result hygiene:** size-trim + UNTRUSTED envelope + provenance stamp (`call_id`, sha256) + injection-pattern flag counts.
- **Egress scoping:** executor refuses args containing vault material; egress_allowlist pinned at connect.
- **Transport:** https enforced non-local; localhost http only with `--insecure-local`; endpoint creds in Fernet vault only.
- **Audit:** `skills/<name>/audit.jsonl` — one line per call (ts, origin, hashes, duration, status, flags).

## 5. Phases
P1 pinning+namespace+audit → P2 scopes+arg guard → P3 allowlist+suspend → P4 desktop surfaces.

## 6. Non-goals
Sandboxing remote internals; Needle (stays OFF); content trust beyond UNTRUSTED flagging.
