# RazorMind AI — One-Page Executive Brief

**Tagline:** Autonomous Financial Intelligence for Revenue Leakage Detection, Recovery, and Audit.

---

### PROBLEM
Online merchants running high-volume payments lose **15% to 20% of their top-line revenue** to failed transactions (soft bank declines, transient network drops, and dynamic card limits). Today, merchants rely on dumb, aggressive cronjobs that spam networks or do nothing at all, leading to customer churn, disputes, and lost revenue.

### SOLUTION
**RazorMind AI** is an autonomous revenue protection and recovery platform. It replaces blunt retry rules with an intelligent, closed-loop system: an AI agent that investigates payment failures, calibrated ML models that predict recovery yield, a deterministic Policy Engine that enforces merchant safety rules, and an immutable audit flight recorder.

### HOW IT WORKS
1. **Detect:** Real-time Razorpay webhooks alert RazorMind to a failed payment.
2. **Investigate:** Machine learning scores fraud risk while our local open-weight LLM (Qwen3-8B) investigates cardholder history and decline context.
3. **Propose:** The AI recommends a context-aware intervention (e.g., targeted retry, personalized payment link).
4. **Govern:** A deterministic Policy Engine evaluates the proposal against merchant caps (amounts, attempt limits, risk tiers).
5. **Act & Verify:** Approved actions execute via Razorpay Test Mode rails, verify outcome, and update financial ledgers.
6. **Audit:** Every step is logged in a cryptographically auditable flight record.

### AI
Powered by **Qwen3-8B-Q4_K_M** running locally via `llama-server`. The AI utilizes 13 registered inspection tools (`get_customer_history`, `get_risk_score`, `get_policy`) to produce structured JSON reasoning without risking external data leakage.

### ML
A layered scikit-learn statistical pipeline:
- **Random Forest:** Evaluates transaction velocity, deviation from merchant norms, and fraud likelihood.
- **Isolation Forest:** Detects behavioral and network anomalies.
- **Gradient Boosted Classifier:** Predicts calibrated recovery probability (0.00 to 1.00) based on issuer response codes.

### POLICY GOVERNANCE
**Core Security Rule:** *AI PROPOSES, POLICY DECIDES.*  
The LLM has zero direct write access to payment rails. A deterministic Python engine evaluates hard rules (max amount ₹10,000, min prob 65%, max 2 attempts, 60m cooldown). Unsafe transactions are halted into `REQUIRE_REVIEW`.

### RAZORPAY
Deeply integrated with the Razorpay ecosystem:
- Listens to `payment.failed`, `order.paid`, and checkout events.
- Leverages the official Razorpay Python SDK for test order creation, payment status polling, and customer link generation.

### REVENUE RECOVERY
Implements a 9-step orchestration engine:
`OBSERVE` $\to$ `DETECT` $\to$ `INVESTIGATE` $\to$ `DECIDE` $\to$ `POLICY CHECK` $\to$ `ACT` $\to$ `VERIFY` $\to$ `AUDIT` $\to$ `LEARN`. In verified testing, it successfully recovered **₹2,999.00** from a soft decline.

### AUDITABILITY
Every autonomous event creates an immutable `AuditLog` entry detailing actor, action, timestamp, policy verdict (`ALLOW`, `DENY`, `REQUIRE_REVIEW`), tool trace IDs, and full JSON metadata.

### TECH STACK
- **Frontend:** React 18, TypeScript, Vite 6, TailwindCSS, Three.js, Recharts, Framer Motion.
- **Backend:** FastAPI, Python 3.10+, SQLAlchemy, Pydantic v2, SQLite / PostgreSQL.
- **AI/ML:** Qwen3-8B GGUF, Scikit-Learn, Joblib, NumPy.
- **Mobile:** Capacitor v8 native Android project (`com.razormind.ai`).

### DEMO
Run in 3 simple commands:
```powershell
# 1. Reset Demo State:  .venv\Scripts\python scripts\seed_demo.py
# 2. Run Verification:  .venv\Scripts\python scripts\verify_phase8_recovery.py
# 3. Launch UI:         http://localhost:5173
```

### LIMITATIONS
Operates in Razorpay Test Mode; local LLM inference requires ~6GB RAM; native Android APK binary compilation requires an external host with the Android SDK installed.
