from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.llm import DEFAULT_MODEL
from app.services.query_service import answer_query, DEFAULT_TOP_K

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    model: str = DEFAULT_MODEL
    top_k: int = DEFAULT_TOP_K


@router.post("/query")
async def query(data: QueryRequest):
    result = answer_query(data.question, top_k=data.top_k, model=data.model)
    return result
