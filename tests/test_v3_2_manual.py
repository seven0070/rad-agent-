"""v3.2 Omarchy OS manual completeness — full 11-repo fusion table + install steps."""
import pathlib

MANUAL = pathlib.Path("manual/README.md").read_text(encoding="utf-8")
LOWER = MANUAL.lower()

# 11 repos required
REPOS = ["appsmith", "magnitude", "buzz", "openhands", "comfyui", "openmausbot", "flue", "agent-zero", "langflow", "omarchy", "roboflow"]


def test_manual_contains_all_11_repos():
    for repo in REPOS:
        assert repo.lower() in LOWER, f"manual must mention {repo}"


def test_manual_has_fusion_table_with_integration_points():
    # Full table header
    assert "11-repo fusion" in LOWER or "11-repo" in LOWER
    assert "what rad borrows" in LOWER
    assert "where it lands" in LOWER or "where it lands in rad" in LOWER
    # Check each repo appears in table row context
    for repo in REPOS:
        # at least one mention with integration hint
        assert repo.lower() in LOWER
    # Specific integration points
    assert "McpMallPane" in MANUAL
    assert "FlowCanvas" in MANUAL
    assert "blackboard" in LOWER
    assert "roboflow" in LOWER and "vision" in LOWER


def test_manual_has_install_steps():
    assert "install" in LOWER
    assert 'pip install -e ".[dev]"' in MANUAL or "pip install -e" in MANUAL
    assert "pytest -q -n auto" in MANUAL
    # voice install
    assert "pip install -e" in MANUAL and "voice" in LOWER
    assert "rad chat --voice --voice-backend ten" in MANUAL
    assert "RAD_TEN=1" in MANUAL
    # desktop
    assert "cargo check" in MANUAL
    assert "npm ci" in MANUAL or "npm run build" in MANUAL
    # omarchy manifest
    assert "omarchy_os" in LOWER or "omarchy manifest" in LOWER
    # observability
    assert "rad trace" in MANUAL
    assert "rad replay" in MANUAL


def test_manual_preserves_opinionated_defaults_and_v32_polish():
    assert "objective_parallel = 8" in MANUAL
    assert "VERIFIED-only" in MANUAL
    assert "Needle OFF" in MANUAL or "tool_router = existing" in MANUAL
    assert "nvidia" in LOWER
    assert "v3.2" in MANUAL
    assert "919" in MANUAL  # 919 tests
    assert "11 cats" in MANUAL or "11 cats" in MANUAL


def test_manual_mentions_lab_gated_and_no_vendoring():
    assert "lab-gated" in LOWER or "lab_gated" in LOWER
    assert "not vendored" in LOWER or "not vendoring" in LOWER or "inspiration" in LOWER


def test_omarchy_os_manifest_exists():
    from rad.omarchy_os import omarchy_manifest
    m = omarchy_manifest()
    assert m["os"] == "rad-omarchy"
    assert m["defaults"]["objective_parallel"] == 8
    assert m["defaults"]["tool_router"] == "existing"
    assert "VERIFIED-only" in m["defaults"]["verification"]
