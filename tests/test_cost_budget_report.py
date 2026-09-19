"""v0.5.5 G4-6 — operational scale / cost/budget reporting (RW-098 / RW-099).

Investigate-first (ROADMAP G4-6 / Cycle 34 findings):
- ``rad cost`` / ``RouterState.cost_report`` is paid 14-day tokens only.
- Per-objective ``Usage`` (tool_calls / model_calls / money_usd / tokens)
  already persists on ``~/.rad/objectives/<id>/objective.json`` and is not
  rolled up. Scripted/offline runs already write those records.
- Free-tier remaining quota is not in the API until HTTP 429 (RW-086).
- G4-2 already persists last Class C + Retry-After — do not re-do.

G4-6 rolls persisted Usage into ``rad cost``. No remaining-quota field.
No Class A for 403/429. Caps 16/60 unchanged. Needle OFF. F-17 / F-26
stay closed. No live PASS claim. No GitHub Release / tag.
"""
from __future__ import annotations

from rad import __version__
from rad.cli import main
from rad.control.objectives import (
    REMAINING_QUOTA_NOTE,
    USAGE_ROLLUP_FIELDS,
    Budget,
    Objective,
    ObjectiveStore,
    Usage,
    UsageRollup,
    usage_rollup_report,
)
from rad.control.planner import Planner
from rad.health import last_class_c, record_class_c
from rad.home import DEFAULTS
from rad.router import RouterState
from rad.toolrouter import resolve_tool_router


# ---------------------------------------------------------------- architecture freeze

def test_g46_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_g46_does_not_invent_remaining_quota_or_reopen_g42():
    assert USAGE_ROLLUP_FIELDS == ("tool_calls", "model_calls", "money_usd", "tokens")
    assert "remaining" not in UsageRollup().to_dict()
    assert "quota" not in UsageRollup().to_dict()
    assert "remaining-quota" not in REMAINING_QUOTA_NOTE
    assert "not in the API until HTTP 429" in REMAINING_QUOTA_NOTE


# ---------------------------------------------------------------- RW-098 persisted Usage rolls up

def test_rw098_persisted_usage_rolls_up_across_objectives(home):
    """RW-098: two scripted/offline objective.json records sum to one rollup."""
    store = ObjectiveStore(home)
    a = Objective.new(
        "RW-086 shape $0 tools 12/12",
        status="failed",
        usage=Usage(tool_calls=12, model_calls=4, money_usd=0.0, tokens=800),
    )
    b = Objective.new(
        "scripted paid fallback",
        status="completed",
        usage=Usage(tool_calls=3, model_calls=2, money_usd=0.02, tokens=150),
    )
    store.save(a)
    store.save(b)

    loaded = store.list()
    assert {o.id for o in loaded} == {a.id, b.id}
    assert (store.dir(a.id) / "objective.json").is_file()

    rollup = store.usage_rollup()
    assert rollup.count == 2
    assert rollup.tool_calls == 15
    assert rollup.model_calls == 6
    assert abs(rollup.money_usd - 0.02) < 1e-9
    assert rollup.tokens == 950
    by_id = {row["id"]: row for row in rollup.rows}
    assert by_id[a.id]["tool_calls"] == 12
    assert by_id[b.id]["money_usd"] == 0.02
    data = rollup.to_dict()
    assert set(USAGE_ROLLUP_FIELDS).issubset(data)
    assert "remaining_quota" not in data
    assert "remaining" not in data
    assert "quota" not in data

    text = usage_rollup_report(rollup)
    assert a.id in text and b.id in text
    assert "tools 15" in text
    assert "model 6" in text
    assert "$0.0200" in text
    assert "tokens 950" in text
    assert REMAINING_QUOTA_NOTE in text
    assert "remaining  " not in text
    assert "quota left" not in text


def test_rw098_empty_store_is_honest_and_offline(home):
    rollup = ObjectiveStore(home).usage_rollup()
    assert rollup.count == 0
    assert rollup.tool_calls == 0
    text = usage_rollup_report(rollup)
    assert "no objective usage recorded" in text
    assert REMAINING_QUOTA_NOTE in text
    assert RouterState(home).cost_report() == "  no paid usage recorded (you're on free/local)"


# ---------------------------------------------------------------- RW-099 rad cost surfaces the rollup

def test_rw099_rad_cost_surfaces_rollup_without_live_provider(home, capsys):
    """RW-099: rad cost shows paid 14-day AND persisted Usage; no remaining-quota."""
    store = ObjectiveStore(home)
    o = Objective.new(
        "offline scripted objective",
        status="completed",
        usage=Usage(tool_calls=12, model_calls=3, money_usd=0.0, tokens=400),
    )
    store.save(o)
    record_class_c(
        home,
        "openrouter",
        kind="rate_limit",
        status=429,
        retry_after=3600,
        err="free-models-per-day",
    )
    before = last_class_c(home)

    rc = main(["--home", str(home.root), "cost"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "Paid spend" in out
    assert "no paid usage recorded" in out
    assert "Objective usage" in out
    assert "not remaining quota" in out
    assert o.id in out
    assert "tools    12" in out or "tools 12" in out
    assert "model     3" in out or "model 3" in out
    assert "$0.0000" in out
    assert "tokens    400" in out or "tokens 400" in out
    assert REMAINING_QUOTA_NOTE in out
    assert "remaining_quota" not in out
    assert "quota remaining" not in out.lower()
    after = last_class_c(home)
    assert after == before
    assert after["provider"] == "openrouter"
    assert after["status"] == 429
    assert after["kind"] == "rate_limit"
    assert after.get("retry_after_until") == before.get("retry_after_until")
