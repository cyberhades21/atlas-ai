"""
Document ingestion pipeline.

FIX #12 — replace print() with logging:
    All progress output used raw `print()` calls.  In production (or when
    running behind uvicorn) print() output:
      - Is not captured by any log aggregator or handler
      - Cannot be filtered by log level (INFO vs DEBUG vs WARNING)
      - Cannot be silenced without redirecting stdout
      - Provides no timestamp, module name, or severity context

    Fix: replace every print() with logger.info() / logger.debug() using the
    module-level logger obtained via logging.getLogger(__name__).  The log
    level can now be controlled globally via logging configuration without
    touching this file.
"""

import logging

from app.utils.pdf_parser import extract_text
from app.ai.chunking import chunk_text
from app.ai.embeddings import embed_chunks
from app.storage.vector_store import store_embeddings
from app.ai.relationship_extractor import extract_relationships
from app.storage.graph_store import store_relationships
from app.ai.entity_extractor import extract_entities
from app.storage.entity_store import store_entities

logger = logging.getLogger(__name__)


async def ingest_document(filepath: str, filename: str):
    logger.info("Extracting text from %s", filename)
    text = extract_text(filepath)

    logger.info("Chunking document — %s chars", len(text))
    chunks = chunk_text(text)
    logger.info("Chunk count: %d", len(chunks))

    all_entities = []
    all_relationships = []

    logger.info("Extracting relationships from %d chunks", len(chunks))
    for i, chunk in enumerate(chunks):
        entities = extract_entities(chunk)
        triples = extract_relationships(chunk)
        logger.debug("Chunk %d — entities: %s  triples: %d", i, entities, len(triples))

        if entities:
            all_entities.extend(entities)
        if triples:
            all_relationships.extend(triples)

    logger.info("Generating embeddings")
    embeddings = embed_chunks(chunks)

    logger.info("Storing vectors")
    store_embeddings(chunks, embeddings, filename)

    logger.info("Storing %d entities", len(all_entities))
    store_entities(all_entities, filename)

    logger.info("Storing %d knowledge-graph triples", len(all_relationships))
    store_relationships(all_relationships, filename)

    logger.info("Indexing complete: %s", filename)
