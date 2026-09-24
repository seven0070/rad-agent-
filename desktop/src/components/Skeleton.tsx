// Skeleton.tsx — Reusable loading skeleton for async surfaces.
// Zero layout shifts (CLS = 0) with a subtle dark theme shimmer.

import type { HTMLAttributes, CSSProperties } from "react";

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  radius?: string | number;
  className?: string;
}

export function Skeleton({
  width = "100%",
  height = "1rem",
  radius,
  className = "",
  style,
  ...props
}: SkeletonProps) {
  const customStyle: CSSProperties = {
    width,
    height,
    borderRadius: radius ?? "var(--radius-sm)",
    ...style,
  }; // DYNAMIC-STYLE: width/height/radius props

  return (
    <div
      className={`skeleton ${className}`}
      style={customStyle}
      aria-hidden="true"
      {...props}
    />
  );
}

export function SkeletonCard({
  lines = 3,
  className = "",
}: {
  lines?: number;
  className?: string;
}) {
  return (
    <div className={`card skeleton-container ${className}`} aria-busy="true">
      <Skeleton width="40%" height="20px" className="mb-14" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? "60%" : "100%"}
          height="14px"
          className="mb-8"
        />
      ))}
    </div>
  );
}

export function SkeletonMetricsRow({ count = 4 }: { count?: number }) {
  return (
    <div className="metrics-row" aria-busy="true">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton
          key={i}
          width="130px"
          height="32px"
          radius="var(--radius-sm)"
        />
      ))}
    </div>
  );
}
