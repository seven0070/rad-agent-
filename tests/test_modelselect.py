"""Task-aware model selection — free-first is law, requirements only reorder within a tier."""
from dataclasses import dataclass

import pytest

from rad.modelselect import (CAP_CODING, CAP_LONG, CAP_PRIVATE, CAP_VISION, ModelProfile,
                             ModelRegistry, Requirements, TASK_KINDS)


@dataclass
class FakeSpec:
    name: str
    tier: str = "free"
    local: bool = False
    supports_vision: bool = False
    default_model: str = "m"


@dataclass
class FakeEntry:
    spec: FakeSpec
    model: str = "m"


def entries(*specs):
    return [FakeEntry(s) for s in specs]


def test_requirement_classification_from_task_text():
    assert Requirements.for_task_text("implement a python function to sort users").kind == "code"
    assert Requirements.for_task_text("research the history of the printing press").kind == "research"
    assert Requirements.for_task_text("plan the migration and break down the steps").kind == "plan"
    assert Requirements.for_task_text("summarize this article in 20 words").kind == "summarize"
    assert Requirements.for_task_text("what is the capital of Peru?").kind == "chat"
    r = Requirements.for_task_text("read the file and write a report")
    assert r.need_tools is True


def test_free_first_is_preserved(home):
    reg = ModelRegistry(home)
    e = entries(FakeSpec("paidbrain", "paid"), FakeSpec("freebrain", "free"), FakeSpec("localbrain", "local", local=True))
    order = [x.spec.name for x in reg.select(e, Requirements(kind="code"))]
    assert order[0] == "localbrain" and order[1] == "freebrain" and order[2] == "paidbrain"


def test_vision_requirement_filters_non_vision_models(home):
    reg = ModelRegistry(home)
    e = entries(FakeSpec("textonly", "free", supports_vision=False),
                FakeSpec("seer", "paid", supports_vision=True))
    order = [x.spec.name for x in reg.select(e, Requirements(kind="vision", need_vision=True))]
    assert order == ["seer"]


def test_privacy_local_only(home):
    reg = ModelRegistry(home)
    e = entries(FakeSpec("cloudy", "free"), FakeSpec("offline", "local", local=True))
    order = [x.spec.name for x in reg.select(e, Requirements(kind="chat", privacy="local"))]
    assert order == ["offline"]


def test_avoid_and_allow_paid_filters(home):
    reg = ModelRegistry(home)
    e = entries(FakeSpec("a", "free"), FakeSpec("b", "free"), FakeSpec("expensive", "paid"))
    order = [x.spec.name for x in reg.select(e, Requirements(kind="chat", avoid=["a"]))]
    assert "a" not in order
    order2 = [x.spec.name for x in reg.select(e, Requirements(kind="chat", allow_paid=False))]
    assert "expensive" not in order2


def test_measured_scores_influence_ranking_within_tier(home):
    reg = ModelRegistry(home)
    e = entries(FakeSpec("weak", "free"), FakeSpec("strong", "free"))
    reg.set("strong", scores={"coding": 0.95, "reasoning": 0.9})
    reg.set("weak", scores={"coding": 0.2})
    order = [x.spec.name for x in reg.select(e, Requirements(kind="code"))]
    assert order[0] == "strong"


def test_long_context_requirement_drops_small_context_models(home):
    reg = ModelRegistry(home)
    reg.set("tiny", context=8000)
    reg.set("big", context=200_000)
    e = entries(FakeSpec("tiny", "free"), FakeSpec("big", "free"))
    order = [x.spec.name for x in reg.select(e, Requirements(kind="research", min_context=100_000))]
    assert order == ["big"]


def test_profiles_expose_capabilities(home):
    p = ModelProfile(provider="x", tier="local", context=64_000, vision=True, latency_s=1.0)
    caps = p.caps()
    assert CAP_PRIVATE in caps and CAP_LONG in caps and CAP_VISION in caps
    ps = ModelProfile(provider="y", tier="paid", context=8000, vision=False, latency_s=9.0)
    assert ps.score_for([CAP_CODING]) >= 0.0
    assert ps.to_dict()["tier"] == "paid"


def test_registry_roundtrip_and_render(home):
    reg = ModelRegistry(home)
    reg.set("mine", tier="free", context=32_000, scores={"coding": 0.8})
    again = ModelRegistry(home).get("mine")
    assert again is not None and again.context == 32_000 and again.scores["coding"] == 0.8
    text = reg.render()
    assert "mine" in text
    e = entries(FakeSpec("mine", "free"))
    assert "requirements" in reg.render(e, Requirements(kind="code"))
