"""Ship-readiness regressions found while validating the v0.2 release candidate.

These are not new features: they lock in install/doctor/docs behaviour a new user
actually hits (missing keys, advertised CLI, default workspace, config validation).
"""
from __future__ import annotations

import json
from pathlib import Path

from rad import __version__
from rad.cli import main
from rad.doctor import Doctor
from rad.home import RadHome
from rad.lab import scenarios


def test_version_is_synced():
    assert __version__ == "0.2.0"
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    assert 'version = "0.2.0"' in pyproject.read_text(encoding="utf-8")


def test_default_workspace_is_inside_home_not_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    h = RadHome(str(tmp_path / "rh"))
    ws = h.workspace().resolve()
    assert ws == (h.root / "workspace").resolve()
    assert ws.is_dir()
    assert ws != Path.cwd().resolve()
    assert (h.root / "workspace").is_dir()


def test_lab_suite_bank_is_an_alias_for_banks():
    a = scenarios("bank", sample=5, seed=1)
    b = scenarios("banks", sample=5, seed=1)
    assert a and [s.id for s in a] == [s.id for s in b]


def test_advertised_lab_suite_bank_runs(home, capsys):
    rc = main(["--home", str(home.root), "lab", "run", "--suite", "bank", "--sample", "2", "--seed", "1"])
    out = capsys.readouterr().out
    assert rc == 0, out
    assert "no scenarios" not in out.lower()
    assert "suite must be" not in out


def test_config_set_rejects_invalid_and_unknown(home, capsys):
    rc = main(["--home", str(home.root), "config", "set", "objective_parallel", "99"])
    captured = capsys.readouterr()
    err = captured.out + captured.err
    assert rc == 1
    assert "out of range" in err
    data = json.loads(home.config_path.read_text(encoding="utf-8"))
    assert data.get("objective_parallel") != 99

    rc = main(["--home", str(home.root), "config", "set", "not_a_real_key", "1"])
    assert rc == 1

    rc = main(["--home", str(home.root), "config", "set", "free_lock", "true"])
    assert rc == 0
    data = json.loads(home.config_path.read_text(encoding="utf-8"))
    assert data["free_lock"] is True


def test_doctor_missing_provider_is_optional_not_error(home):
    """A clean install without keys must not make `rad doctor` fail — providers are optional."""
    fs = {f.check: f for f in Doctor(home, fix=False, probe_network=True).run()}
    assert fs["providers"].status == "optional"
    assert fs["providers"].status != "fail"
    assert "rad keys add" in fs["providers"].message
    assert fs["sandbox"].status == "ok"
    from rad.cli import cmd_doctor
    import argparse
    ns = argparse.Namespace(home=str(home.root), fix=False, offline=False, json=False)
    assert cmd_doctor(ns) == 0


def test_global_home_flag_works_with_subcommands(home, capsys):
    """`rad --home <dir> <cmd>` used to be rewritten into `rad chat --home …` and fail."""
    rc = main(["--home", str(home.root), "version"])
    out = capsys.readouterr().out
    assert rc == 0 and "v0.2.0" in out


def test_nvidia_default_model_is_not_eol(tmp_path):
    """NIM retired meta/llama-3.3-70b-instruct (HTTP 410, 2026-08-26). The builtin default
    must be a model that still exists so `rad keys add nvidia` works without a pin."""
    from rad.providers import all_specs
    spec = next(s for s in all_specs(RadHome(str(tmp_path / "h"))) if s.name == "nvidia")
    assert spec.default_model != "meta/llama-3.3-70b-instruct"
    assert spec.default_model.startswith("meta/")
    assert spec.vision_model


def test_openai_tool_calls_use_nested_function_shape():
    """NVIDIA NIM rejects flat `{id,name,arguments}` tool_calls (HTTP 400)."""
    from rad.providers import _openai_message
    m = _openai_message({"role": "assistant", "content": "", "tool_calls": [
        {"id": "c1", "name": "write_file", "arguments": {"path": "a.txt", "content": "x"}},
    ]})
    tc = m["tool_calls"][0]
    assert tc["type"] == "function" and tc["id"] == "c1"
    assert tc["function"]["name"] == "write_file"
    assert json.loads(tc["function"]["arguments"]) == {"path": "a.txt", "content": "x"}
    already = _openai_message({"role": "assistant", "tool_calls": [{
        "id": "c2", "type": "function",
        "function": {"name": "read_file", "arguments": {"path": "b.txt"}},
    }]})
    assert json.loads(already["tool_calls"][0]["function"]["arguments"])["path"] == "b.txt"


def test_rad_version_cli(capsys):
    assert main(["version"]) == 0
    assert "v0.2.0" in capsys.readouterr().out
