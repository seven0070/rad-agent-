# RFC-005: The Federation Layer — Verified Agent → Verified Web

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
