# RAD Desktop 0.1.0-alpha

Tauri 2 + React + TypeScript + Vite desktop app with a **self-managed** RAD Python backend.

Desktop does **not** move the control plane into TypeScript. The only way to act is still:

Objective → Planner → Task Graph → Executor → `Policy.decide` → Tools

## Run

```bash
cd desktop
npm install
npm run tauri dev
```

Browser-only (no Tauri): `VITE_RAD_TOKEN=$(cat ~/.rad/api.token) npm run dev` then open the Vite URL.

`rad desktop` prints this path and launches a built binary if one exists.

## Standalone behavior

- The Tauri app can start RAD itself from bundled `rad/` sources.
- It no longer requires a separately installed `rad` Python package for the desktop flow.
- It still requires a local Python 3.9+ runtime unless you additionally bundle Python at packaging time.

## Security boundary

- Frontend talks only to `/v1/*` (chat, objectives, authority, settings, tasks, events).
- Tauri commands use a fixed `python3 -m rad serve` spawn against bundled RAD sources plus token/home reads.
- There is **no** arbitrary-shell command and no `tauri-plugin-shell`.
- UNRESTRICTED requires an explicit checkbox; it does not bypass Policy.decide.

## Not in this slice

Full Jerry personality, cloud sync, telemetry, SQLite, Needle-on-by-default, budget raises.
