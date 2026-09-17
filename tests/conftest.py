import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RAD_HOME", str(tmp_path / "radhome"))
    from rad.home import RadHome
    return RadHome(str(tmp_path / "radhome"))
