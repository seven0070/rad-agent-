// WebConnectionModal.tsx — Connection configuration dialog for RAD Web UI.
// Allows browser users to configure API endpoint and Bearer Token.

import { useState } from "react";
import { RadClient } from "../api";
import { getStoredConnection, saveStoredConnection } from "../backend";
import { Button } from "../design-system/primitives/Button";
import { Card } from "../design-system/primitives/Card";
import { IconCheck, IconAlert } from "./Icons";

interface WebConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (base: string, token: string) => Promise<void>;
  currentBase?: string;
  currentToken?: string;
}

export function WebConnectionModal({
  isOpen,
  onClose,
  onConnect,
  currentBase,
  currentToken,
}: WebConnectionModalProps) {
  const stored = getStoredConnection();
  const [base, setBase] = useState(
    currentBase || stored.base || import.meta.env.VITE_RAD_API || "http://127.0.0.1:7331",
  );
  const [token, setToken] = useState(
    currentToken || stored.token || import.meta.env.VITE_RAD_TOKEN || "",
  );
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [connecting, setConnecting] = useState(false);

  if (!isOpen) return null;

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const cleanBase = base.replace(/\/$/, "");
      const testClient = new RadClient(cleanBase, token.trim());
      const data = await testClient.health();
      if (data.ok) {
        setTestResult({
          ok: true,
          message: `Connected successfully! RAD Agent v${data.version || "0.2.0"} is online.`,
        });
      } else {
        setTestResult({
          ok: false,
          message: "Health check returned false status",
        });
      }
    } catch (e) {
      setTestResult({
        ok: false,
        message: e instanceof Error ? e.message : "Connection failed. Is `rad serve` running?",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveAndConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    try {
      saveStoredConnection(base, token);
      await onConnect(base, token);
      onClose();
    } catch (err) {
      setTestResult({
        ok: false,
        message: err instanceof Error ? err.message : "Failed to connect",
      });
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="web-modal-backdrop">
      <Card className="web-modal-card">
        <div className="web-modal-header">
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>Web Client Connection</h3>
              <span className="badge-platform font-mono">RUST + JS</span>
            </div>
            <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 4 }}>
              Connect your browser frontend to the RAD Agent control plane.
            </div>
          </div>
          <button className="icon-button" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        <form onSubmit={handleSaveAndConnect} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label className="field-label">Agent API Base URL</label>
            <input
              type="text"
              className="field-input font-mono"
              value={base}
              onChange={(e) => setBase(e.target.value)}
              placeholder="http://127.0.0.1:7331"
              required
            />
            <div className="field-hint">
              Default loopback port is <code>7331</code> (or Rust proxy on <code>3000</code>).
            </div>
          </div>

          <div>
            <label className="field-label">API Bearer Token</label>
            <input
              type="password"
              className="field-input font-mono"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste ~/.rad/api.token here..."
            />
            <div className="field-hint">
              Found at <code>~/.rad/api.token</code> or printed in terminal via <code>rad serve</code>.
            </div>
          </div>

          {testResult && (
            <div
              className={`test-result-box ${testResult.ok ? "test-result-ok" : "test-result-err"}`}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {testResult.ok ? <IconCheck size={14} /> : <IconAlert size={14} />}
                <span style={{ fontWeight: 600 }}>{testResult.ok ? "Success" : "Connection Error"}</span>
              </div>
              <div style={{ marginTop: 4 }}>{testResult.message}</div>
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleTest}
              loading={testing}
            >
              Test Connection
            </Button>
            <div style={{ display: "flex", gap: 8 }}>
              <Button type="button" variant="ghost" size="sm" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={connecting}
              >
                Save & Connect
              </Button>
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
}
