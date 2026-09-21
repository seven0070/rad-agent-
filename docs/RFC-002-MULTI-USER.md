# RFC-002: Multi-User Sessions

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
