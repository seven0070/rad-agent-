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

  const variantColors: Record<string, string> = {
    indigo: "var(--rad-indigo)",
    emerald: "var(--emerald-verif)",
    amber: "var(--rad-amber)",
    rose: "var(--rose-danger)",
  };

  const fillColor = variantColors[variant] || variantColors.indigo;

  return (
    <div className={`progress-bar-container ${className}`.trim()} {...props}>
      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{
            width: `${pct}%`,
            backgroundColor: fillColor,
            boxShadow: `0 0 8px ${fillColor}`,
          }}
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
