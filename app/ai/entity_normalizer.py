"""
Entity name and relation normalization.

normalize_entity()   — collapses entity name variants to a canonical lowercase,
                       title-free form: "President Obama" → "obama"

normalize_relation() — normalizes a relation string using pure linguistic
                       transformations powered by nltk's WordNet lemmatizer:
                       "is believed to be rival of" → "rival of"
                       "believed_to_fear"           → "fear"
                       "plotted against"            → "plot against"
                       "may be associated with"     → "associate with"

Both functions are applied at write time in graph_store.py and entity_store.py
so the graph always contains clean, deduplicated nodes and edges regardless of
what the LLM returns or what corpus is being indexed.

Dependencies
------------
nltk (pip install nltk) — used only for WordNetLemmatizer in normalize_relation.
On first run the WordNet corpus is auto-downloaded to ~/nltk_data (~10 MB).
No other NLTK components are required.
"""

import re
import unicodedata
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# nltk lazy-load — download WordNet data silently on first use
# ---------------------------------------------------------------------------

_lemmatizer = None


def _get_lemmatizer():
    global _lemmatizer
    if _lemmatizer is not None:
        return _lemmatizer
    try:
        import nltk
        from nltk.stem import WordNetLemmatizer
        # Download required corpora silently if not already present
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
        _lemmatizer = WordNetLemmatizer()
    except Exception as exc:
        logger.warning("nltk unavailable — verb lemmatization disabled: %s", exc)
        _lemmatizer = None
    return _lemmatizer


# ---------------------------------------------------------------------------
# Entity normalization
# ---------------------------------------------------------------------------

TITLES: frozenset[str] = frozenset({
    "president", "dr", "mr", "mrs", "ms", "miss", "prof", "professor",
    "senator", "sen", "rep", "representative", "sec", "secretary", "gov",
    "governor", "gen", "general", "capt", "captain", "lt", "lieutenant",
    "ceo", "cto", "cfo", "sir", "lord", "lady", "king", "queen",
    "prince", "princess", "minister", "pm", "vp",
})

# Corpus-agnostic alias map — empty by default.
# Add entries when the same real-world entity appears under genuinely different
# surface forms that cannot be caught by title-stripping alone
# (e.g. acronyms, abbreviations, alternate spellings).
# Keys AND values must already be in normalized form (lowercase, no titles).
# Example: ALIAS_MAP["usa"] = "united states"
ALIAS_MAP: dict[str, str] = {}


def normalize_entity(name: str) -> str:
    """
    Normalize an entity name to a canonical, lowercase, title-free string.

    Steps:
      1. Unicode → ASCII  (removes accented/variant characters)
      2. Lowercase
      3. Strip possessives  ("Obama's" → "obama")
      4. Underscores → spaces; strip remaining punctuation except hyphens
      5. Collapse whitespace
      6. Drop honorific/title tokens  ("President Obama" → "obama")
      7. ALIAS_MAP lookup  (user-extensible; empty by default)

    Returns an empty string if the input normalizes to nothing.
    Known limitation: title-stripping is token-level ("Dr Pepper" → "pepper").
    Fix specific cases by adding entries to ALIAS_MAP.
    """
    if not name:
        return ""

    # 1. Unicode → ASCII
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    # 2. Lowercase
    text = text.lower()
    # 3. Strip possessives
    text = re.sub(r"'s\b", "", text)
    # 4. Underscores → spaces; remove remaining punctuation except hyphens
    text = text.replace("_", " ")
    text = re.sub(r"[^\w\s-]", "", text)
    # 5. Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    fallback = text
    # 6. Drop title tokens
    tokens = [t for t in text.split() if t not in TITLES]
    text = " ".join(tokens).strip()
    if not text:
        text = fallback  # don't reduce a bare title token (e.g. "Dr.") to ""

    # 7. Alias map
    return ALIAS_MAP.get(text, text)


# ---------------------------------------------------------------------------
# Relation normalization
# ---------------------------------------------------------------------------

# Epistemic passive construction:
#   "is/was/are/were/has/had/been believed/thought/said/known/considered... to (be)? / as?"
_HEDGE_PASSIVE = re.compile(
    r"^(?:is|are|was|were|has|had|have|been|be|being)\s+"
    r"(?:believed|thought|said|known|considered|supposed|reported|found|seen|understood|deemed|regarded)\s+"
    r"(?:to\s+be\s+|to\s+|as\s+|as$)?",
    re.IGNORECASE,
)

# Bare epistemic verb without copula:
#   "believed to", "considered to be", "thought to be", etc.
_HEDGE_BARE = re.compile(
    r"^(?:believed|thought|said|considered|supposed|reported|seen|understood|deemed|regarded)\s+"
    r"(?:to\s+be\s+|to\s+|as\s+)",
    re.IGNORECASE,
)

# Appearance / probability verbs:
#   "appears to (be)?", "seems to (be)?", "looks to (be)?"
_HEDGE_APPEAR = re.compile(
    r"^(?:appears|seems|looks)\s+to\s+(?:be\s+)?",
    re.IGNORECASE,
)

# Modal hedges:
#   "may (be)?", "might (be)?", "could (be)?", etc.
_HEDGE_MODAL = re.compile(
    r"^(?:may|might|could|should|would|can|must|will)\s+(?:be\s+)?",
    re.IGNORECASE,
)

# Leading copula / articles — stripped iteratively (handles "is the other self of")
_COPULA = re.compile(
    r"^(?:is|are|was|were|has|had|have|be|been|being|the|a|an)\s+",
    re.IGNORECASE,
)

# Lone "as" left over after stripping "is known as" → strip only if word boundary
_LONE_AS = re.compile(r"^as(?:\s+|$)")

_HEDGE_PATTERNS = (_HEDGE_PASSIVE, _HEDGE_BARE, _HEDGE_APPEAR, _HEDGE_MODAL)


def normalize_relation(relation: str) -> str:
    """
    Normalize a relation string to a canonical, lowercase, hedge-free,
    lemmatized form using corpus-agnostic linguistic transformations.

    Pipeline:
      1. Lowercase + underscores → spaces + collapse whitespace
      2. Strip epistemic/modal hedge prefixes  (grammar-driven regex, not a word list)
      3. Strip leading copula / articles       ("is" / "was" / "the" / "a" / "an" …)
      4. Strip lone residual "as"              (leftover from "is known as")
      5. Lemmatize the leading verb to its base form via nltk WordNetLemmatizer
         (falls back to no-op if nltk is unavailable)
      6. Collapse whitespace

    Examples (corpus-independent):
      "is believed to be rival of"   → "rival of"
      "believed_to_fear"             → "fear"
      "plotted against"              → "plot against"
      "may be associated with"       → "associate with"
      "is known as"                  → ""
      "heard tales about"            → "hear tales about"
      "is the other self of"         → "other self of"
      "appears to control"           → "control"
    """
    if not relation:
        return ""

    # 1. Clean
    text = relation.strip().lower()
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()

    # 2. Strip hedge prefix (first match wins)
    for pat in _HEDGE_PATTERNS:
        m = pat.match(text)
        if m:
            text = text[m.end():].strip()
            break

    # 3. Strip leading copula/articles (up to 3 passes for "is the X of")
    for _ in range(3):
        m = _COPULA.match(text)
        if m:
            text = text[m.end():].strip()
        else:
            break

    # 4. Strip lone residual "as" (e.g. "is known as" → "" after copula pass)
    m = _LONE_AS.match(text)
    if m:
        text = text[m.end():].strip()

    # 5. Lemmatize first token as verb
    lem = _get_lemmatizer()
    if lem and text:
        tokens = text.split()
        tokens[0] = lem.lemmatize(tokens[0], "v")
        text = " ".join(tokens)

    # 6. Final cleanup
    return re.sub(r"\s+", " ", text).strip()
