// WelcomeScreen.tsx — Workbench welcome card with quick-prompt starters.
import React from "react";

interface WelcomeScreenProps {
  onQuickPrompt: (prompt: string) => void;
}

const QUICK_PROMPTS = [
  {
    label: "Complete Autonomous Project Audit",
    desc: "Inspect RAD workspace files and generate JSON/CSV/Markdown reports with verification proof.",
    prompt: "Perform a complete autonomous project audit of the RAD workspace. Generate a JSON machine-readable audit, a CSV metrics table, and a Markdown executive report. Validate every generated artifact independently.",
  },
  {
    label: "Verify System & Artifact Integrity",
    desc: "Execute Level 1-5 checks on file existence, minimum size, hashes, and schema validity.",
    prompt: "Verify all workspace artifacts and generate independent Level 1-5 verification proof.",
  },
  {
    label: "Inspect Checkpoint Sequence",
    desc: "Validate state machine transitions, journal seq, and rollback consistency.",
    prompt: "Audit checkpoint sequences, verify journal digests, and inspect state transitions.",
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onQuickPrompt }) => {
  return (
    <div className="workbench-welcome-card">
      <div className="rad-logo-mark lg">
        RAD
      </div>
      <div>
        <h2 className="fs-18 fw-700 m-0 mb-6 tc-primary">
          RAD Autonomous Execution Workbench
        </h2>
        <p className="lead mw-520 mx-auto tc-muted">
          Deterministic Python control plane with task DAG planning, progressive tool inspection,
          and ground-truth machine verification.
        </p>
      </div>

      <div className="workbench-quick-prompts">
        {QUICK_PROMPTS.map((item, i) => (
          <div
            key={i}
            className="card card-interactive text-left cursor-pointer mb-0"
            onClick={() => onQuickPrompt(item.prompt)}
          >
            <div className="fw-600 fs-13 tc-indigo-light">
              ✦ {item.label}
            </div>
            <div className="fs-12 tc-dim mt-2">
              {item.desc}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
