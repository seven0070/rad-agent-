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
    READY: { color: "var(--text-secondary)", border: "var(--border-card)", bg: "rgba(255, 255, 255, 0.04)", dotColor: "var(--text-secondary)" },
    RUNNING: { color: "var(--text-primary)", border: "var(--border-active)", bg: "rgba(255, 255, 255, 0.08)", dotColor: "#f4f4f5" },
    OBSERVING: { color: "var(--text-secondary)", border: "var(--border-card)", bg: "rgba(255, 255, 255, 0.04)", dotColor: "var(--text-muted)" },
    VERIFYING: { color: "var(--text-primary)", border: "var(--border-card)", bg: "rgba(255, 255, 255, 0.05)", dotColor: "#ffffff" },
    COMPLETED: { color: "#e4e4e7", border: "rgba(255, 255, 255, 0.16)", bg: "rgba(255, 255, 255, 0.06)", dotColor: "#10b981" },
    FAILED: { color: "#fca5a5", border: "rgba(244, 63, 94, 0.35)", bg: "rgba(244, 63, 94, 0.08)", dotColor: "var(--rose-danger)" },
    RETRYING: { color: "var(--text-secondary)", border: "var(--border-card)", bg: "rgba(255, 255, 255, 0.04)", dotColor: "var(--text-muted)" },
    BLOCKED: { color: "#fca5a5", border: "rgba(244, 63, 94, 0.35)", bg: "rgba(244, 63, 94, 0.08)", dotColor: "var(--rose-danger)" },
    NEEDS_USER: { color: "var(--text-primary)", border: "var(--border-active)", bg: "rgba(255, 255, 255, 0.08)", dotColor: "#ffffff" },
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
