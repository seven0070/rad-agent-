// Badge.tsx — Semantic status pills for Tasks, Objectives, and Authority.

import type { HTMLAttributes, ReactNode } from "react";
import type { TaskState } from "../../util";

export interface StatusBadgeProps extends HTMLAttributes<HTMLSpanElement> {
  status: string;
  dot?: boolean;
  children?: ReactNode;
}

const statusClass: Record<string, string> = {
  PENDING: "ts-pending",
  READY: "ts-ready",
  RUNNING: "ts-running",
  OBSERVING: "ts-observing",
  VERIFYING: "ts-verifying",
  COMPLETED: "ts-completed",
  FAILED: "ts-failed",
  RETRYING: "ts-retrying",
  BLOCKED: "ts-blocked",
  NEEDS_USER: "ts-needs-user",
  CANCELLED: "ts-cancelled",
};

export function TaskStatusBadge({ status, dot = true, children, className = "", ...props }: StatusBadgeProps) {
  const s = (status || "PENDING").toUpperCase() as TaskState;
  const sc = statusClass[s] || statusClass.PENDING;

  return (
    <span className={`chip font-mono ${sc} ${className}`.trim()} {...props}>
      {dot && <span className={`chip-dot ${sc}`} />}
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
