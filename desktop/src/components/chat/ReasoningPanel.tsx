// ReasoningPanel.tsx — Collapsible Agent Reasoning & Planning trace accordion.
import React, { useState } from "react";
import type { LiveView, TaskRow } from "../../api";

interface ReasoningPanelProps {
  live: LiveView | null;
  trace: unknown;
  tasks: TaskRow[];
  completedTasks: number;
  modelName: string;
}

type TraceShape = {
  objective?: { plan_version?: number };
} | null | undefined;

export const ReasoningPanel: React.FC<ReasoningPanelProps> = ({
  live,
  trace,
  tasks,
  completedTasks,
  modelName,
}) => {
  const [isReasoningOpen, setIsReasoningOpen] = useState(false);
  const traceObj = (trace as TraceShape)?.objective;

  return (
    <div className="thinking-accordion">
      <div
        className="thinking-header"
        onClick={() => setIsReasoningOpen((prev) => !prev)}
        role="button"
        tabIndex={0}
        aria-expanded={isReasoningOpen}
      >
        <div className="inline-mid gap-8">
          <span className="tc-amber">✦</span>
          <span className="fw-600">Agent Reasoning & Planning</span>
        </div>
        <div className="inline-mid gap-6">
          <span className="thinking-meta-pill font-mono">
            Plan v{live?.plan_version || traceObj?.plan_version || 1}
          </span>
          <span className="thinking-meta-pill font-mono">
            {tasks.length > 0 ? `${completedTasks}/${tasks.length} tasks` : "Planning"}
          </span>
          <span className="thinking-meta-pill font-mono">
            {modelName}
          </span>
          <span className="fs-11 tc-dim ml-4">
            {isReasoningOpen ? "▲" : "▼"}
          </span>
        </div>
      </div>

      {isReasoningOpen && (
        <div className="thinking-content">
          {live?.current_task && (
            <div className="mb-10 tc-indigo-light">
              ▶ Active Task: <strong>{live.current_task.text}</strong> ({live.current_task.status}, attempt {live.current_task.attempts || 1})
            </div>
          )}

          {tasks.length > 0 ? (
            <div className="stack gap-6">
              <div className="fs-11 tc-dim fw-600">
                TASK GRAPH BREAKDOWN:
              </div>
              {tasks.map((t, idx) => (
                <div
                  key={t.id || idx}
                  className="inline-mid gap-8 fs-12 py-2-0"
                >
                  <span
                    className={
                      t.status === "COMPLETED"
                        ? "tc-verif"
                        : t.status === "FAILED"
                          ? "tc-danger"
                          : "tc-amber"
                    }
                  >
                    {t.status === "COMPLETED" ? "✓" : t.status === "FAILED" ? "✕" : "○"}
                  </span>
                  <span className="font-mono tc-dim">
                    [{t.id.slice(0, 8)}]
                  </span>
                  <span
                    className={t.status === "COMPLETED" ? "tc-secondary" : "tc-primary"}
                  >
                    {t.text || t.title}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div>Initializing tasks and analyzing objective constraints…</div>
          )}
        </div>
      )}
    </div>
  );
};
