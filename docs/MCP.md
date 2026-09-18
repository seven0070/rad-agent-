# MCP and skills

A **skill** is any tool provider RAD can call — an MCP server over stdio or HTTP, or a local
package. Skills are not a separate world: their tools appear as `mcp__<skill>__<tool>` and go
through the same capability gate, sandbox, budget and audit path as `run_shell` or `write_file`.

## Connect

```bash
rad connect <link-or-path>          # inspect, confirm, then register (rad connect --yes skips the prompt)
rad skills                          # list connected skills
rad skills audit                    # declared vs. actually-exposed tools, approvals, drift
rad skills approve <name> allow|ask|deny
rad skills declare <name> <tool> <cap,cap>   # pin a tool's capability instead of inferring it
rad skills manifest <name>          # the manifest for one skill
rad drop <name>                     # disconnect
```

`rad connect` detects the server's tools by handshaking with it, then writes a registry entry
(`~/.rad/skills/skills.json`) and a manifest (`~/.rad/skills/<name>.manifest.json`).

## What a manifest contains

```json
{
  "name": "probe", "description": "a probe skill", "version": "1.2.0",
  "transport": "stdio", "trust": "local",
  "capabilities": ["web"], "permissions": ["web"], "dependencies": ["httpx>=0.27"],
  "approval": "policy", "pinned": "359fd736dd2bc156",
  "security": {"approval": "policy", "trust": "local", "sandbox": "required",
               "credentials": "never shared", "network": "scoped by sandbox grants"},
  "tools": {"fetch_thing": ["web"]},
  "spec": [{"name": "fetch_thing", "description": "fetch it", "inputs": ["q"],
            "outputs": ["text"], "permissions": ["web"]}],
  "declared": false
}
```

* `capabilities`/`permissions` are **inferred from the tool names** unless the skill (or you)
  declares them — `rad skills audit` flags every inferred capability as a warning so the guess is
  visible instead of silent.
* `pinned` is a fingerprint of the tool list. When a server adds or changes tools, the manifest
  records the drift (`drift.from`, `drift.to`, `drift.new_tools`) and an `allow` approval is
  downgraded to `ask`: a skill cannot silently grow new powers.
* Credentials are never passed to a skill, and network egress stays scoped by the sandbox.

## Permissions and lifecycle

| layer | who decides |
|---|---|
| capability of the tool | `T`he tool name is mapped (`browser_*` → `browser`, unknown → `mcp`) |
| the skill's own caps | every cap the skill declares is gated individually, so a file-writing MCP tool needs `fs.write` |
| approval | `allow` (skill-level MCP ask waived) · `ask` (prompt per call) · `deny` (refused and audited) |
| policy | `rad policy` defaults and rules still apply on top |
| sandbox | an agent session can only narrow the envelope; MCP servers run with the extra env stripped |
| audit | every MCP call is written to `~/.rad/audit.jsonl` with capability, effect and reason |

## Example: a local stdio server

```python
# my_server.py — speaks JSON-RPC on stdin/stdout
import sys, json
def send(o): print(json.dumps(o), flush=True)
for line in sys.stdin:
    m = json.loads(line)
    if m.get("method") == "initialize":
        send({"jsonrpc": "2.0", "id": m["id"], "result": {"protocolVersion": "2025-03-26",
              "capabilities": {}, "serverInfo": {"name": "my", "version": "0"}}})
    elif m.get("method") == "tools/list":
        send({"jsonrpc": "2.0", "id": m["id"], "result": {"tools": [
            {"name": "echo", "description": "echo back",
             "inputSchema": {"type": "object", "properties": {"x": {"type": "string"}}}}]}})
```

```bash
rad connect ./my_server.py          # or: rad connect "python3 my_server.py"
rad skills audit
rad agents run researcher "use the echo tool"   # the tool is available as mcp__my__echo
```

The acceptance gate starts exactly such a server and calls `mcp__acceptance_probe__echo` through
the tool layer, asserting the result *and* the audit record — if MCP integration regresses, the gate
fails.
