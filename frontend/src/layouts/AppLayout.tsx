import React, { useState, useEffect } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  DollarSign,
  ShieldAlert,
  Bot,
  Sliders,
  FileText,
  CreditCard,
  Settings,
  Menu,
  X,
  Bell,
  Activity,
  CheckCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { BackendStatusBadge } from "@/components/BackendStatusBadge";
import { api } from "@/lib/api";
import type { MerchantRead } from "@/types/api";

const NAV_ITEMS = [
  { name: "Command Center", path: "/dashboard", icon: LayoutDashboard },
  { name: "Revenue Recovery", path: "/recovery", icon: DollarSign },
  { name: "Risk Center", path: "/risk", icon: ShieldAlert },
  { name: "AI Decision Center", path: "/ai", icon: Bot },
  { name: "Policies", path: "/policies", icon: Sliders },
  { name: "Audit / Flight Recorder", path: "/audit", icon: FileText },
  { name: "Razorpay", path: "/razorpay", icon: CreditCard },
  { name: "Settings", path: "/settings", icon: Settings },
];

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [merchants, setMerchants] = useState<MerchantRead[]>([]);
  const [selectedMerchantId, setSelectedMerchantId] = useState<string>("");
  const location = useLocation();

  useEffect(() => {
    api
      .getMerchants()
      .then((data) => {
        setMerchants(data);
        if (data.length > 0) {
          setSelectedMerchantId(data[0].id);
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="flex h-screen bg-fintech-dark text-fintech-text overflow-hidden">
      {/* Mobile Backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 w-64 bg-fintech-surface border-r border-fintech-border flex flex-col transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Brand Header */}
        <div className="h-16 flex items-center justify-between px-6 border-b border-fintech-border">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-fintech-cyan to-fintech-blue flex items-center justify-center font-mono font-bold text-fintech-dark text-sm tracking-wider shadow-fintech-glow">
              RM
            </div>
            <div>
              <span className="font-bold text-base tracking-wider text-white block leading-none">
                RAZORMIND
              </span>
              <span className="text-[9px] font-mono uppercase tracking-widest text-fintech-muted">
                FINANCIAL AI
              </span>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-fintech-muted hover:text-white p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-medium tracking-wide transition-all",
                  isActive
                    ? "bg-fintech-cyan/10 text-fintech-cyan border border-fintech-cyan/30 shadow-sm"
                    : "text-fintech-subtle hover:text-white hover:bg-fintech-elevated"
                )}
              >
                <Icon className={cn("w-4 h-4", isActive ? "text-fintech-cyan" : "text-fintech-muted")} />
                {item.name}
              </NavLink>
            );
          })}
        </nav>

        {/* AI & Infrastructure Status Footer */}
        <div className="p-4 border-t border-fintech-border bg-fintech-elevated/40 space-y-2.5 text-xs font-mono">
          <div className="flex items-center justify-between">
            <span className="text-fintech-muted">Qwen 3 Model</span>
            <span className="flex items-center gap-1 text-fintech-emerald text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-fintech-emerald animate-pulse" />
              ONLINE
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-fintech-muted">Policy Gate</span>
            <span className="text-fintech-cyan text-[11px]">DETERMINISTIC</span>
          </div>
          <div className="pt-1">
            <BackendStatusBadge compact={false} className="w-full" />
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-fintech-surface/80 border-b border-fintech-border flex items-center justify-between px-4 sm:px-6 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-fintech-subtle hover:text-white rounded-md"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Merchant Selector */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-fintech-elevated border border-fintech-border text-xs">
              <span className="text-fintech-muted font-mono">Merchant:</span>
              {merchants.length > 0 ? (
                <select
                  value={selectedMerchantId}
                  onChange={(e) => setSelectedMerchantId(e.target.value)}
                  className="bg-transparent font-semibold text-white outline-none cursor-pointer text-xs"
                >
                  {merchants.map((m) => (
                    <option key={m.id} value={m.id} className="bg-fintech-surface text-white">
                      {m.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="font-semibold text-white">RazorMind Flagship Store</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Global Live Backend Indicator */}
            <BackendStatusBadge compact={true} />

            {/* Test Mode Badge */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-fintech-amber/10 border border-fintech-amber/30 text-fintech-amber text-[10px] font-mono uppercase tracking-wider">
              <Activity className="w-3 h-3" />
              Test Mode
            </div>

            {/* AI Active Indicator */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-fintech-cyan/10 border border-fintech-cyan/30 text-fintech-cyan text-[10px] font-mono uppercase tracking-wider">
              <CheckCircle className="w-3 h-3" />
              AI Active
            </div>

            {/* Notification Bell */}
            <button className="p-2 text-fintech-subtle hover:text-white rounded-md hover:bg-fintech-elevated relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-fintech-cyan rounded-full" />
            </button>

            {/* User Profile Avatar */}
            <div className="w-8 h-8 rounded-full bg-fintech-elevated border border-fintech-border flex items-center justify-center font-mono text-xs text-fintech-cyan font-bold">
              OP
            </div>
          </div>
        </header>

        {/* Page Outlet with route transition */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 bg-fintech-dark">
          <div key={location.pathname} className="page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
