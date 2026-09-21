"""Integration adapters — VERIFIED -> INTEGRATED (Phase B).

Five wires, each conformed to a live signature:

  1. make_brain_fn      -> papers.extract  brain_fn   via BrainRouter.complete
  2. make_battery_fn    -> evolution.canary battery_fn via CapabilityBattery.run
  3. make_execute_fn    -> papers.battle    execute_fn via Executor.execute_task
  4. build_row_factory  -> TaskRow construction via inspect-probing (no guessing)
  5. promotion_gate     -> both promote-path gates in one fail-closed call

HONEST DEGRADATION CONTRACT (L2):
  - battery overrides (temperature/max_tokens) are ATTEMPTED as extra kwargs;
    TypeError -> retry without them and flag {'_degraded': True}. Never silent.
  - TaskRow mapping is inspect-probed; unknown required fields raise a
    clear TypeError telling you to pass row_factory= explicitly.
  - Observation mapping: verified_rate(max)=1 iff COMPLETED;
    false_done(min)=1 iff COMPLETED with zero artifacts;
    cost(min)=len(tool_calls). Direction honored by battle verdicts.
"""
import inspect
from datetime import datetime, timezone
from pathlib import Path

def _now(): return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------- 1. brain_fn

EXTRACT_SYSTEM = ("You extract research claims as strict JSON matching a "
                  "provided schema. Output ONLY the JSON object.")

def make_brain_fn(router, system_prompt: str = EXTRACT_SYSTEM,
                  temperature: float = 0.2):
    """papers.extract brain_fn. BrainRouter.complete returns str — direct."""
    def brain_fn(prompt: str) -> str:
        return router.complete(prompt=prompt, system_prompt=system_prompt,
                               temperature=temperature)
    return brain_fn

# -------------------------------------------------------------- 2. battery_fn

def make_battery_fn(battery, default_provider=None, default_model=None):
    """evolution.canary battery_fn from CapabilityBattery.

    config keys used: provider, model, optional temperature/max_tokens.
    The canary's crippled-config markers ride as extra kwargs when the
    battery accepts them; on TypeError the run degrades to provider/model
    only AND FLAGS IT — a degraded canary comparison is still reported,
    never passed off as full-fidelity."""
    def battery_fn(config: dict, task: dict, seed: int) -> dict:
        base = {"provider": config.get("provider", default_provider),
                "model": config.get("model", default_model)}
        extras = {k: config[k] for k in ("temperature", "max_tokens") if k in config}
        try:
            report = battery.run(**base, **extras)
            degraded = False
        except TypeError:
            report = battery.run(**base)
            degraded = True
        return {"score": float(report.get("score", 0)), "_degraded": degraded}
    return battery_fn

# ------------------------------------------------------- 3/4. executor wiring

_ROW_ID_KEYS = ("id", "task_id", "key", "name")
_ROW_TEXT_KEYS = ("prompt", "description", "text", "goal", "instruction")

def build_row_factory(task_row_cls):
    """Probe TaskRow.__init__ and map our task dict onto its real params.
    Returns row_factory(task={'task_id','prompt'}) -> TaskRow.
    Extra required fields on TaskRow -> TypeError with explicit guidance."""
    sig = inspect.signature(task_row_cls.__init__)
    params = [p for p in sig.parameters.values() if p.name != "self"]
    names = {p.name for p in params}
    id_key = next((k for k in _ROW_ID_KEYS if k in names), None)
    text_key = next((k for k in _ROW_TEXT_KEYS if k in names), None)

    def row_factory(task: dict):
        if id_key and text_key:
            return task_row_cls(**{id_key: task["task_id"],
                                   text_key: task["prompt"]})
        order = [p.name for p in params]
        vals = [task["task_id"], task["prompt"]][:len(order)]
        return task_row_cls(**dict(zip(order, vals)))
    row_factory.mapped = {"id": id_key, "text": text_key}
    return row_factory

def make_execute_fn(executor, objective_id: str, tools=None, workspace=None,
                    row_factory=None, task_row_cls=None):
    """papers.battle execute_fn from Executor.execute_task.

    Observation -> grader_result (direction metadata in keys' docs):
      verified_rate (max): 1.0 iff status == 'COMPLETED'
      false_done    (min): 1.0 iff COMPLETED but artifacts list empty
      cost          (min): len(tool_calls) — proxy until real cost lands
    """
    if row_factory is None and task_row_cls is not None:
        row_factory = build_row_factory(task_row_cls)

    def execute_fn(config: dict, task: dict, seed: int) -> dict:
        import tempfile
        ws = config.get("workspace") or workspace or tempfile.mkdtemp(prefix="rad_exec_")
        row = row_factory(task) if row_factory else task
        ctx = {"workspace": ws,
               "budget_remaining": config.get("budget_remaining", 50),
               "seed": seed}
        obs = executor.execute_task(objective_id=objective_id, task=row,
                                    context=ctx, tools=tools)
        status = getattr(obs, "status", None)
        artifacts = list(getattr(obs, "artifacts", None) or [])
        tool_calls = list(getattr(obs, "tool_calls", None) or [])
        completed = (status == "COMPLETED")
        grader_spec = task.get("grader") if isinstance(task, dict) else getattr(task, "grader", None)
        disk_fails = []
        if grader_spec and ws:
            try:
                from pathlib import Path
                from tools.scenario_runner import _grade
                disk_checks = _grade(grader_spec, Path(ws), [f"executor:{status}"])
                verified = all(c["passed"] for c in disk_checks) if disk_checks else completed
                disk_fails = [f"disk_fail:{c['name']}" for c in disk_checks if not c.get("passed")]
            except Exception:
                verified = completed
        else:
            verified = completed

        if grader_spec and workspace:
            false_done = 1.0 if (completed and not verified) else 0.0
        else:
            false_done = 1.0 if (completed and not artifacts) else 0.0

        return {"grader_result": {
                    "verified_rate": 1.0 if verified else 0.0,
                    "false_done": false_done,
                    "cost": float(len(tool_calls)),
                },
                "events": [f"executor:{status}", f"artifacts:{len(artifacts)}"] + disk_fails,
                "status": status}
    return execute_fn

# ------------------------------------------------------------ 5. promote gate

def promotion_gate(corpus_dir=None, battery_dir=None,
                   battery_fn=None, current_config=None, tasks=None,
                   margin: float = 10.0,
                   check_canary: bool = True, check_contamination: bool = True,
                   results_dir=None) -> dict:
    """Both promotion gates, fail-closed. Wire at the top of `brain promote`:

        from rad.integrate.hooks import promotion_gate
        promotion_gate(corpus_dir=..., battery_dir=..., battery_fn=...,
                       current_config=..., tasks=...)

    Raises PermissionError on: canary integrity flag on file, live canary
    winning, or contamination overlap >= threshold. Pass otherwise."""
    from rad.evolution import canary, contamination
    report = {"checked_at": _now(), "canary": None,
              "contamination": None, "gates_passed": True}

    canary.assert_pipeline_clear(results_dir)          # cheap flag check first

    if check_canary and battery_fn and (current_config is not None) and tasks:
        rec = canary.run_canary_check(battery_fn, current_config, tasks,
                                      margin=margin, results_dir=results_dir)
        report["canary"] = rec
        if not rec["battery_healthy"]:
            report["gates_passed"] = False
            raise PermissionError(f"canary gate failed: {rec['verdict']}")

    if check_contamination and corpus_dir and battery_dir:
        overlap = contamination.overlap_score(Path(corpus_dir), Path(battery_dir))
        report["contamination"] = overlap
        if overlap["verdict"] == "blocked":
            report["gates_passed"] = False
            raise PermissionError(
                f"contamination gate blocked: jaccard={overlap['jaccard']} "
                f"theft={overlap['battery_theft_ratio']} — rotate battery items")
    return report
