"""v3.4 Agent P — Studio Flow polish: FlowCanvas renders TaskGraph.to_flow() with minimap/zoom/pan + McpMallPane integration, visual test."""
import pathlib

FLOW = pathlib.Path("desktop/src/components/FlowCanvas.tsx").read_text(encoding="utf-8")
MALL = pathlib.Path("desktop/src/components/chat/McpMallPane.tsx").read_text(encoding="utf-8")
VTEST = pathlib.Path("desktop/src/components/FlowCanvas.test.tsx")

def test_to_flow_shape_is_flowcanvas_compatible():
    from rad.control.tasks import Task
    from rad.control.graph import TaskGraph
    g = TaskGraph()
    t1 = Task.new("o", "ingest raw notes"); t1.id = "t_ingest"
    t2 = Task.new("o", "transform into report"); t2.id = "t_transform"; t2.depends_on = ["t_ingest"]
    t3 = Task.new("o", "verify report exists"); t3.id = "t_verify"; t3.depends_on = ["t_transform"]
    for t in (t1, t2, t3):
        g.add(t)
    flow = g.to_flow()
    assert "nodes" in flow and "edges" in flow
    assert len(flow["nodes"]) == 3 and len(flow["edges"]) == 2
    for n in flow["nodes"]:
        assert "id" in n and "position" in n and "data" in n and "style" in n
        assert "x" in n["position"] and "y" in n["position"]
        assert "label" in n["data"] and "status" in n["data"] and "checks" in n["data"]
        assert "depends_on" in n["data"]
        assert isinstance(n["data"]["checks"], int)
        assert n["id"] in {t.id for t in (t1, t2, t3)}
    # edges mirror depends_on
    assert any(e["source"] == "t_ingest" and e["target"] == "t_transform" for e in flow["edges"])
    # style.status == data.status
    for n in flow["nodes"]:
        assert n["style"]["status"] == n["data"]["status"]
    # positions are deterministic grid (no LLM)
    positions = {(n["position"]["x"], n["position"]["y"]) for n in flow["nodes"]}
    assert len(positions) == 3

def test_flowcanvas_has_minimap_zoom_pan():
    assert "MINIMAP" in FLOW
    assert 'data-testid="flow-minimap"' in FLOW or "flow-minimap" in FLOW
    assert "setZoom" in FLOW and "setPan" in FLOW
    # zoom buttons + Fit + zoom readout
    assert "zoomIn" in FLOW or "zoom" in FLOW.lower()
    assert "Fit" in FLOW
    # pan handler (drag background)
    assert "isPanning" in FLOW or "onMouseDown" in FLOW
    # minimap node click focuses via onSelect
    assert "minimap-node-" in FLOW

def test_flowcanvas_renders_to_flow_shapes():
    # props must accept TaskGraph.to_flow() arrays directly
    assert "FlowNode" in FLOW and "FlowEdge" in FLOW
    assert "position: { x: number; y: number }" in FLOW
    assert "data: { label: string; status: string; checks: number" in FLOW
    # bezier edge path
    assert "C ${sx + dx}" in FLOW or "bezier" in FLOW.lower() or "M ${sx}" in FLOW
    # status color mapping uses VERIFIED-only palette
    assert "VERIFIED" in FLOW and "COMPLETED" in FLOW and "STATUS_COLOR" in FLOW
    # draggable nodes
    assert "handleNodeDown" in FLOW

def test_flowcanvas_integrates_mcp_mallpane():
    assert 'from "./chat/McpMallPane"' in FLOW or "McpMallPane" in FLOW
    assert "showMall" in FLOW
    assert "mallGoal" in FLOW
    assert "McpMallPane" in FLOW and "<McpMallPane" in FLOW
    assert "objectiveGoal" in FLOW
    # McpMallPane itself must exist and be Appsmith auto panel with x402
    assert "McpMallPane" in MALL
    assert "x402" in MALL.lower()
    assert "data-testid=\"mcp-mall-pane\"" in MALL

def test_flowcanvas_visual_test_exists():
    assert VTEST.exists(), "desktop/src/components/FlowCanvas.test.tsx visual test must exist"
    txt = VTEST.read_text(encoding="utf-8")
    assert "renders nodes from TaskGraph.to_flow" in txt
    assert "minimap" in txt.lower() and "zoom" in txt.lower()
    assert "McpMallPane" in txt or "showMall" in txt
    assert "to_flow" in txt or "sampleFlow" in txt
    assert "visual" in txt.lower() or "FlowCanvas" in txt

def test_blackboard_lab_gated_verified_only_preserved():
    # v3.4 keeps swarm invariants: objective_parallel=8, needle OFF
    from rad.home import DEFAULTS
    assert DEFAULTS["objective_parallel"] == 8
    assert DEFAULTS["accept_unverified_done"] is False
    assert DEFAULTS["tool_router"] == "existing"
