# RazorMind AI Backend

Production-quality backend foundation for RazorMind AI, an AI-powered merchant finance, fraud/risk, and revenue recovery platform for the Razorpay Buildathon.

This phase includes FastAPI routing, configuration, logging/error foundations, SQLAlchemy models, Supabase PostgreSQL wiring, Alembic migrations, service functions, and endpoint tests. It intentionally does not implement Razorpay execution, ML models, Qwen, an AI agent, RAG, frontend code, or payment execution.

## Setup

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment

Create `.env` from the example:

```bash
cp .env.example .env
```

Windows Command Prompt:

```cmd
copy .env.example .env
```

Fill in the placeholders:

```text
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DATABASE_URL=postgresql+psycopg://postgres:password@db.your-project.supabase.co:5432/postgres
JWT_SECRET=replace_with_a_long_random_secret
```

Never commit `.env` or real secrets. `SUPABASE_SERVICE_ROLE_KEY` must stay server-side only and must never be returned by an API response.

## Supabase Setup

1. Create a Supabase project.
2. Open Project Settings > Database.
3. Copy the PostgreSQL connection string.
4. Use the SQLAlchemy/psycopg format in `.env`:

```text
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

For Supabase pooler URLs, keep the same `postgresql+psycopg://` prefix and use the host, port, database, user, and password shown by Supabase.

## Migrations

Run migrations from `backend/` after `DATABASE_URL` is configured:

```bash
alembic upgrade head
```

Create future migrations after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The app does not auto-create tables at startup. Use Alembic for local development and production schema changes.

## Run FastAPI

Start the API from `backend/`:

```bash
uvicorn app.main:app --reload
```

Health endpoints:

```text
http://127.0.0.1:8000/api/v1/health
http://127.0.0.1:8000/api/v1/db/health
```

`/api/v1/db/health` returns `not_configured` when `DATABASE_URL` is missing, and `ok` only when it can connect and execute `SELECT 1`.

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

Implemented in Phases 2, 3, 4, and 5:

```text
GET  /api/v1/health
GET  /api/v1/db/health
GET  /api/v1/merchants
POST /api/v1/merchants
GET  /api/v1/transactions
GET  /api/v1/transactions/{transaction_id}
POST /api/v1/transactions
GET  /api/v1/razorpay/status
POST /api/v1/razorpay/orders
GET  /api/v1/razorpay/orders/{order_id}
GET  /api/v1/razorpay/payments/{payment_id}
GET  /api/v1/razorpay/orders/{order_id}/payments
POST /api/v1/webhooks/razorpay
GET  /api/v1/risk/scores/{transaction_id}
POST /api/v1/risk/analyze
GET  /api/v1/risk/summary
GET  /api/v1/recovery/opportunities
POST /api/v1/recovery/analyze
GET  /api/v1/recovery/summary
GET  /api/v1/audit/logs
POST /api/v1/agent/chat
```

## Phase 5 — Qwen3-8B AI Agent

RazorMind AI integrates local Qwen3-8B LLM reasoning with a controlled, read-only tool-calling agent framework. The agent answers natural language merchant queries by retrieving ground-truth metrics from the database, executing ML prediction pipelines, and synthesizing actionable explanations without ever fabricating financial figures.

### Qwen Model & Inference Setup
- **Model File**: `D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf`
- **Format**: GGUF (4-bit quantized, medium) optimized for local inference within 8GB VRAM budgets.
- **Inference Server**: Any OpenAI-compatible inference server (such as `llama-server` from `llama.cpp` or Ollama).
- **Example Start Command**:
  ```bash
  llama-server -m D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf --port 8080 -c 4096 --n-gpu-layers 33
  ```

### Environment Variables
```text
QWEN_ENABLED=true
QWEN_MODEL_PATH=D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf
QWEN_BASE_URL=http://127.0.0.1:8080/v1
QWEN_MODEL_NAME=Qwen3-8B
QWEN_TEMPERATURE=0.2
QWEN_MAX_TOKENS=1024
```

### Controlled Tool Registry (10 Read-Only Tools)
1. `get_transaction(transaction_id)`: Fetches non-sensitive transaction details and failure reasons.
2. `get_customer_history(customer_id)`: Aggregates customer payment volume, success/failure counts, and recovery history.
3. `get_risk_score(transaction_id)`: Queries Phase 3 ML fraud and anomaly risk assessment.
4. `get_recovery_probability(transaction_id)`: Retrieves ML recovery probability and actionable yield recommendations.
5. `get_revenue_metrics(start_date, end_date, merchant_id)`: Computes volume, revenue, success rates, and failure amounts over date ranges.
6. `get_failed_payments(start_date, end_date, failure_reason, limit)`: Lists recent failed payments with error codes.
7. `get_risk_summary()`: Summarizes evaluated transactions, high/critical risk counts, and risk distribution.
8. `get_recovery_summary()`: Summarizes recovery opportunities, recoverable revenue, and yield rates.
9. `get_payment_details(razorpay_payment_id)`: Queries sanitized payment details via Razorpay service or DB fallback.
10. `get_policy(merchant_id)`: Returns merchant guardrails (strictly enforcing read-only mode in Phase 5).

### Security & Operational Guardrails
- **Read-Only**: Phase 5 tools cannot issue refunds, retry payments, block customers, or alter database balances.
- **Zero Hallucination of Numbers**: The agent prompt mandates that all financial amounts and rates originate from tool execution.
- **No Secret Leakage**: API secrets, webhook keys, authorization headers, and raw credentials are never included in prompts or returned in output.
- **No Hidden Chain-of-Thought**: Internal `<think>` tags are stripped; only the final explanation and `tools_used` list are returned.
- **Graceful Degradation**: If the local LLM is offline or disabled, `POST /api/v1/agent/chat` returns an HTTP 503 error detail without crashing the API or fabricating responses.

### Example Queries
- *"Why did my revenue drop this week?"* -> Calls `get_revenue_metrics`, `get_failed_payments`, `get_recovery_summary`.
- *"Which failed payments should I prioritize for recovery?"* -> Calls `get_failed_payments`, `get_recovery_probability`.
- *"Are there any suspicious high-risk transactions recently?"* -> Calls `get_risk_summary`, `get_risk_score`.

## ML Pipeline

Generate the synthetic dataset, train/evaluate fraud, anomaly, and recovery models, save artifacts, and write the report:

```bash
python -m app.ai.train_all
```

Outputs:

```text
../data/raw/synthetic_transactions.csv
../data/processed/transactions.csv
../data/processed/dataset_metadata.json
../models/fraud_model.joblib
../models/anomaly_model.joblib
../models/recovery_model.joblib
../models/fraud_metadata.json
../models/anomaly_metadata.json
../models/recovery_metadata.json
../docs/ml_evaluation.md
```

Fraud classification compares XGBoost, LightGBM, CatBoost, and a simple averaged ensemble on held-out test data. Anomaly detection uses Isolation Forest and is intentionally separate from fraud classification. Recovery prediction compares LightGBM and CatBoost. The ML layer only predicts; it does not execute financial actions.

## Phase 6 — Autonomous Revenue Recovery, Policy Engine & RAG

Phase 6 implements bounded, deterministic autonomous revenue recovery:
```text
OBSERVE -> DETECT -> INVESTIGATE -> DECIDE -> POLICY CHECK -> ACT -> VERIFY -> AUDIT -> LEARN
```

### Key Modules:
- **Policy Engine (`app/ai/policy/`)**: Deterministic rules engine enforcing maximum attempts (stopping rule), recovery probability floors, maximum amount ceilings, cooldown intervals, allowed action whitelists, and risk tier restrictions. The LLM has zero authority to bypass policies.
- **RAG Knowledge Layer (`app/ai/rag/`)**: Zero-cloud, instant local vector search across merchant documents (refund policies, retry rules, communication guides) with strict merchant isolation.
- **Autonomous Workflow Orchestrator (`app/ai/workflows/`)**: Runs the 9-step closed-loop recovery workflow, executes safe actions in Razorpay TEST MODE, verifies financial outcomes, and persists audit logs and prediction learning records.
- **Outcome Tracking (`recovery_outcomes`)**: Database table added via Alembic migration `003_recovery_outcomes.py` storing predicted vs actual recovery performance.

### Endpoints:
- `POST /api/v1/policies/evaluate`: Evaluate proposed recovery actions.
- `GET /api/v1/policies`: List merchant policies.
- `POST /api/v1/rag/documents`: Ingest knowledge documents.
- `POST /api/v1/rag/query`: Semantic knowledge retrieval.
- `POST /api/v1/recovery/execute`: Run autonomous recovery loop.
- `GET /api/v1/recovery/outcomes`: Inspect recovery outcomes.

## Tests

Run tests from `backend/`:

```bash
pytest -v
```

88 tests passing across Phases 1 through 6. Tests use an isolated SQLite database and do not require Supabase or external production credentials.


## Architecture Notes

- `app/db/models.py` contains SQLAlchemy 2.x models for merchants, customers, transactions, payment attempts, risk scores, fraud events, recovery opportunities/actions, revenue events, policies, agent decisions, audit logs, and documents.
- `app/db/session.py` owns engine/session creation from `DATABASE_URL`.
- `app/services/` contains small CRUD/service helpers for merchants, transactions, risk scores, recovery opportunities, audit logs, and database health.
- `app/schemas/` contains Pydantic request/response contracts.
- `alembic/` owns migration strategy for Supabase PostgreSQL.
- `app/ai/` contains feature engineering, model training, prediction, anomaly detection, recovery prediction, risk scoring, and the Qwen agent tool registry.

