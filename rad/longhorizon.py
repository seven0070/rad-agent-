"""Long-horizon benchmark — objectives that take 20–50 meaningful actions.

The banks in `rad.lab_banks` guarantee that each scenario performs at least twelve
real tool actions; this module runs them (or any scenario list) and reports the
numbers that actually say whether an autonomous agent is any good:

    objective completion    did the objective reach the expected terminal state
    task completion         tasks completed / tasks planned (partial work is visible)
    correctness             did deterministic graders agree the artifact is right
    verification accuracy   did the Verifier's verdict agree with the graders
    recovery rate           of the runs that hit an injected fault, how many recovered
    human intervention rate runs that ended needs_user / failed
    tool failure rate       failed tool calls / tool calls
    retries                 attempts beyond the first
    cost / latency          USD (0 on free/local) and wall-clock seconds
    false completion rate   objectives the *system* marked VERIFIED while graders failed

    rad benchmark long [--sample 10] [--suite bank:long_horizon] [--json]
"""
from __future__ import annotations

import json
import statistics
import time
from typing import Any, Dict, List, Optional

from rad.home import RadHome, _read_json, _write_json

DEFAULT_SUITE = "bank:long_horizon"


class LongHorizonBenchmark:
    def __init__(self, home: RadHome) -> None:
        self.home = home
        self.dir = home.root / "benchmarks" / "longhorizon"
        self.dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ run
    def run(self, suite: str = DEFAULT_SUITE, sample: int = 0, label: str = "",
            seed: int = 0, faults: bool = True, progress=None) -> Dict[str, Any]:
        from rad.lab import Lab
        lab = Lab(self.home)
        report = lab.run(suite=suite, label=label or f"lh-{time.strftime('%Y%m%d-%H%M%S')}",
                         seed=seed, sample=sample, progress=progress)
        metrics = self.metrics(report.get("results", []))
        out = {"at": time.time(), "label": report.get("label"), "suite": suite,
               "n": report.get("n", 0), "metrics": metrics,
               "lab": {k: report.get(k) for k in
                       ("score", "success_rate", "verified_rate", "honesty", "safety",
                        "seconds", "tool_calls", "model_calls", "retries", "cost_usd")},
               "ids": [r["id"] for r in report.get("results", [])]}
        _write_json(self.dir / f"{time.strftime('%Y%m%d-%H%M%S')}_{out['label']}.json", out)
        return out

    # ------------------------------------------------------------------ metrics
    @staticmethod
    def metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        n = len(results) or 1
        completed = [r for r in results if r.get("status") == "completed"]
        graders_ok = [r for r in results
                      if all(g.get("ok") for g in r.get("graders", []) if not str(g.get("kind", "")).startswith("follow_up:"))
                      and r.get("trajectory_ok", True)]
        verified = [r for r in results if r.get("verified") == "VERIFIED"]
        faults = [r for r in results if int(r.get("injected_faults", 0)) > 0
                  or int(r.get("task_attempts", 0)) > int(r.get("tasks_total", 0))]
        recovered = [r for r in faults if r.get("status") == "completed" and int(r.get("recovered", 0)) > 0]
        tools = sum(int(r.get("tool_calls", 0)) for r in results)
        tool_errors = sum(int(r.get("tool_errors", 0)) for r in results)
        attempts = sum(int(r.get("task_attempts", 0)) for r in results)
        tasks = sum(int(r.get("tasks_total", 0)) for r in results)
        tasks_done = sum(int(r.get("tasks_completed", 0)) for r in results)
        secs = [float(r.get("seconds", 0) or 0) for r in results]
        verified_agree = sum(1 for r in results
                             if (r.get("verified") == "VERIFIED") == bool(all(
                                 g.get("ok") for g in r.get("graders", [])
                                 if not str(g.get("kind", "")).startswith("follow_up:"))))
        return {
            "objective_completion_rate": round(len(completed) / n, 3),
            "task_completion_rate": round(tasks_done / tasks, 3) if tasks else None,
            "correctness": round(len(graders_ok) / n, 3),
            "verification_accuracy": round(verified_agree / n, 3),
            "recovery_rate": round(len(recovered) / len(faults), 3) if faults else None,
            "runs_needing_recovery": len(faults),
            "human_intervention_rate": round(sum(1 for r in results
                                                  if r.get("status") in ("needs_user", "failed")) / n, 3),
            "tool_failure_rate": round(tool_errors / tools, 4) if tools else 0.0,
            "tool_calls": tools,
            "tool_blocked": sum(int(r.get("tool_blocked", 0)) for r in results),
            "retries": max(0, attempts - tasks),
            "model_calls": sum(int(r.get("model_calls", 0)) for r in results),
            "cost_usd": round(sum(float(r.get("cost_usd", 0) or 0) for r in results), 6),
            "latency_s_mean": round(statistics.mean(secs), 3) if secs else 0.0,
            "latency_s_p95": round(sorted(secs)[max(0, int(len(secs) * 0.95) - 1)], 3) if secs else 0.0,
            "actions_per_objective": round(tools / n, 2),
            "false_completion_rate": round(sum(1 for r in results if r.get("verified_false_completion")) / n, 4),
            "model_false_claims": sum(1 for r in results if r.get("model_false_claim")),
        }

    # ------------------------------------------------------------------ history
    def history(self, n: int = 20) -> List[Dict[str, Any]]:
        out = []
        for p in sorted(self.dir.glob("*.json"), reverse=True)[:n]:
            d = _read_json(p, None)
            if isinstance(d, dict):
                d["path"] = str(p)
                out.append(d)
        return out

    def latest(self) -> Optional[Dict[str, Any]]:
        h = self.history(1)
        return h[0] if h else None

    @staticmethod
    def compare(base: Dict[str, Any], cand: Dict[str, Any]) -> Dict[str, Any]:
        keys = ("objective_completion_rate", "task_completion_rate", "correctness",
                "verification_accuracy", "recovery_rate", "human_intervention_rate",
                "tool_failure_rate", "false_completion_rate")
        deltas = {}
        regressions = []
        for k in keys:
            b, c = (base.get("metrics", {}) or {}).get(k), (cand.get("metrics", {}) or {}).get(k)
            if b is None or c is None:
                continue
            deltas[k] = round(c - b, 4)
            lower_is_better = k in ("human_intervention_rate", "tool_failure_rate",
                                    "false_completion_rate", "latency_s_mean")
            if (c > b and not lower_is_better) or (c < b and lower_is_better):
                regressions.append(k)
        return {"base": base.get("label"), "cand": cand.get("label"), "deltas": deltas,
                "regressions": regressions,
                "verdict": "REGRESSION" if regressions else "ok"}

    # ------------------------------------------------------------------ view
    @staticmethod
    def render(rep: Dict[str, Any]) -> str:
        from rad.ui import col
        m = rep.get("metrics", {})
        if not m:
            return "no long-horizon runs yet — `rad benchmark long --sample 10`"
        rows = [
            ("objective completion", m.get("objective_completion_rate")),
            ("task completion", m.get("task_completion_rate")),
            ("correctness (graders)", m.get("correctness")),
            ("verification accuracy", m.get("verification_accuracy")),
            ("recovery rate", m.get("recovery_rate")),
            ("human intervention", m.get("human_intervention_rate")),
            ("tool failure rate", m.get("tool_failure_rate")),
            ("retries", m.get("retries")),
            ("actions/objective", m.get("actions_per_objective")),
            ("cost (USD)", m.get("cost_usd")),
            ("latency mean/p95 (s)", f"{m.get('latency_s_mean')} / {m.get('latency_s_p95')}"),
            ("false completion rate", m.get("false_completion_rate")),
        ]
        lines = [col.bold(f"long-horizon {rep.get('label')}  n={rep.get('n')}  suite={rep.get('suite')}")]
        for name, val in rows:
            lines.append(f"  {name:<24} {val}")
        return "\n".join(lines)
