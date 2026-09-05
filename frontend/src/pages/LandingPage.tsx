import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRight,
  ShieldCheck,
  Zap,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Lock,
  ChevronDown,
} from "lucide-react";
import { SceneContainer } from "@/components/three/SceneContainer";
import { useLenis } from "@/hooks/useLenis";
import { AnimatedCounter } from "@/components/AnimatedCounter";
import { formatINR } from "@/lib/utils";

gsap.registerPlugin(ScrollTrigger);

const STAGES = [
  { id: "opening", title: "Genesis", label: "Autonomous Financial AI" },
  { id: "universe", title: "Universe", label: "Real-time Flow" },
  { id: "payment", title: "Payment", label: "Transaction Isolated" },
  { id: "risk", title: "At Risk", label: "Revenue Leak Detected" },
  { id: "activation", title: "Activation", label: "RazorMind Core Active" },
  { id: "investigation", title: "Investigation", label: "Qwen 3 Deep Context" },
  { id: "policy", title: "Policy Gate", label: "Deterministic Guardrails" },
  { id: "recovery", title: "Recovery", label: "Bounded Execution" },
  { id: "payoff", title: "Payoff", label: "Revenue Recovered" },
  { id: "transition", title: "Command", label: "Platform Command Center" },
];

export const LandingPage: React.FC = () => {
  useLenis();
  const [currentStage, setCurrentStage] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const sectionsRef = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      sectionsRef.current.forEach((section, index) => {
        if (!section) return;

        ScrollTrigger.create({
          trigger: section,
          start: "top center",
          end: "bottom center",
          onEnter: () => setCurrentStage(index),
          onEnterBack: () => setCurrentStage(index),
        });

        // Animate section content cards on scroll
        const card = section.querySelector(".section-card");
        if (card) {
          gsap.fromTo(
            card,
            {
              opacity: 0,
              y: 40,
              scale: 0.97,
            },
            {
              opacity: 1,
              y: 0,
              scale: 1,
              duration: 0.8,
              ease: "power3.out",
              scrollTrigger: {
                trigger: section,
                start: "top 70%",
                toggleActions: "play none none reverse",
              },
            }
          );
        }
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="relative bg-fintech-dark text-fintech-text min-h-screen scanline-overlay">
      {/* 3D Financial Universe Scene Layer */}
      <SceneContainer stage={currentStage} />

      {/* Top Header */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-fintech-dark/60 backdrop-blur-md border-b border-fintech-border/40">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-fintech-cyan to-fintech-blue flex items-center justify-center font-mono font-bold text-fintech-dark text-sm tracking-wider shadow-fintech-glow">
            RM
          </div>
          <span className="font-bold text-lg tracking-wider text-white">RAZORMIND</span>
          <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] uppercase font-mono tracking-widest bg-fintech-cyan/10 border border-fintech-cyan/30 text-fintech-cyan rounded">
            Autonomous AI
          </span>
        </div>

        <div className="flex items-center gap-4">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-fintech-dark bg-fintech-cyan hover:bg-fintech-cyan/90 rounded transition-all shadow-fintech-glow"
          >
            Command Center
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* Right Sidebar Stage Timeline Indicator */}
      <div className="fixed right-6 top-1/2 -translate-y-1/2 z-40 hidden lg:flex flex-col gap-3">
        {STAGES.map((s, idx) => (
          <div key={s.id} className="flex items-center gap-3 justify-end group cursor-default">
            <span
              className={`text-[10px] font-mono tracking-wider transition-opacity duration-300 ${
                currentStage === idx ? "opacity-100 text-fintech-cyan" : "opacity-0 group-hover:opacity-60 text-fintech-muted"
              }`}
            >
              {s.title}
            </span>
            <div
              className={`w-2 h-2 rounded-full transition-all duration-300 ${
                currentStage === idx
                  ? "bg-fintech-cyan scale-125 shadow-fintech-glow"
                  : "bg-fintech-border group-hover:bg-fintech-subtle"
              }`}
            />
          </div>
        ))}
      </div>

      {/* Scrollable Narrative Content */}
      <div className="relative z-10">
        {/* ========================================================================= */}
        {/* SECTION 1 — OPENING */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[0] = el)}
          className="min-h-screen flex flex-col items-center justify-center text-center px-4 relative"
        >
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-fintech-cyan/5 border border-fintech-cyan/20 text-fintech-cyan text-xs font-mono uppercase tracking-widest animate-pulse">
              <Zap className="w-3 h-3" />
              Autonomous Financial AI
            </div>

            <h1 className="text-5xl sm:text-7xl md:text-8xl font-black tracking-tight text-white uppercase">
              Razor<span className="text-transparent bg-clip-text bg-gradient-to-r from-fintech-cyan via-fintech-blue to-white">Mind</span>
            </h1>

            <p className="text-xl sm:text-2xl text-fintech-subtle font-light tracking-wide max-w-xl mx-auto">
              Your money. <span className="text-white font-normal">Under intelligence.</span>
            </p>

            <div className="pt-8 flex flex-col items-center gap-3">
              <span className="text-xs font-mono uppercase tracking-widest text-fintech-muted flex items-center gap-1.5">
                Scroll to Explore the Journey <ChevronDown className="w-3.5 h-3.5 animate-bounce" />
              </span>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 2 — FINANCIAL UNIVERSE */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[1] = el)}
          className="min-h-screen flex items-center justify-start px-6 md:px-20 max-w-6xl mx-auto"
        >
          <div className="section-card max-w-md bg-fintech-surface/80 border border-fintech-border p-8 rounded-lg backdrop-blur-md space-y-4 glass-card">
            <span className="text-xs font-mono uppercase tracking-widest text-fintech-cyan flex items-center gap-2">
              <Activity className="w-4 h-4" /> Global Financial Universe
            </span>
            <h2 className="text-3xl font-bold tracking-tight text-white">
              Every Millisecond, Capital Flows in Thousands of Streams.
            </h2>
            <p className="text-sm text-fintech-subtle leading-relaxed">
              Payments, checkouts, customer authorizations, and settlement rails moving across the globe. Each node represents a living transaction.
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 3 — PAYMENT */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[2] = el)}
          className="min-h-screen flex items-center justify-end px-6 md:px-20 max-w-6xl mx-auto"
        >
          <div className="section-card max-w-md bg-fintech-surface/90 border border-fintech-crimson/30 p-8 rounded-lg backdrop-blur-md space-y-6 glass-card-crimson">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-widest text-fintech-subtle">Isolated Transaction</span>
              <span className="px-2 py-0.5 text-[10px] font-mono bg-fintech-crimson/10 border border-fintech-crimson/40 text-fintech-crimson rounded uppercase">
                Payment Failed
              </span>
            </div>

            <div className="space-y-1">
              <div className="text-4xl font-extrabold text-white tracking-tight">₹2,999.00</div>
              <div className="text-xs font-mono text-fintech-muted">pay_isolated_demo_982 · Card Network Failure</div>
            </div>

            <div className="space-y-2 pt-2 border-t border-fintech-border/50 text-xs font-mono">
              <div className="flex justify-between text-fintech-subtle">
                <span>PAYMENT</span>
                <span className="text-white">INITIATED</span>
              </div>
              <div className="flex justify-between text-fintech-subtle">
                <span>AUTHORIZATION</span>
                <span className="text-white">GATEWAY TIMEOUT</span>
              </div>
              <div className="flex justify-between text-fintech-crimson font-semibold">
                <span>CAPTURE</span>
                <span>FAILED</span>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 4 — REVENUE AT RISK */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[3] = el)}
          className="min-h-screen flex items-center justify-center px-6 text-center"
        >
          <div className="section-card max-w-xl bg-fintech-surface/90 border border-fintech-crimson/40 p-10 rounded-lg backdrop-blur-md space-y-5 shadow-crimson-glow glass-card-crimson">
            <span className="text-xs font-mono uppercase tracking-widest text-fintech-crimson flex items-center justify-center gap-1.5">
              <AlertTriangle className="w-4 h-4" /> Revenue Leak Detected
            </span>
            <div className="text-6xl font-black tracking-tight text-white">₹38,420.00</div>
            <p className="text-lg text-fintech-subtle font-light italic">
              "Revenue leaks are invisible until someone looks."
            </p>
            <p className="text-xs font-mono text-fintech-muted uppercase tracking-wider">
              14 transactions accumulated across retry lockouts and silent gateway drops.
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 5 — RAZORMIND ACTIVATION */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[4] = el)}
          className="min-h-screen flex items-center justify-start px-6 md:px-20 max-w-6xl mx-auto"
        >
          <div className="section-card max-w-md bg-fintech-surface/90 border border-fintech-cyan/40 p-8 rounded-lg backdrop-blur-md space-y-6 shadow-fintech-glow glass-card-cyan">
            <span className="text-xs font-mono uppercase tracking-widest text-fintech-cyan">Autonomous Core Active</span>
            <h2 className="text-3xl font-bold tracking-tight text-white">RAZORMIND Engages</h2>

            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="p-3 bg-fintech-elevated/80 border border-fintech-border rounded text-center">
                <span className="text-[10px] font-mono text-fintech-cyan block">PHASE 1</span>
                <span className="text-sm font-semibold text-white">OBSERVE</span>
              </div>
              <div className="p-3 bg-fintech-elevated/80 border border-fintech-border rounded text-center">
                <span className="text-[10px] font-mono text-fintech-cyan block">PHASE 2</span>
                <span className="text-sm font-semibold text-white">DETECT</span>
              </div>
              <div className="p-3 bg-fintech-elevated/80 border border-fintech-border rounded text-center">
                <span className="text-[10px] font-mono text-fintech-cyan block">PHASE 3</span>
                <span className="text-sm font-semibold text-white">INVESTIGATE</span>
              </div>
              <div className="p-3 bg-fintech-elevated/80 border border-fintech-border rounded text-center">
                <span className="text-[10px] font-mono text-fintech-cyan block">PHASE 4</span>
                <span className="text-sm font-semibold text-white">DECIDE</span>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 6 — AI INVESTIGATION */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[5] = el)}
          className="min-h-screen flex items-center justify-end px-6 md:px-20 max-w-6xl mx-auto"
        >
          <div className="section-card max-w-md bg-fintech-surface/90 border border-fintech-border p-8 rounded-lg backdrop-blur-md space-y-5 glass-card">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase tracking-widest text-fintech-cyan">Qwen 3 Deep Inspection</span>
              <span className="text-xs font-mono text-fintech-muted">8B GGUF Model</span>
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">✓ Payment Details</span>
                <span className="text-white">Timeout (Temporary)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">✓ Customer History</span>
                <span className="text-white">Loyal (12 Successful)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">✓ Risk Score</span>
                <span className="text-fintech-emerald">0.08 (LOW RISK)</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-fintech-elevated border border-fintech-border">
                <span className="text-fintech-subtle">✓ Recovery Probability</span>
                <span className="text-fintech-cyan font-bold">82.0%</span>
              </div>
            </div>

            <div className="p-3 bg-fintech-elevated/90 border-l-2 border-fintech-cyan rounded text-xs text-fintech-subtle italic">
              "AI Decision Proposal: Execute automated payment retry via alternative route. High probability recovery without risk."
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 7 — POLICY GATE */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[6] = el)}
          className="min-h-screen flex items-center justify-center px-6 text-center"
        >
          <div className="section-card max-w-xl bg-fintech-surface/90 border border-fintech-border p-8 md:p-10 rounded-lg backdrop-blur-md space-y-6 glass-card-cyan">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-fintech-cyan/10 border border-fintech-cyan/30 text-fintech-cyan text-xs font-mono uppercase tracking-wider">
              <Lock className="w-3.5 h-3.5" /> Deterministic Policy Gate
            </div>

            <h3 className="text-3xl font-extrabold text-white tracking-tight uppercase">
              "AI proposes. Policy decides."
            </h3>

            <div className="grid grid-cols-2 gap-3 text-left font-mono text-xs">
              <div className="flex items-center justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span>RECOVERY ≥ 65%</span>
                <CheckCircle2 className="w-4 h-4 text-fintech-emerald" />
              </div>
              <div className="flex items-center justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span>AMOUNT ≤ ₹10,000</span>
                <CheckCircle2 className="w-4 h-4 text-fintech-emerald" />
              </div>
              <div className="flex items-center justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span>ATTEMPTS ≤ 2</span>
                <CheckCircle2 className="w-4 h-4 text-fintech-emerald" />
              </div>
              <div className="flex items-center justify-between p-3 rounded bg-fintech-elevated border border-fintech-border">
                <span>RISK PERMITS ACTION</span>
                <CheckCircle2 className="w-4 h-4 text-fintech-emerald" />
              </div>
            </div>

            <div className="p-3 bg-fintech-emerald/10 border border-fintech-emerald/30 text-fintech-emerald font-mono font-bold text-sm tracking-widest uppercase rounded">
              POLICY VERDICT: ALLOW (GATE UNLOCKED)
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 8 — RECOVERY */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[7] = el)}
          className="min-h-screen flex items-center justify-start px-6 md:px-20 max-w-6xl mx-auto"
        >
          <div className="section-card max-w-md bg-fintech-surface/90 border border-fintech-emerald/40 p-8 rounded-lg backdrop-blur-md space-y-5 shadow-emerald-glow glass-card-emerald">
            <span className="text-xs font-mono uppercase tracking-widest text-fintech-emerald flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" /> Bounded Execution Verified
            </span>
            <div className="text-5xl font-black text-white tracking-tight">₹2,999.00</div>
            <div className="text-xs font-mono text-fintech-emerald uppercase font-semibold">
              RECOVERED IN TEST MODE
            </div>
            <p className="text-sm text-fintech-subtle">
              Executed through Razorpay test rails. Payment state verified as captured. Complete telemetry written to audit logs.
            </p>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 9 — FINANCIAL PAYOFF */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[8] = el)}
          className="min-h-screen flex items-center justify-center px-6 text-center"
        >
          <div className="section-card max-w-2xl bg-fintech-surface/90 border border-fintech-border p-10 rounded-lg backdrop-blur-md space-y-6 animate-glowPulse glass-card-cyan">
            <span className="text-xs font-mono uppercase tracking-widest text-fintech-cyan">Live Merchant Yield</span>
            <div className="text-6xl sm:text-7xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-fintech-emerald via-fintech-cyan to-white">
              <AnimatedCounter value={21740} formatFn={formatINR} />
            </div>
            <div className="text-sm font-mono uppercase tracking-widest text-fintech-emerald font-semibold">
              TOTAL REVENUE RECOVERED
            </div>

            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-fintech-border text-center font-mono text-xs">
              <div>
                <div className="text-2xl font-bold text-white">
                  <AnimatedCounter value={3} />
                </div>
                <div className="text-fintech-muted uppercase text-[10px]">Actions Executed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-fintech-amber">
                  <AnimatedCounter value={2} />
                </div>
                <div className="text-fintech-muted uppercase text-[10px]">Escalated to Review</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-fintech-emerald">
                  <AnimatedCounter value={0} />
                </div>
                <div className="text-fintech-muted uppercase text-[10px]">Policy Violations</div>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* SECTION 10 — TRANSITION TO DASHBOARD */}
        {/* ========================================================================= */}
        <section
          ref={(el) => (sectionsRef.current[9] = el)}
          className="min-h-screen flex flex-col items-center justify-center text-center px-6"
        >
          <div className="max-w-xl space-y-8">
            <div className="space-y-3">
              <h2 className="text-4xl sm:text-5xl font-black text-white uppercase tracking-tight">
                Enter the Command Center
              </h2>
              <p className="text-fintech-subtle text-base font-light">
                Monitor recovery opportunities, configure deterministic policies, and converse with Qwen AI.
              </p>
            </div>

            <Link
              to="/dashboard"
              className="inline-flex items-center gap-3 px-8 py-4 text-sm font-bold uppercase tracking-wider text-fintech-dark bg-fintech-cyan hover:bg-fintech-cyan/90 rounded-md transition-all shadow-fintech-glow hover-glow"
            >
              Launch Command Center
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
};
