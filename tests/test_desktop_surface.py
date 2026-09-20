"""Desktop is a surface: no shell from the frontend, no second control plane."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESK = ROOT / "desktop"


def test_desktop_stack_present():
    assert (DESK / "package.json").exists()
    pkg = (DESK / "package.json").read_text(encoding="utf-8")
    assert "1.0.1" in pkg
    assert "@tauri-apps/api" in pkg
    assert (DESK / "src-tauri" / "tauri.conf.json").exists()
    assert (DESK / "src-tauri" / "src" / "lib.rs").exists()
    assert (DESK / "src" / "App.tsx").exists()
    app = (DESK / "src" / "App.tsx").read_text(encoding="utf-8")
    for label in ("Jerry", "Objectives", "Execution", "Task graph", "Trace",
                  "Verification", "Artifacts", "Why", "Usage", "Permissions", "Settings"):
        assert label in app


def test_frontend_has_no_arbitrary_shell():
    src = ""
    for p in (DESK / "src").rglob("*"):
        if p.suffix in {".ts", ".tsx", ".js"}:
            src += p.read_text(encoding="utf-8") + "\n"
    rust = (DESK / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    cargo = (DESK / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    assert "run_shell" not in src
    assert "shell.execute" not in src or "capabilities" in src  # conceptual name in UI is ok
    assert "invoke(\"shell" not in src
    # no shell plugin anywhere in the Rust crate (manifest or source)
    assert "tauri-plugin-shell" not in rust
    assert "tauri-plugin-shell" not in cargo
    # dev path stays: `python -m rad serve` launched with a fixed argv literal
    assert 'args(["-m", "rad", "serve"' in rust
    assert "Command::new(python_bin())" in rust  # python backend launch is the allowed dev form
    # Phase 2 sidecar resolver must exist and be wired into the bundle
    assert "fn rad_program" in rust
    conf = (DESK / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    assert '"externalBin"' in conf
    assert '"binaries/rad"' in conf
    # the resolved program is fixed (RAD_BIN env, sidecar path, or python_bin()) —
    # never a user-supplied command string
    assert ".arg(cmd)" not in rust
    assert "Command::new(cmd)" not in rust
    assert "Command::new(user" not in rust
    assert "std::process::Command::new(user" not in rust


def test_api_client_only_known_routes():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    assert "/v1/chat" in text and "/v1/authority" in text
    assert "/v1/usage" in text
    assert "/v1/shell" not in text
    assert "run_tool" not in text
    assert "ROUTES" in text


def test_http_layer_supports_put():
    src = (ROOT / "rad" / "api.py").read_text(encoding="utf-8")
    assert "def do_PUT" in src
    assert "def do_OPTIONS" in src
    assert '"run"' in src
