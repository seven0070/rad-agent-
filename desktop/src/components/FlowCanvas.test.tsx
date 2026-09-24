import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FlowCanvas } from "./FlowCanvas";

// to_flow shape from rad/control/graph.py TaskGraph.to_flow()
const sampleFlow = {
  nodes: [
    { id: "t1", type: "taskNode", position: { x: 0, y: 0 }, data: { label: "ingest", status: "PENDING", checks: 1, depends_on: [] }, style: { status: "PENDING" } },
    { id: "t2", type: "taskNode", position: { x: 220, y: 0 }, data: { label: "transform", status: "RUNNING", checks: 2, depends_on: ["t1"] }, style: { status: "RUNNING" } },
    { id: "t3", type: "taskNode", position: { x: 440, y: 0 }, data: { label: "report", status: "COMPLETED", checks: 1, depends_on: ["t2"] }, style: { status: "COMPLETED" } },
  ],
  edges: [
    { id: "t1->t2", source: "t1", target: "t2", type: "dagEdge" },
    { id: "t2->t3", source: "t2", target: "t3", type: "dagEdge" },
  ],
};

describe("FlowCanvas visual", () => {
  it("renders nodes from TaskGraph.to_flow()", () => {
    render(<FlowCanvas nodes={sampleFlow.nodes} edges={sampleFlow.edges} />);
    expect(screen.getByText("t1")).toBeTruthy();
    expect(screen.getByText("t2")).toBeTruthy();
    expect(screen.getByText("t3")).toBeTruthy();
    // status badges rendered
    expect(screen.getByText("PENDING")).toBeTruthy();
    expect(screen.getByText("RUNNING")).toBeTruthy();
    expect(screen.getByText("COMPLETED")).toBeTruthy();
  });

  it("has minimap zoom/pan controls", () => {
    render(<FlowCanvas nodes={sampleFlow.nodes} edges={sampleFlow.edges} />);
    // minimap label
    expect(screen.getByText("MINIMAP")).toBeTruthy();
    // zoom controls
    expect(screen.getByText("Fit")).toBeTruthy();
    expect(screen.getByText("100%")).toBeTruthy();
    // zoom interaction
    const plus = screen.getByText("+");
    fireEvent.click(plus);
    expect(screen.getByText("115%")).toBeTruthy();
    const minus = screen.getByText("-");
    fireEvent.click(minus);
    expect(screen.getByText("100%")).toBeTruthy();
  });

  it("bezier edges use TaskGraph depends_on via flow edges", () => {
    const { container } = render(<FlowCanvas nodes={sampleFlow.nodes} edges={sampleFlow.edges} />);
    const paths = container.querySelectorAll("svg path");
    // at least 2 dag edges + 1 arrow marker path = 3, but filter marker
    const edgePaths = Array.from(paths).filter((p) => p.getAttribute("markerEnd") !== null);
    expect(edgePaths.length).toBe(2);
  });

  it("integrates McpMallPane when showMall is true", async () => {
    render(<FlowCanvas nodes={sampleFlow.nodes} edges={sampleFlow.edges} showMall mallGoal="count words" />);
    // McpMallPane renders with data-testid mcp-mall-pane
    expect(screen.getByTestId("mcp-mall-pane")).toBeTruthy();
  });

  it("renders empty flow without crashing", () => {
    render(<FlowCanvas nodes={[]} edges={[]} />);
    expect(screen.getByText("MINIMAP")).toBeTruthy();
  });
});
