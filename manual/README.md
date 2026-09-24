# Rad Omarchy Manual — opinionated defaults (N5)

Rad v3.1 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only. v3.1 polish adds Battery 11 cats, desktop hardening, SSE observability, voice TEN e2e.

## v3.1 Polish (Battery 3.0 + Desktop + Observability)

- **Battery 11 cats** (was 9): `swe` (SWE-bench-lite stub: patch+verify) + `safety` (harm prevention, bias) — all VERIFIED-only, deterministic graders, no shell bypass.
- **Desktop hardened**: Tauri CSP `connect-src 'self' http://127.0.0.1:* http://localhost:*` loopback-only, `tauri.conf` pattern `brownfield` + `freezePrototype:true` + `dangerousDisableAssetCspModification:false` (Isolation), externalBin sidecars `binaries/rad`, `binaries/rad-backend` with process-group orphan reaping + health probe; `McpMallPane` (Appsmith auto panel) + `FlowCanvas` (Langflow/ComfyUI DAG via `graph.to_flow()`) integrated in `ChatView`+`Trace`, `fetch()` only in `api.ts` (102 static tests enforce).
- **Observability**: SSE `GET /v1/events/stream` + `GET /v1/observability/stream` with `Accept: text/event-stream` (loopback, bearer, no-store), `rad trace` / `rad replay --verify` (deterministic replay + `reverify()` drift detection), `rad why <claim|artifact>` provenance (artifact lineage + token-overlap evidence), all redacted and lab-gated.
- **Voice TEN e2e**: `voice_backend=ten` when `RAD_TEN=1` or `ten` importable, VAD→STT→LLM→TTS `realtime_pipeline()` with Piper/Whisper/OpenAI fallback, `--voice auto` picks `ten`→`fallback`→`text`; stubbed when engine absent, never breaks chat.
- **Omarchy completeness**: `manual/` covers all 11 repos + 8+4 tracks + weird set, `rad/omarchy_os.py` manifest = `rad-omarchy` fork stub (overlay `arch+hyprland+waybar` with rad as loop).

Rad v3 is **opinionated** (omarchy style). These defaults ship out-of-the-box, lab-gated, VERIFIED-only.

## Defaults (v3.0)

- `objective_parallel = 8`  — 1h -> 2m swarm (was 2). Only with `--auto`; no unbounded fork.
- `accept_unverified_done = false` — **VERIFIED-only**. A `DONE:` without machine checks is `FAILED`, never `COMPLETED`. 16/60 VERIFIED gate.
- `tool_router = existing`  — Needle **OFF**. `RAD_TOOL_ROUTER=needle` is measurement only (`rad needle-eval`), never sovereign.
- `force_provider = nvidia` *recommended pin* — `meta/llama-3.2-11b-vision-instruct` pinned (llama-3.3-70b EOL 2026-08-26, HTTP 410 fallback to vision). No shell bypass — all via Executor + Sandbox + Policy.
- `budget = 60 tool_calls / 16 tasks` — hard caps, not suggestions.
- `lab_gated` — every evolution/promotion/harness needs lab suite pass.

## 11 repos fetched (inspiration, not vendoring)

| repo | what rad borrows |
|------|------------------|
| appsmith | auto-panel UX (McpMallPane) |
| magnitude | hardware profiler -> Qwen3 GGUF per RAM |
| buzz | nostr relay gossip abstraction |
| roboflow | few-shot detector (10 shots) |
| OpenHands | CodeAct harness wiring |
| ComfyUI | node canvas (FlowCanvas.tsx) |
| openmausbot | roster gossip bots |
| flue | lightweight agent harness |
| agent-zero | blackboard collaboration |
| langflow | flow UX for DAG |
| omarchy | opinionated defaults + OS fork stub |

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

## Quick start

```bash
rad objective create "build a CLI that counts words" --auto  # parallel 8, VERIFIED-only
rad web  # Studio v3 + FlowCanvas
rad --help  # see manual/
```
