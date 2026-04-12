import logging
from app.ai.llm import call_llm_json

logger = logging.getLogger(__name__)

PROMPT = """Extract knowledge-graph relationships from the text below.

Rules:
- Return ONLY a JSON array of triple objects, nothing else.
- Use canonical entity names: no titles, honorifics, or possessives.
  WRONG: {"entity1": "President Obama", "relation": "signed", "entity2": "ACA"}
  RIGHT: {"entity1": "barack obama", "relation": "signed", "entity2": "affordable care act"}
- Use lowercase for all entity names and relations.
- Keep relation concise (1-3 words): "founded", "works at", "located in", "part of".
- If no relationships are found, return [].

Format:
[{"entity1": "...", "relation": "...", "entity2": "..."}]

Text:
"""


def extract_relationships(text):

    try:
        triples = call_llm_json(PROMPT + text)
        return triples
    except Exception as exc:
        logger.warning("Relationship extraction failed: %s", exc)
        return []