"""v3.3 Agent M — Docker Swarm + x402 USDC for MCP marketplace (McpMallPane), lab-gated VERIFIED-only.

Tests:
- docker isolation hardened (read_only_root, no_new_privileges, cap_drop ALL, secrets never injected)
- swarm spawn in Docker without secrets leak (vault secret must not appear in artifact/output)
- x402 USDC micropay for McpMallPane: create -> verify -> micropay_for_mcp
"""
import os
import tempfile
import pathlib


def _tmp_home():
    from rad.home import RadHome
    tmp = pathlib.Path(tempfile.mkdtemp()) / ".rad"
    return RadHome(str(tmp))


def test_docker_isolation_hardened():
    from rad.agent_swarm import isolation_config, DOCKER_ISOLATION
    cfg = isolation_config()
    assert cfg["read_only_root"] is True
    assert cfg["no_new_privileges"] is True
    assert cfg["cap_drop"] == ["ALL"]
    assert cfg["secrets_env"] == "never"
    assert cfg["network_mode"] == "none"
    assert cfg["lab_gated"] is True
    assert cfg["verified_only"] is True
    # also direct constant
    assert DOCKER_ISOLATION["read_only_root"] is True


def test_swarm_health_lab_gated_verified():
    from rad.agent_swarm import DockerSwarm
    home = _tmp_home()
    os.environ["RAD_DOCKER"] = "1"
    try:
        swarm = DockerSwarm(home)
        h = swarm.health()
        assert h["isolation"]["read_only_root"] is True
        assert h["lab_gated"] is True
        assert h["verified_only"] is True
        assert h["no_shell_bypass"] is True
        assert h["scope"] == "agent-swarm"
    finally:
        os.environ.pop("RAD_DOCKER", None)


def test_swarm_spawn_isolated_no_secrets_leak():
    from rad.agent_swarm import DockerSwarm, check_no_secrets_leak
    home = _tmp_home()
    # inject a secret into vault — swarm must never leak it
    secret = "gsk_live_9f3ab77cd21e4deadbeef00112233445566"
    home.vault_set("groq", secret)
    os.environ["RAD_DOCKER"] = "1"
    try:
        swarm = DockerSwarm(home)
        result = swarm.spawn_isolated("write swarm artifact for test", agent="coder")
        assert result["verified"] is True
        assert result["leak_check"]["ok"] is True
        assert result["escaped"] is False
        assert result["lab_gated"] is True
        # artifact must not contain secret
        art = pathlib.Path(result["artifact"])
        assert art.exists()
        text = art.read_text(encoding="utf-8")
        assert secret not in text
        assert secret not in str(result)
        # also check via helper: secret text should be flagged as leak
        leak = check_no_secrets_leak(f"token {secret}", home)
        assert leak["ok"] is False
        # clean text passes
        clean = check_no_secrets_leak("hello swarm isolated", home)
        assert clean["ok"] is True
    finally:
        os.environ.pop("RAD_DOCKER", None)


def test_swarm_spawn_many_parallel_capped_8():
    from rad.agent_swarm import DockerSwarm
    home = _tmp_home()
    os.environ["RAD_DOCKER"] = "1"
    try:
        swarm = DockerSwarm(home)
        goals = [f"task {i} write file" for i in range(4)]
        results = swarm.spawn_many(goals, parallel=8)
        assert len(results) == 4
        assert all(r["verified"] for r in results)
        # each has isolation and no leak
        for r in results:
            assert r["isolation"]["cap_drop"] == ["ALL"]
    finally:
        os.environ.pop("RAD_DOCKER", None)


def test_x402_usdc_micropay_for_mcp_mallpane():
    from rad.x402 import create_payment, verify_payment, micropay_for_mcp, x402_health, X402_CURRENCY
    # basic create/verify
    p = create_payment("demo-skill", amount_usdc=0.02, payer="tester")
    assert p["ok"] is True
    assert p["currency"] == "USDC"
    assert p["payment_id"].startswith("x402_")
    v = verify_payment(p)
    assert v["verified"] is True
    # full flow via mall
    home = _tmp_home()
    from rad.skills import mall_invent
    inv = mall_invent(home, "a test MCP that counts words", name="x402-demo")
    assert inv["invented"] == "x402-demo"
    res = micropay_for_mcp(home, "x402-demo", amount_usdc=0.05, payer="tester")
    assert res["ok"] is True
    assert res["verified"] is True
    assert res["currency"] == "USDC"
    assert res["chain"] == "base"
    assert "x402" in res["note"].lower() or "mcp" in res["note"].lower()
    # health
    h = x402_health()
    assert h["currency"] == "USDC"
    assert h["available"] is True
    # McpMallPane component must exist and mention x402
    pane = pathlib.Path("desktop/src/components/chat/McpMallPane.tsx").read_text(encoding="utf-8")
    assert "x402" in pane.lower()
    assert "McpMallPane" in pane


def test_x402_price_range_enforced():
    from rad.x402 import create_payment
    low = create_payment("s", amount_usdc=0.0001)
    assert low["ok"] is False
    high = create_payment("s", amount_usdc=999)
    assert high["ok"] is False
    ok = create_payment("s", amount_usdc=0.02)
    assert ok["ok"] is True
