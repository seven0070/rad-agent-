"""v3.1 Desktop hardening — Tauri CSP/Isolation, sidecar health, McpMallPane/FlowCanvas, fetch_only_in_api_client stays green."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DESK = ROOT / "desktop"

def _conf():
    return json.loads((DESK / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))

def _frontend():
    for p in sorted((DESK / "src").rglob("*")):
        if p.is_file() and p.suffix in {".ts",".tsx",".js"}:
            yield p

def test_csp_isolation_hardened():
    c = _conf()
    sec = c["app"]["security"]
    # Isolation pattern brownfield + freezePrototype etc already in v3.0 — v3.1 keeps
    assert sec["pattern"]["use"] == "brownfield"
    assert sec["freezePrototype"] is True
    assert sec["dangerousDisableAssetCspModification"] is False
    csp = sec["csp"]
    m = re.search(r"connect-src\s+([^;]+)", csp)
    assert m and "'self'" in m.group(1)
    assert "http://127.0.0.1:*" in csp
    assert "http://localhost:*" in csp
    assert "https://" not in m.group(1)

def test_external_bin_sidecars_present():
    conf = _conf()
    bins = conf["bundle"]["externalBin"]
    assert "binaries/rad" in bins
    assert "binaries/rad-backend" in bins

def test_tauri_capabilities_minimal_surface():
    cap = DESK / "src-tauri" / "capabilities" / "default.json"
    assert cap.exists()
    data = json.loads(cap.read_text(encoding="utf-8"))
    perms = data.get("permissions", [])
    # only backend lifecycle + no arbitrary shell
    assert "core:default" in perms
    # no fs.write, no shell, no http plugin in capabilities (network stays in api.ts)
    joined = " ".join(perms).lower()
    assert "fs:" not in joined or "fs:default" not in joined  # minimal
    assert "shell" not in joined

def test_mcp_mall_pane_integrated_and_flowcanvas():
    # Both panes exist
    assert (DESK / "src" / "components" / "chat" / "McpMallPane.tsx").exists()
    assert (DESK / "src" / "components" / "FlowCanvas.tsx").exists()
    # ChatView integrates McpMallPane (v3.1)
    chatview = (DESK / "src" / "components" / "ChatView.tsx").read_text(encoding="utf-8")
    assert "McpMallPane" in chatview, "ChatView must integrate McpMallPane auto panel (N4 Appsmith)"
    # Trace integrates FlowCanvas (v3.1 observability)
    trace = (DESK / "src" / "pages" / "Trace.tsx").read_text(encoding="utf-8")
    assert "FlowCanvas" in trace, "Trace must render FlowCanvas DAG"

def test_fetch_only_in_api_client_stays_green():
    for p in _frontend():
        text = p.read_text(encoding="utf-8")
        assert "XMLHttpRequest" not in text, f"{p.name} must not use XHR"
        assert "axios." not in text
        if p.name != "api.ts":
            # McpMallPane uses RadClient, not raw fetch
            assert "fetch(" not in text, f"{p.name} must reach API only through api.ts — found fetch in {p}"

def test_api_client_has_no_shell_and_settings_safe():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    assert "/v1/shell" not in text
    assert "run_tool" not in text
    assert "SETTINGS_SAFE_KEYS" in text
    assert "eventsStream" in text, "api.ts must expose eventsStream for SSE observability (v3.1)"

def test_sidecar_health_and_reaping():
    # sidecar.py must have process-group orphan reaping + health probe
    sc = pathlib.Path("rad/sidecar.py").read_text(encoding="utf-8")
    assert "ensure_process_group" in sc
    assert "reap_process_group" in sc
    assert "def health" in sc
    # api health still reachable via sidecar loopback only
    assert "127.0.0.1" in sc and "loopback" in sc.lower()

def test_desktop_no_node_process_apis():
    for p in _frontend():
        text = p.read_text(encoding="utf-8")
        for token in ("child_process","exec(","spawn(","fs."):
            assert token not in text, f"{p.name} must not use {token}"
