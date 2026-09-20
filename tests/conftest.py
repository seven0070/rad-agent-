import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def _isolate_provider_env(monkeypatch):
    """Tests must stay offline: a developer (or this agent) with keys in the process
    env must not make doctor/router see a live brain or spend money."""
    for k in list(os.environ):
        if k.endswith("_API_KEY") or k.endswith("_NIM_API_KEY"):
            monkeypatch.delenv(k, raising=False)
    monkeypatch.delenv("RAD_TOOL_ROUTER", raising=False)


@pytest.fixture(autouse=True)
def _isolate_disk_env(monkeypatch):
    """Ensure disk check reports healthy free space during automated testing."""
    import collections
    import shutil
    usage_tuple = collections.namedtuple("usage", ["total", "used", "free"])
    monkeypatch.setattr(shutil, "disk_usage", lambda path: usage_tuple(100_000_000_000, 10_000_000_000, 90_000_000_000))


@pytest.fixture()
def home(tmp_path, monkeypatch):
    """A throw-away RAD home with its own workspace.

    The workspace is set explicitly. The runtime default is `~/.rad/workspace` (never the
    process CWD); tests still pin their own directory so they cannot collide with each other.
    """
    monkeypatch.setenv("RAD_HOME", str(tmp_path / "radhome"))
    from rad.home import RadHome
    ws = tmp_path / "home_ws"          # deliberately not `tmp_path/"ws"`: tests create that one
    ws.mkdir(parents=True, exist_ok=True)
    h = RadHome(str(tmp_path / "radhome"))
    h.update(workspace=str(ws))
    return h
