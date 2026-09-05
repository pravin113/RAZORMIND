# RazorMind AI — Autonomous Financial Intelligence Platform

> **Buildathon Submission:** Autonomous revenue protection, payment failure investigation, deterministic policy governance, and tamper-evident audit logging for modern digital merchants.

---

## 1. The Problem
Online merchants lose **15% to 20% of their top-line revenue** to transient payment failures — soft bank declines, brief telecom network drops, or momentary card limit constraints. Today, businesses face two bad options:
1. **Blind Retries:** Dumb cronjobs spam payment networks, triggering customer annoyance, bank friction, and fraud penalties.
2. **Inaction:** Finance teams lack the bandwidth to manually inspect thousands of declines, losing customers to silent churn.

---

## 2. Core Features

- **Autonomous 9-Step Recovery Lifecycle:** Detects failures in real time, investigates context, computes recovery probability, executes authorized interventions, and confirms outcomes.
- **Deterministic Policy Engine:** Mathematical, code-enforced guardrails ensure that **AI PROPOSES, POLICY DECIDES**. The LLM cannot unilaterally move funds or override merchant caps.
- **100% Private Local Agent Reasoning:** Powered by **Qwen3-8B-Q4_K_M** running locally via `llama-server`. Zero customer cardholder data or sensitive financial telemetry leaves your infrastructure.
- **Calibrated ML Models:** Multi-layer scikit-learn models for fraud risk classification, isolation forest anomaly detection, and calibrated recovery yield estimation.
- **Razorpay Integration:** Real-time webhook ingestion (`payment.failed`), test order generation, and payment status verification.
- **Immutable Flight Recorder:** Tamper-evident, queryable audit log storing decision IDs, prompt tokens, policy rules, and financial outcome deltas.
- **Institutional Command Center:** React 18 + Vite 6 UI featuring an interactive 3D particle universe (Three.js), live telemetry charts (Recharts), and animated cubic ease-out metric counters.
- **Mobile Native Ready:** Cross-platform Capacitor Android project initialized and synced (`com.razormind.ai`).

---

## 3. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAZORMIND AI ARCHITECTURE                       │
└────────────────────────────────────────────────────────────────────────┘

  [ PRESENTATION ]  React 18 + Vite 6 + TailwindCSS + Three.js + Recharts
         │ (REST API / JSON)
  [ APPLICATION ]   FastAPI Async Gateway + SQLAlchemy + SQLite / PostgreSQL
         │
         ├─── [ ML LAYER ]       Random Forest (Risk) + GBC (Yield Predictor)
         ├─── [ AGENT LAYER ]    Qwen3-8B Local GGUF (13 Inspection Tools)
         ├─── [ POLICY GATE ]    Deterministic Guardrails (Amount/Prob/Limits)
         └─── [ RAILS ]          Razorpay Gateway (Test Mode / Webhooks)
```

---

## 4. Technology Stack

| Layer | Technology |
|:---|:---|
| **Frontend** | React 18, TypeScript 5.7, Vite 6, TailwindCSS, Three.js, Recharts, Framer Motion |
| **Backend** | FastAPI, Python 3.10+, SQLAlchemy, Pydantic v2, SQLite / PostgreSQL |
| **Local LLM** | Qwen3-8B-Q4_K_M GGUF via `llama-server.exe` (Port 8080) |
| **Machine Learning** | Scikit-Learn (Random Forest, Isolation Forest, Gradient Boosting), Joblib, NumPy |
| **Mobile** | Capacitor v8 Android Platform (`com.razormind.ai`) |
| **Payments** | Razorpay Python SDK (Test Mode Rails) |

---

## 5. Quick Start & Setup

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm
- [llama-server](https://github.com/ggerganov/llama.cpp) (for local LLM inference)

### 1. Backend Setup
```powershell
cd D:\RazorMind\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Setup
```powershell
cd D:\RazorMind\frontend
npm install
```

### 3. Launch Services
```powershell
# Terminal 1: Local Qwen3-8B Model
llama-server.exe -m D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf --port 8080 -c 4096 --host 127.0.0.1

# Terminal 2: FastAPI Backend Engine
cd D:\RazorMind\backend
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 3: Frontend Command Center
cd D:\RazorMind\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
Open `http://127.0.0.1:5173/` in your browser.

---

## 6. Deterministic Demo Walkthrough

### 1. Reset Clean Demo State
```powershell
cd D:\RazorMind\backend
.venv\Scripts\python scripts\seed_demo.py
```

### 2. Run Automated Lifecycle & Policy Proof
```powershell
cd D:\RazorMind\backend
.venv\Scripts\python scripts\verify_phase8_recovery.py
```
*Expected Output:* Confirms positive recovery of **₹2,999.00** alongside 5/5 blocked negative safety scenarios.

### 3. Visual Presentation Flow
- **Landing (`/`)**: Cinematic 3D interactive particle constellation.
- **Dashboard (`/dashboard`)**: Live KPI metrics streaming from the backend.
- **Recovery (`/recovery`)**: 9-step autonomous orchestration visualizer and pending opportunity stream.
- **AI Console (`/ai`)**: Chat with Qwen3-8B; observe tool invocation (`get_transaction`) and structured reasoning.
- **Policies (`/policies`)**: Deterministic merchant limits (Amount < ₹10,000, Probability > 65%).
- **Audit (`/audit`)**: Cryptographically auditable flight recorder showing timestamps, actors, verdicts, and payloads.

---

## 7. Testing & Verification

### Backend Pytest Suite
```powershell
cd D:\RazorMind\backend
.venv\Scripts\pytest -q
# Result: 88 passed in 30.48s
```

### Frontend Vitest Suite
```powershell
cd D:\RazorMind\frontend
npm test
# Result: 8 passed in 742ms
```

### Production Build
```powershell
cd D:\RazorMind\frontend
npm run build
# Result: 0 TypeScript errors, optimized chunks in dist/
```

---

## 8. Android Mobile Packaging

The project includes an initialized and synced native Android platform via Capacitor:
- **App ID:** `com.razormind.ai`
- **Native Project:** `frontend/android/`
- **Status:** Web assets synced into Android distribution. Host environment requires Android SDK Platform 34 to compile `.apk` binary.
- Complete instructions available in [docs/ANDROID_BUILD.md](file:///D:/RazorMind/docs/ANDROID_BUILD.md).

---

## 9. Security & Governance Invariant

> **AI PROPOSES, POLICY DECIDES. SYSTEM ACTS. EVERYTHING IS AUDITED.**

- **No Hallucinated Actions:** The LLM has zero direct write bindings to payment gateways.
- **Code-Enforced Gatekeeper:** Pure Python Policy Engine determines `ALLOW`, `DENY`, or `REQUIRE_REVIEW`.
- **Zero Cloud Leakage:** All inference runs on-premise/locally via GGUF quantization.
- **Strict Hygiene:** No live keys, passwords, or production secrets in source code; comprehensive root [.gitignore](file:///D:/RazorMind/.gitignore) enforced.

---

## 10. Limitations & Production Path

- **Gateway Sandbox:** Currently executes against Razorpay Test Mode rails (`rzp_test_*`).
- **Inference Hardware:** Local CPU inference on 8B parameters requires 8–25s per multi-tool turn; production deployments recommend dedicated GPU worker nodes (vLLM / Triton).
- Full details documented in [docs/LIMITATIONS.md](file:///D:/RazorMind/docs/LIMITATIONS.md).

---

## 11. Documentation Directory (`docs/`)

- [docs/BUILDBATHON_DEMO_SCRIPT.md](file:///D:/RazorMind/docs/BUILDBATHON_DEMO_SCRIPT.md) — Exact 3–5 min judge presentation script.
- [docs/JUDGE_TALKING_POINTS.md](file:///D:/RazorMind/docs/JUDGE_TALKING_POINTS.md) — Technical FAQ covering 14 critical evaluation questions.
- [docs/RAZORMIND_ARCHITECTURE.md](file:///D:/RazorMind/docs/RAZORMIND_ARCHITECTURE.md) — Detailed architecture layers and Mermaid diagrams.
- [docs/RAZORMIND_ONE_PAGE.md](file:///D:/RazorMind/docs/RAZORMIND_ONE_PAGE.md) — One-page executive brief.
- [docs/BUILDBATHON_PRESENTATION.md](file:///D:/RazorMind/docs/BUILDBATHON_PRESENTATION.md) — 7-slide visual pitch deck.
- [docs/2_MINUTE_PITCH.md](file:///D:/RazorMind/docs/2_MINUTE_PITCH.md) — 120-second fast-paced verbal pitch.
- [docs/5_MINUTE_PITCH.md](file:///D:/RazorMind/docs/5_MINUTE_PITCH.md) — 300-second comprehensive presentation with live demo marks.
- [docs/ANDROID_BUILD.md](file:///D:/RazorMind/docs/ANDROID_BUILD.md) — Detailed Android APK reproduction guide and SDK requirements.
- [docs/LIMITATIONS.md](file:///D:/RazorMind/docs/LIMITATIONS.md) — Transparent analysis of current constraints and production roadmap.
- [docs/FINAL_RELEASE_REPORT.md](file:///D:/RazorMind/docs/FINAL_RELEASE_REPORT.md) — Official release verification sign-off document.
