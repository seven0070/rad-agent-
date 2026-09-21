// Button.tsx — Primitive Button with tactile push feedback and spring transition.

import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "mini";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: ReactNode;
  children?: ReactNode;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  icon,
  children,
  loading = false,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  const variantClass =
    variant === "primary"
      ? "btn-primary"
      : variant === "secondary"
        ? "btn-secondary"
        : variant === "danger"
          ? "btn-danger"
          : "ghost";

  const sizeClass = size === "mini" || size === "sm" ? "mini" : "";

  return (
    <button
      className={`btn ${variantClass} ${sizeClass} ${className}`.trim()}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="dot ok spin" style={{ width: 6, height: 6, marginRight: 6 }} />
      ) : icon ? (
        <span style={{ display: "inline-flex", alignItems: "center", marginRight: children ? 6 : 0 }}>
          {icon}
        </span>
      ) : null}
      {children}
    </button>
  );
}
