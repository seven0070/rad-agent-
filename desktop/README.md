# RAD Desktop 1.0.1

Tauri 2 + React + TypeScript + Vite **surface** over the existing RAD Python HTTP API.

Desktop does **not** move the control plane into TypeScript. The only way to act is still:

```
User → Jerry → Session/Controller → Planner → Task graph → Executor → Policy.decide → Tools
       → Observer → Verifier → Recovery → COMPLETED | NEEDS_USER | FAILED
```

## Surfaces

Jerry · Objectives (Run / Pause / Resume / Recover / Cancel) · live execution · task graph ·
tool trace · verification · artifacts · provenance · usage · permissions · settings.

UNRESTRICTED requires an explicit checkbox. Needle stays off. Planner cap 16 / tool budget 60
cannot be raised from Desktop. A model `DONE:` is never shown as VERIFIED.

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

`rad desktop` prints this path and launches a built binary if one exists. Native signed
Windows/macOS/Linux installers are **not** produced by this commit.

## Security boundary

- Frontend talks only to `/v1/*` (chat, objectives, authority, settings, tasks, events, usage, why).
- Tauri commands are a fixed `python3 -m rad serve` spawn plus token/home reads.
- There is **no** arbitrary-shell command and no `tauri-plugin-shell`.
- Desktop Run is operator confirmation (ASK→ALLOW for that objective). DENY / hard / budget / scope stay.
