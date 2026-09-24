# Rad Omarchy Manual — opinionated defaults (N5)

Rad v3.2 — **v3.1 polish carried forward** (4243386, 919 tests, 11 cats, Desktop CSP, SSE) — this manual is the single source of truth for the 11-repo fusion. All 11 repos below are fetched as inspiration (not vendored); every borrow has an integration point and a lab-gated test.

Rad v3.2 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only. v3.2 polish: Voice TEN e2e hardening (VAD→STT→LLM→TTS + fallback), manual completeness, Desktop CI reliability.

## v3.2 Polish (carries v3.1: Battery 3.0 + Desktop + Observability)

- **Battery 11 cats** (was 9): `swe` (SWE-bench-lite stub: patch+verify) + `safety` (harm prevention, bias) — all VERIFIED-only, deterministic graders, no shell bypass. `pytest -q -n auto` stays 919+ (no OOM, worksteal).
- **Desktop hardened**: Tauri CSP `connect-src 'self' http://127.0.0.1:* http://localhost:*` loopback-only, `tauri.conf` pattern `brownfield` + `freezePrototype:true` + `dangerousDisableAssetCspModification:false` (Isolation), externalBin sidecars `binaries/rad`, `binaries/rad-backend` with process-group orphan reaping + health probe; `McpMallPane` (Appsmith auto panel) + `FlowCanvas` (Langflow/ComfyUI DAG via `graph.to_flow()`) integrated in `ChatView`+`Trace`, `fetch()` only in `api.ts` (102+ static tests enforce). Desktop CI `cargo check` retries 3× to absorb flake.
- **Observability**: SSE `GET /v1/events/stream` + `GET /v1/observability/stream` with `Accept: text/event-stream` (loopback, bearer, no-store), `rad trace` / `rad replay --verify` (deterministic replay + `reverify()` drift detection), `rad why <claim|artifact>` provenance (artifact lineage + token-overlap evidence), all redacted and lab-gated.
- **Voice TEN e2e**: `rad chat --voice --voice-backend ten` streams VAD→STT→LLM→TTS via `ten_available()` + `realtime_pipeline()` + `realtime_stream()` with Piper/Whisper/OpenAI fallback. `RAD_TEN=1` stub makes CI pass without TEN installed; `--voice auto` picks `ten`→`fallback`→`text`; never breaks chat.
- **Omarchy completeness**: `manual/` covers all 11 repos + 8+4 tracks + weird set, `rad/omarchy_os.py` manifest = `rad-omarchy` fork stub (overlay `arch+hyprland+waybar` with rad as loop). Full fusion table below.

Rad v3 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only.

## Defaults (v3.0 — carried into v3.2)

- `objective_parallel = 8`  — 1h -> 2m swarm (was 2). Only with `--auto`; no unbounded fork.
- `accept_unverified_done = false` — **VERIFIED-only**. A `DONE:` without machine checks is `FAILED`, never `COMPLETED`. 16/60 VERIFIED gate.
- `tool_router = existing`  — Needle **OFF**. `RAD_TOOL_ROUTER=needle` is measurement only (`rad needle-eval`), never sovereign.
- `force_provider = nvidia` *recommended pin* — `meta/llama-3.2-11b-vision-instruct` pinned (llama-3.3-70b EOL 2026-08-26, HTTP 410 fallback to vision). No shell bypass — all via Executor + Sandbox + Policy.
- `budget = 60 tool_calls / 16 tasks` — hard caps, not suggestions.
- `lab_gated` — every evolution/promotion/harness needs lab suite pass.

## 11-Repo Fusion — Full Table (v3.2 completeness)

> All 11 repos are fetched as inspiration, not vendored. Each row shows source, what Rad borrows, and where it lands.

| # | repo | source | what Rad borrows | where it lands in Rad |
|---|------|--------|------------------|-----------------------|
| 1 | **appsmith** | appsmithorg/appsmith | auto-panel UX (dynamic property panes, widget auto-layout) | `desktop/src/components/chat/McpMallPane.tsx` — McpMallPane auto panel for MCP tools |
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

Additional borrow context: `roboflow vision` shares the ComfyUI node path (`rad/vision` → ComfyUI nodes), `buzz` + `openmausbot` + `agent-zero` together form the Hive blackboard, `magnitude` + `flue` inform the hardware-aware harness sizing.

### Fusion verification

- Each repo has a `tests/test_v3_*.py` assertion (11-cat battery, desktop CSP, SSE, TEN, manual completeness).
- `rad/omarchy_os.py` manifest = `rad-omarchy` fork stub (not a real ISO — overlay `arch+hyprland+waybar` with Rad as the command loop). Lab-gated: `rad acceptance` must pass before any promotion.

## Tracks

- **Normal**: N1 Magnitude, N2 FlowCanvas, N3 Harness, N4 McMallPane, N5 Omarchy defaults.
- **Non-normal**: X1 Hive, X2 Vision, X3 Self-Writing Mall (x402 kept), X4 Omarchy OS stub.
- **Weird**: Dream Gym, Genetic PSO, Time-Travel replay, Red Cell, DAO swarm, Embodied edge.

## Verification

- Every track has `tests/test_v3_*.py` with lab-gated, VERIFIED-only assertions.
- `lab_gate` in evolution/memory: no promotion without `battery` suite.
- Blackboard at `~/.rad/agents/blackboard/` is the shared relay — inspect with `rad agents bus`.

## OS Fork (X4)

`rad/omarchy_os.py` is a manifest stub — no ISO built. Real fork would overlay arch+hyprland+waybar with rad as the loop.

## Install — Full 11-Repo Fusion (v3.2)

> One-line base + per-capability extras. All 11 repos are inspiration only; nothing is vendored.

```bash
# 0. Base (required) — 919 tests, VERIFIED-only lab gate
git clone https://github.com/seven0070/rad-agent-.git && cd rad-agent-
python -m pip install -U pip
pip install -e ".[dev]"          # dev = pytest + pytest-xdist (for `pytest -q -n auto`)
rad doctor --offline             # no keys needed
pytest -q -n auto                # must stay 919+ (no -n auto OOM)
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
# 2. Desktop (Tauri + Rust) — McpMallPane (Appsmith) + FlowCanvas (Langflow/ComfyUI)
cd desktop
npm ci && npm run build         # frontendDist for tauri.conf
npx tsc --noEmit
# Rust gate (CI retries cargo check 3× on flake)
cargo check --manifest-path src-tauri/Cargo.toml
cargo clippy -- -D warnings
cargo build
cd .. && pytest -q tests/test_desktop*.py
```

```bash
# 3. Vision (Roboflow 10-shot via ComfyUI nodes)
# No extra pip — uses rad/tools.py:see_image (provider chain handles vision model)
# Pin vision model: meta/llama-3.2-11b-vision-instruct (Nvidia NIM)
rad see ./photo.jpg "what do you see?"
```

```bash
# 4. Omarchy OS fork stub (arch+hyprland+waybar + rad as loop)
python -c "from rad.omarchy_os import omarchy_manifest; print(omarchy_manifest())"
cat manual/README.md             # this file = single source of truth
```

```bash
# 5. Observability + Replay
rad serve --port 7331 &          # loopback-only, bearer token
curl -H "Authorization: Bearer $(cat ~/.rad/api.token)" http://127.0.0.1:7331/v1/events/stream -H "Accept: text/event-stream"
rad trace <objective-id>         # FlowCanvas DAG
rad replay <objective-id> --verify
rad why "claim or artifact path"
```

Verify after install:

```bash
rad acceptance                   # 50-item gate, VERIFIED-only
rad benchmark bank --sample 4    # lab banks, 11 cats
```

## Quick start

```bash
rad objective create "build a CLI that counts words" --auto  # parallel 8, VERIFIED-only
rad web  # Studio v3 + FlowCanvas
rad --help  # see manual/
```
