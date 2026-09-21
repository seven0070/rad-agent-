// tokens.ts — Design System Tokens for RAD Desktop.
// Strictly anti-slop: neutral charcoal/slate base, single calibrated indigo accent,
// 1px liquid-glass refraction, monospace data numbers, 8-point spatial discipline.

export const TOKENS = {
  colors: {
    // Canvas & Surface Hierarchy
    bgCanvas: "var(--bg-canvas, #090a0f)",
    bgSurface: "var(--bg-surface, #10131c)",
    bgCard: "var(--bg-card, #151924)",
    bgCardHover: "var(--bg-card-hover, #1c2232)",
    bgElevated: "var(--bg-elevated, #222a3d)",

    // Borders & Liquid-Glass Strokes
    borderSubtle: "var(--border-subtle, #1e2433)",
    borderCard: "var(--border-card, #283042)",
    borderActive: "var(--border-active, #3b465e)",
    strokeLiquidGlass: "rgba(255, 255, 255, 0.08)",

    // Typography
    textPrimary: "var(--text-primary, #f8fafc)",
    textSecondary: "var(--text-secondary, #cbd5e1)",
    textMuted: "var(--text-muted, #94a3b8)",
    textDim: "var(--text-dim, #64748b)",

    // Accents & Brand
    indigo: "var(--rad-indigo, #6366f1)",
    indigoLight: "var(--rad-indigo-light, #818cf8)",
    indigoGlow: "var(--rad-indigo-glow, rgba(99, 102, 241, 0.22))",

    // Semantic Status
    emerald: "var(--emerald-verif, #10b981)",
    amber: "var(--rad-amber, #f59e0b)",
    rose: "var(--rose-danger, #f43f5e)",
    sky: "var(--sky-info, #0ea5e9)",
  },

  radii: {
    xs: "4px",
    sm: "6px",
    md: "10px",
    lg: "14px",
    pill: "9999px",
  },

  shadows: {
    liquidGlass: "inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 4px 20px -2px rgba(0, 0, 0, 0.4)",
    glowIndigo: "0 0 16px rgba(99, 102, 241, 0.22)",
    glowEmerald: "0 0 16px rgba(16, 185, 129, 0.22)",
  },

  transitions: {
    fast: "150ms cubic-bezier(0.16, 1, 0.3, 1)",
    normal: "200ms cubic-bezier(0.16, 1, 0.3, 1)",
  },
} as const;
