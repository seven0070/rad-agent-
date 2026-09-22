// StudioCanvas.tsx — CrewAI Studio v2 Node-Based Workflow Canvas for RAD Agent.
// Renders interactive DAG nodes (Objective, Tasks, Tools, Verification) with SVG connection curves,
// live execution pulses, zoom/pan controls, and inspector synchronization.

import { useMemo, useState } from "react";
import type { ObjectiveRow, TaskRow } from "../api";
import { TaskStatusBadge } from "../design-system/primitives/Badge";
import { IconArtifacts, IconCheck, IconTasks, IconTerminal } from "./Icons";

interface StudioCanvasProps {
  objective: ObjectiveRow | null;
  tasks: TaskRow[];
  currentTaskId?: string | null;
  selectedNodeId?: string | null;
  onSelectNode: (nodeId: string, nodeType: "objective" | "task" | "verification") => void;
  isExecuting?: boolean;
}

interface NodeLayout {
  id: string;
  type: "objective" | "task" | "verification";
  title: string;
  subtitle?: string;
  status: string;
  x: number;
  y: number;
  width: number;
  height: number;
  data?: any;
}

export function StudioCanvas({
  objective,
  tasks,
  currentTaskId,
  selectedNodeId,
  onSelectNode,
  isExecuting = false,
}: StudioCanvasProps) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [isPanning, setIsPanning] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Calculate layout of nodes in a multi-layer workflow
  const { nodes, edges } = useMemo(() => {
    const nodeWidth = 240;
    const nodeHeight = 110;
    const layerGapX = 120;
    const itemGapY = 40;

    const nodeList: NodeLayout[] = [];
    const edgeList: Array<{ fromId: string; toId: string; status: string }> = [];

    if (!objective) return { nodes: nodeList, edges: edgeList };

    // Layer 0: Root Objective Node
    const rootX = 40;
    const rootY = 160;
    nodeList.push({
      id: "objective-root",
      type: "objective",
      title: objective.goal || "New Objective",
      subtitle: `Plan v${objective.plan_version || 1} • ${objective.status.toUpperCase()}`,
      status: objective.status,
      x: rootX,
      y: rootY,
      width: 250,
      height: 120,
      data: objective,
    });

    // Layer 1+: Tasks organized by dependencies or pipeline
    const taskLayers: TaskRow[][] = [];
    if (tasks.length === 0) {
      // Fallback empty placeholder task
      taskLayers.push([
        {
          id: "task-init",
          text: "Synthesizing execution plan...",
          status: objective.status === "completed" ? "COMPLETED" : "RUNNING",
          attempts: 1,
        },
      ]);
    } else {
      // Group tasks into layers: independent tasks first, then dependents
      const placed = new Set<string>();
      let remaining = [...tasks];

      while (remaining.length > 0) {
        const currentLayer = remaining.filter((t) => {
          if (!t.depends_on || t.depends_on.length === 0) return true;
          return t.depends_on.every((dep) => placed.has(dep));
        });

        if (currentLayer.length === 0) {
          // Break cyclic or unresolvable dependencies by taking the next item
          currentLayer.push(remaining[0]);
        }

        taskLayers.push(currentLayer);
        currentLayer.forEach((t) => placed.add(t.id));
        remaining = remaining.filter((t) => !placed.has(t.id));
      }
    }

    let currentX = rootX + 250 + layerGapX;
    taskLayers.forEach((layer, layerIdx) => {
      const totalHeight = layer.length * nodeHeight + (layer.length - 1) * itemGapY;
      const startY = Math.max(40, rootY + 60 - totalHeight / 2);

      layer.forEach((task, idx) => {
        const y = startY + idx * (nodeHeight + itemGapY);
        nodeList.push({
          id: task.id,
          type: "task",
          title: task.title || task.text || `Task #${idx + 1}`,
          subtitle: `Step ${layerIdx + 1}.${idx + 1} • Attempt ${task.attempts || 1}`,
          status: task.status,
          x: currentX,
          y,
          width: nodeWidth,
          height: nodeHeight,
          data: task,
        });

        // Add edges from dependencies or from root if first layer
        if (layerIdx === 0) {
          edgeList.push({
            fromId: "objective-root",
            toId: task.id,
            status: task.status,
          });
        } else if (task.depends_on && task.depends_on.length > 0) {
          task.depends_on.forEach((depId) => {
            edgeList.push({
              fromId: depId,
              toId: task.id,
              status: task.status,
            });
          });
        } else {
          // Connect to previous layer's first task
          const prevTask = taskLayers[layerIdx - 1]?.[0];
          if (prevTask) {
            edgeList.push({
              fromId: prevTask.id,
              toId: task.id,
              status: task.status,
            });
          }
        }
      });

      currentX += nodeWidth + layerGapX;
    });

    // Terminal Layer: Machine Verification Node
    const verifX = currentX;
    const verifY = rootY;
    nodeList.push({
      id: "verification-gate",
      type: "verification",
      title: "Ground-Truth Verification",
      subtitle:
        objective.status === "completed"
          ? "Deterministically Verified"
          : "Verification Gate Active",
      status: objective.status === "completed" ? "COMPLETED" : "PENDING",
      x: verifX,
      y: verifY,
      width: 240,
      height: 110,
      data: objective.verification,
    });

    // Connect last layer tasks to verification
    const lastLayer = taskLayers[taskLayers.length - 1] || [];
    lastLayer.forEach((t) => {
      edgeList.push({
        fromId: t.id,
        toId: "verification-gate",
        status: objective.status === "completed" ? "COMPLETED" : "PENDING",
      });
    });

    return { nodes: nodeList, edges: edgeList };
  }, [objective, tasks]);

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest(".studio-node") || (e.target as HTMLElement).closest(".studio-controls-bar")) {
      return;
    }
    setIsPanning(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsPanning(false);

  // Zoom controls
  const handleZoomIn = () => setZoom((z) => Math.min(1.8, Number((z + 0.15).toFixed(2))));
  const handleZoomOut = () => setZoom((z) => Math.max(0.4, Number((z - 0.15).toFixed(2))));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 40, y: 40 });
  };

  return (
    <div
      className="studio-canvas-container"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ cursor: isPanning ? "grabbing" : "grab" }}
    >
      {/* Floating Canvas Controls Toolbar (CrewAI Studio v2 style) */}
      <div className="studio-controls-bar">
        <button className="studio-tool-btn" onClick={handleZoomIn} title="Zoom In">
          +
        </button>
        <span className="studio-zoom-indicator font-mono">{Math.round(zoom * 100)}%</span>
        <button className="studio-tool-btn" onClick={handleZoomOut} title="Zoom Out">
          −
        </button>
        <div className="studio-tool-divider" />
        <button className="studio-tool-btn" onClick={handleReset} title="Reset View">
          ⛶ Fit
        </button>
      </div>

      {/* Interactive Canvas Plane with Zoom/Pan */}
      <div
        className="studio-canvas-plane"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: "0 0",
        }}
      >
        {/* SVG Edges Layer */}
        <svg className="studio-edges-layer">
          <defs>
            <linearGradient id="edge-gradient-running" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#eb6658" />
              <stop offset="100%" stopColor="#f59e0b" />
            </linearGradient>
            <linearGradient id="edge-gradient-done" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
          </defs>
          {edges.map((edge, idx) => {
            const fromNode = nodes.find((n) => n.id === edge.fromId);
            const toNode = nodes.find((n) => n.id === edge.toId);
            if (!fromNode || !toNode) return null;

            const startX = fromNode.x + fromNode.width;
            const startY = fromNode.y + fromNode.height / 2;
            const endX = toNode.x;
            const endY = toNode.y + toNode.height / 2;
            const deltaX = Math.max(60, (endX - startX) * 0.5);

            const isDone = edge.status.toUpperCase() === "COMPLETED";
            const isRun = edge.status.toUpperCase() === "RUNNING" || edge.status.toUpperCase() === "OBSERVING";

            const pathData = `M ${startX} ${startY} C ${startX + deltaX} ${startY}, ${endX - deltaX} ${endY}, ${endX} ${endY}`;

            return (
              <g key={`edge-${idx}`}>
                <path
                  d={pathData}
                  className={`studio-edge-curve ${isDone ? "edge-done" : isRun ? "edge-running" : "edge-pending"}`}
                  fill="none"
                  strokeWidth={isRun ? 2.5 : 1.8}
                />
              </g>
            );
          })}
        </svg>

        {/* Nodes Layer */}
        {nodes.map((node) => {
          const isSelected = selectedNodeId === node.id;
          const isCurrent = currentTaskId === node.id;
          const isDone = node.status.toUpperCase() === "COMPLETED";
          const isRun = node.status.toUpperCase() === "RUNNING" || node.status.toUpperCase() === "OBSERVING";

          return (
            <div
              key={node.id}
              className={`studio-node node-${node.type} ${isSelected ? "node-selected" : ""} ${
                isCurrent || isRun ? "node-running" : ""
              } ${isDone ? "node-completed" : ""}`}
              style={{
                left: node.x,
                top: node.y,
                width: node.width,
              }}
              onClick={() => onSelectNode(node.id, node.type)}
            >
              {/* Input Port Pin */}
              {node.type !== "objective" && <div className="node-port node-port-in" />}

              {/* Node Header */}
              <div className="node-header">
                <div className="node-type-badge">
                  {node.type === "objective" && <IconTasks size={12} />}
                  {node.type === "task" && <IconTerminal size={12} />}
                  {node.type === "verification" && <IconCheck size={12} />}
                  <span className="font-mono">{node.type.toUpperCase()}</span>
                </div>
                <TaskStatusBadge status={node.status} dot={isRun || isExecuting} />
              </div>

              {/* Node Title & Description */}
              <div className="node-body">
                <div className="node-title font-sans">{node.title}</div>
                {node.subtitle && <div className="node-subtitle font-mono">{node.subtitle}</div>}
              </div>

              {/* Node Footer / Metadata */}
              <div className="node-footer font-mono">
                {node.type === "task" && (
                  <span className="node-meta-item">
                    <IconArtifacts size={11} />
                    <span>Auto-Verifier Pin</span>
                  </span>
                )}
                {node.type === "objective" && (
                  <span className="node-meta-item" style={{ color: "var(--brand-coral)" }}>
                    ● Active Root
                  </span>
                )}
                {node.type === "verification" && (
                  <span
                    className="node-meta-item"
                    style={{ color: isDone ? "var(--emerald-verif)" : "var(--text-dim)" }}
                  >
                    {isDone ? "✓ Checks Passed" : "Pending Evaluation"}
                  </span>
                )}
              </div>

              {/* Output Port Pin */}
              {node.type !== "verification" && <div className="node-port node-port-out" />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
