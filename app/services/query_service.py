"""
Core RAG pipeline logic.

FIX #4 — single source of truth:
    Previously `instrumented_query.py` contained a near-verbatim copy of the
    pipeline defined here.  Any change to the prompt, top_k default, model
    name, or context-merging strategy had to be applied in two places; it was
    inevitable that they would diverge.

    Fix: each pipeline stage is now a standalone function exported from this
    module.  `answer_query()` composes them for the plain /query endpoint.
    `instrumented_query.py` imports and calls the same functions so there is
    exactly one implementation of the logic.

Stage functions
---------------
run_entity_extraction(question)  -> list[str]
run_graph_search(entities)       -> (str, list[dict])
run_embedding(question)          -> list[float]
run_vector_retrieval(embedding, n_results) -> (list[str], list[dict])
run_context_builder(graph_ctx, chunks)     -> str
run_prompt_builder(context, question)      -> str
"""

import logging

from app.ai.embeddings import embed_query
from app.storage.vector_store import search
from app.ai.llm import generate_answer, DEFAULT_MODEL
from app.ai.entity_extractor import extract_entities
from app.storage.graph_store import search_relationships, search_relationships_nhop

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


# ---------------------------------------------------------------------------
# Individual stage functions — imported by instrumented_query.py
# ---------------------------------------------------------------------------

def run_entity_extraction(question: str) -> list:
    return extract_entities(question)


def run_graph_search(entities: list) -> tuple:
    """Returns (graph_context_str, list_of_triple_dicts).

    Uses 2-hop BFS via search_relationships_nhop() so connected context
    (neighbors of neighbors) is gathered in a single batched traversal.
    """
    graph_context = ""
    graph_triples = []
    if not entities:
        return graph_context, graph_triples

    for a, r, b in search_relationships_nhop(entities, hops=2):
        graph_context += f"{a} {r} {b}\n"
        graph_triples.append({"entity1": a, "relation": r, "entity2": b})
    return graph_context, graph_triples


def run_embedding(question: str) -> list:
    return embed_query(question)


def run_vector_retrieval(embedding: list, n_results: int = DEFAULT_TOP_K) -> tuple:
    """Returns (chunks, metadatas).  metadatas include _distance key."""
    return search(embedding, n_results=n_results)


def run_context_builder(graph_context: str, chunks: list) -> str:
    vector_context = "\n\n".join(chunks)
    return graph_context + "\n\n" + vector_context


def run_prompt_builder(context: str, question: str) -> str:
    return (
        "Answer using ONLY the context below.\n\n"
        'If the answer is not found, say "Not found in documents".\n\n'
        f"Context:\n{context}\n\nQuestion:\n{question}"
    )


# ---------------------------------------------------------------------------
# Composed pipeline — used by the plain /query endpoint
# ---------------------------------------------------------------------------

def answer_query(
    question: str,
    top_k: int = DEFAULT_TOP_K,
    model: str = DEFAULT_MODEL,
) -> dict:
    entities = run_entity_extraction(question)
    graph_context, _ = run_graph_search(entities)
    embedding = run_embedding(question)
    chunks, metadata = run_vector_retrieval(embedding, n_results=top_k)
    context = run_context_builder(graph_context, chunks)
    answer = generate_answer(context, question, model=model)

    sources = [
        {"document": meta["document"], "text": chunk[:300]}
        for chunk, meta in zip(chunks, metadata)
    ]

    return {
        "answer": answer,
        "entities": entities,
        "graph_context": graph_context,
        "sources": sources,
        "model": model,
    }
