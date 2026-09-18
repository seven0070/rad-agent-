# Troubleshooting

Start here:

```bash
rad doctor            # 23 checks; READY / WARNING / OPTIONAL / ERROR; every non-READY line carries a fix
rad doctor --fix      # repairs only what is safe (dirs, permissions, config types, migrations, quarantine)
rad status            # objectives, memory, brain, jobs, schema on one screen
```

`rad doctor` exits 1 if anything is ERROR. OPTIONAL findings (no cloud key, no local engine,
no MCP skills, no voice) do not fail the command — RAD stays usable.

## "No brain available"

```
rad providers         # what RAD can see right now, and the fallback chain
rad keys add groq gsk_…      # or: export GROQ_API_KEY=…
rad install edge0            # Mac: local 35B/10B MoE, no key, no cost
rad provider add myserver --base-url http://127.0.0.1:1234/v1 --model local-model
```

A provider that is rate-limited or unreachable is skipped automatically and reported
(`rad [groq → openrouter] …`). If chain order surprises you, check `rad providers` — local engines
come first, then free tiers, then paid, and `free_lock = true` removes paid entirely.

## A vision task went to a model that cannot see

`rad providers` shows which models are known to accept images. RAD keeps a model whose *name*
suggests vision (e.g. `llama3.2-vision`, `qwen2.5-vl`) as a fallback rather than dropping it, and
records `vision_gap` in its selection trace when it cannot confirm image support. Fix it by pinning
a confirmed model: `rad use <provider>` or `rad config set vision_order <p1,p2>`.

## "BLOCKED by safety policy" / "DENIED by policy"

```bash
rad security                 # the enforcement layers and their settings
rad audit -n 20 --effect DENY # exactly which action, which capability, which rule
rad policy show              # capability defaults and rules
rad policy allow shell 'git status*'   # narrow the refusal to one command pattern
```

The **hard layer** (sudo, pipe-to-shell, `rm -rf /`, protected paths such as `~/.rad/keys`,
`~/.ssh`, private/metadata hosts, credentials in URLs) is code and cannot be allowed from settings.
Everything else is a rule you can change — and every decision is audited with its reason.

## The agent writes outside the workspace

That is by design: the workspace is a boundary. Point RAD at the project you mean:

```bash
rad workspace ~/code/myproject
rad config set allow_outside_workspace true    # only if you really want absolute paths allowed
```

## A task says NEEDS_USER / the objective stalls

```bash
rad inspect last              # which task, which check failed, how many attempts were used
rad trace last --kind RECOVERY_DECISION
rad objective resume <id>     # after you have resolved whatever it asked about
rad objective retry <id>      # re-open failed tasks and try a different decomposition
```

RAD stops rather than looping: retries are bounded by `max_attempts` and the retry budget, then it
replans, then it asks. `NEEDS_USER` means it refused to guess.

## "task completed without machine verification"

`accept_unverified_done` is `false` by default: a task whose checks could not run is not reported as
done. Either give the task machine-checkable criteria (file/json/shell checks) or accept the risk
explicitly with `rad config set accept_unverified_done true`.

## An objective is stuck after a crash

```bash
rad doctor                    # detects stale locks and interrupted objectives
rad objective list --active
rad inspect <id>              # checkpoints are restored on the next run
rad objective resume <id>
```

Checkpoints live in `~/.rad/objectives/<id>/checkpoint.json`; a lock whose pid is gone is treated as
stale (never as a live run), finished tasks are not re-run, and the audit trail shows what happened.

## Memory or state looks wrong / a file is corrupt

```bash
rad storage check --repair    # quarantines corrupt files as *.corrupt-<ts>, never deletes
rad storage snapshot --label before-fix
rad storage restore --label <file>
rad memory check              # contradictions, unconsolidated entries
rad world disputes
```

## MCP / skill problems

```bash
rad skills                    # connected skills and their approvals
rad skills audit              # inferred capabilities, drift, pinned fingerprint
rad skills approve <name> ask # a skill that drifted is downgraded to ask
rad drop <name> && rad connect <link>   # reconnect (handshake again)
```

A server that fails to handshake is reported with its stderr; nothing is registered on a failed
handshake, so a broken skill can never be silently called.

## Browser tools

```bash
rad doctor                    # reports whether playwright is installed
pip install playwright && playwright install chromium
```

Without playwright, `browser_screenshot` refuses (it will not claim a screenshot it did not take)
and navigation falls back to plain HTTP fetching. Local dev servers need the documented opt-in:
`rad config set allow_localhost_web true`; private/metadata addresses stay blocked regardless.

## Voice

`rad listen` / `rad say` need the engine binaries; `rad install` prints what it would fetch and
`rad doctor` reports which are missing. Everything else works without them.

## Nothing is slower than before, but a run behaved differently

```bash
rad regression compare        # differences between the last two regression runs
rad lab history -n 5          # per-scenario scores over time
rad replay last --verify      # re-run the recorded checks against the current workspace
```

`rad replay --verify` distinguishes "the artifact changed since the run" (`drift`) from "the run was
wrong", which is usually the difference between a code bug and an environment bug.
