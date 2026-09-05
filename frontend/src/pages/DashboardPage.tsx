import React, { useEffect, useState, useMemo } from "react";
import {
  DollarSign,
  ShieldAlert,
  TrendingUp,
  RefreshCw,
  ShieldCheck,
  Play,
  Activity,
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { api } from "@/lib/api";
import { formatINR, formatPercentage, formatDateTime, cn } from "@/lib/utils";
import { ApiStateView } from "@/components/ApiStateView";
import { AnimatedCounter } from "@/components/AnimatedCounter";
import type {
  RecoveryOpportunityRead,
  RecoverySummary,
  RiskSummary,
  TransactionRead,
  MerchantRead,
} from "@/types/api";

export const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recoverySummary, setRecoverySummary] = useState<RecoverySummary | null>(null);
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null);
  const [transactions, setTransactions] = useState<TransactionRead[]>([]);
  const [opportunities, setOpportunities] = useState<RecoveryOpportunityRead[]>([]);
  const [merchants, setMerchants] = useState<MerchantRead[]>([]);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [recSum, rkSum, txList, oppList, merchList] = await Promise.all([
        api.getRecoverySummary().catch(() => null),
        api.getRiskSummary().catch(() => null),
        api.getTransactions(0, 50).catch(() => []),
        api.getRecoveryOpportunities(0, 10).catch(() => []),
        api.getMerchants(0, 10).catch(() => []),
      ]);

      setRecoverySummary(recSum);
      setRiskSummary(rkSum);
      setTransactions(txList);
      setOpportunities(oppList);
      setMerchants(merchList);
    } catch (err: any) {
      setError(err?.message || "Failed to load dashboard telemetry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleTriggerRecovery = async (opp: RecoveryOpportunityRead) => {
    if (!opp.id) return;
    setTriggeringId(opp.id);
    setActionSuccessMessage(null);
    try {
      const merchantId =
        (merchants.length > 0 && merchants[0].id) ||
        (transactions.length > 0 && transactions[0].merchant_id) ||
        "24858aff-1023-4415-9df6-58d8c5495fdd";

      const res = await api.executeRecoveryWorkflow({
        merchant_id: merchantId,
        opportunity_id: opp.id,
        transaction_id: opp.transaction_id,
        dry_run: false,
      });

      setActionSuccessMessage(
        `Autonomous Recovery Executed: ${res.decision.action} | Policy: ${res.policy.decision} | Result: ${res.verification.status} (${formatINR(res.amount_recovered)} recovered)`
      );
      // Refresh to update opportunities and stats
      fetchData();
    } catch (err: any) {
      setError(err?.message || "Autonomous recovery execution failed.");
    } finally {
      setTriggeringId(null);
      setTimeout(() => setActionSuccessMessage(null), 5000);
    }
  };

  // Derive KPIs from real data
  const totalVolume = useMemo(() => {
    return transactions.reduce((acc, t) => {
      const amt = typeof t.amount === "string" ? parseFloat(t.amount) : t.amount;
      return acc + (isNaN(amt) ? 0 : amt);
    }, 0);
  }, [transactions]);

  const capturedCount = useMemo(() => {
    return transactions.filter((t) => t.status === "captured").length;
  }, [transactions]);

  const successRate = useMemo(() => {
    if (transactions.length === 0) return 1.0;
    return capturedCount / transactions.length;
  }, [transactions, capturedCount]);

  // Aggregate daily volume from real transactions
  const trendData = useMemo(() => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const dailyMap: Record<string, { day: string; gross: number; recovered: number }> = {};

    days.forEach((d) => {
      dailyMap[d] = { day: d, gross: 0, recovered: 0 };
    });

    transactions.forEach((tx) => {
      try {
        const d = new Date(tx.transaction_timestamp);
        const dayName = days[d.getDay()];
        const amt = typeof tx.amount === "string" ? parseFloat(tx.amount) : tx.amount;
        if (!isNaN(amt) && dailyMap[dayName]) {
          dailyMap[dayName].gross += amt;
          if (tx.status === "captured") {
            dailyMap[dayName].recovered += amt * 0.15; // Estimated recovered fraction
          }
        }
      } catch {
        // Safe fallback for date parsing
      }
    });

    return Object.values(dailyMap);
  }, [transactions]);

  // Real risk distribution from ML summary
  const riskData = useMemo(() => {
    const byLevel = riskSummary?.by_risk_level || {};
    return [
      { name: "LOW", count: byLevel.LOW ?? 0, color: "#10b981" },
      { name: "MEDIUM", count: byLevel.MEDIUM ?? 0, color: "#06b6d4" },
      { name: "HIGH", count: byLevel.HIGH ?? 0, color: "#f59e0b" },
      { name: "CRITICAL", count: byLevel.CRITICAL ?? 0, color: "#ef4444" },
    ];
  }, [riskSummary]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <Activity className="w-6 h-6 text-fintech-cyan" />
            Financial Intelligence Command Center
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Autonomous payment telemetry, machine learning risk gates, and deterministic recovery rails
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="px-3.5 py-1.5 bg-fintech-elevated hover:bg-fintech-border text-fintech-cyan text-xs font-mono rounded border border-fintech-border flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Sync Telemetry
        </button>
      </div>

      {actionSuccessMessage && (
        <div className="p-3 bg-fintech-emerald/10 border border-fintech-emerald/30 rounded text-xs font-mono text-fintech-emerald flex items-center gap-2 animate-fadeIn">
          <ShieldCheck className="w-4 h-4 shrink-0" />
          <span>{actionSuccessMessage}</span>
        </div>
      )}

      <ApiStateView loading={loading} error={error} onRetry={fetchData}>
        {/* KPI Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 stagger-children">
          {/* Metric 1: Total Volume Scored */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-2 glass-card-hover">
            <div className="flex items-center justify-between text-xs font-mono text-fintech-muted uppercase tracking-wider">
              <span>Processed Volume</span>
              <DollarSign className="w-4 h-4 text-fintech-cyan" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
              <AnimatedCounter value={totalVolume} formatFn={formatINR} />
            </div>
            <div className="flex items-center gap-1 text-[11px] text-fintech-emerald font-mono">
              <TrendingUp className="w-3 h-3" />
              <span>{transactions.length} total transactions</span>
            </div>
          </div>

          {/* Metric 2: Expected Recoverable */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-2 glass-card-hover">
            <div className="flex items-center justify-between text-xs font-mono text-fintech-muted uppercase tracking-wider">
              <span>Recoverable Revenue</span>
              <TrendingUp className="w-4 h-4 text-fintech-emerald" />
            </div>
            <div className="text-2xl font-bold text-fintech-emerald tracking-tight tabular-nums">
              <AnimatedCounter value={recoverySummary?.expected_recovered_value || 0} formatFn={formatINR} />
            </div>
            <div className="text-[11px] text-fintech-subtle font-mono">
              {recoverySummary?.open_opportunities || opportunities.length} open opportunities
            </div>
          </div>

          {/* Metric 3: Recovery Yield */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-2 glass-card-hover">
            <div className="flex items-center justify-between text-xs font-mono text-fintech-muted uppercase tracking-wider">
              <span>Success Rate</span>
              <ShieldCheck className="w-4 h-4 text-fintech-blue" />
            </div>
            <div className="text-2xl font-bold text-white tracking-tight tabular-nums">
              <AnimatedCounter value={successRate} formatFn={formatPercentage} />
            </div>
            <div className="text-[11px] text-fintech-muted font-mono">
              Avg Yield: {formatPercentage(recoverySummary?.average_recovery_probability || 0.70)}
            </div>
          </div>

          {/* Metric 4: High-Risk Interventions */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-2 glass-card-hover">
            <div className="flex items-center justify-between text-xs font-mono text-fintech-muted uppercase tracking-wider">
              <span>High-Risk Flags</span>
              <ShieldAlert className="w-4 h-4 text-fintech-crimson" />
            </div>
            <div className="text-2xl font-bold text-fintech-crimson tracking-tight font-mono">
              <AnimatedCounter value={riskSummary?.by_risk_level?.HIGH || 0} />
            </div>
            <div className="text-[11px] text-fintech-subtle font-mono">
              {riskSummary?.total_risk_scores || 0} ML transactions scored
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Trajectory Area Chart */}
          <div className="lg:col-span-2 p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                  Financial Activity & Revenue
                </h2>
                <p className="text-[11px] font-mono text-fintech-muted">
                  Gross transaction amounts plotted over daily activity
                </p>
              </div>
              <span className="text-xs font-mono text-fintech-cyan">Live Aggregates</span>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2979FF" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#2979FF" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="colorRec" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00E676" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#00E676" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="day" stroke="#64748B" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#070A14",
                      border: "1px solid #18223B",
                      borderRadius: "4px",
                      fontSize: "12px",
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="gross"
                    stroke="#2979FF"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorRev)"
                    name="Gross Volume (₹)"
                  />
                  <Area
                    type="monotone"
                    dataKey="recovered"
                    stroke="#00E676"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorRec)"
                    name="Estimated Recovered (₹)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ML Risk Distribution Chart */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                  Risk Tier Distribution
                </h2>
                <p className="text-[11px] font-mono text-fintech-muted">
                  ML Fraud & Anomaly Tiers
                </p>
              </div>
              <span className="text-xs font-mono text-fintech-muted">Real Scores</span>
            </div>

            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <XAxis dataKey="name" stroke="#64748B" fontSize={11} tickLine={false} />
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
                    {riskData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Recovery Opportunities & Recent Transactions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recovery Opportunities Table */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                  Active Recovery Opportunities
                </h2>
                <p className="text-[11px] font-mono text-fintech-muted">
                  ML-ranked failed payments eligible for recovery
                </p>
              </div>
              <span className="text-xs font-mono text-fintech-cyan">Policy Protected</span>
            </div>

            <div className="space-y-3">
              {opportunities.length === 0 ? (
                <div className="py-10 text-center text-xs font-mono text-fintech-muted border border-dashed border-fintech-border rounded-md">
                  No active recovery opportunities found. All payments healthy.
                </div>
              ) : (
                opportunities.map((opp) => (
                  <div
                    key={opp.id}
                    className="p-3.5 bg-fintech-elevated/60 border border-fintech-border hover:border-fintech-cyan/40 rounded-md flex items-center justify-between gap-4 transition-all hover-glow"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white tabular-nums">
                          {formatINR(opp.amount_at_risk)}
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30 font-semibold">
                          {formatPercentage(opp.recovery_probability)} yield
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-fintech-surface text-fintech-muted uppercase">
                          {opp.priority}
                        </span>
                      </div>
                      <div className="text-xs text-fintech-subtle truncate">
                        Action: <span className="text-white font-mono">{opp.recommended_action}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleTriggerRecovery(opp)}
                      disabled={triggeringId === opp.id}
                      className="px-3.5 py-1.5 bg-fintech-cyan/10 hover:bg-fintech-cyan text-fintech-cyan hover:text-fintech-dark border border-fintech-cyan/30 text-xs font-mono uppercase tracking-wider rounded transition-all shrink-0 flex items-center gap-1.5 disabled:opacity-50 font-semibold"
                    >
                      <Play className="w-3 h-3" />
                      {triggeringId === opp.id ? "Executing..." : "Recover"}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Transactions Table */}
          <div className="p-5 bg-fintech-surface border border-fintech-border rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                  Live Transactions Stream
                </h2>
                <p className="text-[11px] font-mono text-fintech-muted">
                  Recent captured and failed merchant transactions
                </p>
              </div>
              <span className="text-xs font-mono text-fintech-muted">Live Feed</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-fintech-border text-fintech-muted font-mono uppercase text-[10px]">
                    <th className="pb-2">Amount</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Method</th>
                    <th className="pb-2">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-fintech-border/40 font-mono">
                  {transactions.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="py-10 text-center text-fintech-muted">
                        No transactions recorded in database yet.
                      </td>
                    </tr>
                  ) : (
                    transactions.slice(0, 6).map((tx) => (
                      <tr key={tx.id} className="hover:bg-fintech-elevated/40">
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
