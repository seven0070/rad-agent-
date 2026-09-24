// FlowCanvas.tsx — N2 DAG: Langflow/ComfyUI style for rad/control/graph.py
// Renders TaskGraph.to_flow() nodes/edges with draggable nodes, bezier edges,
// zoom/pan, and ComfyUI-like sockets. Inspired by langflow + comfyui node canvas.

import { useMemo, useState, useCallback } from "react";

export interface FlowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: { label: string; status: string; checks: number; depends_on: string[] };
  style?: { status: string };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  type: string;
}

interface FlowCanvasProps {
  nodes: FlowNode[];
  edges: FlowEdge[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
  onMoveNode?: (id: string, pos: { x: number; y: number }) => void;
}

const STATUS_COLOR: Record<string, string> = {
  PENDING: "#71717a",
  RUNNING: "#facc15",
  COMPLETED: "#22c55e",
  VERIFIED: "#22c55e",
  FAILED: "#ef4444",
  BLOCKED: "#ef4444",
  NEEDS_USER: "#f97316",
};

export function FlowCanvas({ nodes: initialNodes, edges, selectedId, onSelect, onMoveNode }: FlowCanvasProps) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 20, y: 20 });
  const [drag, setDrag] = useState<{ id: string; dx: number; dy: number } | null>(null);
  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>({});

  const nodes = useMemo(() => {
    return initialNodes.map((n) => ({
      ...n,
      position: positions[n.id] ?? n.position,
    }));
  }, [initialNodes, positions]);

  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);

  const handleNodeDown = useCallback(
    (e: React.MouseEvent, id: string) => {
      e.stopPropagation();
      const startX = e.clientX;
      const startY = e.clientY;
      const orig = nodeMap.get(id)?.position ?? { x: 0, y: 0 };
      const onMove = (ev: MouseEvent) => {
        const nx = orig.x + (ev.clientX - startX) / zoom;
        const ny = orig.y + (ev.clientY - startY) / zoom;
        setPositions((prev) => ({ ...prev, [id]: { x: nx, y: ny } }));
        setDrag({ id, dx: ev.clientX - startX, dy: ev.clientY - startY });
      };
      const onUp = () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
        const finalPos = positions[id] ?? orig;
        // Use latest from closure — read from DOM event not reliable, use stored
        setPositions((prev) => {
          const p = prev[id];
          if (p && onMoveNode) onMoveNode(id, p);
          return prev;
        });
        setDrag(null);
      };
      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp);
    },
    [nodeMap, zoom, positions, onMoveNode]
  );

  const zoomIn = () => setZoom((z) => Math.min(2, +(z + 0.15).toFixed(2)));
  const zoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.15).toFixed(2)));

  return (
    <div className="flow-canvas-root" style={{ position: "relative", width: "100%", height: 500, overflow: "hidden", background: "#0a0a0a", border: "1px solid #27272a", borderRadius: 10 }}>
      <div className="flow-controls" style={{ position: "absolute", top: 8, right: 8, zIndex: 10, display: "flex", gap: 6 }}>
        <button onClick={zoomOut} style={{ width: 28, height: 28, background: "#18181b", color: "#fafafa", border: "1px solid #27272a", borderRadius: 6 }}>-</button>
        <span style={{ fontSize: 11, color: "#a1a1aa", lineHeight: "28px", fontFamily: "monospace" }}>{Math.round(zoom * 100)}%</span>
        <button onClick={zoomIn} style={{ width: 28, height: 28, background: "#18181b", color: "#fafafa", border: "1px solid #27272a", borderRadius: 6 }}>+</button>
        <button onClick={() => { setPan({ x: 20, y: 20 }); setZoom(1); setPositions({}); }} style={{ padding: "0 8px", height: 28, background: "#18181b", color: "#fafafa", border: "1px solid #27272a", borderRadius: 6, fontSize: 11 }}>Fit</button>
      </div>

      <div
        className="flow-plane"
        style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: "0 0", position: "absolute", inset: 0 }}
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) {
            const sx = e.clientX - pan.x;
            const sy = e.clientY - pan.y;
            const startPan = { ...pan };
            const onMove = (ev: MouseEvent) => setPan({ x: startPan.x + ev.clientX - e.clientX, y: startPan.y + ev.clientY - e.clientY });
            const onUp = () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
            window.addEventListener("mousemove", onMove);
            window.addEventListener("mouseup", onUp);
          }
        }}
      >
        {/* SVG edges */}
        <svg style={{ position: "absolute", inset: 0, width: 2000, height: 1200, pointerEvents: "none" }}>
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#52525b" />
            </marker>
          </defs>
          {edges.map((ed) => {
            const a = nodeMap.get(ed.source);
            const b = nodeMap.get(ed.target);
            if (!a || !b) return null;
            const sx = a.position.x + 160;
            const sy = a.position.y + 36;
            const tx = b.position.x;
            const ty = b.position.y + 36;
            const dx = Math.max(40, (tx - sx) * 0.5);
            const d = `M ${sx} ${sy} C ${sx + dx} ${sy}, ${tx - dx} ${ty}, ${tx} ${ty}`;
            const col = STATUS_COLOR[b.data.status?.toUpperCase() ?? "PENDING"] ?? "#52525b";
            return <path key={ed.id} d={d} fill="none" stroke={col} strokeWidth={1.6} opacity={0.9} markerEnd="url(#arrow)" />;
          })}
        </svg>

        {/* Nodes */}
        {nodes.map((n) => {
          const isSel = selectedId === n.id;
          const col = STATUS_COLOR[n.data.status?.toUpperCase() ?? "PENDING"] ?? "#71717a";
          return (
            <div
              key={n.id}
              onMouseDown={(e) => handleNodeDown(e, n.id)}
              onClick={() => onSelect?.(n.id)}
              style={{
                position: "absolute",
                left: n.position.x,
                top: n.position.y,
                width: 160,
                minHeight: 72,
                background: isSel ? "#1f1f23" : "#18181b",
                border: `1.5px solid ${isSel ? "#fafafa" : "#27272a"}`,
                borderLeft: `3px solid ${col}`,
                borderRadius: 8,
                padding: "8px 10px",
                cursor: "grab",
                userSelect: "none",
                boxShadow: isSel ? "0 0 0 2px rgba(250,250,250,0.08)" : "0 4px 12px rgba(0,0,0,0.4)",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 600, color: "#fafafa", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{n.id}</div>
              <div style={{ fontSize: 11, color: "#a1a1aa", marginTop: 4, lineHeight: 1.3, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{n.data.label}</div>
              <div style={{ marginTop: 6, display: "flex", gap: 6, alignItems: "center" }}>
                <span style={{ fontSize: 9, padding: "2px 6px", borderRadius: 10, background: col, color: "#0a0a0a", fontWeight: 700, fontFamily: "monospace" }}>{n.data.status}</span>
                {n.data.checks > 0 && <span style={{ fontSize: 9, color: "#71717a", fontFamily: "monospace" }}>{n.data.checks} checks</span>}
              </div>
              {/* ComfyUI sockets */}
              <div style={{ position: "absolute", left: -6, top: 32, width: 10, height: 10, borderRadius: 5, background: "#52525b", border: "2px solid #0a0a0a" }} />
              <div style={{ position: "absolute", right: -6, top: 32, width: 10, height: 10, borderRadius: 5, background: col, border: "2px solid #0a0a0a" }} />
            </div>
          );
        })}
      </div>

      {/* Langflow-style minimap */}
      <div style={{ position: "absolute", bottom: 8, left: 8, width: 120, height: 80, background: "#18181b", border: "1px solid #27272a", borderRadius: 6, opacity: 0.7 }}>
        <div style={{ padding: 6, fontSize: 8, color: "#52525b", fontFamily: "monospace" }}>MINIMAP</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 2, padding: "0 6px" }}>
          {nodes.slice(0, 12).map((n) => (
            <div key={n.id} style={{ width: 18, height: 10, background: STATUS_COLOR[n.data.status?.toUpperCase() ?? "PENDING"] ?? "#27272a", borderRadius: 2 }} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default FlowCanvas;
