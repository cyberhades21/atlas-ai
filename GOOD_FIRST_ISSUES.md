# Good First Issues

A catalogue of well-scoped, self-contained tasks for new contributors.
Each issue is grounded in a specific file and line range so you can jump straight in.

Pick one, open it as a GitHub issue using the linked template, and mention this file in your issue so the maintainer can label it `good first issue`.

---

## #GFI-01 — Add file-type validation on PDF upload

**File:** `app/api/documents.py`
**Effort:** ~15 min | **Skills:** Python, FastAPI

`upload_document()` accepts any file type. A non-PDF upload fails silently deep in the pipeline when the parser tries to read it. The endpoint should reject non-PDFs early with a descriptive HTTP 400.

---

## #GFI-02 — Add error handling to `pdf_parser.py`

**File:** `app/utils/pdf_parser.py`
**Effort:** ~20 min | **Skills:** Python

`extract_text()` has no error handling. Corrupted PDFs, missing files, and permission errors all propagate as unhandled exceptions and produce an unhelpful 500 at the API layer.

---

## #GFI-03 — Add type hints to `embeddings.py`

**File:** `app/ai/embeddings.py`
**Effort:** ~20 min | **Skills:** Python, type hints

`embed_chunks()` and `embed_query()` have no parameter or return type annotations. This makes IDE support and static analysis blind to the module.

---

## #GFI-04 — Add type hints to `chunking.py` and `relationship_extractor.py`

**Files:** `app/ai/chunking.py`, `app/ai/relationship_extractor.py`
**Effort:** ~20 min | **Skills:** Python, type hints

Both modules export functions with no type annotations, leaving callers without IDE inference or static analysis coverage.

---

## #GFI-05 — Extract magic strings into a constants module

**Files:** scattered across `app/`
**Effort:** ~30 min | **Skills:** Python, refactoring

Model names, collection names, and file paths are hardcoded in multiple places with no single source of truth:

| Value | Files |
|---|---|
| `"nomic-embed-text"` | `app/ai/embeddings.py`, `app/api/debug.py` |
| `"mistral"` | `app/ai/llm.py` |
| `"atlas"` | `app/storage/vector_store.py` |
| `"data/entities.db"` | `app/storage/entity_store.py`, `app/storage/graph_store.py` |

Centralising these makes them easy to change without hunting across the codebase.

---

## #GFI-06 — Convert smoke tests into real unit tests

**File:** `app/test/`
**Effort:** ~1 hr | **Skills:** Python, pytest

All three test files (`test_embed.py`, `test_ollama.py`, `test_pdf.py`) call code and print output but make zero assertions. They cannot catch regressions because they never fail.

---

## #GFI-07 — Add input validation to the query endpoint

**File:** `app/api/query.py` (and wherever `QueryRequest` is defined)
**Effort:** ~20 min | **Skills:** Python, FastAPI, Pydantic

`QueryRequest.question` has no length constraints. An empty string or an enormous payload passes validation and hits the LLM. `top_k` and `temperature` also have no bounds enforcement at the API layer.

---

## #GFI-08 — Add a logging configuration to `main.py`

**File:** `app/main.py`
**Effort:** ~25 min | **Skills:** Python, logging

Individual modules call `logging.getLogger(__name__)` but there is no root logging setup. Nothing below WARNING is shown and there is no consistent log format across the app.

---

## #GFI-09 — Add a `dev-requirements.txt` with linting and type-checking tools

**File:** new file `dev-requirements.txt`, update `CONTRIBUTING.md`
**Effort:** ~20 min | **Skills:** Python tooling

There are no dev-dependency tools in the repo. Contributors have no standard way to lint, type-check, or run tests before submitting a PR. `CONTRIBUTING.md` should be updated to document the workflow once the file exists.

---

## #GFI-10 — Add a GitHub Actions CI workflow

**File:** new file `.github/workflows/ci.yml`
**Effort:** ~45 min | **Skills:** GitHub Actions, Python

There is no automated CI. PRs are merged without any automated checks for lint errors, type errors, or test regressions. Ollama-dependent tests will need to be skipped in the CI environment.

---

## #GFI-11 — Add OpenAPI descriptions to all API endpoints

**Files:** `app/api/*.py`
**Effort:** ~30 min | **Skills:** Python, FastAPI

FastAPI auto-generates Swagger docs at `/docs`, but all endpoints are missing `summary` and `description` fields. The auto-generated docs are bare and hard to use. This is a documentation-only change — no logic should be touched.

---

## #GFI-12 — Show retrieval scores in the chat source panel

**Files:** `app/services/query_service.py`, `app/api/query.py`, `static/index.html`
**Effort:** ~1 hr | **Skills:** Python, FastAPI, JavaScript

The `/query` endpoint computes vector similarity scores during retrieval but drops them before returning the response. The chat source panel lists chunks with no indication of how relevant each one was, which undermines the observability goal of the project.

---

## How to claim an issue

1. Open a new [Feature Request](https://github.com/cyberhades21/atlas-ai/issues/new?template=feature_request.md) or [Bug Report](https://github.com/cyberhades21/atlas-ai/issues/new?template=bug_report.md) issue.
2. Title it exactly as shown above (e.g. `[GFI-03] Add type hints to embeddings.py`).
3. Reference this file in the description.
4. The maintainer will label it `good first issue` and you can start a PR.
