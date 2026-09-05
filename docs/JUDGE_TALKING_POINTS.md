# RazorMind AI — Judge Talking Points & Technical FAQ

Concise, technically honest answers for hackathon/buildathon judges and technical evaluators.

---

### 1. What problem are you solving?
Online merchants lose **15% to 20% of their revenue to failed payments** caused by soft bank declines, temporary network timeouts, or momentary credit limits. Today, businesses either do nothing (losing the customer) or use crude, dumb retry cronjobs that spam payment networks, annoy cardholders, and trigger fraud penalties.

---

### 2. Why is this better than a normal payment dashboard?
A standard dashboard is purely **passive** — it shows you how much money you lost after the fact. RazorMind AI is **active and autonomous** — it detects failures the moment webhooks arrive, investigates the customer and transaction profile, computes the probability of successful recovery, and executes targeted, policy-governed interventions in real time.

---

### 3. What is actually autonomous?
The entire 9-step recovery loop:
$$\text{Webhook Ingestion} \to \text{Feature Extraction} \to \text{ML Risk Scoring} \to \text{LLM Investigation} \to \text{Proposal} \to \text{Policy Check} \to \text{Execution} \to \text{Outcome Verification} \to \text{Audit Recording}$$
Once configured by the merchant, zero human intervention is required for transactions that fall within safe policy parameters.

---

### 4. What does the AI do?
Our local LLM (Qwen3-8B) acts as an **investigative reasoning agent**. It examines unstructured context, prior transaction history, failure codes, and customer velocity using structured tool calling (`get_customer_history`, `get_risk_score`, `get_policy`). It synthesizes these inputs to recommend the best recovery strategy (e.g., immediate retry, dynamic WhatsApp link, or human escalation).

---

### 5. What does the Policy Engine do?
The Policy Engine is a **code-enforced, deterministic mathematical gatekeeper**. It validates:
- Is the recovery amount under the merchant's automated cap (e.g., ₹10,000)?
- Is the calibrated recovery probability above the threshold (e.g., 65%)?
- Have prior attempts exceeded the limit (e.g., $\le$ 2)?
- Has the cooldown window elapsed (e.g., 60 minutes)?
- Is the proposed action on the merchant's approved whitelist?

---

### 6. Can the AI bypass the Policy Engine?
**No. Absolutely never.** The system follows a strict security invariant:
> **AI PROPOSES, POLICY DECIDES.**
The LLM has zero direct bindings or network credentials for payment execution APIs. All execution paths require an explicit `ALLOW` verdict from the deterministic Python Policy Engine. If the policy returns `DENY` or `REQUIRE_REVIEW`, execution is halted immediately.

---

### 7. How does Razorpay fit into the system?
Razorpay is the core payment gateway infrastructure:
1. **Ingestion:** Razorpay payment failure webhooks (`payment.failed`) trigger the RazorMind pipeline.
2. **Telemetry:** The backend synchronizes order and payment telemetry via the official Razorpay Python SDK.
3. **Execution:** Approved recovery actions trigger targeted payment orders and customer checkout links in Razorpay Test Mode.

---

### 8. What ML models are used?
RazorMind uses a layered scikit-learn statistical ML pipeline:
1. **Fraud & Risk Model:** Random Forest Classifier trained on transaction velocity, amount deviations, customer age, and failure frequency.
2. **Anomaly Detector:** Isolation Forest identifying abnormal transaction spikes or device fingerprint anomalies.
3. **Recovery Yield Predictor:** Calibrated Gradient Boosted Classifier predicting the likelihood (0.00–1.00) of successful recovery given error code and cardholder profile.

---

### 9. Why Qwen3-8B running locally?
1. **Financial Privacy & Compliance:** Customer cardholder data and merchant transaction amounts never leave the host machine or get sent to third-party cloud LLM APIs.
2. **Zero API Costs:** Local inference via quantized GGUF on `llama-server` eliminates variable token costs for recurring payment evaluations.
3. **Deterministic Function Calling:** Qwen3-8B excels at rigid JSON tool calling and structured output extraction.

---

### 10. What happens when recovery is unsafe?
When a transaction is scored as high risk, exceeds amount limits, or violates cooldown windows, the Policy Engine halts automated execution. It tags the opportunity as `REQUIRE_REVIEW`, leaves an immutable audit note, and surfaces it to the merchant's human operations dashboard. No unauthorized debit attempt is ever made.

---

### 11. How is everything audited?
Every workflow execution writes an immutable `AuditLog` flight record to the database:
- `actor`: Identifies the originating agent or merchant.
- `action`: Specific operation performed (`execute_recovery_workflow`, `evaluate_policy`).
- `decision`: Verdict (`ALLOW`, `DENY`, `REQUIRE_REVIEW`).
- `details`: Complete JSON payload including model weights, tool trace IDs, and gateway responses.

---

### 12. Is this using real money?
In this buildathon prototype, all payment interactions run in **Razorpay Test Mode** using sandbox API keys (`rzp_test_*`). This allows full functional verification of the payment lifecycle, webhooks, and recovery without incurring real financial risk or regulatory debit requirements.

---

### 13. What are the current limitations?
1. **Local Inference Hardware:** Running Qwen3-8B locally requires ~6GB of RAM and performs best with modern CPU/GPU acceleration.
2. **Test Mode Rails:** Real-world banking rails have 24-48 hour settlement cycles; Test Mode simulates instant confirmation.
3. **Android APK:** The Capacitor native Android project is 100% configured and synced, but the final APK binary requires a machine with the Android SDK installed.

---

### 14. How would this scale in production?
In a live production enterprise deployment:
- **Backend:** Scaled horizontally on Kubernetes behind an event-driven Redis/Kafka task queue to process thousands of webhooks per second.
- **Database:** Migrated to managed PostgreSQL (Supabase / AWS RDS) with read replicas.
- **Inference:** Hosted on a dedicated private vLLM or Triton inference cluster serving quantized open models with sub-100ms response times.
