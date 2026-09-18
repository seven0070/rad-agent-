"""The gate itself: 50 items, one honest verdict, evidence written to disk."""
import json

from rad.acceptance import AREAS, REQUIRED, Gate, render
from rad.home import RadHome


def test_item_list_is_complete_and_unique(home):
    items = Gate(RadHome(str(home.root))).items()
    assert len(items) == 50 and REQUIRED == 50
    assert [i.n for i in items] == list(range(1, 51))
    assert len({i.id for i in items}) == 50
    assert {i.area for i in items} == set(AREAS)
    assert all(i.check and i.requirement and i.title for i in items)


def test_area_subset_runs_and_writes_evidence(home):
    gate = Gate(RadHome(str(home.root)))
    rep = gate.run(areas=["docs"])
    assert rep["partial"] is True and rep["total"] == 3
    assert rep["ok"] and not rep["failed"]
    assert all(item["evidence"] for item in rep["items"])
    path = home.root / "acceptance"
    written = sorted(path.glob("*_gate.json"))
    assert written, "the gate must leave its evidence behind"
    data = json.loads(written[-1].read_text(encoding="utf-8"))
    assert data["total"] == 3 and "items" in data and data["items"][0]["reproduce"]
    text = render(rep)
    assert "docs" in text and "items pass" in text


def test_unknown_area_reports_nothing_rather_than_lying(home):
    rep = Gate(RadHome(str(home.root))).run(areas=["nonexistent"])
    assert rep["total"] == 0 and rep["ok"] is False


def test_gate_homes_never_use_the_process_cwd(home):
    """The gate runs on real machines: item homes must be self-contained, not the current directory.

    Regression: `RadHome.workspace()` falls back to the process CWD, so a gate item that ran a
    scenario without setting a workspace wrote its artifacts into the repository root.
    """
    from pathlib import Path

    gate = Gate(RadHome(str(home.root)))
    gate._current_item = "probe"
    ih = gate.item_home()
    ws = ih.workspace().resolve()
    assert ws.is_absolute() and ws.exists()
    assert ws.is_relative_to(Path(ih.root).resolve())
    assert ws != Path.cwd().resolve()
    # the tests' own home is isolated too
    assert Path(home.workspace()).resolve() != Path.cwd().resolve()
