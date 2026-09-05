# RazorMind AI — Buildathon Demo Script (3–5 Minutes)

This document provides the exact, deterministic script for presenting RazorMind AI to hackathon and buildathon judges.

---

## Pre-Demo Setup Checklist (1 Minute Before Presentation)

### 1. Launch Background Daemons
Open three terminal windows:
```powershell
# Terminal 1: Qwen3-8B Local LLM Inference Engine (Port 8080)
cd D:\RazorMind\models
llama-server.exe -m Qwen3-8B-Q4_K_M.gguf --port 8080 -c 4096 --host 127.0.0.1

# Terminal 2: FastAPI Autonomous Backend Engine (Port 8000)
cd D:\RazorMind\backend
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 3: Vite Frontend Command Center (Port 5173)
cd D:\RazorMind\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

### 2. Reset Deterministic Demo Database
Run the deterministic seeder to ensure clean starting data:
```powershell
cd D:\RazorMind\backend
.venv\Scripts\python scripts\seed_demo.py
```
*Expected output:* `BUILDATHON DEMO ENVIRONMENT READY`

### 3. Open Browser
Open Google Chrome or Microsoft Edge at `http://127.0.0.1:5173/`.

---

## Live Presentation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SCENE 1    │     │   SCENE 2    │     │   SCENE 3    │     │   SCENE 4    │
│ The Problem  │ ──> │Command Center│ ──> │Failed Payment│ ──> │AI Investigate│
│   Landing    │     │  /dashboard  │     │  /recovery   │     │     /ai      │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   SCENE 5    │     │   SCENE 6    │     │   SCENE 7    │     │   SCENE 8    │
│ Policy Gate  │ ──> │ Real Recovery│ ──> │ Audit Flight │ ──> │ Safety Block │
│  /policies   │     │  /recovery   │     │    /audit    │     │ /policies/sim│
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

### Scene 1 — The Problem (30 seconds)
- **URL:** `http://127.0.0.1:5173/`
- **Visual:** Cinematic 3D interactive particle constellation, glowing financial nodes.
- **Spoken Script:**
  > "Every year, online businesses lose up to 15% to 20% of their top-line revenue to transient payment failures. Traditional retry systems are blind and aggressive: they blindly retry cards until banks block them or trigger dispute fees.
  >
  > Welcome to **RazorMind AI** — an autonomous financial intelligence platform that investigates payment failures, predicts recovery yield, proposes targeted recovery actions, enforces deterministic policy guardrails, and audits every financial execution."

---

### Scene 2 — Command Center Telemetry (30 seconds)
- **URL:** Click **"Launch App"** or navigate to `http://127.0.0.1:5173/dashboard`
- **Visual:** Live KPI cards with animated count-up numbers:
  - *Processed Volume:* ₹1,48,991.00
  - *Recoverable Revenue:* ₹1,08,392.50
  - *Risk Tier Distribution:* Machine learning risk classification
- **Spoken Script:**
  > "This is the RazorMind Command Center. Every metric you see is streaming directly from our FastAPI backend and SQLite database.
  >
  > Out of ₹1.48 Lakhs in transaction volume, our calibrated ML models have identified over ₹1.08 Lakhs in potential recoverable revenue. Let's see how the system handles an actual payment failure."

---

### Scene 3 — The Failed Payment Opportunity (30 seconds)
- **URL:** Navigate to `http://127.0.0.1:5173/recovery`
- **Visual:** 9-Step Autonomous Recovery Engine visualizer (`OBSERVE` $\to$ `DETECT` $\to$ `INVESTIGATE` $\to$ `DECIDE` $\to$ `POLICY GATE` $\to$ `ACT` $\to$ `VERIFY` $\to$ `AUDIT` $\to$ `LEARN`).
- **Focus:** Highlight the failed transaction of **₹2,999.00** with **85.0% Recovery Yield**.
- **Spoken Script:**
  > "Here in the Revenue Recovery stream, we see an incoming failed payment of ₹2,999. Notice the yield score: 85%.
  >
  > Rather than blasting the payment gateway blindly, RazorMind initiates an AI-driven investigation."

---

### Scene 4 — AI Investigation (45 seconds)
- **URL:** Navigate to `http://127.0.0.1:5173/ai`
- **Action:** In the prompt box, click the suggestion chip or type:
  ```text
  Why should the failed payment of Rs 2,999 be considered for recovery?
  ```
- **Visual:** Qwen3-8B status shows `ONLINE (GGUF Local)`. The AI executes tool `get_transaction`, evaluates cardholder history, and outputs structured reasoning:
  - Cardholder has a strong historical completion rate.
  - Failure reason was transient (`network_timeout` / soft decline).
  - Risk tier is `LOW` (0.08).
  - Recommended action: `retry_payment`.
- **Spoken Script:**
  > "We just asked our local Qwen3-8B model to investigate. Notice that the AI doesn't just hallucinate a response — it invoked backend query tools to inspect customer history and risk scores.
  >
  > But here is our core philosophy: **AI PROPOSES, POLICY DECIDES.** The AI cannot directly touch payment rails."

---

### Scene 5 — Deterministic Policy Guardrails (30 seconds)
- **URL:** Navigate to `http://127.0.0.1:5173/policies`
- **Visual:** Active Merchant Guardrails:
  - Minimum Recovery Probability: `65.0%`
  - Maximum Automated Amount: `₹10,000.00`
  - Maximum Retry Attempts: `2 Attempts`
  - Cooldown Interval: `60 Minutes`
  - Allowed Actions: `retry_payment, send_payment_reminder, create_followup`
- **Spoken Script:**
  > "These are the merchant's mathematical guardrails. If an AI proposes an action, our Policy Engine evaluates whether the amount is below ₹10,000, whether the ML probability is above 65%, whether attempts are under the limit, and whether the cooldown has elapsed.
  >
  > The LLM has zero authority to bypass this engine."

---

### Scene 6 — Autonomous Execution & Recovery (45 seconds)
- **URL:** Navigate to `http://127.0.0.1:5173/recovery`
- **Action:** Click **"Autonomous Recovery"** or run the automated verification:
  ```powershell
  .venv\Scripts\python scripts\verify_phase8_recovery.py
  ```
- **Visual:** Workflow executes:
  - Step 1–4: AI proposes `retry_payment`
  - Step 5: Policy Engine returns `ALLOW`
  - Step 6: Razorpay Test Mode execution triggers
  - Step 7: Verification confirms status: `RECOVERED`
  - Step 8: ₹2,999.00 recovered!
- **Spoken Script:**
  > "When we execute the workflow, the policy engine confirmed `ALLOW`. The system triggered the safe payment attempt in Razorpay Test Mode, verified the result, and recovered the full ₹2,999."

---

### Scene 7 — Tamper-Evident Flight Recorder / Audit (30 seconds)
- **URL:** Navigate to `http://127.0.0.1:5173/audit`
- **Visual:** Flight Recorder table displaying the latest audit records:
  - `actor`: `razormind_ai_agent`
  - `action`: `execute_recovery_workflow`
  - `resource`: `recovery_opportunity`
  - `decision`: `ALLOW`
  - `reason`: Full telemetry payload
- **Spoken Script:**
  > "Finally, look at the Flight Recorder. Every single recommendation made by the AI, every rule checked by the policy engine, and every financial rupee moved is stored in an immutable audit ledger.
  >
  > If a compliance officer or auditor asks why a retry was triggered, we have complete cryptographic provenance."

---

### Scene 8 — The Safety Demonstration (Stopping Rule) (30 seconds)
- **Action:** Open `backend/scripts/verify_phase8_recovery.py` output or demonstrate the Policy Gate Simulator on `/policies`:
  - Input: Amount = ₹25,000.00 (Exceeds ₹10,000 cap)
  - Result: `REQUIRE_REVIEW` (Auto-recovery halted)
  - Input: Risk = HIGH (Anomaly detected)
  - Result: `DENY` (Auto-retry blocked)
- **Spoken Script:**
  > "What happens when recovery is unsafe? Here you see our negative stopping rules in action: when an amount exceeds ₹10,000 or risk is high, the system immediately locks the workflow into `REQUIRE_REVIEW`.
  >
  > Autonomy is strictly bounded by deterministic merchant policy."

---

## Fallback Contingency Plan

| Scenario | Contingency Action |
|:---|:---|
| **Local LLM is slow to respond (< 10 tokens/sec)** | Pre-run the query in `/ai` prior to judge arrival; show the verified tool execution badge and audit record `4664121a`. |
| **Port conflict on 8000 or 5173** | Run `Get-NetTCPConnection -LocalPort 8000,5173` and kill conflicting PID. |
| **Judge requests terminal proof** | Run `.venv\Scripts\python scripts\verify_phase8_recovery.py` directly in terminal — shows all 6 test cases passing in under 4 seconds. |
