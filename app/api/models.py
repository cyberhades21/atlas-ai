"""
GET /models — list Ollama models suitable for chat/generation.

Queries the local Ollama daemon and returns every model that is NOT
an embedding-only model (nomic-embed-text, mxbai-embed, all-minilm, etc.).
The frontend uses this list to populate the model-picker dropdown.
"""

import logging
from fastapi import APIRouter
import ollama

logger = logging.getLogger(__name__)

router = APIRouter()

# Substrings that identify embedding-only models — exclude them from the list
_EMBED_PATTERNS = (
    "embed",
    "minilm",
    "bge-",
    "e5-",
    "instructor",
)


def _is_embed_model(name: str) -> bool:
    lower = name.lower()
    return any(p in lower for p in _EMBED_PATTERNS)


@router.get("/models")
def list_models():
    """
    Return a list of chat-capable Ollama models installed locally.
    Falls back to ["mistral"] if Ollama is unreachable.
    """
    try:
        raw = ollama.list()
        # ollama.list() returns an object with a .models attribute (list of Model objects)
        models_raw = getattr(raw, "models", None) or raw.get("models", [])
        names = []
        for m in models_raw:
            # Model objects expose .model (full tag) or .name
            name = getattr(m, "model", None) or getattr(m, "name", None) or str(m)
            if name and not _is_embed_model(name):
                names.append(name)
        if not names:
            names = ["mistral"]
        return {"models": names}
    except Exception as exc:
        logger.warning("Could not reach Ollama to list models: %s", exc)
        return {"models": ["mistral"]}
