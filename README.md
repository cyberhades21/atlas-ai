# ATLAS AI — Local LLM Observability & Glass Box RAG System

A fully local, open-source Retrieval-Augmented Generation system with a **live knowledge graph, step-by-step pipeline visualiser, and full execution observability**.

ATLAS is not just another chatbot.

It is a **glass-box AI system** that lets you:

* Trace every stage of retrieval and generation
* Inspect intermediate data (chunks, entities, scores, prompts)
* Replay full pipeline executions
* Visualise knowledge as a live graph

> If you've ever wondered *"what exactly happened inside my RAG system?"* — ATLAS shows you.

![Chat Home](static/images/Chat%20Home.png)

---

## Why ATLAS?

Most RAG systems are black boxes — you ask a question and get an answer with no visibility into how it was retrieved or reasoned about.

ATLAS turns that into a **fully observable pipeline**.

### What makes ATLAS different

* **Glass box pipeline** — watch every stage execute in real time
* **Pipeline observability** — every step emits inspectable events
* **Execution replay system** — re-run queries like a debugger
* **Node-level inspection** — inspect chunks, scores, entities, prompts
* **Dual retrieval engine** — vector + graph combined
* **Live knowledge graph** — updates instantly as documents are indexed
* **100% local** — powered by Ollama, zero cloud dependency

---

## What is ATLAS (really)?

ATLAS is best understood as:

> **An observability layer for AI systems**

Similar to how debuggers work for code, ATLAS lets you debug **LLM pipelines**.

---

## Who is this for?

* AI engineers building RAG systems
* Developers learning how LLM pipelines work
* Teams working on explainable AI
* Anyone tired of black-box AI behavior

---

## What you can do with ATLAS

* Debug why your RAG system gave a wrong answer
* Inspect retrieval quality (chunks, scores, context)
* Understand graph-based retrieval
* Teach RAG concepts visually
* Experiment with pipeline design

---

## Screenshots

### Chat

Ask questions against your indexed documents. The right panel shows session context — which documents are loaded, last query, retrieved chunks, and a link to the knowledge graph.

| Home                                        | Answer + Sources                                                             |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| ![Chat Home](static/images/Chat%20Home.png) | ![Chat Answer](static/images/Chat%20Question%20answer%20and%20documents.png) |

---

### Document Indexing

Upload a PDF and watch the progress bar track each stage of the pipeline in real time — chunking, embedding, entity extraction, relationship extraction, graph storage.

| Indexing in Progress                                                   | Indexed                                                 |
| ---------------------------------------------------------------------- | ------------------------------------------------------- |
| ![Indexing](static/images/Chat%20Document%20indexing%20inprogress.png) | ![Indexed](static/images/Chat%20Document%20indexed.png) |

---

### Pipeline Simulator

Step through every node of the RAG pipeline visually.

| Home                                            | In Progress                                                  | Completed                                            |
| ----------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| ![Sim Home](static/images/Simulator%20Home.png) | ![Sim Progress](static/images/Simulator%20in%20progress.png) | ![Sim Done](static/images/Simulator%20Completed.png) |

Click any pipeline node to inspect:

* vector previews
* entity lists
* similarity scores
* prompt fragments
* LLM output

| Node Inspect                                           | Paused                                          |
| ------------------------------------------------------ | ----------------------------------------------- |
| ![Node](static/images/Simulator%20Node%20Selected.png) | ![Paused](static/images/Simulator%20Paused.png) |

---

### Knowledge Graph

All entities and relationships extracted from your documents are rendered as an interactive force-directed graph.

| Full Graph                                               | Zoomed + Entity Selected                                                   |
| -------------------------------------------------------- | -------------------------------------------------------------------------- |
| ![Graph](static/images/Graph%20Visualization%20Main.png) | ![Graph Zoom](static/images/Graph%20Visualization%20Zoomed%20Selected.png) |

Pan, zoom, and click any node to see relationships and connected documents.

![Graph Zoomed](static/images/Graph%20Visualization%20Zoomerd.png)

---

## Features

| Feature                 | Detail                                                               |
| ----------------------- | -------------------------------------------------------------------- |
| PDF ingestion           | Upload and index any PDF                                             |
| Chunked embedding       | Text split into overlapping chunks, embedded with `nomic-embed-text` |
| Entity extraction       | Named entities via LLM                                               |
| Relationship extraction | Subject → predicate → object triples in SQLite                       |
| Vector search           | ChromaDB similarity search with distance scores                      |
| Graph search            | Keyword traversal across entity graph                                |
| Dual context fusion     | Vector + graph merged before LLM                                     |
| Live progress bar       | SSE-driven real-time indexing                                        |
| Pipeline simulator      | Node-by-node playback with pause/resume                              |
| Run replay              | Re-watch previous executions                                         |
| Live graph updates      | Graph updates instantly in browser                                   |
| Model switcher          | Switch Ollama models at runtime                                      |
| Deduplication           | UNIQUE(entity1, relation, entity2)                                   |
| Flush tool              | Hidden dev tool                                                      |

---

## Core Innovation

ATLAS introduces **pipeline instrumentation for LLM systems**.

Instead of opaque execution, every step is:

* Captured as an event
* Streamed via SSE
* Stored for replay
* Visualised in the UI

This enables:

* Time-travel debugging
* Deep inspection of intermediate states
* Understanding *why* an answer was generated

---

## Architecture

```
Upload PDF
    │
    ▼
┌─────────────┐
│   Chunking  │
└──────┬──────┘
       ▼
┌─────────────────┐
│   Embedding     │
└──────┬──────────┘
       │
       ├───────────────┐
       ▼               ▼
Vector DB         Entity Extraction
(ChromaDB)             │
                       ▼
                Relationship Extraction
                       ▼
                  Graph DB (SQLite)

Query
    │
    ├── Vector search
    ├── Graph traversal
    ▼
Context Fusion → LLM → Answer
    │
    ▼
Pipeline Events → UI + Replay
```

---

## Prerequisites

### Python 3.11

```bash
python --version
```

### Ollama

```bash
ollama --version
```

---

## Quick Start

### 1. Pull models

```bash
ollama pull mistral
ollama pull nomic-embed-text
```

### 2. Clone repo

```bash
git clone https://github.com/cyberhades21/atlas-ai.git
cd atlas-ai
```

### 3. Setup environment

```bash
python -m venv venv
source venv/bin/activate  # Windows equivalent if needed
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run

```bash
uvicorn app.main:app --reload
```

Open:

```
http://localhost:8000
```

---

## Pages

| URL           | Description         |
| ------------- | ------------------- |
| `/`           | Chat interface      |
| `/simulator`  | Pipeline visualiser |
| `/graph-view` | Knowledge graph     |
| `/docs`       | FastAPI Swagger     |

---

## Usage

### Indexing

Upload → watch pipeline execute live.

### Query

Ask → inspect chunks, scores, context.

### Simulator

Run → pause → inspect → replay.

### Switching models

Use model picker in UI (filters non-chat models automatically).

### Flush tool (Dev)

Triple-click logo within 600ms → flush DB.

---

## Project Structure

```
atlas-ai/
├── app/
│   ├── api/
│   ├── pipeline/
│   ├── services/
│   ├── storage/
│   ├── ai/
│   └── static/
├── data/
├── static/images/
```

---

## Environment Variables

| Variable    | Default |
| ----------- | ------- |
| ATLAS_MODEL | mistral |
| LLM_TIMEOUT | 120     |

---

## Recommended Models

* mistral
* llama3.2
* phi3:mini
* gemma3:1b
* nomic-embed-text

---

## Reset Data

UI: triple-click logo → Flush

CLI:

```bash
rm -rf data
```

---

## API Reference

Available at:

```
http://localhost:8000/docs
```

### Key Endpoints

* `POST /documents/upload`
* `GET /documents/progress/{task_id}` (SSE)
* `POST /query`
* `GET /graph`
* `GET /graph/updates` (SSE)
* `GET /models`
* `GET /simulator/runs`
* `POST /simulator/run`
* `GET /simulator/stream/{run_id}` (SSE)
* `DELETE /admin/flush`

---

## License

MIT
