# Operations: doctor, storage, migrations, backups

## `rad doctor [--fix] [--offline] [--json]`
23 checks: python, home tree, secret-file permissions, config schema, storage schema, integrity,
workspace, DNA, policy (flags permissive defaults), memory (contradictions / unconsolidated),
objectives (needs-you / stale-running), agents, MCP skills, providers, local engines, MCP
handshake, browser, voice, crash recovery, benchmarks, sandbox (hard layer + workspace jail),
disk, helper binaries.

Each line is **READY / WARNING / OPTIONAL / ERROR**. Missing optional capabilities
(providers, local engines, MCP, voice) are OPTIONAL — they do not make RAD unusable and do
not fail the exit code. Report mode changes nothing. `--fix` only does what is safe: recreate dirs, chmod secrets, coerce
invalid config to defaults / drop unknown keys, run pending migrations (snapshot first), quarantine
corrupt files (`*.corrupt-<ts>`, never delete). Exit 1 only if anything is ERROR.

Provider HTTP **401 / 403 / 429** are **Class C** (G4-1 / v0.5.0): `rad doctor`
names the rotate-key / wait-quota / `rad use` pause when a chain exists;
`free_lock` never silently spends paid.

G4-2 / v0.5.1: `rad doctor` distinguishes **catalog-alive** (`GET /v1/models` 200)
from **inference-entitled** (`chat/completions`). A 403-chat pin is WARNING, not
READY. Last Class C (kind / status / next-steps / Retry-After) is persisted in
`~/.rad/provider_health.json`. `rad objective resume` live-gates Class C pauses
until an inference-entitled brain recovers — it does not silently re-burn the
same 403/429. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Storage schema & migrations (`rad/storage.py`)
`~/.rad/schema.json` records the schema version and every applied migration (name, time, summary).
Migrations are ordered, forward-only, idempotent, and each is preceded by a snapshot.
The CLI auto-migrates at startup (fresh homes are just stamped); `rad storage migrate --dry-run`
shows what would run.

| v | migration |
|---|---|
| 1 | memory files gain explicit origin/confidence/verification front-matter |
| 2 | DNA generations gain `history` (evolution provenance) |
| 3 | world-model entities/relations gain origin/confidence/status |

## Config validation
`validate_config()` checks type, range and enum for every key in `DEFAULTS` and flags unknown keys.
Used by `rad doctor`; RAD itself keeps tolerating bad values at runtime (defaults win) so a typo
never makes the CLI unusable.

## Integrity & failure behaviour
`rad storage check [--repair]` finds invalid JSON, leftover `.tmp` files from interrupted writes,
unparsable JSONL lines, objective dirs without `objective.json`, memory files without front-matter,
and too-open `keys/`. Every store (memory, world, user model, policy, agents, DNA, objectives) is
tested to degrade to empty/default on corrupt or wrong-shaped files instead of raising.

## Snapshots
`rad storage snapshot [--label x] [--include-keys]` → `~/.rad/backups/<ts>_<label>.tar.gz` (0600,
keys excluded by default, newest 10 kept). `rad storage restore --label <file>` takes a
pre-restore snapshot, refuses path-traversal members, never touches `keys/`.
