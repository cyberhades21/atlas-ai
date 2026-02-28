from fastapi import APIRouter
from app.services.query_service import answer_query

router = APIRouter()


@router.post("/query")
async def query(data: dict):

    question = data["question"]

    return answer_query(question)