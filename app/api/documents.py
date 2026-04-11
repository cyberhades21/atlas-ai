import asyncio
import json
import os
import uuid

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse

from app.pipeline.ingest_progress import ingest_bus
from app.services.ingestion_service import ingest_document

router = APIRouter(prefix="/documents")

UPLOAD_DIR = "data/documents"


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Save the uploaded file, register a progress task, kick off ingestion as a
    background asyncio task, and return task_id immediately.

    The browser then opens GET /documents/progress/{task_id} as an SSE stream
    to receive real stage-by-stage progress events.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(UPLOAD_DIR, file.filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    task_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    ingest_bus.create_task(task_id, loop)

    # Run ingestion as a non-blocking background task
    asyncio.create_task(ingest_document(filepath, file.filename, task_id=task_id))

    return {"status": "started", "task_id": task_id, "filename": file.filename}


@router.get("/progress/{task_id}")
async def ingestion_progress(task_id: str):
    """
    SSE stream of ingestion progress events for a given task_id.
    Each event: { stage, detail, pct, chunk_idx, total_chunks, ts }
    Stream closes when ingestion emits None (sentinel).

    The queue is kept alive until this endpoint reads the sentinel, so
    late-connecting clients (browser opens SSE after ingestion finishes)
    still receive the final done event rather than a "Task not found" error.
    """
    # Retry briefly in case the background task hasn't registered yet
    queue = None
    for _ in range(20):
        queue = ingest_bus.get_queue(task_id)
        if queue is not None:
            break
        await asyncio.sleep(0.05)

    if queue is None:
        async def not_found():
            yield f"data: {json.dumps({'stage':'error','detail':'Task not found','pct':0})}\n\n"
        return StreamingResponse(not_found(), media_type="text/event-stream")

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=300.0)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue

                if event is None:
                    # Ingestion finished — send final 100% done event then close
                    yield f"data: {json.dumps({'stage':'done','detail':'Indexed successfully','pct':100})}\n\n"
                    break

                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            ingest_bus.cleanup_task(task_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
