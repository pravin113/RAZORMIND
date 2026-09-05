import React from "react";
import { AlertTriangle, RefreshCw, ServerOff, Database } from "lucide-react";

interface ApiStateViewProps {
  loading?: boolean;
  loadingMessage?: string;
  error?: string | null;
  onRetry?: () => void;
  empty?: boolean;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  children: React.ReactNode;
}

export const ApiStateView: React.FC<ApiStateViewProps> = ({
  loading = false,
  loadingMessage = "SYNCING FINANCIAL DATA WITH RAZORMIND ENGINE...",
  error = null,
  onRetry,
  empty = false,
  emptyMessage = "No financial records found in current view.",
  emptyIcon,
  children,
}) => {
  if (loading) {
    return (
      <div className="p-12 rounded-lg border border-fintech-border bg-fintech-surface flex flex-col items-center justify-center text-center space-y-4 min-h-[260px] animate-pulse">
        <div className="w-10 h-10 rounded-full bg-fintech-cyan/10 border border-fintech-cyan/30 flex items-center justify-center text-fintech-cyan">
          <RefreshCw className="w-5 h-5 animate-spin" />
        </div>
        <div className="space-y-1">
          <div className="text-xs font-mono uppercase tracking-widest text-fintech-cyan font-bold">
            CONNECTING TO RAZORMIND
          </div>
          <p className="text-xs text-fintech-subtle font-mono">{loadingMessage}</p>
        </div>
      </div>
    );
  }

  if (error) {
    const isNetworkError =
      error.toLowerCase().includes("network") ||
      error.toLowerCase().includes("unable to connect") ||
      error.toLowerCase().includes("connection");

    return (
      <div className="p-8 rounded-lg border border-fintech-crimson/30 bg-fintech-crimson/5 flex flex-col items-center justify-center text-center space-y-4 min-h-[260px]">
        <div className="w-12 h-12 rounded-full bg-fintech-crimson/10 border border-fintech-crimson/30 flex items-center justify-center text-fintech-crimson">
          {isNetworkError ? <ServerOff className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
        </div>
        <div className="space-y-1 max-w-md">
          <div className="text-sm font-mono uppercase tracking-wider text-fintech-crimson font-bold">
            {isNetworkError ? "BACKEND UNAVAILABLE" : "FINANCIAL TELEMETRY ERROR"}
          </div>
          <p className="text-xs text-fintech-subtle font-mono break-words">{error}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-fintech-surface hover:bg-fintech-elevated border border-fintech-border hover:border-fintech-cyan text-white text-xs font-mono uppercase tracking-wider rounded transition-all flex items-center gap-2 shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5 text-fintech-cyan" />
            Retry Connection
          </button>
        )}
      </div>
    );
  }

  if (empty) {
    return (
      <div className="p-10 rounded-lg border border-fintech-border bg-fintech-surface flex flex-col items-center justify-center text-center space-y-3 min-h-[200px]">
        <div className="w-10 h-10 rounded-full bg-fintech-elevated border border-fintech-border flex items-center justify-center text-fintech-muted">
          {emptyIcon || <Database className="w-5 h-5" />}
        </div>
        <div className="space-y-1">
          <div className="text-xs font-mono uppercase tracking-wider text-white font-semibold">
            EMPTY TELEMETRY
          </div>
          <p className="text-xs text-fintech-muted font-mono">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
