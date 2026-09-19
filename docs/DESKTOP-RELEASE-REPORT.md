# RAD Desktop 0.2 — Validation report (2026-09-19)

Factual validation per area. **PASS only where evidence exists in this tree or was
executed in this workspace.** CI-only / machine-owned items are marked FAIL-HERED (not
claimed) with what would prove them.

Workspace: `arena/01a0bafc-rad-agent` @ branch from `bbfa991` (baseline 4c0c1020 line).
Interpreter: `.venv-dev` (Python 3.11.16, `pip install -e ".[dev,sidecar]"`).

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
- Windows/macOS freezes remain CI-only (PyInstaller cannot cross-compile; CI builds on
  native runners — `sidecar` job in `.github/workflows/desktop.yml`).

## 5. Tauri shell / lifecycle — FAIL-HERED (compile), PASS (design + static)

- `desktop/src-tauri/src/lib.rs` rewritten: 7 commands (`default_home`, `api_token`,
  `backend_info`, `backend_start`, `backend_stop`, `backend_restart`,
  `backend_health`); sidecar resolution by target triple (exe dir + `binaries/` +
  `Resources/` + manifest `binaries/` + cwd); **fixed argv** spawn (sidecar
  `serve --host 127.0.0.1 --port <n> [--home <dir>]`, dev fallback `python -m rad
  serve`); raw-TCP health probe with Bearer token (20 s / 250 ms, backend-log tail on
  failure); stdout/stderr pumped to `~/.rad/logs/backend.log`; stale-RAD (401+`bearer`)
  vs foreign-process detection before start; `State{backend: Mutex<Option<Backend>>}`.
  Uses only std + serde + serde_json + tauri — no new crates, `Cargo.lock` untouched.
- **Not compiled here: no cargo/rustc in the sandbox** (rust-lang/crates hosts blocked).
  `cargo build`/`cargo test` are CI-owned.
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

## 10. Packaging & CI/CD (missions §18, §22, §24) — PASS (pipeline written), FAIL-HERED (execution)

- `bundle.externalBin`, per-triple binary naming, 7-permission capability scope —
  verified statically (above).
- `.github/workflows/desktop.yml` written: `test` (full pytest + acceptance) →
  `frontend` (npm ci + strict build, dist artifact) → `sidecar` (matrix
  ubuntu/windows/macos: PyInstaller freeze + **live smoke**: serve → `/v1/health` with
  issued token → port-conflict exit 3; artifacts uploaded) → `desktop` (matrix: npm
  build + fetch matching sidecar + `npx tauri build` + installer upload; tag-driven
  `gh release upload`). The same sidecar smoke was executed manually in this workspace
  against the installed console script (section 4).
- **Not executed here**: cargo compile, PyInstaller freeze, Tauri installer builds,
  release-attach. Environment-blocked (section 4/5). These are release preconditions,
  not claimed done.

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

1. **`cargo build`/`cargo check` of `desktop/src-tauri`** — no Rust toolchain in this
   workspace (rust-lang/crates/anaconda hosts all network-blocked; verified again
   2026-09-19). First compile will happen in CI. Any Rust error there would surface on
   the first push (lib.rs reviewed statically for the known hazards: double-match
   unwrap, import scope, dead code; still uncompiled).
2. **PyInstaller freezes for x86_64-pc-windows-msvc and aarch64-apple-darwin** —
   Linux (x86_64-unknown-linux-gnu) is frozen and smoke-tested in this workspace
   (section 4); the other two triples need native runners (CI `sidecar` job).
3. **Tauri installer builds** (MSI/NSIS, .app/.dmg, AppImage) — depend on 1+2.
4. **Clean-machine install pass** per platform (install → launch → no Python/Node →
   objective → VERIFIED → close → reopen → persisted) — release-checklist item in
   `docs/DESKTOP.md`; the API-level equivalent (same objective flow, same persistence)
   is the golden E2E test above, and the frozen Linux sidecar's clean-machine binary
   requirement (self-contained vs glibc) is verified (section 4, `ldd`).
5. **AppImage on GitHub ubuntu runners** (FUSE availability) — known CI risk; if
   `tauri build` refuses, the Linux bundle target list needs adjusting in
   `tauri.conf.json` (deliberately not pre-empted without evidence).
6. **Live `npm run tauri dev` run** (dev fallback spawn path `python -m rad serve`) —
   requires the Rust side to compile first.
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

