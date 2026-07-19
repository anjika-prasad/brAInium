from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_graph, routes_ingest, routes_query

app = FastAPI(
    title="Industrial Knowledge Intelligence API",
    description="Unified Asset & Operations Brain -- ingestion, hybrid RAG+graph retrieval, and copilot endpoints.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_ingest.router)
app.include_router(routes_query.router)
app.include_router(routes_graph.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
