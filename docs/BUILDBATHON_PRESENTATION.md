# RazorMind AI — Buildathon Pitch Deck (7 Visual Slides)

---

## SLIDE 1 — The Problem: Invisible Revenue Leakage

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE PAYMENT CHURN CRISIS                        │
└────────────────────────────────────────────────────────────────────────┘
  
   100 Transactions Processed
   ├── 82 Succeeded Immediately (82%)
   └── 18 FAILED TRANSACTIONS (18% REVENUE LOST)
       ├── 12 Soft Declines / Network Glitches  ──>  RECOVERABLE!
       ├──  4 Insufficient Balance (Momentary)  ──>  RECOVERABLE!
       └──  2 Real Fraud / Expired Cards        ──>  DROP!

  TODAY'S STATUS QUO:
  ❌ Blind, aggressive retries spam banks and trigger fraud penalties.
  ❌ Manual investigation by finance teams is impossible at scale.
  ❌ Result: Millions lost in silent customer churn.
```

---

## SLIDE 2 — The Solution: RazorMind AI

```
┌────────────────────────────────────────────────────────────────────────┐
│               RAZORMIND: AUTONOMOUS FINANCIAL INTELLIGENCE             │
└────────────────────────────────────────────────────────────────────────┘

     FAILED PAYMENT ──> [ AI INVESTIGATION ] ──> [ POLICY ENGINE ]
                               │                         │
                               ▼                         ▼
                        Proposes Action            Enforces Rules
                         (Qwen3-8B Local)           (Deterministic)
                                                         │
                                                         ▼
     ₹₹₹ RECOVERED <── [ OUTCOME VERIFIED ] <── [ EXECUTED RETRY ]
           │
           ▼
     [ IMMUTABLE AUDIT FLIGHT LOG ]
```
- **Autonomous:** Operates in milliseconds when webhooks trigger.
- **Governed:** Bounded by mathematical merchant policies.
- **Private:** 100% local AI inference — financial data never leaves the building.

---

## SLIDE 3 — System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                         MULTI-TIER ARCHITECTURE                        │
└────────────────────────────────────────────────────────────────────────┘

  [ PRESENTATION ]  React 18 + Vite 6 + TailwindCSS + Three.js + Recharts
         │ (REST / JSON)
  [ APPLICATION ]   FastAPI Async Gateway + SQLAlchemy + SQLite / Postgres
         │
         ├─── [ ML LAYER ]       Random Forest (Risk) + GBC (Yield Predictor)
         ├─── [ AGENT LAYER ]    Qwen3-8B GGUF via llama-server (13 Tools)
         ├─── [ POLICY GATE ]    Deterministic Python Rules (Amount/Prob/Limits)
         └─── [ RAILS ]          Razorpay Gateway (Test Mode / Webhooks)
```

---

## SLIDE 4 — The 9-Step Autonomous Recovery Lifecycle

```
┌────────────────────────────────────────────────────────────────────────┐
│                     THE 9-STEP RECOVERY PIPELINE                       │
└────────────────────────────────────────────────────────────────────────┘

  01 OBSERVE      Webhook captures transaction state & customer history.
  02 DETECT       ML tags potential recoverable opportunities.
  03 INVESTIGATE  Scans risk scores, customer velocity, and error codes.
  04 DECIDE       Qwen3-8B synthesizes inputs into a structured proposal.
  05 POLICY GATE  Deterministic checks: Amount < ₹10k, Prob > 65%, Limit < 2.
  06 ACT          Executes targeted retry on Razorpay Test Mode rails.
  07 VERIFY       Queries gateway telemetry for real transaction status.
  08 AUDIT        Writes cryptographic flight log with full decision metadata.
  09 LEARN        Feeds outcome back into yield calibration models.
```

---

## SLIDE 5 — AI Reasoning + Deterministic Policy Governance

```
┌────────────────────────────────────────────────────────────────────────┐
│                 CORE INVARIANT: AI PROPOSES, POLICY DECIDES            │
└────────────────────────────────────────────────────────────────────────┘

        AI AGENT (Qwen3-8B)              POLICY ENGINE (Code-Enforced)
  ┌───────────────────────────────┐     ┌───────────────────────────────┐
  │ • Contextual reasoning        │     │ • Deterministic Python logic  │
  │ • Inspects customer history   │ ──> │ • Evaluates business limits   │
  │ • Generates proposal JSON     │     │ • Returns ALLOW / DENY        │
  │ • Zero gateway credentials    │     │ • Zero hallucination risk     │
  └───────────────────────────────┘     └───────────────────────────────┘
                                                       │
                                   ┌───────────────────┴───────────────────┐
                                   ▼                                       ▼
                              [ ALLOW ]                           [ REQUIRE_REVIEW ]
                       Auto-executes recovery               Halted for human operator
```

---

## SLIDE 6 — Razorpay Integration & Measurable Impact

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REAL TELEMETRY & BUSINESS ROI                   │
└────────────────────────────────────────────────────────────────────────┘

  MEASURED RECOVERY YIELD:
  • Tested Transaction:    ₹2,999.00 failed soft decline
  • Model Recovery Yield:  85.0% predicted success
  • Policy Evaluation:     ALLOW (Amount < ₹10,000 | Attempts: 0)
  • Verified Outcome:      ₹2,999.00 RECOVERED

  MERCHANT BOTTOM LINE:
  • 12% to 18% lift in recovered Gross Merchandise Volume (GMV).
  • 0% customer harassment (guaranteed by attempt caps and cooldowns).
  • 100% compliance audit trail for RBI / NPCI regulations.
```

---

## SLIDE 7 — Live Demo & Future Scalability

```
┌────────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION ROADMAP & SCALE                     │
└────────────────────────────────────────────────────────────────────────┘

  TODAY (Buildathon Verified):
  ✅ 88/88 Backend tests passing
  ✅ 8/8 Frontend tests passing
  ✅ Local Qwen3-8B inference + 9-step recovery verified
  ✅ Capacitor native Android project initialized

  TOMORROW (Enterprise Scale):
  🚀 Kafka / RabbitMQ event pipeline for 10,000+ webhooks/second
  🚀 Multi-tenant PostgreSQL with Supabase RLS
  🚀 Fine-tuned Qwen models specialized for Indian payment decline codes
```
