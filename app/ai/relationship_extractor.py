from app.ai.llm import call_llm_json

PROMPT = """
Extract knowledge relationships from the following technical text.

Return a JSON array of triples in this format:

[
  {"entity1": "...", "relation": "...", "entity2": "..."}
]

Text:
"""


def extract_relationships(text):

    try:
        triples = call_llm_json(PROMPT + text)
        return triples
    except Exception:
        return []