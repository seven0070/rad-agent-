/** Task graph layout. Pure display math over backend task data — the frontend
 *  never schedules; the controller's ready-set is authoritative. */

import type { TaskRow } from "./api";

export interface GNode {
  id: string;
  task: TaskRow;
  depth: number;
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface GEdge {
  from: string;
  to: string;
  active: boolean;
}

export interface GraphLayout {
  nodes: GNode[];
  edges: GEdge[];
  width: number;
  height: number;
}

const NODE_W = 172;
const NODE_H = 56;
const GAP_X = 46;
const GAP_Y = 14;
const PAD = 16;

/** Layer = longest dependency chain ending at the task (deps first, left to right). */
export function layoutTasks(tasks: TaskRow[]): GraphLayout {
  const byId = new Map<string, TaskRow>(tasks.map((t) => [t.id, t]));
  const depth = new Map<string, number>();

  const compute = (id: string, seen: Set<string>): number => {
    if (depth.has(id)) return depth.get(id)!;
    if (seen.has(id)) return 0; // cycle guard — backend plans are DAGs
    seen.add(id);
    const t = byId.get(id);
    let d = 0;
    if (t && t.depends_on) {
      for (const dep of t.depends_on) {
        if (byId.has(dep)) d = Math.max(d, compute(dep, seen) + 1);
      }
    }
    seen.delete(id);
    depth.set(id, d);
    return d;
  };
  for (const t of tasks) compute(t.id, new Set());

  const columns = new Map<number, string[]>();
  for (const t of tasks) {
    const d = depth.get(t.id) ?? 0;
    const col = columns.get(d) ?? [];
    col.push(t.id);
    columns.set(d, col);
  }
  // stable vertical order: task id (matches backend order)
  for (const col of columns.values()) col.sort();

  const nodes: GNode[] = [];
  const maxRows = Math.max(1, ...[...columns.values()].map((c) => c.length));
  for (const [d, ids] of [...columns.entries()].sort((a, b) => a[0] - b[0])) {
    const colH = ids.length * NODE_H + (ids.length - 1) * GAP_Y;
    const totalH = maxRows * NODE_H + (maxRows - 1) * GAP_Y;
    const offsetY = (totalH - colH) / 2;
    ids.forEach((id, i) => {
      nodes.push({
        id,
        task: byId.get(id)!,
        depth: d,
        x: PAD + d * (NODE_W + GAP_X),
        y: PAD + offsetY + i * (NODE_H + GAP_Y),
        w: NODE_W,
        h: NODE_H,
      });
    });
  }
  const pos = new Map(nodes.map((n) => [n.id, n]));
  const edges: GEdge[] = [];
  for (const t of tasks) {
    for (const dep of t.depends_on || []) {
      if (pos.has(dep)) edges.push({ from: dep, to: t.id, active: true });
    }
  }
  const width = PAD * 2 + (Math.max(0, nodes.length) ? [...columns.keys()].length : 1) * NODE_W +
    (Math.max(0, [...columns.keys()].length - 1)) * GAP_X;
  const height = PAD * 2 + maxRows * NODE_H + (maxRows - 1) * GAP_Y;
  return { nodes, edges, width: Math.max(width, 320), height: Math.max(height, 160) };
}
