# RAD Web UI — Rust + JavaScript/TypeScript Interface

A first-class, browser-accessible Web UI for the RAD Agent control plane, powered by a compiled Rust daemon (`rad-web`) and a responsive React/TypeScript frontend.

---

## 🚀 Quickstart

### 1. Launch with the CLI (One Command)
Start the agent control plane and open the Web UI directly in your default browser:

```bash
rad web
```

- **Frontend URL**: `http://127.0.0.1:3000`
- **Agent API Proxy**: `http://127.0.0.1:3000/v1/*` → forward to `http://127.0.0.1:7331`
- **Auto-Authentication**: Automatically reads `~/.rad/api.token` and authenticates requests.

Options:
```bash
rad web --port 3000        # Custom web interface port
rad web --api-port 7331    # Target RAD backend port
rad web --no-open          # Do not automatically launch the browser
```

---

## 🏛️ Architecture: Rust + JS Duality

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Browser (Client)                     │
│  Chrome / Firefox / Edge / Safari / Tablet / Mobile Browser │
│                                                             │
│  React 18 + TypeScript + Vite UI                            │
│  • Progressive Disclosure: Feed, Pills, Inspector Drawer    │
│  • 4 Workspaces: Workbench, Runs & Tasks, Ledger, Vitals    │
│  • In-browser Connection Manager (localStorage cache)       │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Rust Web Server (`rad-web`)                 │
│                 crates/rad-web/src/main.rs                  │
│                                                             │
│  • High-performance HTTP server (1.2 MB compiled binary)    │
│  • Static asset hosting for desktop/dist/                   │
│  • Reverse proxy for /v1/* and /api/*                       │
│  • Automatic Bearer Token injection from ~/.rad/api.token    │
│  • CORS & preflight header termination                      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Loopback HTTP
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                RAD Agent Control Plane                      │
│                rad serve (--port 7331)                      │
│                                                             │
│  • Python Controller, Policy, & Execution Engine            │
│  • Machine verification & artifact ledger                   │
│  • Unrestricted / Standard / Safe authority gates           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Building & Running Standalone

### Build the Rust Web Server
```bash
cargo build --release --manifest-path crates/rad-web/Cargo.toml
# Binary produced: crates/rad-web/target/release/rad-web[.exe]
```

### Build the Web Frontend Assets
```bash
cd desktop
npm run build:web
```

### Run the Rust Daemon Directly
```bash
./crates/rad-web/target/release/rad-web --port 3000 --api-port 7331
```

### Run in Vite Dev Mode (Hot Reload)
```bash
cd desktop
npm run dev
# Open http://localhost:5173
```

When connecting via Vite dev mode, click the **🌐 Web UI** status badge in the bottom bar or enter your API URL (`http://127.0.0.1:7331`) and token (`~/.rad/api.token`) in the Connection Modal.
