"""
Simulator API routes.

POST /simulator/run          — start a pipeline run, return run_id
GET  /simulator/stream/{id}  — SSE stream of pipeline events
GET  /simulator/replay/{id}  — return full snapshot of a past run
GET  /simulator/runs         — list all run IDs
POST /simulator/next-step    — advance to next step in step mode
"""

import asyncio
import json
import uuid
import threading

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.pipeline.events import bus
from app.pipeline.instrumented_query import run_instrumented_pipeline, advance_step

router = APIRouter(prefix="/simulator")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    question: str
    step_mode: bool = False


class NextStepRequest(BaseModel):
    run_id: str


# ---------------------------------------------------------------------------
# POST /simulator/run
# ---------------------------------------------------------------------------

@router.post("/run")
async def start_run(body: RunRequest):
    """
    Kick off an instrumented pipeline run in a background thread.
    Returns run_id immediately so the client can open the SSE stream.
    """
    run_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()

    # Register the run queue before the thread starts
    bus.create_run(run_id, loop)

    def _worker():
        run_instrumented_pipeline(run_id, body.question, step_mode=body.step_mode)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()

    return {"run_id": run_id, "step_mode": body.step_mode}


# ---------------------------------------------------------------------------
# GET /simulator/stream/{run_id}
# ---------------------------------------------------------------------------

@router.get("/stream/{run_id}")
async def stream_events(run_id: str):
    """
    Server-Sent Events stream.
    Each pipeline event is sent as an SSE message.
    Stream closes when the pipeline emits None (sentinel).
    """
    queue = bus.get_queue(run_id)

    if queue is None:
        # Run doesn't exist — try to replay from snapshot
        snapshot = bus.get_snapshot(run_id)
        if snapshot:
            async def replay_gen():
                for event in snapshot:
                    yield f"data: {json.dumps(event)}\n\n"
                yield "data: {\"step\":\"pipeline\",\"status\":\"done\",\"payload\":{}}\n\n"
            return StreamingResponse(replay_gen(), media_type="text/event-stream")

        async def not_found():
            yield f"data: {json.dumps({'step':'error','status':'error','payload':{'message':'Run not found'}})}\n\n"
        return StreamingResponse(not_found(), media_type="text/event-stream")

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    # Keep-alive ping
                    yield ": ping\n\n"
                    continue

                if event is None:
                    # Pipeline signalled completion
                    break

                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ---------------------------------------------------------------------------
# POST /simulator/next-step
# ---------------------------------------------------------------------------

@router.post("/next-step")
async def next_step(body: NextStepRequest):
    advance_step(body.run_id)
    return {"status": "advanced", "run_id": body.run_id}


# ---------------------------------------------------------------------------
# GET /simulator/replay/{run_id}
# ---------------------------------------------------------------------------

@router.get("/replay/{run_id}")
async def get_replay(run_id: str):
    snapshot = bus.get_snapshot(run_id)
    if snapshot is None:
        return {"error": "Run not found"}
    return {"run_id": run_id, "events": snapshot}


# ---------------------------------------------------------------------------
# GET /simulator/runs
# ---------------------------------------------------------------------------

@router.get("/runs")
async def list_runs():
    return {"runs": bus.list_runs()}
