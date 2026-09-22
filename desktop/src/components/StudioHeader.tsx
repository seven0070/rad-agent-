// StudioHeader.tsx — CrewAI Studio v2 style header toolbar for RAD Agent.
// Features breadcrumbs, view mode toggles, execution controls, progress bar, and export actions.

import { useState } from "react";
import type { ObjectiveRow } from "../api";
import { Button } from "../design-system/primitives/Button";
import { ProgressBar } from "../design-system/primitives/ProgressBar";

interface StudioHeaderProps {
  objective: ObjectiveRow | null;
  totalTasks: number;
  completedTasks: number;
  viewMode: "canvas" | "feed";
  onChangeViewMode: (mode: "canvas" | "feed") => void;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
  onExportCode?: (format: "python" | "yaml" | "json") => void;
  onOpenSettings?: () => void;
}

export function StudioHeader({
  objective,
  totalTasks,
  completedTasks,
  viewMode,
  onChangeViewMode,
  onPause,
  onResume,
  onStop,
  onExportCode,
  onOpenSettings,
}: StudioHeaderProps) {
  const [showExport, setShowExport] = useState(false);

  const percent =
    totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
  const isRunning =
    objective?.status === "running" || objective?.status === "planning";

  return (
    <header className="studio-header">
      {/* Left: Breadcrumbs & Mode Toggle */}
      <div className="studio-header-left">
        <div className="studio-breadcrumbs font-mono">
          <span className="crumb-root">RAD Studio</span>
          <span className="crumb-sep">/</span>
          <span className="crumb-version">v2</span>
          <span className="crumb-sep">/</span>
          <span className="crumb-title font-sans">
            {objective?.goal ? objective.goal : "Select or Create an Objective"}
          </span>
        </div>

        {/* View Mode Switcher */}
        <div className="studio-view-toggle">
          <button
            className={`view-toggle-btn ${viewMode === "canvas" ? "active" : ""}`}
            onClick={() => onChangeViewMode("canvas")}
            title="Visual Workflow Canvas"
          >
            <span>☊ Canvas</span>
          </button>
          <button
            className={`view-toggle-btn ${viewMode === "feed" ? "active" : ""}`}
            onClick={() => onChangeViewMode("feed")}
            title="Execution Feed & Observations"
          >
            <span>≡ Stream</span>
          </button>
        </div>
      </div>

      {/* Right: Progress Meter, Execution Controls & Export */}
      <div className="studio-header-right">
        {objective && (
          <div className="studio-progress-box font-mono">
            <span className="studio-progress-label">
              {completedTasks}/{totalTasks} tasks ({percent}%)
            </span>
            <div style={{ width: 100 }}>
              <ProgressBar current={completedTasks} total={totalTasks || 1} />
            </div>
          </div>
        )}

        {/* Action Controls (CrewAI Studio v2 style) */}
        <div className="studio-actions-group">
          {isRunning ? (
            <Button variant="secondary" size="sm" onClick={onPause} title="Pause Run">
              ⏸ Pause
            </Button>
          ) : (
            <Button variant="primary" size="sm" onClick={onResume} title="Resume Run">
              ▶ Run
            </Button>
          )}

          <Button variant="danger" size="sm" onClick={onStop} title="Stop Run">
            ⏹ Stop
          </Button>

          {/* Export Code Dropdown */}
          <div style={{ position: "relative" }}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowExport((v) => !v)}
              title="Export Workflow to Code"
            >
              Export ▾
            </Button>

            {showExport && (
              <div className="studio-export-menu font-mono">
                <button
                  className="export-item"
                  onClick={() => {
                    setShowExport(false);
                    onExportCode?.("python");
                  }}
                >
                  <span>🐍 Python (`crew.py`)</span>
                </button>
                <button
                  className="export-item"
                  onClick={() => {
                    setShowExport(false);
                    onExportCode?.("yaml");
                  }}
                >
                  <span>📄 YAML (`tasks.yaml`)</span>
                </button>
                <button
                  className="export-item"
                  onClick={() => {
                    setShowExport(false);
                    onExportCode?.("json");
                  }}
                >
                  <span>📦 JSON DAG Specification</span>
                </button>
              </div>
            )}
          </div>

          {/* Settings / Connection Button */}
          <button
            className="icon-button"
            onClick={onOpenSettings}
            title="Configure Connection & Settings"
            style={{ width: 32, height: 32 }}
          >
            ⚙
          </button>
        </div>
      </div>
    </header>
  );
}
