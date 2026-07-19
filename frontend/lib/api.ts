export type SourceCitation = {
  document_id: string;
  filename: string;
  page: number | null;
  snippet: string;
  score: number;
};

export type QueryResponse = {
  answer: string;
  confidence: number;
  sources: SourceCitation[];
  retrieval_mode: "vector" | "graph" | "hybrid";
  graph_paths_used: string[];
};

export type IngestResult = {
  document_id: string;
  filename: string;
  doc_type: string;
  num_chunks: number;
  num_entities: number;
  num_relationships: number;
  ingested_at: string;
};

const BACKEND_BASE = "http://localhost:8000";

async function safeFetch(url: string, init?: RequestInit) {
  try {
    const res = await fetch(url, init);
    if (res.ok) return res;
  } catch (e) {
    console.warn(`Fetch to ${url} failed, trying fallback direct backend port`, e);
  }

  // Fallback to direct backend URL if proxy fails
  const directUrl = url.replace("/api/backend", BACKEND_BASE);
  const res = await fetch(directUrl, init);
  if (!res.ok) throw new Error(`API call to ${directUrl} failed with status ${res.status}`);
  return res;
}

export async function askCopilot(question: string): Promise<QueryResponse> {
  const res = await safeFetch("/api/backend/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: 8 }),
  });
  return res.json();
}

export async function ingestDocument(file: File, docType: string): Promise<IngestResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await safeFetch(`/api/backend/ingest?doc_type=${docType}`, {
    method: "POST",
    body: form,
  });
  return res.json();
}

export async function seedDemoCorpus(): Promise<{ status: string; message: string; documents: string[] }> {
  const res = await safeFetch("/api/backend/ingest/seed", {
    method: "POST",
  });
  return res.json();
}

export async function fetchNeighborhood(entityId: string, depth = 2) {
  const res = await safeFetch(`/api/backend/graph/neighborhood?entity_id=${encodeURIComponent(entityId)}&depth=${depth}`);
  return res.json();
}
