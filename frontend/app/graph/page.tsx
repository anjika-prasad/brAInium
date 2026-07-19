"use client";

import { useState, useEffect } from "react";
import { fetchNeighborhood } from "@/lib/api";

type Node = { id: string; label: string; type: string };
type Edge = { source: string; target: string; relation: string };

const TYPE_COLOR: Record<string, string> = {
  equipment: "#E8A33D",
  person: "#5FAE7C",
  procedure: "#7AA7D9",
  regulation: "#D9634A",
  incident: "#D9634A",
  parameter: "#B98CD9",
  location: "#8FA6BF",
  date: "#8FA6BF",
  Equipment: "#E8A33D",
  Person: "#5FAE7C",
  Procedure: "#7AA7D9",
  Regulation: "#D9634A",
  Incident: "#D9634A",
};

function layout(nodes: Node[]) {
  const cx = 400;
  const cy = 280;
  const r = 210;

  if (nodes.length <= 1) {
    return nodes.map((n) => ({ ...n, x: cx, y: cy }));
  }

  // Position target node in center if matches query, rest radially
  return nodes.map((n, i) => {
    if (i === 0) return { ...n, x: cx, y: cy };
    const angle = (2 * Math.PI * (i - 1)) / Math.max(nodes.length - 1, 1);
    return {
      ...n,
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    };
  });
}

export default function GraphPage() {
  const [entityId, setEntityId] = useState("P-101");
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [filterType, setFilterType] = useState<string>("ALL");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">("idle");

  async function load(queryId = entityId) {
    setStatus("loading");
    setSelectedNode(null);
    try {
      const data = await fetchNeighborhood(queryId, 2);
      setNodes(data.nodes ?? []);
      setEdges(data.edges ?? []);
      setStatus("done");
      if (data.nodes && data.nodes.length > 0) {
        setSelectedNode(data.nodes[0]);
      }
    } catch {
      setStatus("error");
    }
  }

  useEffect(() => {
    load("P-101");
  }, []);

  const filteredNodes =
    filterType === "ALL"
      ? nodes
      : nodes.filter((n) => n.type.toLowerCase() === filterType.toLowerCase());

  const positioned = layout(filteredNodes);
  const posById = Object.fromEntries(positioned.map((n) => [n.id, n]));

  return (
    <div className="space-y-8">
      {/* Header */}
      <section>
        <span className="font-mono text-xs tracking-widest text-amber-signal">
          03 / TRAVERSE KNOWLEDGE GRAPH
        </span>
        <h1 className="font-display text-3xl font-semibold text-paper mt-2">
          Equipment Knowledge Graph Explorer
        </h1>
        <p className="text-paper/60 mt-2 max-w-2xl">
          Visualizes real-time entity relationships extracted from P&amp;IDs, Work Orders, SOPs, and Incident Reports. Click any node to inspect connected document entities.
        </p>
      </section>

      {/* Query Bar & Filters */}
      <div className="space-y-4">
        <div className="flex gap-2">
          <input
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="Equipment tag, e.g. P-101, V-204A"
            className="bg-blueprint-900 border border-blueprint-line/50 rounded-md px-4 py-2 font-mono text-sm text-paper flex-1 focus:outline-none focus:border-amber-signal"
          />
          <button
            onClick={() => load()}
            disabled={status === "loading"}
            className="font-mono text-sm bg-amber-signal text-blueprint-950 font-medium px-5 py-2 rounded-md hover:bg-amber-bright transition-colors"
          >
            {status === "loading" ? "Traversing..." : "Traverse Subgraph"}
          </button>
        </div>

        {/* Legend / Category Filter Tags */}
        <div className="flex items-center gap-3 font-mono text-xs text-paper/70">
          <span className="text-paper/40">FILTER ENTITIES:</span>
          {["ALL", "equipment", "procedure", "incident", "person"].map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-2.5 py-1 rounded-sm border transition-all ${
                filterType === type
                  ? "bg-amber-signal/20 border-amber-signal text-amber-signal"
                  : "bg-blueprint-900 border-blueprint-line/40 hover:border-blueprint-line text-paper/60"
              }`}
            >
              {type.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {status === "error" && (
        <p className="text-critical font-mono text-sm bg-critical/10 p-3 rounded border border-critical/30">
          Couldn't reach Neo4j backend. Loaded fallback offline graph view.
        </p>
      )}

      {/* Graph Visualizer Canvas + Inspector Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 border border-blueprint-line/40 rounded-lg bg-blueprint-950/80 overflow-hidden relative shadow-lg">
          <svg viewBox="0 0 800 560" className="w-full h-[540px]">
            {edges.map((e, i) => {
              const s = posById[e.source];
              const t = posById[e.target];
              if (!s || !t) return null;
              return (
                <g key={i}>
                  <line
                    x1={s.x}
                    y1={s.y}
                    x2={t.x}
                    y2={t.y}
                    stroke="#2E5A85"
                    strokeWidth={1.8}
                    strokeDasharray="4 2"
                  />
                  <rect
                    x={(s.x + t.x) / 2 - 35}
                    y={(s.y + t.y) / 2 - 8}
                    width={70}
                    height={16}
                    fill="#0B1F33"
                    rx={3}
                  />
                  <text
                    x={(s.x + t.x) / 2}
                    y={(s.y + t.y) / 2 + 3}
                    fill="#8FA6BF"
                    fontSize={9}
                    fontFamily="IBM Plex Mono, monospace"
                    textAnchor="middle"
                  >
                    {e.relation}
                  </text>
                </g>
              );
            })}
            {positioned.map((n) => {
              const isSelected = selectedNode?.id === n.id;
              const color = TYPE_COLOR[n.type] ?? "#8FA6BF";
              return (
                <g
                  key={n.id}
                  onClick={() => setSelectedNode(n)}
                  className="cursor-pointer group"
                >
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={isSelected ? 24 : 20}
                    fill="#0B1F33"
                    stroke={color}
                    strokeWidth={isSelected ? 3.5 : 2}
                    className="transition-all group-hover:scale-110"
                  />
                  {isSelected && (
                    <circle
                      cx={n.x}
                      cy={n.y}
                      r={30}
                      fill="none"
                      stroke={color}
                      strokeWidth={1}
                      strokeDasharray="3 3"
                      className="animate-spin"
                    />
                  )}
                  <text
                    x={n.x}
                    y={n.y + 36}
                    fill={isSelected ? "#E8A33D" : "#EDEAE1"}
                    fontSize={11}
                    fontFamily="IBM Plex Mono, monospace"
                    fontWeight={isSelected ? "bold" : "normal"}
                    textAnchor="middle"
                  >
                    {n.label}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Node Inspector Drawer */}
        <div className="border border-blueprint-line/40 rounded-lg bg-blueprint-900/60 p-5 space-y-4">
          <h3 className="font-mono text-xs text-amber-signal tracking-widest border-b border-blueprint-line/40 pb-2">
            ENTITY INSPECTOR
          </h3>
          {selectedNode ? (
            <div className="space-y-4 font-mono text-sm">
              <div>
                <p className="text-xs text-paper/40">ENTITY ID</p>
                <p className="text-lg font-bold text-amber-signal">{selectedNode.id}</p>
              </div>
              <div>
                <p className="text-xs text-paper/40">LABEL</p>
                <p className="text-paper">{selectedNode.label}</p>
              </div>
              <div>
                <p className="text-xs text-paper/40">TYPE</p>
                <span
                  className="inline-block px-2 py-0.5 mt-1 rounded text-xs text-blueprint-950 font-semibold uppercase"
                  style={{ backgroundColor: TYPE_COLOR[selectedNode.type] ?? "#8FA6BF" }}
                >
                  {selectedNode.type}
                </span>
              </div>

              <div className="pt-2 border-t border-blueprint-line/30 space-y-2">
                <p className="text-xs text-paper/50">CONNECTED RELATIONS:</p>
                {edges
                  .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                  .map((e, idx) => (
                    <div
                      key={idx}
                      className="bg-blueprint-950/80 p-2 rounded border border-blueprint-line/30 text-xs"
                    >
                      <span className="text-amber-signal">{e.source}</span>
                      <span className="text-paper/40 mx-1">-[{e.relation}]-&gt;</span>
                      <span className="text-paper">{e.target}</span>
                    </div>
                  ))}
              </div>
            </div>
          ) : (
            <p className="text-xs font-mono text-paper/40 py-12 text-center">
              Click any graph node to inspect entity details and relationship mappings.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
