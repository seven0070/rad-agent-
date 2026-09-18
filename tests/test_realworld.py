"""The four real-world acceptance tests, run as part of the normal suite.

They are end-to-end: whole objectives through the real control plane, real tools on disk,
independent verification. If these fail, RAD is not finished — so they are pinned here.
"""
import json

from rad.realworld import RealWorldSuite


def test_research_multi_source_cross_check(home):
    rep = RealWorldSuite(home).run(["research"])
    t = rep["tests"][0]
    assert t["passed"], t["problems"]
    failed = [c["what"] for c in t["checks"] if not c["ok"]]
    assert not failed, failed
    assert t["verified"] == "VERIFIED"
    assert t["artifacts"] and t["artifacts"][0]["sha256"]


def test_coding_inspect_implement_test_repair_verify(home):
    rep = RealWorldSuite(home).run(["coding"])
    t = rep["tests"][0]
    assert t["passed"], t["problems"]
    assert t["verified"] == "VERIFIED"
    assert "ALL TESTS PASSED" in t.get("test_output", "")
    assert t["tool_errors"] >= 1                    # the injected failure really happened


def test_multi_agent_independent_verification(home):
    rep = RealWorldSuite(home).run(["multi_agent"])
    t = rep["tests"][0]
    assert t["passed"], t["problems"]
    assert set(t["agents"]) >= {"researcher", "writer", "reviewer"}
    assert t["verified"] == "VERIFIED"


def test_failure_recovery_and_crash_resume(home):
    rep = RealWorldSuite(home).run(["failure"])
    t = rep["tests"][0]
    assert t["passed"], t["problems"]
    assert t["crash_resume"]["detected"] and t["crash_resume"]["restored"]
    assert t["crash_resume"]["resumed_status"] == "completed"


def test_suite_reports_everything_and_writes_evidence(home):
    rep = RealWorldSuite(home).run(["research", "multi_agent"])
    assert rep["total"] == 2 and rep["ok"]
    doc = json.loads(open(rep["report"]).read())
    assert doc["passed"] == 2 and all(t["checks"] for t in doc["tests"])
