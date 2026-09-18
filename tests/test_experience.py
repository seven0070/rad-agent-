"""Experience learning — lessons are proposed from outcomes and must be validated.

The rules under test:
  * a recovery that worked becomes a `supported` lesson → procedural memory (low confidence)
  * the same recovery seen twice, with no contradicting episode → `validated` → behaviour
  * a failure with no successful recovery never becomes a rule
  * efficiency measurements are recorded but never promoted into behaviour
"""
import json
import time
from pathlib import Path

import pytest

from rad.control import Controller, ObjectiveStatus
from rad.control.graph import TaskGraph
from rad.control.observer import Observer
from rad.control.tasks import Check, Task, TaskStatus
from rad.experience import Experience, KIND_EFFICIENCY, KIND_RECOVERY, KIND_SAFETY, Lesson
from rad.memory import OBSERVED, Memory
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm


@pytest.fixture
def ws(home, tmp_path):
    w = tmp_path / "ws"
    w.mkdir()
    home.update(workspace=str(w))
    return w


@pytest.fixture
def scripted():
    ScriptedSession.script = []
    ScriptedSession.prompts = []
    return ScriptedSession


def _write_objective(home, oid, tasks, events=None):
    d = home.root / "objectives" / oid
    d.mkdir(parents=True, exist_ok=True)
    (d / "tasks.json").write_text(json.dumps(tasks), encoding="utf-8")
    with open(d / "events.jsonl", "a", encoding="utf-8") as f:
        for ev in (events or []):
            f.write(json.dumps(ev) + "\n")


def _episode_task(tid, failure_class, status, verified, attempts, strategy=""):
    return {"id": tid, "objective_id": "obj_x", "text": "do a thing", "status": status,
            "attempts": attempts, "failure_class": failure_class,
            "verification": {"status": verified} if verified else {},
            "history": [{"from": "RUNNING", "to": "FAILED", "at": time.time(), "note": "x"}]}


def test_recovery_lesson_is_supported_then_validated(home):
    exp = Experience(home)
    _write_objective(home, "obj_a", [_episode_task("t1", "VALIDATION_FAILURE", "COMPLETED", "VERIFIED", 2)])
    les = Lesson.new(KIND_RECOVERY, "when a step fails with VALIDATION_FAILURE, retrying with feedback worked",
                     objective_id="obj_a", failure_class="VALIDATION_FAILURE")
    exp.validate(les)
    assert les.status == "supported" and les.supports == 1
    # a second independent episode validates it
    _write_objective(home, "obj_b", [_episode_task("t1", "VALIDATION_FAILURE", "COMPLETED", "VERIFIED", 3)])
    exp.validate(les)
    assert les.status == "validated" and les.supports >= 2
    assert exp.promote(les) is True
    mem = Memory(home)
    hits = [e for e in mem.scan("procedural") if "VALIDATION_FAILURE" in e.text]
    assert hits and hits[0].origin == OBSERVED and "lesson" in hits[0].tags
    assert "lesson-candidate" not in hits[0].tags or les.status == "validated"


def test_recovery_lesson_with_only_failures_is_contradicted(home):
    exp = Experience(home)
    _write_objective(home, "obj_a", [_episode_task("t1", "TOOL_FAILURE", "FAILED", "", 3)])
    les = Lesson.new(KIND_RECOVERY, "retry fixes TOOL_FAILURE", failure_class="TOOL_FAILURE")
    exp.validate(les)
    assert les.status == "contradicted"
    assert exp.promote(les) is False
    assert [e for e in Memory(home).scan("procedural")] == []


def test_efficiency_lessons_are_recorded_but_not_behaviour(home):
    exp = Experience(home)

    class FakeUsage:
        tool_calls, retries, seconds = 7, 2, 42

    class FakeObj:
        id = "obj_eff"
        goal = "summarise something"
        usage = FakeUsage()

    lessons = exp.analyze(FakeObj(), TaskGraph())
    eff = [l for l in lessons if l.kind == KIND_EFFICIENCY]
    assert eff and "7 tool calls" in eff[0].text
    exp.validate(eff[0])
    assert eff[0].status == "supported"
    assert exp.promote(eff[0]) is False
    assert [e for e in Memory(home).scan("procedural")] == []


def test_lesson_store_roundtrip_and_stats(home):
    exp = Experience(home)
    l = Lesson.new(KIND_RECOVERY, "something", failure_class="X")
    exp.save(l)
    exp.validate(l)
    again = Experience(home).lessons()
    assert again and again[0].id == l.id
    st = exp.stats()
    assert st["lessons"] >= 1 and "by_status" in st and st["by_kind"].get(KIND_RECOVERY)
    assert "no lessons yet" not in exp.show()


def test_controller_run_creates_and_promotes_a_lesson(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "make report", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "report.md"}}]}]}
    scripted.script = [([], "DONE: (lie)"),
                       ([("write_file", {"path": "report.md", "content": "real"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("make a report"))
    assert obj.status == ObjectiveStatus.COMPLETED
    lessons = Experience(home).lessons()
    rec = [l for l in lessons if l.kind == KIND_RECOVERY]
    assert rec and rec[0].failure_class == "VALIDATION_FAILURE"
    assert rec[0].status in ("supported", "validated") and rec[0].promoted
    report = ctl.last_run.get("lessons")
    assert report and report["proposed"] >= 1


def test_safety_lesson_recorded_when_policy_denies(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "read secret", "depends_on": [], "checks": []}]}
    scripted.script = [([("read_file", {"path": "/etc/shadow"})], "BLOCKED: cannot")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("read secret"))
    obs = Observer(ctl.store.dir(obj.id))
    assert any(o.status in ("blocked", "declined") for o in obs.observations())
    lessons = Experience(home).lessons()
    assert any(l.kind == "safety" for l in lessons) or any(l.kind == KIND_SAFETY for l in lessons)
