"""
Pipeline event schema and emitter.
Each pipeline stage emits structured PipelineEvent objects.
The EventBus holds per-run queues that the SSE endpoint drains.
"""

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, Tuple
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
    The query service writes events from a sync thread via run_coroutine_threadsafe.

    FIX #1 — per-run loop storage:
        Previously `self._loop` was a single field overwritten on every
        create_run() call.  Under concurrent runs, the second caller would
        overwrite the loop reference used by the first run's emit(), causing
        events for run-1 to be dispatched onto run-2's event loop — resulting
        in either silent drops or a RuntimeError on the wrong loop.

        Fix: store (queue, loop) together in `self._runs[run_id]` so each run
        always uses the loop that was current when it was registered.
    """

    def __init__(self):
        # run_id -> (asyncio.Queue, asyncio.AbstractEventLoop)
        self._runs: Dict[str, Tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = {}
        self._lock = threading.Lock()
        # Snapshot store: run_id -> list[dict]
        self._snapshots: Dict[str, list] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def create_run(self, run_id: str, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
        """Register a new run and return its queue."""
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._runs[run_id] = (q, loop)
            self._snapshots[run_id] = []
        return q

    def get_queue(self, run_id: str) -> Optional[asyncio.Queue]:
        with self._lock:
            entry = self._runs.get(run_id)
            return entry[0] if entry else None

    def close_run(self, run_id: str):
        """Signal the SSE stream that this run is done by enqueuing None."""
        with self._lock:
            entry = self._runs.get(run_id)
        if entry:
            q, loop = entry
            try:
                asyncio.run_coroutine_threadsafe(q.put(None), loop).result(timeout=2)
            except Exception:
                pass
            # Remove from active runs (snapshot stays for replay)
            with self._lock:
                self._runs.pop(run_id, None)

    # ------------------------------------------------------------------
    # Emitting
    # ------------------------------------------------------------------

    def emit(self, event: PipelineEvent):
        """Emit an event from any thread (sync or async)."""
        with self._lock:
            snapshot = self._snapshots.get(event.run_id)
            if snapshot is not None:
                snapshot.append(event.to_dict())
            entry = self._runs.get(event.run_id)

        if entry:
            q, loop = entry
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
