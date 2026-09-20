"""Desktop API client contract: 15 new client methods, safe settings filter, budget guard.

Static tests only - no server needed.
"""
import re
from pathlib import Path

from rad.control.objectives import Budget  # conftest adds repo root to sys.path

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "desktop" / "src" / "api.ts"
TEXT = API.read_text(encoding="utf-8")

NEW_METHODS = {
    "objectiveEvents": "/v1/objectives/{id}/events",
    "objectiveAction": "/v1/objectives/{id}/resume",
    "objectiveWhy": "/v1/objectives/{id}/why",
    "memoryRecall": "/v1/memory/recall",
    "memoryAdd": "/v1/memory",
    "tools": "/v1/tools",
    "doctor": "/v1/doctor",
    "policy": "/v1/policy",
    "audit": "/v1/audit",
    "user": "/v1/user",
    "world": "/v1/world",
    "benchmarks": "/v1/benchmarks",
    "labHistory": "/v1/lab/history",
    "evolveCandidates": "/v1/evolve/candidates",
    "agents": "/v1/agents",
}

EXPECTED_SAFE_KEYS = {
    "workspace",
    "free_lock",
    "force_provider",
    "model",
    "tts",
    "stt",
    "allow_outside_workspace",
    "allow_localhost_web",
}

FORBIDDEN_SETTINGS = {
    "max_plan_tasks",
    "max_tool_rounds",
    "tool_calls",
    "budget",
    "tool_router",
    "auto",
}


def _parse_const(name: str) -> set[str]:
    m = re.search(rf"{name}\s*=\s*\[(.*?)\]\s*as const", TEXT, re.S)
    assert m, f"{name} constant not found in api.ts"
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def test_no_shell_and_no_tool_execution_surface():
    assert "/v1/shell" not in TEXT
    assert "run_tool" not in TEXT


def test_routes_constant_present():
    assert "ROUTES" in TEXT


def test_all_fifteen_new_methods_exist():
    for method in NEW_METHODS:
        assert f"{method}(" in TEXT, f"method {method} missing from RadClient"


def test_every_new_method_route_is_registered():
    routes = _parse_const("ROUTES")
    for method, route in NEW_METHODS.items():
        assert route in routes, f"{method} route {route} missing from ROUTES"
    assert len(routes) >= 20


def test_objective_action_only_resume_pause_cancel():
    m = re.search(r"objectiveAction\(id: string, action: \"resume\" \| \"pause\" \| \"cancel\"\)", TEXT)
    assert m, "objectiveAction must accept exactly resume | pause | cancel"
    verbs = set(re.findall(r"\{id\}/(resume|pause|cancel)\b", TEXT))
    assert verbs == {"resume", "pause", "cancel"}


def test_create_objective_signature_uses_options_object():
    assert "run = true" not in TEXT, "old boolean run param must be replaced"
    assert "createObjective(" in TEXT
    assert "unknown budget key" in TEXT, "budget key validation must exist"
    assert "Object.keys(budget)" in TEXT


def test_budget_keys_match_backend_budget_fields():
    keys = _parse_const("BUDGET_KEYS")
    assert keys == set(Budget.__dataclass_fields__)
    assert "run_tool" not in keys


def test_settings_safe_keys_filter():
    safe = _parse_const("SETTINGS_SAFE_KEYS")
    assert safe == EXPECTED_SAFE_KEYS
    assert safe.isdisjoint(FORBIDDEN_SETTINGS), "forbidden keys must never be settable"
    assert "SETTINGS_SAFE_KEYS as readonly string[]" in TEXT, "setSettings must filter via safe keys"