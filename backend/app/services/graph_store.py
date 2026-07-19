from functools import lru_cache
import logging
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError

from app.config import get_settings
from app.models.schemas import Entity, GraphSubgraph, Relationship, EntityType, GraphNode, GraphEdge

logger = logging.getLogger(__name__)
settings = get_settings()


@lru_cache
def get_driver():
    return GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))


def init_constraints():
    try:
        with get_driver().session() as session:
            session.run(
                "CREATE CONSTRAINT entity_id IF NOT EXISTS "
                "FOR (n:Entity) REQUIRE n.id IS UNIQUE"
            )
    except Exception as e:
        logger.warning(f"Neo4j init_constraints failed (will use in-memory fallback if needed): {e}")


# Pre-loaded sample plant fallback graph for zero-friction hackathon demos
MOCK_NODES = {
    "P-101": GraphNode(id="P-101", label="P-101 Crude Pump", type=EntityType.equipment),
    "V-204A": GraphNode(id="V-204A", label="V-204A Suction Valve", type=EntityType.equipment),
    "M-101": GraphNode(id="M-101", label="M-101 Pump Motor", type=EntityType.equipment),
    "S-101": GraphNode(id="S-101", label="S-101 Suction Strainer", type=EntityType.equipment),
    "WO-8842": GraphNode(id="WO-8842", label="WO-8842 Seal Maintenance", type=EntityType.procedure),
    "SOP-LOTO-204": GraphNode(id="SOP-LOTO-204", label="SOP-LOTO-204 Protocol", type=EntityType.procedure),
    "IR-2025-0589": GraphNode(id="IR-2025-0589", label="IR-2025 Vibration Inspection", type=EntityType.regulation),
    "INC-2025-014": GraphNode(id="INC-2025-014", label="INC-014 Seal Flush Fracture", type=EntityType.incident),
    "INC-2025-032": GraphNode(id="INC-2025-032", label="INC-032 Bearing Overheating", type=EntityType.incident),
    "J_Miller": GraphNode(id="J_Miller", label="J. Miller (Senior Tech)", type=EntityType.person),
    "S_Kumar": GraphNode(id="S_Kumar", label="S. Kumar (Reliability Eng)", type=EntityType.person),
}

MOCK_EDGES = [
    GraphEdge(source="P-101", target="V-204A", relation="CONNECTED_TO"),
    GraphEdge(source="P-101", target="M-101", relation="DRIVEN_BY"),
    GraphEdge(source="P-101", target="S-101", relation="PROTECTED_BY"),
    GraphEdge(source="WO-8842", target="P-101", relation="MAINTAINED"),
    GraphEdge(source="WO-8842", target="J_Miller", relation="PERFORMED_BY"),
    GraphEdge(source="SOP-LOTO-204", target="V-204A", relation="REQUIRES_ISOLATION"),
    GraphEdge(source="SOP-LOTO-204", target="P-101", relation="GOVERNS_SAFETY"),
    GraphEdge(source="IR-2025-0589", target="P-101", relation="INSPECTED"),
    GraphEdge(source="IR-2025-0589", target="S_Kumar", relation="REPORTED_BY"),
    GraphEdge(source="INC-2025-014", target="P-101", relation="INVOLVES"),
    GraphEdge(source="INC-2025-014", target="S-101", relation="ROOT_CAUSE"),
    GraphEdge(source="INC-2025-032", target="P-101", relation="INVOLVES"),
    GraphEdge(source="INC-2025-032", target="INC-2025-014", relation="FOLLOWS_OUTAGE"),
]


def upsert_entities(entities: list[Entity], document_id: str):
    by_type: dict[str, list[dict]] = {}
    for e in entities:
        if not e.normalized_id:
            continue
        by_type.setdefault(e.type.value, []).append(
            {"normalized_id": e.normalized_id, "text": e.text, "type": e.type.value}
        )
        MOCK_NODES[e.normalized_id] = GraphNode(id=e.normalized_id, label=e.text, type=e.type)

    try:
        with get_driver().session() as session:
            session.run("MERGE (d:Document {id: $document_id})", document_id=document_id)
            for etype, items in by_type.items():
                session.run(
                    f"""
                    UNWIND $items AS e
                    MERGE (n:Entity:`{etype}` {{id: e.normalized_id}})
                    ON CREATE SET n.label = e.text, n.created_at = timestamp()
                    SET n.last_seen_doc = $document_id
                    WITH n
                    MATCH (d:Document {{id: $document_id}})
                    MERGE (n)-[:MENTIONED_IN]->(d)
                    """,
                    items=items,
                    document_id=document_id,
                )
    except Exception as e:
        logger.warning(f"Neo4j upsert_entities fallback to in-memory: {e}")


def upsert_relationships(relationships: list[Relationship]):
    for rel in relationships:
        MOCK_EDGES.append(GraphEdge(source=rel.source, target=rel.target, relation=rel.relation.upper()))

    try:
        with get_driver().session() as session:
            for rel in relationships:
                rel_type = "".join(c if c.isalnum() else "_" for c in rel.relation.upper())
                session.run(
                    f"""
                    MATCH (a:Entity {{id: $source}})
                    MATCH (b:Entity {{id: $target}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    SET r += $attributes
                    """,
                    source=rel.source,
                    target=rel.target,
                    attributes=rel.attributes,
                )
    except Exception as e:
        logger.warning(f"Neo4j upsert_relationships fallback: {e}")


def neighborhood(entity_id: str, depth: int = 2) -> GraphSubgraph:
    """Pull local subgraph with graceful fallback."""
    try:
        with get_driver().session() as session:
            result = session.run(
                f"""
                MATCH path = (start:Entity {{id: $entity_id}})-[*1..{depth}]-(connected)
                RETURN path
                LIMIT 200
                """,
                entity_id=entity_id,
            )
            nodes: dict[str, GraphNode] = {}
            edges: list[GraphEdge] = []
            for record in result:
                path = record["path"]
                for node in path.nodes:
                    node_type = next((l for l in node.labels if l != "Entity"), "other")
                    try:
                        etype = EntityType(node_type)
                    except ValueError:
                        etype = EntityType.equipment
                    nodes[node["id"]] = GraphNode(
                        id=node["id"], label=node.get("label", node["id"]), type=etype
                    )
                for rel in path.relationships:
                    edges.append(
                        GraphEdge(source=rel.start_node["id"], target=rel.end_node["id"], relation=rel.type)
                    )
            if nodes:
                return GraphSubgraph(nodes=list(nodes.values()), edges=edges)
    except Exception as e:
        logger.warning(f"Neo4j neighborhood error ({e}), serving fallback graph.")

    # Fallback neighborhood logic
    target_id = entity_id.upper()
    found_nodes = {}
    found_edges = []

    if target_id in MOCK_NODES:
        found_nodes[target_id] = MOCK_NODES[target_id]

    for edge in MOCK_EDGES:
        if edge.source == target_id or edge.target == target_id or target_id in ("P-101", "ALL"):
            found_edges.append(edge)
            if edge.source in MOCK_NODES:
                found_nodes[edge.source] = MOCK_NODES[edge.source]
            if edge.target in MOCK_NODES:
                found_nodes[edge.target] = MOCK_NODES[edge.target]

    if not found_nodes:
        # Return default P-101 cluster if unknown entity
        return GraphSubgraph(nodes=list(MOCK_NODES.values())[:6], edges=MOCK_EDGES[:6])

    return GraphSubgraph(nodes=list(found_nodes.values()), edges=found_edges)


def failure_history(equipment_id: str) -> list[dict]:
    try:
        with get_driver().session() as session:
            result = session.run(
                """
                MATCH (eq:Entity {id: $equipment_id})<-[:INVOLVES]-(i:Entity:Incident)
                OPTIONAL MATCH (i)-[:ROOT_CAUSE]->(cause:Entity)
                OPTIONAL MATCH (i)-[:MENTIONED_IN]->(doc:Document)
                RETURN i.label AS incident, cause.label AS root_cause, doc.id AS document_id
                ORDER BY i.created_at DESC
                """,
                equipment_id=equipment_id,
            )
            res = [dict(r) for r in result]
            if res:
                return res
    except Exception as e:
        logger.warning(f"Neo4j failure_history error ({e}), returning fallback history.")

    return [
        {
            "incident": "INC-2025-014 (Mechanical Seal Flushing Failure)",
            "root_cause": "Particulate debris blockage in suction strainer S-101 starving Plan 11 seal flush cavity",
            "document_id": "INC_2025_01_P101.txt",
        },
        {
            "incident": "INC-2025-032 (Drive-End Bearing Overheating & Spalling)",
            "root_cause": "Uncorrected motor shaft misalignment following June emergency seal replacement",
            "document_id": "INC_2025_02_P101.txt",
        },
    ]
