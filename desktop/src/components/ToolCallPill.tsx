// ToolCallPill.tsx — Progressive disclosure for Tool Observations.
// Level 1: Compact inline pill with tool name, arguments hint, and latency.
// Level 2: Expandable drawer/card with full input parameters and output text.

import { useState } from "react";
import { redactText } from "../util";
import { IconCheck, IconAlert } from "./Icons";

export interface ToolObservation {
  id?: string;
  task_id?: string;
  tool: string;
  args?: Record<string, unknown> | string;
  status: string;
  duration_ms?: number;
  output?: string;
  artifacts?: string[];
  at?: number;
}

export function ToolCallPill({ obs }: { obs: ToolObservation }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isOk = obs.status === "ok" || obs.status === "completed" || obs.status === "SUCCESS";
  const isErr = obs.status === "failed" || obs.status === "error" || obs.status === "FAILED";

  // Parse args string representation for quick summary
  let argsSummary = "";
  if (obs.args) {
    if (typeof obs.args === "object") {
      const keys = Object.keys(obs.args);
      if (keys.length === 1) {
        argsSummary = String((obs.args as Record<string, unknown>)[keys[0]]);
      } else {
        argsSummary = JSON.stringify(obs.args);
      }
    } else {
      argsSummary = String(obs.args);
    }
  }

  return (
    <div className={`tool-call-card ${isExpanded ? "expanded" : ""}`}>
      <div
        className="tool-card-header"
        onClick={() => setIsExpanded((prev) => !prev)}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsExpanded((prev) => !prev);
          }
        }}
      >
        <div className="tool-title-group">
          <span
            className={`inline-mid ${
              isOk ? "tc-verif" : isErr ? "tc-danger" : "tc-amber"
            }`}
          >
            {isOk ? <IconCheck size={13} /> : isErr ? <IconAlert size={13} /> : "●"}
          </span>
          <span className="tool-name-badge">tool:{obs.tool}</span>
          {argsSummary && (
            <span className="tool-args-preview font-mono">
              {argsSummary}
            </span>
          )}
        </div>

        <div className="tool-meta-actions">
          {obs.duration_ms !== undefined && (
            <span className="tool-duration-tag font-mono tabular-nums">
              {obs.duration_ms}ms
            </span>
          )}
          <span className="tool-disclosure-toggle font-mono">
            {isExpanded ? "▲ Hide" : "▼ Inspect"}
          </span>
        </div>
      </div>

      {isExpanded && (
        <div className="tool-card-body">
          {obs.args && (
            <div className="tool-card-args font-mono">
              <span className="hint">INPUT ARGUMENTS:</span>
              <pre>{JSON.stringify(obs.args, null, 2)}</pre>
            </div>
          )}
          <div className="tool-card-output font-mono">
            <span className="hint">OUTPUT / RESULT:</span>
            <pre>{obs.output ? redactText(obs.output) : "[Tool completed with 0 errors]"}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
