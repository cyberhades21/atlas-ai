# Changelog

All notable changes to ATLAS are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `.github` community health files: issue templates, PR template, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG

---

## [0.3.0] — 2026-04-13

### Added
- Pipeline simulation page with node-by-node playback, pause/resume
- Vector update broadcast bus for live embedding updates in the graph view

---

## [0.2.0] — 2026-04-12

### Added
- Token enhancer for improved entity extraction
- Refined entity and relationship extraction prompts

---

## [0.1.0] — 2026-04-11

### Added
- Initial release
- PDF ingestion with chunking, embedding, entity and relationship extraction
- ChromaDB vector search + SQLite graph search with dual context fusion
- Live SSE-driven progress bar during indexing
- Interactive force-directed knowledge graph (react-force-graph)
- Chat interface with source inspection
- Model switcher (runtime Ollama model selection)
- Pipeline execution replay
- FastAPI backend with Swagger docs at `/docs`
