from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    pnid = "pnid"
    work_order = "work_order"
    sop = "sop"
    inspection_report = "inspection_report"
    incident_report = "incident_report"
    manual = "manual"
    email = "email"
    regulation = "regulation"
    other = "other"


class EntityType(str, Enum):
    equipment = "Equipment"
    person = "Person"
    procedure = "Procedure"
    regulation = "Regulation"
    incident = "Incident"
    parameter = "Parameter"
    location = "Location"
    date = "Date"


class Entity(BaseModel):
    text: str
    type: EntityType
    normalized_id: Optional[str] = None  # e.g. canonical equipment tag "P-101"
    attributes: dict = Field(default_factory=dict)


class Relationship(BaseModel):
    source: str          # normalized_id of source entity
    target: str          # normalized_id of target entity
    relation: str         # e.g. "MAINTAINED_BY", "REFERENCES", "FAILED_WITH"
    attributes: dict = Field(default_factory=dict)


class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    page: Optional[int] = None
    entities: list[Entity] = Field(default_factory=list)


class IngestResult(BaseModel):
    document_id: str
    filename: str
    doc_type: DocumentType
    num_chunks: int
    num_entities: int
    num_relationships: int
    ingested_at: datetime


class QueryRequest(BaseModel):
    question: str
    top_k: int = 8
    filters: dict = Field(default_factory=dict)  # e.g. {"equipment": "P-101"}


class SourceCitation(BaseModel):
    document_id: str
    filename: str
    page: Optional[int] = None
    snippet: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[SourceCitation]
    retrieval_mode: str   # "vector" | "graph" | "hybrid"
    graph_paths_used: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    label: str
    type: EntityType
    properties: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class GraphSubgraph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
