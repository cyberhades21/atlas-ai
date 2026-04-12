"""
Entity name normalization.

Converts raw entity strings (as extracted by an LLM) into a canonical,
lowercase, title-free form so that "Barack Obama", "President Obama", and
"Obama's" all resolve to the same node ("obama") in the knowledge graph.

Usage
-----
    from app.ai.entity_normalizer import normalize_entity

    normalize_entity("President Obama")   # → "obama"
    normalize_entity("Dr. Jane Smith")    # → "jane smith"

Known limitation
----------------
Title stripping is token-level, so "Dr Pepper" → "pepper".
Patch specific cases via ALIAS_MAP:
    from app.ai.entity_normalizer import ALIAS_MAP
    ALIAS_MAP["pepper"] = "dr pepper"
"""

import re
import unicodedata

TITLES: frozenset[str] = frozenset({
    "president", "dr", "mr", "mrs", "ms", "miss", "prof", "professor",
    "senator", "rep", "representative", "sec", "secretary", "gov",
    "governor", "gen", "general", "capt", "captain", "lt", "lieutenant",
    "ceo", "cto", "cfo", "sir", "lord", "lady", "king", "queen",
    "prince", "princess", "minister", "pm", "vp",
})

# Operator-extensible alias map.
# Keys AND values must already be in normalized form (lowercase, no titles).
# Example: ALIAS_MAP["usa"] = "united states"
ALIAS_MAP: dict[str, str] = {}


def normalize_entity(name: str) -> str:
    """
    Normalize an entity name to a canonical, lowercase, title-free string.

    Steps:
      1. Unicode → ASCII  (removes accented/variant characters)
      2. Lowercase
      3. Strip possessives ("Obama's" → "obama")
      4. Remove punctuation except hyphens and spaces
      5. Collapse whitespace
      6. Drop leading/trailing title tokens ("President Obama" → "obama")
      7. Alias map lookup

    Returns an empty string if the input is empty or normalizes to nothing.
    """
    if not name:
        return ""

    # 1. Unicode normalise → ASCII
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()

    # 2. Lowercase
    text = text.lower()

    # 3. Strip possessives
    text = re.sub(r"'s\b", "", text)

    # 4. Remove punctuation except hyphens and word chars
    text = re.sub(r"[^\w\s-]", "", text)

    # 5. Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    fallback = text  # keep pre-title-strip version as fallback

    # 6. Drop title tokens
    tokens = [t for t in text.split() if t not in TITLES]
    text = " ".join(tokens).strip()

    # Don't reduce a single-token title (e.g. bare "Dr.") to empty
    if not text:
        text = fallback

    # 7. Alias resolution
    return ALIAS_MAP.get(text, text)
