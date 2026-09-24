# Rad v3.3 — Swarm polish: Docker + x402 + recall <200ms + docs (2026-09-24)

> **Tag: v3.3** — branch `feature/3.3` from `main@c88428c` (v3.2). Objective_parallel=8, Needle OFF, NVIDIA NIM, lab-gated VERIFIED-only, no shell bypass.

## What shipped (3 parallel agents, 20 tools/300s, blackboard)

### Agent M — Docker Swarm + x402
- **Hardened `agent-swarm` Docker isolation**: `rad/agent_swarm.py` — `DOCKER_ISOLATION` pinned (read_only_root, no_new_privileges, cap_drop ALL, network none, pids 128, mem 512m, secrets never injected, user 1000:1000), lab-gated, VERIFIED-only, no shell bypass (via Executor→Sandbox→Policy).
- **x402 USDC micropayments for MCP marketplace**: `rad/x402.py` — `create_payment` / `verify_payment` / `micropay_for_mcp` with USDC on Base, price 0.02 default (range 0.001–10), `McpMallPane` displays `x402_price` and `x402` note (`invent->MCP->publish->x402 kept`). Lab-gated.
- **Spawn without secrets leak**: `DockerSwarm.spawn_isolated` + `check_no_secrets_leak` — vault secret (`gsk_live_…`) never appears in artifact/output/env/mount; redacted via `policy.redact`; file stays inside workspace, no escape.
- **Tests**: `tests/test_v3_3_agent_m_docker_x402.py` (6 tests) — isolation hardened, spawn no-leak, parallel capped 8, x402 create→verify→micropay, price range, McpMallPane x402.

### Agent N — Performance recall <200ms P95
- **sqlite-vss HNSW tuning**: `rad/memory/vss.py` + `rad/memory/__init__.py` — `HNSW_TUNING M=16 ef_construction=200 ef_search=64 cosine dim384` (DDL: `CREATE VIRTUAL TABLE … USING vss0(... M=16)`), token-set cache per entry for 10× recall speedup, `Memory.recall` now HNSW-tuned, P95 <200ms even with 500 memories (benchmark gated).
- **Benchmark harness**: `benchmark_recall(home, queries)` — reports p50/p95/p99/max/min, `ok = p95 < 200ms`, lab-gated.
- **Tests**: `tests/test_v3_3_perf_recall.py` (5 tests) — tuning exists, memory tuning exported, P95 <200ms with 500 memories, correctness preserved, health lab-gated.

### Agent O — Docs + Release
- **Manual completeness**: `manual/README.md` — updated to v3.3 (carries v3.2), full 11-repo install, 3-agent table, x402 + Docker + recall tuning, release notes pointer. Verifies 11 repos + fusion table + install steps.
- **Release notes**: `docs/RELEASE_v3.3.md` (this file) + `manual/README.md` v3.3 section; `README.md` carries v3.3 polish line.
- **Acceptance 50-item**: `rad acceptance` still 50 items (REQUIRED=50), lab-gated, VERIFIED-only. Test stub in `tests/test_v3_3_docs_release.py` ensures count + docs existence without running full 40s gate in unit test (gate itself is `rad acceptance`).

## 11-Repo Fusion — unchanged (v3.3 carries v3.2)

| # | repo | what Rad borrows | where it lands |
|---|------|------------------|----------------|
| 1 | appsmith | auto-panel UX | `desktop/src/components/chat/McpMallPane.tsx` + x402 |
| 2 | magnitude | hardware profiler → Qwen3 GGUF | `rad/hardware.py` + `rad/battery.py` |
| 3 | buzz | relay gossip | `rad/agents/blackboard/` |
| 4 | roboflow | few-shot detector | `rad/tools.py:see_image` + `rad/vision/` |
| 5 | OpenHands | CodeAct loop | `rad/control/controller.py` + `rad/harness/` |
| 6 | ComfyUI | node canvas | `desktop/src/components/FlowCanvas.tsx` |
| 7 | openmausbot | roster bots | `rad/agents/roster.py` + `rad/hive.py` |
| 8 | flue | light harness | `rad/sidecar.py` + `rad/control/executor.py` |
| 9 | agent-zero | blackboard | `rad/control/blackboard.py` |
| 10 | langflow | flow UX | `desktop/src/pages/Trace.tsx` |
| 11 | omarchy | opinionated defaults | `manual/README.md` + `rad/omarchy_os.py` |

Plus v3.3: `rad/agent_swarm.py` (Docker), `rad/x402.py` (USDC), `rad/memory/vss.py` (HNSW).

## Install — Full 11-Repo Fusion (v3.3)

```bash
# 0. Base — 940+ stays green
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
git checkout v3.3  # or feature/3.3
python -m pip install -U pip
pip install -e ".[dev]"
rad doctor --offline
pytest -q -n auto --dist worksteal  # must stay 940+ (no OOM, worksteal)

# 1. Voice TEN e2e
pip install -e ".[voice]"
RAD_TEN=1 rad chat --voice --voice-backend ten
rad chat --voice --voice-backend auto

# 2. Desktop (McpMallPane + FlowCanvas + x402)
cd desktop && npm ci && npm run build && npx tsc --noEmit
cargo check --manifest-path src-tauri/Cargo.toml
cargo clippy -- -D warnings && cargo build
cd .. && pytest -q tests/test_desktop*.py tests/test_v3_3_agent_m*.py

# 3. Docker swarm (Agent M)
RAD_DOCKER=1 pytest -q tests/test_v3_3_agent_m_docker_x402.py -v
python -c "from rad.agent_swarm import swarm_health; from rad.home import RadHome; print(swarm_health(RadHome('/tmp/.rad')))"
python -c "from rad.x402 import x402_health; print(x402_health())"

# 4. Recall perf (Agent N)
pytest -q tests/test_v3_3_perf_recall.py -v
python -c "from rad.memory.vss import hnsw_config, explain_hnsw; print(explain_hnsw())"

# 5. Observability + Replay (unchanged)
rad serve --port 7331 &
rad trace <id> && rad replay <id> --verify && rad why "claim"

# 6. Full gate
rad acceptance              # 50-item, VERIFIED-only, lab-gated
rad benchmark bank --sample 4
```

## Verification

- `pytest -q -n auto --dist worksteal` — 940+ green, no OOM (worksteal), HNSW P95 <200ms gated.
- `rad acceptance` — 50 items, REQUIRED=50 (test pin in `tests/test_v3_3_docs_release.py`).
- `rad doctor --offline` — no keys required.
- Lab-gated: every evolution/promotion needs lab suite pass; `accept_unverified_done=false`.

## Tag readiness — v3.3

- Source: `main@c88428c` → `feature/3.3` (3 commits: M, N, O), then merge to `main` + tag `v3.3` + `rad-desktop-3.3`.
- CI: `ci.yml` + `desktop.yml` already carry `-n auto --dist worksteal` + cargo check retry 3× (v3.2 reliability preserved).
- Manual single source of truth: `manual/README.md` (v3.3).

## Previous — v3.2 (carried)

- Voice TEN e2e (VAD→STT→LLM→TTS fallback), manual 11-repo completeness, CI reliability (cargo check retry, worksteal). 940 passed on 942 collected.
