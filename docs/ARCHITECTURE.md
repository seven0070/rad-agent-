# RAD architecture (v0.2)

```
                 ┌──────────── interfaces ────────────┐
                 │ CLI (rad …)   REPL   HTTP API      │  docs/API.md
                 └──────┬───────────┬──────────┬──────┘
                        ▼           ▼          ▼
┌─────────────── control plane  rad/control/ ────────────────┐   docs/CONTROL-PLANE.md
│ objectives → planner → task graph → executor → observer    │
│ → verifier (machine checks; llm/agent review never VERIFIED│
│   alone) → recovery (bounded) → checkpoints/resume → events│
└──────┬──────────────┬───────────────┬──────────────────────┘
       ▼              ▼               ▼
  Session/brain   agent runtime    tools  ── single policy gate ──►  docs/SECURITY.md
  (router,        rad/agents.py    rad/tools.py   rad/policy.py       hard layer · rules ·
   providers)     caps+budgets+    (fs/shell/web/  audit.jsonl        LIMITED · redaction
                  blackboard       mcp via skill manifests docs/SKILLS.md)
       │
       ▼
  memory 2.0 · user model · world model        docs/MEMORY.md
  (origin/confidence/verification, contradictions, temporal relations)

  evaluation  rad/lab.py   whole objectives in isolated homes, graded on disk   docs/LAB.md
  evolution   rad/evolution.py   whitelist → sandbox → lab gate → promote/rollback docs/EVOLUTION.md
  operations  rad/storage.py rad/doctor.py   schema+migrations, integrity, snapshots docs/OPERATIONS.md
```

## Invariants (each backed by tests)
1. **Nothing is VERIFIED without a passing machine check.** Model or reviewer opinions can fail a task, never pass it.
2. **One enforcement point.** Every tool call — REPL, control plane, sub-agent, MCP — passes `run_tool → Policy.decide`. The hard layer cannot be configured away; `--auto` only turns ASK into ALLOW.
3. **Explicit state.** Goals, tasks, retries, budgets, checkpoints, artifacts, verification, events, audit, memory provenance are files under `~/.rad`, replayable and inspectable (`rad trace/inspect/events/replay/why`).
4. **Provenance everywhere.** Memories, user facts, world relations carry origin + confidence + verification; contradictions are linked, not merged.
5. **Evolution cannot touch code.** Only persona/style/lessons and three config knobs; every change is sandboxed, lab-gated, recorded, reversible.
6. **Degrade, don't crash.** Corrupt state files quarantine (never delete); every store loads to defaults on garbage.

## State layout (`~/.rad`)
```
rad.json schema.json policy.json audit.jsonl user.json api.token
memory/{short,long/{episodic,semantic,procedural},archive}   world/graph.json   dna/gen*.json
objectives/<id>/{objective.json,tasks.json,events.jsonl,observations/,artifacts.json,checkpoints/}
agents/{registry.json,runs/,blackboard/}   skills/{registry.json,*.manifest.json}
lab/runs/   evolution/{candidates/,log.jsonl}   backups/   logs/api.jsonl   keys/ (0700)
```

## Known limits (honest)
No OS-level sandbox for shell; hard-block patterns are regexes. Lab suites are small and fixed.
Agent memory isolation is recorded, not enforced. Storage is files, not a DB (by design; migrations exist).
Optional Needle tool-router (`RAD_TOOL_ROUTER=needle`) may propose calls only; it is off by default and never sovereign.
