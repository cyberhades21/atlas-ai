"""
Instrumented RAG pipeline.
Wraps every stage of query_service with PipelineEvent emissions.
The original answer_query() is untouched; this adds a parallel path.
"""

import time
import threading
from typing import Any, Dict, Optional

from app.pipeline.events import bus, PipelineEvent
from app.ai.embeddings import embed_query
from app.storage.vector_store import search
from app.ai.llm import generate_answer
from app.ai.entity_extractor import extract_entities
from app.storage.graph_store import search_relationships


# ---------------------------------------------------------------------------
# Step mode: an Event a thread waits on between steps.
# step_gates[run_id] = threading.Event()
# ---------------------------------------------------------------------------
step_gates: Dict[str, threading.Event] = {}
step_mode_runs: set = set()


def _emit(run_id: str, step: str, status: str, payload: dict = None, latency_ms: float = None):
    bus.emit(PipelineEvent(
        run_id=run_id,
        step=step,
        status=status,
        payload=payload or {},
        latency_ms=latency_ms
    ))


def _wait_for_gate(run_id: str):
    """If run is in step mode, block until the frontend sends 'next step'."""
    if run_id in step_mode_runs:
        gate = step_gates.get(run_id)
        if gate:
            gate.clear()
            _emit(run_id, "step_mode", "waiting", {"message": "Waiting for next-step trigger"})
            gate.wait()


def advance_step(run_id: str):
    """Called by the /simulator/next-step endpoint."""
    gate = step_gates.get(run_id)
    if gate:
        gate.set()


# ---------------------------------------------------------------------------
# Main instrumented pipeline
# ---------------------------------------------------------------------------

def run_instrumented_pipeline(run_id: str, question: str, step_mode: bool = False):
    """
    Execute the full RAG pipeline, emitting events at each stage.
    Runs synchronously; call from a background thread.
    """
    if step_mode:
        step_mode_runs.add(run_id)
        step_gates[run_id] = threading.Event()
        step_gates[run_id].set()   # first step starts immediately

    result = {}

    try:
        # ----------------------------------------------------------------
        # STEP 0: query_received
        # ----------------------------------------------------------------
        _emit(run_id, "query_received", "completed", {
            "question": question,
            "char_count": len(question)
        })

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 1: entity_extraction
        # ----------------------------------------------------------------
        _emit(run_id, "entity_extraction", "started", {"question": question})
        t0 = time.time()
        entities = extract_entities(question)
        latency = (time.time() - t0) * 1000
        _emit(run_id, "entity_extraction", "completed", {
            "entities": entities,
            "count": len(entities)
        }, latency_ms=latency)

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 2: graph_search
        # ----------------------------------------------------------------
        _emit(run_id, "graph_search", "started", {"entities": entities})
        t0 = time.time()
        graph_context = ""
        graph_triples = []
        for entity in entities:
            relations = search_relationships(entity)
            for a, r, b in relations:
                graph_context += f"{a} {r} {b}\n"
                graph_triples.append({"entity1": a, "relation": r, "entity2": b})
        latency = (time.time() - t0) * 1000
        _emit(run_id, "graph_search", "completed", {
            "triples_found": len(graph_triples),
            "triples": graph_triples[:20],   # cap payload
            "graph_context_length": len(graph_context)
        }, latency_ms=latency)

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 3: embedding
        # ----------------------------------------------------------------
        _emit(run_id, "embedding", "started", {"text": question})
        t0 = time.time()
        query_embedding = embed_query(question)
        latency = (time.time() - t0) * 1000
        _emit(run_id, "embedding", "completed", {
            "model": "nomic-embed-text",
            "dimensions": len(query_embedding),
            "vector_preview": query_embedding[:8]   # first 8 dims only
        }, latency_ms=latency)

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 4: vector_retrieval
        # ----------------------------------------------------------------
        _emit(run_id, "vector_retrieval", "started", {
            "top_k": 5,
            "collection": "atlas"
        })
        t0 = time.time()
        chunks, metadata = search(query_embedding)
        latency = (time.time() - t0) * 1000

        # Build rich payload
        retrieved_docs = []
        for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
            retrieved_docs.append({
                "rank": i + 1,
                "document": meta.get("document", "unknown"),
                "text_preview": chunk[:300],
                "char_count": len(chunk)
            })

        low_score = len(chunks) == 0
        _emit(run_id, "vector_retrieval", "completed", {
            "results_count": len(chunks),
            "retrieved_docs": retrieved_docs,
            "degraded": low_score
        }, latency_ms=latency)

        if low_score:
            _emit(run_id, "vector_retrieval", "warning", {
                "message": "No chunks retrieved — knowledge base may be empty"
            })

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 5: context_builder
        # ----------------------------------------------------------------
        _emit(run_id, "context_builder", "started", {})
        t0 = time.time()
        vector_context = "\n\n".join(chunks)
        context = graph_context + "\n\n" + vector_context
        latency = (time.time() - t0) * 1000
        _emit(run_id, "context_builder", "completed", {
            "graph_triples": len(graph_triples),
            "vector_chunks": len(chunks),
            "total_context_chars": len(context),
            "context_preview": context[:400]
        }, latency_ms=latency)

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 6: prompt_builder
        # ----------------------------------------------------------------
        _emit(run_id, "prompt_builder", "started", {})
        t0 = time.time()
        prompt = f"""Answer using ONLY the context below.\n\nIf the answer is not found, say "Not found in documents".\n\nContext:\n{context}\n\nQuestion:\n{question}"""
        latency = (time.time() - t0) * 1000
        # Approx token count: ~4 chars per token
        approx_tokens = len(prompt) // 4
        _emit(run_id, "prompt_builder", "completed", {
            "prompt_length_chars": len(prompt),
            "approx_tokens": approx_tokens,
            "prompt_preview": prompt[:500]
        }, latency_ms=latency)

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 7: llm_generation
        # ----------------------------------------------------------------
        _emit(run_id, "llm_generation", "started", {
            "model": "mistral",
            "approx_input_tokens": approx_tokens
        })
        t0 = time.time()
        answer = generate_answer(context, question)
        latency = (time.time() - t0) * 1000
        approx_output_tokens = len(answer) // 4
        _emit(run_id, "llm_generation", "completed", {
            "model": "mistral",
            "answer_preview": answer[:300],
            "answer_length_chars": len(answer),
            "approx_output_tokens": approx_output_tokens
        }, latency_ms=latency)

        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 8: response_assembly
        # ----------------------------------------------------------------
        sources = [
            {"document": metadata[i]["document"], "text": chunks[i][:300]}
            for i in range(len(chunks))
        ]
        result = {
            "answer": answer,
            "entities": entities,
            "graph_context": graph_context,
            "sources": sources
        }
        _emit(run_id, "response_assembly", "completed", {
            "answer": answer,
            "sources_count": len(sources),
            "sources": sources
        })

        # ----------------------------------------------------------------
        # Pipeline done
        # ----------------------------------------------------------------
        _emit(run_id, "pipeline", "done", {"run_id": run_id})

    except Exception as exc:
        _emit(run_id, "pipeline", "error", {"error": str(exc)})

    finally:
        # Unblock any waiting gate and signal SSE stream to close
        if run_id in step_mode_runs:
            step_mode_runs.discard(run_id)
            gate = step_gates.pop(run_id, None)
            if gate:
                gate.set()
        bus.close_run(run_id)

    return result
