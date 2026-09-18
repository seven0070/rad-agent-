# Migration, upgrade, backup and rollback

RAD keeps state as plain files under `~/.rad`. That makes upgrades boring on purpose: nothing needs
a database server, and every change is a forward-only, idempotent migration that snapshots first.

## Upgrading RAD

```bash
git pull && pip install -e .        # or: pip install -U rad-agent
rad doctor                          # migrations run at startup; doctor confirms the schema
rad version                         # CLI version; `rad storage status` shows the schema version
```

The CLI stamps a fresh home with the current schema; an older home is migrated on first use
(`rad storage migrate --dry-run` shows exactly what would run, before it runs).

## Schema migrations

`~/.rad/schema.json` records the version and every applied migration (name, time, summary).

| version | migration | why |
|---|---|---|
| 1 | memory files gain explicit origin/confidence/verification front-matter | memories became provenance-bearing in 2.0 |
| 2 | DNA generations gain `history` (evolution provenance) | lineage for gated evolution |
| 3 | world-model entities/relations gain origin/confidence/status | world model distinguishes fact / observation / inference / assumption |

Each migration is preceded by a snapshot (`~/.rad/backups/`), is idempotent, and quarantines
anything it cannot parse (`*.corrupt-<ts>`) instead of deleting it.

```bash
rad storage status
rad storage migrate --dry-run
rad storage migrate
rad storage check --repair
```

## Backup

```bash
rad storage snapshot --label pre-upgrade          # ~/.rad/backups/<ts>_pre-upgrade.tar.gz (0600)
rad storage snapshot --label full --include-keys # only if you want the vault in the archive
rad storage list                                 # newest 10 snapshots are kept automatically
```

Keys are excluded by default. The archive is a tar.gz of the home directory with the same layout, so
it is also a portable copy.

## Restore

```bash
rad storage restore --label 20260918-120000_pre-upgrade
```

Restoring takes a pre-restore snapshot, refuses path-traversal members, and never touches `keys/`
(so a restored state cannot silently change your credentials).

## Rollback of RAD's own behaviour

Two things change behaviour, and both are versioned and reversible:

```bash
rad brain rollback <id>        # restore a previous DNA generation (behaviour/config/prompts)
rad evolve rollback <id>       # roll back an applied evolution candidate
rad evolve list                # generations with their benchmark, security and approval records
```

No candidate is promoted without the sandbox → benchmark → regression → security → approval gate,
and every promotion keeps the previous state as a rollback target.

## Moving to another machine

```bash
rad storage snapshot --label move --include-keys
# copy the archive, then on the new machine:
rad storage restore --label <file>
```

The workspace path is the only machine-specific setting; set it again with `rad workspace <dir>`
(or leave it and RAD recreates `~/.rad/workspace`).

## Crash and state recovery

* `rad doctor` finds stale locks, interrupted objectives, invalid JSON, leftover `.tmp` writes and
  half-written JSONL lines.
* Objectives write a checkpoint after every task (`objective.json`, `tasks.json`,
  `checkpoint.json`); on the next run, a lock whose pid is gone is treated as stale, the checkpoint
  is restored and finished tasks are not re-run. The failure-recovery acceptance test performs
  exactly this crash/resume cycle and asserts the finished work survived.
* `rad replay <id> --verify` re-runs a past objective's checks against the current workspace so you
  can tell "the artifact drifted" from "the run was wrong".

## Compatibility promises

* **v1 commands keep working.** The v1 surface (chat, keys, providers, memory, user, world, sleep,
  doctor, serve, …) is preserved; the acceptance gate fails if a v1 command disappears.
* **State is readable.** Files are JSON/markdown with a documented layout
  ([INSTALLATION.md](INSTALLATION.md)); you can read, diff and version-control them yourself.
* **Nothing is mandatory infrastructure.** No database, no daemon, no service — the simplest
  install keeps working on a machine with no network and no key.
