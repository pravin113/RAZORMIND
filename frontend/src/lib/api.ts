import axios, { type AxiosRequestConfig } from "axios";
import type {
  AgentChatRequest,
  AgentChatResponse,
  AuditLogRead,
  DbHealthStatus,
  HealthStatus,
  MerchantCreate,
  MerchantRead,
  PolicyCreate,
  PolicyEvaluationRequest,
  PolicyEvaluationResponse,
  PolicyRead,
  PolicyUpdate,
  RAGDocumentIngestRequest,
  RAGQueryRequest,
  RAGQueryResponse,
  RazorpayOrderCreate,
  RazorpayOrderResponse,
  RazorpayPaymentResponse,
  RazorpayPaymentsResponse,
  RazorpayStatusResponse,
  RecoveryAnalysisResponse,
  RecoveryOpportunityRead,
  RecoveryOutcomeRead,
  RecoverySummary,
  RiskAnalysisResponse,
  RiskScoreRead,
  RiskSummary,
  TransactionAnalysisInput,
  TransactionCreate,
  TransactionRead,
  WorkflowExecuteRequest,
  WorkflowExecuteResponse,
} from "@/types/api";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000, // 60s default to support local LLM inferences
});

// Response interceptor with normalized error extraction
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = "Network error: Unable to connect to RazorMind backend.";
    if (error.response) {
      const data = error.response.data;
      message =
        (typeof data?.detail === "string" ? data.detail : null) ||
        data?.message ||
        `HTTP ${error.response.status}: ${error.response.statusText || "Request failed"}`;
    } else if (error.code === "ECONNABORTED") {
      message = "Request timed out while waiting for server response.";
    } else if (error.message) {
      message = error.message;
    }
    return Promise.reject(new Error(message));
  }
);

// Generic typed helpers with optional AbortSignal
async function requestGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.get<T>(url, config);
  return data;
}

async function requestPost<T, B = any>(url: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.post<T>(url, body, config);
  return data;
}

async function requestPut<T, B = any>(url: string, body?: B, config?: AxiosRequestConfig): Promise<T> {
  const { data } = await apiClient.put<T>(url, body, config);
  return data;
}

export const api = {
  // ==========================================================================
  // Health & Telemetry
  // ==========================================================================
  getHealth: async (signal?: AbortSignal): Promise<HealthStatus> => {
    return requestGet<HealthStatus>("/api/v1/health", { signal, timeout: 5000 });
  },

  getDbHealth: async (signal?: AbortSignal): Promise<DbHealthStatus> => {
    return requestGet<DbHealthStatus>("/api/v1/db/health", { signal, timeout: 5000 });
  },

  // ==========================================================================
  // Merchants
  // ==========================================================================
  getMerchants: async (offset = 0, limit = 100, signal?: AbortSignal): Promise<MerchantRead[]> => {
    return requestGet<MerchantRead[]>("/api/v1/merchants", {
      params: { offset, limit },
      signal,
    });
  },

  createMerchant: async (payload: MerchantCreate): Promise<MerchantRead> => {
    return requestPost<MerchantRead, MerchantCreate>("/api/v1/merchants", payload);
  },

  // ==========================================================================
  // Transactions
  // ==========================================================================
  getTransactions: async (offset = 0, limit = 100, signal?: AbortSignal): Promise<TransactionRead[]> => {
    return requestGet<TransactionRead[]>("/api/v1/transactions", {
      params: { offset, limit },
      signal,
    });
  },

  getTransaction: async (id: string, signal?: AbortSignal): Promise<TransactionRead> => {
    return requestGet<TransactionRead>(`/api/v1/transactions/${id}`, { signal });
  },

  createTransaction: async (payload: TransactionCreate): Promise<TransactionRead> => {
    return requestPost<TransactionRead, TransactionCreate>("/api/v1/transactions", payload);
  },

  // ==========================================================================
  // ML Risk Analysis
  // ==========================================================================
  getRiskSummary: async (signal?: AbortSignal): Promise<RiskSummary> => {
    return requestGet<RiskSummary>("/api/v1/risk/summary", { signal });
  },

  getRiskScores: async (transactionId: string, signal?: AbortSignal): Promise<RiskScoreRead[]> => {
    return requestGet<RiskScoreRead[]>(`/api/v1/risk/scores/${transactionId}`, { signal });
  },

  postRiskAnalysis: async (payload: TransactionAnalysisInput): Promise<RiskAnalysisResponse> => {
    return requestPost<RiskAnalysisResponse, TransactionAnalysisInput>("/api/v1/risk/analyze", payload);
  },

  // ==========================================================================
  // Autonomous Revenue Recovery
  // ==========================================================================
  getRecoverySummary: async (signal?: AbortSignal): Promise<RecoverySummary> => {
    return requestGet<RecoverySummary>("/api/v1/recovery/summary", { signal });
  },

  getRecoveryOpportunities: async (
    offset = 0,
    limit = 100,
    signal?: AbortSignal
  ): Promise<RecoveryOpportunityRead[]> => {
    return requestGet<RecoveryOpportunityRead[]>("/api/v1/recovery/opportunities", {
      params: { offset, limit },
      signal,
    });
  },

  postRecoveryAnalysis: async (payload: TransactionAnalysisInput): Promise<RecoveryAnalysisResponse> => {
    return requestPost<RecoveryAnalysisResponse, TransactionAnalysisInput>("/api/v1/recovery/analyze", payload);
  },

  executeRecoveryWorkflow: async (payload: WorkflowExecuteRequest): Promise<WorkflowExecuteResponse> => {
    return requestPost<WorkflowExecuteResponse, WorkflowExecuteRequest>("/api/v1/recovery/execute", payload);
  },

  getRecoveryOutcomes: async (
    merchantId?: string,
    offset = 0,
    limit = 100,
    signal?: AbortSignal
  ): Promise<RecoveryOutcomeRead[]> => {
    return requestGet<RecoveryOutcomeRead[]>("/api/v1/recovery/outcomes", {
      params: { merchant_id: merchantId || undefined, offset, limit },
      signal,
    });
  },

  getWorkflowOutcome: async (outcomeId: string, signal?: AbortSignal): Promise<RecoveryOutcomeRead> => {
    return requestGet<RecoveryOutcomeRead>(`/api/v1/recovery/workflows/${outcomeId}`, { signal });
  },

  // ==========================================================================
  // Deterministic Policy Engine
  // ==========================================================================
  getPolicies: async (merchantId?: string, offset = 0, limit = 100, signal?: AbortSignal): Promise<PolicyRead[]> => {
    return requestGet<PolicyRead[]>("/api/v1/policies", {
      params: { merchant_id: merchantId || undefined, offset, limit },
      signal,
    });
  },

  getPolicy: async (policyId: string, signal?: AbortSignal): Promise<PolicyRead> => {
    return requestGet<PolicyRead>(`/api/v1/policies/${policyId}`, { signal });
  },

  createPolicy: async (payload: PolicyCreate): Promise<PolicyRead> => {
    return requestPost<PolicyRead, PolicyCreate>("/api/v1/policies", payload);
  },

  updatePolicy: async (policyId: string, payload: PolicyUpdate): Promise<PolicyRead> => {
    return requestPut<PolicyRead, PolicyUpdate>(`/api/v1/policies/${policyId}`, payload);
  },

  evaluatePolicy: async (payload: PolicyEvaluationRequest): Promise<PolicyEvaluationResponse> => {
    return requestPost<PolicyEvaluationResponse, PolicyEvaluationRequest>("/api/v1/policies/evaluate", payload);
  },

  // ==========================================================================
  // Agent / Qwen AI Console
  // ==========================================================================
  sendAgentChat: async (
    message: string,
    merchantId?: string | null,
    sessionId?: string | null,
    signal?: AbortSignal
  ): Promise<AgentChatResponse> => {
    const payload: AgentChatRequest = {
      message,
      merchant_id: merchantId || null,
      session_id: sessionId || null,
    };
    return requestPost<AgentChatResponse, AgentChatRequest>("/api/v1/agent/chat", payload, {
      signal,
      timeout: 120000, // Up to 120s for multi-turn local GGUF reasoning
    });
  },

  // ==========================================================================
  // Audit / Flight Recorder
  // ==========================================================================
  getAuditLogs: async (offset = 0, limit = 100, signal?: AbortSignal): Promise<AuditLogRead[]> => {
    return requestGet<AuditLogRead[]>("/api/v1/audit/logs", {
      params: { offset, limit },
      signal,
    });
  },

  // ==========================================================================
  // Razorpay Gateway
  // ==========================================================================
  getRazorpayStatus: async (signal?: AbortSignal): Promise<RazorpayStatusResponse> => {
    return requestGet<RazorpayStatusResponse>("/api/v1/razorpay/status", { signal });
  },

  createRazorpayOrder: async (payload: RazorpayOrderCreate): Promise<RazorpayOrderResponse> => {
    return requestPost<RazorpayOrderResponse, RazorpayOrderCreate>("/api/v1/razorpay/orders", payload);
  },

  getRazorpayOrder: async (orderId: string, signal?: AbortSignal): Promise<RazorpayOrderResponse> => {
    return requestGet<RazorpayOrderResponse>(`/api/v1/razorpay/orders/${orderId}`, { signal });
  },

  getRazorpayPayment: async (paymentId: string, signal?: AbortSignal): Promise<RazorpayPaymentResponse> => {
    return requestGet<RazorpayPaymentResponse>(`/api/v1/razorpay/payments/${paymentId}`, { signal });
  },

  getRazorpayOrderPayments: async (orderId: string, signal?: AbortSignal): Promise<RazorpayPaymentsResponse> => {
    return requestGet<RazorpayPaymentsResponse>(`/api/v1/razorpay/orders/${orderId}/payments`, { signal });
  },

  // ==========================================================================
  // RAG Knowledge Base
  // ==========================================================================
  ingestRAGDocument: async (payload: RAGDocumentIngestRequest): Promise<{ id: string; chunk_count: number }> => {
    return requestPost<{ id: string; chunk_count: number }, RAGDocumentIngestRequest>(
      "/api/v1/rag/documents",
      payload
    );
  },

  queryRAG: async (payload: RAGQueryRequest, signal?: AbortSignal): Promise<RAGQueryResponse> => {
    return requestPost<RAGQueryResponse, RAGQueryRequest>("/api/v1/rag/query", payload, { signal });
  },
};
