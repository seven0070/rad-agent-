# RAD Desktop 0.1.0-alpha

Desktop is a **face**, not a second control plane. Stack: Tauri 2 + React + TypeScript + Vite
talking to `rad serve` (docs/API.md). Source: `desktop/`.

```
RAD Desktop → local HTTP /v1/* → Session / Controller → Executor → Policy.decide → Tools
```

Jerry (chat) is the operator layer. Changing the authority profile uses `PUT /v1/authority`
(UNRESTRICTED requires `confirm_unrestricted`). The frontend cannot run shell, raise the
planner cap or tool budget, or turn Needle on.

Launch: `rad desktop` (prints the path; starts a built binary if present) or
`cd desktop && npm install && npm run tauri dev`.

See `desktop/README.md` for the security boundary.
