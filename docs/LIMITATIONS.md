# RazorMind AI — Technical Limitations & Production Readiness

Honesty and technical integrity are central to RazorMind AI. This document transparently outlines the known limitations of the current buildathon release, along with the concrete engineering steps required for enterprise production deployment.

---

## 1. Gateway & Payment Rails: Razorpay Test Mode
- **Current State:** The entire payment lifecycle operates in **Razorpay Test Mode** using sandbox API keys (`rzp_test_*`).
- **Limitation:** In sandbox mode, bank responses and charge states are simulated instantly. Real banking rails (Visa/Mastercard/RuPay networks, NPCI UPI switches, netbanking gateways) exhibit real-world latency (2–48 hours for dispute notices and settlement confirmation).
- **Production Path:** Transition to Razorpay Live API keys (`rzp_live_*`), implement IP-whitelisted webhook endpoints over HTTPS with TLS 1.3, and register for Razorpay Optimizer automated routing.

---

## 2. Local AI Inference & Hardware Constraints
- **Current State:** The investigative AI agent uses an open-weight **Qwen3-8B model quantized to Q4_K_M** running locally via `llama-server`.
- **Limitation:** On CPU-only development machines without discrete GPUs, generating structured multi-step reasoning with tool calling takes between **8 to 25 seconds**. While acceptable for asynchronous background recovery, it requires patience during interactive live demonstrations.
- **Production Path:** In production, decouple agent reasoning into an asynchronous worker pool running on dedicated GPU infrastructure (e.g., vLLM or Triton Inference Server on NVIDIA A10G/L4 GPUs), reducing inference latency to under 300ms.

---

## 3. Machine Learning Training Data & Model Scope
- **Current State:** The ML models (Random Forest for fraud scoring, Isolation Forest for anomaly detection, and Gradient Boosted Classifier for recovery yield) were trained and validated on a synthetic dataset of 5,000 realistic e-commerce payment transactions.
- **Limitation:** Real merchant transaction distributions vary dramatically by industry vertical (e.g., SaaS recurring billing vs quick-commerce vs high-ticket luxury). The current model weights reflect general e-commerce patterns and need merchant-specific calibration.
- **Production Path:** Implement an ongoing online learning loop (`app/ai/workflows/recovery_orchestrator.py` Step 9: `LEARN`) that ingests confirmed `RecoveryOutcome` records, recalibrates priors per merchant tenant, and exports versioned model artifacts weekly.

---

## 4. Mobile Native Build (Android APK Status)
- **Current State:** The Capacitor cross-platform framework is fully initialized, `capacitor.config.ts` is configured with `com.razormind.ai`, production web assets are synced into `frontend/android/app/src/main/assets/public`, and the Gradle 8.14.3 wrapper is verified.
- **Limitation:** The host Windows development environment lacks the standalone Android SDK / `sdkmanager`. As a result, the final binary `.apk` file could not be compiled on this machine.
- **Production Path:** Documented in [docs/ANDROID_BUILD.md](file:///D:/RazorMind/docs/ANDROID_BUILD.md). Installing Android Studio or configuring CI/CD with GitHub Actions using an `ubuntu-latest` runner with `setup-android` will compile the APK automatically.

---

## 5. Storage & Concurrency
- **Current State:** Defaults to a local SQLite database (`backend/app/db/razormind.db`) for zero-dependency local verification and testing.
- **Limitation:** SQLite has write concurrency limits under high simultaneous transaction loads and is not suitable for distributed multi-instance horizontal scaling.
- **Production Path:** RazorMind's database layer is built entirely on SQLAlchemy with standard migration scripts. Switching to PostgreSQL or Supabase requires only setting `DATABASE_URL=postgresql+psycopg2://...` in `.env`.

---

## 6. Regulatory & Compliance Scope
- **Current State:** The Policy Engine enforces merchant-configured risk and amount ceilings, and the Flight Recorder maintains an immutable audit log.
- **Limitation:** While designed around RBI and NPCI payment guidelines (e-mandate rules, cooldown windows, attempt limits), the system has not undergone third-party PCI-DSS Level 1 certification or formal statutory financial auditing.
- **Production Path:** Ensure all card data handling relies exclusively on Razorpay tokenization rails (Card-on-File Tokenization compliance), ensuring zero plaintext PAN/CVV storage on RazorMind servers.
