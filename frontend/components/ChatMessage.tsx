import { QueryResponse } from "@/lib/api";
import SourcePanel from "./SourcePanel";

export function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-xl rounded-lg rounded-tr-sm bg-blueprint-700 border border-blueprint-line/50 px-4 py-3 text-paper">
        {text}
      </div>
    </div>
  );
}

function ModeTag({ mode }: { mode: QueryResponse["retrieval_mode"] }) {
  const labels: Record<string, string> = {
    vector: "SEMANTIC SEARCH",
    graph: "GRAPH TRAVERSAL",
    hybrid: "HYBRID: SEMANTIC + GRAPH",
  };
  return (
    <span className="font-mono text-[10px] tracking-widest text-amber-signal border border-amber-signal/50 rounded-sm px-1.5 py-0.5">
      {labels[mode] ?? mode.toUpperCase()}
    </span>
  );
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.75 ? "bg-ok" : value >= 0.45 ? "bg-warn" : "bg-critical";
  return (
    <div className="flex items-center gap-2 font-mono text-[10px] text-paper/60">
      <span>CONFIDENCE</span>
      <div className="w-16 h-1.5 bg-blueprint-800 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span>{pct}%</span>
    </div>
  );
}

export function AssistantBubble({ response }: { response: QueryResponse }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-2xl w-full rounded-lg rounded-tl-sm bg-blueprint-900/80 border border-blueprint-line/50 px-4 py-4 space-y-3">
        <div className="flex items-center justify-between">
          <ModeTag mode={response.retrieval_mode} />
          <ConfidenceMeter value={response.confidence} />
        </div>
        <p className="text-paper leading-relaxed whitespace-pre-wrap">{response.answer}</p>
        {response.graph_paths_used.length > 0 && (
          <p className="font-mono text-[11px] text-paper/50">
            graph paths: {response.graph_paths_used.join(", ")}
          </p>
        )}
        {response.sources.length > 0 && <SourcePanel sources={response.sources} />}
      </div>
    </div>
  );
}
