# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands

These are the concrete, working commands used in this repo today. Use PowerShell on Windows; bash/zsh equivalents are provided where helpful.

- Create and activate a virtual environment (PowerShell):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
  Bash/zsh:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  ```

- Install backend dependencies:
  ```powershell
  pip install -r services\api\requirements.txt
  ```

- Run the FastAPI backend with autoreload (default port 8000):
  ```powershell
  uvicorn services.api.main:app --reload
  ```

- Verify the API is up (PowerShell):
  ```powershell
  iwr http://localhost:8000/health | Select-Object -ExpandProperty Content
  ```
  Bash/zsh:
  ```bash
  curl http://localhost:8000/health
  ```

- Serve the static prototype frontend without changing directories (Python 3.7+):
  ```powershell
  python -m http.server 5500 --directory apps\web
  ```
  Then open http://localhost:5500 in a browser. The prototype calls the API at http://localhost:8000/health.

Notes:
- There is no configured linter/formatter or test runner in the repository at this time.
- Environment variables are documented in .env.example (GEMINI_API_KEY, NEO4J_*, NASA_DOCS_DIR, DEFAULT_LOCALE).

## High-level architecture and structure

This repository is an early-stage monorepo with a minimal but clear separation of concerns:

- Backend service (services/api)
  - FastAPI application exposing:
    - GET /health – service status
    - POST /summarize – Gemini-backed summarization with language parameter (fallback: heuristic)
    - POST /search – semantic search using Gemini embeddings (fallback: bag-of-words)
    - POST /chat – "AstroBio Buddy" chat (Gemini if configured)
    - POST /gap_analyze – Gemini-backed gap analysis
    - GET /timeline – mission summaries (Gemini if configured)
  - Implementation is in services/api/main.py using Pydantic models for request/response shapes.

- Frontend (multi-screen static UI) in apps/web
  - Pages: index.html (Dashboard), search.html, chat.html, analysis.html, timeline.html, gallery.html
  - Galaxy space theme; no build tooling required; serve via a static server.

- Shared package placeholder (packages/shared)
  - Reserved for future shared schemas/types/utilities. No runtime code today.

- Documentation (docs)
  - docs/architecture.md documents API endpoints and screens, and the plan for vector stores and Neo4j.

- Environment variables (.env.example)
  - GEMINI_API_KEY, NEO4J_* values, NASA_DOCS_DIR, DEFAULT_LOCALE

Data flow (current state):
- Static pages call FastAPI endpoints directly; when GEMINI_API_KEY is set, AI features are enabled; otherwise, graceful fallbacks are used.

Scope and omissions (intentional at this stage):
- No test suite, CI, containers, or Node-based frontend framework yet. The README describes these as roadmap items rather than implemented features.
