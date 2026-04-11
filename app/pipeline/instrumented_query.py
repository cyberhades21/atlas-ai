"""
Instrumented RAG pipeline.

Wraps every stage of the core pipeline (defined in query_service.py) with
PipelineEvent emissions.  The original answer_query() is untouched; this adds
a parallel observation path.

FIX #4 — no more duplicate logic:
    Previously this file re-implemented every pipeline stage verbatim.  Now it
    imports the canonical stage functions from query_service and calls them
    directly.  All business logic lives in exactly one place.

FEATURE — top_k and temperature wired through:
    The simulator UI exposes top_k (1-10) and temperature (0-1) sliders.
    RunRequest now carries those values; they are forwarded to
    run_vector_retrieval() and generate_answer() respectively.

FEATURE — similarity scores in vector_retrieval payload:
    vector_store.search() now returns `_distance` inside each metadata dict
    (added in the vector_store fix).  The instrumented pipeline surfaces this
    as a `scores` list in the completed payload so the Node Inspector can show
    per-chunk relevance.
"""

import time
import threading
import logging
from typing import Any, Dict

from app.pipeline.events import bus, PipelineEvent
from app.ai.llm import generate_answer
from app.services.query_service import (
    run_entity_extraction,
    run_graph_search,
    run_embedding,
    run_vector_retrieval,
    run_context_builder,
    run_prompt_builder,
    DEFAULT_TOP_K,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Step-mode gates — one threading.Event per active run
# ---------------------------------------------------------------------------
step_gates: Dict[str, threading.Event] = {}
step_mode_runs: set = set()


def _emit(run_id: str, step: str, status: str, payload: dict = None, latency_ms: float = None):
    bus.emit(PipelineEvent(
        run_id=run_id,
        step=step,
        status=status,
        payload=payload or {},
        latency_ms=latency_ms,
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

def run_instrumented_pipeline(
    run_id: str,
    question: str,
    step_mode: bool = False,
    top_k: int = DEFAULT_TOP_K,
    temperature: float = 0.7,
):
    """
    Execute the full RAG pipeline, emitting events at each stage.
    Runs synchronously; call from a background thread.

    Parameters
    ----------
    top_k : number of vector chunks to retrieve (wired from UI slider)
    temperature : LLM sampling temperature (wired from UI slider)
    """
    if step_mode:
        step_mode_runs.add(run_id)
        step_gates[run_id] = threading.Event()
        step_gates[run_id].set()   # first step starts immediately

    try:
        # ----------------------------------------------------------------
        # STEP 0: query_received
        # ----------------------------------------------------------------
        _emit(run_id, "query_received", "completed", {
            "question": question,
            "char_count": len(question),
            "top_k": top_k,
            "temperature": temperature,
        })
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 1: entity_extraction
        # ----------------------------------------------------------------
        _emit(run_id, "entity_extraction", "started", {"question": question})
        t0 = time.time()
        entities = run_entity_extraction(question)
        latency = (time.time() - t0) * 1000
        _emit(run_id, "entity_extraction", "completed", {
            "entities": entities,
            "count": len(entities),
        }, latency_ms=latency)
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 2: graph_search
        # ----------------------------------------------------------------
        _emit(run_id, "graph_search", "started", {"entities": entities})
        t0 = time.time()
        graph_context, graph_triples = run_graph_search(entities)
        latency = (time.time() - t0) * 1000
        _emit(run_id, "graph_search", "completed", {
            "triples_found": len(graph_triples),
            "triples": graph_triples[:20],
            "graph_context_length": len(graph_context),
        }, latency_ms=latency)
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 3: embedding
        # ----------------------------------------------------------------
        _emit(run_id, "embedding", "started", {"text": question})
        t0 = time.time()
        query_embedding = run_embedding(question)
        latency = (time.time() - t0) * 1000
        _emit(run_id, "embedding", "completed", {
            "model": "nomic-embed-text",
            "dimensions": len(query_embedding),
            "vector_preview": query_embedding[:8],
        }, latency_ms=latency)
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 4: vector_retrieval  (top_k wired here)
        # ----------------------------------------------------------------
        _emit(run_id, "vector_retrieval", "started", {
            "top_k": top_k,
            "collection": "atlas",
        })
        t0 = time.time()
        chunks, metadata = run_vector_retrieval(query_embedding, n_results=top_k)
        latency = (time.time() - t0) * 1000

        retrieved_docs = []
        for i, (chunk, meta) in enumerate(zip(chunks, metadata)):
            retrieved_docs.append({
                "rank": i + 1,
                "document": meta.get("document", "unknown"),
                "text_preview": chunk[:300],
                "char_count": len(chunk),
                # _distance populated by vector_store.search() fix
                "score": round(1 - meta.get("_distance", 1), 4),
            })

        low_result = len(chunks) == 0
        _emit(run_id, "vector_retrieval", "completed", {
            "results_count": len(chunks),
            "retrieved_docs": retrieved_docs,
            "degraded": low_result,
        }, latency_ms=latency)

        if low_result:
            _emit(run_id, "vector_retrieval", "warning", {
                "message": "No chunks retrieved — knowledge base may be empty",
            })
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 5: context_builder
        # ----------------------------------------------------------------
        _emit(run_id, "context_builder", "started", {})
        t0 = time.time()
        context = run_context_builder(graph_context, chunks)
        latency = (time.time() - t0) * 1000
        _emit(run_id, "context_builder", "completed", {
            "graph_triples": len(graph_triples),
            "vector_chunks": len(chunks),
            "total_context_chars": len(context),
            "context_preview": context[:400],
        }, latency_ms=latency)
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 6: prompt_builder
        # ----------------------------------------------------------------
        _emit(run_id, "prompt_builder", "started", {})
        t0 = time.time()
        prompt = run_prompt_builder(context, question)
        latency = (time.time() - t0) * 1000
        approx_tokens = len(prompt) // 4
        _emit(run_id, "prompt_builder", "completed", {
            "prompt_length_chars": len(prompt),
            "approx_tokens": approx_tokens,
            "prompt_preview": prompt[:500],
        }, latency_ms=latency)
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 7: llm_generation  (temperature wired here)
        # ----------------------------------------------------------------
        _emit(run_id, "llm_generation", "started", {
            "model": "mistral",
            "approx_input_tokens": approx_tokens,
            "temperature": temperature,
        })
        t0 = time.time()
        answer = generate_answer(context, question, temperature=temperature)
        latency = (time.time() - t0) * 1000
        approx_output_tokens = len(answer) // 4
        _emit(run_id, "llm_generation", "completed", {
            "model": "mistral",
            "answer_preview": answer[:300],
            "answer_length_chars": len(answer),
            "approx_output_tokens": approx_output_tokens,
        }, latency_ms=latency)
        _wait_for_gate(run_id)

        # ----------------------------------------------------------------
        # STEP 8: response_assembly
        # ----------------------------------------------------------------
        sources = [
            {"document": metadata[i].get("document", "unknown"), "text": chunks[i][:300]}
            for i in range(len(chunks))
        ]
        _emit(run_id, "response_assembly", "completed", {
            "answer": answer,
            "sources_count": len(sources),
            "sources": sources,
        })

        _emit(run_id, "pipeline", "done", {"run_id": run_id})

    except TimeoutError as exc:
        _emit(run_id, "pipeline", "error", {"error": str(exc), "type": "timeout"})
        logger.error("Pipeline run %s timed out: %s", run_id, exc)

    except Exception as exc:
        _emit(run_id, "pipeline", "error", {"error": str(exc)})
        logger.exception("Pipeline run %s raised an exception", run_id)

    finally:
        if run_id in step_mode_runs:
            step_mode_runs.discard(run_id)
            gate = step_gates.pop(run_id, None)
            if gate:
                gate.set()
        bus.close_run(run_id)
