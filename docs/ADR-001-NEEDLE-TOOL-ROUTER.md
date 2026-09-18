# ADR-001 — Optional Needle tool-router

**Status:** Accepted (do **not** integrate as default)  
**Date:** 2026-09-18  
**Package:** RAD 0.2.1  
**Related:** NEEDLE_EVALUATION_REPORT.md, `rad/toolrouter.py`

## Context

Needle 3 (cactus-compute/needle) is a tiny on-device model that emits grammar-constrained tool calls. The v0.3 mission asked whether RAD should insert it as:

`planner (general LLM) → Needle (tool name/args) → RAD controller → permission/sandbox/budget → tool → observe → verify`

v0.2.0 already has a working native-tools path (`RouterState.chat` + provider `tool_calls`). The 11B NIM default is a weak planner, which is a separate Class B issue.

## Decision

1. **Ship an optional experimental adapter**, selected by `RAD_TOOL_ROUTER=existing|needle` (config key `tool_router`, default `existing`). Env wins.
2. **Do not make Needle mandatory.** Missing package, failed engine load, or malformed `complete()` falls back to existing and records why.
3. **Needle is never sovereign.** It does not execute tools (`complete()` only, never `run()`), does not grant permission, does not skip sandbox/budget, does not verify, does not decide DONE.
4. **Do not bump to v0.3.0.** Measured Needle 3 tool-selection **0.60** and arg accuracy **0.20** vs existing heuristic **0.80 / 0.80** on a 5-case RAD gold set. Invalid calls: 1 vs 1. No measured gain. Live NIM A/B BLOCKED (no NVIDIA key).
5. **Unavailable:** `NeedleUnavailable` → fallback; CLI `rad needle-eval` reports BLOCKED lanes honestly.

## Where it sits

```
Session.think
  → chat_with_tools(home, router.chat, messages, tools)
       existing: RouterState.chat (NIM / Groq / local / …)
       needle:   NeedleAdapter.propose → ChatResult.tool_calls
  → tool_runner  (Executor when under Controller)
  → Policy / Sandbox / Budget / Observer / Verifier
```

The planner and verifier are unchanged. Needle is not on the control-plane decision path.

## What Needle never controls

Permission decisions, sandbox grants, budgets, task status, objective completion, audit, recovery strategy, and any side effect. A well-formed `function_calls` list is a **proposal**.

## Consequences

- Users with `cactus-needle` installed can experiment without a RAD fork.
- Default installs and CI stay Needle-free (pytest skips engine download).
- A future 0.3.0 would need a measured win (tool selection / arg accuracy / invalid calls / latency or cost) on RAD’s real tools, with the controller still in charge — plus a live NIM comparison if that is the production brain.

## Alternatives considered

| option | why not |
|---|---|
| Needle as default router | Measured regression on RAD-shaped tools |
| Needle `run()` executing host functions | Bypasses RAD’s single enforcement point |
| Fine-tune Needle in this PR | Out of scope; no evidence yet it would beat existing+NIM |
| Drop the adapter | The experiment is cheap behind a flag and the measurements exist |
