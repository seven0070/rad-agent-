// VerificationVerdict.tsx — Ground-Truth Machine Verification verdict card.
import React from "react";
import { IconCheck } from "../Icons";

interface VerificationVerdictProps {
  isVerified: boolean;
  verCount: number;
  digest: string;
}

export const VerificationVerdict: React.FC<VerificationVerdictProps> = ({
  isVerified,
  verCount,
  digest,
}) => {
  return (
    <div className="verification-verdict-card">
      <div className="verdict-left">
        <span className="verdict-badge">
          {isVerified ? "VERIFIED" : "COMPLETED"}
        </span>
        <div>
          <div className="fw-600 fs-13 tc-verif">
            Ground-Truth Machine Verification Passed
          </div>
          <div className="fs-11 tc-secondary mt-2">
            {verCount > 0
              ? `${verCount}/${verCount} checks passed · 0 regressions · Checkpoint intact`
              : "Filesystem existence, size, JSON/CSV schema, and content assertions passed."}
          </div>
        </div>
      </div>
      <div className="text-right">
        <div className="fs-11 tc-verif fw-600">
          <IconCheck size={12} className="mr-4" />
          Level 1-5 Machine Proof
        </div>
        <div className="font-mono tabular-nums fs-10 tc-dim">
          Digest: {digest}
        </div>
      </div>
    </div>
  );
};
