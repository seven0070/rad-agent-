// tokens.ts — Design System Tokens for RAD Studio (Light Grey & Black Minimalist Aesthetic).
// High-contrast monochromatic theme, neutral dark charcoal surfaces, crisp light grey accents,
// monospace metrics, dot-grid canvas, 8-point spatial discipline.

export const TOKENS = {
  colors: {
    // Canvas & Surface Hierarchy (Light Grey & Black Minimalist Theme)
    bgCanvas: "var(--bg-canvas, #09090b)",
    bgSurface: "var(--bg-surface, #111114)",
    bgCard: "var(--bg-card, #17171a)",
    bgCardHover: "var(--bg-card-hover, #1f1f23)",
    bgElevated: "var(--bg-elevated, #26262b)",

    // Borders & Hairline Strokes
    borderSubtle: "var(--border-subtle, #222226)",
    borderCard: "var(--border-card, #2d2d33)",
    borderActive: "var(--border-active, #45454f)",
    strokeLiquidGlass: "rgba(255, 255, 255, 0.08)",

    // Typography (High-contrast Light Grey & White)
    textPrimary: "var(--text-primary, #f4f4f5)",
    textSecondary: "var(--text-secondary, #a1a1aa)",
    textMuted: "var(--text-muted, #71717a)",
    textDim: "var(--text-dim, #52525b)",

    // Signature Light Grey & Monochrome Brand Accents
    brandCoral: "var(--brand-coral, #f4f4f5)",
    brandCoralHover: "var(--brand-coral-hover, #ffffff)",
    brandCoralActive: "var(--brand-coral-active, #e4e4e7)",
    brandCoralGlow: "rgba(255, 255, 255, 0.12)",

    // Visual Node Accents (Sleek Dark Greys)
    nodeTask: "#17171a",
    nodeAgent: "#1a1a1e",
    nodeRouter: "#1c1c20",
    nodeVerification: "#161619",

    // Semantic Status (Subtle & Refined)
    emerald: "var(--emerald-verif, #10b981)",
    amber: "var(--rad-amber, #d4d4d8)",
    rose: "var(--rose-danger, #f87171)",
    sky: "var(--sky-info, #cbd5e1)",
    indigo: "var(--rad-indigo, #f4f4f5)",
  },

  radii: {
    xs: "4px",
    sm: "6px",
    md: "10px",
    lg: "14px",
    pill: "9999px",
  },

  shadows: {
    liquidGlass: "inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 4px 24px -2px rgba(0, 0, 0, 0.6)",
    glowCoral: "0 0 20px rgba(255, 255, 255, 0.15)",
    glowEmerald: "0 0 20px rgba(16, 185, 129, 0.2)",
    nodeShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6)",
  },

  transitions: {
    fast: "150ms cubic-bezier(0.16, 1, 0.3, 1)",
    normal: "200ms cubic-bezier(0.16, 1, 0.3, 1)",
  },
} as const;
