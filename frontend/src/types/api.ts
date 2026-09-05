/**
 * RazorMind AI — Production Frontend Type Definitions
 * Strictly aligned with FastAPI backend Pydantic models.
 */

// ============================================================================
// HEALTH & DATABASE
// ============================================================================

export interface HealthStatus {
  status: string;
  message: string;
}

export interface DbHealthStatus {
  database: string;
  database_type?: string;
  table_count?: number;
}

// ============================================================================
// MERCHANTS
// ============================================================================

export interface MerchantCreate {
  name: string;
  email: string;
  business_type?: string;
  currency?: string;
}

export interface MerchantRead {
  id: string;
  name: string;
  email: string;
  business_type: string;
  currency: string;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// TRANSACTIONS
// ============================================================================

export interface TransactionCreate {
  merchant_id: string;
  customer_id?: string | null;
  razorpay_payment_id?: string | null;
  razorpay_order_id?: string | null;
  amount: number | string;
  currency?: string;
  status: string;
  payment_method: string;
  transaction_timestamp: string;
  metadata?: Record<string, any>;
}

export interface TransactionRead {
  id: string;
  merchant_id: string;
  customer_id: string | null;
  razorpay_payment_id: string | null;
  razorpay_order_id: string | null;
  amount: number | string;
  currency: string;
  status: "captured" | "failed" | "authorized" | "refunded" | string;
  payment_method: string;
  transaction_timestamp: string;
  metadata?: Record<string, any>;
  created_at: string;
}

// ============================================================================
// RISK & FRAUD ANALYSIS
// ============================================================================

export interface TransactionAnalysisInput {
  transaction_id?: string | null;
  merchant_id?: string | null;
  customer_id?: string | null;
  amount: number | string;
  currency?: string;
  payment_method: string;
  transaction_hour: number;
  day_of_week: number;
  customer_transaction_count?: number;
  customer_avg_amount?: number | string | null;
  merchant_avg_amount?: number | string | null;
  amount_deviation?: number;
  customer_age_days?: number;
  failed_attempts?: number;
  device_change?: number;
  ip_change?: number;
  country_change?: number;
  velocity_1h?: number;
  velocity_24h?: number;
  previous_chargebacks?: number;
  previous_fraud_events?: number;
  checkout_duration?: number;
  retry_count?: number;
  subscription?: number;
  transaction_status?: string;
  payment_failure?: number;
  failure_reason?: string;
  subscription_status?: string;
  customer_value?: number | string;
  previous_successful_payments?: number;
  recovery_attempts?: number;
}

export interface RiskAnalysisResponse {
  fraud_probability: number;
  anomaly_score: number;
  anomaly_flag: boolean;
  business_rule_score: number;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  model_version: string;
}

export interface RiskScoreRead {
  id: string;
  transaction_id: string;
  fraud_probability: number | string;
  anomaly_score: number | string;
  risk_score: number | string;
  risk_level: string;
  model_version: string;
  created_at: string;
}

export interface RiskSummary {
  total_risk_scores: number;
  average_risk_score: number;
  by_risk_level: {
    LOW?: number;
    MEDIUM?: number;
    HIGH?: number;
    CRITICAL?: number;
    [key: string]: number | undefined;
  };
}

// ============================================================================
// REVENUE RECOVERY & WORKFLOWS
// ============================================================================

export interface RecoveryAnalysisResponse {
  recovery_probability: number;
  expected_recovered_value: number | string;
  recommended_priority: string;
  model_version: string;
}

export interface RecoverySummary {
  total_opportunities: number;
  open_opportunities: number;
  average_recovery_probability: number;
  expected_recovered_value: number | string;
}

export interface RecoveryOpportunityRead {
  id: string;
  transaction_id: string | null;
  customer_id: string | null;
  opportunity_type: string;
  amount_at_risk: number | string;
  recovery_probability: number | string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  status: "open" | "in_progress" | "recovered" | "expired" | "failed" | string;
  recommended_action: string;
  expires_at: string | null;
  created_at: string;
}

export interface WorkflowExecuteRequest {
  merchant_id: string;
  transaction_id?: string | null;
  opportunity_id?: string | null;
  dry_run?: boolean;
}

export interface ProposedDecision {
  action: string;
  confidence: number;
  reason: string;
  expected_recovery: number;
}

export interface WorkflowPolicyResult {
  decision: "ALLOW" | "DENY" | "REQUIRE_REVIEW";
  reason: string;
  policy_id: string | null;
  checks: Record<string, boolean>;
}

export interface WorkflowExecutionResult {
  status: string;
  action_type: string;
  details: Record<string, any>;
}

export interface WorkflowVerificationResult {
  status: "recovered" | "stopped" | "queued_for_review" | "failed" | "pending" | string;
  details: Record<string, any>;
}

export interface WorkflowExecuteResponse {
  workflow_id: string;
  status: string;
  merchant_id: string;
  transaction_id: string | null;
  opportunity_id: string | null;
  decision: ProposedDecision;
  policy: WorkflowPolicyResult;
  execution: WorkflowExecutionResult;
  verification: WorkflowVerificationResult;
  amount_recovered: number;
  tools_used: string[];
  outcome_id: string | null;
  created_at: string;
}

export interface RecoveryOutcomeRead {
  id: string;
  opportunity_id: string;
  merchant_id: string;
  predicted_probability: number;
  chosen_action: string;
  policy_decision: string;
  actual_result: string;
  recovered_amount: number;
  attempt_number: number;
  prediction_correctness: boolean | null;
  created_at: string;
}

// ============================================================================
// DETERMINISTIC POLICY ENGINE
// ============================================================================

export type PolicyDecisionType = "ALLOW" | "DENY" | "REQUIRE_REVIEW";

export interface PolicyConfig {
  enabled?: boolean;
  min_recovery_probability?: number;
  max_recovery_amount?: number;
  max_attempts?: number;
  cooldown_minutes?: number;
  allowed_actions?: string[];
  risk_restrictions?: string[];
  min_confidence?: number;
  custom_rules?: Record<string, any>;
}

export interface PolicyCreate {
  merchant_id: string;
  policy_name: string;
  policy_type?: string;
  configuration?: Record<string, any> | PolicyConfig;
  enabled?: boolean;
}

export interface PolicyUpdate {
  policy_name?: string;
  configuration?: Record<string, any>;
  enabled?: boolean;
}

export interface PolicyRead {
  id: string;
  merchant_id: string;
  policy_name: string;
  policy_type: string;
  configuration: PolicyConfig;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyChecks {
  enabled?: boolean;
  amount_limit?: boolean;
  probability_threshold?: boolean;
  attempt_limit?: boolean;
  cooldown?: boolean;
  action_allowed?: boolean;
  risk_acceptable?: boolean;
  confidence_acceptable?: boolean;
  [key: string]: boolean | undefined;
}

export interface PolicyEvaluationRequest {
  merchant_id: string;
  action_type: string;
  amount: number;
  recovery_probability: number;
  attempt_number?: number;
  risk_level?: string | null;
  confidence?: number | null;
  last_attempt_at?: string | null;
}

export interface PolicyEvaluationResponse {
  decision: PolicyDecisionType;
  reason: string;
  policy_id: string | null;
  checks: PolicyChecks;
}

// ============================================================================
// AGENT / QWEN AI
// ============================================================================

export interface AgentChatRequest {
  message: string;
  merchant_id?: string | null;
  session_id?: string | null;
}

export interface AgentChatResponse {
  answer: string;
  tools_used: string[];
  model: string;
  agent_id: string;
  decision_id: string;
  session_id: string | null;
  metadata: Record<string, any>;
}

// ============================================================================
// AUDIT / FLIGHT RECORDER
// ============================================================================

export interface AuditLogRead {
  id: string;
  merchant_id: string | null;
  actor_type: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  decision: string;
  reason: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

// ============================================================================
// RAZORPAY INTEGRATION
// ============================================================================

export interface RazorpayStatusResponse {
  configured: boolean;
  mode: string;
}

export interface RazorpayOrderCreate {
  amount: number;
  currency?: string;
  receipt?: string | null;
  notes?: Record<string, any> | null;
}

export interface RazorpayOrderResponse {
  id: string;
  entity?: string | null;
  amount: number;
  amount_paid?: number | null;
  amount_due?: number | null;
  currency: string;
  receipt?: string | null;
  status?: string | null;
  attempts?: number | null;
  notes?: Record<string, any> | null;
  created_at?: number | null;
}

export interface RazorpayPaymentResponse {
  id: string;
  entity?: string | null;
  amount: number;
  currency: string;
  status?: string | null;
  order_id?: string | null;
  method?: string | null;
  captured?: boolean | null;
  description?: string | null;
  email?: string | null;
  contact?: string | null;
  error_code?: string | null;
  error_description?: string | null;
  created_at?: number | null;
  notes?: Record<string, any> | null;
}

export interface RazorpayPaymentsResponse {
  count: number;
  items: RazorpayPaymentResponse[];
}

export interface WebhookResponse {
  status: string;
  event_id?: string | null;
  event_type?: string | null;
  processed: boolean;
}

// ============================================================================
// RAG KNOWLEDGE BASE
// ============================================================================

export interface RAGDocumentIngestRequest {
  merchant_id?: string | null;
  title: string;
  content: string;
  document_type?: string;
}

export interface RAGQueryResult {
  chunk_id: string;
  document_id: string;
  title: string;
  content: string;
  score: number;
}

export interface RAGQueryRequest {
  query: string;
  merchant_id?: string | null;
  top_k?: number;
}

export interface RAGQueryResponse {
  query: string;
  results: RAGQueryResult[];
}
