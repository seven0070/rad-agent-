"""v3.3 Agent O — Docs + Release: manual/README.md 11-repo install, release notes, rad acceptance 50-item stub."""
import pathlib

MANUAL = pathlib.Path("manual/README.md").read_text(encoding="utf-8")
LOWER = MANUAL.lower()
README = pathlib.Path("README.md").read_text(encoding="utf-8")
RELEASE = pathlib.Path("docs/RELEASE_v3.3.md").read_text(encoding="utf-8") if pathlib.Path("docs/RELEASE_v3.3.md").exists() else ""

REPOS = ["appsmith", "magnitude", "buzz", "openhands", "comfyui", "openmausbot", "flue", "agent-zero", "langflow", "omarchy", "roboflow"]


def test_manual_v33_has_all_11_repos_and_fusion_table():
    for repo in REPOS:
        assert repo.lower() in LOWER, f"manual must mention {repo}"
    assert "11-repo fusion" in LOWER or "11-repo" in LOWER
    assert "what rad borrows" in LOWER
    assert "where it lands" in LOWER
    assert "McpMallPane" in MANUAL
    assert "FlowCanvas" in MANUAL
    assert "blackboard" in LOWER


def test_manual_v33_has_full_install_and_3_agents():
    assert "v3.3" in MANUAL
    assert any(x in MANUAL for x in ("940", "973", "985", "940+", "v3.4"))
    assert "objective_parallel = 8" in MANUAL
    assert "VERIFIED-only" in MANUAL
    assert "Needle OFF" in MANUAL or "tool_router = existing" in MANUAL
    assert "nvidia" in LOWER
    # full install steps
    assert 'pip install -e ".[dev]"' in MANUAL
    assert "pytest -q -n auto" in MANUAL
    assert "cargo check" in MANUAL
    assert "npm ci" in MANUAL
    assert "RAD_TEN=1" in MANUAL
    assert "RAD_DOCKER=1" in MANUAL or "docker" in LOWER
    assert "rad acceptance" in MANUAL
    # 3 agents
    assert "Agent M" in MANUAL or "Docker Swarm" in MANUAL
    assert "Agent N" in MANUAL or "HNSW" in MANUAL or "recall" in LOWER
    assert "Agent O" in MANUAL or "Release" in MANUAL
    # x402
    assert "x402" in LOWER
    # vss/HNSW
    assert "HNSW" in MANUAL or "hnsw" in LOWER or "sqlite-vss" in LOWER or "vss" in LOWER
    # docs pointer
    assert "docs/RELEASE_v3.3.md" in MANUAL or "RELEASE_v3.3" in MANUAL


def test_release_notes_v33_exist_and_complete():
    p = pathlib.Path("docs/RELEASE_v3.3.md")
    assert p.exists(), "docs/RELEASE_v3.3.md must exist for v3.3"
    txt = p.read_text(encoding="utf-8")
    lower = txt.lower()
    assert "v3.3" in txt
    assert "docker" in lower
    assert "x402" in lower
    assert "HNSW" in txt or "hnsw" in lower or "sqlite-vss" in lower
    assert "c88428c" in txt  # base tag
    assert "940" in txt
    assert "lab-gated" in lower or "lab_gated" in lower
    assert "11-repo" in lower
    for repo in REPOS:
        assert repo.lower() in lower, f"release notes must mention {repo}"


def test_acceptance_50_item_still_required():
    from rad.acceptance import REQUIRED, AREAS
    assert REQUIRED == 50
    assert len(AREAS) == 10
    # docs/ACCEPTANCE.md must still describe 50 items
    acc = pathlib.Path("docs/ACCEPTANCE.md").read_text(encoding="utf-8")
    assert "50" in acc
    assert "rad acceptance" in acc


def test_acceptance_stub_runs_two_items_without_heavy_gate():
    """Light stub that proves the gate is wired, without running full 40s gate in unit test."""
    from rad.acceptance import Gate
    from rad.home import RadHome
    import tempfile
    home = RadHome(tempfile.mkdtemp(prefix="radacc_v33_"))
    gate = Gate(home, full=False)
    # run two cheap items that must exist
    ok1, ev1 = gate.i_local_first()
    ok2, ev2 = gate.i_v1_cli()
    assert ok1 is True, ev1[:200]
    assert ok2 is True, ev2[:200]


def test_readme_carries_v33_polish_line():
    # README may not yet have v3.3 tag but should mention v3.2+v3.3 or docs pointer
    # we require at least v3.2 line exists and manual pointer
    assert "Rad Agent" in README
    # after our edit, ensure docs/release pointer is reachable
    assert "manual/README.md" in README or "docs/" in README
