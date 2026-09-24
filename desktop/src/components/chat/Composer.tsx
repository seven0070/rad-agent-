// Composer.tsx — Bottom composer area with slash pills, textarea, and run button.
import React from "react";
import { Button } from "../../design-system/primitives/Button";
import "./composer.css";

interface ComposerProps {
  inputPrompt: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  isSubmitting: boolean;
  modelName: string;
  profile: string;
  isInspectorOpen: boolean;
  onToggleInspector: () => void;
}

export const Composer: React.FC<ComposerProps> = ({
  inputPrompt,
  onInputChange,
  onSubmit,
  isSubmitting,
  modelName,
  profile,
  isInspectorOpen,
  onToggleInspector,
}) => {
  return (
    <footer className="chat-composer-area">
      <div className="slash-hints-bar">
        <button
          className="slash-pill"
          onClick={() =>
            onInputChange(
              "Perform a complete autonomous project audit of the RAD workspace. Generate a JSON machine-readable audit, a CSV metrics table, and a Markdown executive report. Validate every generated artifact independently."
            )
          }
        >
          /audit Complete Workspace Audit
        </button>
        <button
          className="slash-pill"
          onClick={() => onInputChange("/verify Level 1-5 multi-artifact integrity")}
        >
          /verify
        </button>
        <button
          className="slash-pill"
          onClick={() => onInputChange("/plan [Objective goal without auto-run]")}
        >
          /plan
        </button>
        <button
          className="slash-pill"
          onClick={() => {
            if (!isInspectorOpen) onToggleInspector();
          }}
        >
          /inspector Contextual Drawer
        </button>
      </div>

      <div className="composer-box">
        <textarea
          className="composer-textarea"
          placeholder="Instruct RAD autonomous agent (e.g. Audit workspace, replicate paper, run verification)..."
          value={inputPrompt}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
              e.preventDefault();
              onSubmit();
            }
          }}
        />

        <div className="composer-controls">
          <div className="composer-left-controls">
            <span className="font-mono fs-11 tc-dim">
              Model: {modelName}
            </span>
            <span className={`pill ${profile} fs-10`}>
              {profile}
            </span>
            <span className="inline-mid gap-4 fs-11 tc-dim">
              <i className="dot ok dot-5" />
              Checkpoint Journal ON
            </span>
          </div>

          <Button
            variant="primary"
            size="md"
            disabled={isSubmitting || !inputPrompt.trim()}
            onClick={onSubmit}
            loading={isSubmitting}
          >
            Run Objective ↵
          </Button>
        </div>
      </div>
    </footer>
  );
};
