import React, { useEffect, useState } from "react";
import {
  Sliders,
  RefreshCw,
  Lock,
  Play,
  Check,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatINR, formatPercentage, cn } from "@/lib/utils";
import { ApiStateView } from "@/components/ApiStateView";
import type {
  PolicyRead,
  PolicyEvaluationResponse,
} from "@/types/api";

export const PoliciesPage: React.FC = () => {
  const [policies, setPolicies] = useState<PolicyRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Policy Evaluation Simulator State
  const [simAction, setSimAction] = useState("retry_payment");
  const [simAmount, setSimAmount] = useState(2500);
  const [simProb, setSimProb] = useState(0.78);
  const [simAttempt, setSimAttempt] = useState(1);
  const [simRisk, setSimRisk] = useState("LOW");
  const [evaluating, setEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<PolicyEvaluationResponse | null>(null);

  const fetchPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPolicies();
      setPolicies(data);
    } catch (err: any) {
      setError(err.message || "Failed to load configured policies.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleSimulatePolicy = async (e: React.FormEvent) => {
    e.preventDefault();
    setEvaluating(true);
    try {
      const merchantId =
        (policies.length > 0 && policies[0].merchant_id) ||
        "24858aff-1023-4415-9df6-58d8c5495fdd";

      const res = await api.evaluatePolicy({
        merchant_id: merchantId,
        action_type: simAction,
        amount: Number(simAmount),
        recovery_probability: Number(simProb),
        attempt_number: Number(simAttempt),
        risk_level: simRisk,
      });
      setEvalResult(res);
    } catch (err: any) {
      setError(err.message || "Policy evaluation request failed.");
    } finally {
      setEvaluating(false);
    }
  };

  const activeConfig = policies.length > 0 ? policies[0].configuration : null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Sliders className="w-6 h-6 text-fintech-cyan" />
            Deterministic Policy Engine
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Hard non-bypassable guardrail stopping rules governing all autonomous financial actions
          </p>
        </div>

        <button
          onClick={fetchPolicies}
          disabled={loading}
          className="px-3.5 py-1.5 bg-fintech-elevated hover:bg-fintech-border text-fintech-cyan text-xs font-mono rounded border border-fintech-border flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Refresh Policies
        </button>
      </div>

      <ApiStateView loading={loading} error={error} onRetry={fetchPolicies}>
        {/* Core Policy Rule Notice */}
        <div className="p-4 rounded-lg bg-fintech-cyan/5 border border-fintech-cyan/20 glass-card flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-2.5 text-fintech-cyan">
            <Lock className="w-4 h-4 shrink-0" />
            <span>
              <strong>DETERMINISTIC AUTHORITY:</strong> AI models only propose actions. The Policy Engine holds absolute veto power.
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30 text-[10px] font-bold">
            NON-BYPASSABLE
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 stagger-children">
          {/* Active Platform Guardrails */}
          <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                Active Recovery Guardrails
              </h2>
              <span className="text-[10px] font-mono text-fintech-emerald bg-fintech-emerald/10 px-2 py-0.5 rounded border border-fintech-emerald/30">
                ACTIVE
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Minimum Recovery Probability</span>
                <span className="text-white font-bold">
                  {formatPercentage(activeConfig?.min_recovery_probability ?? 0.65)}
                </span>
              </div>
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Maximum Automated Amount</span>
                <span className="text-white font-bold">
                  {formatINR(activeConfig?.max_recovery_amount ?? 10000)}
                </span>
              </div>
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Maximum Retry Attempts</span>
                <span className="text-white font-bold">
                  {activeConfig?.max_attempts ?? 2} Attempts
                </span>
              </div>
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Cooldown Interval</span>
                <span className="text-white font-bold">
                  {activeConfig?.cooldown_minutes ?? 60} Minutes
                </span>
              </div>
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Allowed Automated Actions</span>
                <span className="text-fintech-cyan font-bold truncate max-w-xs">
                  {(activeConfig?.allowed_actions || ["retry_payment", "send_payment_reminder"]).join(", ")}
                </span>
              </div>
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Restricted Risk Tiers</span>
                <span className="text-fintech-crimson font-bold">
                  {(activeConfig?.risk_restrictions || ["HIGH", "CRITICAL"]).join(", ")}
                </span>
              </div>
            </div>
          </div>

          {/* Interactive Policy Evaluation Simulator */}
          <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                Live Policy Gate Simulator
              </h2>
              <p className="text-[11px] font-mono text-fintech-muted">
                Test proposed AI actions against live deterministic stopping rules
              </p>
            </div>

            <form onSubmit={handleSimulatePolicy} className="space-y-3 font-mono text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] text-fintech-muted uppercase">Action Type</label>
                  <select
                    value={simAction}
                    onChange={(e) => setSimAction(e.target.value)}
                    className="w-full mt-1 bg-fintech-elevated border border-fintech-border rounded p-2 text-white outline-none"
                  >
                    <option value="retry_payment">retry_payment</option>
                    <option value="send_payment_reminder">send_payment_reminder</option>
                    <option value="create_followup">create_followup</option>
                    <option value="unauthorized_action">unauthorized_action</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-fintech-muted uppercase">Amount (INR)</label>
                  <input
                    type="number"
                    value={simAmount}
                    onChange={(e) => setSimAmount(Number(e.target.value))}
                    className="w-full mt-1 bg-fintech-elevated border border-fintech-border rounded p-2 text-white outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] text-fintech-muted uppercase">Recovery Prob</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={simProb}
                    onChange={(e) => setSimProb(Number(e.target.value))}
                    className="w-full mt-1 bg-fintech-elevated border border-fintech-border rounded p-2 text-white outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-fintech-muted uppercase">Attempt #</label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={simAttempt}
                    onChange={(e) => setSimAttempt(Number(e.target.value))}
                    className="w-full mt-1 bg-fintech-elevated border border-fintech-border rounded p-2 text-white outline-none"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-fintech-muted uppercase">Risk Tier</label>
                  <select
                    value={simRisk}
                    onChange={(e) => setSimRisk(e.target.value)}
                    className="w-full mt-1 bg-fintech-elevated border border-fintech-border rounded p-2 text-white outline-none"
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={evaluating}
                className="w-full mt-2 py-2.5 bg-fintech-cyan hover:bg-fintech-cyan/90 text-fintech-dark font-bold text-xs uppercase tracking-wider rounded flex items-center justify-center gap-2 transition-all hover-glow disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                {evaluating ? "Evaluating Against Policy Rules..." : "Evaluate Policy Gate"}
              </button>
            </form>

            {/* Verdict Display */}
            {evalResult && (
              <div className="p-4 rounded bg-fintech-elevated border border-fintech-border space-y-2.5 font-mono text-xs glass-card animate-fadeIn">
                <div className="flex items-center justify-between">
                  <span className="text-fintech-muted text-[10px] uppercase">Policy Verdict:</span>
                  <span
                    className={cn(
                      "px-2.5 py-0.5 rounded font-bold text-xs uppercase",
                      evalResult.decision === "ALLOW" &&
                        "bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30",
                      evalResult.decision === "REQUIRE_REVIEW" &&
                        "bg-fintech-amber/10 text-fintech-amber border border-fintech-amber/30",
                      evalResult.decision === "DENY" &&
                        "bg-fintech-crimson/10 text-fintech-crimson border border-fintech-crimson/30"
                    )}
                  >
                    {evalResult.decision}
                  </span>
                </div>
                <p className="text-white text-xs">{evalResult.reason}</p>

                <div className="pt-2 border-t border-fintech-border grid grid-cols-2 gap-2 text-[10px]">
                  {Object.entries(evalResult.checks || {}).map(([rule, passed]) => (
                    <div key={rule} className="flex items-center gap-1.5 text-fintech-subtle">
                      {passed ? (
                        <Check className="w-3 h-3 text-fintech-emerald" />
                      ) : (
                        <X className="w-3 h-3 text-fintech-crimson" />
                      )}
                      <span>{rule}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </ApiStateView>
    </div>
  );
};
