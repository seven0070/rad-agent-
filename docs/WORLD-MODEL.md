# World model

`rad world` is RAD's picture of *your* world: entities, the relations between them, and — crucially
— **where each statement came from**. It is the third memory besides raw memories
([MEMORY.md](MEMORY.md)) and the user model (`rad user`).

```bash
rad world                      # entities + current relations with origin and confidence
rad world query <term>         # history included with --history
rad world add "Alice works at Acme"          # a stated fact (origin USER_PROVIDED)
rad world add "The gate host has network access" --assume
rad world confirm <from> <rel> <to>          # promote a disputed/assumed relation to fact
rad world retract <from> <rel> <to>          # keep it as history, stop treating it as true
rad world disputes             # relations whose sources disagree
rad world sync | cypher        # optional kuzu graph mirror (`pip install kuzu`)
```

## Origins — what RAD is allowed to believe

| origin | confidence | meaning |
|---|---|---|
| `USER_PROVIDED` | 0.9 | you said it; treated as fact |
| `OBSERVED` | 0.8 | a tool or a finished objective really saw it (artifacts that exist, files that were read) |
| `INFERRED` | 0.5 | derived from other statements |
| `MODEL_GENERATED` | 0.4 | a model wrote it — stored, never a fact on its own |
| `ASSUMPTION` | 0.3 | an explicit working assumption: listed separately, confirmed before use |

Assumptions exist so that a guess never quietly becomes truth: `rad world add … --assume` stores an
`ASSUMPTION` relation which `rad world show` displays as such, `assumptions()` lists it, and
`rad world confirm` upgrades it (with the confirmation recorded). The acceptance gate exercises
exactly this round trip.

## Structure

* **Entities** — name, kind (person/organization/project/tool/software/location/…), sources, origin,
  confidence, first-seen and last-seen counts.
* **Relations** — `from`, `rel`, `to`, `since`, `until`, origin, confidence, status. The relation
  vocabulary is open-ended (`rad world add` normalises spaces to underscores) with functional
  relations (`located_in`, `works_at`, `named`, `is`) superseding the previous value instead of
  deleting it — so "where did Alice work in March?" stays answerable through `--history`.
* **Status** — `current`, `superseded`, `disputed` (two sources disagree), `retracted`. Nothing is
  deleted; `retract` keeps the record and stops using it.

## How it fills itself

* `_learn` at the end of every objective records artifacts as `OBSERVED` facts (`Alive: created
  report.md`) — ground truth from the control plane, not from a model.
* `rad sleep` / chat-close mining extracts entities and relations from conversations and files
  (`rad world learn <file>`), with the model's output marked `MODEL_GENERATED`.
* `rad world context_block` injects only the relations relevant to the current turn, each tagged
  with its origin, so the prompt never presents a guess as a fact.

The JSON store is authoritative and always works offline; `kuzu` is an optional mirror for Cypher
queries (`rad world sync`, `rad world cypher "MATCH (n) RETURN n.name AS name LIMIT 5"`).
