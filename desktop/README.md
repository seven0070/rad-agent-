# RAD Desktop 0.1.0-alpha

Tauri 2 + React + TypeScript + Vite **surface** over the existing RAD Python HTTP API.

Desktop does **not** move the control plane into TypeScript. The only way to act is still:

Objective → Planner → Task Graph → Executor → `Policy.decide` → Tools

## Run

```bash
# terminal 1 — optional; the app can spawn this itself
rad serve

# terminal 2
cd desktop
npm install
npm run tauri dev
```

Browser-only (no Tauri): `VITE_RAD_TOKEN=$(cat ~/.rad/api.token) npm run dev` then open the Vite URL.

`rad desktop` prints this path and launches a built binary if one exists.

## Security boundary

- Frontend talks only to `/v1/*` (chat, objectives, authority, settings, tasks, events).
- Tauri commands are a fixed `python3 -m rad serve` spawn plus token/home reads.
- There is **no** arbitrary-shell command and no `tauri-plugin-shell`.
- UNRESTRICTED requires an explicit checkbox; it does not bypass Policy.decide.

## Not in this slice

Full Jerry personality, cloud sync, telemetry, SQLite, Needle-on-by-default, budget raises.
