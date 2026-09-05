# RazorMind AI — Institutional Financial Frontend

Production React 18 + Vite + TypeScript web interface and autonomous command center for RazorMind AI.

## Quick Start

### 1. Start Backend & AI Engine
```powershell
# In terminal 1: Start Qwen3-8B local inference
llama-server -m "D:\RazorMind\models\Qwen3-8B-Q4_K_M.gguf" --host 127.0.0.1 --port 8080 -c 4096

# In terminal 2: Start FastAPI backend
cd D:\RazorMind\backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend
```powershell
cd D:\RazorMind\frontend
npm install
npm run dev
```

The application will be accessible at: `http://localhost:5173`

---

## Environment Variables

Configured in `frontend/.env` (defaults to local FastAPI):

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Testing & Validation

### Build Verification
```powershell
npm run build
```
Runs `tsc -b && vite build` ensuring 0 TypeScript errors and bundling into `frontend/dist/`.

### Run Frontend Unit Tests
```powershell
npm test
```
Runs Vitest suite verifying API client configuration, telemetry formatting, and endpoint handlers.

### Run Backend Tests
```powershell
cd D:\RazorMind\backend
.venv\Scripts\pytest -q
```
Maintains 88/88 passed tests covering Phase 1–6 functionality.

---

## Application Navigation Routes

| Route | Page | Purpose | Real Backend APIs Used |
| :--- | :--- | :--- | :--- |
| `/` | `LandingPage` | 3D Cinematic Storytelling Universe | Three.js / React Three Fiber / GSAP |
| `/dashboard` | `DashboardPage` | Executive Command Center | `/api/v1/transactions`, `/api/v1/recovery/summary`, `/api/v1/risk/summary`, `/api/v1/recovery/opportunities` |
| `/recovery` | `RevenueRecoveryPage`| 9-Step Autonomous Orchestrator | `/api/v1/recovery/summary`, `/api/v1/recovery/opportunities`, `POST /api/v1/recovery/execute`, `/api/v1/recovery/outcomes` |
| `/risk` | `RiskCenterPage` | ML Fraud & Anomaly Center | `/api/v1/risk/summary`, `/api/v1/transactions`, `POST /api/v1/risk/analyze` |
| `/ai` | `AIDecisionPage` | Qwen3-8B Decision Console | `POST /api/v1/agent/chat` |
| `/policies` | `PoliciesPage` | Deterministic Policy Gate & Simulator | `GET /api/v1/policies`, `POST /api/v1/policies/evaluate` |
| `/audit` | `AuditPage` | Flight Recorder Telemetry | `GET /api/v1/audit/logs` |
| `/razorpay` | `RazorpayPage` | Gateway & Test Mode Orders | `GET /api/v1/razorpay/status`, `POST /api/v1/razorpay/orders` |
| `/settings` | `SettingsPage` | System Health & Parameters | `GET /api/v1/health`, `GET /api/v1/db/health`, `GET /api/v1/razorpay/status` |
