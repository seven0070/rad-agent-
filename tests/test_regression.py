"""Regression system: verdict rules, report comparison, and the live-benchmark wiring.

No pytest-inside-pytest here: `_pytest` is exercised only for its "skipped" path, while the
verdict/compare logic — the part that decides whether a change is accepted — is tested
directly against synthetic reports so the rules are pinned.
"""
import time

from rad.regression import TEST_GROUPS, RegressionSystem


def _report(label, **kw):
    base = {"at": time.time(), "label": label, "groups": {}, "benchmark": {}, "verdict": {}}
    base.update(kw)
    return base


def _groups(passed=100, failed=0, ok=True):
    return {"unit": {"skipped": False, "ok": ok, "passed": passed, "failed": failed,
                     "summary": f"{passed} passed, {failed} failed"}}


def _agent(success=1.0, safety=1.0, honesty=1.0, failures=()):
    return {"agent_sample": {"n": 10, "score": 100.0, "success_rate": success, "safety": safety,
                             "honesty": honesty, "failures": list(failures)}}


def _lh(**over):
    metrics = {"objective_completion_rate": 1.0, "correctness": 1.0, "recovery_rate": 1.0,
               "verification_accuracy": 1.0, "false_completion_rate": 0.0, "tool_failure_rate": 0.0,
               "human_intervention_rate": 0.0}
    metrics.update(over)
    return {"long_horizon": {"n": 6, "label": "x", "metrics": metrics}}


# ---------------------------------------------------------------- verdict

def test_verdict_passes_on_healthy_report(home):
    v = RegressionSystem._verdict({"groups": _groups(), "benchmark": {**_agent(), **_lh()}})
    assert v["pass"] and not v["problems"]


def test_verdict_fails_on_test_failures(home):
    v = RegressionSystem._verdict({"groups": _groups(passed=98, failed=2, ok=False), "benchmark": {}})
    assert not v["pass"] and "test failure" in v["problems"][0]


def test_verdict_fails_on_lab_failure_safety_or_honesty(home):
    v = RegressionSystem._verdict({"groups": _groups(),
                                   "benchmark": _agent(safety=0.9, honesty=0.8,
                                                       failures=["adversarial_003_fam2"])})
    joined = " ".join(v["problems"])
    assert not v["pass"]
    assert "scenario failure" in joined and "safety" in joined and "honesty" in joined


def test_verdict_fails_on_false_completion_or_incomplete_objectives(home):
    v = RegressionSystem._verdict({"groups": _groups(),
                                   "benchmark": {**_agent(), **_lh(objective_completion_rate=0.9,
                                                                   false_completion_rate=0.1)}})
    joined = " ".join(v["problems"])
    assert not v["pass"] and "completion" in joined and "false completion" in joined


# ---------------------------------------------------------------- compare

def test_compare_detects_regressions_and_improvements(home):
    base = _report("base", groups=_groups(100), benchmark={**_agent(), **_lh()})
    same = _report("same", groups=_groups(100), benchmark={**_agent(), **_lh()})
    assert RegressionSystem.compare(base, same)["verdict"] == "ok"

    worse = _report("worse", groups=_groups(95),
                    benchmark={**_agent(success=0.8, honesty=0.9), **_lh(tool_failure_rate=0.2)})
    cmp = RegressionSystem.compare(base, worse)
    assert cmp["verdict"] == "REGRESSION"
    joined = " ".join(cmp["regressions"])
    assert "unit" in joined and "success" in joined and "honesty" in joined and "tool_failure_rate" in joined


def test_compare_flags_better_long_horizon_without_regression(home):
    base = _report("base", groups=_groups(100),
                   benchmark={**_agent(), **_lh(recovery_rate=0.8, tool_failure_rate=0.02)})
    better = _report("better", groups=_groups(100),
                     benchmark={**_agent(), **_lh(recovery_rate=1.0, tool_failure_rate=0.01)})
    assert RegressionSystem.compare(base, better)["regressions"] == []


# ---------------------------------------------------------------- plumbing

def test_test_groups_are_named_and_disjoint():
    assert set(TEST_GROUPS) == {"unit", "security", "agent", "integration"}
    flat = [f for files in TEST_GROUPS.values() for f in files]
    assert len(flat) == len(set(flat))


def test_unknown_test_file_is_skipped_not_failed(home):
    rs = RegressionSystem(home)
    out = rs._pytest(["test_does_not_exist.py"])
    assert out["skipped"] and "no such tests" in out["reason"]


def test_history_and_render_round_trip(home, monkeypatch):
    rs = RegressionSystem(home)
    # don't shell out: verify the report writing + render path
    monkeypatch.setattr(rs, "_pytest", lambda files: {"skipped": True, "reason": "test stub"})
    monkeypatch.setattr(rs, "_lab", lambda suite, sample, label: {
        "n": sample, "score": 100.0, "success_rate": 1.0, "safety": 1.0, "honesty": 1.0,
        "label": label, "failures": [], "results": []})
    monkeypatch.setattr(rs, "_longhorizon", lambda sample: {
        "label": "lh", "n": sample, "metrics": {"objective_completion_rate": 1.0, "correctness": 1.0,
                                                "recovery_rate": 1.0, "verification_accuracy": 1.0,
                                                "false_completion_rate": 0.0, "tool_failure_rate": 0.0}})
    rep = rs.run(groups=["security"], sample=3, benchmarks=True, label="unit-test")
    assert rep["verdict"]["pass"]
    assert rs.latest()["label"] == "unit-test"
    rendered = RegressionSystem.render(rep)
    assert "unit-test" in rendered and "long-horizon" in rendered
