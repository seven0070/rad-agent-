"""Phase 3 — reliability: parallel execution, transcripts + replay, provenance, budgets across
resumes, and a long-horizon objective with mixed failures."""
import json
import threading
import time
from pathlib import Path

import pytest

from rad.control import Controller, ObjectiveStatus, TaskStatus
from rad.control import events as E
from rad.control.events import EventLog
from rad.control.objectives import Budget
from rad.control.provenance import Provenance
from rad.control.replay import Replay
from rad.tools import ToolCtx, run_tool
from tests.test_control_plane import ScriptedSession, _ctl, _plan_llm, scripted, ws  # noqa: F401


# ---------------------------------------------------------------- parallel execution

class SlowScripted(ScriptedSession):
    """Scripted by task text (not order) so concurrent tasks pick the right step."""
    by_text = {}
    active = 0
    peak = 0
    lock = threading.Lock()

    def think(self, prompt):
        text = prompt.split("CURRENT TASK: ")[1].splitlines()[0]
        with SlowScripted.lock:
            SlowScripted.active += 1
            SlowScripted.peak = max(SlowScripted.peak, SlowScripted.active)
        try:
            time.sleep(0.15)
            actions, reply = SlowScripted.by_text[text]
            for tool, args in actions:
                self.tool_runner(tool, args, self.ctx)
            return reply
        finally:
            with SlowScripted.lock:
                SlowScripted.active -= 1


def _fanout_plan():
    return {"tasks": [
        {"id": "a", "text": "A", "depends_on": [], "checks": [{"kind": "file_exists", "args": {"path": "a"}}]},
        {"id": "b", "text": "B", "depends_on": [], "checks": [{"kind": "file_exists", "args": {"path": "b"}}]},
        {"id": "c", "text": "C", "depends_on": [], "checks": [{"kind": "file_exists", "args": {"path": "c"}}]},
        {"id": "d", "text": "D", "depends_on": ["a", "b", "c"],
         "checks": [{"kind": "shell_ok", "args": {"command": "test -f a && test -f b && test -f c && test -f d"}}]},
    ]}


def test_parallel_ready_tasks_run_concurrently(home, ws):
    SlowScripted.by_text = {t: ([("write_file", {"path": t.lower(), "content": t})], "DONE") for t in "ABCD"}
    SlowScripted.peak = 0
    home.update(objective_parallel=3)
    ctl = Controller(home, session_factory=SlowScripted, llm=_plan_llm(_fanout_plan()), quiet=True)
    t0 = time.time()
    obj = ctl.run(ctl.create("fanout", auto=True))
    dt = time.time() - t0
    assert obj.status == ObjectiveStatus.COMPLETED
    assert SlowScripted.peak == 3
    # Two waves (A,B,C then D) ≈ 0.30s of sleep; sequential would be ≥ 0.60s of
    # sleep plus controller/policy/IO. Slack is for CI scheduling — peak==3 is
    # the concurrency proof.
    assert dt < 0.15 * 4 + 0.35
    assert obj.usage.tool_calls == 4 and obj.usage.model_calls == 4
    par = [e for e in EventLog(ctl.store.events_path(obj.id)).read(kind=E.TASK_STATUS) if e.data.get("status") == "parallel"]
    assert par and len(par[0].data["tasks"]) == 3


def test_parallel_disabled_without_auto(home, ws):
    SlowScripted.by_text = {t: ([("write_file", {"path": t.lower(), "content": t})], "DONE") for t in "ABCD"}
    SlowScripted.peak = 0
    home.update(objective_parallel=3)
    ctl = Controller(home, session_factory=SlowScripted, llm=_plan_llm(_fanout_plan()), quiet=True)
    obj = ctl.run(ctl.create("fanout", auto=False))
    assert obj.status == ObjectiveStatus.COMPLETED
    assert SlowScripted.peak == 1


def test_parallel_budget_is_shared_and_consistent(home, ws):
    SlowScripted.by_text = {t: ([("list_dir", {})] * 3, "DONE") for t in "ABCD"}
    home.update(objective_parallel=3)
    ctl = Controller(home, session_factory=SlowScripted, llm=_plan_llm(_fanout_plan()), quiet=True)
    obj = ctl.run(ctl.create("fanout", auto=True, budget=Budget(tool_calls=5)))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    assert obj.usage.tool_calls == 5        # never over-counted under concurrency
    seqs = [e.seq for e in EventLog(ctl.store.events_path(obj.id)).all()]
    assert seqs == sorted(seqs) and len(seqs) == len(set(seqs))   # log stayed ordered/unique


# ---------------------------------------------------------------- transcript + replay

def test_transcript_records_exact_prompt_and_reply(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "make x", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "x"}}]}]}
    scripted.script = [([], "DONE: (lie)"), ([("write_file", {"path": "x", "content": "1"})], "DONE: real")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("x"))
    tl = Replay(ctl.store, obj.id, ws).timeline()
    assert len(tl) == 2
    assert tl[0]["prompt"] == scripted.prompts[0] and tl[0]["reply"] == "DONE: (lie)"
    assert tl[0]["verification"]["status"] == "FAILED" and tl[0]["recovery"]["strategy"] == "retry_with_hint"
    assert tl[1]["tools"][0]["tool"] == "write_file" and tl[1]["tools"][0]["status"] == "success"
    assert tl[1]["verification"]["status"] == "VERIFIED"


def test_reverify_detects_drift(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "make x", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "x"}}]}],
            "objective_checks": [{"kind": "file_exists", "args": {"path": "x"}}]}
    scripted.script = [([("write_file", {"path": "x", "content": "1"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("x"))
    rp = Replay(ctl.store, obj.id, ws)
    assert rp.reverify()["drift"] == [] and rp.reverify()["objective_now"] == "VERIFIED"
    (ws / "x").unlink()
    rep = rp.reverify()
    assert rep["drift"] == [list(ctl.load_graph(obj).tasks)[0]]
    assert rep["objective_now"] == "FAILED"
    assert EventLog(ctl.store.events_path(obj.id)).count(E.REPLAY) == 3


# ---------------------------------------------------------------- provenance

def test_artifact_provenance_chain(home, ws, scripted):
    (ws / "src.txt").write_text("the port is 8080")
    plan = {"tasks": [{"id": "t1", "text": "derive", "depends_on": [],
                       "checks": [{"kind": "file_exists", "args": {"path": "out.txt"}}]}]}
    scripted.script = [([("read_file", {"path": "src.txt"}),
                         ("write_file", {"path": "out.txt", "content": "port=8080"})], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("derive"))
    pv = Provenance(ctl.store.dir(obj.id))
    chain = pv.artifact("out.txt")
    assert chain["artifact"]["creator"] == "write_file"
    assert chain["action"]["tool"] == "write_file"
    assert chain["task"]["text"] == "derive"
    assert chain["evidence"][0]["source"] == "file:src.txt" and chain["evidence"][0]["trusted"]
    assert chain["verification"]["ok"]


def test_why_claim_finds_support_and_flags_untrusted(home, ws, scripted, monkeypatch):
    import rad.tools as T
    monkeypatch.setattr(T, "fetch_public_page", lambda url, **k: ("Bengaluru elevation is about 920 metres.", ""))
    plan = {"tasks": [{"id": "t1", "text": "research", "depends_on": [], "checks": []}]}
    scripted.script = [([("fetch_page", {"url": "https://example.org/blr"})], "DONE: Bengaluru is at 920 m")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("research"))
    pv = Provenance(ctl.store.dir(obj.id))
    res = pv.why("Bengaluru elevation 920 metres")
    assert res["verdict"] == "supported"
    assert res["support"][0]["trusted"] is False and "example.org" in res["support"][0]["source"]
    assert pv.why("population of Tokyo")["verdict"] == "unsupported"


# ---------------------------------------------------------------- budgets across resumes

def test_time_budget_accumulates_across_resume(home, ws, scripted):
    plan = {"tasks": [{"id": "t1", "text": "a", "depends_on": [], "checks": []},
                      {"id": "t2", "text": "b", "depends_on": ["t1"], "checks": []}]}
    scripted.script = [([], "DONE")]
    ctl = _ctl(home, scripted, plan)
    obj = ctl.run(ctl.create("ab"), max_tasks=1)
    obj.usage.seconds = 1000            # pretend the first run took long
    obj.budget.seconds = 1001
    ctl.store.save(obj)
    scripted.script = [([], "DONE")]
    obj2 = _ctl(home, scripted, plan).resume(obj.id)
    assert obj2.usage.seconds >= 1000   # not reset by resume


# ---------------------------------------------------------------- long-horizon

def test_long_horizon_objective_with_mixed_failures(home, ws):
    """12 tasks, fan-out/fan-in, one liar, one tool error, one env failure needing repair,
    one NEEDS_USER that is then resumed. Must end COMPLETED + VERIFIED with a coherent trail."""
    tasks = []
    for i in range(1, 6):                       # 5 parallel researchers
        tasks.append({"id": f"r{i}", "text": f"research {i}", "depends_on": [],
                      "checks": [{"kind": "file_exists", "args": {"path": f"r{i}.txt"}}]})
    tasks.append({"id": "merge", "text": "merge research", "depends_on": [f"r{i}" for i in range(1, 6)],
                  "checks": [{"kind": "shell_output", "args": {"command": "cat merged.txt", "contains": "r5"}}]})
    tasks.append({"id": "build", "text": "build report tool", "depends_on": ["merge"],
                  "checks": [{"kind": "file_min_bytes", "args": {"path": "report.md", "n": 5}}]})
    tasks.append({"id": "review", "text": "review report", "depends_on": ["build"], "checks": []})
    tasks.append({"id": "ask", "text": "confirm publish target", "depends_on": ["review"], "checks": []})
    tasks.append({"id": "publish", "text": "publish", "depends_on": ["ask"],
                  "checks": [{"kind": "file_exists", "args": {"path": "published.flag"}}]})
    plan = {"tasks": tasks,
            "objective_checks": [{"kind": "shell_ok", "args": {"command": "test -s report.md && test -f published.flag"}}]}

    state = {"r3_lied": False, "build_failed": False, "asked": False}

    def by_text(text, prompt):
        if text.startswith("research"):
            n = text.split()[-1]
            if n == "3" and not state["r3_lied"]:
                state["r3_lied"] = True
                return [], "DONE: research 3 saved"                                   # liar
            if n == "4" and "FEEDBACK" not in prompt:
                return [("read_file", {"path": "nope.txt"})], "DONE: r4"                # tool error, no file
            return [("write_file", {"path": f"r{n}.txt", "content": f"r{n}"})], "DONE"
        if text == "merge research":
            return [("run_shell", {"command": "cat r1.txt r2.txt r3.txt r4.txt r5.txt > merged.txt"})], "DONE"
        if text == "build report tool":
            if not state["build_failed"]:
                state["build_failed"] = True
                return [("run_shell", {"command": "mkreport_xyz merged.txt > report.md"})], "DONE"  # env failure
            return [("run_shell", {"command": "sh mk.sh"})], "DONE"
        if text.startswith("Repair prerequisite"):
            return [("write_file", {"path": "mk.sh", "content": "cp merged.txt report.md"})], "DONE"
        if text == "review report":
            return [("read_file", {"path": "report.md"})], "DONE: looks good"
        if text == "confirm publish target":
            if not state["asked"]:
                state["asked"] = True
                return [], "NEEDS_USER: publish to staging or prod?"
            return [], "DONE: staging"
        if text == "publish":
            return [("write_file", {"path": "published.flag", "content": "staging"})], "DONE"
        raise AssertionError(text)

    class LH(ScriptedSession):
        def think(self, prompt):
            text = prompt.split("CURRENT TASK: ")[1].splitlines()[0]
            actions, reply = by_text(text, prompt)
            for tool, args in actions:
                self.tool_runner(tool, args, self.ctx)
            return reply

    home.update(objective_parallel=3, accept_unverified_done=True)  # v3 VERIFIED-only would block review task without checks
    ctl = Controller(home, session_factory=LH, llm=_plan_llm(plan), quiet=True)
    obj = ctl.run(ctl.create("long horizon", auto=True))
    assert obj.status == ObjectiveStatus.NEEDS_USER
    g = ctl.load_graph(obj)
    st = {t.text: t.status for t in g.tasks.values()}
    assert st["confirm publish target"] == TaskStatus.NEEDS_USER and st["publish"] == TaskStatus.BLOCKED
    assert sum(1 for s in st.values() if s == TaskStatus.COMPLETED) == 9   # 5 research + merge + repair + build + review

    obj = Controller(home, session_factory=LH, llm=_plan_llm(plan), quiet=True).resume(obj.id)
    assert obj.status == ObjectiveStatus.COMPLETED
    assert obj.verification["objective"]["status"] == "VERIFIED"
    g = ctl.load_graph(obj)
    assert all(t.status == TaskStatus.COMPLETED for t in g.tasks.values())
    assert len(g.tasks) == 11                                     # 10 planned + 1 repair
    r3 = [t for t in g.tasks.values() if t.text == "research 3"][0]
    assert r3.attempts == 2 and r3.verification["status"] == "VERIFIED"
    log = EventLog(ctl.store.events_path(obj.id))
    classes = sorted({e.data["failure_class"] for e in log.read(kind=E.RECOVERY_DECISION)})
    assert classes == ["ENVIRONMENT_FAILURE", "TOOL_FAILURE", "VALIDATION_FAILURE"]
    assert (ws / "report.md").read_text() == "r1r2r3r4r5"
    assert obj.usage.retries == 3
    tl = Replay(ctl.store, obj.id, ws).timeline()
    assert len(tl) == 15                                          # 11 tasks + 3 retries + 1 re-ask after resume
    assert Replay(ctl.store, obj.id, ws).reverify()["drift"] == []
