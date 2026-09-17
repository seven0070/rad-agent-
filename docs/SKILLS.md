# Skill manifests (`rad/skills.py`)

Every connected MCP skill gets a manifest at `~/.rad/skills/<name>.manifest.json`:

```json
{"name": "fsx", "trust": "local", "approval": "ask",
 "capabilities": ["fs.read", "fs.write", "shell"],
 "tools": {"read_file": ["fs.read"], "write_file": ["fs.write"], "run_command": ["shell"]},
 "declared": false, "pinned": "3f1c…"}
```

* **Per-tool capabilities** are declared (`rad skills declare <skill> <tool> fs.write`) or inferred
  from tool names. Unknown tools are treated as `shell`.
* **Enforcement** happens inside `run_tool`: an MCP tool call is gated for each of its effective
  capabilities (so a file-writing MCP tool is `fs.write`, a fetcher is `web`), plus the generic `mcp`
  gate unless the skill is approved `allow`. Policy rules can target MCP tools by name
  (`rad policy deny fs.write "mcp__fsx__*"`).
* **Approval** `allow | ask | deny | policy`. `deny` blocks every tool of the skill and is audited.
* **Drift pinning.** The tool list is fingerprinted when approved. If the skill later exposes
  different tools, `approval: allow` is downgraded to `ask`, the new tools are recorded under
  `drift`, and `rad skills audit` flags it until `rad skills approve` re-pins.

```
rad skills                      list with approval + caps
rad skills audit                flags: write/exec tools, inferred caps, drift, remote, allow-on-dangerous (exit 1 if any)
rad skills approve <name> [allow|ask|deny|policy]
rad skills declare <skill> <tool> <cap,cap>
rad skills manifest <name>
```
