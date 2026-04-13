# Contributing to ATLAS AI

Thank you for your interest in ATLAS. Contributions of all kinds are welcome — bug reports, feature proposals, new pipeline stages, documentation improvements, and code.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Proposing Features](#proposing-features)
- [Proposing a New Pipeline Stage](#proposing-a-new-pipeline-stage)
- [Development Setup](#development-setup)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Coding Conventions](#coding-conventions)
- [Project Architecture at a Glance](#project-architecture-at-a-glance)
- [Roadmap & Good First Issues](#roadmap--good-first-issues)

---

## Code of Conduct

All contributors must follow the [Code of Conduct](CODE_OF_CONDUCT.md). In short: be respectful, constructive, and inclusive.

---

## Ways to Contribute

| Type | Where to start |
|---|---|
| Report a bug | [Bug report issue](https://github.com/cyberhades21/atlas-ai/issues/new?template=bug_report.md) |
| Request a feature | [Feature request issue](https://github.com/cyberhades21/atlas-ai/issues/new?template=feature_request.md) |
| Propose a new pipeline stage | [Pipeline stage issue](https://github.com/cyberhades21/atlas-ai/issues/new?template=pipeline_stage.md) |
| Ask a question | [Question issue](https://github.com/cyberhades21/atlas-ai/issues/new?template=question.md) or [Discussions](https://github.com/cyberhades21/atlas-ai/discussions) |
| Submit code | Open a PR against `main` |
| Improve docs | Edit `README.md` or inline docstrings and open a PR |

---

## Reporting Bugs

1. Search [existing issues](https://github.com/cyberhades21/atlas-ai/issues) first — it may already be reported.
2. Open a new [Bug Report](https://github.com/cyberhades21/atlas-ai/issues/new?template=bug_report.md).
3. Include your OS, Python version, Ollama version, and the exact error message or stack trace.
4. Attach screenshots or terminal output wherever possible.

---

## Proposing Features

1. Check [Discussions](https://github.com/cyberhades21/atlas-ai/discussions) and open issues to see if the idea already exists.
2. Open a [Feature Request](https://github.com/cyberhades21/atlas-ai/issues/new?template=feature_request.md).
3. Describe the problem first, then the solution — this helps evaluate the proposal independently of any implementation bias.

High-value feature areas:
- New retrieval strategies (e.g. reranking, HyDE, multi-hop graph traversal)
- Additional observable pipeline stages
- Export / import of knowledge graph data
- Multi-document sessions
- Alternative embedding models
- Evaluation / benchmarking tooling

---

## Proposing a New Pipeline Stage

ATLAS is an observability platform for RAG pipelines. A "pipeline stage" is a discrete, observable node that:

- Accepts typed input
- Produces typed output
- Emits SSE events that the simulator and graph UI can render

Use the [Pipeline Stage template](https://github.com/cyberhades21/atlas-ai/issues/new?template=pipeline_stage.md) and include:
- Stage name and position in the pipeline
- Input/output schema
- Events emitted
- Why making this stage visible improves understanding

---

## Development Setup

### Prerequisites

| Tool | Minimum version |
|---|---|
| Python | 3.11 |
| Ollama | latest |
| Git | any recent |

### Local Setup

```bash
# 1. Fork and clone
git clone https://github.com/<your-username>/atlas-ai.git
cd atlas-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Pull Ollama models
ollama pull mistral
ollama pull nomic-embed-text

# 5. Run the dev server
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ATLAS_MODEL` | `mistral` | Default Ollama LLM model |
| `LLM_TIMEOUT` | `120` | Seconds before LLM call times out |

---

## Submitting a Pull Request

1. **Fork** the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes.** Keep commits focused and atomic.

3. **Test locally** — run the server, upload a PDF, run a query, check the simulator and graph view.

4. **Fill in the PR template** when you open the PR. Incomplete PRs may be closed without review.

5. **Open the PR against `main`.**

### PR guidelines

- One logical change per PR. Large refactors should be discussed in an issue first.
- If the PR touches the UI, include before/after screenshots or a screen recording.
- New pipeline stages must emit SSE events compatible with the existing simulator event schema.
- Do not commit secrets, API keys, model weights, or large binary files.
- Keep `requirements.txt` changes minimal and justified.

---

## Coding Conventions

- **Python** — follow PEP 8. Use type hints for all function signatures.
- **SSE events** — follow the existing event shape in `app/pipeline/`. New stages should emit `stage_start`, `stage_complete`, and `stage_error` events.
- **Frontend (Jinja + vanilla JS)** — keep logic in dedicated `<script>` blocks or separate `.js` files. Avoid inline event handlers.
- **No framework churn** — ATLAS intentionally avoids heavy frontend frameworks. Do not introduce React, Vue, or similar dependencies unless discussed first.
- **Comments** — only where the logic is non-obvious. Self-documenting code is preferred.

---

## Project Architecture at a Glance

```
atlas-ai/
├── app/
│   ├── api/          # FastAPI route handlers
│   ├── pipeline/     # Observable pipeline stages (chunking, embedding, retrieval, generation)
│   ├── services/     # Business logic (indexing, querying, replay)
│   ├── storage/      # ChromaDB + SQLite adapters
│   ├── ai/           # LLM and embedding client wrappers
│   └── main.py       # App entry point
├── static/           # CSS, JS, images
├── data/             # Runtime data (gitignored)
└── requirements.txt
```

The core observability contract: every pipeline stage in `app/pipeline/` **must** emit SSE events. The simulator, graph, and chat panels all consume these events.

---

## Roadmap & Good First Issues

Browse issues labelled [`good first issue`](https://github.com/cyberhades21/atlas-ai/labels/good%20first%20issue) for beginner-friendly tasks.

Browse [`help wanted`](https://github.com/cyberhades21/atlas-ai/labels/help%20wanted) for tasks where outside input is especially welcome.

---

## Questions?

Open a [Question issue](https://github.com/cyberhades21/atlas-ai/issues/new?template=question.md) or start a thread in [Discussions](https://github.com/cyberhades21/atlas-ai/discussions).
