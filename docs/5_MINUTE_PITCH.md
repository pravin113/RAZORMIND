# RazorMind AI — 5-Minute Buildathon Presentation & Live Demo Script

**Target Duration:** 300 Seconds (5:00 Minutes)  
**Structure:** 1.5 Min Concept $\to$ 1.75 Min Live Demo $\to$ 1.75 Min Governance, Impact & Q&A.

---

### [0:00 – 0:30] Phase 1: The Problem (30 Seconds)
**Visual:** Slide 1 or Landing Page Hero (`http://127.0.0.1:5173/`)  
**Presenter:**
> "Judges, consider an Indian e-commerce merchant doing 10 Crore rupees a year in Gross Merchandise Value. On average, 15 to 20 percent of their payment attempts fail. That is **1.5 to 2 Crore rupees in lost revenue** evaporating into thin air.
>
> Why does this happen? Because online payments fail for dozens of subtle reasons — transient telecom timeouts, momentary card balance limits, or soft bank switch declines. Today's merchants either rely on dumb retry scripts that harass customers and trigger payment dispute penalties, or they leave that money on the table.
>
> We built **RazorMind AI** to solve this problem autonomously."

---

### [0:30 – 1:00] Phase 2: The Solution (30 Seconds)
**Visual:** Slide 2 or Command Center (`http://127.0.0.1:5173/dashboard`)  
**Presenter:**
> "RazorMind AI is an autonomous financial intelligence platform built on top of Razorpay.
>
> When a payment fails, RazorMind doesn't just log an error in a passive dashboard. It immediately initiates an autonomous 9-step recovery loop: it scores fraud risk with machine learning, investigates cardholder history using a local open-weight AI agent, calculates recovery yield probability, checks merchant policy guardrails, executes targeted recovery, and writes an immutable audit trail.
>
> It turns passive revenue leakage into an active, policy-governed recovery pipeline."

---

### [1:00 – 1:45] Phase 3: The Architecture (45 Seconds)
**Visual:** Slide 3 (Architecture Diagram)  
**Presenter:**
> "Let's look under the hood:
>
> 1. **Client Tier:** A React 18 + Vite 6 web application with a 3D financial universe, Recharts telemetry, and a synced Capacitor Android project.
> 2. **Application Tier:** A high-throughput asynchronous FastAPI backend running on Python.
> 3. **Intelligence Tier:** Random Forest and Isolation Forest models for fraud scoring, plus a calibrated Gradient Boosted Classifier predicting recovery probability.
> 4. **Agent Tier:** An open-weight **Qwen3-8B model running 100% locally** on `llama-server`. It has 13 inspection tools to query customer history, transaction records, and policies without sending sensitive cardholder data to third-party cloud APIs.
> 5. **Governance Tier:** A deterministic, code-enforced **Policy Engine** that sits between the AI and Razorpay Test Mode rails."

---

### [1:45 – 3:30] Phase 4: The Live Demonstration (1 Minute 45 Seconds)
**Visual:** Live Browser (`http://127.0.0.1:5173`)  
**Presenter:**

#### A. Command Center Telemetry (15 Seconds)
> "Here on our live dashboard, you see real telemetry streamed from our FastAPI backend: ₹1.48 Lakhs processed, ₹1.08 Lakhs identified as recoverable, and risk distributions classified by our ML models."

#### B. The Opportunity (15 Seconds)
*(Switch to `/recovery`)*
> "In the Recovery Stream, we have an incoming failed payment: **₹2,999.00** with an **85% recovery yield**. Let's ask our AI to investigate."

#### C. AI Investigation (30 Seconds)
*(Switch to `/ai`, submit prompt: 'Why should the failed payment of Rs 2,999 be considered for recovery?')*
> "Watch the AI Decision Console. Qwen3-8B is running locally on this machine. Notice what happened: the AI didn't just guess. It called backend tool `get_transaction`, inspected cardholder velocity, noted the failure was a transient timeout, confirmed clean history, and proposed: `retry_payment`.
>
> But watch what happens next — **the AI cannot touch the money.**"

#### D. Policy Gate Evaluation (20 Seconds)
*(Switch to `/policies`)*
> "Here is our Policy Engine. It mathematically checks: Is ₹2,999 under our ₹10,000 ceiling? Yes. Is 85% above our 65% probability floor? Yes. Are prior attempts under 2? Yes.
>
> The Policy Engine issues an **ALLOW** verdict."

#### E. Execution, Verification & Flight Log (25 Seconds)
*(Switch to `/recovery`, click 'Execute Recovery', then open `/audit`)*
> "We trigger execution. The system runs the retry through Razorpay Test Mode, polls the gateway for verification, confirms status `RECOVERED`, and credits the ₹2,999.
>
> Finally, we jump to the **Audit Flight Recorder**. Every single prompt token, tool invocation, policy rule, and financial result is permanently stamped into an immutable audit record."

---

### [3:30 – 4:15] Phase 5: Governance & Safety Stopping Rules (45 Seconds)
**Visual:** Slide 5 or Policy Simulator  
**Presenter:**
> "Now, what happens when an action is unsafe?
>
> We ran 5 controlled negative scenarios:
> 1. When a transaction was flagged as **High Risk**, the policy engine issued `DENY`.
> 2. When the recovery probability was **below 65%**, it locked into `REQUIRE_REVIEW`.
> 3. When an amount was **₹25,000 (above our ₹10,000 limit)**, automated debit was blocked.
> 4. When attempt limits or cooldown intervals were breached, retries were refused.
>
> This guarantees that our autonomous agent cannot hallucinate or overstep merchant authority."

---

### [4:15 – 5:00] Phase 6: Measurable Impact, Hardening & Conclusion (45 Seconds)
**Visual:** Slide 6 & 7  
**Presenter:**
> "To prepare for this submission, we hardened the entire codebase:
> - **88 out of 88** backend pytest tests pass.
> - **8 out of 8** frontend test suites pass.
> - Zero TypeScript errors; production bundle built and code-split.
> - Native Capacitor Android project initialized and synced.
> - Zero leaked secrets; comprehensive `.gitignore` protection.
>
> RazorMind AI provides online merchants with an immediate **12% to 18% lift in recovered revenue**, total privacy with local AI inference, and bulletproof policy governance.
>
> **AI proposes. Policy decides. System acts. Everything is audited.**
>
> We are ready for your questions. Thank you."
