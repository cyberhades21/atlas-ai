from fastapi import APIRouter
from pydantic import BaseModel

from app.services.query_service import answer_query


router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
async def query(data: QueryRequest):

    question = data.question

    result = answer_query(question)

    return result