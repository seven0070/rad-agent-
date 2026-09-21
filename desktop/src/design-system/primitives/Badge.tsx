// Badge.tsx — Semantic status pills for Tasks, Objectives, and Authority.

import type { HTMLAttributes, ReactNode } from "react";
import type { TaskState } from "../../util";

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: string;
  dot?: boolean;
  children?: ReactNode;
}

export function TaskStatusBadge({ status, dot = true, children, className = "", ...props }: StatusBadgeProps) {
  const s = (status || "PENDING").toUpperCase() as TaskState;

  const colorMap: Record<string, { color: string; border: string; bg: string; dotColor: string }> = {
    PENDING: { color: "var(--text-dim)", border: "var(--border-subtle)", bg: "var(--bg-canvas)", dotColor: "var(--text-dim)" },
    READY: { color: "var(--sky-info)", border: "rgba(14, 165, 233, 0.3)", bg: "rgba(14, 165, 233, 0.08)", dotColor: "var(--sky-info)" },
    RUNNING: { color: "var(--rad-indigo-light)", border: "rgba(99, 102, 241, 0.4)", bg: "rgba(99, 102, 241, 0.12)", dotColor: "var(--rad-indigo-light)" },
    OBSERVING: { color: "var(--rad-amber)", border: "rgba(245, 158, 11, 0.3)", bg: "rgba(245, 158, 11, 0.08)", dotColor: "var(--rad-amber)" },
    VERIFYING: { color: "var(--sky-info)", border: "rgba(14, 165, 233, 0.3)", bg: "rgba(14, 165, 233, 0.08)", dotColor: "var(--sky-info)" },
    COMPLETED: { color: "var(--emerald-verif)", border: "rgba(16, 185, 129, 0.4)", bg: "rgba(16, 185, 129, 0.12)", dotColor: "var(--emerald-verif)" },
    FAILED: { color: "var(--rose-danger)", border: "rgba(244, 63, 94, 0.4)", bg: "rgba(244, 63, 94, 0.12)", dotColor: "var(--rose-danger)" },
    RETRYING: { color: "var(--rad-amber)", border: "rgba(245, 158, 11, 0.4)", bg: "rgba(245, 158, 11, 0.12)", dotColor: "var(--rad-amber)" },
    BLOCKED: { color: "var(--rose-danger)", border: "rgba(244, 63, 94, 0.4)", bg: "rgba(244, 63, 94, 0.12)", dotColor: "var(--rose-danger)" },
    NEEDS_USER: { color: "var(--rad-amber)", border: "rgba(245, 158, 11, 0.4)", bg: "rgba(245, 158, 11, 0.12)", dotColor: "var(--rad-amber)" },
    CANCELLED: { color: "var(--text-muted)", border: "var(--border-subtle)", bg: "var(--bg-canvas)", dotColor: "var(--text-muted)" },
  };

  const scheme = colorMap[s] || colorMap.PENDING;

  return (
    <span
      className={`chip font-mono ${className}`.trim()}
      style={{
        color: scheme.color,
        borderColor: scheme.border,
        backgroundColor: scheme.bg,
      }}
      {...props}
    >
      {dot && (
        <span
          className="dot"
          style={{
            backgroundColor: scheme.dotColor,
            boxShadow: `0 0 6px ${scheme.dotColor}`,
            width: 6,
            height: 6,
          }}
        />
      )}
      {children || s}
    </span>
  );
}

export function ObjectiveStatusBadge({ status, className = "", ...props }: { status: string; className?: string }) {
  const s = (status || "pending").toLowerCase();
  const isOk = s === "completed";
  const isFail = s === "failed" || s === "cancelled";
  const isRun = s === "running" || s === "planning";

  return (
    <span
      className={`badge ${
        isOk ? "b-ok" : isFail ? "b-bad" : isRun ? "os-running" : "b-warn"
      } font-mono ${className}`.trim()}
      {...props}
    >
      {status.toUpperCase()}
    </span>
  );
}
