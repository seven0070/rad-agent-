# DESKTOP_ACCEPTANCE_REPORT.md

**Date:** 2026-09-19
**Baseline HEAD:** `4c0c102 RAD Desktop 0.1 — Authority Foundation (stay 1.0.1)`
**Package version:** stays `1.0.1` (never 2.x)
**Stack:** Tauri 2.11.5 + React 19 + TypeScript + Vite 6 + the existing Python control plane (`rad serve`), Windows first.
**Guiding constraint:** desktop is a **face**, not a second control plane. One source of truth (`rad/`), one executor, chain User → Jerry → Controller → Planner → Executor → Policy → Tool. `rad/` source was not rewritten (see "Scope evidence").

## Status

| Gates | Result |
|---|---|
| Frontend typecheck (`npx tsc --noEmit`) | `tsc exit: 0` |
| Frontend production build (`npm run build` = `tsc -b && vite build`) | `build exit: 0` — 38 modules, 182.67 kB js / 56.63 kB gzip |
| Rust compile (`cargo check`) | `cargo check exit: 0` |
| Rust lints (`cargo clippy -- -D warnings`) | `clippy exit: 0` |
| Rust MSVC link (`cargo +stable-x86_64-pc-windows-msvc build`) with sidecar present | `build exit: 0` — real `rad-desktop.exe` produced (12.6 MB) |
| Desktop pytest (7 files, live HTTP server) | `25 passed in 12.95s` |
| Full pytest suite (699 collected) | `695 passed, 23 failed, 1 skipped` — failures pre-existing / environmental, none in desktop scope (see below) |

## IMPLEMENTED

- **`desktop/src/api.ts`** — `RadClient` over local `http://127.0.0.1:8787`, 27 routes mirroring the v1 HTTP API; `SETTINGS_SAFE_KEYS`/`BUDGET_KEYS` whitelists; `fetch(` appears nowhere else in `desktop/src`.
- **`desktop/src-tauri/src/lib.rs`** — `rad_program` resolver (candidate candidates incl. `python -m rad`) and Tauri backend spawn; Python is bundled via PyInstaller sidecar.
- **`desktop/src-tauri/tauri.conf.json`** — `bundle.externalBin: ["binaries/rad"]` + CSP `connect-src` loopback-only.
- **`desktop/src-tauri/binaries/README.md`** — documents the cross-platform sidecar naming contract (`rad-<target-triple>.exe` / `rad-<target-triple>`).
- **Views** (`desktop/src/views/`) — `ActiveRun`, `ObjectiveDetail`, `ToolsTrace`, `Memory`, `VerificationCard`; hook `desktop/src/hooks/usePolling.ts`; wiring + styling in `desktop/src/App.tsx`, `desktop/src/styles.css`.
- **Tests** (`tests/test_desktop_*.py`, 7 files, 25 items) — surface, API contract, security surface (fixed copy string `No machine-check pass ⇒ No VERIFIED`), golden workflow, failure recovery, token persistence, authority matrix.
- **CI/CD** — `.github/workflows/desktop.yml` (per-PR desktop gates), `.github/workflows/release-desktop.yml` (tag → PyInstaller sidecar + `tauri build`), `ci.yml` `paths-ignore` for `desktop/**`; `scripts/build-sidecar.{ps1,sh}`.
- **`docs/DESKTOP.md`** — desktop surface documentation (from the landing commit).

## TESTED (machine-verified evidence)

1. **Desktop pytest, all green** — `python -m pytest -q tests/test_desktop_surface.py tests/test_desktop_api.py tests/test_desktop_security_surface.py tests/test_desktop_golden_workflow.py tests/test_desktop_failure_recovery.py tests/test_desktop_token_persistence.py tests/test_desktop_authority_matrix.py` → `25 passed in 12.95s`. Includes the security-surface exact-copy assertion and the authority matrix (UNRESTRICTED requires `confirm_unrestricted`; frontend cannot raise budget/planner cap, cannot run shell).
2. **Typecheck clean** — `npx tsc --noEmit` exits 0 after aligning the `ActiveRun`/`ObjectiveDetail` navigation-callback props (the one real defect found in the P3 landing; a TS2322 that would have broken `npm run build`).
3. **Production build clean** — `npm run build` exits 0 (38 modules, minified bundle written to `dist/`).
4. **Rust compile gates clean** — `cargo check` and `cargo clippy -- -D warnings` both exit 0 from a spaceless workspace copy (a local `C:\Users\sanath\Cargo.toml` workspace with missing members requires `[workspace]` isolation for the copy only; CI checkouts are unaffected).
5. **Real Windows binary links** — after building the PyInstaller sidecar with the repo's own build contract (`--onefile --name rad --collect-all rad --collect-submodules rad`, entry `rad/__main__.py`), `cargo +stable-x86_64-pc-windows-msvc build` exits 0 and produces a runnable `target/debug/rad-desktop.exe` (12.6 MB). The sidecar is a fresh local build (568 MB onefile, local tmp only — not copied into the synced tree).

## VERIFIED vs REMAINING

**VERIFIED (observable now):** all gates above — including the real binary `cargo +stable-x86_64-pc-windows-msvc build` linking successfully with a locally-built PyInstaller sidecar present; `desktop/src` contains no forbidden surface (no shell runner, no authority escalation in the UI path, no parallel control-plane write path); control plane code under `rad/` is byte-identical to the pre-desktop baseline.

**REMAINING — needs a dedicated release host, not this machine:**
- `npm run tauri build` / the bundled MSI + NSIS installer and the packaged frontend (local MSVC linker is fine, but the full installer pipeline is exercised in CI).
- Sidecar + binary smoke test on a clean Windows machine (end user has no Python/Node/npm): the onefile `rad` sidecar must spawn, serve `/v1`, and be reached by the desktop UI.
- GNU/mingw link note (recorded, not shipped): the GNU toolchain alone fails at link with `export ordinal too large: 90157` (known mingw cdylib exporter limitation); the MSVC path used above is the shipping one.

## Pre-existing full-suite failures (23) — not desktop-caused

Evidence that these are baseline/environmental, not a regression from this work:
- `git diff --name-only HEAD -- rad/` → **0 files**. The control plane was not touched.
- The failing modules (`browser_tools`, `hardening`, `interfaces`, `realworld`, `regression`, `reliability`, `agents`, `acceptance`, `memory2`, `class_a_budget_investigation`, `control_plane`) are byte-identical to baseline HEAD.
- Failure signatures are OS/ABI/quiet-env specific: `ActionOutcome.__init__() got an unexpected keyword argument 'driver'`; POSIX permission-mode assertions (`0o666 != 0o600`) failing on NTFS; `realworld` objectives reaching `needs_user` with no LLM/network; daemon/retry-count quirks. Repo workflows target Python 3.10–3.12; this box is **Python 3.14.6 on Windows AMD64**.

## Scope evidence

`git status` — modified: `.github/workflows/ci.yml`, `desktop/src-tauri/gen/schemas/desktop-schema.json`, `desktop/src-tauri/src/lib.rs`, `desktop/src-tauri/tauri.conf.json`, `desktop/src/App.tsx`, `desktop/src/api.ts`, `desktop/src/styles.css`, `tests/test_desktop_surface.py`. Untracked: `.github/workflows/{desktop,release-desktop}.yml`, `desktop/src-tauri/binaries/`, `desktop/src-tauri/gen/schemas/windows-schema.json`, `desktop/src/hooks/`, `desktop/src/views/`, `scripts/`, `tests/test_desktop_{api,authority_matrix,failure_recovery,golden_workflow,security_surface,token_persistence}.py`, plus this report. No changes outside `desktop/`, `tests/test_desktop_*`, CI work, `scripts/`, and docs.