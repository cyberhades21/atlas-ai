# ATLAS AI — Local LLM Observability & RAG Debugger

A fully local, open-source system to **see, inspect, and debug how RAG pipelines actually work**.

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

Most RAG systems are black boxes.

You send a query → you get an answer → everything in between is hidden.

ATLAS turns that into a **fully observable pipeline**.

### What makes ATLAS different

* **Full pipeline observability**
  Every stage (embedding, retrieval, graph traversal, context building, generation) is visible and inspectable.

* **Execution replay system**
  Re-run and step through past queries like a debugger.

* **Node-level inspection**
  Click any stage to see:

  * Retrieved chunks
  * Similarity scores
  * Extracted entities
  * Prompt sent to the LLM

* **Dual retrieval engine**
  Combines:

  * Vector search (semantic similarity)
  * Knowledge graph traversal (relationships)

* **Live knowledge graph**
  Documents become entities + relationships, visualised in real time.

* **100% local**
  Powered by Ollama — no APIs, no data leaving your machine.

---

## Who is this for?

* AI engineers building RAG systems
* Developers who want to understand how LLM pipelines work
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

| Home                                        | Answer + Sources                                                             |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| ![Chat Home](static/images/Chat%20Home.png) | ![Chat Answer](static/images/Chat%20Question%20answer%20and%20documents.png) |

### Document Indexing

| Indexing                                                               | Indexed                                                 |
| ---------------------------------------------------------------------- | ------------------------------------------------------- |
| ![Indexing](static/images/Chat%20Document%20indexing%20inprogress.png) | ![Indexed](static/images/Chat%20Document%20indexed.png) |

### Pipeline Simulator

| Home                                            | Progress                                                     | Completed                                            |
| ----------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| ![Sim Home](static/images/Simulator%20Home.png) | ![Sim Progress](static/images/Simulator%20in%20progress.png) | ![Sim Done](static/images/Simulator%20Completed.png) |

### Node Inspection

| Inspect                                                | Paused                                          |
| ------------------------------------------------------ | ----------------------------------------------- |
| ![Node](static/images/Simulator%20Node%20Selected.png) | ![Paused](static/images/Simulator%20Paused.png) |

### Knowledge Graph

| Full                                                     | Zoom  + Selected                                                                     |
| -------------------------------------------------------- | -------------------------------------------------------------------------- |
| ![Graph](static/images/Graph%20Visualization%20Main.png) | ![Graph Zoom](static/images/Graph%20Visualization%20Zoomed%20Selected.png) |

---

## Capabilities

> ⚠️ ATLAS is designed for **transparency and debugging**, not just answering questions.

| Capability              | Detail                     |
| ----------------------- | -------------------------- |
| PDF ingestion           | Upload and index documents |
| Chunked embedding       | nomic-embed-text           |
| Entity extraction       | LLM-based                  |
| Relationship extraction | Triples stored in SQLite   |
| Vector search           | ChromaDB                   |
| Graph search            | Entity traversal           |
| Context fusion          | Vector + graph             |
| Pipeline simulator      | Step-by-step execution     |
| Replay system           | Re-run pipelines           |
| Live updates            | SSE-driven                 |
| Model switching         | Runtime selection          |
| Deduplication           | Graph constraints          |

---

## Core Innovation

ATLAS introduces **pipeline instrumentation for LLM systems**.

Instead of a single opaque flow, every step is:

* Captured as an event
* Streamed in real-time
* Stored for replay
* Visualised in the UI

This enables:

* Time-travel debugging for AI pipelines
* Fine-grained inspection of intermediate states
* Understanding *why* an answer was generated

---

## Architecture Overview

ATLAS splits the RAG pipeline into observable stages.

```
User Query
   ↓
Embedding
   ↓
Vector Search ─┐
               ├──→ Context Fusion → LLM
Graph Search ──┘
   ↓
Pipeline Events → UI + Replay System
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

```bash
ollama pull mistral
ollama pull nomic-embed-text

git clone https://github.com/cyberhades21/atlas-ai.git
cd atlas-ai

python -m venv venv
source venv/bin/activate  # or Windows equivalent

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: http://localhost:8000

---

## Pages

* `/` → Chat
* `/simulator` → Pipeline debugger
* `/graph-view` → Knowledge graph
* `/docs` → API

---

## Usage

### Indexing

Upload PDF → watch pipeline execute live.

### Query

Ask → inspect retrieval + context.

### Simulator

Run → pause → inspect → replay.

---

## Project Structure

```
atlas-ai/
  app/
    ai/
    pipeline/
    services/
    api/
    storage/
    static/
  data/
  static/images/
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

## API

Available at `/docs`

---

## License

MIT
