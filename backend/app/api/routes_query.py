from fastapi import APIRouter

from app.models.schemas import QueryRequest, QueryResponse
from app.services.retrieval import answer_query

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query_copilot(req: QueryRequest):
    return answer_query(req)
