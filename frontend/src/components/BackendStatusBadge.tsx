import React, { useEffect, useState, useCallback } from "react";
import { api, API_BASE_URL } from "@/lib/api";
import { cn } from "@/lib/utils";

interface BackendStatusBadgeProps {
  compact?: boolean;
  className?: string;
}

export const BackendStatusBadge: React.FC<BackendStatusBadgeProps> = ({
  compact = false,
  className,
}) => {
  const [online, setOnline] = useState<boolean | null>(null);
  const [latency, setLatency] = useState<number | null>(null);

  const checkStatus = useCallback(async () => {
    const start = performance.now();
    try {
      await api.getHealth();
      const end = performance.now();
      setLatency(Math.round(end - start));
      setOnline(true);
    } catch {
      setLatency(null);
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
    // Low-frequency polling: every 30s to avoid hammering backend
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, [checkStatus]);

  if (compact) {
    return (
      <div
        className={cn(
          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[10px] font-mono uppercase tracking-wider transition-colors",
          online === true &&
            "bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30",
          online === false &&
            "bg-fintech-crimson/10 text-fintech-crimson border border-fintech-crimson/30",
          online === null &&
            "bg-fintech-elevated text-fintech-muted border border-fintech-border",
          className
        )}
        title={`Backend: ${API_BASE_URL} ${latency ? `(${latency}ms)` : ""}`}
      >
        <span
          className={cn(
            "w-1.5 h-1.5 rounded-full",
            online === true && "bg-fintech-emerald animate-pulse",
            online === false && "bg-fintech-crimson",
            online === null && "bg-fintech-muted"
          )}
        />
        {online === true ? "ONLINE" : online === false ? "OFFLINE" : "CHECKING..."}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex items-center justify-between p-2.5 rounded bg-fintech-surface border border-fintech-border text-xs font-mono",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "w-2 h-2 rounded-full",
            online === true && "bg-fintech-emerald shadow-sm animate-pulse",
            online === false && "bg-fintech-crimson",
            online === null && "bg-fintech-muted"
          )}
        />
        <span className="text-white font-semibold">
          {online === true
            ? "RAZORMIND ENGINE ONLINE"
            : online === false
            ? "BACKEND OFFLINE"
            : "CHECKING SYSTEM..."}
        </span>
      </div>
      <div className="flex items-center gap-2 text-[11px] text-fintech-muted">
        {latency !== null && (
          <span className="text-fintech-cyan font-bold">{latency}ms</span>
        )}
        <button
          onClick={checkStatus}
          className="hover:text-white underline underline-offset-2 transition-colors"
        >
          Check
        </button>
      </div>
    </div>
  );
};
