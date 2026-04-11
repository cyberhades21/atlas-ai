"""
Graph update broadcast bus.

When store_relationships() saves new triples it calls graph_update_bus.emit()
with the list of new triples.  Any connected SSE client (graph.html) receives
the event and merges the new nodes/edges into the live Cytoscape instance
without a page reload.
"""

import asyncio
import json
import threading
from typing import List, Dict, Set


class GraphUpdateBus:
    def __init__(self):
        # Set of (asyncio.Queue, asyncio.AbstractEventLoop) — one per connected client
        self._clients: Set = set()
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

    def emit(self, triples: List[Dict]):
        """
        Broadcast new triples to all connected clients.
        Called from store_relationships() (sync thread).
        triples: list of {"entity1": str, "relation": str, "entity2": str}
        """
        if not triples:
            return

        # Build Cytoscape-compatible payload
        new_nodes: Set[str] = set()
        new_edges = []
        for t in triples:
            e1 = t.get("entity1", "")
            e2 = t.get("entity2", "")
            rel = t.get("relation", "")
            if not e1 or not e2:
                continue
            new_nodes.add(e1)
            new_nodes.add(e2)
            new_edges.append({"data": {"source": e1, "target": e2, "label": rel}})

        payload = {
            "nodes": [{"data": {"id": n}} for n in new_nodes],
            "edges": new_edges,
        }

        with self._lock:
            clients = list(self._clients)

        for q, loop in clients:
            try:
                asyncio.run_coroutine_threadsafe(q.put(payload), loop)
            except Exception:
                pass


graph_update_bus = GraphUpdateBus()
