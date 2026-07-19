"""
Simple sliding-window token chunker. Kept dependency-light (tiktoken only)
so it works the same regardless of which LLM/embedding provider is active.
Swap for a semantic/structure-aware chunker (e.g. respecting P&ID
tag-table boundaries) as a fast follow -- flagged in the architecture doc.
"""
import tiktoken

_ENC = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, max_tokens: int = 400, overlap: int = 60) -> list[str]:
    tokens = _ENC.encode(text)
    if not tokens:
        return []

    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(_ENC.decode(chunk_tokens))
        if end == len(tokens):
            break
        start = end - overlap
    return chunks
