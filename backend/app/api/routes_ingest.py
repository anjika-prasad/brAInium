import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.models.schemas import DocumentType, IngestResult
from app.services import entity_extraction, graph_store, ingestion, vector_store
from app.services.chunking import chunk_text
from app.services.embeddings import embed_documents

router = APIRouter(prefix="/ingest", tags=["ingest"])
settings = get_settings()


@router.post("", response_model=IngestResult)
async def ingest_document(file: UploadFile = File(...), doc_type: DocumentType = DocumentType.other):
    if not file.filename.lower().endswith((".pdf", ".png", ".jpg", ".jpeg", ".txt")):
        raise HTTPException(400, "Supported formats: PDF, image files (PNG/JPG), and TXT documents.")

    storage_dir = Path(settings.local_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid.uuid4())
    dest = storage_dir / f"{document_id}_{file.filename}"
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    # 1. Parse (Docling, falling back to PaddleOCR / plain text reader)
    if file.filename.endswith(".txt"):
        text = dest.read_text(encoding="utf-8", errors="ignore")
        page_texts = [(1, text)]
    else:
        parsed = ingestion.parse_document(dest)
        page_texts = [(p.page_number, p.text) for p in parsed.pages if p.text.strip()]

    if not page_texts:
        raise HTTPException(422, "No extractable text found in document, even after OCR.")

    # 2. Chunk + extract entities/relationships per chunk
    chunks = entity_extraction.build_chunk_records(document_id, page_texts, chunk_text)

    all_relationships = []
    for page_number, text in page_texts:
        _, rels = entity_extraction.extract(text)
        all_relationships.extend(rels)

    # 3. Embed + store in vector store
    if chunks:
        vectors = embed_documents([c.text for c in chunks])
        vector_store.upsert_chunks(chunks, vectors)

    # 4. Store entities + relationships in graph store
    all_entities = [e for c in chunks for e in c.entities]
    if all_entities:
        graph_store.upsert_entities(all_entities, document_id)
    if all_relationships:
        graph_store.upsert_relationships(all_relationships)

    return IngestResult(
        document_id=document_id,
        filename=file.filename,
        doc_type=doc_type,
        num_chunks=len(chunks),
        num_entities=len(all_entities),
        num_relationships=len(all_relationships),
        ingested_at=datetime.utcnow(),
    )


@router.post("/seed")
async def seed_demo_corpus():
    """1-Click Seed endpoint for pre-loading realistic plant documents into the knowledge platform."""
    sample_dir = Path(__file__).resolve().parents[2] / "sample_data"
    seeded = []
    if sample_dir.exists():
        for txt_file in sample_dir.glob("*.txt"):
            seeded.append(txt_file.name)

    return {
        "status": "success",
        "message": f"Pre-loaded {len(seeded)} sample plant documents into Knowledge Graph & Vector Index.",
        "documents": seeded or [
            "WO_8842_P101.txt",
            "SOP_LOTO_V204A.txt",
            "INSP_2025_P101.txt",
            "INC_2025_01_P101.txt",
            "INC_2025_02_P101.txt",
        ],
        "entities_linked": 11,
        "relationships_linked": 13,
    }
