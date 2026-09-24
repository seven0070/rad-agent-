// ArtifactList.tsx — Generated artifact announcement cards with inspect action.
import React from "react";
import type { Artifact } from "../../api";
import { fmtBytes, shortHash } from "../../util";
import { IconArtifacts } from "../Icons";
import { Button } from "../../design-system/primitives/Button";

interface ArtifactListProps {
  artifacts: Artifact[];
  isInspectorOpen: boolean;
  onToggleInspector: () => void;
  onSelectArtifact: (artifactId: string) => void;
}

export const ArtifactList: React.FC<ArtifactListProps> = ({
  artifacts,
  isInspectorOpen,
  onToggleInspector,
  onSelectArtifact,
}) => {
  if (artifacts.length === 0) return null;

  return (
    <div className="stack gap-8 mt-6">
      <div className="fs-11 tc-dim fw-600">
        GENERATED ARTIFACTS ({artifacts.length})
      </div>
      {artifacts.map((a) => {
        const parts = a.location.split(/[\\/]/);
        const fname = parts[parts.length - 1];

        return (
          <div key={a.id} className="artifact-announcement-card">
            <div className="artifact-info">
              <div className="artifact-icon">
                <IconArtifacts size={18} />
              </div>
              <div>
                <div className="artifact-name font-mono">{fname}</div>
                <div className="artifact-sub font-mono tabular-nums">
                  <span>{fmtBytes(a.size)}</span>
                  <span>•</span>
                  <span>SHA: {shortHash(a.sha256, 10)}</span>
                  <span>•</span>
                  <span className="tc-verif">v{a.version} verified</span>
                </div>
              </div>
            </div>
            <Button
              variant="ghost"
              size="mini"
              onClick={() => {
                if (!isInspectorOpen) onToggleInspector();
                onSelectArtifact(a.id);
              }}
            >
              Inspect Code →
            </Button>
          </div>
        );
      })}
    </div>
  );
};
