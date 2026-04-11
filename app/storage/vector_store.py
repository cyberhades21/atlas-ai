"""
Vector store backed by ChromaDB.

FIX #10 — lazy initialisation:
    Previously `chromadb.PersistentClient` and `collection` were created at
    module import time.  If `data/vector_db` did not exist (first run, fresh
    clone, CI) the import raised an exception and brought down the entire
    FastAPI app before a single request was served.

    Fix: wrap initialisation in `_get_collection()` which is called lazily on
    first use.  `pathlib.Path.mkdir(parents=True, exist_ok=True)` ensures the
    directory always exists before ChromaDB tries to open it.

FIX #3 — empty collection guard:
    ChromaDB raises `chromadb.errors.InvalidArgumentError` (and in some
    versions a plain `Exception`) when `n_results` is larger than the number
    of documents stored.  With an empty or near-empty knowledge base this
    caused every query to crash with a 500 error.

    Fix: clamp `n_results = min(n_results, collection.count())` before
    calling `collection.query()`.  When count is 0 we skip the query
    entirely and return empty lists.
"""

import os
from pathlib import Path
from typing import List, Tuple

import chromadb

_client = None
_collection = None
_DB_PATH = "data/vector_db"


def _get_collection():
    """Return the ChromaDB collection, initialising lazily on first call."""
    global _client, _collection
    if _collection is None:
        Path(_DB_PATH).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=_DB_PATH)
        _collection = _client.get_or_create_collection("atlas")
    return _collection


def store_embeddings(chunks: List[str], embeddings: List, filename: str):
    col = _get_collection()
    ids = [f"{filename}_{i}" for i in range(len(chunks))]
    metadatas = [{"document": filename} for _ in chunks]
    col.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def search(query_embedding, n_results: int = 5) -> Tuple[List[str], List[dict]]:
    col = _get_collection()

    total = col.count()
    if total == 0:
        return [], []

    safe_n = min(n_results, total)

    results = col.query(
        query_embeddings=[query_embedding],
        n_results=safe_n,
        include=["documents", "metadatas", "distances"],
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    # Attach distance score to each metadata entry so callers can use it
    for meta, dist in zip(metas, distances):
        meta["_distance"] = round(dist, 6)

    return docs, metas
