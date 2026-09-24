// Card.tsx — Liquid-glass container primitive with 1px border refraction.

import type { HTMLAttributes, ReactNode } from "react";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  interactive?: boolean;
  active?: boolean;
}

export function Card({
  children,
  interactive = false,
  active = false,
  className = "",
  style,
  ...props
}: CardProps) {
  const interactiveClass = interactive ? "card-interactive" : "";
  const activeClass = active ? "card-active" : "";

  return (
    <div
      className={`card ${interactiveClass} ${activeClass} ${className}`.trim()}
      style={style} // DYNAMIC-STYLE: caller pass-through prop
      {...props}
    >
      {children}
    </div>
  );
}
