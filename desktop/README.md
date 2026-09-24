# RAD Desktop 0.2.0-alpha

Tauri 2 (Rust) + React + TypeScript + Vite **surface** over the existing RAD control
plane. The packaged app bundles the Python core as a `rad-backend` sidecar (Tauri
`bundle.externalBin`, one frozen binary per platform triple) and owns its lifecycle —
a user never runs `rad serve` or installs Python/Node.

Desktop does **not** move the control plane into TypeScript. The only way to act is still:

```
Objective → Planner → Task Graph → Executor → Policy.decide → Tools
```

and the browser never holds authoritative state (no localStorage/sessionStorage/indexedDB;
no authority stored locally; status/verification come from `/v1/*` only).

## Pages

Jerry · Objectives · Active Run · Tasks (live graph from backend deps) · Trace ·
Verification · Artifacts · Authority · Memory · Settings.

## Run (development)

```bash
cd desktop
npm install
# the shell's dev fallback runs `python -m rad serve` when no sidecar is bundled:
RAD_PYTHON=../.venv-dev/bin/python npm run tauri dev
npm run build          # tsc -b && vite build (strict)
```

Browser-only (no Tauri): `VITE_RAD_TOKEN=$(cat ~/.rad/api.token) npm run dev`, with a
`rad serve` running on the printed port.

## Build the sidecar

```bash
pip install -e ".[sidecar]"
python -m sidecar.build                     # this platform (isolated venv)
python -m sidecar.build --triple x86_64-pc-windows-msvc   # CI: pinned per runner
```

Output: `src-tauri/binaries/rad-backend-<triple>[.exe]` — where `bundle.externalBin`
(`binaries/rad-backend`) expects it. PyInstaller does not cross-compile; CI freezes one
binary per native OS and runs a live smoke (serve → `/v1/health` with the issued token →
port-conflict exit 3).

## Security boundary

- The frontend talks only to typed `/v1/*` routes (`src/api.ts` ROUTES); there is no
  shell/tools/exec route in the HTTP API or the client.
- The Tauri shell spawns the sidecar with a **fixed argv**
  (`serve --host 127.0.0.1 --port <n> [--home <dir>]`) — no user string ever reaches a
  command line; no `tauri-plugin-shell`/`fs`; capabilities are limited to the seven
  `backend_*` lifecycle commands (`capabilities/default.json`).
- The sidecar binds loopback only and requires the Bearer token (`0600` at
  `~/.rad/api.token`). Stale/foreign listeners on the port are probed and reported, never
  killed silently; an unhealthy start is killed and the backend log tail is shown.
- UNRESTRICTED requires the explicit authorization checkbox (`confirm_unrestricted`) and
  does not bypass `Policy.decide`, hard blocks, budgets, audit or verification.

## Not in this slice

Cloud sync, telemetry, SQLite, Needle-on-by-default, budget raises, arbitrary extra
capabilities. The full status + what-is-tested-here vs CI-owned: `docs/DESKTOP.md`.
