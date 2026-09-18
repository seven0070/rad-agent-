import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def home(tmp_path, monkeypatch):
    """A throw-away RAD home with its own workspace.

    The workspace is set explicitly: `RadHome.workspace()` falls back to the process CWD, so a
    test that forgets it writes into the repository (that is how stray `f.csv`/`r0_out.txt` files
    used to appear in the project root).
    """
    monkeypatch.setenv("RAD_HOME", str(tmp_path / "radhome"))
    from rad.home import RadHome
    ws = tmp_path / "home_ws"          # deliberately not `tmp_path/"ws"`: tests create that one
    ws.mkdir(parents=True, exist_ok=True)
    h = RadHome(str(tmp_path / "radhome"))
    h.update(workspace=str(ws))
    return h
