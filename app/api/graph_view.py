from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path

router = APIRouter()


@router.get("/graph-view", response_class=HTMLResponse)
def graph_page():

    html = Path("app/static/graph.html").read_text(encoding="utf-8")

    return HTMLResponse(html)