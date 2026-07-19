"""
Wraps BAAI/bge-large-en-v1.5 (1024-dim). BGE models expect a query
instruction prefix for asymmetric search quality -- documents are
embedded raw, queries get the instruction prepended.
"""
from functools import lru_cache

from app.config import get_settings

settings = get_settings()

_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


def embed_documents(texts: list[str]) -> list[list[float]]:
    vectors = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    vector = _model().encode(_QUERY_INSTRUCTION + text, normalize_embeddings=True)
    return vector.tolist()
