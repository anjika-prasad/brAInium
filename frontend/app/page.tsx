"use client";

import { useState } from "react";
import { askCopilot, QueryResponse } from "@/lib/api";
import { UserBubble, AssistantBubble } from "@/components/ChatMessage";

type Message =
  | { sender: "user"; text: string }
  | { sender: "assistant"; response: QueryResponse };

const DEMO_PRESETS = [
  {
    label: "SOP Lockout Rules",
    text: "What does the SOP say about lockout-tagout for isolation valve V-204A?",
    type: "vector",
  },
  {
    label: "Equipment Failures & RCA",
    text: "Which pumps failed more than twice this year and what were the root causes?",
    type: "graph",
  },
  {
    label: "Full P-101 Synthesis",
    text: "Summarize maintenance history, vibration reports, and incident logs for Pump P-101.",
    type: "hybrid",
  },
  {
    label: "Work Order Details",
    text: "Who performed the last mechanical seal work order on P-101 and what actions were taken?",
    type: "hybrid",
  },
];

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "assistant",
      response: {
        answer:
          "Welcome to brAInium Industrial Knowledge Intelligence. Select a sample question below or ask any operational query regarding plant equipment (e.g. Pump P-101, Valve V-204A), SOPs, Work Orders, or Incident Reports.",
        confidence: 0.98,
        sources: [],
        retrieval_mode: "hybrid",
        graph_paths_used: [],
      },
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSend(queryText?: string) {
    const text = queryText || input;
    if (!text.trim() || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { sender: "user", text }]);
    setLoading(true);

    try {
      const res = await askCopilot(text);
      setMessages((prev) => [...prev, { sender: "assistant", response: res }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "assistant",
          response: {
            answer:
              "Could not complete retrieval query. Please ensure the backend server is running on http://localhost:8000.",
            confidence: 0.0,
            sources: [],
            retrieval_mode: "hybrid",
            graph_paths_used: [],
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <section className="border-b border-blueprint-line/40 pb-5">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs tracking-widest text-amber-signal">
            01 / QUERY COPILOT
          </span>
          <span className="text-[10px] font-mono bg-blueprint-800 text-paper/70 px-2 py-0.5 rounded">
            HYBRID GRAPH + VECTOR RAG
          </span>
        </div>
        <h1 className="font-display text-3xl font-semibold text-paper mt-2">
          Industrial Operational Copilot
        </h1>
        <p className="text-paper/60 mt-1 text-sm max-w-2xl">
          Queries P&amp;IDs, SOPs, Work Orders, and Incident Reports simultaneously using a dynamic query planner that fuses vector search with Neo4j Knowledge Graph traversal.
        </p>
      </section>

      {/* Quick Demo Preset Chips */}
      <div className="space-y-2">
        <p className="font-mono text-xs text-paper/50 tracking-wider">
          HACKATHON DEMO PRESETS:
        </p>
        <div className="flex flex-wrap gap-2">
          {DEMO_PRESETS.map((preset) => (
            <button
              key={preset.label}
              onClick={() => handleSend(preset.text)}
              disabled={loading}
              className="font-mono text-xs bg-blueprint-900/90 border border-blueprint-line/60 hover:border-amber-signal/70 text-paper/90 hover:text-amber-signal px-3 py-1.5 rounded-md transition-all text-left flex items-center gap-2"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-signal" />
              <span>{preset.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Conversation Container */}
      <div className="border border-blueprint-line/40 rounded-lg bg-blueprint-950/70 p-4 min-h-[420px] max-h-[560px] overflow-y-auto space-y-4 shadow-inner">
        {messages.map((msg, idx) => (
          <div key={idx}>
            {msg.sender === "user" ? (
              <UserBubble text={msg.text} />
            ) : (
              <AssistantBubble response={msg.response} />
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 p-4 bg-blueprint-900/40 rounded-lg border border-blueprint-line/30 text-amber-signal font-mono text-xs animate-pulse">
            <div className="w-3 h-3 rounded-full border-2 border-amber-signal border-t-transparent animate-spin" />
            <span>Query Planner analyzing question &amp; executing hybrid retrieval...</span>
          </div>
        )}
      </div>

      {/* Input controls */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask an operational question (e.g. Pump P-101 failure causes, Lockout procedure for V-204A)..."
          className="bg-blueprint-900 border border-blueprint-line/60 rounded-md px-4 py-3 font-mono text-sm text-paper flex-1 focus:outline-none focus:border-amber-signal/80 transition-colors"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="font-mono text-sm bg-amber-signal text-blueprint-950 font-semibold px-6 py-3 rounded-md hover:bg-amber-bright transition-all disabled:opacity-50"
        >
          Send Query
        </button>
      </div>
    </div>
  );
}
