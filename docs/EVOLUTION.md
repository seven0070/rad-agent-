# Gated evolution (`rad/evolution.py`)

RAD may change **how it behaves**, never **what it is made of**. Both halves are enforced in code.

## The evolvable surface (whitelist, `validate()`)
| surface | fields | limits |
|---|---|---|
| DNA | `persona` (≤1500 chars), `style` (≤12 short strings), `lessons` (≤50) | may not mention/weaken core rules, untrusted-data handling, confirmations, verification |
| config | `plan_infer_done`, `objective_parallel` (1–4), `accept_unverified_done` | values range-checked |

Everything else — code, `policy.json`, keys, `auto`, `allow_outside_workspace`, `free_lock`, the hard
layer — is *not* a surface. A change-set naming them is rejected before anything runs. Even the
explicit human override (`--force`) goes through the whitelist.

## Pipeline
```
propose ──► stage (sandbox copy of ~/.rad, real home untouched)
        ──► evaluate (lab suite on baseline home AND sandbox)
        ──► gate: safety 1.0, honesty 1.0, no per-scenario regression, no score loss
        ──► promote (new DNA generation whose history note carries the lab labels + deltas)
              │  or reject (reason kept)
              └─ rollback (DNA → parent generation, config → recorded 'from')
verify_current: re-run the lab on the live home; auto-rollback the last promotion if the floors fail
```
Every step is appended to `~/.rad/evolution/log.jsonl`; candidates live in `evolution/candidates/`.

## Sources of candidates
* `rad evolve <direction>` — the existing Evolver rewrite (LLM or deterministic) captured as a
  change-set instead of written directly.
* `rad evolve from-lab [label]` — deterministic proposals derived from lab evidence
  (dishonest runs → verification lesson; injected runs → data-not-instructions lesson;
  unverified successes → `accept_unverified_done=false`).

## Commands
```
rad evolve <direction>              propose → sandbox → lab gate → promote/reject
rad evolve list | show <id> | log
rad evolve approve <id> [--force]   promote a gate-passed (or, with --force, UNGATED) candidate
rad evolve reject <id> [why] · rad evolve rollback <id>
rad evolve verify                   re-run the gate on the live home (auto-rollback on failure)
rad evolve from-lab [label]
rad evolve <direction> --unsafe-direct   old ungated behaviour, logged as UNGATED
```
Config: `evolution_require_approval` (gate + human), `evolution_suite` (default `smoke`).

## Honest limits
The gate is only as good as the lab suite; a 4-scenario smoke suite catches gross regressions
(dishonesty, unsafe behaviour), not subtle style drift. Use `evolution_suite: all` for anything
important. Without a brain the gate cannot run, so candidates are saved, not applied.
