# ATLAS AI — Glass Box RAG System

A fully local, open-source Retrieval-Augmented Generation system with a live knowledge graph, step-by-step pipeline visualiser, and zero cloud dependency. Every inference call stays on your machine.

![Chat Home](static/images/Chat%20Home.png)

---

## What is ATLAS?

Most RAG systems are black boxes — you ask a question and get an answer with no visibility into how it was retrieved or reasoned about. ATLAS is different.

- **Glass box pipeline** — watch every stage of retrieval execute in real time
- **Knowledge graph** — entities and relationships extracted from your documents, visualised as a live force-directed graph
- **Dual retrieval** — vector similarity search + graph traversal combined into a single context window
- **100% local** — powered by [Ollama](https://ollama.com). No API keys, no data leaving your machine

---

## Screenshots

### Chat
Ask questions against your indexed documents. The right panel shows session context — which documents are loaded, last query, retrieved chunks, and a link to the knowledge graph.

| Home | Answer + Sources |
|------|-----------------|
| ![Chat Home](static/images/Chat%20Home.png) | ![Chat Answer](static/images/Chat%20Question%20answer%20and%20documents.png) |

### Document Indexing
Upload a PDF and watch the progress bar track each stage of the pipeline in real time — chunking, embedding, entity extraction, relationship extraction, graph storage.

| Indexing in Progress | Indexed |
|----------------------|---------|
| ![Indexing](static/images/Chat%20Document%20indexing%20inprogress.png) | ![Indexed](static/images/Chat%20Document%20indexed.png) |

### Pipeline Simulator
Step through every node of the RAG pipeline visually. See exactly which chunks were retrieved, what entities were extracted, how the context was assembled, and what the LLM received.

| Home | In Progress | Completed |
|------|-------------|-----------|
| ![Sim Home](static/images/Simulator%20Home.png) | ![Sim Progress](static/images/Simulator%20in%20progress.png) | ![Sim Done](static/images/Simulator%20Completed.png) |

Click any pipeline node to inspect its full payload — vector previews, entity lists, similarity scores, prompt fragments, and LLM output.

| Node Inspect | Paused |
|--------------|--------|
| ![Node](static/images/Simulator%20Node%20Selected.png) | ![Paused](static/images/Simulator%20Paused.png) |

### Knowledge Graph
All entities and relationships extracted from your documents rendered as an interactive force-directed graph. Updates live as you index new documents — no page reload needed.

| Full Graph | Zoomed + Entity Selected |
|------------|--------------------------|
| ![Graph](static/images/Graph%20Visualization%20Main.png) | ![Graph Zoom](static/images/Graph%20Visualization%20Zoomed%20Selected.png) |

Pan, zoom, and click any node to see all its relationships and connected documents in the side panel.

![Graph Zoomed](static/images/Graph%20Visualization%20Zoomerd.png)

---

## Features

| Feature | Detail |
|---------|--------|
| PDF ingestion | Upload and index any PDF |
| Chunked embedding | Text split into overlapping chunks, embedded with `nomic-embed-text` |
| Entity extraction | Named entities pulled from each chunk via LLM |
| Relationship extraction | Subject → predicate → object triples stored in SQLite |
| Vector search | ChromaDB similarity search with distance scores |
| Graph search | Keyword traversal across the entity graph |
| Dual context fusion | Vector + graph context merged before LLM call |
| Live progress bar | SSE-driven real-time indexing stages with percentages |
| Pipeline simulator | Node-by-node visual playback with pause/resume |
| Run replay | Re-watch any previous pipeline run |
| Live graph updates | Knowledge graph updates in browser as documents are indexed |
| Model switcher | Switch Ollama chat models on the fly in Chat and Simulator |
| Duplicate deduplication | Graph DB enforces `UNIQUE(entity1, relation, entity2)` |
| Flush tool | Hidden dev tool to wipe vector + graph DB without touching files |

---

## Architecture

```
Upload PDF
    │
    ▼
┌─────────────┐
│   Chunking  │  pypdf → fixed-size overlapping text chunks
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   Embedding     │  nomic-embed-text via Ollama
└──────┬──────────┘
       │
       ├──────────────────────────────┐
       ▼                              ▼
┌─────────────┐              ┌──────────────────────┐
│  ChromaDB   │              │  Entity Extraction   │  LLM → named entities
│ (vector_db) │              └──────────┬───────────┘
└─────────────┘                         │
                                        ▼
                              ┌──────────────────────┐
                              │ Relation Extraction  │  LLM → (e1, rel, e2) triples
                              └──────────┬───────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │  SQLite graph.db │
                               └──────────────────┘

Query
    │
    ├─── Vector search (ChromaDB)
    ├─── Graph search (SQLite LIKE traversal)
    │
    ▼
Context assembly → LLM → Answer
```

---

## Prerequisites

### Python 3.11

```bash
python --version
# Python 3.11.x
```

Download: https://www.python.org/downloads/

### Ollama

Download and install from https://ollama.com, then verify:

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

`mistral` is used for chat, entity extraction, and relationship extraction.  
`nomic-embed-text` is the embedding model.

Any other Ollama chat model can be switched to at runtime via the model picker in the UI. To use a smaller/faster model as default, set:

```bash
# Linux / macOS
export ATLAS_MODEL=llama3.2

# Windows (PowerShell)
$env:ATLAS_MODEL = "llama3.2"
```

### 2. Clone the repo

```bash
git clone https://github.com/cyberhades21/atlas-ai.git
cd atlas-ai
```

### 3. Create and activate a virtual environment

```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# macOS / Linux
python3.11 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Open your browser at:

```
http://localhost:8000
```

That's it. No `.env` file, no configuration, no database migrations.

---

## Pages

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Chat interface |
| `http://localhost:8000/simulator` | Pipeline visualiser |
| `http://localhost:8000/graph-view` | Knowledge graph |
| `http://localhost:8000/docs` | FastAPI Swagger UI |

---

## Usage

### Indexing a document

1. Click **Upload Doc** in the top navbar
2. Choose a PDF file
3. Click **Index Document**
4. Watch the progress bar track each pipeline stage

The knowledge graph at `/graph-view` will update live as relationships are extracted.

### Asking questions

Type any question in the chat input and press **Send**. The right panel shows:
- Which documents contributed context
- Retrieved chunks with similarity scores
- Links to the knowledge graph

### Switching models

Click the model badge (bottom-left of the chat input) to open the model picker. Only chat-capable models from `ollama list` are shown — embedding models are filtered out automatically.

### Using the Simulator

1. Go to `/simulator`
2. Type a question in **Reference Query**
3. Click **Run Execution**
4. Watch each pipeline node light up as it executes
5. Click any node to inspect its full data payload
6. Use the **pause** button to freeze the visualisation mid-run
7. Use **Replay** to re-watch any previous run

### Flushing all data (dev tool)

Triple-click the **ATLAS AI** logo in the top-left within 600ms. A hidden **Flush** button appears in the navbar. This wipes all vector embeddings and graph relationships from the database without deleting uploaded PDF files.

---

## Project Structure

```
atlas-ai/
├── app/
│   ├── main.py                  # FastAPI app, router registration
│   ├── api/
│   │   ├── documents.py         # Upload + SSE progress endpoint
│   │   ├── query.py             # Chat query endpoint
│   │   ├── graph.py             # Graph data + live SSE updates
│   │   ├── graph_view.py        # Serves graph.html
│   │   ├── simulator.py         # Simulator run/stream/replay endpoints
│   │   ├── models.py            # Ollama model list endpoint
│   │   └── admin.py             # Flush endpoint (dev tool)
│   ├── pipeline/
│   │   ├── events.py            # Per-run SSE event bus (simulator)
│   │   ├── ingest_progress.py   # Per-task SSE progress bus (indexing)
│   │   ├── graph_updates.py     # Live graph broadcast bus
│   │   └── instrumented_query.py# Query pipeline with event emission
│   ├── services/
│   │   ├── ingestion_service.py # Full ingest pipeline orchestration
│   │   └── query_service.py     # Query pipeline orchestration
│   ├── storage/
│   │   ├── vector_store.py      # ChromaDB wrapper (lazy init)
│   │   ├── graph_store.py       # SQLite relationships (dedup enforced)
│   │   └── entity_store.py      # Entity persistence
│   ├── ai/
│   │   ├── llm.py               # Ollama generate wrapper + timeout
│   │   ├── embeddings.py        # Embedding via nomic-embed-text
│   │   ├── chunking.py          # PDF text chunking
│   │   ├── entity_extractor.py  # LLM-based entity extraction
│   │   └── relationship_extractor.py # LLM triple extraction
│   └── static/
│       ├── index.html           # Chat UI
│       ├── simulator.html       # Pipeline visualiser UI
│       └── graph.html           # Knowledge graph UI
├── data/                        # Created at runtime
│   ├── documents/               # Uploaded PDFs
│   ├── vector_db/               # ChromaDB files
│   └── graph.db                 # SQLite graph database
├── static/
│   └── images/                  # Screenshots
├── requirements.txt
└── README.md
```

---

## Environment Variables

All variables are optional — the defaults work out of the box.

| Variable | Default | Description |
|----------|---------|-------------|
| `ATLAS_MODEL` | `mistral` | Default Ollama chat model |
| `LLM_TIMEOUT` | `120` | Seconds before an LLM call times out |

---

## Recommended Models

Small models that run well on CPU or modest GPU:

| Model | Pull command | Notes |
|-------|-------------|-------|
| `mistral` | `ollama pull mistral` | Default. Good balance of speed and quality |
| `llama3.2` | `ollama pull llama3.2` | Fast, strong reasoning |
| `llama3.2:1b` | `ollama pull llama3.2:1b` | Very fast, lower quality |
| `phi3:mini` | `ollama pull phi3:mini` | ~2GB, runs on CPU |
| `gemma3:1b` | `ollama pull gemma3:1b` | ~800MB, minimal RAM |
| `nomic-embed-text` | `ollama pull nomic-embed-text` | Required embedding model |

---

## Resetting Data

### Via the UI
Triple-click **ATLAS AI** logo → click **Flush** → confirm. Wipes vectors and graph, keeps PDFs.

### Via the filesystem

```bash
# Stop the server first (Ctrl+C), then:

# Windows
rmdir /s data

# macOS / Linux
rm -rf data
```

Restart the server — the `data/` directory and database are recreated automatically on first use.

---

## API Reference

The full interactive API docs are available at `http://localhost:8000/docs` when the server is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload and index a PDF |
| `GET` | `/documents/progress/{task_id}` | SSE stream of indexing progress |
| `POST` | `/query` | Ask a question |
| `GET` | `/graph` | Get all nodes and edges |
| `GET` | `/graph/updates` | SSE stream of live graph updates |
| `GET` | `/models` | List available Ollama chat models |
| `GET` | `/simulator/runs` | List past simulator runs |
| `POST` | `/simulator/run` | Start a new simulator run |
| `GET` | `/simulator/stream/{run_id}` | SSE stream of simulator events |
| `DELETE` | `/admin/flush` | Wipe all vector and graph data |

---

## License

MIT — see [LICENSE](LICENSE).
