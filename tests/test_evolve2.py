import time

from rad.battery import Benchmark, _tasks, build_caller
from rad.brains import Brains
from rad.corpus import Corpus
from rad.home import RadHome


def _fake_home(tmp_path, monkeypatch):
    monkeypatch.setenv("RAD_HOME", str(tmp_path / "rh"))
    return RadHome(str(tmp_path / "rh"))


# ---------------------------------------------------------------- battery

def test_task_bank_complete(home):
    cats = {t["category"] for t in _tasks()}
    assert cats == {"math", "logic", "code", "tool", "json", "summarize", "style"}
    assert len(_tasks()) >= 15


def test_graders(home):
    tasks = {t["id"]: t for t in _tasks()}
    assert tasks["m1"]["check"]("The answer is 391.")[0] == 1.0
    assert tasks["m1"]["check"]("I think 390?")[0] == 0.0
    assert tasks["j1"]["check"]('{"name":"rad","age":1}')[0] == 1.0
    assert tasks["j1"]["check"]("hello")[0] == 0.0
    assert tasks["t1"]["check"]('TOOL: {"name": "get_weather", "args": {"city": "Tokyo"}}')[0] == 1.0
    assert tasks["t1"]["check"]("It is sunny in Tokyo.")[0] == 0.0
    assert tasks["y1"]["check"]("I am Rad your agent")[0] == 1.0
    assert tasks["y1"]["check"]("I am Rad your agent friend")[0] == 0.0


def test_benchmark_run_and_history(home):
    bench = Benchmark(home)

    def caller(system, user):
        # a deliberately weak but parseable brain
        if "17" in user and "23" in user:
            return "391"
        return "42"

    rep = bench.run(caller, label="weak-test", provider="fake", model="fake-1")
    assert 0 <= rep["score"] <= 100
    assert rep["categories"]["math"] > 0
    hist = bench.history()
    assert len(hist) == 1 and hist[0]["label"] == "weak-test"
    assert "weak-test" in bench.compare()


def test_benchmark_error_handling(home):
    bench = Benchmark(home)

    def caller(system, user):
        raise RuntimeError("boom")

    rep = bench.run(caller, label="broken", provider="fake", model="x")
    assert rep["score"] == 0.0


# ---------------------------------------------------------------- brains

def test_brain_add_current_and_rollback(home):
    b = Brains(home)
    b.add("a", "groq", model="m-a")
    assert b.current()["name"] == "a"
    b.add("b", "cerebras", model="m-b")
    d = b.data()
    d["current"] = "b"
    d["candidates"]["b"]["parent"] = "a"
    b.save(d)
    prev = b.rollback()
    assert prev == "a"


class _FakeBench:
    def __init__(self, scores):
        self.scores = scores
        self.calls = []

    def run(self, caller, label, provider="?", model="?", categories=None):
        self.calls.append(label)
        return {"score": self.scores[label], "label": label, "categories": {}}


def test_promotion_requires_winning(home, monkeypatch):
    # brains.promote does `from rad.battery import build_caller` at call time
    import rad.battery as battery_mod
    monkeypatch.setattr(battery_mod, "build_caller", lambda home, **kw: (lambda s, u: "42"))
    b = Brains(home)
    b.add("cur", "cerebras", model="x")
    b.add("challenger", "groq", model="y")
    bench = _FakeBench({"challenger": 80.0, "cur": 90.0})
    res = b.promote("challenger", bench)
    assert res["promoted"] is False
    assert b.current()["name"] == "cur"
    bench2 = _FakeBench({"challenger": 95.0, "cur": 90.0})
    res2 = b.promote("challenger", bench2)
    assert res2["promoted"] is True
    assert b.current()["name"] == "challenger"
    # chat config pinned to winner
    assert home.cfg["force_provider"] == "groq"
    assert home.cfg["model"] == "y"


# ---------------------------------------------------------------- corpus

def test_corpus_mining(home):
    from rad.dna import Evolver
    m = home.memory_dir / "short" / (time.strftime("%Y-%m-%d") + ".md")
    now_hms = time.strftime("%H:%M:%S")
    m.write_text(
        f"[{now_hms}] user: what is the capital of France?\n"
        f"[{now_hms}] rad: The capital of France is Paris, which has been the political center since the medieval era.\n"
    )
    c = Corpus(home)
    pairs = c.mine()
    assert len(pairs) == 1
    assert pairs[0]["quality"] == "normal"
    assert pairs[0]["input"] == "what is the capital of France?"

    # praised pair via DNA feedback
    Evolver(home).add_feedback("good", "nice")
    pairs = Corpus(home).mine()
    assert pairs[0]["quality"] == "praised"


def test_corpus_export(home):
    m = home.memory_dir / "short" / (time.strftime("%Y-%m-%d") + ".md")
    now_hms = time.strftime("%H:%M:%S")
    m.write_text(
        f"[{now_hms}] user: build me a flag\n"
        f"[{now_hms}] rad: I created flags.py with a Flag class, tested it with pytest, and the suite passed with 3 tests.\n"
    )
    c = Corpus(home)
    dest = c.export(str(home.root / "corpus" / "test.jsonl"))
    import json
    lines = [json.loads(l) for l in open(dest)]
    assert len(lines) == 1 and lines[0]["quality"] == "normal"
    assert "flags.py" in lines[0]["output"]


def test_corpus_short_ack_skipped(home):
    m = home.memory_dir / "short" / (time.strftime("%Y-%m-%d") + ".md")
    now_hms = time.strftime("%H:%M:%S")
    m.write_text(
        f"[{now_hms}] user: ok\n"
        f"[{now_hms}] rad: ok\n"
    )
    assert Corpus(home).mine() == []


# ---------------------------------------------------------------- train / plan

def test_train_plan_route_b(home):
    from rad import train
    out = train.plan(home)
    assert "Route B" in out
    assert "rad-train.jsonl" in out
    assert (home.root / "corpus" / "rad-train.jsonl").exists()


def test_train_detect(home):
    from rad import train
    backends = train.detect_backends()
    assert isinstance(backends, dict)


def test_plan_fallback_and_toggle(home):
    from rad.plan import Plan
    p = Plan(home)
    plan = p.create("Set up the project and then write tests and then deploy it")
    assert len(plan["steps"]) >= 2
    p.toggle(0, done=True, note="verified")
    st = p.status()
    assert "[x]" in st and "verified" in st
    p.clear()
    assert p.load() is None
