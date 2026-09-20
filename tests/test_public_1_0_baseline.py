"""v1.0.0 G5-1 — public / product-grade 1.0 baseline (RW-100 / RW-101).

Investigate-first (ROADMAP G5-1 / Cycle 37 findings):
- Install is git clone + ``pip install -e .``; Version 5 GitHub Release
  has no installable assets.
- QUICKSTART still said ``rad version`` prints **0.4.1** while the packed
  line was 0.5.5.
- 0.5.x honesty gates were not locked as a public 1.0 bar.

G5-1: package **1.0.0**; PyPI-ready metadata; documented public install
from Version 1 GitHub Release wheel/sdist (Sanath packs after merge —
no release/tag in this change); first-run docs match ``rad version``
**1.0.0**; honesty bar locked (false DONE 0, Needle OFF, caps 16/60,
F-17 / F-26 closed, Class C is not a product patch, remaining-quota
not invented). No live PASS claim. Caps unchanged. Needle OFF.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rad import __version__
from rad.cli import main
from rad.control.objectives import (
    REMAINING_QUOTA_NOTE,
    USAGE_ROLLUP_FIELDS,
    Budget,
    Objective,
)
from rad.control.planner import Planner
from rad.home import DEFAULTS
from rad.toolrouter import resolve_tool_router
from tests.test_f17_fallback_investigation import SEVEN_SENTENCE_GOAL


ROOT = Path(__file__).resolve().parent.parent
QUICKSTART = ROOT / "docs" / "QUICKSTART.md"
INSTALLATION = ROOT / "docs" / "INSTALLATION.md"
ROADMAP = ROOT / "docs" / "ROADMAP.md"
README = ROOT / "README.md"
PYPROJECT = ROOT / "pyproject.toml"


# ---------------------------------------------------------------- architecture freeze

def test_g51_does_not_raise_caps_or_enable_needle(home):
    assert __version__ == "1.0.1"
    assert Budget().tool_calls == 60
    assert int(home.cfg.get("max_plan_tasks", 16) or 16) == 16
    assert Planner(None, str(home.workspace())).max_tasks == 16
    assert "max_plan_tasks" not in DEFAULTS or DEFAULTS.get("max_plan_tasks") in (None, 16)
    assert resolve_tool_router(home) == "existing"


def test_g51_does_not_invent_remaining_quota_or_class_a_for_403():
    assert USAGE_ROLLUP_FIELDS == ("tool_calls", "model_calls", "money_usd", "tokens")
    assert "remaining-quota" not in REMAINING_QUOTA_NOTE
    assert "not in the API until HTTP 429" in REMAINING_QUOTA_NOTE
    pyproject = PYPROJECT.read_text(encoding="utf-8")
    assert 'version = "1.0.1"' in pyproject
    assert "pack = [" in pyproject
    assert "Homepage = " in pyproject
    assert "Development Status :: 5 - Production/Stable" in pyproject


# ---------------------------------------------------------------- RW-100 public install + docs honesty

def test_rw100_first_run_docs_match_package_1_0_0(capsys):
    """RW-100: QUICKSTART / INSTALLATION advertise Version 1 pack; CLI matches this tree."""
    assert __version__ == "1.0.1"
    qs = QUICKSTART.read_text(encoding="utf-8")
    inst = INSTALLATION.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    assert "prints 1.0.1" in qs
    assert "prints 1.0.0" in qs  # packed Version 1 wheel still v1.0.0
    assert "prints 0.4.1" not in qs
    assert "prints 0.4.1" not in inst
    # README banner tracks the packaged version (stale v1.0.0 banner fixed in 0.2 desktop work)
    assert "v1.0.1 — open door" in readme
    assert "rad_agent-1.0.0-py3-none-any.whl" in qs
    assert "rad_agent-1.0.0-py3-none-any.whl" in inst
    assert "Version 1 packing (Sanath)" in inst
    assert "Do not** cut the GitHub Release" in inst or "Do **not** cut the GitHub Release" in inst
    assert "claimed PASS" in inst
    assert main(["version"]) == 0
    assert "v1.0.1" in capsys.readouterr().out


def test_rw100_wheel_and_sdist_build_without_credentials(tmp_path):
    """RW-100: PEP 517 wheel + sdist exist for Version 1 assets. No token."""
    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "build", "-q"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stdout + install.stderr
    dist = tmp_path / "dist"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--sdist",
            "--outdir",
            str(dist),
            str(ROOT),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    names = sorted(p.name for p in dist.iterdir())
    wheels = list(dist.glob("rad_agent-1.0.1-*.whl"))
    sdists = list(dist.glob("rad_agent-1.0.1.tar.gz")) + list(
        dist.glob("rad-agent-1.0.1.tar.gz")
    )
    assert wheels, names
    assert sdists, names


# ---------------------------------------------------------------- RW-101 1.0 honesty bar

def test_rw101_honesty_bar_locked_in_roadmap_and_gates():
    """RW-101: public 1.0 bar is false DONE 0, Needle OFF, caps 16/60, Class C."""
    text = ROADMAP.read_text(encoding="utf-8")
    assert "## Generation 5 — 1.0" in text
    assert "ACCEPTED + IMPLEMENTED" in text
    assert "**v1.0.0**" in text
    assert "**v1.0.1**" in text
    assert "false DONE **0**" in text
    assert "Needle **OFF**" in text
    assert "caps **16/60**" in text or "`max_plan_tasks` **16**" in text
    assert "F-17 / F-26 stay closed" in text or "F-17 / F-26 closed" in text
    assert "Class C is not a product patch" in text
    assert "No GitHub Release" in text or "**no GitHub Release**" in text.lower() or (
        "No GitHub Release / tag in this PR" in text
        or "no GitHub Release / tag in this change" in text
        or "**No GitHub Release / tag**" in text
    )
    readme = README.read_text(encoding="utf-8")
    assert "false DONE **0**" in readme
    assert "Needle **OFF**" in readme
    assert "caps **16/60**" in readme
    assert "not** claimed PASS" in readme or "not claimed PASS" in readme


def test_rw101_f17_fallback_tasks_stay_checkless():
    """RW-101: F-17 stays closed — fallback tasks remain goal-only / check-less."""
    g = Planner(None, "/tmp/ws")._fallback(Objective.new(SEVEN_SENTENCE_GOAL))
    assert len(g.tasks) == 7
    assert all(not t.checks for t in g.tasks.values())
