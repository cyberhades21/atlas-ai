"""
Debug / visualization endpoints.

GET  /vectors              — PCA-reduced 2D positions of all embeddings
GET  /vectors/updates      — SSE stream: new points after each ingest
GET  /vectors/last-query   — last query's retrieved chunk IDs, scores, and projected position
POST /vectors/project-query — project a raw embedding into the current PCA space
"""

import asyncio
import json
import logging
from typing import List

import chromadb
import numpy as np
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sklearn.decomposition import PCA

from app.pipeline.vector_updates import vector_update_bus

logger = logging.getLogger(__name__)
router = APIRouter()

client = chromadb.PersistentClient(path="data/vector_db")

# ---------------------------------------------------------------------------
# In-memory state for the last query overlay
# Written by instrumented_query.py after vector_retrieval completes.
# ---------------------------------------------------------------------------
_last_query_state: dict = {
    "retrieved_ids": [],   # list of ChromaDB chunk IDs
    "scores":        {},   # id → similarity score (0-1)
    "query_xy":      None, # {"x": float, "y": float} in PCA space
}


def _fit_pca(embeddings: list):
    """Fit PCA on all embeddings and return (pca, reduced_array)."""
    pca = PCA(n_components=2)
    reduced = pca.fit_transform(embeddings)
    return pca, reduced


# ---------------------------------------------------------------------------
# GET /vectors
# ---------------------------------------------------------------------------

@router.get("/vectors")
def inspect_vectors():
    """Return all collection points with PCA-reduced 2D coordinates."""
    try:
        collection = client.get_collection("atlas")
    except Exception:
        return []

    data = collection.get(include=["embeddings", "documents", "metadatas"])
    if data["embeddings"] is None or len(data["embeddings"]) == 0:
        return []

    _, reduced = _fit_pca(data["embeddings"])

    return [
        {
            "id":       data["ids"][i],
            "x":        float(reduced[i][0]),
            "y":        float(reduced[i][1]),
            "text":     data["documents"][i][:200],
            "document": data["metadatas"][i]["document"],
        }
        for i in range(len(reduced))
    ]


# ---------------------------------------------------------------------------
# GET /vectors/updates  — SSE stream
# ---------------------------------------------------------------------------

@router.get("/vectors/updates")
async def vector_updates(request: Request):
    """
    Server-Sent Events stream.  Emits a JSON array of new points whenever
    store_embeddings() ingests new chunks.
    """
    loop = asyncio.get_event_loop()
    q = vector_update_bus.subscribe(loop)

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    points = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {json.dumps(points)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            vector_update_bus.unsubscribe(q)

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# GET /vectors/last-query
# ---------------------------------------------------------------------------

@router.get("/vectors/last-query")
def get_last_query():
    """Return the last query overlay state (retrieved IDs, scores, projected position)."""
    return _last_query_state


# ---------------------------------------------------------------------------
# POST /vectors/project-query
# ---------------------------------------------------------------------------

class ProjectQueryRequest(BaseModel):
    embedding: List[float]


@router.post("/vectors/project-query")
def project_query(body: ProjectQueryRequest):
    """
    Project a raw query embedding into the same 2D PCA space as the collection.
    Updates _last_query_state["query_xy"] and returns the projected point.
    """
    try:
        collection = client.get_collection("atlas")
        all_data = collection.get(include=["embeddings"])
        if all_data["embeddings"] is None or len(all_data["embeddings"]) == 0:
            return {"x": 0.0, "y": 0.0}

        pca, _ = _fit_pca(all_data["embeddings"])
        xy = pca.transform([body.embedding])[0]
        result = {"x": float(xy[0]), "y": float(xy[1])}
        _last_query_state["query_xy"] = result
        return result
    except Exception as exc:
        logger.warning("project_query failed: %s", exc)
        return {"x": 0.0, "y": 0.0}
