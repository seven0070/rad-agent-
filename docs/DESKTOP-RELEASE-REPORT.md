# RAD Desktop 0.2 — Validation report (2026-09-19)

Factual validation per area. **PASS only where evidence exists in this tree or was
executed in this workspace.** CI-only / machine-owned items are marked FAIL-HERED (not
claimed) with what would prove them.

Workspace: `arena/01a0bafc-rad-agent` @ branch from `bbfa991` (baseline 4c0c1020 line).
Interpreter: `.venv-dev` (Python 3.11.16, `pip install -e ".[dev,sidecar]"`).

## 0. Windows release build + install smoke (2026-09-23) — PASS (build machine)

Fresh local build and a real NSIS install on this machine; every line below is
backed by output captured during that run:

- **Windows MSVC sidecars frozen + smoke-green**: `rad-x86_64-pc-windows-msvc.exe`
  **14,143,697** B (SHA256 `C318D038…EFA5E1440`), `rad-backend-x86_64-pc-windows-msvc.exe`
  **11,348,875** B (SHA256 `D24FB1E6…D9630BF67`); shell `rad-desktop.exe` **3,251,200** B.
  The backend answered `/v1/health` 200 during the install smoke; the runtime binary is
  SHA256-identical to the embedded copy (resolver note below).
- **MSI/NSIS built fresh 2026-09-23** (not stale): NSIS `RAD Desktop_0.2.0_x64-setup.exe`
  26,454,443 B @ 18:20:30; MSI `RAD Desktop_0.2.0_x64_en-US.msi` 27,009,024 B @ 18:20:12.
  Embedded sidecars proven:
  - MSI — WindowsInstaller COM file table: `rad-desktop.exe` 3,251,200, `rad.exe`
    14,143,697, `rad-backend.exe` 11,348,875, `rad_desktop_lib.dll` 114,688;
  - NSIS — direct 7-Zip extraction (Type=Nsis, Method=LZMA:23, “Everything is Ok”,
    9 files): `rad-desktop.exe` 3,251,200 / `rad.exe` 14,143,697 /
    `rad-backend.exe` 11,348,875 — all three MZ, SHA256-identical to the source
    `src-tauri/binaries/` freezes and to the installed copies.
- **Local release orchestrator + CI written**: `scripts/build-desktop-release.ps1`
  (sidecar freeze → size asserts → `tauri build` → MSI/NSIS freshness asserts) and
  `.github/workflows/release-desktop.yml`.
- **Install smoke (this machine)**: NSIS `/S` exit 0 → install dir
  `C:\Users\sanath\AppData\Local\RAD Desktop` (all three exes with the sizes above +
  `uninstall.exe`); launch → window title “RAD Desktop” + WebView2 processes;
  installed shell spawned `… serve --host 127.0.0.1 --port 7331 --home C:\Users\sanath\.rad`
  (PID chain parented to the installed `rad-desktop.exe`); `GET /v1/health` with Bearer
  from `~/.rad/api.token` (43 B, owner-only ACL) → **200**
  `{"ok": true, "version": "1.0.1", "schema": 3, "running": []}`; `~/.rad/logs/backend.log`
  fresh `listening` event on 127.0.0.1:7331.
- **Test suite re-run 2026-09-23**: `python -m pytest -q -n auto` → **839 passed,
  2 skipped** (includes new resolver regression test), 0 failed.
- **Resolver gap fixed (2026-09-23 evening)**: installers ship short sidecar names
  (`rad.exe`, `rad-backend.exe`); `resolve_sidecar()` previously only matched the
  triple name (`rad-backend-x86_64-pc-windows-msvc.exe`) and fell through to the
  compile-time `CARGO_MANIFEST_DIR` repo path. `desktop/src-tauri/src/lib.rs` now
  probes **short name first, then triple**, install-dir layout before the
  manifest-dir fallback (size gate >1024 B unchanged). Rebuilt via
  `scripts/build-desktop-release.ps1 -SkipSidecar` (shell 3,250,688 B; NSIS
  26,455,098 B @ 20:48:32; MSI 27,009,024 B @ 20:48:18). Re-smoke **PASS**:
  backend process path `C:\Users\sanath\AppData\Local\RAD Desktop\rad-backend.exe`
  (install dir, not repo) → `/v1/health` 200
  `{"ok": true, "version": "1.0.1", "schema": 3, "running": []}` → stop shell +
  backend → NSIS `/S` uninstall → install dir gone, port 7331 free.
  Clean-machine gap for this failure mode is **closed** on this machine; a true
  no-repo machine still needs the release-checklist run (REMAINING item 4).
- **MSI smoke PASS (this machine)**: dual-mode package needs per-user mode when not
  elevated — `msiexec /i … /qn MSIINSTALLPERUSER=1 ALLUSERS=2` → install → launch →
  backend from install dir → health 200 → `msiexec /x {87CEE1AD-…} MSIINSTALLPERUSER=1 /qn`
  → dir/port/registry clean. Default double-click MSI asks for UAC (Error 1925 if declined).
- **Python-fallback path PASS** (REMAINING 6, partial): no sidecar —
  `C:\Python314\python.exe -m rad serve --host 127.0.0.1 --port 7331` → health 200
  `{"ok": true, "version": "1.0.1", …}` → process stopped → port clean.
- **Live `npm run tauri dev` PASS (REMAINING 6, closed 2026-09-24)**: full stack run
  from a C:-side source copy (`%TEMP%\rad-desktop-dev`, `node_modules` reinstalled on
  C: — Drive I/O is too slow for Vite's HMR transform of `/src/main.tsx`, which hung
  indefinitely when the repo lived on Google Drive). Launcher env:
  `TAURI_DEV_HOST=127.0.0.1`, `RAD_PYTHON=C:\Python314\python.exe`,
  `CARGO_TARGET_DIR=%TEMP%\rad-tauri-target`,
  `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=9333`.
  Evidence captured during the run:
  - Vite `ready in 687 ms` on `http://127.0.0.1:1420`;
  - CDP: React mounted in 1 s (`rootLen 7678` → later `22372`),
    `hasTauri: true`, `src/main.tsx` + `src/App.tsx` resources present, no console errors;
  - backend spawned as Python fallback (64-byte sidecar stub rejected by the
    >1024 B size gate): child PID `35584` parented to `rad-desktop` PID `20736`,
    cmdline `C:\Python314\python.exe -m rad serve --host 127.0.0.1 --port 7331`;
  - `GET /v1/health` with Bearer from `~/.rad/api.token` → **200**
    `{"ok": true, "version": "1.0.1", "schema": 3, "running": []}`;
  - UI showed `v1.0.1 · Studio Online` and rendered real RECENT SESSIONS data.
  Workaround notes: `TAURI_DEV_HOST=127.0.0.1` forces Vite off IPv6-only `[::1]`;
  source must be on local disk (C:) not Google Drive for the dev server.
- **Backend API surface smoke PASS**: 14/14 — GET 200 on `/v1/health`, `/v1/authority`,
  `/v1/status`, `/v1/tools`, `/v1/events`, `/v1/audit`; 404 on non-existent
  `/v1/models`, `/v1/providers`, `/v1/cost`, `/v1/config`, `/v1/objective`,
  `/v1/security` (route absent ≠ failure); no-token → 401, bad-token → 401; CLI
  `rad-backend health --port 7331` → ok JSON.
- **Frontend unit tests (vitest)**: jsdom environment hangs on this Google Drive path
  (RUN banner, no workers). Workaround: `vitest.min.config.ts` (node pool + threads)
  + `src/test/setup-node.ts` window/localStorage polyfill → **3 files, 13 tests PASS**
  (`api.test.ts` 4, `backend.test.ts` 5, `backend.tauri.test.ts` 4), exit 0.
   `Button.test.tsx` (React DOM) **3/3 PASS** on 2026-09-24 via a C:-side jsdom
   vitest project (`%TEMP%\rad-btn-test`, same `vitest.min.config.ts` +
   `setup-node.ts` polyfill pattern) — Drive path still hangs full jsdom workers;
   the C: copy does not.

## 1. Stale doc version references — PASS

- README banner now `v1.0.1` (was `v1.0.0`); the regression test
  `tests/test_public_1_0_baseline.py::test_rw100_first_run_docs_match_package_1_0_0`
  was updated to pin the corrected banner and still passes.
- Package `rad.__version__` == `1.0.1`, `pyproject.toml` `version = "1.0.1"` (unchanged;
  no cosmetic bump). Desktop app version `0.2.0-alpha` in `desktop/package.json`,
  `desktop/src-tauri/tauri.conf.json`, `desktop/src-tauri/Cargo.toml` — asserted by
  `tests/test_desktop_surface.py::test_desktop_stack_present`.

## 2. Frontend (D2 cockpit, real state only) — PASS

- `cd desktop && npm run build` (`tsc -b && vite build`) is **clean**: 45 modules,
  `dist/assets/index-*.js` 210.49 kB (gzip 64.92 kB).
- 10 nav pages (Jerry, Objectives, Active Run, Tasks, Trace, Verification, Artifacts,
  Authority, Memory, Settings) — `test_desktop_stack_present`.
- No mock/demo/lorem data, no `localStorage`/`sessionStorage`/`indexedDB` anywhere in
  `desktop/src` — `test_no_mock_or_demo_data_in_frontend`,
  `test_frontend_cannot_write_authority_directly`, `test_frontend_renders_only_backend_state`.
- Client routes are typed `/v1/*` strings only — `test_api_client_only_known_routes`.
- Status/verification render from backend fields (e.g. `ver.status`,
  `obj?.verification`); reconnect is surfaced explicitly in `App.tsx`
  (`"reconnecting"`), never silent — `test_frontend_renders_only_backend_state`.

## 3. Backend desktop API — PASS

`tests/test_desktop_api.py` (15 tests, green): artifacts list (registry w/ sha256,
versions, task ids); artifact-content registered-only (404 unregistered / raw path),
outside-workspace 403, binary 415, secret redaction; plan view (version, source,
replans, machine checks); recovery view (decisions, failed tasks, retry budget); live
view (tasks by status, current task, budget account, verification, events) + `since_seq`
pagination; observations (+task filter, redaction); usage rollup (real counts,
no invented quota — 429 note); memory list/layer (fix applied: `Memory.scan`, the old
`mem.items` silently swallowed an AttributeError); run endpoint gating (409 `auto=false`,
202→completed `auto=true`); objective summary task counts; no shell/tool/exec routes
(404).

A real bug was found and fixed while testing: `/v1/memory` GET called a non-existent
`Memory.items()` whose `except` hid the failure (always-empty list). Now `scan()`.

## 4. Sidecar (Python core packaging) — PASS

- `rad/sidecar.py` + console script `rad-backend` verified end-to-end multiple times in
  this workspace (installed entry point, not a stub):
  - `serve --port N` → stdout JSON `{"event":"listening","host":"127.0.0.1",...}`,
    token written to `$RAD_HOME/api.token` with mode **0600**;
  - `/v1/health` with Bearer → `{"ok":true,"version":"1.0.1","schema":3,...}`;
    wrong/missing token → 401;
  - `health --port N` subcommand → ok JSON;
  - second `serve` on same port → **exit 3** `{"error":"port_in_use",...}`;
  - `--host 0.0.0.0` → **exit 1** `{"error":"sidecar only binds loopback (127.0.0.1)"}`.
- **The Linux sidecar is actually frozen and smoke-tested in this workspace** (the
  earlier "impossible" verdict was an environment limitation that was removed):
  - Built CPython **3.11.16 from source** in the sandbox (`build/cpython-3.11.16`,
    `--enable-shared`; zlib 1.3.1 from source for the build tooling; system
    `_ctypes`/`_ssl`/`_hashlib` 3.11 extensions reused — ABI-stable within the minor
    version) → shared `libpython3.11.so.1.0` available;
  - `PyInstaller 6.22.3` frozen `rad-backend` in **12 s** →
    `desktop/src-tauri/binaries/rad-backend-x86_64-unknown-linux-gnu` (**8.8 MB**),
    exactly where `bundle.externalBin` expects it;
  - `ldd` on the frozen binary: only base glibc (`libc/libdl/libpthread/libz` +
    loader) — libffi/libssl are embedded by PyInstaller → runs on any modern x86_64
    Linux with glibc, i.e. the clean-machine requirement for the sidecar is met;
  - full contract smoke re-run against the **frozen** binary: serve→token(0600)→
    health 200 w/ token → 401 without → `health` subcommand → second serve **exit 3**
    → non-loopback **exit 1**. All green.
- Windows MSVC freeze is built + smoke-green **locally 2026-09-23** (rad 14,143,697 /
  backend 11,348,875; install smoke in §0). macOS freeze remains CI-only (PyInstaller
  cannot cross-compile — `sidecar` job in `.github/workflows/desktop.yml`).

## 5. Tauri shell / lifecycle — PASS (compiled + install-smoked 2026-09-23, §0; design + static)

- `desktop/src-tauri/src/lib.rs` rewritten: 7 commands (`default_home`, `api_token`,
  `backend_info`, `backend_start`, `backend_stop`, `backend_restart`,
  `backend_health`); sidecar resolution by target triple (exe dir + `binaries/` +
  `Resources/` + manifest `binaries/` + cwd); **fixed argv** spawn (sidecar
  `serve --host 127.0.0.1 --port <n> [--home <dir>]`, dev fallback `python -m rad
  serve`); raw-TCP health probe with Bearer token (20 s / 250 ms, backend-log tail on
  failure); stdout/stderr pumped to `~/.rad/logs/backend.log`; stale-RAD (401+`bearer`)
  vs foreign-process detection before start; `State{backend: Mutex<Option<Backend>>}`.
  Uses only std + serde + serde_json + tauri — no new crates, `Cargo.lock` untouched.
- **Compiled + shipped locally 2026-09-23** (MSVC release build): shell
  `rad-desktop.exe` 3,251,200 B in `target/release`, installed via NSIS and smoke-tested
  end-to-end (§0). CI remains the cross-platform compile owner (`desktop.yml`).
- Static guarantees pinned by tests: fixed argv, loopback only, no
  `tauri-plugin-shell`/`fs`, no user-interpolated commands, no shell strings
  (`test_frontend_has_no_arbitrary_shell`, `test_sidecar_is_bundled_and_scoped`,
  `test_tauri_sidecar_is_fixed_argv`); `bundle.externalBin: ["binaries/rad-backend"]`;
  capabilities limited to the 7 `allow-backend-*` permissions.

## 6. Authority matrix (mission §29) — PASS

`tests/test_authority_matrix.py` (26 tests, green) — all 5 profiles × invariants:

- grant surface per profile (SAFE: write/shell UNAUTHORIZED, reads ok; STANDARD:
  existing ASK defaults; AUTONOMOUS/UNRESTRICTED: ASK→ALLOW without `--auto`; CUSTOM:
  exact configured effects).
- **UNRESTRICTED requires explicit authorization**: `ValueError` without
  `confirm_unrestricted`; missing hand-edited `authority.json` claiming it, corrupt
  JSON, unknown profile → all fall back to STANDARD; explicit authorization persists
  across restart (fresh `Authority` instance reads it back).
- **Hard blocks survive every profile** (`sudo`, `rm -rf /`, secret paths,
  `credentials` UNAUTHORIZED even under UNRESTRICTED); soft DENY rules survive every
  profile (DENY or UNAUTHORIZED — either way no execution).
- **Budgets invariant**: 60/80/6 unchanged by any profile; HTTP cannot raise
  `tool_calls`/`max_plan_tasks`/`auto`/`tool_router`/`budget` (400); budget exhaustion
  under AUTONOMOUS/UNRESTRICTED stops the run and yields no fake VERIFIED.
- Confirmation semantics per profile (ask/never; SAFE writes stop at UNAUTHORIZED
  before any prompt; declined prompt stops the action).
- `--auto` never infers UNRESTRICTED; SAFE + auto still UNAUTHORIZED for writes.
- Scopes: workspace escape → SCOPE_VIOLATION at policy layer for granted caps
  (SAFE read / AUTONOMOUS / CUSTOM+web); extra_paths grant exactly; host scope
  allows only listed hosts; UNRESTRICTED with `workspace_only=False` reaches outside
  (that is its documented semantics).
- MCP/packages/spawn matrix per profile; every profile change audited
  (`AUTHORITY_PROFILE_CHANGED`), no-op not audited; verification independence:
  a false `DONE` with an unmet machine check ends NEEDS_USER/FAILED — never VERIFIED.
- STANDARD is a passthrough: zero delta vs no authority file.

## 7. Desktop security (mission §25) — PASS

`tests/test_security_desktop.py` (14 tests, green): token ≥32 bytes + file mode 0600 +
rotation; `credentials` denied in every profile and via the tool layer (model cannot
read `api.token` or workspace `keys.env`); secrets redacted from tool output and
artifact previews; API cannot escalate (UNRESTRICTED without flag → 409), cannot raise
budgets/caps, `credentials` capability coerced to DENY; frontend holds no local
authority store; artifact-content registry-gated (unregistered 404, outside 403,
raw paths 404); no shell surface in API or frontend (all 5 candidate routes 404;
client routes all `/v1/*`); Tauri sidecar fixed-argv (no `sh -c`/`/bin/sh`, no
`tauri-plugin-shell`/`fs`); MCP denied under SAFE / ASK under STANDARD; budget
exhaustion never fake VERIFIED; untrusted web data labeled `trusted:false` in
provenance (`pv.why` verdict `supported` with `trusted:False` on `fetch_page`
support); frontend hygiene (no mock data; real-state rendering; explicit reconnect);
sidecar loopback-only string in `rad/sidecar.py`.

## 8. Golden E2E (mission §26) — PASS (at the API level the desktop uses)

`tests/test_golden_e2e.py` (3 tests, green), canonical small-Python-project objective
(module + pytest test + README, machine checks incl. `python3 -c` import-assert):

- create+start via `POST /v1/objectives` (202) → background run → **completed +
  VERIFIED**; real files in workspace; plan/trace/recovery/artifacts/observations
  endpoints all real (3 tasks COMPLETED, 3 artifacts w/ sha256).
- **close → reopen** (fresh `Api` + controller): objective `completed/VERIFIED`,
  `tasks_total=3/tasks_completed=3`, artifacts ≥3, artifact-content preview,
  provenance `why` chain (artifact → versions → action `write_file` → task), usage
  (1 objective, 3 tool_calls, 3 model_calls) all intact.
- **Restart/resume (§28)**: sidecar death simulated mid-t2 (`SystemExit` — a
  BaseException the executor's `except Exception` cannot swallow, leaving exactly the
  crash state on disk; t2 left RUNNING via a mid-task checkpoint capture). Reopen →
  `POST /objectives/{id}/resume` → 202 → completed VERIFIED. t1 **not re-run**
  (`attempts==1`, exactly one `write_file` observation for `mathutil.py` across the
  whole objective); t2 carries the `interrupted` history note; `CRASH_DETECTED`
  event recorded with `tasks=1`.
- Planner fallback without any LLM: never fakes VERIFIED — a VERIFIED outcome is only
  accepted when the claimed files exist.

## 9. Failure & recovery (mission §27) — PASS

`tests/test_failure_recovery.py` (4 tests, green):

- transient `VALIDATION_FAILURE` → recovery `retry_with_hint` with explicit feedback →
  second attempt fixes + proves (`run_shell`) → task and objective **VERIFIED**
  (2 attempts, RETRYING in history, correct final file content).
- persistent failure (model keeps claiming DONE, machine check keeps failing) →
  original attempt + inserted **repair task** with its own retries (≥3 model attempts
  total) → task ends FAILED/NEEDS_USER/BLOCKED, objective **NEEDS_USER**, nothing
  VERIFIED, the unmet machine check is in the recorded verification results.
- budget exhaustion mid-plan → `NEEDS_USER` with open tasks, never VERIFIED.
- tool error (read of missing file) → observed (`status=error`, path in output),
  fails the task's machine verification, recovery retries → eventually VERIFIED.

## 10. Packaging & CI/CD (missions §18, §22, §24) — PASS (pipeline written; Windows MSI/NSIS built fresh 2026-09-23 with embedded sidecars proven, §0), FAIL-HERED (non-Windows bundles / release-attach)

- `bundle.externalBin`, per-triple binary naming, 7-permission capability scope —
  verified statically (above).
- `.github/workflows/desktop.yml` written and YAML-validated in this workspace
  (parses; job graph test/frontend/sidecar/desktop with correct `needs`).
  **Push note:** the Arena GitHub App integration lacks the `workflows` scope, so
  GitHub rejects pushes that create this file; it is in the workspace (and this
  report documents it) but lands on `main` only via the repo owner (or after the
  integration gains `workflows` permission).
- Pipeline: `test` (full pytest + acceptance) →
  `frontend` (npm ci + strict build, dist artifact) → `sidecar` (matrix
  ubuntu/windows/macos: PyInstaller freeze + **live smoke**: serve → `/v1/health` with
  issued token → port-conflict exit 3; artifacts uploaded) → `desktop` (matrix: npm
  build + fetch matching sidecar + `npx tauri build` + installer upload; tag-driven
  `gh release upload`). The same sidecar smoke was executed manually in this workspace
  against the installed console script (section 4).
- **Executed locally 2026-09-23** (Windows): cargo release compile (§5), PyInstaller
  MSVC freezes (§4/§0), Tauri MSI + NSIS builds with embedded sidecars proven (MSI file
  table + NSIS 7-Zip extraction, §0), and a real install smoke (§0). Orchestrator
  `scripts/build-desktop-release.ps1` + CI `release-desktop.yml` written. Still
  CI-owned / not done here: non-Windows bundles (.app/.dmg/AppImage) and GitHub
  release-attach — these remain release preconditions, not claimed done.

## 11. Documentation (mission §28) — PASS

- `README.md`: banner 1.0.1; face socket row + new Desktop 0.2 section (what's
  packaged, what's CI-owned).
- `docs/DESKTOP.md`: rewritten for 0.2 — non-developer flow, lifecycle table,
  exact authority semantics, security-boundary table with test evidence,
  **tested-here vs CI-owned honesty bar**, clean-machine release checklist (Windows
  first).
- `docs/API.md`: all 9 desktop endpoints + `why` shape + usage + memory documented
  with their status codes and crash-resume semantics.
- `docs/SECURITY.md`: new Desktop & sidecar section (loopback, fixed argv, token 0600,
  registry-gated artifacts, stale-process handling, UNRESTRICTED flag) + honest
  "Not covered" additions (Rust/installers CI-owned).
- `docs/ARCHITECTURE.md`: interface diagram updated (bundled sidecar, lifecycle-owned).
- `docs/ROADMAP.md`: "This change" row updated to Desktop 0.2 with the 783-test
  evidence and the CI-owned remainder; still **no GitHub Release / tag, not v1.1.0**.
- `desktop/README.md`: rewritten (sidecar build, dev fallback, security boundary;
  removed the non-existent `rad desktop` command from the 0.1 doc).

## 12. Full test suite — PASS

`python -m pytest -q` (in `.venv-dev`): **783 passed, 0 failed** in ~19 s
(baseline 697 + 86 new: desktop API 15, authority matrix 26, desktop security 14,
golden E2E 3, failure/recovery 4, desktop surface 2 extended, plus adjusted
pre-existing assertions that pinned old behavior: README banner test, desktop-surface
argv test).

## REMAINING (honest list — nothing below is claimed done)

1. **`cargo build`/`cargo check` of `desktop/src-tauri`** — **done locally 2026-09-23**
   (MSVC release shell 3,251,200 B → rebuilt 3,250,688 B after the resolver fix,
   install-smoked, §0); CI still owns cross-platform compile on other OSes.
2. **PyInstaller freeze for aarch64-apple-darwin** — **Windows x86_64-pc-windows-msvc
   done locally 2026-09-23** (rad 14,143,697 / backend 11,348,875, smoke-green, §0);
   Linux was already frozen + smoke-tested (section 4). macOS needs a native runner
   (CI `sidecar` job).
3. **Tauri installer builds** — **Windows MSI/NSIS built fresh 2026-09-23 with embedded
   sidecars proven** (MSI file table + NSIS 7-Zip extraction, §0). macOS (.app/.dmg)
   and Linux AppImage remain CI-owned.
4. **Clean-machine install pass** per platform (install → launch → no Python/Node →
   objective → VERIFIED → close → reopen → persisted) — release-checklist item in
   `docs/DESKTOP.md`. **Resolver gap fixed + re-smoked 2026-09-23 evening (§0):**
   installed backend resolves from the install dir short name
   (`…\RAD Desktop\rad-backend.exe`), health 200, clean uninstall. Still open: the
   pass above ran on the **build machine**, not a true no-repo machine — a
   clean-machine (or CI-only) run of the full release checklist is still required
   before claiming that item. The API-level equivalent (same objective flow,
   same persistence) is the golden E2E test above, and the frozen Linux sidecar's
   clean-machine binary requirement (self-contained vs glibc) is verified (section 4,
   `ldd`).
5. **AppImage on GitHub ubuntu runners** (FUSE availability) — known CI risk; if
   `tauri build` refuses, the Linux bundle target list needs adjusting in
   `tauri.conf.json` (deliberately not pre-empted without evidence).
6. **Live `npm run tauri dev` run** (dev fallback spawn path `python -m rad serve`) —
   **PASS closed 2026-09-24 (§0)**: full `tauri dev` from a C:-side source copy;
   React mounted via CDP, Python child parented to `rad-desktop`, health 200,
   UI `Studio Online`. Bare Python fallback was already proven (§0).
7. macOS **Intel** (x86_64-apple-darwin) triple — pipeline maps it, but no
   x86_64 macOS runner is in the CI matrix (current `macos-latest` is ARM). Add only
   if an Intel artifact is actually wanted.

## Appendix — how the Linux freeze was produced in this sandbox (reproducible)

```
# 1. sources (codeload.github.com is reachable in this sandbox)
codeload.github.com/python/cpython  v3.11.16
codeload.github.com/madler/zlib    v1.3.1
# 2. build (gcc-12/make available; no root needed)
./configure --prefix=.../cpython-install --enable-shared \
    CFLAGS="-O1 -g0 -I.../zlib-install/include" \
    LDFLAGS="-Wl,-rpath,.../cpython-install/lib -L.../zlib-install/lib"
make -j2                      # _ctypes/_ssl compile steps fail (no dev headers)
# 3. reuse ABI-compatible system extensions (same 3.11 minor → stable ABI)
cp /usr/lib/python3.11/lib-dynload/{_ctypes,_ssl,_hashlib}.cpython-311-x86_64-linux-gnu.so \
    build/lib.linux-x86_64-3.11/
# 4. tooling + freeze (pypi reachable)
./python -m ensurepip && ./python -m pip install -U pip \
    && ./python -m pip install -e ".[dev,sidecar]"
./python -m sidecar.build --triple x86_64-unknown-linux-gnu   # 12 s
```

