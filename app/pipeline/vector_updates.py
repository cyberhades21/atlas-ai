"""
Vector embedding update broadcast bus.

When store_embeddings() saves new chunks it calls vector_update_bus.emit()
with the list of new 2D-projected points. Any connected SSE client
(vectors.html) receives the event and merges the new points into the live
scatter plot without a page reload.

Mirrors the pattern in graph_updates.py exactly.
"""

import asyncio
import threading
from typing import List, Dict


class VectorUpdateBus:
    def __init__(self):
        self._clients: set = set()
        self._lock = threading.Lock()

    def subscribe(self, loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
        """Register a new SSE client and return its queue."""
        q = asyncio.Queue()
        with self._lock:
            self._clients.add((q, loop))
        return q

    def unsubscribe(self, q: asyncio.Queue):
        """Remove a client queue when its SSE connection closes."""
        with self._lock:
            self._clients = {(cq, cl) for cq, cl in self._clients if cq is not q}

    def emit(self, points: List[Dict]):
        """
        Broadcast new 2D-projected points to all connected clients.
        Called from store_embeddings() (sync thread).
        points: list of {"id": str, "x": float, "y": float, "text": str, "document": str}
        """
        if not points:
            return
        with self._lock:
            clients = list(self._clients)
        for q, loop in clients:
            try:
                asyncio.run_coroutine_threadsafe(q.put(points), loop)
            except Exception:
                pass


vector_update_bus = VectorUpdateBus()
