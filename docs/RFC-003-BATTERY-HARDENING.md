# RFC-003: Battery Hardening — Evolution Integrity

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
