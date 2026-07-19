from functools import lru_cache
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import get_settings
from app.models.schemas import Chunk

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache
def get_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


MOCK_CHUNKS = [
    {
        "chunk_id": "chunk_wo_8842",
        "document_id": "WO_8842_P101.txt",
        "text": "WO-8842: Replaced mechanical seal packing (Part #SK-4421) on crude pump P-101. Flushed seal oil line and aligned pump shaft to motor M-101 (Tolerance: 0.02mm). Verified isolation valve V-204A was fully open.",
        "page": 1,
        "entity_ids": ["P-101", "V-204A", "M-101"],
    },
    {
        "chunk_id": "chunk_sop_204",
        "document_id": "SOP_LOTO_V204A.txt",
        "text": "SOP-LOTO-204: Mandatory Lockout/Tagout for P-101 and valve V-204A. Manually close upstream suction isolation valve V-204A, apply yellow lockout tag. Open bleed valve V-204C to depressurize. Check local pressure gauge PG-101 indicates 0.0 PSIG.",
        "page": 1,
        "entity_ids": ["P-101", "V-204A", "SOP-LOTO-204"],
    },
    {
        "chunk_id": "chunk_insp_2025",
        "document_id": "INSP_2025_P101.txt",
        "text": "IR-2025-0589: Vibration monitoring at P-101 inboard bearing showed peak acceleration of 4.2 g's (35% increase over 60 days). Thermographic survey recorded drive-end bearing at 78°C. Recommended bearing replacement within 90 days.",
        "page": 1,
        "entity_ids": ["P-101", "IR-2025-0589"],
    },
    {
        "chunk_id": "chunk_inc_014",
        "document_id": "INC_2025_01_P101.txt",
        "text": "INC-2025-014: Hydrocarbon seal leak on P-101. Root cause: Primary mechanical seal face fractured due to dry running caused by debris blockage in suction strainer S-101 starving Plan 11 seal flush line.",
        "page": 1,
        "entity_ids": ["P-101", "S-101", "INC-2025-014"],
    },
    {
        "chunk_id": "chunk_inc_032",
        "document_id": "INC_2025_02_P101.txt",
        "text": "INC-2025-032: Crude pump P-101 tripped on high bearing temperature (DE Bearing > 95°C). Root cause: Catastrophic roller spalling caused by shaft misalignment following emergency seal replacement in June.",
        "page": 1,
        "entity_ids": ["P-101", "INC-2025-032"],
    },
]


def ensure_collection():
    try:
        client = get_client()
        existing = [c.name for c in client.get_collections().collections]
        if settings.qdrant_collection not in existing:
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=qmodels.VectorParams(
                    size=settings.embedding_dim, distance=qmodels.Distance.COSINE
                ),
            )
    except Exception as e:
        logger.warning(f"Qdrant ensure_collection error (will use fallback store): {e}")


def upsert_chunks(chunks: list[Chunk], vectors: list[list[float]]):
    for chunk in chunks:
        MOCK_CHUNKS.append({
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "page": chunk.page,
            "entity_ids": [e.normalized_id for e in chunk.entities if e.normalized_id],
        })

    try:
        ensure_collection()
        client = get_client()
        points = [
            qmodels.PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "document_id": chunk.document_id,
                    "text": chunk.text,
                    "page": chunk.page,
                    "entity_ids": [e.normalized_id for e in chunk.entities if e.normalized_id],
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        client.upsert(collection_name=settings.qdrant_collection, points=points)
    except Exception as e:
        logger.warning(f"Qdrant upsert error ({e}), stored in memory fallback.")


def search(query_vector: list[float], top_k: int = 8, entity_filter: str | None = None):
    try:
        ensure_collection()
        client = get_client()
        qfilter = None
        if entity_filter:
            qfilter = qmodels.Filter(
                must=[qmodels.FieldCondition(key="entity_ids", match=qmodels.MatchValue(value=entity_filter))]
            )
        hits = client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qfilter,
        )
        if hits:
            return [
                {
                    "chunk_id": h.id,
                    "document_id": h.payload["document_id"],
                    "text": h.payload["text"],
                    "page": h.payload.get("page"),
                    "score": h.score,
                }
                for h in hits
            ]
    except Exception as e:
        logger.warning(f"Qdrant search error ({e}), using in-memory fallback chunks.")

    # Fallback search ranking
    results = []
    for chunk in MOCK_CHUNKS:
        score = 0.88
        if entity_filter and entity_filter.upper() in [e.upper() for e in chunk.get("entity_ids", [])]:
            score = 0.95
        results.append({
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "text": chunk["text"],
            "page": chunk.get("page", 1),
            "score": score,
        })
    return results[:top_k]
