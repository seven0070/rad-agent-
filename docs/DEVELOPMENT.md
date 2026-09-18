# Development

## Layout

```
rad/
  cli.py            argument parser + thin command wrappers (no agent logic lives here)
  home.py           ~/.rad layout, config
  session.py        one chat turn: context → model → tools → memory
  tools.py          the tool registry + the single enforcement point (run_tool)
  policy.py         capability decisions, hard layer, audit, secret redaction
  sandbox.py        grants, limits, workspace jail, agent envelopes
  control/          the control plane: objectives, planner, graph, scheduler, executor,
                    observer, verifier, recovery, budgets, checkpoints, lifecycle, events,
                    replay, provenance, controller
  memory.py         working/episodic/semantic/procedural memory + origins/confidence
  usermodel.py, world.py            user model, world model (facts/assumptions)
  agents.py         agent registry, runtime, blackboard, lifecycle, scheduler, bus, evaluator
  router.py, modelselect.py, providers.py   routing, requirements, profiles, selection
  lab.py, lab_banks.py, longhorizon.py      benchmarks (900 scenarios, long-horizon metrics)
  evaluation.py, regression.py, realworld.py, acceptance.py   measurement and the gate
  browser.py, background.py, skills.py, mcp.py, storage.py, doctor.py, api.py, evolution.py,
  experience.py, dna.py, memory.py, voice.py, drive.py, jobs.py, corpora…
tests/              275 tests, all offline
docs/               this documentation set
```

## Running the tests

```bash
python -m pytest -q                 # everything (~8s, no network, no keys)
python -m pytest -q tests/test_policy.py -k hard
rad regression --quick              # security + agent groups + a live benchmark sample
rad acceptance                      # the 50-item gate, with per-item evidence
```

The suite is expected to pass **offline**. A test that needs the network, a key or a model is a bug
in the test: use a scripted session (`tests/test_control_plane.ScriptedSession`) or a fake HTTP
layer, as `tests/test_browser_tools.py` and `tests/test_mcp.py` do.

## Adding a tool

1. Add a schema entry to `TOOLS` in `rad/tools.py` (name, description, parameters).
2. Add the branch in `_run_tool`, gated: `limits = _gate(ctx, CAP_X, resource, prompt, tool=name)`.
3. Map the name to its capability in `rad/agents.py: TOOL_CAP` (unknown names default to `shell`,
   the most restrictive kind, so forgetting the mapping is safe but noisy).
4. If it touches the network or the filesystem, check `rad/sandbox.py` handles it, and add the
   capability to `NETWORK_TOOLS`/`CAP_TO_KIND` when relevant.
5. Add a test that proves a refusal *and* a success path (see `tests/test_browser_tools.py`).

## Adding a scenario to the lab

`rad/lab_banks.py` builds the 900-scenario bank from templates: a goal, a plan, a script of tool
calls, graders (file/shell/json checks), canaries and budget. Add a template with `_s(...)`, and the
bank count, the long-horizon metrics and the acceptance items pick it up automatically. Graders must
be deterministic and disk-based.

## Adding a migration

Extend `rad/storage.py`:

```python
def _m4_something(home): ...            # idempotent, tolerant, quarantines what it cannot parse
MIGRATIONS.append(Migration(4, "what it does", _m4_something))
SCHEMA_VERSION = 4
```

The `assert [m.version for m in MIGRATIONS] == list(range(1, SCHEMA_VERSION + 1))` line keeps the
list honest, and every migration runs behind a snapshot.

## Rules the codebase follows

* **The model proposes, the executor decides.** Nothing in the codebase calls a tool except through
  `rad.tools.run_tool` / `rad/control/executor.py`.
* **Verification is independent.** Completion comes from `rad/control/verifier.py` checks and
  graders, never from a model's sentence. Add a check kind rather than trusting a claim.
* **Failures are observations.** Denials, tool errors and crashes are recorded (observation +
  event + audit), classified (`rad/control/recovery.py`) and then handled with a bounded strategy.
* **No hidden state.** New persistent state goes through `RadHome` as JSON/markdown, is added to
  `rad doctor`, and is covered by `rad storage check`.
* **No feature theater.** A capability that cannot be demonstrated by the acceptance gate is not
  finished; prefer extending an existing subsystem over adding a parallel one.
* **No heavy dependencies in the core.** `dependencies = []`; extras stay optional and are probed
  (`playwright_available()`, `kuzu_available()`), with an honest refusal when missing.
* **Docs describe shipped behaviour.** `docs/CLI.md` is generated from the parser and the acceptance
  gate checks that the commands referenced in the docs exist.

## Contributing checklist

```bash
python -m pytest -q && rad regression --quick && rad acceptance
```

A change is ready when the tests pass, the regression verdict is PASS, and all 50 acceptance items
still pass — the gate is the contract this repository holds itself to.
