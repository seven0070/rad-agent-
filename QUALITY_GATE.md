# Final quality gate (v0.2.1)

Only items **actually run** on this machine are marked PASS. Untested live NIM is BLOCKED, not PASS.

**HEAD of work:** branch `cursor/rad-v03-realworld-needle-56b4` off `main` `c93f82b`.  
**Version:** `0.2.1` — Class A controller fix + optional Needle adapter. **Not v0.3.0.**

| gate | result | how |
|---|---|---|
| Baseline pytest on `c93f82b` | **PASS** 303 | `python -m pytest -q` |
| Pytest after changes | **PASS** 326 in 8.27s | same command |
| `rad doctor --offline` | **PASS** READY exit 0 | `/tmp/rad-v021-gate` |
| `rad acceptance` | **PASS** 50/50 | `/tmp/rad-v021-gate` |
| `rad realworld` | **PASS** 10/11 + 1 BLOCKED | `/tmp/rad-v021-rw` |
| `rad version` | **PASS** v0.2.1 | |
| Class A regressions | **PASS** | `tests/test_control_plane.py` budget/overdecompose |
| False-success / needs_user / no-loop | **PASS** | realworld + pytest |
| Needle isolation | **PASS** | `rad needle-eval` + `tests/test_toolrouter.py` |
| Needle real engine gold set | **RUN** (no integrate) | selection 0.60 < heuristic 0.80 |
| Existing path without Needle | **PASS** | default config; fallback tests |
| Live NVIDIA NIM chat | **BLOCKED** | no `NVIDIA_NIM_API_KEY` / `NVIDIA_API_KEY` |
| Live NIM `objective run` | **BLOCKED** | same |
| NIM → Needle → RAD | **BLOCKED** | no NIM key |
| Secrets in git | **PASS** (inspected) | none committed or printed |
| DONE semantics | **PASS** | unmet checks still not VERIFIED |
| Architecture freeze | **PASS** | no new control-plane rewrite |

## Versioning rule (applied)

v0.3.0 only if a meaningful validated capability is integrated. Needle remains optional and did not beat the existing router on measured RAD tools → **0.2.1**.
