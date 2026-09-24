// ChatFeed.tsx — Execution feed surface: goal bubble, reasoning, observations, artifacts, verdict.
import { forwardRef } from "react";
import type { Artifact, LiveView, ObjectiveRow, TaskRow } from "../../api";
import { fmtTime } from "../../util";
import { ToolCallPill, type ToolObservation } from "../ToolCallPill";
import { WelcomeScreen } from "./WelcomeScreen";
import { ReasoningPanel } from "./ReasoningPanel";
import { ArtifactList } from "./ArtifactList";
import { VerificationVerdict } from "./VerificationVerdict";
import "./chat-feed.css";

interface ChatFeedProps {
  objective: ObjectiveRow | null;
  onQuickPrompt: (prompt: string) => void;
  live: LiveView | null;
  trace: unknown;
  observations: ToolObservation[];
  artifacts: Artifact[];
  tasks: TaskRow[];
  completedTasks: number;
  modelName: string;
  isInspectorOpen: boolean;
  onToggleInspector: () => void;
  onSelectArtifact: (artifactId: string) => void;
  isVerified: boolean;
  verCount: number;
  digest: string;
}

export const ChatFeed = forwardRef<HTMLDivElement, ChatFeedProps>(
  (
    {
      objective,
      onQuickPrompt,
      live,
      trace,
      observations,
      artifacts,
      tasks,
      completedTasks,
      modelName,
      isInspectorOpen,
      onToggleInspector,
      onSelectArtifact,
      isVerified,
      verCount,
      digest,
    },
    ref,
  ) => {
    return (
      <div className="chat-feed" ref={ref}>
        {!objective ? (
          <WelcomeScreen onQuickPrompt={onQuickPrompt} />
        ) : (
          <>
            {/* Operator Goal Bubble */}
            <div className="chat-msg-user">
              <div className="chat-bubble-user">
                <div
                  className="fs-11 tc-indigo-light fw-600 mb-4 row no-wrap justify-between"
                >
                  <span>OBJECTIVE GOAL</span>
                  <span className="font-mono tabular-nums tc-dim">
                    {fmtTime(objective.created || 0)}
                  </span>
                </div>
                <div className="pre-wrap">{objective.goal}</div>
              </div>
            </div>

            {/* Agent Execution Flow */}
            <div className="chat-msg-agent">
              {/* Level 1: Collapsible Reasoning & Planning Trace */}
              <ReasoningPanel
                live={live}
                trace={trace}
                tasks={tasks}
                completedTasks={completedTasks}
                modelName={modelName}
              />

              {/* Level 1: Tool Observations (Progressive Disclosure via ToolCallPill) */}
              {observations.length > 0 && (
                <div className="stack gap-6">
                  <div className="fs-11 tc-dim fw-600 mt-4">
                    TOOL OBSERVATIONS ({observations.length})
                  </div>
                  {observations.map((obs, idx) => (
                    <ToolCallPill key={obs.id || idx} obs={obs} />
                  ))}
                </div>
              )}

              {/* Level 1: Generated Artifact Cards */}
              <ArtifactList
                artifacts={artifacts}
                isInspectorOpen={isInspectorOpen}
                onToggleInspector={onToggleInspector}
                onSelectArtifact={onSelectArtifact}
              />

              {/* Ground-Truth Verification Verdict Card */}
              {objective.status === "completed" && (
                <VerificationVerdict
                  isVerified={isVerified}
                  verCount={verCount}
                  digest={digest}
                />
              )}
            </div>
          </>
        )}
      </div>
    );
  },
);

ChatFeed.displayName = "ChatFeed";
