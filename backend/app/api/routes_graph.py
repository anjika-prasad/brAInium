from fastapi import APIRouter, Query

from app.models.schemas import GraphSubgraph
from app.services.graph_store import neighborhood

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/neighborhood", response_model=GraphSubgraph)
async def get_neighborhood(entity_id: str = Query(...), depth: int = Query(2, ge=1, le=4)):
    return neighborhood(entity_id, depth=depth)
