from app.ai.llm import call_llm_json

PROMPT = """
Extract key entities from the text.

Return JSON array:

["entity1","entity2","entity3"]

Text:
"""


def extract_entities(text):

    try:
        return call_llm_json(PROMPT + text)
    except:
        return []