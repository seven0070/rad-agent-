// RunProgressHeader.tsx — Active run status, stepped progress, and controls.

import type { ObjectiveRow } from "../api";
import { ObjectiveStatusBadge } from "../design-system/primitives/Badge";
import { ProgressBar } from "../design-system/primitives/ProgressBar";
import { Button } from "../design-system/primitives/Button";

interface RunProgressHeaderProps {
  objective: ObjectiveRow | null;
  tasksCount: number;
  completedTasksCount: number;
  currentTaskTitle?: string;
  isInspectorOpen: boolean;
  onToggleInspector: () => void;
  onAction: (action: "pause" | "resume" | "cancel") => void;
}

export function RunProgressHeader({
  objective,
  tasksCount,
  completedTasksCount,
  currentTaskTitle,
  isInspectorOpen,
  onToggleInspector,
  onAction,
}: RunProgressHeaderProps) {
  if (!objective) {
    return (
      <header className="session-header">
        <div className="session-header-left">
          <div className="rad-logo-mark sm">
            RAD
          </div>
          <span className="session-title">RAD Agent Cockpit</span>
          <span className="badge fs-11 tc-dim">
            IDLE
          </span>
        </div>
      </header>
    );
  }

  const isRunning = ["running", "planning"].includes(objective.status.toLowerCase());
  const isPaused = objective.status.toLowerCase() === "paused";

  return (
    <header className="session-header run-progress-header">
      <div className="session-header-left">
        <div className="rad-logo-mark sm">
          RAD
        </div>
        <div className="run-header-titles">
          <div className="inline-mid gap-8">
            <span className="session-title">{objective.goal}</span>
            <ObjectiveStatusBadge status={objective.status} />
            <span className="font-mono run-id-pill">
              {objective.id.slice(0, 10)}
            </span>
          </div>

          {currentTaskTitle && isRunning && (
            <div className="run-active-task-hint">
              <span className="live-pulse-dot" />
              <span>In-flight: <b>{currentTaskTitle}</b></span>
            </div>
          )}
        </div>
      </div>

      <div className="session-header-actions">
        {tasksCount > 0 && (
          <div className="run-progress-meter-wrapper">
            <ProgressBar
              current={completedTasksCount}
              total={tasksCount}
              showLabel
              variant={objective.status === "completed" ? "emerald" : "indigo"}
            />
          </div>
        )}

        {isRunning && (
          <>
            <Button
              variant="ghost"
              size="mini"
              onClick={() => onAction("pause")}
              title="Pause execution"
            >
              ❚❚ Pause
            </Button>
            <Button
              variant="danger"
              size="mini"
              onClick={() => onAction("cancel")}
              title="Cancel run"
            >
              ✕ Stop
            </Button>
          </>
        )}

        {isPaused && (
          <Button
            variant="primary"
            size="mini"
            onClick={() => onAction("resume")}
            title="Resume execution"
          >
            ▶ Resume
          </Button>
        )}

        <Button
          variant="ghost"
          size="mini"
          onClick={onToggleInspector}
          className={isInspectorOpen ? "active" : ""}
          title="Toggle Contextual Inspector Drawer"
        >
          {isInspectorOpen ? "◨ Inspector [On]" : "◨ Inspector"}
        </Button>
      </div>
    </header>
  );
}
