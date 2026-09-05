import { describe, it, expect, vi, beforeEach } from "vitest";
import { api, API_BASE_URL, apiClient } from "@/lib/api";
import { formatINR, formatPercentage, formatDateTime } from "@/lib/utils";

describe("API Client & Utilities", () => {
  it("uses the correct default or configured base URL", () => {
    expect(API_BASE_URL).toBeDefined();
    expect(apiClient.defaults.baseURL).toBe(API_BASE_URL);
  });

  it("formats INR currency correctly for various input types", () => {
    expect(formatINR(0)).toContain("0");
    expect(formatINR(2500)).toContain("2,500");
    expect(formatINR("14999.50")).toContain("14,999.50");
    expect(formatINR(null)).toBe("₹0.00");
    expect(formatINR(undefined)).toBe("₹0.00");
  });

  it("formats percentage correctly for numbers and string inputs", () => {
    expect(formatPercentage(0.75)).toBe("75.0%");
    expect(formatPercentage(0.654)).toBe("65.4%");
    expect(formatPercentage("0.85")).toBe("85.0%");
    expect(formatPercentage(null)).toBe("0.0%");
  });

  it("formats date-times gracefully without throwing", () => {
    const formatted = formatDateTime("2026-09-04T12:00:00Z");
    expect(formatted).not.toBe("--");
    expect(formatDateTime(null)).toBe("--");
  });
});

describe("API Endpoint Handlers", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls getHealth using apiClient.get", async () => {
    const mockData = { status: "ok", message: "RazorMind AI API is running" };
    vi.spyOn(apiClient, "get").mockResolvedValueOnce({ data: mockData });

    const res = await api.getHealth();
    expect(res).toEqual(mockData);
    expect(apiClient.get).toHaveBeenCalledWith("/api/v1/health", expect.anything());
  });

  it("calls executeRecoveryWorkflow with typed payload", async () => {
    const mockResponse = {
      workflow_id: "wf-123",
      status: "completed",
      merchant_id: "m-1",
      transaction_id: "tx-1",
      opportunity_id: "opp-1",
      decision: {
        action: "retry_payment",
        confidence: 0.95,
        reason: "Valid card details",
        expected_recovery: 2500,
      },
      policy: {
        decision: "ALLOW",
        reason: "Within risk and amount limits",
        policy_id: null,
        checks: { amount_limit: true },
      },
      execution: {
        status: "success",
        action_type: "retry_payment",
        details: {},
      },
      verification: {
        status: "recovered",
        details: {},
      },
      amount_recovered: 2500,
      tools_used: ["tool_evaluate_recovery_policy"],
      outcome_id: "out-1",
      created_at: new Date().toISOString(),
    };

    vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockResponse });

    const payload = {
      merchant_id: "m-1",
      opportunity_id: "opp-1",
      transaction_id: "tx-1",
      dry_run: false,
    };

    const res = await api.executeRecoveryWorkflow(payload);
    expect(res.workflow_id).toBe("wf-123");
    expect(res.policy.decision).toBe("ALLOW");
    expect(res.amount_recovered).toBe(2500);
    expect(apiClient.post).toHaveBeenCalledWith("/api/v1/recovery/execute", payload, undefined);
  });

  it("calls evaluatePolicy with merchant and action parameters", async () => {
    const mockEval = {
      decision: "ALLOW",
      reason: "All 7 safety checks passed",
      policy_id: null,
      checks: {
        enabled: true,
        amount_limit: true,
        probability_threshold: true,
        attempt_limit: true,
      },
    };

    vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockEval });

    const evalPayload = {
      merchant_id: "m-1",
      action_type: "retry_payment",
      amount: 1500,
      recovery_probability: 0.8,
      attempt_number: 1,
      risk_level: "LOW",
    };

    const res = await api.evaluatePolicy(evalPayload);
    expect(res.decision).toBe("ALLOW");
    expect(apiClient.post).toHaveBeenCalledWith("/api/v1/policies/evaluate", evalPayload, undefined);
  });

  it("calls sendAgentChat with query string and optional session ID", async () => {
    const mockChat = {
      answer: "Platform recovery yield is currently 72.4%.",
      tools_used: ["get_revenue_metrics", "get_recovery_summary"],
      model: "Qwen3-8B",
      agent_id: "razormind-agent-v1",
      decision_id: "dec-999",
      session_id: "sess-abc",
      metadata: {},
    };

    vi.spyOn(apiClient, "post").mockResolvedValueOnce({ data: mockChat });

    const res = await api.sendAgentChat("What is our recovery yield?", "m-1", "sess-abc");
    expect(res.answer).toContain("72.4%");
    expect(res.tools_used).toHaveLength(2);
    expect(apiClient.post).toHaveBeenCalledWith(
      "/api/v1/agent/chat",
      {
        message: "What is our recovery yield?",
        merchant_id: "m-1",
        session_id: "sess-abc",
      },
      expect.objectContaining({ timeout: 120000 })
    );
  });
});
