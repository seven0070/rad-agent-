#!/usr/bin/env python3
"""build_docs.py — writes the complete documentation pack to docs_staging/.
    python build_docs.py
Canonical repo copies. (Full rhetorical prose versions remain in chat history;
these carry 100% of the substance: laws, tables, threats, phases, evidence.)"""
from pathlib import Path

STAGE = Path(__file__).resolve().parent / "docs_staging"
FILES = {}

FILES["docs/JERRY-SPEC.md"] = '''# JERRY: Security Enforcement Layer

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
'''

FILES["docs/RFC-001-REMOTE-MCP-HARDENING.md"] = '''# RFC-001: Remote-MCP Tool Execution Hardening

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
'''

FILES["docs/RFC-002-MULTI-USER.md"] = '''# RFC-002: Multi-User Sessions

**Law:** memory/DNA are local files you own — ownership must survive shared machines.

## Problem
One `~/.rad/` is one mind. Shared machines leak memories, DNA, budgets, approvals.

## Design
```
~/.rad/users/<uid>/   # rad.json · keys/ · memory/ · dna/ · skills/ · papers/ · objectives/
~/.rad/shared/        # opt-in world edges (explicit adds only, origin=user)
```
- `RAD_USER=<uid>` / `rad who <uid>`; default `~/.rad` stays single-user (zero breakage).
- Recall never crosses uid boundaries. Skill approvals are per-user — sharing an install ≠ sharing approval.
- Budgets/cost per-uid. Vault per-uid. `rad why` never spans uids.

## Threats
MU-1 memory leak · MU-2 DNA contamination · MU-3 approval inheritance · MU-4 budget theft · MU-5 uid spoof (uid = OS username; session marker 0600).

## Phases
P1 namespace plumbing (old layouts still boot) · P2 per-user registry/vault/budget · P3 shared world-edges.
'''

FILES["docs/RFC-003-BATTERY-HARDENING.md"] = '''# RFC-003: Battery Hardening — Evolution Integrity

**Law:** nothing goes live without winning a benchmark battle — *and a battle
is only a law if the battery cannot be gamed.* False DONE = 0, at evolutionary
timescale too.

## 1. The contamination loop
```
sessions → corpus → training → candidate
    ▲                               │
    └── battery ◄─ same idiom ◄─────┘
```
Candidates selected for *battery-shape*, not capability. Reverse leak: battle
sessions mined by corpus put exam answers into training data.

## 2. Threats
EV-1 style overfitting · EV-2 reverse item leakage · EV-3 item reuse · EV-4 battery drift · EV-5 no negative control · EV-6 silent integrity failure.

## 3. Mechanisms
- **M1 Bidirectional firewall:** promotion-gate overlap check (n-gram/normalized,
  threshold 0.15 → blocked). Corpus miner excludes benchmark sessions; strip events `corpus_strip:battery_material`.
- **M2 Fresh items from lineage seeds:** `seed_K = sha256(parent_gen ‖ K ‖ battery_version)`;
  deterministic backward, unpredictable forward; rotation after N battles (event, never silent edit);
  generator context free of corpus, digest pinned.
- **M3 Canary Candidate:** crippled brain MUST LOSE by margin. Wins → `BATTERY_INTEGRITY_FAIL`,
  promotion + release hard-blocked. The "no canary touched" ethic aimed at the battery itself.
- **M4 Promotion record pinning:** candidate hashes, parent gen, battery version+seed+item hashes+
  generator digest, scores, contamination verdict, canary verdict, decision. `rad why brain` reads the chain.

## 4. Evidence (disk-only)
E-01 canary must lose · E-02 contamination block · E-03 generation gap (item-hash disjoint) ·
E-04 re-audit byte-reproducible · E-05 rotation retired events · E-06 determinism sha-equal ·
E-07 honest INTEGRITY_FAIL · E-08 reverse firewall (zero battery items in export).

## 5. Phases
P1 reverse firewall · P2 pinning + `rad why brain` · P3 seeds+rotation+detector · P4 canary as battery release gate.
'''

FILES["docs/RFC-004-RESEARCH-FRONTIER.md"] = '''# RFC-004: The Research Frontier Loop

**Law:** nothing ships untested — *including ideas that arrive with a citation.*
Evolution gains its second input: humanity's published methods, not just Rad's own tail.

## Components
1. **Ingest** `rad paper add <url|arxiv-id>` — HTML-first (no PDF parsing), sha256-pinned to `~/.rad/papers/<slug>/`.
2. **Technique Cards** — quote-provenance extraction (every claim carries a verbatim quote,
   verified against paper text before acceptance; retry-with-feedback on failure). Type system:
   technique|benchmark|dataset|theory|survey — only technique/benchmark enter battles. COI flags:
   a paper proposing benchmark B is never validated on B.
3. **Technique Generations** — promotion protocol parallel to `rad brain`: paired battles
   (baseline vs candidate, identical seeds, disk-graded metrics with direction metadata),
   promote/rollback, pinned records.
4. **Replication Ledger** — claimed-vs-measured per paper; CONFIRMED / NOT_REPLICATED verdicts;
   append-only jsonl; `rad ledger export` = open replication dataset. Losses are data.

## Commands
`rad paper add|list|show|card|battle|ledger` · `rad techniques list|promote|rollback`

## Invariants
No technique ships untested · no claim without an exact quote on disk · no self-benchmark
validation (COI) · every battle lands in the ledger.

## Phases
P1 ingest+cards ✅(shipped) · P2 paired-battle harness ✅(shipped, hooks pending) ·
P3 generations + `rad why paper` · P4 ledger export as open dataset.
'''

FILES["docs/RFC-005-FEDERATION.md"] = '''# RFC-005: The Federation Layer — Verified Agent → Verified Web

**Laws:** graded on disk, never claims · verification independent · sovereignty — no agent governs another's internals.

## Primitives
| Primitive | Law |
|---|---|
| Evidence Bundle | signed disk-derived claims; a model sentence is never a claim |
| Challenge Round | B grades A's **artifacts** on B's machine, never A's internals |
| Cross-Ledger | append-only; reputation = verifications survived |

## Jerry Protocol wire format (v0)
`deny.v0` · `approve.v0` · `bundle.v0` · `challenge.v0` · `response.v0` · `verdict.v0`

## Challenge Round
1. B→A challenge (task, seed, grader, artifact spec, deadline)
2. A runs under its own Jerry — B never governs A's internals
3. A→B response (artifact hashes + events + signed bundle)
4. B fetches artifacts, re-runs grader locally
5. B→cross-ledger verdict.v0

## Cross-audit (N4)
Bidirectional periodic challenges; symmetry is the defense. The regress gets
no top — it gets redundant (N5 Trustless Horizon: verification cheaper than
belief ⇒ anyone can re-check anything ⇒ nobody must check everything).

## Phases
P1 bundles ✅ · P2 challenge rounds (same machine) ✅ · P3 transport+key exchange · P4 cross-ledger merge.

## Non-goals
No blockchain (jsonl + signatures suffice). No identity/KYC (agents are keys). No internal-governance export.
'''

FILES["docs/RFC-006-HEARTH.md"] = '''# RFC-006: HEARTH — Everything Happens Inside

**Law:** Rad is the door, not the room — HEARTH makes the room livable without
the door, never removes the door. **Added law:** sovereignty is measured, never assumed.

## The Sovereign Loop
`INGEST → UNDERSTAND → PLAN → EXECUTE → VERIFY → DELIVER → SLEEP → EVOLVE`
Every stage has an internal implementation. Externals exist only at five
declared PORTS — explicit, metered, optional.

## The Five Ports
| Port | Internal default | External opt-in | Meter |
|---|---|---|---|
| P1 Cognition | Edge0/Ollama | free-first cloud chain | P1_cognition_cloud |
| P2 Knowledge | corpus+world model+papers | browse/search | P2_knowledge_web |
| P3 Skills | self-fabricated MCP tools | rad connect clones | P3_skill_clone |
| P4 Compute | local MLX/PEFT | rented GPU | P4_train_cloud |
| P5 Backup | local snapshots | Drive sync | P5_drive_sync |

Port calls are never silent — every call writes its metering event.

## Self-Fabrication
No tool for the task → brain drafts MCP tool → Jerry gates it EXACTLY like a
foreign skill (handshake, approval, namespace — zero shortcuts for homegrown)
→ registered, usable offline. Fabricated tools are battle-eligible too.

## Cold Start
`rad bootstrap --sovereign`: one local wheel + one local model file → full loop, zero network.

## Sovereignty Score
`internal_ratio = fully-internal objectives / total` (rolling, from events only).
`--cost` prints the measured benchmark delta of closing each port
(the Sovereignty Curve — measured, never asserted). Cloud-routed tasks are
NOT sovereign: capability borrowed is not capability owned.

## Threats
SV-1 silent dependency creep → metering · SV-2 self-made smuggle → same gates ·
SV-3 sovereignty theater → events-only scoring · SV-4 hidden degradation → NEEDS_USER honesty ·
SV-5 cold-start forces network → bootstrap pack.

## Evidence
SV-E1 metering exists · SV-E2 zero-port objective · SV-E3 ungated self-made rejected ·
SV-E4 fabricated tools battle before promotion · SV-E5 offline honesty · SV-E6 score reproducible.

## Phases
P1 auditor ✅ · P2 port metering hooks · P3 self-fabrication · P4 cold-start · P5 sovereign evolution.
'''

FILES["CONTRIBUTIONS.md"] = '''# Contributions — Manifest & State

External AI-assisted design contribution, integrated under the project's own laws.

## SHIPPED (verified on-machine)
| Phase | Commit | Contents | Checks |
|---|---|---|---|
| P1 | f69323d | rad/papers/ (ingest, cards, battle, ledger, extract) · memory/strength.py · verify_contrib.py | 5/5 |
| P2 | db1058c | evolution/ (contamination, canary) · security/toolset_pin · control/verifier_checks · why/lineage · world/temporal · sovereignty/audit | 14/14 |

## SHIPPED (P3)
| Phase | Commit | Contents | Checks |
|---|---|---|---|
| P3 | (this commit) | routing/relay · federation/challenge · sovereignty/costcurve · tools/scenario_runner · 28-scenario pack · verify_contrib3.py | 13/13 |

## DOCS
docs/RFC-001..006 · docs/JERRY-SPEC.md — canonical copies.

## State vocabulary
PROPOSED → ATTACHED → VERIFIED → INTEGRATED → SHIPPED

## Integration hooks (VERIFIED → INTEGRATED), live signatures
| Hook | Live signature | Adapter |
|---|---|---|
| canary.battery_fn | `CapabilityBattery(home).run(provider=, model=) -> {"score": ...}` | wrap config→(provider,model); return {"score": report["score"]} |
| battle.execute_fn | `Executor(home).execute_task(obj_id, task, context, tools) -> Observation` | map Observation.status/artifacts → grader_result |
| extract.brain_fn | `BrainRouter(home).complete(prompt, system_prompt=..., ...) -> str` | direct one-liner |
| pipeline gate | call `canary.assert_pipeline_clear()` before any promote | one line in promote path |
| promote gate | run `contamination.overlap_score()` before `brain promote` | one line |
'''

def main():
    written = []
    for rel, content in FILES.items():
        p = STAGE / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.lstrip("\n"), encoding="utf-8")
        written.append(rel)
    print(f"[docs] {len(written)} files written to {STAGE}")
    for w in written:
        print(f"  + {w}")
    print("Attach: copy docs/ -> repo docs/ ; CONTRIBUTIONS.md -> repo root")

if __name__ == "__main__":
    main()
