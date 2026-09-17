from rad.dna import Evolver


def test_factory_generation(home):
    ev = Evolver(home)
    dna = ev.load()
    assert dna["generation"] == 0
    assert dna["name"] == "Rad"


def test_system_prompt_contains_rules(home):
    ev = Evolver(home)
    sp = ev.system_prompt()
    assert "Rad" in sp
    assert "UNTRUSTED" in sp  # security rule baked in


def test_directed_evolve_deterministic(home):
    ev = Evolver(home)
    dna = ev.evolve("reply shorter and more casual", llm=None)
    assert dna["generation"] == 1
    style = dna["style"]
    assert any("short" in s for s in style)
    assert any("casual" in s for s in style)


def test_rollback(home):
    ev = Evolver(home)
    ev.evolve("be formal", llm=None)
    prev = ev.rollback()
    assert prev["generation"] == 0
    assert ev.load()["generation"] == 0


def test_reset(home):
    ev = Evolver(home)
    ev.evolve("x", llm=None)
    dna = ev.reset()
    assert dna["generation"] == 0
    assert ev.load()["generation"] == 0


def test_feedback_auto_tune(home):
    ev = Evolver(home)
    for _ in range(3):
        ev.add_feedback("bad", "too long")
    dna = ev.load()
    assert any("tighter" in s for s in dna["style"])
