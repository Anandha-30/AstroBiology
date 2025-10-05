<<<<<<< HEAD

# AstroBiology

# A webApp that highlights the Biology Experiments performed on moon and mars to explore and revisit the habitat .This project is made for a hackathon (Nasa space apps challenge)

# AstroBio Explorer

A student-led web app to explore, visualize, and converse with NASA bioscience research conducted for lunar and Martian exploration. As humans prepare to revisit the Moon and explore Mars, NASA has generated a vast corpus of bioscience research spanning humans, plants, and microbes in space environments.

## Key Features (initial vision)

1. AI-Powered Publication Summarization
   - Abstract summaries in plain English
   - Key takeaways (Impacts on humans/plants/microbes)
   - AI tags (e.g., "Microgravity effects", "Plant growth", "Immune response")
2. Smart Search & Filter
   - Filter by topic, organism, mission, year, author
   - AI-based semantic search (e.g., "plant behavior in microgravity")
3. Knowledge Graph Explorer
   - Interactive graph of Experiments → Organisms → Missions → Findings
   - Backed by Neo4j or rendered via D3.js
4. Dynamic Visualization Dashboard
   - Experiments per year, domains, missions, and topic clouds
   - Export CSV/PNG/PDF
5. AI Chat Assistant ("AstroBio Buddy")
   - Answers research questions with summaries, visualizations, and links
6. Gap Analysis & Research Insights
   - AI highlights underexplored areas and proposes new experiments
7. Mission Timeline
   - Interactive timeline (ISS, Apollo, Artemis) showing bioscience studies
8. User Personalization
   - Login, favorites, collections, export insights
9. Multilingual AI Summaries
   - English + optional Hindi/Spanish

## Architecture

- services/api: FastAPI server with SQLite database, NASA data integration, and AI features
- apps/web: Static HTML/CSS/JavaScript frontend with space-themed design
- docs: Technical docs, architecture, and planning materials
- packages/shared: For shared schemas/utilities (future)
- data/: SQLite database and cached NASA data

## Local Development

### Backend API (Python)

1. Create a virtual environment (PowerShell):
   ```powershell path=null start=null
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r services\api\requirements.txt
   ```
2. Configure Gemini (optional but recommended for full AI features):
   ```powershell path=null start=null
   $env:GEMINI_API_KEY="{{GEMINI_API_KEY}}"
   ```
3. Run the API:
   ```powershell path=null start=null
   uvicorn services.api.main:app --reload
   ```

### Frontend (Multi-screen prototype)

Serve the static site and navigate between screens:

```powershell path=null start=null
python -m http.server 5500 --bind 127.0.0.1 --directory apps\web
```

Open http://127.0.0.1:5500 and navigate to:

- Dashboard: /index.html
- Search: /search.html
- Assistant: /chat.html
- Gap Analysis: /analysis.html
- Timeline: /timeline.html
- Gallery: /gallery.html

## Environment Variables (.env.example)

- GEMINI_API_KEY=
- NEO4J_URI=
- NEO4J_USERNAME=
- NEO4J_PASSWORD=
- NASA_DOCS_DIR=./data/nasa_papers
- DEFAULT_LOCALE=en

Do not commit real secrets. Use a secret manager for local dev or set environment variables in your shell.

## Roadmap

- Replace static frontend with a framework (e.g., Next.js) and set up a design system
- Implement summarization pipeline (NLP model + chunking + prompt templates)
- Add vector search for semantic queries (e.g., FAISS/PGVector) and metadata filters
- Integrate Neo4j for knowledge graph and D3.js for visualization
- Add analytics dashboards and export functionality
- Implement "AstroBio Buddy" chat and gap analysis
- Authentication (student/researcher modes) and user profiles

## License

MIT

> > > > > > > e750cab (New files)
