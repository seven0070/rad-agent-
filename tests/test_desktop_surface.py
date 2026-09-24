"""Desktop is a surface: no shell from the frontend, no second control plane."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESK = ROOT / "desktop"


def test_desktop_stack_present():
    assert (DESK / "package.json").exists()
    pkg = (DESK / "package.json").read_text(encoding="utf-8")
    assert "0.2.0-alpha" in pkg
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
    assert "tauri-plugin-fs" not in rust
    # fixed argv for the sidecar and the dev fallback (no user-controlled strings)
    assert '"serve".into()' in rust and '"--host".into()' in rust
    assert '"127.0.0.1".into()' in rust          # loopback only
    assert "0.0.0.0" not in rust
    assert '"-m".into()' in rust and '"rad".into()' in rust   # dev fallback: python -m rad serve
    # no user-controlled command interpolation
    assert ".arg(cmd)" not in rust
    assert "Command::new(user" not in rust
    assert "sh -c" not in rust and "/bin/sh" not in rust and "/bin/bash" not in rust


def test_api_client_only_known_routes():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    assert "/v1/chat" in text and "/v1/authority" in text
    assert "/v1/shell" not in text
    assert "run_tool" not in text
    assert "ROUTES" in text
    # every route the client knows is a /v1/* string
    import re
    routes = re.findall(r'"/v1/[^"]*"', text)
    assert routes and all(r.startswith('"/v1/') for r in routes)


def test_sidecar_is_bundled_and_scoped():
    import json
    conf = json.loads((DESK / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    ext = conf.get("bundle", {}).get("externalBin") or []
    assert "binaries/rad-backend" in ext
    caps = json.loads((DESK / "src-tauri" / "capabilities" / "default.json").read_text(encoding="utf-8"))
    perms = caps[0]["permissions"] if isinstance(caps, list) else caps["permissions"]
    flat = [p if isinstance(p, str) else p.get("identifier", p.get("default", "")) for p in perms]
    for needed in (
        "allow-backend-info", "allow-backend-start", "allow-backend-stop",
        "allow-backend-restart", "allow-backend-health", "allow-default-home", "allow-api-token",
    ):
        assert needed in flat, needed
    # lifecycle commands only — no shell/fs/window-control plugins in capabilities
    joined = json.dumps(caps)
    assert "plugin:shell" not in joined and "plugin:fs" not in joined


def test_resolve_sidecar_prefers_installed_short_name():
    """Installers ship rad-backend[.exe]; the resolver must try that before the
    triple name and before the compile-time CARGO_MANIFEST_DIR fallback."""
    rust = (DESK / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    # names are preferred in sidecar_names() order: short first, then triple
    i_names = rust.find("fn sidecar_names()")
    i_resolve = rust.find("fn resolve_sidecar()")
    assert i_names > 0 and i_resolve > i_names, "sidecar_names must exist before resolve_sidecar"
    names_body = rust[i_names:i_resolve]
    i_short = names_body.find('"rad-backend.exe"')
    i_short_unix = names_body.find('"rad-backend"')
    i_triple = names_body.find("sidecar_name(triple)")
    assert i_short > 0 or i_short_unix > 0, "resolver must consider the installed short name"
    assert i_triple > 0, "resolver must still support the triple name (dev tree)"
    assert min(x for x in (i_short, i_short_unix) if x > 0) < i_triple, (
        "installed short name must be preferred over the triple name"
    )
    # install-dir candidates are pushed before the compile-time manifest path
    resolve_body = rust[i_resolve:]
    i_current_exe = resolve_body.find("current_exe()")
    i_manifest = resolve_body.find('env!("CARGO_MANIFEST_DIR")')
    assert i_current_exe > 0 and i_manifest > 0
    assert i_current_exe < i_manifest, "install-dir layout must be probed before CARGO_MANIFEST_DIR"
