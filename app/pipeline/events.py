"""
Pipeline event schema and emitter.
Each pipeline stage emits structured PipelineEvent objects.
The EventBus holds per-run queues that the SSE endpoint drains.
"""

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import asyncio
import threading


# ---------------------------------------------------------------------------
# Event data class
# ---------------------------------------------------------------------------

@dataclass
class PipelineEvent:
    run_id: str
    step: str                        # e.g. "embedding", "retrieval"
    status: str                      # "started" | "completed" | "error" | "info"
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    latency_ms: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Event bus
# ---------------------------------------------------------------------------

class EventBus:
    """
    Thread-safe event bus.
    Each run_id maps to an asyncio.Queue that the SSE handler reads.
    The query service writes events from a sync thread via put_nowait.
    """

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._lock = threading.Lock()
        # Snapshot store: run_id -> list[PipelineEvent]
        self._snapshots: Dict[str, list] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def create_run(self, run_id: str, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
        """Register a new run and return its queue."""
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._queues[run_id] = q
            self._snapshots[run_id] = []
            self._loop = loop
        return q

    def get_queue(self, run_id: str) -> Optional[asyncio.Queue]:
        with self._lock:
            return self._queues.get(run_id)

    def close_run(self, run_id: str):
        """Signal the SSE stream that this run is done by enqueuing None."""
        with self._lock:
            q = self._queues.get(run_id)
        if q:
            try:
                asyncio.run_coroutine_threadsafe(q.put(None), self._loop).result(timeout=2)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Emitting
    # ------------------------------------------------------------------

    def emit(self, event: PipelineEvent):
        """Emit an event from any thread (sync or async)."""
        with self._lock:
            snapshot = self._snapshots.get(event.run_id)
            if snapshot is not None:
                snapshot.append(event.to_dict())
            q = self._queues.get(event.run_id)
            loop = getattr(self, "_loop", None)

        if q and loop:
            asyncio.run_coroutine_threadsafe(q.put(event.to_dict()), loop)

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def get_snapshot(self, run_id: str) -> Optional[list]:
        with self._lock:
            return self._snapshots.get(run_id)

    def list_runs(self) -> list:
        with self._lock:
            return list(self._snapshots.keys())


# Module-level singleton
bus = EventBus()
