# AstroBio Explorer — Architecture

## Goals
- Provide summarization, semantic search, knowledge graph exploration, and visualization over NASA bioscience research.
- Support multilingual summaries and a student-friendly UX.

## Initial Components
- API (FastAPI)
  - `/health`: service status
  - `/summarize`: Gemini-backed summarization (falls back to heuristic)
  - `/search`: semantic search using Gemini embeddings (falls back to bag-of-words)
  - `/chat`: "AstroBio Buddy" chat via Gemini
  - `/gap_analyze`: Gemini-backed gap analysis
  - `/timeline`: mission summaries (Gemini if available)
- Frontend (Multi-screen static UI)
  - Dashboard (index.html), Search (search.html), Assistant (chat.html), Gap Analysis (analysis.html), Timeline (timeline.html), Gallery (gallery.html)
  - Space-themed design with galaxy background
- Data & Graph (Future)
  - Vector store for semantic search (FAISS/PGVector)
  - Neo4j for knowledge graph
  - ETL pipelines to ingest NASA publications and metadata

## Next Steps
- Replace static frontend with a framework (Next.js or similar)
- Implement NLP summarization pipeline and semantic search
- Design graph schema (Experiments, Organisms, Missions, Findings)
- Add authentication and user profiles
