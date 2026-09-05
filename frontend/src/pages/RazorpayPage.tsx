import React, { useEffect, useState } from "react";
import {
  CreditCard,
  CheckCircle2,
  RefreshCw,
  Activity,
  Plus,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatINR, cn } from "@/lib/utils";
import { ApiStateView } from "@/components/ApiStateView";
import type {
  RazorpayOrderResponse,
  RazorpayStatusResponse,
} from "@/types/api";

export const RazorpayPage: React.FC = () => {
  const [status, setStatus] = useState<RazorpayStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Test Order creation state
  const [testAmount, setTestAmount] = useState(1499);
  const [creatingOrder, setCreatingOrder] = useState(false);
  const [recentOrder, setRecentOrder] = useState<RazorpayOrderResponse | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getRazorpayStatus();
      setStatus(data);
    } catch (err: any) {
      setError(err.message || "Failed to query Razorpay integration status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleCreateTestOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingOrder(true);
    try {
      const res = await api.createRazorpayOrder({
        amount: Math.round(Number(testAmount) * 100), // convert to paise
        currency: "INR",
        receipt: `rcpt_${Date.now().toString().slice(-6)}`,
        notes: { environment: "test_mode", initiated_by: "razormind_frontend" },
      });
      setRecentOrder(res);
    } catch (err: any) {
      setError(err.message || "Razorpay test order creation failed.");
    } finally {
      setCreatingOrder(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <CreditCard className="w-6 h-6 text-fintech-cyan" />
            Razorpay Gateway Rails
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Payment processing gateway, HMAC signed webhooks, and Test Mode rails
          </p>
        </div>

        <button
          onClick={fetchStatus}
          disabled={loading}
          className="px-3.5 py-1.5 bg-fintech-elevated hover:bg-fintech-border text-fintech-cyan text-xs font-mono rounded border border-fintech-border flex items-center gap-1.5 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
          Check Gateway Status
        </button>
      </div>

      <ApiStateView loading={loading} error={error} onRetry={fetchStatus}>
        {/* Test Mode Notification Banner */}
        <div className="p-4 rounded-lg bg-fintech-amber/10 border border-fintech-amber/30 glass-card flex items-center justify-between font-mono text-xs">
          <div className="flex items-center gap-2 text-fintech-amber">
            <Activity className="w-4 h-4 shrink-0" />
            <span>
              <strong>RAZORPAY TEST MODE ACTIVE:</strong> No real funds are debited. All transactions and webhooks operate on simulated test rails.
            </span>
          </div>
          <span className="px-2 py-0.5 rounded bg-fintech-amber/20 border border-fintech-amber/40 text-fintech-amber font-bold text-[10px]">
            TEST MODE
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 stagger-children">
          {/* Integration Status Card */}
          <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                Integration Health & Telemetry
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30">
                HEALTHY
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Gateway Configuration</span>
                <span className="text-fintech-emerald font-bold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  {status?.configured ? "CONNECTED (API KEYS LOADED)" : "CONNECTED (TEST SANDBOX)"}
                </span>
              </div>

              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Operating Rail Mode</span>
                <span className="text-fintech-cyan font-bold uppercase">
                  {status?.mode || "TEST"}
                </span>
              </div>

              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Webhook Signature Verification</span>
                <span className="text-white font-bold">HMAC-SHA256 (RFC 2104)</span>
              </div>

              <div className="flex justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">Idempotency Layer</span>
                <span className="text-white font-bold">Database Webhook Events Table</span>
              </div>
            </div>
          </div>

          {/* Test Order Creation Harness */}
          <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-wider text-white">
                Create Test Mode Order
              </h2>
              <p className="text-[11px] font-mono text-fintech-muted">
                Simulate merchant order creation via <code>POST /api/v1/razorpay/orders</code>
              </p>
            </div>

            <form onSubmit={handleCreateTestOrder} className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-[10px] text-fintech-muted uppercase">Order Amount (INR)</label>
                <input
                  type="number"
                  min="1"
                  value={testAmount}
                  onChange={(e) => setTestAmount(Number(e.target.value))}
                  className="w-full mt-1 bg-fintech-elevated border border-fintech-border rounded p-2.5 text-white outline-none focus:border-fintech-cyan"
                />
              </div>

              <button
                type="submit"
                disabled={creatingOrder}
                className="w-full py-2.5 bg-fintech-cyan hover:bg-fintech-cyan/90 text-fintech-dark font-bold text-xs uppercase tracking-wider rounded flex items-center justify-center gap-2 transition-all hover-glow disabled:opacity-50"
              >
                <Plus className="w-3.5 h-3.5" />
                {creatingOrder ? "Creating Test Order..." : "Create Razorpay Test Order"}
              </button>
            </form>

            {/* Test Order Response Result */}
            {recentOrder && (
              <div className="p-4 rounded bg-fintech-elevated border border-fintech-cyan/30 space-y-2 font-mono text-xs glass-card animate-fadeIn">
                <div className="flex items-center justify-between text-[11px] text-fintech-muted">
                  <span>ORDER GENERATED:</span>
                  <span className="text-fintech-emerald font-bold uppercase">{recentOrder.status}</span>
                </div>
                <div className="text-white font-bold text-sm">{recentOrder.id}</div>
                <div className="flex justify-between text-fintech-subtle text-[11px]">
                  <span>Amount: {formatINR(recentOrder.amount / 100)}</span>
                  <span>Receipt: {recentOrder.receipt || "--"}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </ApiStateView>
    </div>
  );
};
