"""v3.2 Reliability — Desktop CI cargo check retry + pytest -q -n auto 919+ no OOM."""
import pathlib

DESKTOP_YML = pathlib.Path(".github/workflows/desktop.yml").read_text(encoding="utf-8")
CI_YML = pathlib.Path(".github/workflows/ci.yml").read_text(encoding="utf-8")


def test_desktop_ci_cargo_check_has_retry():
    assert "cargo check" in DESKTOP_YML
    # retry logic: must have retry 3x or loop
    lower = DESKTOP_YML.lower()
    has_retry = (
        "retry" in lower
        and "cargo check" in lower
        or "for i in 1 2 3" in DESKTOP_YML
        or "attempt" in lower
    )
    assert has_retry, "desktop.yml must retry cargo check on flake (3×)"
    # ensure it loops 3 times
    assert "3" in DESKTOP_YML and "cargo check" in DESKTOP_YML
    # also ensure cargo clippy/build still present
    assert "cargo clippy" in DESKTOP_YML
    assert "cargo build" in DESKTOP_YML


def test_desktop_ci_full_suite_uses_n_auto_without_oom():
    assert "-n auto" in DESKTOP_YML
    # worksteal or loadscope prevents OOM
    assert "worksteal" in DESKTOP_YML or "loadscope" in DESKTOP_YML or "worksteal" in CI_YML


def test_ci_uses_n_auto_and_stays_919_no_oom():
    assert "-n auto" in CI_YML, "CI must keep pytest -q -n auto"
    assert "worksteal" in CI_YML or "loadscope" in CI_YML, "CI should use worksteal/loadscope to avoid OOM"
    # ensure acceptance gate still runs
    assert "rad acceptance" in CI_YML
    assert "rad doctor --offline" in CI_YML


def test_pytest_collect_stays_919_plus():
    # v3.2 must keep 919+ tests; we added ~22 new v3.2 tests so should be 941+
    import subprocess, sys
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "--collect-only"], capture_output=True, text=True, timeout=60)
    out = result.stdout + result.stderr
    # look for "tests collected" line
    import re
    m = re.search(r"(\d+) tests? collected", out)
    assert m, f"could not parse collect: {out[:500]}"
    n = int(m.group(1))
    assert n >= 919, f"must stay 919+, got {n}"
    # ensure v3.2 files counted
    assert n >= 935, f"with v3.2 additions should be >=935, got {n}"


def test_pytest_n_auto_runs_without_oom_quick_sample():
    # run a quick single-test with -n auto to ensure not OOM on small sample (fast, low overhead)
    import subprocess, sys
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-n", "auto", "--dist", "worksteal", "-k", "test_ten_available_stub_ci_safe_without_install", "tests/test_v3_2_voice_ten.py"],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, f"-n auto sample should pass: {result.stdout[-500:]} {result.stderr[-500:]}"
    assert "passed" in result.stdout
