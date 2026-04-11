"""
Ingestion progress bus.

Each upload gets a task_id.  The ingestion service calls emit() at each
stage; the SSE endpoint drains the queue and forwards events to the browser.

Race-condition fix
------------------
The ingestion coroutine can complete (and call close_task) before the browser
has opened the SSE connection, because:
  - asyncio.create_task() schedules the coroutine on the same event loop
  - the PDF extraction + chunking can finish in < 1 s for small files
  - the browser only opens EventSource after receiving the fetch() response

Solution: close_task() no longer deletes the entry.  It marks the task as
done and enqueues the None sentinel.  The SSE endpoint is responsible for
cleanup via cleanup_task() once the stream closes.  A late-connecting client
that calls get_queue() on an already-done task receives a pre-built queue
that already contains the sentinel, so it still gets the final "done" event.

Stages and their weights (must sum to 100):
  extract_text        5 %
  chunk               5 %
  extract_relations  50 %   (slowest — one LLM call per chunk)
  embed              20 %
  store_vectors       5 %
  store_entities      5 %
  store_graph         5 %
  done                5 %
"""

import asyncio
import threading
import time
from typing import Dict, Optional, Tuple


STAGES = [
    ("extract_text",       "Extracting text",           5),
    ("chunk",              "Chunking document",          5),
    ("extract_relations",  "Extracting relationships",  50),
    ("embed",              "Generating embeddings",     20),
    ("store_vectors",      "Storing vectors",            5),
    ("store_entities",     "Storing entities",           5),
    ("store_graph",        "Storing knowledge graph",    5),
    ("done",               "Complete",                   5),
]

# Cumulative progress at the START of each stage
_STAGE_START: Dict[str, int] = {}
_cumulative = 0
for _sid, _slabel, _weight in STAGES:
    _STAGE_START[_sid] = _cumulative
    _cumulative += _weight


class IngestProgressBus:
    def __init__(self):
        # task_id -> (asyncio.Queue, asyncio.AbstractEventLoop, is_done: bool)
        self._tasks: Dict[str, Tuple[asyncio.Queue, asyncio.AbstractEventLoop, bool]] = {}
        self._lock = threading.Lock()

    def create_task(self, task_id: str, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._tasks[task_id] = (q, loop, False)
        return q

    def get_queue(self, task_id: str) -> Optional[asyncio.Queue]:
        """
        Returns the queue for task_id, or None if unknown.
        Safe to call before or after the ingestion completes.
        """
        with self._lock:
            entry = self._tasks.get(task_id)
            return entry[0] if entry else None

    def emit(self, task_id: str, stage: str, detail: str = "", chunk_idx: int = 0, total_chunks: int = 0):
        """Emit a progress event from any thread."""
        stage_start = _STAGE_START.get(stage, 0)

        if stage == "extract_relations" and total_chunks > 0:
            _, _, weight = STAGES[2]
            within = (chunk_idx / total_chunks) * weight
            pct = stage_start + int(within)
        else:
            pct = stage_start

        event = {
            "stage": stage,
            "detail": detail,
            "pct": pct,
            "chunk_idx": chunk_idx,
            "total_chunks": total_chunks,
            "ts": time.time(),
        }
        with self._lock:
            entry = self._tasks.get(task_id)
        if entry:
            q, loop, _ = entry
            asyncio.run_coroutine_threadsafe(q.put(event), loop)

    def close_task(self, task_id: str):
        """
        Signal completion by enqueuing the None sentinel and marking the task
        as done.  Does NOT delete the entry — the SSE consumer calls
        cleanup_task() when it has finished reading.
        """
        with self._lock:
            entry = self._tasks.get(task_id)
            if entry:
                q, loop, _ = entry
                self._tasks[task_id] = (q, loop, True)   # mark done
        if entry:
            asyncio.run_coroutine_threadsafe(q.put(None), loop)

    def cleanup_task(self, task_id: str):
        """Remove the task entry once the SSE stream has closed."""
        with self._lock:
            self._tasks.pop(task_id, None)

    def is_done(self, task_id: str) -> bool:
        with self._lock:
            entry = self._tasks.get(task_id)
            return entry[2] if entry else False


ingest_bus = IngestProgressBus()
