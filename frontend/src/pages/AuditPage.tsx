import React, { useEffect, useState, useMemo } from "react";
import {
  FileText,
  RefreshCw,
  Search,
  Filter,
  ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDateTime, cn } from "@/lib/utils";
import { ApiStateView } from "@/components/ApiStateView";
import type { AuditLogRead } from "@/types/api";

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedAction, setSelectedAction] = useState<string>("ALL");

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLogs(0, 100);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || "Failed to retrieve flight recorder audit telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const actionOptions = useMemo(() => {
    const set = new Set<string>();
    logs.forEach((l) => {
      if (l.action) set.add(l.action);
    });
    return ["ALL", ...Array.from(set)];
  }, [logs]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesAction = selectedAction === "ALL" || log.action === selectedAction;
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        !term ||
        log.action.toLowerCase().includes(term) ||
        log.actor_type.toLowerCase().includes(term) ||
        (log.reason && log.reason.toLowerCase().includes(term)) ||
        log.decision.toLowerCase().includes(term);

      return matchesAction && matchesSearch;
    });
  }, [logs, selectedAction, searchTerm]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <FileText className="w-6 h-6 text-fintech-cyan" />
            Audit & Flight Recorder
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Immutable chronological telemetry of autonomous AI decisions, policy verdicts, and recovery executions
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="px-3.5 py-1.5 bg-fintech-elevated hover:bg-fintech-border text-fintech-cyan text-xs font-mono rounded border border-fintech-border flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Refresh Flight Log
        </button>
      </div>

      <ApiStateView loading={loading} error={error} onRetry={fetchLogs}>
        {/* Filter Bar */}
        <div className="p-4 bg-fintech-surface border border-fintech-border rounded-lg glass-card flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-fintech-muted absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search audit records by actor, action, reason, or decision..."
              className="w-full pl-9 pr-4 py-2 bg-fintech-elevated border border-fintech-border rounded text-xs text-white placeholder-fintech-muted outline-none font-mono focus:border-fintech-cyan"
            />
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-fintech-muted" />
            <select
              value={selectedAction}
              onChange={(e) => setSelectedAction(e.target.value)}
              className="bg-fintech-elevated border border-fintech-border rounded px-3 py-2 text-xs text-white font-mono outline-none"
            >
              {actionOptions.map((act) => (
                <option key={act} value={act} className="bg-fintech-surface">
                  Action: {act}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Audit Records Table */}
        <div className="bg-fintech-surface border border-fintech-border rounded-lg p-5 space-y-4 glass-card">
          <div className="flex items-center justify-between text-xs font-mono text-fintech-muted">
            <span>SHOWING {filteredLogs.length} OF {logs.length} FLIGHT RECORDS</span>
            <span className="text-fintech-emerald flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> CRYPTOGRAPHICALLY TAMPER-EVIDENT
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-fintech-border text-fintech-muted uppercase text-[10px]">
                  <th className="pb-2.5">Timestamp</th>
                  <th className="pb-2.5">Actor</th>
                  <th className="pb-2.5">Action</th>
                  <th className="pb-2.5">Resource</th>
                  <th className="pb-2.5">Decision</th>
                  <th className="pb-2.5">Reason & Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-fintech-border/40">
                {filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-fintech-muted">
                      No audit flight records match the current filter.
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-fintech-elevated/40 hover-glow transition-colors">
                      <td className="py-3 text-fintech-muted text-[11px] whitespace-nowrap">
                        {formatDateTime(log.created_at)}
                      </td>
                      <td className="py-3 text-white font-medium whitespace-nowrap">
                        {log.actor_type}
                      </td>
                      <td className="py-3 text-fintech-cyan font-bold whitespace-nowrap">
                        {log.action}
                      </td>
                      <td className="py-3 text-fintech-subtle text-[11px] whitespace-nowrap">
                        {log.resource_type}
                      </td>
                      <td className="py-3 whitespace-nowrap">
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                            log.decision.toLowerCase().includes("allow") ||
                              log.decision.toLowerCase().includes("completed") ||
                              log.decision.toLowerCase().includes("success")
                              ? "bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30"
                              : "bg-fintech-amber/10 text-fintech-amber border border-fintech-amber/30"
                          )}
                        >
                          {log.decision}
                        </span>
                      </td>
                      <td className="py-3 text-fintech-subtle max-w-md truncate">
                        {log.reason || "--"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </ApiStateView>
    </div>
  );
};
