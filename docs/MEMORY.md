# Memory model (v0.2)

RAD keeps four stores, all plain files under `~/.rad`, all carrying **provenance**:

| store | file(s) | what |
|---|---|---|
| short-term | `memory/short/<day>.md` | raw session log, consolidated by `rad sleep` |
| long-term | `memory/long/{episodic,semantic,procedural}/*.md` | one markdown file per memory with front-matter |
| user model | `user.json` | structured beliefs about *you*: preferences, goals, projects, constraints, communication |
| world model | `world/graph.json` | entities + relations about your world, with temporal validity |

## Origin, confidence, verification
Every memory / user-fact / world-relation has:

* `origin` — `USER_PROVIDED` (0.9) · `OBSERVED` (0.8, a tool saw it) · `INFERRED` (0.5, heuristic) · `MODEL_GENERATED` (0.4, an LLM wrote it)
* `confidence` — starts from origin, rises on independent re-observation
* `verification` — `UNVERIFIED` · `VERIFIED` · `CONTRADICTED`
* `source` — where (chat, `obj_…/t_…`, `file:…`, URL)

Rules:
* A weaker origin never overwrites a stronger one (user model) — it is recorded as *disputed*.
* Near-duplicate from a stronger origin **upgrades** the memory; user/observed re-assertion marks it `VERIFIED`.
* **Contradictions** (negation flip, or same subject+verb with a different object) are linked on both sides;
  the less-trusted side is marked `CONTRADICTED`, ranks low in recall and decays 2–5× faster. Nothing is silently merged.
* Prompt injection labels every memory: `[semantic|user_provided,verified] …` and tells the model
  MODEL_GENERATED/INFERRED are hints, not facts.
* Decay half-life scales with importance and verification.

## What the control plane writes
On objective completion: an `OBSERVED` episodic memory (goal, tasks, retries, artifacts) and, only when
a recovery *actually worked* (retry → VERIFIED), an `OBSERVED` procedural lesson. Artifacts become `OBSERVED`
world entities with a `created` relation. Nothing the model merely claimed is stored as fact.

## World model temporality
Functional relations (`located_in`, `works_at`, `named`, `is`) supersede: a newer assertion from an
equal/stronger source closes the old one (`until`, `status: superseded`); a *weaker* source becomes
`disputed` instead. History is queryable (`--history`); `rad world confirm|retract` resolves.

## Commands
```
rad memory                      # layers + contradiction count
rad memory conflicts            # list contradictions
rad memory verify|dispute|forget <id> · rad memory correct <id> <new text>
rad user                        # inspect; rad user set <section> <key> <value> · add · forget · reset
rad world disputes · rad world confirm|retract <from> <rel> <to> · rad world query <x> [--history]
```
