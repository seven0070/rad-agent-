# RFC-004: The Research Frontier Loop

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
