// tokens.ts — Design System Tokens for RAD Studio v2 (CrewAI Studio v2 aesthetic).
// High-contrast dark theme, signature coral accent (#eb6658), visual node graph tokens,
// monospace metrics, dot-grid canvas, 8-point spatial discipline.

export const TOKENS = {
  colors: {
    // Canvas & Surface Hierarchy (CrewAI Studio v2 Dark Theme)
    bgCanvas: "var(--bg-canvas, #0a0c10)",
    bgSurface: "var(--bg-surface, #12151d)",
    bgCard: "var(--bg-card, #181c26)",
    bgCardHover: "var(--bg-card-hover, #1f2533)",
    bgElevated: "var(--bg-elevated, #252c3d)",

    // Borders & Liquid-Glass Strokes
    borderSubtle: "var(--border-subtle, #1d222e)",
    borderCard: "var(--border-card, #272e3f)",
    borderActive: "var(--border-active, #3a455c)",
    strokeLiquidGlass: "rgba(255, 255, 255, 0.08)",

    // Typography
    textPrimary: "var(--text-primary, #fcfcfc)",
    textSecondary: "var(--text-secondary, #cbd5e1)",
    textMuted: "var(--text-muted, #94a3b8)",
    textDim: "var(--text-dim, #64748b)",

    // CrewAI Studio v2 Signature Brand Accents (Coral / Vermilion)
    brandCoral: "var(--brand-coral, #eb6658)",
    brandCoralHover: "var(--brand-coral-hover, #de594c)",
    brandCoralActive: "var(--brand-coral-active, #d04b3f)",
    brandCoralGlow: "rgba(235, 102, 88, 0.25)",

    // Visual Node Accents
    nodeTask: "#1c2130",
    nodeAgent: "#192338",
    nodeRouter: "#2b2219",
    nodeVerification: "#142922",

    // Semantic Status
    emerald: "var(--emerald-verif, #10b981)",
    amber: "var(--rad-amber, #f59e0b)",
    rose: "var(--rose-danger, #f43f5e)",
    sky: "var(--sky-info, #38bdf8)",
    indigo: "var(--rad-indigo, #818cf8)",
  },

  radii: {
    xs: "4px",
    sm: "6px",
    md: "10px",
    lg: "14px",
    pill: "9999px",
  },

  shadows: {
    liquidGlass: "inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 4px 24px -2px rgba(0, 0, 0, 0.5)",
    glowCoral: "0 0 20px rgba(235, 102, 88, 0.3)",
    glowEmerald: "0 0 20px rgba(16, 185, 129, 0.25)",
    nodeShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
  },

  transitions: {
    fast: "150ms cubic-bezier(0.16, 1, 0.3, 1)",
    normal: "200ms cubic-bezier(0.16, 1, 0.3, 1)",
  },
} as const;
