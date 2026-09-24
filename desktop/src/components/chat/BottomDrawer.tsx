// BottomDrawer.tsx — Collapsible bottom AI thoughts & execution logs drawer (canvas mode).
import React, { useState } from "react";
import type { Artifact } from "../../api";
import { ToolCallPill, type ToolObservation } from "../ToolCallPill";
import "./bottom-drawer.css";
import "./reasoning-panel.css";

interface BottomDrawerProps {
  observations: ToolObservation[];
  artifacts: Artifact[];
  currentTaskTitle?: string;
}

export const BottomDrawer: React.FC<BottomDrawerProps> = ({
  observations,
  artifacts,
  currentTaskTitle,
}) => {
  const [isBottomDrawerOpen, setIsBottomDrawerOpen] = useState(false);

  return (
    <div
      className={`studio-bottom-drawer${isBottomDrawerOpen ? " is-open" : ""}`}
    >
      <div
        className="studio-bottom-handle"
        onClick={() => setIsBottomDrawerOpen((prev) => !prev)}
      >
        <div className="inline-mid gap-8 fs-12">
          <span className="tc-primary fs-13">⚡</span>
          <span className="fw-600">Execution Stream & Reasoning</span>
          {currentTaskTitle && (
            <span className="font-mono fs-11 tc-dim">
              • Active: {currentTaskTitle}
            </span>
          )}
          {observations.length > 0 && (
            <span className="thinking-meta-pill font-mono">{observations.length} tool calls</span>
          )}
          {artifacts.length > 0 && (
            <span className="thinking-meta-pill font-mono">{artifacts.length} artifacts</span>
          )}
        </div>
        <div className="inline-mid gap-8">
          <span className="font-mono tabular-nums fs-11 tc-dim">
            {isBottomDrawerOpen ? "Collapse ▼" : "Expand Logs ▲"}
          </span>
        </div>
      </div>

      {isBottomDrawerOpen && (
        <div className="studio-bottom-content">
          {observations.length > 0 ? (
            <div className="stack gap-6">
              {observations.slice(-6).map((obs, idx) => (
                <ToolCallPill key={obs.id || idx} obs={obs} />
              ))}
            </div>
          ) : (
            <div className="hint hint-center">
              Node graph active. Live tool execution logs will stream here during run.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
