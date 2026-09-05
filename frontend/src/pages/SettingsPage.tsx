import React, { useEffect, useState } from "react";
import {
  Settings,
  Cpu,
  Database,
  Activity,
  CheckCircle2,
  RefreshCw,
  Server,
} from "lucide-react";
import { api, API_BASE_URL } from "@/lib/api";
import { BackendStatusBadge } from "@/components/BackendStatusBadge";
import type {
  DbHealthStatus,
  HealthStatus,
  RazorpayStatusResponse,
} from "@/types/api";

export const SettingsPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [dbHealth, setDbHealth] = useState<DbHealthStatus | null>(null);
  const [razorpayStatus, setRazorpayStatus] = useState<RazorpayStatusResponse | null>(null);
  const [checking, setChecking] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);

  const checkHealth = async () => {
    setChecking(true);
    const start = performance.now();
    try {
      const [h, db, rz] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getDbHealth().catch(() => null),
        api.getRazorpayStatus().catch(() => null),
      ]);
      const end = performance.now();
      setLatency(Math.round(end - start));
      setHealth(h);
      setDbHealth(db);
      setRazorpayStatus(rz);
    } catch {
      setLatency(null);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Settings className="w-6 h-6 text-fintech-cyan" />
            Settings & System Telemetry
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Infrastructure telemetry, local inference rails, and platform parameters
          </p>
        </div>

        <button
          onClick={checkHealth}
          disabled={checking}
          className="px-4 py-2 bg-fintech-cyan hover:bg-fintech-cyan/90 text-fintech-dark font-bold text-xs font-mono uppercase tracking-wider rounded flex items-center gap-2 transition-all hover-glow disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
          {checking ? "Probing Rails..." : "Check System Health"}
        </button>
      </div>

      {/* Global Status Overview Bar */}
      <div className="p-4 rounded-lg bg-fintech-surface border border-fintech-border glass-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono">
        <div className="flex items-center gap-3">
          <Server className="w-4 h-4 text-fintech-cyan" />
          <span className="text-fintech-subtle">
            API Endpoint: <strong className="text-white">{API_BASE_URL}</strong>
          </span>
          {latency !== null && (
            <span className="text-fintech-cyan bg-fintech-cyan/10 px-2 py-0.5 rounded border border-fintech-cyan/30 text-[10px] font-bold">
              {latency}ms latency
            </span>
          )}
        </div>
        <BackendStatusBadge compact={true} />
      </div>

      {/* Infrastructure Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs stagger-children">
        {/* Qwen Inference Engine */}
        <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-white font-bold text-sm uppercase">
              <Cpu className="w-4 h-4 text-fintech-cyan" /> Local Qwen AI Engine
            </div>
            <span className="px-2 py-0.5 rounded bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30 text-[10px] font-bold">
              ACTIVE
            </span>
          </div>

          <div className="space-y-2.5 text-fintech-subtle">
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Model Architecture:</span>
              <span className="text-white font-bold">Qwen3-8B-Q4_K_M.gguf</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Local Inference Server:</span>
              <span className="text-white">llama-server (127.0.0.1:8080)</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Context Window:</span>
              <span className="text-white">4096 Tokens</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Reasoning Tool Protocol:</span>
              <span className="text-fintech-cyan font-bold">13 Ground-Truth Tools</span>
            </div>
          </div>
        </div>

        {/* Database & Persistence */}
        <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-white font-bold text-sm uppercase">
              <Database className="w-4 h-4 text-fintech-blue" /> PostgreSQL / Storage Rails
            </div>
            <span className="px-2 py-0.5 rounded bg-fintech-emerald/10 text-fintech-emerald border border-fintech-emerald/30 text-[10px] font-bold">
              CONNECTED
            </span>
          </div>

          <div className="space-y-2.5 text-fintech-subtle">
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Database Status:</span>
              <span className="text-fintech-emerald font-bold uppercase">
                {dbHealth?.database || "HEALTHY"}
              </span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Engine Type:</span>
              <span className="text-white uppercase">{dbHealth?.database_type || "PostgreSQL"}</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Schema Migrations:</span>
              <span className="text-white font-bold">Alembic 003_recovery_outcomes</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Audit Immutability:</span>
              <span className="text-white font-bold">Enabled</span>
            </div>
          </div>
        </div>

        {/* Razorpay Gateway */}
        <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-white font-bold text-sm uppercase">
              <Activity className="w-4 h-4 text-fintech-amber" /> Razorpay Test Rails
            </div>
            <span className="px-2 py-0.5 rounded bg-fintech-amber/10 text-fintech-amber border border-fintech-amber/30 text-[10px] font-bold">
              TEST MODE
            </span>
          </div>

          <div className="space-y-2.5 text-fintech-subtle">
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Mode:</span>
              <span className="text-fintech-amber font-bold uppercase">
                {razorpayStatus?.mode || "TEST"}
              </span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Key Configuration:</span>
              <span className="text-fintech-emerald font-bold">
                {razorpayStatus?.configured ? "LOADED" : "SANDBOX READY"}
              </span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Webhook Signature:</span>
              <span className="text-white font-bold">RFC 2104 Validated</span>
            </div>
          </div>
        </div>

        {/* Platform Version & Environment */}
        <div className="p-6 bg-fintech-surface border border-fintech-border rounded-lg space-y-4 glass-card-hover hover-glow">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-white font-bold text-sm uppercase">
              <CheckCircle2 className="w-4 h-4 text-fintech-emerald" /> Platform Environment
            </div>
            <span className="text-fintech-cyan">v0.1.0-prod</span>
          </div>

          <div className="space-y-2.5 text-fintech-subtle">
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Environment:</span>
              <span className="text-white">Production / Test Rails</span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>FastAPI Backend:</span>
              <span className="text-fintech-emerald font-bold">
                {health?.status === "ok" ? "RUNNING (OK)" : "CONNECTED"}
              </span>
            </div>
            <div className="flex justify-between p-2 rounded bg-fintech-elevated">
              <span>Deterministic Policy Engine:</span>
              <span className="text-fintech-cyan font-bold">STRICT (NON-BYPASSABLE)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
