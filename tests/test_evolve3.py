"""Layer 5–6 tests: multi-agent team, world model, plan executor."""
import pytest

from rad.home import RadHome
from rad.team import Team, DEFAULT_ROLES
from rad.world import WorldModel
from rad.plan import Plan
from rad.planrun import PlanRunner


# ---------------------------------------------------------------- team

def test_team_solo_synthesizes(tmp_path, monkeypatch):
    home = RadHome(tmp_path)
    monkeypatch.setattr(Team, "caller_for",
                        lambda self, role, extra="": (lambda u: f"ANS-{role}"))
    res = Team(home).run("pick a db", roles=["coder", "reviewer"], mode="solo")
    assert [a["role"] for a in res["answers"]] == ["coder", "reviewer"]
    assert res["final"] == "ANS-writer"          # synthesis always uses the writer role
    assert res["mode"] == "solo"


def test_team_debate_appends_critique(tmp_path, monkeypatch):
    home = RadHome(tmp_path)
    monkeypatch.setattr(Team, "caller_for",
                        lambda self, role, extra="": (lambda u: f"ANS-{role}"))
    res = Team(home).run("pick a db", roles=["coder"], mode="debate")
    assert res["answers"][-1]["role"] == "debate"
    assert res["answers"][-1]["answer"] == "ANS-reviewer"  # critique uses the reviewer


def test_team_default_roles_and_n(tmp_path, monkeypatch):
    home = RadHome(tmp_path)
    seen = []
    monkeypatch.setattr(Team, "caller_for",
                        lambda self, role, extra="": (lambda u: seen.append(role) or role))
    res = Team(home).run("x")
    assert res["roles"] == ["coder", "reviewer", "planner"]
    res2 = Team(home).run("x", n=2)
    assert res2["roles"] == ["coder", "reviewer"]
    # run 2 spawned coder+reviewer, then synthesis called the writer
    assert seen[-3:] == ["coder", "reviewer", "writer"]
    assert all(r in DEFAULT_ROLES or r == "writer" for r in seen)


def test_team_run_saved_to_history(tmp_path, monkeypatch):
    home = RadHome(tmp_path)
    monkeypatch.setattr(Team, "caller_for", lambda self, role, extra="": (lambda u: role))
    Team(home).run("a problem")
    hist = "\n".join(Team(home).history())
    assert "solo" in hist and "a problem" in hist


# ---------------------------------------------------------------- world model

def test_world_heuristic_learn(tmp_path):
    home = RadHome(tmp_path)
    w = WorldModel(home)
    n = w.learn("Bengaluru is my city. I use Postgres.")
    d = w.data()
    assert n >= 1
    assert "bengaluru" in d["entities"]
    rels = {(r["rel"], r["to"]) for r in d["relations"]}
    assert ("uses", "postgres") in rels
    assert ("is", "my city") in rels


def test_world_brain_json_learn(tmp_path):
    home = RadHome(tmp_path)
    w = WorldModel(home)
    fake = '{"entities": [{"name": "Nimbus-Server", "kind": "server"}], ' \
           '"relations": [{"from": "Rad", "rel": "deploys_to", "to": "Nimbus-Server"}]}'
    n = w.learn("anything", source="chat", caller=lambda p: fake)
    d = w.data()
    assert n == 2
    assert d["entities"]["nimbus-server"]["kind"] == "server"
    assert d["relations"][0]["rel"] == "deploys_to"


def test_world_query_and_context(tmp_path):
    home = RadHome(tmp_path)
    w = WorldModel(home)
    w.learn("Bengaluru is my city. I use Postgres.")
    hits = w.query("bengaluru")
    assert any(h["type"] == "entity" and h["name"] == "Bengaluru" for h in hits)
    block = w.context_block("what do you know about Bengaluru")
    assert "Bengaluru" in block
    assert w.context_block("hello there friend") == ""   # no relevant facts → no injection


def test_world_add_and_show(tmp_path):
    home = RadHome(tmp_path)
    w = WorldModel(home)
    w.add("My server is called Nimbus-Server", caller=None)
    s = w.show()
    assert "store: builtin" in s
    assert "Nimbus" in s
    assert w.query("nimbus")


# ---------------------------------------------------------------- plan executor

class FakeSession:
    script = ["DONE: ok"]

    def __init__(self, home, auto=False, **kw):
        self.auto = auto

    def think(self, prompt):
        return self.script.pop(0) if self.script else "DONE: ok"

    def close(self):
        pass


def _plan_home(tmp_path, steps):
    home = RadHome(tmp_path)
    p = Plan(home)
    p.save({"goal": "test goal", "created": 0,
            "steps": [{"text": s, "done": False, "note": ""} for s in steps]})
    return home


def test_plan_runner_executes_until_done(tmp_path, monkeypatch):
    home = _plan_home(tmp_path, ["build api", "write tests"])

    class S(FakeSession):
        script = ["DONE: api ready", "DONE: tests green"]
    monkeypatch.setattr("rad.planrun.Session", S)
    rep = PlanRunner(home, auto=True).run()
    assert rep["ran"] == 2 and rep["done"] == 2 and rep["blocked"] is None
    plan = Plan(home).load()
    assert plan["steps"][0]["done"] and plan["steps"][0]["note"] == "api ready"


def test_plan_runner_stops_on_blocked(tmp_path, monkeypatch):
    home = _plan_home(tmp_path, ["build api", "deploy to prod"])

    class S(FakeSession):
        script = ["DONE: api ready", "BLOCKED: needs deploy credentials"]
    monkeypatch.setattr("rad.planrun.Session", S)
    rep = PlanRunner(home, auto=True).run()
    assert rep["blocked"] == "needs deploy credentials"
    assert rep["ran"] == 2 and rep["done"] == 1
    plan = Plan(home).load()
    assert plan["steps"][1].get("blocked") is True and not plan["steps"][1]["done"]


def test_plan_runner_no_marker_is_unverified_by_default(tmp_path, monkeypatch):
    """A reply with no DONE:/BLOCKED: marker must NOT be counted as completion."""
    home = _plan_home(tmp_path, ["only step", "next step"])

    class S(FakeSession):
        script = ["I created the file and verified it works.", "DONE: never reached"]
    monkeypatch.setattr("rad.planrun.Session", S)
    rep = PlanRunner(home, auto=True).run()
    assert rep["done"] == 0
    assert rep["ran"] == 1                      # execution halts at the unverified step
    assert rep["report"][0]["state"] == "unverified"
    step = Plan(home).load()["steps"][0]
    assert not step["done"] and step.get("blocked")


def test_plan_runner_infers_done_when_opted_in(tmp_path, monkeypatch):
    home = _plan_home(tmp_path, ["only step"])
    home.update(plan_infer_done=True)

    class S(FakeSession):
        script = ["I created the file and verified it works."]
    monkeypatch.setattr("rad.planrun.Session", S)
    rep = PlanRunner(home, auto=True).run()
    assert rep["done"] == 1
    assert Plan(home).load()["steps"][0]["done"]


def test_plan_runner_max_steps(tmp_path, monkeypatch):
    home = _plan_home(tmp_path, ["a", "b", "c"])

    class S(FakeSession):
        script = ["DONE: x"] * 5
    monkeypatch.setattr("rad.planrun.Session", S)
    rep = PlanRunner(home, auto=True).run(max_steps=2)
    assert rep["ran"] == 2


# ---------------------------------------------------------------- spawn_agents tool

def test_spawn_agents_tool(tmp_path, monkeypatch):
    from rad.tools import ToolCtx, run_tool
    home = RadHome(tmp_path)
    monkeypatch.setattr(Team, "run", lambda self, problem, roles=None, mode="solo", n=0, **kw: {
        "problem": problem, "mode": mode, "roles": roles or [],
        "answers": [{"role": "coder", "answer": "code says X"}],
        "final": "final says Y", "at": 0})
    ctx = ToolCtx(home=home, router=None, auto=True, confirm=lambda q: True,
                  mcp_call=lambda *a: "")
    out = run_tool("spawn_agents", {"problem": "design a queue"}, ctx)
    assert "final says Y" in out and "code says X" in out
    assert run_tool("spawn_agents", {"problem": ""}, ctx) == "empty problem"
