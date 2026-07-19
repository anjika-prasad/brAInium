import { SourceCitation } from "@/lib/api";

export default function SourcePanel({ sources }: { sources: SourceCitation[] }) {
  return (
    <div className="border-t border-blueprint-line/40 pt-3 mt-1">
      <p className="font-mono text-[10px] tracking-widest text-paper/50 mb-2">SOURCE DOCUMENTS</p>
      <div className="space-y-2">
        {sources.map((s, i) => (
          <div
            key={`${s.document_id}-${i}`}
            className="flex items-start gap-3 bg-blueprint-950/60 border border-blueprint-line/30 rounded-sm px-3 py-2"
          >
            <span className="font-mono text-[10px] text-amber-signal shrink-0 mt-0.5">
              [{String(i + 1).padStart(2, "0")}]
            </span>
            <div className="min-w-0">
              <div className="flex items-center gap-2 font-mono text-[11px] text-paper/70">
                <span className="truncate">{s.filename}</span>
                {s.page !== null && <span className="text-paper/40">p.{s.page}</span>}
                <span className="text-paper/40">match {Math.round(s.score * 100)}%</span>
              </div>
              <p className="text-[13px] text-paper/60 mt-1 line-clamp-2">{s.snippet}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
