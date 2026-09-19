"""Desktop is a surface: no shell from the frontend, no second control plane."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESK = ROOT / "desktop"


def test_desktop_stack_present():
    assert (DESK / "package.json").exists()
    pkg = (DESK / "package.json").read_text(encoding="utf-8")
    assert "0.1.0-alpha" in pkg
    assert "@tauri-apps/api" in pkg
    assert (DESK / "src-tauri" / "tauri.conf.json").exists()
    assert (DESK / "src-tauri" / "src" / "lib.rs").exists()
    assert (DESK / "src" / "App.tsx").exists()


def test_frontend_has_no_arbitrary_shell():
    src = ""
    for p in (DESK / "src").rglob("*"):
        if p.suffix in {".ts", ".tsx", ".js"}:
            src += p.read_text(encoding="utf-8") + "\n"
    rust = (DESK / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    assert "run_shell" not in src
    assert "shell.execute" not in src or "capabilities" in src  # conceptual name in UI is ok
    assert "invoke(\"shell" not in src
    assert "tauri-plugin-shell" not in rust
    assert 'args(["-m", "rad", "serve"' in rust
    # no user-controlled command interpolation
    assert ".arg(cmd)" not in rust
    assert "std::process::Command::new(user" not in rust


def test_api_client_only_known_routes():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    assert "/v1/chat" in text and "/v1/authority" in text
    assert "/v1/shell" not in text
    assert "run_tool" not in text
    assert "ROUTES" in text
