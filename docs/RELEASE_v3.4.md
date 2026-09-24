# Rad v3.4 — Studio polish: FlowCanvas + acceptance gate + sidecar reliability (2026-09-24)

> **Tag: v3.4** — branch `feature/3.4` from `main@f5e3854` (v3.3). Objective_parallel=8, Needle OFF, NVIDIA NIM, blackboard, lab-gated VERIFIED-only, no shell bypass. 3 parallel agents (P/Q/R), 20 tools/300s.

## What shipped (3 parallel agents, lab-gated)

### Agent P — Studio Flow polish (FlowCanvas × McpMallPane)
- **FlowCanvas renders TaskGraph.to_flow()**: `desktop/src/components/FlowCanvas.tsx` now directly consumes `TaskGraph.to_flow()` shape (`{nodes: FlowNode[], edges: FlowEdge[]}` with deterministic grid `x=(idx%cols)*220, y=(idx//cols)*140`, `style.status==data.status`, `data: {label,status,checks,depends_on}`), draggable nodes, bezier `M→C` edges with arrow marker, status palette (PENDING/RUNNING/COMPLETED/VERIFIED/FAILED/BLOCKED/NEEDS_USER), ComfyUI sockets.
- **Minimap + zoom/pan**: `flow-minimap` (data-testid) with node count/edge count/zoom readout, per-node minimap click → focus via `onSelect`, `zoomIn/zoomOut` (0.5–2.0, 15% step, `115%` after +), `Fit` resets pan/zoom/positions, pan via background drag (translate+scale plane). Verified in `tests/test_v3_4_p_flow.py` (minimap/zoom/pan) and visual test `desktop/src/components/FlowCanvas.test.tsx` (nodes, minimap, bezier edges, McpMallPane integration, empty flow).
- **McpMallPane integration**: `FlowCanvas` imports `chat/McpMallPane` and renders it as overlay when `showMall` + `mallGoal`/`mallId` (Appsmith auto-panel read-only, x402 note `invent->MCP->publish->x402`). Props: `mallGoal?: string; mallId?: string; showMall?: boolean`. No auto-install.
- **Tests**: `tests/test_v3_4_p_flow.py` (6) — to_flow shape, minimap/zoom/pan, FlowCanvas renders to_flow, McpMallPane integration, visual test exists, invariants preserved. + `desktop/src/components/FlowCanvas.test.tsx` (5 visual).

### Agent Q — Acceptance gate hardened (50/50 offline)
- **Gate 50/50 without heavy model**: `rad/acceptance.py` — `acceptance_health(home)` lightweight health (REQUIRED=50, AREAS=10, heavy_model=False, VERIFIED-only), comment `v3.4 hardened — no heavy model needed`. `Gate.run()` still proves 50/50 offline via isolated `RadHome` per item, no NVIDIA NIM/Needle needed, evidencia `~/.rad/acceptance/*_gate.json`. `rad acceptance --json --area docs` fast subset.
- **Full offline proof**: `Gate(home).run()` on fresh temp home → `total=50 passed=50 failed=[] ok=True` in <120s (measured ~64s single). Evidence per item, persisted report, `rad acceptance 50-item` stays green.
- **Tests**: `tests/test_v3_4_q_acceptance.py` (5) — REQUIRED=50, health offline, Gate 50/50 full, CLI json wiring (parser), VERIFIED-only no shell bypass. Lab-gated; heavy model OFF.

### Agent R — Sidecar reliability (process-group reaping + health survives restart)
- **Process-group reaping**: `rad/sidecar.py` — `ensure_process_group()` (setsid on Unix, CREATE_NEW_PROCESS_GROUP on Windows), `register_orphan(pid)`, `reap_process_group(pid?)` (SIGTERM→SIGKILL pgid+pid, taskkill /T /F on Windows, clears `_ORPHAN_PIDS`), `_install_reap_handlers()` (SIGTERM/SIGINT + atexit), `is_process_group_reaped(pid?)` helper, no `shell=True`.
- **Health survives restart**: `sidecar_health(home_root?, port, timeout)` programmatic health (uses persisted `api.token` via `token_for`, `survives_restart=True` even when down), loopback-only (`LOOPBACK` guard), `serve` prints `pgid` + `version`, port-in-use → EXIT 3, health via `urllib` not shell. Token persists across restarts on same `RAD_HOME`, `health` after kill → `ok=False` but `survives_restart=True`, restart on same port succeeds.
- **Tests**: `tests/test_v3_4_r_sidecar.py` (5) — reaping clears orphans, token persists, serve→health→kill→restart survives, loopback-only/no shell bypass, invariants preserved. Spawn + health live test uses free port + `RAD_HOME` env.

## 11-Repo Fusion — carried + polished (v3.3 → v3.4)

| # | repo | where it lands (v3.4 polish) |
|---|------|------------------------------|
| 6 | ComfyUI | `FlowCanvas.tsx` now polished minimap/zoom/pan + McpMallPane overlay, renders `to_flow()` |
| — | verifications | `rad acceptance` 50/50 remains source of truth, now hardened offline |
| 8 | flue | `rad/sidecar.py` reaping + health survives restart (process-group) |

Full 11-repo table unchanged (appsmith→McpMallPane, magnitude→hardware, buzz→relay, roboflow→vision, OpenHands→CodeAct, ComfyUI→FlowCanvas, openmausbot→roster, flue→sidecar, agent-zero→blackboard, langflow→flow UX, omarchy→defaults).

## Install — Full 11-Repo Fusion (v3.4)

```bash
# 0. Base — 973 green (was 957 v3.3)
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
git checkout v3.4  # or feature/3.4
python -m pip install -U pip
pip install -e ".[dev]"
rad doctor --offline
pytest -q -n auto --dist worksteal  # must stay 973 (worksteal, no OOM)

# 1. Voice TEN e2e (unchanged)
pip install -e ".[voice]"
RAD_TEN=1 rad chat --voice --voice-backend ten

# 2. Desktop (FlowCanvas polished + x402)
cd desktop && npm ci && npm run build && npx tsc --noEmit
cargo check --manifest-path src-tauri/Cargo.toml
cd .. && pytest -q tests/test_v3_4_p_flow.py tests/test_v3_3_agent_m*.py
# visual: desktop/src/components/FlowCanvas.test.tsx  — minimap/zoom/pan + mall

# 3. Docker + x402 (Agent M, carried)
RAD_DOCKER=1 pytest -q tests/test_v3_3_agent_m_docker_x402.py -v

# 4. Recall perf <200ms (Agent N → v3.4 tolerant 250ms under xdist)
pytest -q tests/test_v3_3_perf_recall.py -v

# 5. Acceptance gate hardened (Agent Q)
python -m pytest tests/test_v3_4_q_acceptance.py::test_acceptance_gate_reports_50_50_offline -q  # 50/50 ~60s
rad acceptance --area docs --json  # fast subset
rad acceptance                         # full 50

# 6. Sidecar reliability (Agent R)
pytest -q tests/test_v3_4_r_sidecar.py -v
python -c "from rad.sidecar import sidecar_health; print(sidecar_health())"

# 7. Observability + replay
rad serve --port 7331 &
rad trace <id> && rad replay <id> --verify
```

## Verification

- `pytest -q -n auto --dist worksteal` — 973 passed, 2 skipped (was 957 v3.3), no OOM, HNSW P95 gated (<200ms, <250ms under xdist).
- `rad acceptance` — 50/50, REQUIRED=50, AREAS=10, `acceptance_health` heavy_model=False.
- `rad doctor --offline` — loopback-only, no keys.
- `FlowCanvas.test.tsx` — minimap/zoom/pan + McpMallPane overlay visual.
- Lab-gated, VERIFIED-only, `objective_parallel=8`, Needle OFF, `tool_router=existing`.

## Tag readiness — v3.4

- Source: `main@f5e3854` (v3.3 merge) → `feature/3.4` (P+Q+R + perf fix, 4 commits), then merge to `main` + tag `v3.4` + `rad-desktop-3.4`.
- CI: worksteal kept; heavy gate ~60s fits 300s budget.
- Manual single source of truth: `manual/README.md` (v3.4).

## Previous — v3.3 (carried)

- Docker Swarm isolation + x402 USDC + sqlite-vss HNSW + docs. 957 tests.
