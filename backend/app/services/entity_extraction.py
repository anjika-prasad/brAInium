"""
Extracts entities and relationships from a text chunk using a constrained
JSON schema. Keeping the schema fixed (rather than free-form NER) is what
makes downstream graph construction reliable -- every entity gets a
normalized_id that graph_store.py can MERGE on, so the same equipment tag
mentioned in a work order and in a P&ID resolves to the same graph node.
"""
import re
import uuid

from app.models.schemas import Chunk, Entity, EntityType, Relationship
from app.services.llm_client import get_llm_client, safe_json_parse

_SYSTEM_PROMPT = """You are an industrial document analyst extracting structured knowledge
from plant documents (P&IDs, work orders, SOPs, inspection reports, incident reports,
OEM manuals, regulatory text).

Extract entities and relationships as JSON with this exact shape:
{
  "entities": [
    {"text": "<as written in doc>", "type": "Equipment|Person|Procedure|Regulation|Incident|Parameter|Location|Date",
     "normalized_id": "<canonical id, e.g. equipment tag 'P-101', or a slugified name for others>"}
  ],
  "relationships": [
    {"source": "<normalized_id>", "target": "<normalized_id>", "relation": "MAINTAINED_BY|REFERENCES|FAILED_WITH|GOVERNED_BY|INVOLVES|ROOT_CAUSE|PART_OF|PERFORMED_BY"}
  ]
}

Rules:
- Only extract entities that are explicitly present in the text.
- Equipment tags follow patterns like P-101, V-204A, HX-30, TK-12 -- preserve exact formatting as normalized_id.
- If no clean tag exists for a Person/Procedure/Regulation, slugify the name (lowercase, hyphens).
- Do not invent relationships not supported by the text.
- Return ONLY the JSON object, no commentary.
"""


def extract(chunk_text: str) -> tuple[list[Entity], list[Relationship]]:
    llm = get_llm_client()
    raw = llm.complete(_SYSTEM_PROMPT, chunk_text, json_mode=True)
    data = safe_json_parse(raw)

    if "error" in data:
        return [], []

    entities = []
    for item in data.get("entities", []):
        try:
            entities.append(
                Entity(
                    text=item["text"],
                    type=EntityType(item["type"]),
                    normalized_id=item.get("normalized_id") or _slugify(item["text"]),
                )
            )
        except (KeyError, ValueError):
            continue  # skip malformed items rather than failing the whole chunk

    relationships = []
    for item in data.get("relationships", []):
        try:
            relationships.append(
                Relationship(
                    source=item["source"],
                    target=item["target"],
                    relation=item["relation"],
                )
            )
        except KeyError:
            continue

    return entities, relationships


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_chunk_records(document_id: str, page_texts: list[tuple[int, str]], chunker) -> list[Chunk]:
    """Chunk each page and attach extracted entities per chunk."""
    chunks: list[Chunk] = []
    for page_number, text in page_texts:
        for piece in chunker(text):
            entities, _ = extract(piece)
            chunks.append(
                Chunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    text=piece,
                    page=page_number,
                    entities=entities,
                )
            )
    return chunks
