"""
Document ingestion pipeline with real-time progress events.

Each stage calls ingest_bus.emit() so the SSE endpoint can stream actual
progress percentages to the browser instead of a fake CSS animation.
"""

import logging
from typing import Optional

from app.utils.pdf_parser import extract_text
from app.ai.chunking import chunk_text
from app.ai.embeddings import embed_chunks
from app.storage.vector_store import store_embeddings
from app.ai.relationship_extractor import extract_relationships
from app.storage.graph_store import store_relationships
from app.ai.entity_extractor import extract_entities
from app.storage.entity_store import store_entities
from app.pipeline.ingest_progress import ingest_bus

logger = logging.getLogger(__name__)


async def ingest_document(filepath: str, filename: str, task_id: Optional[str] = None):
    """
    Run the full ingestion pipeline.
    If task_id is provided, progress events are emitted to ingest_bus so the
    browser can track real stage-by-stage progress over SSE.
    """

    def progress(stage: str, detail: str = "", chunk_idx: int = 0, total_chunks: int = 0):
        if task_id:
            ingest_bus.emit(task_id, stage, detail, chunk_idx, total_chunks)
        logger.info("[%s] %s %s", stage, detail, f"({chunk_idx}/{total_chunks})" if total_chunks else "")

    try:
        # ── Stage 1: extract text
        progress("extract_text", f"Reading {filename}")
        text = extract_text(filepath)

        # ── Stage 2: chunk
        progress("chunk", f"{len(text):,} chars")
        chunks = chunk_text(text)
        total = len(chunks)
        logger.info("Chunk count: %d", total)

        # ── Stage 3: extract relationships (one LLM call per chunk — slowest)
        all_entities = []
        all_relationships = []

        for i, chunk in enumerate(chunks):
            progress("extract_relations", f"Chunk {i+1}/{total}", chunk_idx=i+1, total_chunks=total)
            entities = extract_entities(chunk)
            triples  = extract_relationships(chunk)
            logger.debug("Chunk %d — entities: %s  triples: %d", i, entities, len(triples))

            if entities:
                all_entities.extend(entities)
            if triples:
                all_relationships.extend(triples)

        # ── Stage 4: embed
        progress("embed", f"Embedding {total} chunks")
        embeddings = embed_chunks(chunks)

        # ── Stage 5: store vectors
        progress("store_vectors", f"{total} chunks")
        store_embeddings(chunks, embeddings, filename)

        # ── Stage 6: store entities
        progress("store_entities", f"{len(all_entities)} entities")
        store_entities(all_entities, filename)

        # ── Stage 7: store graph
        progress("store_graph", f"{len(all_relationships)} triples")
        store_relationships(all_relationships, filename)

        # ── Done
        progress("done", filename)
        logger.info("Indexing complete: %s", filename)

    finally:
        if task_id:
            ingest_bus.close_task(task_id)
