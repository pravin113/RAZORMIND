import React, { Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { LandingPage } from "@/pages/LandingPage";
import { AppLayout } from "@/layouts/AppLayout";

// Lazy-loaded page chunks — each page splits into its own async chunk
const DashboardPage = React.lazy(() =>
  import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const RevenueRecoveryPage = React.lazy(() =>
  import("@/pages/RevenueRecoveryPage").then((m) => ({ default: m.RevenueRecoveryPage }))
);
const RiskCenterPage = React.lazy(() =>
  import("@/pages/RiskCenterPage").then((m) => ({ default: m.RiskCenterPage }))
);
const AIDecisionPage = React.lazy(() =>
  import("@/pages/AIDecisionPage").then((m) => ({ default: m.AIDecisionPage }))
);
const PoliciesPage = React.lazy(() =>
  import("@/pages/PoliciesPage").then((m) => ({ default: m.PoliciesPage }))
);
const AuditPage = React.lazy(() =>
  import("@/pages/AuditPage").then((m) => ({ default: m.AuditPage }))
);
const RazorpayPage = React.lazy(() =>
  import("@/pages/RazorpayPage").then((m) => ({ default: m.RazorpayPage }))
);
const SettingsPage = React.lazy(() =>
  import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage }))
);

/** Institutional loading skeleton shown while a page chunk loads */
const PageLoadingSkeleton: React.FC = () => (
  <div className="space-y-6 max-w-7xl mx-auto animate-pulse">
    <div className="flex items-center justify-between">
      <div className="space-y-2">
        <div className="h-6 w-64 bg-fintech-elevated rounded" />
        <div className="h-3 w-40 bg-fintech-elevated/60 rounded" />
      </div>
      <div className="h-8 w-32 bg-fintech-elevated rounded" />
    </div>
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-28 bg-fintech-surface border border-fintech-border rounded-lg" />
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 h-72 bg-fintech-surface border border-fintech-border rounded-lg" />
      <div className="h-72 bg-fintech-surface border border-fintech-border rounded-lg" />
    </div>
  </div>
);

/** Wrap lazy page in Suspense */
const Lazy: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<PageLoadingSkeleton />}>{children}</Suspense>
);

export const router = createBrowserRouter([
  {
    path: "/",
    element: <LandingPage />,
  },
  {
    element: <AppLayout />,
    children: [
      {
        path: "/dashboard",
        element: <Lazy><DashboardPage /></Lazy>,
      },
      {
        path: "/recovery",
        element: <Lazy><RevenueRecoveryPage /></Lazy>,
      },
      {
        path: "/risk",
        element: <Lazy><RiskCenterPage /></Lazy>,
      },
      {
        path: "/ai",
        element: <Lazy><AIDecisionPage /></Lazy>,
      },
      {
        path: "/policies",
        element: <Lazy><PoliciesPage /></Lazy>,
      },
      {
        path: "/audit",
        element: <Lazy><AuditPage /></Lazy>,
      },
      {
        path: "/razorpay",
        element: <Lazy><RazorpayPage /></Lazy>,
      },
      {
        path: "/settings",
        element: <Lazy><SettingsPage /></Lazy>,
      },
    ],
  },
  {
    path: "*",
    element: <Navigate to="/" replace />,
  },
]);
