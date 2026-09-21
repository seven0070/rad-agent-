# JERRY: Security Enforcement Layer

**Law:** Jerry is not a model, not a prompt, not a suggestion. Jerry is code.
Nothing executes unless Jerry says yes. Jerry never reads a model's output as
justification — Jerry reads the *world*: files, args, events, digests.

## Identity
The enforcement membrane between capability and action. Every tool call,
shell command, file write, and network request passes through exactly one
Jerry. No second path.

## The Eight Gates (ordered — first deny wins)

| # | Gate | Enforces | Evidence (audit.jsonl) |
|---|------|----------|------------------------|
| 1 | Identity | caller tier: objective / chat / plan / skill | origin |
| 2 | Capability | tool registered, namespace-clean (`mcp__<srv>__<n>`), no reserved prefixes | tool + verdict |
| 3 | Path | workspace sandbox; traversal → deny | path + verdict |
| 4 | Command | hard blocklist (sudo, rm -rf /, pipes-to-sh, dd) — **not bypassable by --auto, ever** | pattern class |
| 5 | Args | vault material never leaves; size caps | args_sha256 only |
| 6 | Network | egress_allowlist per skill; https-only non-local | domain + verdict |
| 7 | Budget | tool/model calls, retries — exhaustion ⇒ honest NEEDS_USER/FAILED, never fake DONE | counters |
| 8 | Result | UNTRUSTED envelope, provenance stamp, size trim, injection flagging | flags[] |

## Behavioral contracts
1. **Deny is data.** Structured, readable by the model, non-appealable.
2. **Fail closed.** Unknown edge = deny. No "probably fine."
3. **Honest by construction.** Jerry verdicts are the disk evidence graders read.
4. **The mouse is part of Jerry.** Adversarial test suite; escape rate target 0.

## Amendment: The Open Gate
Open + gatekept = glass-box enforcement (Kerckhoffs). Rules public,
enforcement absolute. Trust topology: model reads all/writes nothing/bypasses
never; Jerry enforces only; human writes policy via audited warden path only.

**Two-tier denials** (anti probe-oracle):
- to the model: coarse classes only — `{"gate":"command","class":"policy","hint":"blocked by rule, not capability"}`
- to audit.jsonl: full pattern, exact match, origin, ts.

**Probe economics:** N denies in a window → `probe_suspected`; budget
multiplier ×3 per further call. Reconnaissance writes its own arrest record.

## Non-goals
Jerry does not judge content quality (Verifier's job); does not trust skill
authors (handshake's job); never asks the model for permission to enforce.
