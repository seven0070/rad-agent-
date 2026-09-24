// TaskStateMatrix.tsx — Visual state transition matrix and DAG inspector for RAD Tasks.
// Maps the exact deterministic state machine:
// PENDING → READY → RUNNING → OBSERVING → VERIFYING → COMPLETED

import type { TaskRow } from "../api";
import { TaskStatusBadge } from "../design-system/primitives/Badge";
import { IconCheck, IconAlert } from "./Icons";
import { fmtTime } from "../util";

interface TaskStateMatrixProps {
  tasks: TaskRow[];
  currentTaskId?: string | null;
  onSelectTask?: (taskId: string) => void;
}

const LIFECYCLE_STEPS = ["PENDING", "READY", "RUNNING", "OBSERVING", "VERIFYING", "COMPLETED"];

export function TaskStateMatrix({ tasks, currentTaskId, onSelectTask }: TaskStateMatrixProps) {
  if (tasks.length === 0) {
    return (
      <div className="task-matrix-empty font-mono">
        <span className="dot off dot-6" />
        <span>No tasks generated yet (planning phase active)</span>
      </div>
    );
  }

  return (
    <div className="task-matrix-container">
      <div className="task-matrix-header font-mono">
        <span className="hint">TASK EXECUTION MATRIX ({tasks.length} tasks)</span>
        <span className="hint">DAG STATE TRANSITIONS</span>
      </div>

      <div className="task-matrix-list">
        {tasks.map((task, idx) => {
          const isCurrent = currentTaskId === task.id;
          const status = (task.status || "PENDING").toUpperCase();
          const isComplete = status === "COMPLETED";
          const isFailed = status === "FAILED" || status === "BLOCKED";
          const currentStepIdx = LIFECYCLE_STEPS.indexOf(status);

          return (
            <div
              key={task.id || idx}
              className={`task-matrix-row ${isCurrent ? "active-task" : ""}`}
              onClick={() => onSelectTask?.(task.id)}
            >
              {/* Left Task Identification */}
              <div className="task-matrix-meta">
                <div className="inline-mid gap-6">
                  <span className="font-mono task-id-tag">
                    #{idx + 1} [{task.id.slice(0, 8)}]
                  </span>
                  <TaskStatusBadge status={task.status} />
                </div>
                <div className="task-title-text">{task.text || task.title || task.goal}</div>
                {task.depends_on && task.depends_on.length > 0 && (
                  <div className="task-deps-tag font-mono">
                    deps: {task.depends_on.map((d) => d.slice(0, 6)).join(", ")}
                  </div>
                )}
              </div>

              {/* State Machine Step Pipeline */}
              <div className="task-pipeline-track">
                {LIFECYCLE_STEPS.map((step, stepIdx) => {
                  const isPast = stepIdx <= currentStepIdx && !isFailed;
                  const isCurrentStep = stepIdx === currentStepIdx;
                  return (
                    <div
                      key={step}
                      className={`pipeline-step-dot ${isPast ? "done" : ""} ${
                        isCurrentStep ? "current" : ""
                      } ${isFailed && isCurrentStep ? "failed" : ""}`}
                      title={`${step} ${isCurrentStep ? "(Current)" : isPast ? "(Passed)" : "(Pending)"}`}
                    />
                  );
                })}
              </div>

              {/* Checks & Verifications Summary */}
              {task.checks && task.checks.length > 0 && (
                <div className="task-checks-summary font-mono">
                  {task.checks.map((chk, cIdx) => (
                    <span
                      key={cIdx}
                      className={`check-mini-pill ${isComplete ? "passed" : isFailed ? "failed" : ""}`}
                      title={chk.description || `${chk.kind}(${JSON.stringify(chk.args || {})})`}
                    >
                      {isComplete ? <IconCheck size={10} /> : isFailed ? <IconAlert size={10} /> : "○"}
                      <span>{chk.kind}</span>
                    </span>
                  ))}
                </div>
              )}

              {/* Timestamps */}
              {task.finished && (
                <span className="task-time-tag font-mono tabular-nums">
                  {fmtTime(task.finished)}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
