import React, { useEffect, useState } from "react";
import {
  RefreshCw,
  Play,
  CheckCircle2,
  Sliders,
  DollarSign,
  Cpu,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatINR, formatPercentage, formatDateTime, cn } from "@/lib/utils";
import { ApiStateView } from "@/components/ApiStateView";
import type {
  RecoveryOpportunityRead,
  RecoveryOutcomeRead,
  RecoverySummary,
  WorkflowExecuteResponse,
} from "@/types/api";

const WORKFLOW_STEPS = [
  "OBSERVE",
  "DETECT",
  "INVESTIGATE",
  "DECIDE",
  "POLICY GATE",
  "ACT",
  "VERIFY",
  "AUDIT",
  "LEARN",
];

export const RevenueRecoveryPage: React.FC = () => {
  const [opportunities, setOpportunities] = useState<RecoveryOpportunityRead[]>([]);
  const [outcomes, setOutcomes] = useState<RecoveryOutcomeRead[]>([]);
  const [summary, setSummary] = useState<RecoverySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [activeStepIndex, setActiveStepIndex] = useState<number>(-1);
  const [lastExecution, setLastExecution] = useState<WorkflowExecuteResponse | null>(null);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [opps, sum, outc] = await Promise.all([
        api.getRecoveryOpportunities(0, 50).catch(() => []),
        api.getRecoverySummary().catch(() => null),
        api.getRecoveryOutcomes(undefined, 0, 10).catch(() => []),
      ]);
      setOpportunities(opps);
      setSummary(sum);
      setOutcomes(outc);
    } catch (err: any) {
      setError(err.message || "Failed to load recovery telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleExecute = async (opp: RecoveryOpportunityRead) => {
    setTriggeringId(opp.id);
    setLastExecution(null);
    setActiveStepIndex(0);

    // Simulate animated step progression through the 9-step loop
    const stepInterval = setInterval(() => {
      setActiveStepIndex((prev) => {
        if (prev >= 4) {
          clearInterval(stepInterval);
          return 4; // Pause at POLICY GATE
        }
        return prev + 1;
      });
    }, 150);

    try {
      const res = await api.executeRecoveryWorkflow({
        merchant_id: "24858aff-1023-4415-9df6-58d8c5495fdd",
        transaction_id: opp.transaction_id,
        opportunity_id: opp.id,
        dry_run: false,
      });

      clearInterval(stepInterval);
      setActiveStepIndex(8); // Completed through LEARN
      setLastExecution(res);
      fetchAllData();
    } catch (e: any) {
      clearInterval(stepInterval);
      setActiveStepIndex(-1);
      setError(e.message || "Workflow execution failed");
    } finally {
      setTriggeringId(null);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <DollarSign className="w-6 h-6 text-fintech-cyan" />
            Autonomous Revenue Recovery Orchestrator
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Deterministic 9-step recovery loop governing payment retries and customer outreach
          </p>
        </div>

        <button
          onClick={fetchAllData}
          disabled={loading}
          className="px-3.5 py-1.5 bg-fintech-elevated hover:bg-fintech-border text-fintech-cyan text-xs font-mono rounded border border-fintech-border flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Refresh Pipeline
        </button>
      </div>

      <ApiStateView loading={loading} error={error} onRetry={fetchAllData}>
        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 stagger-children">
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover">
            <div className="text-xs font-mono text-fintech-muted uppercase">Total Opportunities</div>
            <div className="text-2xl font-bold text-white">
              {summary?.total_opportunities ?? opportunities.length}
            </div>
            <div className="text-[11px] font-mono text-fintech-cyan">
              {summary?.open_opportunities ?? opportunities.length} open for recovery
            </div>
          </div>

          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover">
            <div className="text-xs font-mono text-fintech-muted uppercase">Expected Recoverable</div>
            <div className="text-2xl font-bold text-fintech-emerald tabular-nums">
              {formatINR(summary?.expected_recovered_value ?? 0)}
            </div>
            <div className="text-[11px] font-mono text-fintech-subtle">
              Deterministic yield floor: 65%
            </div>
          </div>

          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover">
            <div className="text-xs font-mono text-fintech-muted uppercase">Average Probability</div>
            <div className="text-2xl font-bold text-white tabular-nums">
              {formatPercentage(summary?.average_recovery_probability ?? 0.72)}
            </div>
            <div className="text-[11px] font-mono text-fintech-muted">ML model inference (LightGBM)</div>
          </div>
        </div>

        {/* 9-Step Pipeline Visualization */}
        <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-fintech-cyan" />
              <h2 className="text-xs font-mono uppercase tracking-widest text-white font-bold">
                9-Step Autonomous Orchestration Engine
              </h2>
            </div>
            <div className="text-[11px] font-mono text-fintech-cyan flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5" />
              <span>AI proposes. Policy decides.</span>
            </div>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-2 text-center">
            {WORKFLOW_STEPS.map((step, idx) => {
              const isActive = activeStepIndex === idx;
              const isPast = activeStepIndex > idx;
              const isPolicyGate = step === "POLICY GATE";

              return (
                <div
                  key={step}
                  className={cn(
                    "p-2.5 rounded border text-[11px] font-mono font-semibold transition-all relative",
                    isPolicyGate && "border-fintech-cyan/40 bg-fintech-cyan/5",
                    isActive &&
                      "border-fintech-cyan bg-fintech-cyan/20 text-white shadow-fintech-glow animate-pulse",
                    isPast && "border-fintech-emerald/50 bg-fintech-emerald/10 text-fintech-emerald",
                    !isActive && !isPast && "border-fintech-border bg-fintech-elevated/40 text-fintech-muted"
                  )}
                >
                  <div className="text-[9px] text-fintech-muted uppercase">0{idx + 1}</div>
                  <div className="truncate">{step}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Live Execution Outcome Card */}
        {lastExecution && (
          <div className="p-6 bg-fintech-surface border border-fintech-cyan/40 rounded-lg space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between border-b border-fintech-border pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-fintech-emerald" />
                <span className="font-bold text-white text-sm">
                  Autonomous Workflow Completed: {lastExecution.workflow_id.slice(0, 8)}
                </span>
              </div>
              <span className="px-2.5 py-0.5 rounded text-xs font-mono bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30 font-bold uppercase">
                {lastExecution.verification.status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
              <div className="p-3 bg-fintech-elevated rounded border border-fintech-border space-y-1">
                <span className="text-fintech-muted uppercase text-[10px]">AI Proposal</span>
                <div className="text-white font-bold">{lastExecution.decision.action}</div>
                <p className="text-fintech-subtle text-[11px]">{lastExecution.decision.reason}</p>
              </div>

              <div className="p-3 bg-fintech-elevated rounded border border-fintech-border space-y-1">
                <span className="text-fintech-muted uppercase text-[10px]">Policy Gate Verdict</span>
                <div
                  className={cn(
                    "font-bold",
                    lastExecution.policy.decision === "ALLOW"
                      ? "text-fintech-emerald"
                      : "text-fintech-amber"
                  )}
                >
                  {lastExecution.policy.decision}
                </div>
                <p className="text-fintech-subtle text-[11px]">{lastExecution.policy.reason}</p>
              </div>

              <div className="p-3 bg-fintech-elevated rounded border border-fintech-border space-y-1">
                <span className="text-fintech-muted uppercase text-[10px]">Financial Execution</span>
                <div className="text-white font-bold">
                  {formatINR(lastExecution.amount_recovered)} Recovered
                </div>
                <p className="text-fintech-subtle text-[11px]">
                  Tools: {lastExecution.tools_used.join(", ") || "Standard retry"}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Active Recovery Opportunities */}
        <div className="bg-fintech-surface border border-fintech-border rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
              Recovery Opportunities Stream ({opportunities.length})
            </h2>
            <span className="text-xs font-mono text-fintech-muted">Real-Time Queue</span>
          </div>

          {opportunities.length === 0 ? (
            <div className="py-12 text-center text-xs font-mono text-fintech-muted border border-dashed border-fintech-border rounded">
              No failed payments currently flagged for recovery.
            </div>
          ) : (
            <div className="space-y-3">
              {opportunities.map((opp) => (
                <div
                  key={opp.id}
                  className="p-4 bg-fintech-elevated/40 border border-fintech-border hover:border-fintech-cyan/40 rounded-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all hover-glow"
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center gap-3">
                      <span className="text-base font-bold text-white tabular-nums">
                        {formatINR(opp.amount_at_risk)}
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30 font-semibold">
                        {formatPercentage(opp.recovery_probability)} Yield
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-fintech-cyan/10 text-fintech-cyan border border-fintech-cyan/30 uppercase">
                        Priority: {opp.priority}
                      </span>
                    </div>
                    <div className="text-xs text-fintech-subtle font-mono">
                      Proposed Action: <span className="text-white">{opp.recommended_action}</span> |
                      Status: <span className="text-fintech-cyan">{opp.status}</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleExecute(opp)}
                    disabled={triggeringId === opp.id}
                    className="px-4 py-2 bg-fintech-cyan text-fintech-dark font-bold text-xs uppercase tracking-wider rounded flex items-center gap-2 hover:bg-fintech-cyan/90 disabled:opacity-50 transition-all shrink-0"
                  >
                    <Play className="w-3.5 h-3.5" />
                    {triggeringId === opp.id ? "Orchestrating..." : "Execute Recovery"}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Historical Recovery Outcomes */}
        {outcomes.length > 0 && (
          <div className="bg-fintech-surface border border-fintech-border rounded-lg p-5 space-y-4">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
              Recent Recovery Flight Outcomes ({outcomes.length})
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-fintech-border text-fintech-muted uppercase text-[10px]">
                    <th className="pb-2">Timestamp</th>
                    <th className="pb-2">Action</th>
                    <th className="pb-2">Policy Verdict</th>
                    <th className="pb-2">Actual Result</th>
                    <th className="pb-2">Recovered Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-fintech-border/40">
                  {outcomes.map((outc) => (
                    <tr key={outc.id} className="hover:bg-fintech-elevated/40">
                      <td className="py-2.5 text-fintech-muted text-[11px]">
                        {formatDateTime(outc.created_at)}
                      </td>
                      <td className="py-2.5 text-white">{outc.chosen_action}</td>
                      <td className="py-2.5">
                        <span
                          className={cn(
                            "px-1.5 py-0.5 rounded text-[10px] font-bold",
                            outc.policy_decision === "ALLOW"
                              ? "bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30"
                              : "bg-fintech-amber/10 text-fintech-amber border border-fintech-amber/30"
                          )}
                        >
                          {outc.policy_decision}
                        </span>
                      </td>
                      <td className="py-2.5 text-fintech-cyan">{outc.actual_result}</td>
                      <td className="py-2.5 font-bold text-white tabular-nums">
                        {formatINR(outc.recovered_amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </ApiStateView>
    </div>
  );
};
