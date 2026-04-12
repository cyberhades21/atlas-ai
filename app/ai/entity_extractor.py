"""
Entity extractor.

FIX #8 — bare except replaced with except Exception:
    `except:` catches *everything*, including BaseException subclasses such as
    KeyboardInterrupt, SystemExit, and GeneratorExit.  Swallowing those makes
    the process un-killable and hides real programmer errors (NameError,
    TypeError, etc.) that should surface during development.

    Fix: narrow to `except Exception` so only runtime errors are suppressed,
    and log the error at WARNING level so failures are visible in the log
    stream without crashing the caller.
"""

import logging

from app.ai.llm import call_llm_json

logger = logging.getLogger(__name__)

PROMPT = """Extract named entities from the text below.

Rules:
- Return ONLY a JSON array of strings, nothing else.
- Use canonical names: no titles, honorifics, or possessives.
  WRONG: ["President Obama", "Dr. Smith", "Obama's policy"]
  RIGHT: ["barack obama", "jane smith", "obama policy"]
- Use lowercase for all entity names.
- If no entities are found, return [].

Text:
"""


def extract_entities(text: str) -> list:
    try:
        return call_llm_json(PROMPT + text)
    except Exception as exc:
        logger.warning("Entity extraction failed: %s", exc)
        return []
