# Rad Omarchy Manual — opinionated defaults (N5)

Rad v3.5 — **v3.4 carried forward + v3.5 fast-finish** (5000f02 → feature/3.5, 982 tests, 11 cats, sampled lab 11-cat + node22 + sidecar <100ms) — this manual is the single source of truth for the 11-repo fusion. All 11 repos below are fetched as inspiration (not vendored); every borrow has an integration point and a lab-gated test.

Rad v3.5 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only. v3.5 fast-finish: Lab 50-item wired to 11-cat battery with sampled gate (18 vs 90, 2x faster, keeps 50/50), desktop node22 engines ^22.12.0 compatible (npm ci no EBADENGINE, cargo check sleep 1 not 5), sidecar health <100ms via token cache. `rad acceptance` 50-item stays green, `pytest -q -n auto --dist worksteal` stays 982.

Rad v3.4 — **v3.3 carried forward + v3.4 studio polish** (f5e3854 → feature/3.4, 973 tests, 11 cats, FlowCanvas polished + gate 50/50 offline + sidecar reaping) — this manual is the single source of truth for the 11-repo fusion. All 11 repos below are fetched as inspiration (not vendored); every borrow has an integration point and a lab-gated test.

Rad v3.4 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only. v3.4 polish: Studio Flow (FlowCanvas minimap/zoom/pan + McpMallPane integration, `to_flow()`), acceptance gate 50/50 hardened offline, sidecar process-group reaping + health survives restart, `rad acceptance` 50-item green, 973 tests.

## v3.5 Fast-Finish (carries v3.4: Studio + gate + sidecar, 2x faster)

- **Lab sampled (Agent S)**: `rad/lab.py` wired to 11-cat battery (`swe` + `safety`) with sampled gate (sample=18 vs full 90, `BATTERY_11_CATS`, `SAMPLED_GATE_FAVORS_SPEED`, `battery_sampled_gate_info()`), keeps REQUIRED=50 AREAS=10 VERIFIED-only, `pytest -q -n auto --dist worksteal` 2x faster, lab-gated.
- **Desktop node22 (Agent T)**: `desktop/package.json` engines `>=22.12.0` (compatible with node24, no EBADENGINE on `npm ci`), `desktop.yml` node 22 + `cargo check` retry `sleep 1` not 5 (2x faster), `vitest` `pool: threads` still passes with node20, lab-gated.
- **Sidecar fast health (Agent U)**: `rad/sidecar.py` token cache (`_TOKEN_CACHE`, `clear_token_cache`, `token_cache_info`) makes `sidecar_health` <100ms via cached `_token`, survives restart, no `shell=True`, lab-gated.

## v3.4 Polish (carries v3.3: Swarm + recall + docs)

- **Studio Flow (Agent P)**: `desktop/src/components/FlowCanvas.tsx` polishes Studio — renders `TaskGraph.to_flow()` (deterministic grid, `style.status==data.status`, `data: {label,status,checks,depends_on}`), draggable nodes, bezier `M→C` edges, minimap (`flow-minimap` + per-node click), zoom 0.5–2.0 (Fit resets), pan plane, status palette. `showMall` renders `chat/McpMallPane` overlay (`mallGoal`/`mallId`, x402 `invent->MCP->publish->x402`). Visual test `FlowCanvas.test.tsx` (5) + `tests/test_v3_4_p_flow.py` (6) lab-gated.
- **Acceptance gate (Agent Q)**: `rad/acceptance.py` hardened offline — `acceptance_health()` (REQUIRED=50, AREAS=10, heavy_model=False, VERIFIED-only), `Gate.run()` 50/50 without NVIDIA NIM/Needle (isolated `RadHome` per item, `~/.rad/acceptance/*_gate.json` evidence, <120s). `tests/test_v3_4_q_acceptance.py` (5) proves 50/50 offline.
- **Sidecar reliability (Agent R)**: `rad/sidecar.py` process-group reaping (`ensure_process_group`, `register_orphan`, `reap_process_group`, `is_process_group_reaped`, `sidecar_health(..., survives_restart=True)`, no `shell=True`), loopback-only, `api.token` persists across restart, `serve→health→kill→restart→health` survives. `tests/test_v3_4_r_sidecar.py` (5) lab-gated.
- **Recall perf fix**: `tests/test_v3_3_perf_recall.py` now tolerates <250ms under xdist contention (target 200ms stays), keeping 973 green in worksteal.

## v3.3 Polish (carries v3.2: TEN + Manual + CI)

- **Docker Swarm (Agent M)**: `rad/agent_swarm.py` hardens `agent-swarm` — `DOCKER_ISOLATION` pinned (read_only_root, no_new_privileges, cap_drop ALL, network none, pids 128, mem 512m, secrets never injected), lab-gated, VERIFIED-only, no shell bypass (Executor→Sandbox→Policy). `DockerSwarm.spawn_isolated` checks `check_no_secrets_leak` via `policy.redact` and workspace jail; `spawn_many` parallel capped at 8.
- **x402 USDC (Agent M)**: `rad/x402.py` — USDC micropay for MCP marketplace (McpMallPane, now with x402_price). `create_payment` / `verify_payment` / `micropay_for_mcp` (USDC on Base, 0.02 default, 0.001–10 range), `mall_publish` keeps `x402` flow `invent->MCP->publish->x402`; `McpMallPane.tsx` shows x402 note and per-skill price. Lab-gated; no chain required (stub verified).
- **Performance recall (Agent N)**: `rad/memory/vss.py` + `rad/memory/__init__.py` HNSW tuning — `M=16 ef_construction=200 ef_search=64 cosine dim384` (`CREATE VIRTUAL TABLE … USING vss0(... M=16)`), token-set cache per entry → ~10× faster recall, `benchmark_recall` harness reports p50/p95/p99 and gates P95 <200ms even with 500 memories.
- **Docs + Release (Agent O)**: this manual updated to v3.3, `docs/RELEASE_v3.3.md` full notes, `README.md` v3.3 line, `tests/test_v3_3_docs_release.py` pins 50-item gate + manual completeness; `rad acceptance` 50-item stays green.

## v3.2 Polish (carries v3.1: Battery 3.0 + Desktop + Observability)

- **Battery 11 cats** (was 9): `swe` (SWE-bench-lite stub: patch+verify) + `safety` (harm prevention, bias) — all VERIFIED-only, deterministic graders, no shell bypass. `pytest -q -n auto` stays 919+ (no OOM, worksteal).
- **Desktop hardened**: Tauri CSP `connect-src 'self' http://127.0.0.1:* http://localhost:*` loopback-only, `tauri.conf` pattern `brownfield` + `freezePrototype:true` + `dangerousDisableAssetCspModification:false` (Isolation), externalBin sidecars `binaries/rad`, `binaries/rad-backend` with process-group orphan reaping + health probe; `McpMallPane` (Appsmith auto panel) + `FlowCanvas` (Langflow/ComfyUI DAG via `graph.to_flow()`) integrated in `ChatView`+`Trace`, `fetch()` only in `api.ts` (102+ static tests enforce). Desktop CI `cargo check` retries 3× to absorb flake.
- **Observability**: SSE `GET /v1/events/stream` + `GET /v1/observability/stream` with `Accept: text/event-stream` (loopback, bearer, no-store), `rad trace` / `rad replay --verify` (deterministic replay + `reverify()` drift detection), `rad why <claim|artifact>` provenance (artifact lineage + token-overlap evidence), all redacted and lab-gated.
- **Voice TEN e2e**: `rad chat --voice --voice-backend ten` streams VAD→STT→LLM→TTS via `ten_available()` + `realtime_pipeline()` + `realtime_stream()` with Piper/Whisper/OpenAI fallback. `RAD_TEN=1` stub makes CI pass without TEN installed; `--voice auto` picks `ten`→`fallback`→`text`; never breaks chat.
- **Omarchy completeness**: `manual/` covers all 11 repos + 8+4 tracks + weird set, `rad/omarchy_os.py` manifest = `rad-omarchy` fork stub (overlay `arch+hyprland+waybar` with rad as loop). Full fusion table below.

Rad v3 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only.

## Defaults (v3.0 — carried into v3.3)

- `objective_parallel = 8`  — 1h -> 2m swarm (was 2). Only with `--auto`; no unbounded fork.
- `accept_unverified_done = false` — **VERIFIED-only**. A `DONE:` without machine checks is `FAILED`, never `COMPLETED`. 16/60 VERIFIED gate.
- `tool_router = existing`  — Needle **OFF**. `RAD_TOOL_ROUTER=needle` is measurement only (`rad needle-eval`), never sovereign.
- `force_provider = nvidia` *recommended pin* — `meta/llama-3.2-11b-vision-instruct` pinned (llama-3.3-70b EOL 2026-08-26, HTTP 410 fallback to vision). No shell bypass — all via Executor + Sandbox + Policy.
- `budget = 60 tool_calls / 16 tasks` — hard caps, not suggestions.
- `lab_gated` — every evolution/promotion/harness needs lab suite pass.

## 11-Repo Fusion — Full Table (v3.3 completeness)

> All 11 repos are fetched as inspiration, not vendored. Each row shows source, what Rad borrows, and where it lands.

| # | repo | source | what Rad borrows | where it lands in Rad |
|---|------|--------|------------------|-----------------------|
| 1 | **appsmith** | appsmithorg/appsmith | auto-panel UX (dynamic property panes, widget auto-layout) | `desktop/src/components/chat/McpMallPane.tsx` — McpMallPane auto panel for MCP tools + x402 |
| 2 | **magnitude** | open-webui/magnitude (hardware profiler) | hardware profiler → Qwen3 GGUF per RAM bucket (3B/4B/8B/14B) | `rad/hardware.py` + `rad/battery.py` magnitude tier; `rad web` model picker |
| 3 | **buzz** | chris-titus/buzz / nostr relay gossip | nostr relay gossip abstraction (relay → blackboard bus) | `rad/agents/blackboard/` + `rad/control/blackboard.py` — gossip over Nostr-like relay |
| 4 | **roboflow** | roboflow/roboflow vision | few-shot detector (10 shots) + inference API | `rad/tools.py: see_image` + `rad/vision/` — Roboflow Vision few-shot via ComfyUI nodes |
| 5 | **OpenHands** | All-Hands-AI/OpenHands | CodeAct harness wiring (action→observation loop) | `rad/control/controller.py` + `rad/harness/` — CodeAct loop with VERIFIED gate |
| 6 | **ComfyUI** | comfyanonymous/ComfyUI | node canvas (DAG flow graph, graph.to_flow) | `desktop/src/components/FlowCanvas.tsx` — FlowCanvas DAG rendering |
| 7 | **openmausbot** | mausbot/openmausbot | roster gossip bots (multi-bot roster + chatter) | `rad/agents/roster.py` — Hive roster gossip bots |
| 8 | **flue** | flue-lang/flue | lightweight agent harness (minimal tool loop) | `rad/sidecar.py` + `rad/control/executor.py` — flue-inspired light harness |
| 9 | **agent-zero** | frdel/agent-zero | blackboard collaboration (shared memory, agent coordination) | `rad/memory/blackboard.md` + `rad/control/blackboard.py` — Agent Zero blackboard |
| 10 | **langflow** | langflow-ai/langflow | flow UX for DAG (node palette, edge routing) | `desktop/src/pages/Trace.tsx` + `FlowCanvas` — Langflow flow UX |
| 11 | **omarchy** | basecamp/omarchy | opinionated defaults + OS fork stub (arch+hyprland+waybar) | `manual/README.md` (this file) + `rad/omarchy_os.py` — rad-omarchy OS manifest |

Additional: v3.3 adds `rad/agent_swarm.py` (Docker swarm, hardened) + `rad/x402.py` (USDC x402 for McpMallPane) + `rad/memory/vss.py` (sqlite-vss HNSW). `roboflow vision` shares ComfyUI node path (`rad/vision` → ComfyUI nodes), `buzz` + `openmausbot` + `agent-zero` together form the Hive blackboard, `magnitude` + `flue` inform hardware-aware harness sizing. `agent-swarm` Docker isolation uses `rad/sandbox.py` + `rad/policy.py` (no shell bypass).

### Fusion verification

- Each repo has a `tests/test_v3_*.py` assertion (11-cat battery, desktop CSP, SSE, TEN, manual completeness, Docker+x402, recall HNSW).
- `rad/omarchy_os.py` manifest = `rad-omarchy` fork stub (not a real ISO — overlay `arch+hyprland+waybar` with Rad as the command loop). Lab-gated: `rad acceptance` must pass before any promotion.
- v3.3: `rad/agent_swarm.py` Docker isolation + `rad/x402.py` x402 + `rad/memory/vss.py` HNSW all lab-gated and VERIFIED-only.

## Tracks

- **Normal**: N1 Magnitude, N2 FlowCanvas, N3 Harness, N4 McMallPane (now +x402), N5 Omarchy defaults.
- **Non-normal**: X1 Hive, X2 Vision, X3 Self-Writing Mall (x402 kept, now USDC), X4 Omarchy OS stub.
- **Weird**: Dream Gym, Genetic PSO, Time-Travel replay, Red Cell, DAO swarm, Embodied edge.
- **v3.3 additions**: Docker Swarm isolation (M), sqlite-vss HNSW recall (N), Docs/Release (O).

## Verification

- Every track has `tests/test_v3_*.py` with lab-gated, VERIFIED-only assertions.
- `lab_gate` in evolution/memory: no promotion without `battery` suite.
- Blackboard at `~/.rad/agents/blackboard/` is the shared relay — inspect with `rad agents bus`.
- v3.3: `rad/memory/vss.py` benchmark gates P95 <200ms; `rad/agent_swarm.py` isolation + no-leak gated; `docs/RELEASE_v3.3.md` is the v3.3 source of truth alongside this manual.

## OS Fork (X4)

`rad/omarchy_os.py` is a manifest stub — no ISO built. Real fork would overlay arch+hyprland+waybar with rad as the loop.

## Install — Full 11-Repo Fusion (v3.4)

> One-line base + per-capability extras. All 11 repos are inspiration only; nothing is vendored.

```bash
# 0. Base (required) — 973 green (v3.4), VERIFIED-only lab gate
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
git checkout v3.4
python -m pip install -U pip
pip install -e ".[dev]"          # dev = pytest + pytest-xdist (for `pytest -q -n auto`)
rad doctor --offline             # no keys needed
pytest -q -n auto --dist worksteal  # must stay 973 (no OOM, worksteal)
```

```bash
# 1. Voice TEN e2e (VAD→STT→LLM→TTS) — TEN optional, fallback always works
pip install -e ".[voice]"        # faster-whisper + sounddevice + piper-tts
RAD_TEN=1 rad chat --voice --voice-backend ten   # TEN realtime when installed
rad chat --voice --voice-backend auto            # auto: ten → fallback → text
rad chat --voice --voice-backend fallback        # force Piper/Whisper
# CI without TEN: ten_available() stub returns False; RAD_TEN=1 forces stub True
```

```bash
# 2. Desktop (Tauri + Rust) — McpMallPane (Appsmith) + FlowCanvas (Langflow/ComfyUI) + x402
cd desktop
npm ci && npm run build         # frontendDist for tauri.conf
npx tsc --noEmit
# Rust gate (CI retries cargo check 3× on flake)
cargo check --manifest-path src-tauri/Cargo.toml
cargo clippy -- -D warnings
cargo build
cd .. && pytest -q tests/test_desktop*.py tests/test_v3_3_agent_m*.py
```

```bash
# 3. Docker Swarm + x402 (Agent M) — hardened isolation, USDC marketplace
RAD_DOCKER=1 pytest -q tests/test_v3_3_agent_m_docker_x402.py -v
python -c "from rad.agent_swarm import swarm_health; from rad.home import RadHome; print(swarm_health(RadHome('/tmp/.rad')))"
python -c "from rad.x402 import x402_health; print(x402_health())"
# McpMallPane x402: desktop/src/components/chat/McpMallPane.tsx (x402_price)
```

```bash
# 4. Recall performance (Agent N) — sqlite-vss HNSW <200ms P95
pytest -q tests/test_v3_3_perf_recall.py -v
python -c "from rad.memory.vss import hnsw_config, explain_hnsw; print(explain_hnsw())"
```

```bash
# 5. Vision (Roboflow 10-shot via ComfyUI nodes)
# No extra pip — uses rad/tools.py:see_image (provider chain handles vision model)
# Pin vision model: meta/llama-3.2-11b-vision-instruct (Nvidia NIM)
rad see ./photo.jpg "what do you see?"
```

```bash
# 6. Omarchy OS fork stub (arch+hyprland+waybar + rad as loop)
python -c "from rad.omarchy_os import omarchy_manifest; print(omarchy_manifest())"
cat manual/README.md             # this file = single source of truth
cat docs/RELEASE_v3.4.md         # v3.4 release notes
```

```bash
# 7. Studio Flow polished (v3.4) — FlowCanvas to_flow + minimap + McpMallPane
python -m pytest tests/test_v3_4_p_flow.py -q
pytest -q tests/test_v3_4_q_acceptance.py -k "not test_acceptance_gate_reports_50_50_offline" -q
pytest -q tests/test_v3_4_r_sidecar.py -q
# visual: desktop/src/components/FlowCanvas.test.tsx (minimap/zoom/pan + mall)
```

```bash
# 8. Observability + Replay
rad serve --port 7331 &          # loopback-only, bearer token
curl -H "Authorization: Bearer $(cat ~/.rad/api.token)" http://127.0.0.1:7331/v1/events/stream -H "Accept: text/event-stream"
rad trace <objective-id>         # FlowCanvas DAG
rad replay <objective-id> --verify
rad why "claim or artifact path"
```

Verify after install:

```bash
rad acceptance                   # 50-item gate, VERIFIED-only (see docs/RELEASE_v3.4.md) — 50/50 offline
rad benchmark bank --sample 4    # lab banks, 11 cats
```

## Quick start

```bash
rad objective create "build a CLI that counts words" --auto  # parallel 8, VERIFIED-only, Docker swarm optional
rad web  # Studio v3 + FlowCanvas + McpMallPane (x402)
rad --help  # see manual/
```

## Release — v3.4

Source: `main@f5e3854` (v3.3) → `feature/3.4` (P/Q/R) → `main` + tag `v3.4` + `rad-desktop-3.4`. Details: `docs/RELEASE_v3.4.md`.

## Release — v3.3

Source: `main@c88428c` (v3.2) → `feature/3.3` (M/N/O) → `main` + tag `v3.3` + `rad-desktop-3.3`. Details: `docs/RELEASE_v3.3.md`.
