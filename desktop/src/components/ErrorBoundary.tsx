// ErrorBoundary.tsx — Accessible and robust error boundary for RAD Desktop.
// Catches render exceptions, displays technical details, and offers clean recovery.

import { Component, type ErrorInfo, type ReactNode } from "react";
import { IconAlert, IconRefresh } from "./Icons";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an unhandled error:", error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="page" role="alert">
          <div className="error-boundary-card">
            <div className="error-boundary-header">
              <IconAlert size={20} className="icon-alert" />
              <h3>{this.props.fallbackTitle || "Surface Rendering Error"}</h3>
            </div>
            <p className="error-boundary-message">
              {this.state.error?.message || "An unexpected error occurred while rendering this surface."}
            </p>
            {this.state.error?.stack && (
              <pre className="error-boundary-stack">
                {this.state.error.stack.split("\n").slice(0, 5).join("\n")}
              </pre>
            )}
            <div className="error-boundary-actions">
              <button className="btn" onClick={this.handleReset}>
                <IconRefresh size={13} className="mr-6" />
                Try Re-rendering
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
