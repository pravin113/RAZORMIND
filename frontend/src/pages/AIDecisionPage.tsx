import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  Send,
  Sparkles,
  Cpu,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolsUsed?: string[];
  decisionId?: string;
  model?: string;
  timestamp: string;
}

const SUGGESTED_QUERIES = [
  "What is our gross revenue and recovery rate?",
  "Which failed payments are eligible for recovery?",
  "Are there any high-risk fraud anomalies detected?",
  "Evaluate our policy stopping rules for payment retries",
];

export const AIDecisionPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init-0",
      role: "assistant",
      content:
        "RazorMind Autonomous Intelligence Engine initialized. Powered by local Qwen3-8B inference with 13 ground-truth financial, risk, policy, and recovery tools. Ask any questions regarding merchant financials, failed payments, risk scores, or policy verdicts.",
      toolsUsed: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || loading) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.sendAgentChat(query, null, sessionId);
      if (res.session_id) {
        setSessionId(res.session_id);
      }

      const botMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: res.answer,
        toolsUsed: res.tools_used,
        decisionId: res.decision_id,
        model: res.model,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `AI Reasoning Interrupted: ${err.message}. Please verify that llama-server is running on port 8080 and backend is reachable on port 8000.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([
      {
        id: `init-${Date.now()}`,
        role: "assistant",
        content: "Session cleared. Ready for your financial intelligence queries.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
    setSessionId(null);
  };

  return (
    <div className="space-y-4 max-w-5xl mx-auto h-[calc(100vh-8.5rem)] flex flex-col animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Bot className="w-6 h-6 text-fintech-cyan" />
            AI Decision Console
          </h1>
          <p className="text-xs font-mono text-fintech-subtle uppercase tracking-wider">
            Deterministic tool calling over live PostgreSQL, Policy Engine, and ML inference
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-fintech-cyan/10 border border-fintech-cyan/30 text-fintech-cyan text-[10px] font-mono uppercase">
            <Cpu className="w-3 h-3" /> Qwen3-8B GGUF
          </span>
          <button
            onClick={handleClear}
            className="px-2.5 py-1 rounded border border-fintech-border bg-fintech-elevated hover:bg-fintech-border text-fintech-muted hover:text-white text-xs font-mono"
            title="Reset conversation"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Suggested Query Chips */}
      <div className="flex flex-wrap gap-2 shrink-0">
        {SUGGESTED_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => handleSend(q)}
            disabled={loading}
            className="px-3 py-1.5 rounded-full bg-fintech-surface hover:bg-fintech-elevated border border-fintech-border hover:border-fintech-cyan/40 text-[11px] font-mono text-fintech-subtle hover:text-white transition-all text-left flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className="w-3 h-3 text-fintech-cyan shrink-0" />
            <span>{q}</span>
          </button>
        ))}
      </div>

      {/* Messages Container */}
      <div className="flex-1 bg-fintech-surface border border-fintech-border rounded-lg p-5 overflow-y-auto space-y-4 glass-card">
        {messages.map((m) => (
          <div
            key={m.id}
            className={cn("flex flex-col", m.role === "user" ? "items-end" : "items-start")}
          >
            <div
              className={cn(
                "max-w-2xl p-4 rounded-lg text-xs leading-relaxed font-sans space-y-2.5",
                m.role === "user"
                  ? "bg-fintech-cyan/15 border border-fintech-cyan/40 text-white rounded-br-none"
                  : "bg-fintech-elevated border border-fintech-border text-fintech-text rounded-bl-none"
              )}
            >
              <div className="flex items-center justify-between text-[10px] font-mono text-fintech-muted border-b border-fintech-border/30 pb-1.5">
                <span className="font-semibold uppercase text-fintech-cyan">
                  {m.role === "user" ? "Merchant Operator" : "RazorMind AI"}
                </span>
                <span>{m.timestamp}</span>
              </div>

              <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</div>

              {/* Tools invoked breakdown */}
              {m.toolsUsed && m.toolsUsed.length > 0 && (
                <div className="pt-2 border-t border-fintech-border/50 flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] font-mono text-fintech-muted uppercase">
                    Tools Executed:
                  </span>
                  {m.toolsUsed.map((t) => (
                    <span
                      key={t}
                      className="px-2 py-0.5 rounded text-[10px] font-mono bg-fintech-cyan/10 border border-fintech-cyan/30 text-fintech-cyan font-bold"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}

              {m.decisionId && (
                <div className="text-[10px] font-mono text-fintech-muted/70 flex items-center justify-between pt-1">
                  <span>Decision Audit: {m.decisionId.slice(0, 8)}</span>
                  <span>Model: {m.model || "Qwen3-8B"}</span>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="p-3 rounded bg-fintech-elevated/60 border border-fintech-cyan/30 flex items-center gap-2.5 text-xs font-mono text-fintech-cyan animate-pulse max-w-md">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Qwen3-8B is reasoning and invoking financial tools...</span>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      {/* Input Bar */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex gap-2 shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask RazorMind AI about revenues, failed payments, risk scores, or policy verdicts..."
          disabled={loading}
          className="flex-1 bg-fintech-surface border border-fintech-border focus:border-fintech-cyan rounded-lg px-4 py-3 text-xs text-white placeholder-fintech-muted outline-none font-mono transition-colors disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-5 py-3 bg-fintech-cyan hover:bg-fintech-cyan/90 text-fintech-dark font-bold text-xs uppercase tracking-wider rounded-lg flex items-center gap-2 transition-colors disabled:opacity-40 shrink-0"
        >
          <Send className="w-3.5 h-3.5" />
          Send
        </button>
      </form>
    </div>
  );
};
