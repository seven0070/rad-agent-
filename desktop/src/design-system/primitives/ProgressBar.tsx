// ProgressBar.tsx — Stepped task progress and budget utilization indicator.

import type { HTMLAttributes } from "react";

export interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  current: number;
  total: number;
  variant?: "indigo" | "emerald" | "amber" | "rose";
  showLabel?: boolean;
}

export function ProgressBar({
  current,
  total,
  variant = "indigo",
  showLabel = false,
  className = "",
  ...props
}: ProgressBarProps) {
  const pct = total > 0 ? Math.min(100, Math.max(0, Math.round((current / total) * 100))) : 0;

  const variantClass: Record<string, string> = {
    indigo: "pb-indigo",
    emerald: "pb-emerald",
    amber: "pb-amber",
    rose: "pb-rose",
  };

  const fillClass = variantClass[variant] || variantClass.indigo;

  return (
    <div className={`progress-bar-container ${className}`.trim()} {...props}>
      <div className="progress-bar-track">
        <div
          className={`progress-bar-fill ${fillClass}`}
          style={{ width: `${pct}%` }} // DYNAMIC-STYLE: computed pct
        />
      </div>
      {showLabel && (
        <span className="progress-bar-label font-mono tabular-nums">
          {current}/{total} ({pct}%)
        </span>
      )}
    </div>
  );
}
