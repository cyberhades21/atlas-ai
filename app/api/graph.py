import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.storage.graph_store import conn
from app.pipeline.graph_updates import graph_update_bus

router = APIRouter()


@router.get("/graph")
def get_graph():
    cursor = conn.execute(
        "SELECT entity1, relation, entity2 FROM relationships"
    )
    nodes = set()
    edges = []
    for entity1, relation, entity2 in cursor.fetchall():
        nodes.add(entity1)
        nodes.add(entity2)
        edges.append({"data": {"source": entity1, "target": entity2, "label": relation}})

    return {
        "nodes": [{"data": {"id": n}} for n in nodes],
        "edges": edges,
    }


@router.get("/graph/updates")
async def graph_updates(request: Request):
    """
    SSE stream that pushes new nodes/edges to graph.html whenever a document
    is ingested.  The client merges them into the live Cytoscape instance.
    Payload: { nodes: [{data:{id}},...], edges: [{data:{source,target,label}},...] }
    """
    loop = asyncio.get_event_loop()
    queue = graph_update_bus.subscribe(loop)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            graph_update_bus.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
