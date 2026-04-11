"""
LLM wrappers around Ollama.

FIX #9 — generate_answer timeout:
    `ollama.chat()` is a blocking synchronous call with no built-in timeout.
    If Ollama is slow or hangs (e.g. model not loaded, GPU contention), the
    calling thread blocks indefinitely.  In the simulator this holds the SSE
    connection open forever — the browser spinner never stops and the run_id
    queue is never closed, leaking memory in the EventBus.

    Fix: run the Ollama call in a `concurrent.futures.ThreadPoolExecutor`
    and apply `future.result(timeout=LLM_TIMEOUT_SECONDS)`.  On timeout a
    `TimeoutError` is raised, which the caller (instrumented_query.py) catches
    and emits as a pipeline "error" event, closing the stream cleanly.

    LLM_TIMEOUT_SECONDS defaults to 120 s (2 min).  It can be overridden via
    the LLM_TIMEOUT env var.
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

import ollama

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT", "120"))

# Single shared executor — limits total concurrent Ollama calls to 4
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ollama")


def _chat(model: str, messages: list) -> str:
    """Blocking Ollama call — run inside executor for timeout support."""
    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


DEFAULT_MODEL = os.getenv("ATLAS_MODEL", "mistral")


def generate_answer(
    context: str,
    question: str,
    temperature: float = 0.7,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Generate an answer from the LLM.

    Raises TimeoutError if Ollama does not respond within LLM_TIMEOUT_SECONDS.
    """
    prompt = (
        "Answer using ONLY the context below.\n\n"
        'If the answer is not found, say "Not found in documents".\n\n'
        f"Context:\n{context}\n\nQuestion:\n{question}"
    )
    messages = [{"role": "user", "content": prompt}]
    future = _executor.submit(_chat, model, messages)
    try:
        return future.result(timeout=LLM_TIMEOUT_SECONDS)
    except FuturesTimeout:
        future.cancel()
        logger.error("generate_answer timed out after %s s (model=%s)", LLM_TIMEOUT_SECONDS, model)
        raise TimeoutError(
            f"LLM did not respond within {LLM_TIMEOUT_SECONDS} seconds"
        )


def call_llm_json(prompt: str, model: str = DEFAULT_MODEL) -> list:
    """
    Call the LLM and parse the response as JSON.
    Returns an empty list on parse failure or timeout.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a system that extracts structured data and returns ONLY valid JSON.",
        },
        {"role": "user", "content": prompt},
    ]
    future = _executor.submit(_chat, model, messages)
    try:
        content = future.result(timeout=LLM_TIMEOUT_SECONDS)
    except FuturesTimeout:
        future.cancel()
        logger.warning("call_llm_json timed out after %s s (model=%s)", LLM_TIMEOUT_SECONDS, model)
        return []

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return []
