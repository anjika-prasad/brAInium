"""
Query planner + hybrid retrieval.

The key design decision: not every question should hit the same
pipeline. "What does the SOP say about valve lockout" is a semantic
match -> vector search. "Which pumps failed more than twice this year
and why" is a relationship/aggregation question -> graph traversal.
Most real operational questions need both. A small LLM call classifies
the question and extracts any equipment/entity references before we
touch the stores, which is what turns this from "search" into
"reasoning across systems."
"""
import re

from app.models.schemas import QueryRequest, QueryResponse, SourceCitation
from app.services import graph_store, vector_store
from app.services.embeddings import embed_query
from app.services.llm_client import get_llm_client, safe_json_parse

_PLANNER_PROMPT = """Classify this industrial operations question and extract any
equipment tags mentioned (patterns like P-101, V-204A, HX-30).

Return JSON: {"mode": "vector"|"graph"|"hybrid", "equipment_tags": ["..."], "reasoning": "<short>"}

- "vector": general/semantic questions about procedures, standards, how-to.
- "graph": questions about relationships, history, counts, or "everything connected to X".
- "hybrid": needs both a document answer AND relationship context (most maintenance/RCA questions).
"""

_ANSWER_PROMPT = """You are an industrial knowledge copilot. Answer the operator's question
using ONLY the provided context (retrieved document excerpts and/or graph facts).
Cite which source each claim comes from using [doc_id] markers. If the context is
insufficient, say so explicitly rather than guessing -- this is a safety-relevant system.

Question: {question}

Context:
{context}

Respond in plain, direct operational language a field technician can act on.
"""


import logging

logger = logging.getLogger(__name__)

def _plan(question: str) -> dict:
    try:
        llm = get_llm_client()
        raw = llm.complete(_PLANNER_PROMPT, question, json_mode=True)
        plan = safe_json_parse(raw)
        if "error" in plan:
            # Fail safe to hybrid rather than guessing the wrong single mode.
            tags = re.findall(r"\b[A-Z]{1,3}-\d{2,4}[A-Z]?\b", question)
            return {"mode": "hybrid", "equipment_tags": tags, "reasoning": "planner_fallback"}
        return plan
    except Exception as e:
        logger.warning(f"Query planner LLM failed ({e}). Using offline regex planner fallback.")
        tags = re.findall(r"\b[A-Z]{1,3}-\d{2,4}[A-Z]?\b", question)
        mode = "hybrid" if tags else "vector"
        if "fail" in question.lower() or "incident" in question.lower() or "history" in question.lower():
            mode = "graph"
        return {"mode": mode, "equipment_tags": tags, "reasoning": "regex_planner_fallback"}


def answer_query(req: QueryRequest) -> QueryResponse:
    plan = _plan(req.question)
    mode = plan.get("mode", "hybrid")
    tags = plan.get("equipment_tags", [])

    context_blocks: list[str] = []
    sources: list[SourceCitation] = []
    graph_paths: list[str] = []

    if mode in ("vector", "hybrid"):
        query_vec = embed_query(req.question)
        entity_filter = tags[0] if tags else req.filters.get("equipment")
        hits = vector_store.search(query_vec, top_k=req.top_k, entity_filter=entity_filter)
        for h in hits:
            context_blocks.append(f"[{h['document_id']}] {h['text']}")
            sources.append(
                SourceCitation(
                    document_id=h["document_id"],
                    filename=h["document_id"],
                    page=h.get("page"),
                    snippet=h["text"][:280],
                    score=h["score"],
                )
            )

    if mode in ("graph", "hybrid") and tags:
        for tag in tags:
            history = graph_store.failure_history(tag)
            if history:
                summary = "; ".join(
                    f"{row['incident']} (root cause: {row.get('root_cause') or 'undetermined'})"
                    for row in history
                )
                context_blocks.append(f"[graph:{tag}] Failure history: {summary}")
                graph_paths.append(f"failure_history({tag})")

    if not context_blocks:
        return QueryResponse(
            answer="I couldn't find relevant documents or graph records for this question. "
                   "Try rephrasing, or confirm the equipment tag / document set has been ingested.",
            confidence=0.0,
            sources=[],
            retrieval_mode=mode,
            graph_paths_used=graph_paths,
        )

    try:
        llm = get_llm_client()
        system = "You are an industrial knowledge copilot for field technicians and engineers. Be precise, cite sources, and never guess on safety-relevant claims."
        user_prompt = _ANSWER_PROMPT.format(question=req.question, context="\n\n".join(context_blocks))
        answer_text = llm.complete(system, user_prompt, json_mode=False)
    except Exception as e:
        logger.warning(f"Answer LLM call failed ({e}). Using offline answer generator fallback.")
        from app.services.llm_client import FallbackDemoClient
        fallback_llm = FallbackDemoClient()
        answer_text = fallback_llm.complete("", req.question, json_mode=False)

    avg_score = sum(s.score for s in sources) / len(sources) if sources else 0.6
    confidence = round(min(0.95, avg_score), 2)

    return QueryResponse(
        answer=answer_text,
        confidence=confidence,
        sources=sources,
        retrieval_mode=mode,
        graph_paths_used=graph_paths,
    )
