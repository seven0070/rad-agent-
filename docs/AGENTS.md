# Agent runtime (`rad/agents.py`)

A sub-agent is **role prompt + capability set + budget**, executed through the normal brain
loop (`Session`) with a guarded `tool_runner`. Capabilities are enforced at the tool boundary,
not suggested in the prompt: a `reviewer` calling `write_file` gets `DENIED …` back and the
denial is recorded on the run.

| capability | tools |
|---|---|
| `fs.read` | read_file, list_dir |
| `fs.write` | write_file |
| `shell` | run_shell (and any unknown tool) |
| `web` | web_search, fetch_page |
| `vision` | see_image |
| `agents.spawn` | spawn_agents |
| `mcp` | every `mcp__*` tool |

Built-ins: planner, researcher (read+web), coder (read+write+shell), tester (read+shell),
reviewer / analyst / security (read only), writer (read+write). Override or add with
`rad agents define <id> --caps … --prompt … --tools N --seconds S`; definitions live in
`~/.rad/agents/registry.json`, runs in `~/.rad/agents/runs/`.

**Blackboard.** Parallel agents on one objective share `~/.rad/agents/blackboard/<scope>.json`;
each note carries author + evidence sources and is injected into later agents' prompts as
*claims*, not facts.

**Grounded review as a check.** The planner may add `agent_review {criteria}` to a task. The
reviewer runs read-only; its verdict counts only if it actually read something
(`tool_calls > 0` or `checked` non-empty), is stored with `machine: false`, and **can never make a
task `VERIFIED` on its own** — it can only fail one. Pair it with a file/shell check.

`rad team run … --tools` and the `spawn_agents` tool (`tools: true`) route through this runtime;
without the flag the original prompt-only specialists are used.

Not done: per-agent sandboxes / network policy (Phase 6), agent-to-agent messaging beyond the
blackboard, per-agent memory isolation (`memory_scope` is recorded but not enforced yet).
