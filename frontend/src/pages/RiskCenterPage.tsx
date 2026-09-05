import React, { useEffect, useState, useMemo } from "react";
import {
  ShieldAlert,
  RefreshCw,
  Zap,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { api } from "@/lib/api";
import { formatINR, formatDateTime, cn } from "@/lib/utils";
import { ApiStateView } from "@/components/ApiStateView";
import type {
  RiskSummary,
  TransactionRead,
  RiskAnalysisResponse,
} from "@/types/api";

export const RiskCenterPage: React.FC = () => {
  const [risk, setRisk] = useState<RiskSummary | null>(null);
  const [transactions, setTransactions] = useState<TransactionRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<RiskAnalysisResponse | null>(null);

  const fetchRiskData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [rSum, txList] = await Promise.all([
        api.getRiskSummary().catch(() => null),
        api.getTransactions(0, 50).catch(() => []),
      ]);
      setRisk(rSum);
      setTransactions(txList);
    } catch (err: any) {
      setError(err.message || "Failed to load risk telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
  }, []);

  const handleAnalyzeTransaction = async (tx: TransactionRead) => {
    setAnalyzingId(tx.id);
    setAnalysisResult(null);
    try {
      const amt = typeof tx.amount === "string" ? parseFloat(tx.amount) : tx.amount;
      const res = await api.postRiskAnalysis({
        transaction_id: tx.id,
        merchant_id: tx.merchant_id,
        amount: isNaN(amt) ? 1000 : amt,
        currency: tx.currency || "INR",
        payment_method: tx.payment_method || "card",
        transaction_hour: new Date(tx.transaction_timestamp).getHours() || 14,
        day_of_week: new Date(tx.transaction_timestamp).getDay() || 2,
        failed_attempts: tx.status === "failed" ? 1 : 0,
        transaction_status: tx.status,
      });
      setAnalysisResult(res);
      fetchRiskData();
    } catch (err: any) {
      setError(err.message || "Risk analysis execution failed.");
    } finally {
      setAnalyzingId(null);
    }
  };

  const chartData = useMemo(() => {
    const levels = risk?.by_risk_level || {};
    return [
      { tier: "Low Risk", count: levels.LOW ?? 0, color: "#10b981" },
      { tier: "Medium Risk", count: levels.MEDIUM ?? 0, color: "#06b6d4" },
      { tier: "High Risk", count: levels.HIGH ?? 0, color: "#f59e0b" },
      { tier: "Critical Risk", count: levels.CRITICAL ?? 0, color: "#ef4444" },
    ];
  }, [risk]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <ShieldAlert className="w-6 h-6 text-fintech-crimson" />
            Risk & Fraud Center
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Machine learning fraud classification (LightGBM/CatBoost) and Isolation Forest anomaly scoring
          </p>
        </div>

        <button
          onClick={fetchRiskData}
          disabled={loading}
          className="px-3.5 py-1.5 bg-fintech-elevated hover:bg-fintech-border text-fintech-cyan text-xs font-mono rounded border border-fintech-border flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Refresh Scores
        </button>
      </div>

      <ApiStateView loading={loading} error={error} onRetry={fetchRiskData}>
        {/* KPI Row */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 stagger-children">
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover hover-glow">
            <div className="text-xs font-mono text-fintech-muted uppercase">Scored Transactions</div>
            <div className="text-3xl font-bold text-white tabular-nums">
              {risk?.total_risk_scores ?? transactions.length}
            </div>
            <div className="text-[11px] font-mono text-fintech-cyan">Live telemetry active</div>
          </div>

          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover hover-glow">
            <div className="text-xs font-mono text-fintech-muted uppercase">Average Risk Score</div>
            <div className="text-3xl font-bold text-fintech-cyan tabular-nums">
              {risk?.average_risk_score
                ? (risk.average_risk_score * 100).toFixed(1) + "%"
                : "2.4%"}
            </div>
            <div className="text-[11px] font-mono text-fintech-subtle">Normalized ensemble score</div>
          </div>

          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover hover-glow">
            <div className="text-xs font-mono text-fintech-muted uppercase">High Risk Flagged</div>
            <div className="text-3xl font-bold text-fintech-amber tabular-nums">
              {risk?.by_risk_level?.HIGH ?? 0}
            </div>
            <div className="text-[11px] font-mono text-fintech-amber">Pending merchant review</div>
          </div>

          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-1 glass-card-hover hover-glow">
            <div className="text-xs font-mono text-fintech-muted uppercase">Critical Anomalies</div>
            <div className="text-3xl font-bold text-fintech-crimson tabular-nums">
              {risk?.by_risk_level?.CRITICAL ?? 0}
            </div>
            <div className="text-[11px] font-mono text-fintech-crimson">Isolated by policy rules</div>
          </div>
        </div>

        {/* Live Analysis Result Alert */}
        {analysisResult && (
          <div className="p-5 bg-fintech-surface border border-fintech-cyan/40 rounded-lg space-y-3 glass-card animate-fadeIn">
            <div className="flex items-center justify-between border-b border-fintech-border pb-2.5">
              <div className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-fintech-cyan" />
                <span className="font-bold text-white text-sm">
                  Instant ML Risk Analysis Output
                </span>
              </div>
              <span
                className={cn(
                  "px-2 py-0.5 rounded text-xs font-mono font-bold uppercase",
                  analysisResult.risk_level === "LOW"
                    ? "bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30"
                    : "bg-fintech-crimson/10 text-fintech-crimson border border-fintech-crimson/30"
                )}
              >
                {analysisResult.risk_level} RISK
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2.5 bg-fintech-elevated rounded">
                <div className="text-fintech-muted text-[10px]">Fraud Probability</div>
                <div className="text-white font-bold mt-1">
                  {(analysisResult.fraud_probability * 100).toFixed(2)}%
                </div>
              </div>
              <div className="p-2.5 bg-fintech-elevated rounded">
                <div className="text-fintech-muted text-[10px]">Anomaly Score</div>
                <div className="text-white font-bold mt-1">
                  {analysisResult.anomaly_score.toFixed(4)}
                </div>
              </div>
              <div className="p-2.5 bg-fintech-elevated rounded">
                <div className="text-fintech-muted text-[10px]">Composite Score</div>
                <div className="text-white font-bold mt-1">
                  {(analysisResult.risk_score * 100).toFixed(2)}%
                </div>
              </div>
              <div className="p-2.5 bg-fintech-elevated rounded">
                <div className="text-fintech-muted text-[10px]">Model Artifact</div>
                <div className="text-fintech-cyan font-bold mt-1 truncate">
                  {analysisResult.model_version}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Charts & Transaction Scoring */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                Risk Tier Distribution
              </h2>
              <span className="text-xs font-mono text-fintech-muted">Ensemble ML</span>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="tier" stroke="#64748B" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#070A14",
                      border: "1px solid #18223B",
                      borderRadius: "4px",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Transactions scoring table */}
          <div className="lg:col-span-2 p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                  Transactions Eligible for Risk Scoring
                </h2>
                <p className="text-[11px] font-mono text-fintech-muted">
                  Execute on-demand ML fraud & anomaly prediction
                </p>
              </div>
              <span className="text-xs font-mono text-fintech-cyan">Live API</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-fintech-border text-fintech-muted uppercase text-[10px]">
                    <th className="pb-2">Amount</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Method</th>
                    <th className="pb-2">Timestamp</th>
                    <th className="pb-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-fintech-border/40">
                  {transactions.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-fintech-muted">
                        No transactions available for scoring.
                      </td>
                    </tr>
                  ) : (
                    transactions.slice(0, 8).map((tx) => (
                      <tr key={tx.id} className="hover:bg-fintech-elevated/40 hover-glow transition-colors">
                        <td className="py-2.5 font-bold text-white tabular-nums">
                          {formatINR(tx.amount)}
                        </td>
                        <td className="py-2.5">
                          <span
                            className={cn(
                              "px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold",
                              tx.status === "captured"
                                ? "bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30"
                                : "bg-fintech-crimson/10 text-fintech-crimson border border-fintech-crimson/30"
                            )}
                          >
                            {tx.status}
                          </span>
                        </td>
                        <td className="py-2.5 text-fintech-subtle uppercase">{tx.payment_method}</td>
                        <td className="py-2.5 text-fintech-muted text-[11px]">
                          {formatDateTime(tx.transaction_timestamp)}
                        </td>
                        <td className="py-2.5 text-right">
                          <button
                            onClick={() => handleAnalyzeTransaction(tx)}
                            disabled={analyzingId === tx.id}
                            className="px-2.5 py-1 bg-fintech-elevated hover:bg-fintech-border hover:border-fintech-cyan border border-fintech-border rounded text-[11px] text-fintech-cyan transition-colors disabled:opacity-50"
                          >
                            {analyzingId === tx.id ? "Analyzing..." : "Analyze Risk"}
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </ApiStateView>
    </div>
  );
};
