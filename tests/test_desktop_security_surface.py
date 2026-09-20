"""Desktop security surface: loopback-only CSP, no process APIs in the UI, capped client.

Static, offline pytest assertions on repo files — no network, no server, no build.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DESK = ROOT / "desktop"

LOOPBACK_CONNECT_SOURCES = {
    "http://127.0.0.1:*",
    "http://localhost:*",
}

# Keys that route control-plane state. They must never be settable from the surface
# (settings filter) and must never appear in an inline request body literal.
FORBIDDEN_CONTROL_KEYS = {
    "tool_calls",
    "model_calls",
    "retries",
    "seconds",
    "money_usd",
    "tokens",
    "agents",
    "auto",
    "tool_router",
    "max_plan_tasks",
    "max_tool_rounds",
    "budget",
    "needler",
}

# Node/process surfaces that must never reach the UI bundle.
PROCESS_API_TOKENS = ("child_process", "exec(", "spawn(", "fs.")


def _iter_frontend_src():
    for p in sorted((DESK / "src").rglob("*")):
        if p.is_file() and p.suffix in {".ts", ".tsx", ".js"}:
            yield p


def _parse_const(text: str, name: str) -> set[str]:
    m = re.search(rf"{name}\s*=\s*\[(.*?)\]\s*as const", text, re.S)
    assert m, f"{name} constant not found"
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def _conf() -> dict:
    return json.loads((DESK / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))


def test_csp_connect_src_loopback_only():
    csp = _conf()["app"]["security"]["csp"]
    m = re.search(r"connect-src\s+([^;]+)", csp)
    assert m, "CSP must declare a connect-src directive"
    connect = m.group(1)
    assert "'self'" in connect
    assert "http://127.0.0.1:*" in connect
    assert "http://localhost:*" in connect
    # private-range, wildcard, and external https targets are all forbidden
    assert "http://10." not in connect
    assert "http://0.0.0.0" not in connect
    assert "https://" not in connect
    hosts = set(re.findall(r"https?://[^\s;]+", connect))
    assert hosts <= LOOPBACK_CONNECT_SOURCES, (
        f"connect-src must stay loopback-only, got {sorted(hosts - LOOPBACK_CONNECT_SOURCES)}"
    )


def test_external_bin_present_in_bundle():
    conf = _conf()
    assert "externalBin" in conf["bundle"], "bundle must declare externalBin"
    assert "binaries/rad" in conf["bundle"]["externalBin"], (
        "rad sidecar must be bundled as binaries/rad"
    )


def test_no_node_process_apis_in_frontend_src():
    for p in _iter_frontend_src():
        text = p.read_text(encoding="utf-8")
        for token in PROCESS_API_TOKENS:
            assert token not in text, f"{p.name} must not use `{token}` (node/process API in UI)"


def test_fetch_only_in_api_client():
    for p in _iter_frontend_src():
        text = p.read_text(encoding="utf-8")
        assert "XMLHttpRequest" not in text, f"{p.name} must not open raw XHR"
        assert "axios." not in text, f"{p.name} must not call axios directly"
        if p.name != "api.ts":
            assert "fetch(" not in text, f"{p.name} must reach the API only through api.ts"


def test_api_client_no_shell_or_tool_routes():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    assert "/v1/shell" not in text
    assert "run_tool" not in text


def test_settings_safe_keys_exclude_control_plane_keys():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    assert "SETTINGS_SAFE_KEYS" in text
    safe = _parse_const(text, "SETTINGS_SAFE_KEYS")
    assert safe.isdisjoint(FORBIDDEN_CONTROL_KEYS), (
        f"settings must never route control-plane keys, got {sorted(safe & FORBIDDEN_CONTROL_KEYS)}"
    )


def _inline_request_bodies(text: str) -> list[str]:
    """Simple inline object literals passed as the body of POST/PUT req() calls."""
    bodies = []
    for m in re.finditer(r'req<[^>]*>\(\s*"(?:POST|PUT)"[^)]*?,\s*(\{[^{}]*\})\s*\)', text, re.S):
        bodies.append(m.group(1))
    return bodies


def test_no_forbidden_keys_in_inline_request_bodies():
    text = (DESK / "src" / "api.ts").read_text(encoding="utf-8")
    for body in _inline_request_bodies(text):
        words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", body))
        assert words.isdisjoint(FORBIDDEN_CONTROL_KEYS), (
            f"request body literal must not serialize control-plane keys, "
            f"got {sorted(words & FORBIDDEN_CONTROL_KEYS)}"
        )


def test_no_budget_cap_literal_outside_api_client():
    # no view/hook may pass a numeric cap into an objective — that is the client's job,
    # and even api.ts caps are validated against BUDGET_KEYS on the Python side.
    for p in _iter_frontend_src():
        if p.name == "api.ts":
            continue
        text = p.read_text(encoding="utf-8")
        assert "tool_calls:" not in text, f"{p.name} must not send a numeric tool_calls cap"
        assert "model_calls:" not in text, f"{p.name} must not send a numeric model_calls cap"


def test_verification_card_machine_check_copy():
    candidates = sorted((DESK / "src").rglob("VerificationCard.tsx"))
    if not candidates:
        pytest.skip("Phase 3 VerificationCard view not present yet — soft fail")
    text = candidates[0].read_text(encoding="utf-8")
    assert "No machine-check pass" in text, "VerificationCard must carry the fixed copy"
    assert "No VERIFIED" in text, "VerificationCard must carry the fixed copy"


def test_no_node_core_imports_in_frontend_src():
    for p in _iter_frontend_src():
        text = p.read_text(encoding="utf-8")
        assert "from 'node:" not in text, f"{p.name} must not import node core (single quotes)"
        assert 'from "node:' not in text, f"{p.name} must not import node core (double quotes)"
        assert "require('node:" not in text, f"{p.name} must not require node core"
        assert 'require("node:' not in text, f"{p.name} must not require node core"