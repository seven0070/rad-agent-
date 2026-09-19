# RAD Desktop 0.2.0-alpha

Desktop is a **face**, not a second control plane. Stack: Tauri 2 (Rust) + React +
TypeScript + Vite talking to `rad serve`'s HTTP API — which in the packaged app is a
**bundled `rad-backend` sidecar** the desktop owns end to end. Source: `desktop/`.

```
RAD Desktop (React)                    Tauri shell (Rust)              Process
┌──────────────────────────┐  invoke   ┌─────────────────────────┐  spawn (fixed argv)
│ pages · api.ts (fetch)   │──────────▶│ backend_* commands      │──────────────────▶ rad-backend
│ state in React ctx only  │           │ sidecar resolution      │                   (loopback :port)
└──────────────┬───────────┘           │ health · logs · restart │◀──── /v1/health ──  (Bearer token, 0600)
               │ /v1/* over loopback   └─────────────────────────┘
               ▼
        Session / Controller → Executor → Policy.decide → Tools → Observer → Verifier
```

## Non-developer flow

Install the platform installer (CI-built) → launch → choose workspace + authority profile →
talk to **Jerry** → give an objective → watch: planning, live task graph (from backend deps;
the frontend never schedules), execution with **real** pause/resume/cancel, tool trace with
redaction, authority, verification (only backend machine verification yields VERIFIED),
artifacts, provenance ("rad why"), usage/cost. Pause, resume, recover from NEEDS_USER with
reason + Resolve/Cancel, close, reopen — the objective, its artifacts, verification and
provenance persist and reopen cleanly (golden E2E, `tests/test_golden_e2e.py`).

The desktop owns the backend lifecycle and is never silent about it:

| Stage | Behavior |
|---|---|
| locate | `default_home` → `~/.rad` (or configured `RAD_HOME`) |
| start | sidecar `serve --host 127.0.0.1 --port <n> [--home <dir>]` — fixed argv, no user string; dev fallback `python -m rad serve` when no sidecar is bundled |
| health | raw loopback GET `/v1/health` with the issued Bearer token; 20 s / 250 ms wait; on failure the backend log tail is shown |
| stale process | a foreign or stale listener on the port is probed before start; stale RAD is told as such, never killed silently |
| crash/restart | `backend_restart`, `backend_info`, `backend_health`; reconnect is surfaced in the UI banner, never implicit |
| stop | clean terminate + process-group cleanup on quit |

## Authority (exact semantics)

Five profiles over the existing `/v1/authority` — `SAFE`, `STANDARD` (default, passthrough),
`AUTONOMOUS`, `UNRESTRICTED`, `CUSTOM`:

- **UNRESTRICTED requires explicit authorization** (`confirm_unrestricted` /
  `--i-authorize-unrestricted`). It is never inferred from a missing or corrupt authority
  file (those fall back to STANDARD), from `--auto`, or from the frontend. It is broad +
  minimal-confirmation — it does **not** bypass `Policy.decide`, hard blocks, budgets,
  audit or verification; it does not touch provider/model safety policies.
- **CUSTOM** composes the existing capability effects (`ALLOW/ASK/LIMITED/DENY`) and scopes
  (workspace, extra paths, hosts). There is no second policy engine in React — the browser
  never stores authority state at all (no localStorage/sessionStorage/indexedDB in the app).
- Budgets (16 tasks / 60 tool calls / …) and the planner cap cannot be changed via HTTP.
- Every profile change is audited (`AUTHORITY_PROFILE_CHANGED`); a no-op is not.

Proven by `tests/test_authority_matrix.py` (all five profiles × scope/confirm/budget/
hard-block/audit/verification invariants).

## Security boundary (what is true, with evidence)

| Property | Where | Evidence |
|---|---|---|
| sidecar binds loopback only; `--host 0.0.0.0` refused (exit 1) | `rad/sidecar.py` | sidecar smoke in CI + `tests/test_security_desktop.py::test_sidecar_only_binds_loopback` |
| API token ≥32 bytes, file mode `0600`, rotated on demand | `rad/api.py` | `test_api_token_permissions_and_isolation` |
| no shell/tools/exec routes in the HTTP API or the frontend | `rad/api.py`, `desktop/src/api.ts` | `test_api_still_has_no_shell_or_tool_routes`, `test_no_shell_surface_in_api_or_frontend` |
| Tauri spawns a fixed argv sidecar; no `tauri-plugin-shell`/`fs`; no user-interpolated commands | `desktop/src-tauri/src/lib.rs` | `test_frontend_has_no_arbitrary_shell`, `test_sidecar_is_bundled_and_scoped` |
| artifact content is registry-gated (404/403/415), workspace/home-scoped, redacted | `rad/api.py::_artifact_content` | `tests/test_desktop_api.py` (registered-only / outside-403 / binary-415 / redaction) |
| `credentials` can never be granted (coerced to DENY; protected paths denied in every profile) | `rad/authority.py`, `rad/policy.py` | `test_api_cannot_raise_budgets_or_caps`, `test_credentials_denied_in_every_profile` |
| untrusted web data is labeled untrusted in provenance, never treated as fact | `rad/control/provenance.py` | `test_web_evidence_marked_untrusted_in_provenance` |
| a lying model cannot produce VERIFIED (false DONE → NEEDS_USER/FAILED) | Verifier + recovery | `tests/test_failure_recovery.py`, `test_verification_stays_independent` |
| budget exhaustion stops the run — no fake VERIFIED | budgets + driver | `test_budget_exhaustion_is_needs_user_not_verified`, `test_budget_exhaustion_stops_run` |

## What is tested here vs. what CI owns (honesty bar)

**Passing in this tree** (783 tests, `python -m pytest -q`): core control plane, desktop
API endpoints, authority matrix, desktop security, golden E2E (objective → VERIFIED →
close → reopen, with artifacts/verification/provenance intact), restart/resume without
re-running completed tasks (crash state restored, `CRASH_DETECTED` recorded), failure
recovery (retry → VERIFIED; persistent failure → never VERIFIED). The sidecar contract
(`rad-backend serve|health`, token file 0600, port-conflict exit 3, loopback-only) is
functionally verified against both the installed console script **and an actually
frozen Linux binary**: CPython 3.11.16 was built from source in the sandbox, PyInstaller
6.22.3 produced `binaries/rad-backend-x86_64-unknown-linux-gnu` (8.8 MB, self-contained
vs glibc — see `docs/DESKTOP-RELEASE-REPORT.md` §4 + appendix), and the full smoke
passed against it.

**CI-only / machine-owned** — not claimed as verified on a clean machine here:
the Rust compile of `desktop/src-tauri` (no Rust toolchain in this workspace), the
Windows/macOS PyInstaller freezes (cross-compile impossible; native runners only), the
Tauri installer builds, and the clean-machine install → verified objective → close →
reopen pass. Those run in
[.github/workflows/desktop.yml](../.github/workflows/desktop.yml)
(tests → frontend → sidecar freeze+smoke → Tauri build → installer upload) and in the
release checklist below.

## Release checklist (run on a clean machine per platform)

1. Install the CI-uploaded installer (Windows first: `*.msi`/`*.exe`).
2. Launch RAD Desktop. No Python, no Node, no `rad serve` anywhere on the machine.
3. New workspace → STANDARD profile → objective: a small Python project (module + test +
   README with machine checks).
4. Watch to **VERIFIED**; open the artifacts; open provenance on one of them.
5. Close the app. Relaunch. The objective, its artifacts, verification and provenance are
   all present (this is exactly `tests/test_golden_e2e.py` at the API level).
6. Change the profile to UNRESTRICTED without typing the explicit authorization — the UI
   must refuse. With it — the profile applies; a hard-blocked command is still refused.
7. Crash the backend process while a task runs → the UI shows it → restart → resume →
   no completed task runs twice.

## Development

```bash
cd desktop && npm install
RAD_PYTHON=../.venv-dev/bin/python npm run tauri dev   # dev fallback: python -m rad serve
npm run build                                          # tsc -b && vite build
python -m sidecar.build                                # freeze rad-backend for this platform
```

`desktop/src-tauri/binaries/rad-backend-<triple>` is what `bundle.externalBin` ships;
CI builds one per native OS (PyInstaller does not cross-compile). Tauri capabilities are
restricted to the seven `backend_*` lifecycle commands (`capabilities/default.json`).
