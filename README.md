# Unified Asset & Operations Brain

An AI-powered Industrial Knowledge Intelligence platform: ingest heterogeneous plant
documents (P&IDs, work orders, SOPs, inspection reports, incident reports, manuals),
extract entities into a knowledge graph, and answer operational questions through a
hybrid retrieval copilot that cites its sources.

Built for the "AI for Industrial Knowledge Intelligence" hackathon brief. This
prototype focuses on two of the five suggested modules in depth — **Universal
Document Ingestion & Knowledge Graph** and **Expert Knowledge Copilot** — with the
architecture designed so Maintenance Intelligence, Compliance Intelligence, and
Lessons Learned can be added as new graph queries + prompt templates on the same
backbone, without re-architecting anything.

## Why graph + RAG, not RAG alone

Plain document RAG answers "what does the SOP say." It cannot answer "which pumps
failed more than twice this year and why" — that requires joining work orders,
incident reports, and RCA notes that live in different documents entirely. This
prototype builds a knowledge graph (Neo4j) alongside a vector index (Qdrant), and a
query planner decides per-question whether to do semantic search, graph traversal,
or both. That fusion is what "connects the dots no individual team member can
connect alone" — a direct claim from the problem brief — actually means in practice,
rather than being a slogan.

## Architecture

```
                     ┌─────────────────────────────────────────┐
                     │              Next.js Frontend             │
                     │  Copilot Chat · Ingest Console · Graph View│
                     └───────────────────┬─────────────────────┘
                                          │ REST
                     ┌───────────────────▼─────────────────────┐
                     │              FastAPI Backend               │
                     │                                             │
   ┌────────────┐    │  /ingest ─┐                                 │
   │  Upload     │───▶│           ▼                                │
   │  PDF/Image  │    │   ┌───────────────┐   ┌──────────────────┐ │
   └────────────┘    │   │ Docling parser │──▶│ PaddleOCR fallback│ │
                      │   └───────┬───────┘   │ (scanned pages)   │ │
                      │           ▼            └──────────────────┘ │
                      │   ┌───────────────┐                         │
                      │   │  Chunking     │                         │
                      │   └───────┬───────┘                         │
                      │           ▼                                 │
                      │   ┌────────────────────────┐                │
                      │   │ LLM Entity/Relationship  │               │
                      │   │ Extraction (fixed schema)│               │
                      │   └────┬──────────────┬─────┘                │
                      │        ▼              ▼                      │
                      │  ┌───────────┐  ┌─────────────┐              │
                      │  │ bge-large  │  │  Neo4j      │              │
                      │  │ embeddings │  │  graph      │              │
                      │  └─────┬─────┘  │  upsert     │               │
                      │        ▼        └──────┬──────┘              │
                      │  ┌───────────┐         │                     │
                      │  │  Qdrant    │         │                     │
                      │  │  vectors   │         │                     │
                      │  └─────┬─────┘         │                     │
                      │        │                │                     │
                      │  /query ▼                ▼                    │
                      │  ┌──────────────────────────────┐             │
                      │  │  Query Planner (vector/graph/  │            │
                      │  │  hybrid) + Hybrid Retrieval     │            │
                      │  └──────────────┬───────────────┘             │
                      │                 ▼                              │
                      │        LLM Answer + Citations                  │
                      └─────────────────────────────────────────────┘
                                          │
                             PostgreSQL (audit log, doc metadata)
                             S3 / local storage (raw files)
```

## Repository layout

```
backend/    FastAPI app, ingestion pipeline, retrieval, graph & vector store clients
frontend/   Next.js copilot UI (chat, ingestion console, graph explorer)
sample_data/  Notes on building a demo document set
```

## Running it

### 1. Infrastructure

```bash
cd backend
docker compose up -d      # Qdrant, Neo4j, Postgres
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # fill in your LLM_PROVIDER + API key
uvicorn app.main:app --reload --port 8000
```

First run downloads the `bge-large-en-v1.5` embedding model (~1.3GB) — do this ahead
of the demo, not live on stage.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                # http://localhost:3000
```

The frontend proxies `/api/backend/*` to `NEXT_PUBLIC_API_URL` (defaults to
`http://localhost:8000`), so no CORS config needed for local dev.

## API surface

| Endpoint | Purpose |
|---|---|
| `POST /ingest` | Upload a PDF/image, parse, extract entities, embed, write to graph + vector store |
| `POST /query` | Ask a question; hybrid retrieval + cited answer |
| `GET /graph/neighborhood?entity_id=P-101&depth=2` | Pull the local subgraph around an equipment tag |

## Demo script (5 minutes)

1. **Ingest** 3–4 sample documents on the same equipment (a work order, an SOP, an
   inspection report, an incident report) mentioning the same tag, e.g. `P-101`.
   Show the entity/relationship counts returned per document.
2. **Ask a semantic question**: "What does the SOP say about lockout-tagout for
   V-204A?" — show the vector-mode answer with citations.
3. **Ask a relationship question**: "Which pumps failed more than twice this year
   and what were the root causes?" — show the graph-mode / hybrid-mode answer,
   pointing out this couldn't be answered by document search alone.
4. **Open the Graph tab**, load `P-101`'s neighborhood, and show the same equipment
   linked across all four document types — this is the "one document system"
   moment that lands the pitch.
5. Close on the architecture diagram and name the three modules (Maintenance
   Intelligence, Compliance Intelligence, Lessons Learned) as the next layer on the
   same graph, not a rebuild.

## Honest limitations (say these before judges ask)

- Entity extraction quality depends on the LLM and prompt, not a fine-tuned NER
  model — good enough for a demo corpus, needs eval against the domain-expert
  benchmark questions from the brief before any production claim.
- P&ID symbol-level parsing (valves, instruments as graphical symbols, not just
  text) isn't implemented — Docling/OCR extracts text and tables, not vector
  graphics semantics. Flagged as a fast-follow with a CV-based symbol detector.
- No auth/RBAC in this prototype — needed before real plant data touches it.
- Chunking is a fixed sliding window, not structure-aware (e.g. respecting a P&ID
  tag table's boundaries) — noted in `chunking.py`.

## Mapping to judging criteria

- **Innovation**: hybrid graph+vector query planner, not single-mode RAG.
- **Business Impact**: directly targets the downtime and knowledge-cliff numbers in
  the brief — cited answers reduce time-to-answer versus manual document search.
- **Technical Excellence**: two-tier OCR fallback, fixed extraction schema for
  reliable graph merges, pluggable LLM provider.
- **Scalability**: stateless FastAPI backend, horizontally scalable vector/graph
  stores, provider-agnostic LLM layer.
- **UX**: mobile-responsive chat-first interface built for field technicians, not
  just engineers at a desktop.
