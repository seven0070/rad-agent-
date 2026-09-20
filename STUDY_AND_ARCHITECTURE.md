# RAD Agent: Comprehensive Architectural Study & System Report

**Document Version:** 1.0.1  
**Target Repository:** `rad-agent-` (`https://github.com/seven0070/rad-agent-.git`)  
**Package Version:** `1.0.1`  
**Git Branch:** `feat/complete-rad`  
**Date:** 2026-09-20  
**Classification:** Publication-Grade Architectural Survey & Subsystem Specification  

---

## Table of Contents

1. [Executive Summary & System Philosophy](#1-executive-summary--system-philosophy)
   - 1.1 The Core Thesis: "Rad is the Door, Not the Room"
   - 1.2 Sovereignty Inversion & The Verification Doctrine
   - 1.3 Economic Doctrine: Free-First & Local-First
   - 1.4 Defense-in-Depth & Authority Containment
   - 1.5 Multi-Surface Integrity
2. [The Six Open Door Sockets](#2-the-six-open-door-sockets)
   - 2.1 Brain Socket (Inference & Cognitive Routing)
   - 2.2 Engine Socket (Local Execution Runtimes)
   - 2.3 Tools Socket (Hands, Perception, Web & Dynamic MCP Skills)
   - 2.4 Memory Socket (Layered Epistemic Hierarchy & Knowledge Graphs)
   - 2.5 Voice Socket (Acoustic Perception & Speech Synthesis)
   - 2.6 Face Socket (Terminal, Loopback HTTP API & Tauri 2 Desktop Surface)
3. [Control Plane Governance & Autonomous Execution](#3-control-plane-governance--autonomous-execution)
   - 3.1 Central Controller Execution Loop
   - 3.2 11-State Task Finite State Machine (FSM)
   - 3.3 Task Graph (DAG) Scheduling & Yielding Mechanics
   - 3.4 5-Level Independent Machine Verifier
   - 3.5 Recovery Engine & Error Taxonomy
   - 3.6 Multi-Agent Coordination & Capability Envelopes
4. [Safety, Policy Engine & Security Architecture](#4-safety-policy-engine--security-architecture)
   - 4.1 Single Enforcement Point Choke Point
   - 4.2 The Unbypassable Hard Layer
   - 4.3 Soft Policy Rules & Glob Matching
   - 4.4 Authority Profiles & Permissions Matrix
5. [Desktop Surface Architecture](#5-desktop-surface-architecture)
   - 5.1 Process Lifecycle & Sidecar Management
   - 5.2 Tauri v2 Rust Backend & Capability Boundaries
   - 5.3 React/TypeScript Frontend Architecture & Containment
   - 5.4 Loopback Security Guarantees & Control-Plane Locks
6. [Formal Ledger of Architectural Invariants](#6-formal-ledger-of-architectural-invariants)
   - 6.1 The Ten Non-Negotiable Invariants (I-1 through I-10)
   - 6.2 Authority & Capability Matrix
7. [Active Development State & Verification Requirements](#7-active-development-state--verification-requirements)
   - 7.1 Empirical Baseline & Diagnostics
   - 7.2 Root-Cause Failure Catalog (23 Test Remediation Specs)
   - 7.3 Host Environment & Platform Quirks (Windows 11 / NTFS / Toolchains)
   - 7.4 Multi-Gate Verification & Stabilization Roadmap
8. [Conclusion & Architectural Assessment](#8-conclusion--architectural-assessment)

---

## 1. Executive Summary & System Philosophy

### 1.1 The Core Thesis: "Rad is the Door, Not the Room"

The modern artificial intelligence ecosystem is characterized by aggressive vendor lock-in, proprietary runtime coupling, and monolithic agent frameworks that bind reasoning, tool execution, and memory to specific cloud providers. The **RAD Agent** (`rad`) completely inverts this paradigm. Founded on the axiom:

$$\text{\bf "Rad is the door, not the room."}$$

RAD does not attempt to be a closed cognitive silo. Instead, it serves as an open, sovereign, swappable gateway that connects arbitrary local runtimes, cloud inference models, operating system capabilities, external tools, and human interfaces without permanently hitching the user to any external vendor, paid subscription, or proprietary protocol.

```
                  ┌──────────────────────────────────────────────────────────┐
                  │                 RAD AGENT OPEN DOOR SPINE                 │
                  └─────────────────────────────┬────────────────────────────┘
                                                │
         ┌──────────────┬──────────────┬────────┴─────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼              ▼              ▼
     [BRAIN]        [ENGINE]        [TOOLS]        [MEMORY]       [VOICE]        [FACE]
   Any LLM /     Local Engines   MCP Servers,   Multi-Tiered   Piper / STT    CLI / API /
   Cloud APIs    (Edge0, Ollama) Browser, Hands  Markdown/JSON   Whisper       Tauri Surface
```

Every major functional subsystem is implemented as an interchangeable **Socket**. Sockets expose strict, typed contracts. An engine can be swapped from a local Apple Silicon Edge0 instance to an Ollama cluster, or to a remote vLLM endpoint; a brain can rotate from local Llama-3 to Groq, Cerebras, Claude, or GPT-4o; memory can persist to local plain Markdown or mirror into an embedded Kuzu graph database and offsite Google Drive; yet the central control plane, safety guarantees, and verification invariants remain absolute and invariant.

---

### 1.2 Sovereignty Inversion & The Verification Doctrine

In conventional conversational agents, the Large Language Model acts as the ultimate authority: the model decides when a task is completed, verbally declares `"DONE: wrote report"`, and the agent framework terminates. This design is fatally flawed; it suffers from sycophancy, hallucinated success, unhandled runtime errors, and silent failure propagation.

RAD introduces **Sovereignty Inversion**:

$$\text{\bf The model proposes; the RAD Control Plane and Executor decide.}$$

1. **Model Output is Untrusted Proposition:** An LLM turn is merely a candidate action or speculative solution.
2. **Deterministic Governance:** Tool calls proposed by a model must pass through an unbypassable hard security layer and a capability-scoped policy gate (`Policy.decide`).
3. **Independent Machine Verification:** A task is never marked `COMPLETED` based on model verbal claims. Completion requires explicit, machine-checkable evidence executed directly on the host operating system (`file_exists`, `shell_ok`, `json_valid`, `file_min_bytes`). If machine checks fail or are absent, the task is strictly demoted to `UNVERIFIED` or flagged for recovery.

---

### 1.3 Economic Doctrine: Free-First & Local-First

RAD treats inference costs as an architectural constraint rather than an operational afterthought. The system implements a strict **Three-Tier Priority Law**:

$$\text{Tier 0 (Local)} \prec \text{Tier 1 (Free Cloud)} \prec \text{Tier 2 (Paid Cloud)}$$

- **Tier 0 (Local Execution):** Offline runtimes (`edge0`, `ollama`, `lmstudio`, `vLLM`) have zero token cost, zero external data leakage, and operate without internet access.
- **Tier 1 (Free Cloud Tiers):** Cloud inference providers offering generous free tiers (`groq`, `cerebras`, `gemini`, `openrouter`, `nvidia`) are utilized with round-robin load distribution to avoid per-provider rate limits.
- **Tier 2 (Paid Cloud APIs):** High-cost frontier models (`openai`, `anthropic`, `mistral`, `grok`) are strictly locked behind an explicit configuration gate (`free_lock = true` by default).

When `free_lock` is active, paid model spend is rendered mathematically and programmatically impossible. The router dynamically prunes Tier 2 providers from the candidate chain prior to evaluation.

---

### 1.4 Defense-in-Depth & Authority Containment

Autonomous agent architectures face severe security risks, including prompt injection, data exfiltration, accidental system destruction (`rm -rf`), and server-side request forgery (SSRF). RAD implements a two-tier defense-in-depth security model:

1. **The Unbypassable Hard Layer:** Embedded immutably in code (`rad/policy.py`). It enforces hardcoded destructive shell command blocklists, recursive deletion protections, secret path jails (protecting private keys and tokens), private network egress blocking, subprocess environment credential scrubbing, and universal output token redaction. This layer cannot be bypassed by any prompt injection, user flag (`--auto`), or authority profile.
2. **The Soft Policy Layer:** A flexible, capability-based evaluation engine supporting fine-grained glob patterns, user approval prompts (`ASK`), and formal **Authority Profiles** (`SAFE`, `STANDARD`, `AUTONOMOUS`, `UNRESTRICTED`, `CUSTOM`).

---

### 1.5 Multi-Surface Integrity

RAD operates identically regardless of whether the user interfaces through:
- An interactive **Terminal REPL** (`rad`, `rad chat`, `rad objective`),
- A headless **Loopback REST API** (`rad serve` on `127.0.0.1` with bearer token auth), or
- The official **Desktop Application** (`desktop/`, built on Tauri v2, React 18, and TypeScript).

The desktop application is architected under strict containment principles: it possesses zero direct tool execution runners, includes no shell plugins, operates under a loopback-only Content Security Policy (CSP), and treats the desktop UI purely as an observability and steering surface over the sovereign core engine.

---

## 2. The Six Open Door Sockets

RAD formalizes system extensibility through six distinct, modular sockets. Each socket defines explicit abstract contracts, wire protocols, discovery mechanisms, and failure-handling semantics.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE SIX OPEN DOOR SOCKETS                       │
├──────────────┬─────────────────────────────────────────────────────────┤
│ Socket       │ Subsystem & Primary Module                             │
├──────────────┼─────────────────────────────────────────────────────────┤
│ 1. BRAIN     │ Inference Wire Protocols & Routing (`rad/providers.py`) │
│ 2. ENGINE    │ Local Execution Runtimes (`rad/providers.py`)           │
│ 3. TOOLS     │ Tool Registry & Dynamic MCP Skills (`rad/tools.py`)     │
│ 4. MEMORY    │ 4-Tier Epistemic Hierarchy & Graph (`rad/memory.py`)    │
│ 5. VOICE     │ Acoustic Perception & Speech (`rad/voice.py`)           │
│ 6. FACE      │ CLI, HTTP REST API & Tauri Desktop (`desktop/`)         │
└──────────────┴─────────────────────────────────────────────────────────┘
```

---

### 2.1 Brain Socket (Inference & Cognitive Routing)

The Brain Socket governs cognitive model selection, multi-provider wire serialization, capability profiling, and candidate promotion.

#### 2.1.1 Core Contracts
The Brain Socket is anchored in `rad/providers.py`:
- **`ProviderSpec` (`rad/providers.py:127-141`):** Immutable metadata declaring provider identity:
  ```python
  @dataclass
  class ProviderSpec:
      name: str
      kind: str               # "openai" | "anthropic" | "gemini"
      base_url: str
      key_names: List[str]
      default_model: str
      vision_model: str = ""
      tier: str = "paid"      # "local" | "free" | "paid"
      local: bool = False
      requires_key: bool = True
      supports_tools: bool = True
      supports_vision: bool = False
      max_tokens: int = 4096
      desc: str = ""
  ```
- **`ChatResult` (`rad/providers.py:144-150`):** Normalized inference response:
  ```python
  @dataclass
  class ChatResult:
      text: str
      tool_calls: List[Dict[str, Any]]
      usage: Dict[str, int]
      provider: str
      model: str
  ```

#### 2.1.2 Wire Protocols
Inference serialization transforms generic agent dialogue turns into provider-specific REST schemas:
1. **OpenAI Protocol (`kind="openai"`):** Dispatches to `{base_url}/chat/completions`. Handles SSE streaming (`stream=True`) and tool calling schema. Implements custom sequential tool-call unfolding (`_unparallel_tool_history` at line 391) to enforce single-turn execution required by strict downstream providers such as NVIDIA NIM.
2. **Anthropic Protocol (`kind="anthropic"`):** Dispatches to `{base_url}/v1/messages`. Transforms JSON Schema tool declarations into Anthropic `input_schema` structures and maps messages into interleaved content blocks (`_to_anthropic` at line 540).
3. **Gemini Protocol (`kind="gemini"`):** Dispatches to Google's REST endpoint `{base_url}/v1beta/models/{model}:generateContent`. Normalizes dialogue into `contents` parts and tool schemas into `functionDeclarations`.

#### 2.1.3 Verified Brain Promotion & Capability Battery Battles
RAD introduces deterministic evolutionary governance for models via `rad/brains.py` and `rad/battery.py`:
- **Capability Battery:** An automated test battery evaluating candidate models across 7 deterministic categories: `math`, `logic`, `code`, `tool`, `json`, `summarize`, and `style`, yielding an objective composite score in $[0, 100]$.
- **Head-to-Head Promotion Battles:** Before any newly connected model, custom fine-tune, or local weight adapter can replace the active brain, it must execute a head-to-head capability battle against the incumbent. The candidate is promoted if and only if:
  $$\text{Score}_{\text{candidate}} \ge \text{Score}_{\text{incumbent}} + \text{Margin}$$
  Promotion events are cryptographically recorded in `~/.rad/brains/registry.json`. If a promoted brain exhibits runtime regression, instant atomic rollback is supported via `rad brains rollback`.

#### 2.1.4 Credential Resolution Priority
Credentials resolve through a deterministic 3-tier cascade:
1. **RAD Encrypted Vault:** AES-256-GCM encrypted vault at `~/.rad/keys/vault.enc`, unlocked via keyfile `~/.rad/.vault.key`.
2. **Process Environment:** Operating system environment variables (`os.environ`).
3. **Local & Home Environment Files:** `.env` files located in the current workspace or `~/.rad/` via `env_files_scan()`.

---

### 2.2 Engine Socket (Local Execution Runtimes)

The Engine Socket abstracts offline, zero-data-exfiltration inference runtimes executing directly on host hardware.

```
                    ┌──────────────────────────────────┐
                    │      ENGINE SOCKET DISCOVERY     │
                    │   probe_local(spec) -> (ok, ms)  │
                    └─────────────────┬────────────────┘
                                      │
         ┌──────────────────┬─────────┴─────────┬──────────────────┐
         ▼                  ▼                   ▼                  ▼
     [EDGE0]             [OLLAMA]          [LM STUDIO]           [vLLM]
  127.0.0.1:8000     127.0.0.1:11434     127.0.0.1:1234      127.0.0.1:8000
 Apple Silicon MoE    Universal GPU       Desktop GUI        High-Throughput
  MLX SSD Stream      CUDA/ROCm/CPU      Local Server        Production LLM
```

#### 2.2.1 Discovery & Probing Interface
Local runtime availability is determined at boot via `probe_local(spec: ProviderSpec) -> Tuple[bool, List[str]]` (`rad/providers.py:333-351`):
- Probing issues a non-blocking HTTP GET request to the runtime's model enumeration endpoint (e.g. `/v1/models` or `/api/tags`) with a strict **1.2-second timeout**.
- If the endpoint responds with HTTP 200, the runtime is registered as active (`tier="local"`, `local=True`, `requires_key=False`), and available model tags are dynamically ingested.
- If the daemon is inactive, the engine socket gracefully bypasses the runtime without throwing user-facing errors or blocking boot.

#### 2.2.2 Supported Engine Implementations
1. **Edge0:** Optimized Apple Silicon MoE runtime using MLX. Streams weights dynamically from NVMe storage, allowing execution of 35B/10B parameter models within constrained RAM footprints.
2. **Ollama:** Universal local daemon operating on Windows (DirectML/CUDA), Linux (CUDA/ROCm), and macOS (Metal). Interfaced via loopback `http://127.0.0.1:11434`.
3. **LM Studio:** Desktop inference engine hosting local GGUF models with an OpenAI-compatible loopback server at `http://127.0.0.1:1234/v1`.
4. **vLLM:** High-performance, paged-attention server for enterprise local inference clusters.

---

### 2.3 Tools Socket (Hands, Perception, Web & Dynamic MCP Skills)

The Tools Socket provides the execution interface between the cognitive model and the physical computing environment.

#### 2.3.1 Execution Pipeline & Tool Context
All tool invocations across RAD instantiate a `ToolCtx` dataclass (`rad/tools.py:294-314`):
```python
@dataclass
class ToolCtx:
    home: RadHome
    router: Any = None
    auto: bool = False
    confirm: Optional[Callable[[str, str], bool]] = None
    mcp_call: Optional[Callable[..., Any]] = None
    mcp_tool_names: List[str] = field(default_factory=list)
    actor: str = "user"
    agent_caps: Optional[List[str]] = None
    last_decision: Any = None
    sandbox: Optional[Any] = None
    _policy: Optional[Any] = None
```
Execution is initiated solely through `run_tool(name: str, args: Dict[str, Any], ctx: ToolCtx) -> str` (`rad/tools.py:475-509`).

#### 2.3.2 Flat Schema Registry (`TOOLS`)
The core tools registry (`rad/tools.py:175-279`) defines JSON Schema specifications conforming to OpenAI Function Calling standards:
- **Filesystem & Inspection:** `read_file` (with byte-window offsets), `write_file` (atomic writes), `list_dir` (recursive directory walks).
- **Process Execution:** `run_shell` (scrubbed shell execution), `run_python` (isolated child interpreter via `python -I -c` protecting environment integrity).
- **Web Perception:** `web_search` (keyless DuckDuckGo HTML scraping), `fetch_page` (raw HTTP GET wrapping untrusted external content in strict isolation delimiters `=== UNTRUSTED WEB CONTENT ===`), `verify_url` (HTTP HEAD status checks).
- **Vision Perception:** `see_image` (encodes image to base64 Data URI, dispatches to vision-capable models).
- **Headless Browser:** Playwright-backed browser tools (`browser_navigate`, `browser_extract`, `browser_find`, `browser_links`, `browser_submit`, `browser_download`, `browser_screenshot`).
- **Multi-Agent Orchestration:** `spawn_agents` (assembles specialist sub-agent teams).

#### 2.3.3 Dynamic MCP Skill Wrapping & Virtual Environments
RAD integrates the Model Context Protocol (MCP) to allow dynamic extension without touching core code:
- **Installation Pipeline (`rad connect <link>`):** Ingests skills from GitHub repositories, local directories, PyPI packages, npm packages, Docker containers, or remote SSE endpoints.
- **Isolated Virtual Environments:** Every connected Python skill is provisioned inside an isolated virtual environment at `~/.rad/venvs/<name>/`, preventing dependency conflicts with the host RAD installation.
- **Capability Inference:** Inspects skill manifests and automatically assigns granular capability profiles (`fs.read`, `web`, `shell`).
- **Drift Detection via Fingerprinting:** Computes a SHA-256 fingerprint of the MCP server's declared tool schemas (`_fingerprint()` in `rad/skills.py:51`). If an external MCP server mutates its tool definitions post-installation, RAD detects the schema drift and automatically demotes the skill's authority to interactive `ASK` approval.

---

### 2.4 Memory Socket (Layered Epistemic Hierarchy & Knowledge Graphs)

RAD implements a biologically-inspired, multi-tiered memory architecture (`rad/memory.py`, `rad/usermodel.py`, `rad/world.py`) that guarantees data durability and auditability.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAD 4-TIER MEMORY HIERARCHY                     │
├────────────────────────────────────────────────────────────────────────┤
│ 1. SENSORY MEMORY (RAM)                                                │
│    - Current turn raw input buffer, audio waveforms, visual frames     │
├────────────────────────────────────────────────────────────────────────┤
│ 2. WORKING MEMORY (RAM)                                                │
│    - Active conversation window, capped strictly at 24 messages        │
├────────────────────────────────────────────────────────────────────────┤
│ 3. SHORT-TERM MEMORY (Disk)                                            │
│    - Append-only daily interaction logs (~/.rad/memory/short/YYYY-MM-DD) │
├────────────────────────────────────────────────────────────────────────┤
│ 4. LONG-TERM MEMORY (Disk Markdown + Frontmatter)                      │
│    - Episodic: Goal outcomes, task execution history, incident events  │
│    - Semantic: General knowledge, validated user facts, preferences    │
│    - Procedural: Operational recipes, repair patterns, coding loops    │
├────────────────────────────────────────────────────────────────────────┤
│ 5. ARCHIVE MEMORY (Disk)                                               │
│    - Decayed memories (strength < 0.1), preserved for audit history    │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2.4.1 Epistemic Provenance Attributes
Unlike naive vector stores that merge facts indiscriminately, every memory entry in RAD carries four mandatory epistemic attributes (`rad/memory.py:62-109`):
1. **`origin`:** Establishes source authority:
   - `USER_PROVIDED` (Base Confidence: 0.9): Explicit user statements or pinned configuration.
   - `OBSERVED` (Base Confidence: 0.8): First-hand tool output (e.g., file read, command stdout).
   - `INFERRED` (Base Confidence: 0.5): Deductions derived by heuristic evaluation.
   - `MODEL_GENERATED` (Base Confidence: 0.4): Synthetic LLM summarization.
2. **`confidence`:** Float value $\in [0.0, 1.0]$, dynamically reinforced upon independent re-observation.
3. **`verification`:** Tri-state verification flag: `VERIFIED`, `UNVERIFIED`, or `CONTRADICTED`.
4. **`source`:** Exact URI, file location, or objective/task execution ID.

**The Epistemic Precedence Law:**
$$\text{Origin}_{\text{infer/model}} \text{ cannot overwrite } \text{Origin}_{\text{user/observed}}$$
When an incoming inferred fact disputes an established user-provided fact, the user fact remains ground truth. The dispute is appended to `disputed_by` without mutating the primary belief (`rad/usermodel.py:69-75`).

#### 2.4.2 Non-Destructive Contradiction Handling
Contradiction handling is explicit and penalizing rather than destructive (`rad/memory.py:193-205`):
- Semantic overlap combined with polar opposition (e.g. "User prefers tabs" vs "User prefers spaces") triggers contradiction linking.
- Contradicting entries are cross-referenced in their respective `contradicts` metadata lists.
- The lower-confidence entry is marked `verification = CONTRADICTED` and receives an immediate **70% trust penalty**:
  $$\text{Trust} = \text{Confidence} \times 0.3$$
- Contradicted memories rank at the bottom during retrieval recall and experience accelerated decay during consolidation.

#### 2.4.3 Sleep Consolidation & Memory Maintenance
Executing `rad sleep` (`rad/sleep.py`) initiates memory consolidation:
1. Short-term logs (`~/.rad/memory/short/*.md`) are distilled into episodic, semantic, or procedural long-term markdown files.
2. Unused entries experience time-based exponential decay.
3. Entries decaying below strength $0.1$ are migrated to `~/.rad/memory/archive/`. Memories are never silently deleted.
4. Mtime directory caching (`_signature()` at `rad/memory.py:119`) prevents redundant disk re-parsing during recall operations.

#### 2.4.4 Structured User Model (`user.json`)
Maintains an 8-facet belief structure: `preferences`, `goals`, `projects`, `constraints`, `routines`, `communication`, `active_priorities`, and `permissions`. Injected into prompt contexts as a compact, structured summary.

#### 2.4.5 World Model & Embedded Kuzu Cypher Graph
The World Model (`rad/world.py`) models environmental entities and relationships:
- Persisted locally as an Entity-Relation graph in `~/.rad/world/graph.json`.
- **Temporal Superseding:** Relationships carry temporal bounds (`since`, `until`, `status`). When a newer relation contradicts an existing functional relation (e.g. `located_in`), the prior relation is marked `status: superseded` with `until = timestamp`.
- **Kuzu Cypher Mirror:** Running `rad world sync` mirrors entities and edges into an embedded **Kuzu Graph Database**, enabling zero-overhead local Cypher queries (`MATCH (a:Entity)-[r:Rel]->(b:Entity) RETURN a, r, b`).

#### 2.4.6 Cloud Mind Sync (Google Drive)
Provides optional, offsite disaster recovery via Google Drive API v3 (`rad/drive.py`). Uses restricted scope `drive.file`, synchronizing encrypted memory bundles without exposing plaintext credentials or private keys.

---

### 2.5 Voice Socket (Acoustic Perception & Speech Synthesis)

The Voice Socket (`rad/voice.py`) establishes a bi-directional acoustic pipeline prioritizing free, offline, local execution.

- **Audio Capture:** Standardized on 16 kHz 16-bit mono PCM WAV recording (`record_wav` at line 107).
- **Speech-to-Text (STT):** Local transcription uses Whisper via local CLI or `faster-whisper` (`stt_whisper` at line 132). Falls back to OpenAI Whisper API when local models are absent.
- **Text-to-Speech (TTS):** Local synthesis utilizes **Piper ONNX** (`tts_piper` at line 39), streaming text to the `piper` executable and synthesizing WAV audio in near real-time without cloud dependencies or GPU requirements. Falls back to OpenAI `tts-1` when configured.
- **Platform Audio Output:** Automatically abstracts OS-level audio playback engines (`afplay` on macOS, `ffplay`, `mpg123`, or `aplay` on Linux/Windows).

---

### 2.6 Face Socket (Terminal, Loopback HTTP API & Tauri 2 Desktop Surface)

The Face Socket exposes the agent's cognitive capabilities to human operators across three interaction surfaces:

1. **Terminal REPL (`rad/cli.py`, `rad/session.py`):** Interactive TTY interface featuring streaming markdown, ANSI styling (`rad/ui.py:C`), session persistence, and command dispatch.
2. **Loopback HTTP REST API (`rad/api.py`):** Multi-threaded HTTP server (`ThreadingHTTPServer`) bound strictly to loopback `127.0.0.1`. Requires bearer token authentication via `~/.rad/api.token` (enforcing `0600` file permissions). Exposes 22 standardized endpoints:
   - System: `/v1/health`, `/v1/status`, `/v1/config`, `/v1/version`, `/v1/ping`
   - Governance: `/v1/authority`, `/v1/policy`
   - Operations: `/v1/objectives`, `/v1/objectives/{id}`, `/v1/objectives/{id}/pause`, `/v1/objectives/{id}/resume`, `/v1/objectives/{id}/cancel`
   - Cognition: `/v1/chat`, `/v1/memory`, `/v1/memory/recall`, `/v1/tools`, `/v1/agents`, `/v1/models`
3. **Desktop Surface (`desktop/`):** Dedicated Tauri v2 GUI application running React 18, TypeScript, and Vite. Implements full visual orchestration of active runs, objective DAG inspection, memory curation, and verification auditing.

---

## 3. Control Plane Governance & Autonomous Execution

The Control Plane (`rad/control/`) orchestrates autonomous, multi-step goal resolution. Rather than relying on unstructured LLM loops, RAD implements a formally verified supervisory state machine.

```
                             ┌────────────────────────────────────────┐
                             │            OBJECTIVE RUN               │
                             └───────────────────┬────────────────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │   PLANNER (LLM/DAG)   │
                                     └───────────┬───────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  TASK GRAPH SCHEDULER │
                                     └───────────┬───────────┘
                                                 │
                       ┌─────────────────────────┴─────────────────────────┐
                       ▼                                                   ▼
            ┌─────────────────────┐                             ┌─────────────────────┐
            │   TASK (READY)      │                             │   TASK (READY)      │
            └──────────┬──────────┘                             └──────────┬──────────┘
                       │                                                   │
                       ▼                                                   ▼
            ┌─────────────────────┐                             ┌─────────────────────┐
            │ EXECUTOR (SESSION)  │                             │ EXECUTOR (SESSION)  │
            │ Sandbox → Gate      │                             │ Sandbox → Gate      │
            └──────────┬──────────┘                             └──────────┬──────────┘
                       │                                                   │
                       ▼                                                   ▼
            ┌─────────────────────┐                             ┌─────────────────────┐
            │ OBSERVER / ARTIFACTS│                             │ OBSERVER / ARTIFACTS│
            └──────────┬──────────┘                             └──────────┬──────────┘
                       │                                                   │
                       ▼                                                   ▼
            ┌─────────────────────┐                             ┌─────────────────────┐
            │  MACHINE VERIFIER   │                             │  MACHINE VERIFIER   │
            └──────────┬──────────┘                             └──────────┬──────────┘
                       │                                                   │
                       ├─── [FAILED] ──► RECOVERY ENGINE (10 Strategies) ──┤
                       │                                                   │
                       ▼                                                   ▼
                [COMPLETED]                                         [COMPLETED]
                       │                                                   │
                       └─────────────────────────┬─────────────────────────┘
                                                 │
                                                 ▼
                                     ┌───────────────────────┐
                                     │  OBJECTIVE VERIFIER   │
                                     └───────────┬───────────┘
                                                 │
                             ┌───────────────────┴───────────────────┐
                             ▼                                       ▼
                        COMPLETED                                NEEDS_USER /
                       (VERIFIED)                                  FAILED
```

---

### 3.1 Central Controller Execution Loop

The core execution engine is encapsulated in `Controller._drive()` (`rad/control/controller.py:291-416`):
1. **Locking & Resumption:** Acquires an exclusive filesystem lock on `~/.rad/objectives/<id>/lock` to prevent concurrent execution conflicts.
2. **Budget Monitoring:** Initializes `BudgetManager`. On every iteration step, `BudgetManager.tick()` evaluates resource consumption against configured limits (tool calls, model calls, execution seconds, USD cost).
3. **Doom Propagation:** Invokes `scheduler.block_doomed(graph)`. If a prerequisite task fails permanently without remaining retries, all downstream dependents are transitioned to `BLOCKED`.
4. **Batch Scheduling:** Resolves runnable tasks via `scheduler.next_batch(graph)` (supporting parallel execution up to `objective_parallel = 2`).
5. **Session Execution:** Dispatches runnable tasks through `Executor`. Tools execute inside `Sandbox`, passing through `_gate()` and `Policy.decide()`.
6. **Observation & Artifact Ingestion:** `Observer` captures tool outputs, standard error, exit codes, and newly created files.
7. **Verification & State Checkpointing:** Evaluates Level 1 through Level 5 verification checks. Writes atomic checkpoints to `checkpoint.json` and appends immutable events to `events.jsonl`.
8. **Objective-Level Verification:** Upon completion of all tasks in the DAG, executes top-level acceptance verification against overall objective goals.

---

### 3.2 11-State Task Finite State Machine (FSM)

Task progression is strictly governed by the 11-state FSM defined in `rad/control/tasks.py`:

```
       ┌───────────┐       ┌───────────┐       ┌───────────┐
       │  PENDING  ├──────►│   READY   ├──────►│  RUNNING  │
       └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
             │                   │                   │
             │                   ▼                   ▼
             │             ┌───────────┐       ┌───────────┐
             │             │  BLOCKED  │       │ OBSERVING │
             │             └───────────┘       └─────┬─────┘
             │                                       │
             ▼                                       ▼
       ┌───────────┐                           ┌───────────┐
       │ CANCELLED │                           │ VERIFYING │
       └───────────┘                           └─────┬─────┘
                                                     │
                             ┌───────────────────────┴───────────────────────┐
                             ▼                                               ▼
                      ┌─────────────┐                                 ┌─────────────┐
                      │  COMPLETED  │                                 │   FAILED    │
                      └─────────────┘                                 └──────┬──────┘
                                                                             │
                                           ┌─────────────────────────────────┼──────────────────┐
                                           ▼                                 ▼                  ▼
                                    ┌─────────────┐                   ┌─────────────┐    ┌─────────────┐
                                    │  RETRYING   │                   │ NEEDS_USER  │    │   BLOCKED   │
                                    └──────┬──────┘                   └─────────────┘    └─────────────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │    READY    │
                                    └─────────────┘
```

#### Transition Invariants:
- The `ALLOWED` mapping (`rad/control/tasks.py:47-60`) defines all legal state transitions.
- Attempting an undeclared transition raises `IllegalTransition`.
- Every transition automatically updates `task.updated_at`, appends an entry to `task.history` (`{"from": s1, "to": s2, "at": ts, "note": note}`), and emits a structured event to `events.jsonl`.

---

### 3.3 Task Graph (DAG) Scheduling & Yielding Mechanics

`TaskGraph` (`rad/control/graph.py`) manages dependencies and execution topology:
- **Dependency Resolution:** A task enters `READY` when all identifiers in its `depends_on` list are marked `COMPLETED`.
- **Doom Propagation (`block_doomed`):** When any task reaches terminal failure (`FAILED` with exhausted retries, `CANCELLED`, or `BLOCKED`), all reachable descendants in the DAG are immediately marked `BLOCKED`.
- **Leftover-Budget Yielding (`should_yield_for_leftover`):** To prevent early greedy tasks from consuming an objective's entire tool budget, the scheduler evaluates remaining tool call headroom. If a sequential task exhausts its local budget slice, the scheduler forces a yield, preserving budget allocations for independent sibling tasks.
- **Clause-Split Fallback:** When complex objectives are decomposed into clause tasks for independent file generation, dependencies are generated with empty `depends_on` sets (`budgetplan.py:empty_depends_on`), enabling maximal parallel scheduling.

---

### 3.4 5-Level Independent Machine Verifier

Verification is performed exclusively by `Verifier` (`rad/control/verifier.py:34-117`). It implements a 5-tier hierarchical verification stack:

```
┌────────────────────────────────────────────────────────────────────────┐
│                  5-LEVEL INDEPENDENT MACHINE VERIFIER                  │
├─────────┬──────────────────────┬───────────────────────────────────────┤
│ Level   │ Verification Tier    │ Target / Mechanism                    │
├─────────┼──────────────────────┼───────────────────────────────────────┤
│ Level 1 │ Tool Verification    │ Exit codes == 0; filters harmless     │
│         │                      │ thrashing (is_first_task_thrash_noise)│
├─────────┼──────────────────────┼───────────────────────────────────────┤
│ Level 2 │ Explicit Checks      │ Deterministic machine evaluations:    │
│         │                      │ file_exists, shell_ok, json_valid,    │
│         │                      │ file_contains, file_line_count, etc.  │
├─────────┼──────────────────────┼───────────────────────────────────────┤
│ Level 3 │ Artifact Verification│ Registered output files exist, non-   │
│         │                      │ empty, devoid of fake 'DONE:' claims  │
├─────────┼──────────────────────┼───────────────────────────────────────┤
│ Level 4 │ Evidence Verification│ Numerical/factual claims grounded in  │
│         │                      │ local observed data vs untrusted web  │
├─────────┼──────────────────────┼───────────────────────────────────────┤
│ Level 5 │ Safety Verification  │ Confirms 0 policy or sandbox breaches │
└─────────┴──────────────────────┴───────────────────────────────────────┘
```

#### Explicit Machine Check Inventory:
- `file_exists`: Verifies target file exists on disk.
- `file_contains`: Verifies exact substring match inside target file.
- `file_line_count`: Verifies exact line count matches expected integer.
- `file_min_bytes`: Verifies file size exceeds minimum byte threshold.
- `shell_ok`: Runs shell command; expects returncode 0.
- `shell_output`: Runs shell command; matches stdout against regex/substring.
- `json_valid`: Verifies file parses strictly under `json.loads()`.
- `json_field`: Verifies specific key exists in JSON structure with truthy value.
- `json_min_len`: Verifies JSON array or dictionary meets minimum length.
- `reply_matches`: Evaluates regex match on final assistant response.
- `llm_judge`: **Advisory Only** (`machine: false`). An LLM opinion can FAIL a task, but can **NEVER** mark a task `VERIFIED`.
- `agent_review`: **Advisory Only** (`machine: false`). Independent peer review.

#### The Core Verification Invariant:
$$\text{Task} \in \text{VERIFIED} \iff (\text{Passed Machine Checks} \ge 1 \lor \text{Valid Artifact Checks} \ge 1) \land (\text{Failed Machine Checks} = 0)$$

If no machine checks were configured, the task completes as `UNVERIFIED`. A model's verbal declaration is rejected as verification evidence.

---

### 3.5 Recovery Engine & Error Taxonomy

The Recovery Engine (`rad/control/recovery.py`) classifies runtime failures into 11 discrete categories and maps them to bounded recovery strategies.

| Failure Class | Trigger Signals / Regex | Deterministic Strategy | Mitigation & Action |
|---|---|---|---|
| **`AUTH_FAILURE` / `RATE_LIMIT`** (Class C) | HTTP 401, 403, 429, quota exhausted, token expired | `ask_user` / Pause | Records Class C in `provider_health.json`. Pauses objective in `NEEDS_USER` with `class_c_next_steps`. Prohibits hallucinated Class A code refactoring. |
| **`PERMISSION_FAILURE`** | Safety policy denial, sandbox escape attempt, protected path access | `retry_with_hint` | Injects explicit policy denial rationale into hint, forcing model to choose alternate, workspace-compliant path. |
| **`MODEL_FAILURE`** | Provider 5xx error, socket hangup, empty completions | `switch_model` / `retry` | Rotates provider to next available engine in routing chain; blacklists failing provider temporarily. |
| **`TRANSIENT` / `NETWORK`** | Connection reset, read timeout, transient HTTP 502/503 | `retry` | Performs exponential backoff retry within remaining retry budget. |
| **`ENVIRONMENT_FAILURE`** | Missing compiler, command not found, binary not on PATH | `repair` | Injects a single specialized prerequisite installation task (`Repair prerequisite: ...`) into the DAG. |
| **`VALIDATION_FAILURE`** (Broken Artifact) | `json_valid` fail, `shell_ok` exit != 0, syntax error in generated code | `repair` $\to$ `retry_with_hint` | Injects compiler stderr or parser error into hint for targeted repair; triggers single replan if repeated. |
| **`VALIDATION_FAILURE`** (Missing File) | Target file missing, `file_exists` check failed | `retry_with_hint` | Retries task with explicit failure feedback identifying missing artifact path. |
| **`PLANNING_FAILURE`** | Malformed JSON plan, cyclic graph, empty task list | `replan` | Retries JSON plan generation once; falls back to deterministic rule-based template if unrecovered. |
| **`BUDGET`** | Exceeded tool calls, model calls, elapsed seconds, or USD spend | `ask_user` / Abort | Halts execution, records budget exhaustion event, requests user authorization to raise limits. |
| **`UNKNOWN`** | Unclassified runtime exceptions | `retry_with_hint` | Bounded retry with complete exception traceback injected into dialogue. |

---

### 3.6 Multi-Agent Coordination & Capability Envelopes

RAD provides native multi-agent coordination (`rad/agents.py`, `rad/team.py`):
- **Specialist Roles:** `AgentRegistry` declares 9 specialized roles: `planner`, `researcher`, `coder`, `tester`, `reviewer`, `writer`, `analyst`, `security`, and `browser_agent`.
- **Capability Envelopes:** Sub-agents are restricted to explicit capability subsets declared in `AgentSpec.caps`. A sub-agent cannot invoke tools outside its envelope; violations are rejected at the `Policy.decide` choke point via `ToolCtx.agent_caps`.
- **Shared Blackboard:** Agents coordinate asynchronously by posting notes, findings, and evidence links to a per-objective file (`~/.rad/agents/blackboard/<obj_id>.json`).
- **Coordination Modes:** Supports `solo` mode (independent specialist generation followed by synthesis) and `debate` mode (multi-turn adversarial critique evaluated by a `reviewer` prior to executive synthesis).

---

## 4. Safety, Policy Engine & Security Architecture

RAD enforces a defense-in-depth security model centered on a single, mandatory enforcement choke point.

```
 [ANY CALLER: CLI, API, Controller, Sub-Agent, Jerry, Desktop, MCP]
                               │
                               ▼
                   run_tool() in rad/tools.py
                               │
                               ▼
                   _gate() in rad/tools.py
                               │
                               ▼
                  Policy.decide() in rad/policy.py
                               │
    ┌──────────────────────────┴──────────────────────────┐
    ▼                                                     ▼
[HARD LAYER: UNBYPASSABLE CODE]              [SOFT LAYER: POLICY RULES]
- HARD_SHELL regex blocklist                 - Capability Defaults (ALLOW/ASK/DENY)
- HARD_PATH_PARTS secret path jail           - Glob matching rules
- HARD_HOSTS private egress block            - Scope checks (workspace_only)
- Secret Redaction on all outputs            - Limited constraints (timeout, max_bytes)
- Subprocess env credential stripping        - Authority Profile (SAFE/AUTONOMOUS/etc)
    │                                                     │
    └──────────────────────────┬──────────────────────────┘
                               │
                               ▼
                DECISION: ALLOW | ASK | DENY |
             HARD_DENY | LIMITED | SCOPE_VIOLATION
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
    [ALLOW]                  [ASK]              [DENY / VIOLATION]
Execute via             Interactive TTY         Append to audit log
Sandbox / Shell         Prompt / Confirm        Raise PolicyDenied
       │                       │                       │
       ▼                       ▼                       ▼
   Tool Output           User Approves?          Tool Blocked
       │                       │
       ▼                       ▼
   Redact Secrets         Execute Tool
```

---

### 4.1 Single Enforcement Point Choke Point

Every tool execution attempt across the entire repository—originating from the CLI REPL, the Autonomous Controller, a background worker, Jerry, an MCP skill, or the Tauri desktop—must invoke `rad.tools.run_tool()`. Within `run_tool()`, execution passes unconditionally through `_gate()` and invokes `Policy.decide()` (`rad/policy.py:202-268`). There is no secondary, alternative, or bypass execution path in the codebase.

---

### 4.2 The Unbypassable Hard Layer

The Hard Layer is hardcoded in Python logic and cannot be overridden by user configuration, CLI flags (`--auto`), environment variables, or prompt injection:

1. **Destructive Shell Blocklist (`HARD_SHELL`):** Matches dangerous shell commands using regular expressions:
   - Root privilege escalation: `sudo`, `su root`
   - Filesystem destruction: `rm -rf /`, `rm -rf ~`, `mkfs`, `dd if=`
   - System disruption: `shutdown`, `reboot`, fork bombs (`:(){ :|:& };:`)
   - Unvetted execution pipelines: `curl ... | sh`, `wget ... | bash`
   - Raw disk manipulation: `> /dev/sd*`, `chmod -R 777 /`
   - Destructive VCS: `git push --force`
2. **Irreversible Recursive Delete Guard (`_rm_is_destructive`):** Rejects any `rm` command combining recursive (`-r`, `-R`, `--recursive`) and force (`-f`, `--force`) flags, regardless of target path.
3. **Secret Path Protection (`HARD_PATH_PARTS` & `HARD_PATH_NAMES`):** Denies read/write access to sensitive files and directories: `.rad/keys`, `.vault.key`, `~/.ssh/`, `/etc/shadow`, `.git-credentials`, `.netrc`, `.aws/credentials`, and `keys.env`.
4. **SSRF Private Network Egress Blocking (`HARD_HOSTS`):** Blocks outbound network requests to `localhost`, `127.0.0.1`, `0.0.0.0`, RFC 1918 private subnets (`10.*`, `192.168.*`, `172.16-31.*`), link-local `169.254.*`, IPv6 loopback `::1`, and cloud instance metadata services (`metadata.google.internal`).
5. **Universal Secret Token Redaction (`redact`):** Every text output returned by any tool is filtered through sanitizing regexes stripping OpenAI API keys (`sk-...`), GitHub tokens (`ghp_...`), AWS credentials (`AKIA...`), Slack tokens (`xox...`), Bearer headers, and private SSH/RSA keys.
6. **Subprocess Environment Scrubbing (`_shell_env`):** Subprocess shells execute with an environment stripped of any variable matching `KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `PASSWD`, or `CREDENTIAL`, preventing child processes from harvesting host secrets.

---

### 4.3 Soft Policy Rules & Glob Matching

The Soft Layer (`rad/policy.py`) evaluates configurable policy rules defined in `~/.rad/policy.json`:
- **Rule Structure:** Each rule matches a `capability` (e.g. `fs.read`, `fs.write`, `shell`, `web`) and a path/command glob pattern (e.g. `workspace/**`, `git status`).
- **Evaluation Order:** Evaluated sequentially; the first matching rule returns a decision (`ALLOW`, `ASK`, `LIMITED`, `DENY`).
- **Scope Checking:** If `workspace_only` is active, file operations resolving outside `home.workspace()` are rejected with `SCOPE_VIOLATION`.

---

### 4.4 Authority Profiles & Permissions Matrix

Authority Profiles (`rad/authority.py`) package policy rules into clear operational postures:

```
┌─────────────────┬──────────┬──────────────┬───────────────┬─────────────────┬──────────────┐
│ Capability      │ SAFE     │ STANDARD     │ AUTONOMOUS    │ UNRESTRICTED    │ SUB-AGENT    │
├─────────────────┼──────────┼──────────────┼───────────────┼─────────────────┼──────────────┤
│ `fs.read`       │ ALLOW    │ ALLOW        │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `fs.write`      │ DENY     │ ASK          │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `shell`         │ DENY     │ ASK          │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `py.run`        │ DENY     │ ASK          │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `web`           │ ASK      │ ALLOW        │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `browser`       │ ASK      │ ALLOW        │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `mcp`           │ DENY     │ ASK          │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `packages`      │ DENY     │ ASK          │ ALLOW         │ ALLOW           │ Envelope-gated│
│ `agents.spawn`  │ DENY     │ ASK          │ ALLOW         │ ALLOW           │ DENY         │
│ `credentials`   │ HARD-DENY│ HARD-DENY    │ HARD-DENY     │ HARD-DENY       │ HARD-DENY    │
│ `model.free`    │ ALLOW    │ ALLOW        │ ALLOW         │ ALLOW           │ ALLOW        │
│ `model.paid`    │ DENY     │ Config-gated │ Config-gated  │ ALLOW           │ Config-gated │
│ Confirmation    │ `ask`    │ `ask`        │ `never`       │ `never`         │ N/A          │
│ Workspace Scope │ Strict   │ Strict       │ Strict        │ User-Configured │ Strict       │
└─────────────────┴──────────┴──────────────┴───────────────┴─────────────────┴──────────────┘
```

- **`SAFE`:** Read-only mode. All write, execution, shell, package, and paid model capabilities are strictly denied.
- **`STANDARD`:** Default interactive posture. Safe read operations are allowed; state mutations prompt for interactive user confirmation.
- **`AUTONOMOUS`:** Sets confirmation to `never` for granted capabilities, allowing automated execution. Hard layer, budgets, and audit logs remain strictly enforced.
- **`UNRESTRICTED`:** High-autonomy operational mode. Requires explicit operator authorization (`--i-authorize-unrestricted` on CLI or `confirm_unrestricted: true` on API). Expands capability grants, but **never** bypasses `Policy.decide`, the unbypassable hard blocklists, budgets, audit logging, or verification requirements.
- **`CUSTOM`:** Granular user-defined rule overrides.

---

## 5. Desktop Surface Architecture

RAD Desktop (`desktop/`) delivers a graphical interaction surface built using **Tauri v2 + React 18 + TypeScript + Vite**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAD DESKTOP SURFACE ARCHITECTURE                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
 ┌──────────────────────────────────┴──────────────────────────────────┐
 │ 1. FRONTEND WEBVIEW (React 18 + TypeScript + Vite)                  │
 │    - Views: ActiveRun, ObjectiveDetail, Memory, ToolsTrace, etc.    │
 │    - Typed API Client: `desktop/src/api.ts`                         │
 │    - State polling: `desktop/src/hooks/usePolling.ts`               │
 │    - Containment: Zero node/process APIs; loopback-only CSP         │
 └──────────────────────────────────┬──────────────────────────────────┘
                                    │
                          HTTP /v1/* (Bearer Token)
                                    │
 ┌──────────────────────────────────┴──────────────────────────────────┐
 │ 2. TAURI RUST CORE (`desktop/src-tauri/src/lib.rs`)                 │
 │    - IPC Commands: `backend_start`, `backend_stop`, `backend_info`, │
 │      `default_home`, `api_token`                                    │
 │    - Process Supervisor: Spawns fixed argv `rad serve`              │
 │    - Security: No arbitrary command execution; no shell plugin      │
 └──────────────────────────────────┬──────────────────────────────────┘
                                    │
                        Loopback HTTP (127.0.0.1:7331)
                                    │
 ┌──────────────────────────────────┴──────────────────────────────────┐
 │ 3. RAD CORE ENGINE (`rad serve` via `rad/api.py`)                   │
 │    - `ThreadingHTTPServer` bound strictly to loopback               │
 │    - Bearer authentication via `~/.rad/api.token` (0600)            │
 │    - Controller, Session, Executor, Policy.decide, Tool execution   │
 └─────────────────────────────────────────────────────────────────────┘
```

---

### 5.1 Process Lifecycle & Sidecar Management

The desktop application manages the RAD Python backend via `desktop/src-tauri/src/lib.rs`:
- **Fixed Invocation Contract:** The backend process is launched using an immutable command array:
  `Command::new(python_bin()).args(["-m", "rad", "serve", "--host", "127.0.0.1", "--port", ...])` or by executing the bundled sidecar binary `binaries/rad`. User-controlled strings are never passed to shell interpreters or process launchers.
- **Token Discovery:** The webview obtains authentication credentials via the `api_token` Tauri IPC command, which reads `~/.rad/api.token` directly from host storage, ensuring secrets are never serialized into frontend configuration bundles.
- **Process Supervision:** The Rust backend maintains a child process handle in a thread-safe `Mutex<Option<Backend>>`, guaranteeing graceful termination (`backend_stop`) upon application exit.

---

### 5.2 Tauri v2 Rust Backend & Capability Boundaries

Tauri v2 enforces strict capability isolation:
- **Zero Shell Plugins:** The crate explicitly omits `tauri-plugin-shell`. Arbitrary process execution is architecturally impossible from the webview.
- **Permission Scoping:** `desktop/src-tauri/permissions/backend.toml` authorizes exactly 5 commands: `allow-backend-start`, `allow-backend-stop`, `allow-backend-info`, `allow-api-token`, and `allow-default-home`.
- **Capability Binding:** `desktop/src-tauri/capabilities/default.json` restricts the `main` window to these five commands alongside default Tauri window management permissions.

---

### 5.3 React/TypeScript Frontend Architecture & Containment

The frontend (`desktop/src/`) is fully typed under TypeScript 5.7:
- **`RadClient` (`desktop/src/api.ts`):** Centralized HTTP client communicating with `rad serve` over loopback. Implements 27 strictly declared endpoints.
- **Settings Safe Keys:** When operators edit settings in the GUI, `api.ts` filters payload updates against `SETTINGS_SAFE_KEYS` (`workspace`, `free_lock`, `force_provider`, `model`, `tts`, `stt`, `allow_outside_workspace`, `allow_localhost_web`).
- **Control-Plane Configuration Lock:** The frontend is strictly forbidden from modifying control-plane keys (`FORBIDDEN_CONTROL_KEYS`: `tool_calls`, `model_calls`, `retries`, `seconds`, `money_usd`, `tokens`, `agents`, `auto`, `tool_router`, `max_plan_tasks`, `budget`). The frontend cannot increase budgets, bypass policy, or enable experimental routers.
- **Verification Visualization:** `VerificationCard.tsx` renders verification evidence directly from the control plane. If machine checks are missing, it renders the invariant:
  $$\text{"No machine-check pass } \implies \text{No VERIFIED"}$$

---

### 5.4 Loopback Security Guarantees & Control-Plane Locks

Static security tests (`tests/test_desktop_security_surface.py`) enforce the following security invariants:
1. **Loopback-Only Content Security Policy (CSP):** `tauri.conf.json` enforces:
   `default-src 'self'; connect-src 'self' http://127.0.0.1:* http://localhost:*; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:`
   All external HTTPS network requests from the webview are blocked by the browser engine.
2. **Absence of Dangerous Primitives:** Static inspection confirms zero occurrences of `child_process`, `exec`, `spawn`, or Node `fs` in the frontend source.
3. **Absence of Direct Shell Route:** The backend API exposes no `/v1/shell` endpoint.

---

## 6. Formal Ledger of Architectural Invariants

The RAD Agent system is governed by ten immutable architectural laws, verified continuously across the test suite:

### 6.1 The Ten Non-Negotiable Invariants

| # | Invariant Name | Architectural Law | Code Enforcement Point | Test Verification Reference |
|---|---|---|---|---|
| **I-1** | **Independent Machine Verification** | Nothing is `VERIFIED` without a passing machine check (`file_exists`, `shell_ok`, `json_valid`, etc.). Model or reviewer opinions can fail a task, never pass it. | `rad/control/verifier.py:101-110` | `tests/test_control_plane.py`, `tests/test_verified_coding_loop.py` |
| **I-2** | **Single Enforcement Choke Point** | Every tool call across REPL, Control Plane, sub-agents, Jerry, MCP skills, and desktop MUST pass through `Policy.decide()`. | `rad/tools.py:_gate()`, `rad/policy.py:decide()` | `tests/test_policy.py`, `tests/test_authority.py` |
| **I-3** | **Unbypassable Hard Layer** | Dangerous shell commands, destructive `rm -rf`, secret file access, and private network egress cannot be enabled by config, `--auto`, or authority profiles. | `rad/policy.py:HARD_SHELL`, `hard_check_path` | `tests/test_policy.py`, `tests/test_hardening.py` |
| **I-4** | **Explicit Persisted State** | Goals, tasks, checkpoints, artifacts, events, memory, and audit records are plain, human-readable files under `~/.rad`. No hidden database state. | `~/.rad/objectives/`, `~/.rad/audit.jsonl` | `tests/test_storage.py`, `tests/test_control2.py` |
| **I-5** | **Universal Epistemic Provenance** | Every memory, user fact, and world relation carries `origin`, `confidence`, and `verification`. Weaker origins never overwrite stronger ones. Contradictions are linked, not merged. | `rad/memory.py:add()`, `rad/usermodel.py:set()` | `tests/test_memory.py`, `tests/test_memory2.py` |
| **I-6** | **Evolution Cannot Touch Code** | Self-evolution rewrites prompt templates, persona, lessons, and style files only. Python source code is write-protected from agent evolution. | `rad/dna.py:evolve()`, `rad/evolution.py` | `tests/test_evolution.py`, `tests/test_evolve2.py` |
| **I-7** | **Graceful Degradation** | Corrupt state files are quarantined rather than deleted; storage layers fall back to defaults on unparseable data. System degrades safely rather than crashing. | `rad/storage.py`, `rad/home.py:_read_json` | `tests/test_storage.py`, `tests/test_reliability.py` |
| **I-8** | **Free-First Economic Doctrine** | Local runtimes and free cloud tiers are always prioritized. Paid model spend is impossible without explicit user enablement (`free_lock=false`). | `rad/router.py:build_chain()` | `tests/test_router.py`, `tests/test_modelselect.py` |
| **I-9** | **Jerry Operator Containment** | Jerry is strictly an operator and chat layer. Jerry has no tool execution runner and cannot invoke `Policy.decide` or tools directly. | `rad/jerry.py:__getattr__()` | `tests/test_jerry.py` |
| **I-10** | **Needle Non-Sovereignty** | The experimental Needle tool router may only *propose* function call arguments. Needle never executes tools, never bypasses policy, and is OFF by default. | `rad/toolrouter.py:resolve_tool_router` | `tests/test_toolrouter.py`, `docs/ADR-001-NEEDLE-TOOL-ROUTER.md` |

---

### 6.2 Authority & Capability Matrix

```
┌────────────────────┬───────────┬──────────────┬───────────────┬─────────────────┐
│ Capability         │ SAFE      │ STANDARD     │ AUTONOMOUS    │ UNRESTRICTED    │
├────────────────────┼───────────┼──────────────┼───────────────┼─────────────────┤
│ `fs.read`          │ ALLOW     │ ALLOW        │ ALLOW         │ ALLOW           │
│ `fs.write`         │ DENY      │ ASK          │ ALLOW         │ ALLOW           │
│ `shell`            │ DENY      │ ASK          │ ALLOW         │ ALLOW           │
│ `py.run`           │ DENY      │ ASK          │ ALLOW         │ ALLOW           │
│ `web`              │ ASK       │ ALLOW        │ ALLOW         │ ALLOW           │
│ `browser`          │ ASK       │ ALLOW        │ ALLOW         │ ALLOW           │
│ `mcp`              │ DENY      │ ASK          │ ALLOW         │ ALLOW           │
│ `packages`         │ DENY      │ ASK          │ ALLOW         │ ALLOW           │
│ `agents.spawn`     │ DENY      │ ASK          │ ALLOW         │ ALLOW           │
│ `credentials`      │ HARD-DENY │ HARD-DENY    │ HARD-DENY     │ HARD-DENY       │
│ `model.free`       │ ALLOW     │ ALLOW        │ ALLOW         │ ALLOW           │
│ `model.paid`       │ DENY      │ Config-gated │ Config-gated  │ ALLOW           │
│ Confirmation Policy│ `ask`     │ `ask`        │ `never`       │ `never`         │
│ Workspace Scope    │ Strict    │ Strict       │ Strict        │ User-Configured │
└────────────────────┴───────────┴──────────────┴───────────────┴─────────────────┘
```

---

## 7. Active Development State & Verification Requirements

### 7.1 Empirical Baseline & Diagnostics

Empirical audits conducted on the host environment (`Windows 11 AMD64`, `Python 3.14.6`, `pytest 9.1.1`):

1. **CLI Version Command:**
   - Command: `python -m rad.cli version`
   - Outcome: Exits 0, outputs `rad v1.0.1`.
2. **CLI Doctor Command:**
   - Command: `python -m rad.cli doctor --offline`
   - Outcome: Exits 0. Reports 18 READY · 2 WARNING · 3 OPTIONAL · 0 ERROR.
   - Diagnostic: The 2 warnings (`permissions` and `integrity`) are caused by POSIX permission mask checks (`mode & 0o077`) executed against Windows NTFS filesystems.
3. **Desktop Surface Test Suite:**
   - Command: `python -m pytest -q tests/test_desktop_*.py`
   - Outcome: **25 passed out of 25 in 15.02s (100% pass rate)**.
4. **Desktop Frontend Build:**
   - Command: `npm run build` (in `desktop/`)
   - Outcome: Exits 0. 38 modules transformed, generating a 182.77 kB production bundle in `desktop/dist/`.
5. **Full Repository Test Suite Baseline:**
   - Command: `python -m pytest -q`
   - Outcome: **695 passed, 23 failed, 1 skipped (96.8% pass rate)** across 719 tests.

---

### 7.2 Root-Cause Failure Catalog (23 Test Remediation Specs)

The 23 pre-existing test failures fall into 7 discrete root causes, complete with specific remediation specifications:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           TEST FAILURE ROOT CAUSE LEDGER                       │
├────────┬────────────────────────────────────────┬─────────────┬────────────────┤
│ Cat #  │ Root Cause Domain                      │ Test Count  │ Target Files   │
├────────┼────────────────────────────────────────┼─────────────┼────────────────┤
│ Cat 1  │ ActionOutcome missing 'driver' argument│ 5 tests     │ rad/browser.py │
│ Cat 2  │ Missing POSIX `fcntl` on Windows       │ 2 tests     │ rad/agents.py  │
│ Cat 3  │ Subprocess shell selection (cmd vs sh) │ 4 tests     │ rad/tools.py   │
│ Cat 4  │ Windows command-not-found error regex  │ 3 tests     │ rad/control/   │
│ Cat 5  │ Windows backslash path formatting      │ 2 tests     │ rad/storage.py │
│ Cat 6  │ Windows NTFS permission bit checks     │ 4 tests     │ rad/doctor.py  │
│ Cat 7  │ Cascading acceptance / regression tests│ 3 tests     │ tests/         │
└────────┴────────────────────────────────────────┴─────────────┴────────────────┘
```

#### Category 1: Driver Mock Contract & Dataclass Keyword Argument
- **Affected Tests:** `tests/test_browser_tools.py` (5 failures: `test_navigate_separates_ok_from_verified`, `test_expectation_mismatch_is_ok_but_not_verified`, `test_extract_find_links_and_download`, `test_loopback_needs_explicit_opt_in`, `test_localhost_optin_is_settable_and_actually_unblocks`).
- **Root Cause:** In `rad/browser.py`, `ActionOutcome` dataclass lacks a `driver: str = ""` field. When Playwright is detected, `BrowserSession` passes `driver="playwright"`, throwing `TypeError: ActionOutcome.__init__() got an unexpected keyword argument 'driver'`.
- **Remediation:** Add `driver: str = ""` to `ActionOutcome` and include `"driver": self.driver` in `to_dict()`. Ensure offline tests stub `playwright_available` to `False`.

#### Category 2: Missing `fcntl` on Windows (Blackboard Concurrency)
- **Affected Tests:** `tests/test_agents.py` (2 failures: `test_blackboard_shared_between_parallel_agents`, `test_team_tools_mode_uses_runtime`).
- **Root Cause:** In `rad/agents.py:209`, `Blackboard.post` executes `import fcntl` outside a try-except block. On Windows, Python lacks `fcntl`, causing `ModuleNotFoundError` in worker threads.
- **Remediation:** Wrap `import fcntl` in `try ... except ImportError: fcntl = None` and guard `fcntl.flock` with `if fcntl is not None:`.

#### Category 3: Subprocess Shell Selection (`cmd /c` vs `sh -c`)
- **Affected Tests:** `tests/test_realworld.py` (4 failures: `test_filesystem_nested_write_and_jail`, `test_research_multi_source_cross_check`, `test_multi_agent_independent_verification`, `test_failure_recovery_and_crash_resume`).
- **Root Cause:** In `rad/tools.py:_shell` and `rad/control/verifier.py:_sh`, Windows execution routes unconditionally through `["cmd", "/c"]`. Standard POSIX commands (`cp`, `cat`, `test -s`, `mkdir -p`, heredocs) fail under `cmd.exe`.
- **Remediation:** Check `shutil.which("sh")`. On Windows, prefer `sh` when present on PATH, falling back to `cmd.exe` only when `sh` is unavailable.

#### Category 4: Windows Command-Not-Found Regex in Recovery Classifier
- **Affected Tests:** `tests/test_control_plane.py::test_environment_failure_inserts_repair_task`, `tests/test_class_a_budget_investigation.py::test_environment_repair_does_not_skip_verify_or_fake_done`, `tests/test_reliability.py::test_long_horizon_objective_with_mixed_failures`.
- **Root Cause:** In `rad/control/recovery.py`, `_ENV` regex matches Unix `"command not found"`, but lacks Windows error signatures (`"is not recognized as an internal or external command"`). Failed commands are misclassified as `TOOL` errors rather than `ENVIRONMENT` errors, preventing prerequisite repair task insertion.
- **Remediation:** Append `r"|is not recognized as an internal or external command|is not recognized as the name of a cmdlet|\bis not recognized\b"` to `_ENV` regex in `rad/control/recovery.py`.

#### Category 5: Windows Path Normalization
- **Affected Tests:** `tests/test_hardening.py::test_integrity_reports_and_quarantines_without_deleting`, `tests/test_memory2.py::test_objective_completion_feeds_memory_with_observed_origin`.
- **Root Cause:** On Windows, `str(path.relative_to(root))` yields backslashes (`world\graph.json`), whereas integrity assertions expect canonical POSIX slashes (`world/graph.json`). In `rad/world.py`, splitting location on `/` (`rsplit("/", 1)[-1]`) fails on Windows backslashes, polluting entity names with absolute drive paths.
- **Remediation:** Use `path.relative_to(root).as_posix()` in `rad/storage.py` and `Path(a["location"]).name` in `rad/world.py`.

#### Category 6: NTFS Permission Semantics in Doctor & Storage
- **Affected Tests:** `tests/test_hardening.py` (3 tests: `test_snapshot_excludes_keys_and_restore_roundtrip`, `test_doctor_full_run_healthy_and_exit_semantics`, `test_doctor_render_uses_release_labels`), `tests/test_interfaces.py::test_http_requires_token_and_serves`.
- **Root Cause:** NTFS filesystems on Windows do not support POSIX permission bits (`0o700` or `0o600`). `stat().st_mode & 0o777` returns `0o777` for directories and `0o666` for files. Checking `mode & 0o077` always flags `keys/` as "too open".
- **Remediation:** Guard POSIX permission bit checking with `if os.name != "nt":` in `rad/doctor.py:c_permissions` and `rad/storage.py:integrity`. On Windows, verify directory readability and writeability. Update tests to assert `p.exists()` on Windows instead of checking POSIX bits.

#### Category 7: Cascading Acceptance & Regression Tests
- **Affected Tests:** `tests/test_acceptance.py::test_area_subset_runs_and_writes_evidence`, `tests/test_realworld.py::test_suite_reports_everything_and_writes_evidence`, `tests/test_regression.py::test_history_and_render_round_trip`.
- **Root Cause:** These end-to-end suites cascade from the failures in Categories 2, 3, and 6.
- **Remediation:** Automatically resolved once Categories 2, 3, and 6 are remediated.

---

### 7.3 Host Environment & Platform Quirks (Windows 11 / NTFS / Toolchains)

1. **Google Drive Cloud-Sync Filesystem Race Conditions:** Running `npm ci` directly on `G:\My Drive` causes file-lock collisions in the virtual filesystem driver, resulting in empty 0-byte extracted files. In local environments, `npm ci` should be executed on local NTFS (`%TEMP%` or `C:\dev\`) and copied, or cloned locally.
2. **GNU MinGW Toolchain Path Splitting:** The default Rust GNU toolchain (`x86_64-pc-windows-gnu`) fails inside `tauri-winres` when compiling paths with spaces (`G:\My Drive\...`). Compiling under the MSVC toolchain (`x86_64-pc-windows-msvc`) handles quoted path spaces properly and exits with 0 warnings.
3. **Tauri Sidecar Placeholder Requirement:** `tauri-build` enforces that `externalBin` target binaries (`binaries/rad-$TARGET_TRIPLE.exe`) must exist at compile time.
4. **Python Executable Resolution:** On Windows, `python3` frequently maps to the Microsoft Store redirector stub. `desktop/src-tauri/src/lib.rs` must prefer `python` on Windows.
5. **Desktop Executable Extension:** `rad/cli.py:cmd_desktop` must search for `rad-desktop.exe` in addition to `rad-desktop`.

---

### 7.4 Multi-Gate Verification & Stabilization Roadmap

The stabilization roadmap across the milestone lifecycle:

```
┌────────────────────────────────────────────────────────────────────────┐
│                     RAD AGENT STABILIZATION ROADMAP                    │
├───────────┬──────────────────────────────────┬─────────────────────────┤
│ Milestone │ Focus Scope                      │ Key Gate Deliverable    │
├───────────┼──────────────────────────────────┼─────────────────────────┤
│ M1 (Now)  │ Branch Setup & Architecture Study│ `feat/complete-rad` &   │
│           │                                  │ `STUDY_AND_ARCHITECTURE`│
├───────────┼──────────────────────────────────┼─────────────────────────┤
│ M2        │ Core Engine & Test Remediation   │ 719/719 Pytest Passing  │
│           │ (NTFS, Shell, fcntl, Recovery)   │ Doctor 20 READY exits 0 │
├───────────┼──────────────────────────────────┼─────────────────────────┤
│ M3        │ Desktop Surface Finalization     │ TypeScript tsc exit 0   │
│           │ (Tauri MSVC, Lib.rs, Cli.py)     │ Cargo check/clippy 0    │
├───────────┼──────────────────────────────────┼─────────────────────────┤
│ M4        │ Multi-Gate Victory Audit         │ Full End-to-End Release │
│           │ (Clean tree, zero secret leaks)  │ Gate Attestation Report │
└───────────┴──────────────────────────────────┴─────────────────────────┘
```

---

## 8. Conclusion & Architectural Assessment

The RAD Agent codebase represents a mature, meticulously engineered, and principled autonomous agent architecture. By adhering strictly to the **Open Door Socket** abstraction, RAD decouples cognitive capabilities from proprietary vendors and infrastructure. 

Its **Control Plane** enforces a standard of autonomy: LLM proposals are deterministically constrained by an unbypassable hard security layer, evaluated against an explicit 11-state task FSM, and subjected to independent machine verification where verbal model claims are rejected as proof. Its **Layered Memory System** models epistemic provenance and handles contradictions non-destructively. Its **Desktop Surface** maintains containment over the core engine through loopback isolation.

With the empirical baseline established and the 23 environmental defect remediations cataloged in this study, the path to complete system stabilization and production release on branch `feat/complete-rad` is fully specified.
