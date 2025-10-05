from fastapi import FastAPI, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import math
import re
import os
from functools import lru_cache
import google.generativeai as genai
from sqlalchemy.orm import Session
import json

try:
    from .database import get_database, create_tables
    from .database.service import get_database_service
    from .database.models import Publication
except ImportError:
    # Handle direct script execution
    from database import get_database, create_tables
    from database.service import get_database_service
    from database.models import Publication

app = FastAPI(
    title="AstroBio Explorer API",
    version="0.1.0",
    description=(
        "APIs for summarization, semantic search, knowledge graph access, and visualizations "
        "for NASA bioscience research related to Moon and Mars."
    ),
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    create_tables()

# CORS for local dev (static site served on 127.0.0.1/localhost:5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Models
# -----------------------------
class SummarizeRequest(BaseModel):
    text: str
    language: str = "en"  # future: support multilingual summaries (en, hi, es)


class SummarizeResponse(BaseModel):
    abstract: str
    key_takeaways: List[str]
    ai_tags: List[str]


class SearchRequest(BaseModel):
    query: str
    filters: Optional[dict] = None  # e.g., {"organism": "Arabidopsis", "mission": "ISS"}
    limit: int = 20
    offset: int = 0


class PublicationResponse(BaseModel):
    id: int
    title: str
    abstract: Optional[str] = None
    authors: List[str] = []
    publication_year: Optional[int] = None
    organism_type: Optional[str] = None
    research_domain: Optional[str] = None
    url: Optional[str] = None
    

class PublicationListResponse(BaseModel):
    publications: List[PublicationResponse]
    total: int
    offset: int
    limit: int


class NASAIngestRequest(BaseModel):
    source: str  # 'ntrs', 'open_data', 'pubspace', 'all'
    limit: int = 100


# -----------------------------
# Utilities (lightweight, no extra deps)
# -----------------------------

@lru_cache(maxsize=1)
def has_gemini() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))

@lru_cache(maxsize=1)
def configure_gemini() -> bool:
    if not has_gemini():
        return False
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return True

_STOPWORDS = {
    "the","and","a","an","in","on","for","of","to","is","are","was","were","be","been","being",
    "with","by","as","at","that","this","these","those","it","its","from","or","we","our","you",
    "your","their","they","he","she","his","her","i","me","my","mine","but","not","no","yes","can",
    "will","would","could","should","may","might","into","about","over","under","between","among","than",
    "such","more","most","least","also","using","use","used","via","per","each","both","if","then","else",
}

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_TOKEN_SPLIT = re.compile(r"[^a-z0-9]+")


def _sentences(text: str) -> List[str]:
    # simple sentence split on punctuation
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sents if s.strip()]


def _tokens(text: str) -> List[str]:
    toks = [t for t in _TOKEN_SPLIT.split(text.lower()) if t]
    return [t for t in toks if t not in _STOPWORDS and len(t) > 1]


def _top_keywords(text: str, k: int = 5) -> List[str]:
    freq: Dict[str, int] = {}
    for t in _tokens(text):
        freq[t] = freq.get(t, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: kv[1], reverse=True)[:k]]


def _cosine_sim(q: Dict[str, float], d: Dict[str, float]) -> float:
    dot = sum(q.get(t, 0.0) * d.get(t, 0.0) for t in set(q) | set(d))
    nq = math.sqrt(sum(v * v for v in q.values())) or 1.0
    nd = math.sqrt(sum(v * v for v in d.values())) or 1.0
    return dot / (nq * nd)


def _bow(text: str) -> Dict[str, float]:
    vec: Dict[str, float] = {}
    for t in _tokens(text):
        vec[t] = vec.get(t, 0.0) + 1.0
    return vec

# Embeddings helpers (optional, if GEMINI is configured)
@lru_cache(maxsize=1)
def _corpus_embeddings() -> Optional[List[List[float]]]:
    if not configure_gemini():
        return None
    vecs: List[List[float]] = []
    try:
        for d in _SAMPLE_DOCS:
            text = f"{d['title']}\n{d['abstract']}"
            resp = genai.embed_content(model="text-embedding-004", content=text)
            emb = resp.get("embedding") or resp.get("data", {}).get("embedding")
            # Some SDK versions return dict with 'embedding' directly as list
            if isinstance(emb, list):
                vecs.append(emb)
            elif isinstance(resp, dict) and "embedding" in resp:
                vecs.append(resp["embedding"])  # type: ignore
        return vecs if vecs else None
    except Exception:
        return None


def _embed_query(q: str) -> Optional[List[float]]:
    if not configure_gemini():
        return None
    try:
        resp = genai.embed_content(model="text-embedding-004", content=q)
        emb = resp.get("embedding") or resp.get("data", {}).get("embedding")
        if isinstance(emb, list):
            return emb
        if isinstance(resp, dict) and "embedding" in resp:
            return resp["embedding"]  # type: ignore
        return None
    except Exception:
        return None


# -----------------------------
# Demo corpus for semantic search (placeholder)
# -----------------------------
_SAMPLE_DOCS: List[Dict[str, Any]] = [
    {
        "id": "astro-1",
        "title": "Microgravity Effects on Human Bone Density",
        "abstract": "Microgravity accelerates bone density loss in astronauts. Countermeasures include resistance exercise and nutritional interventions.",
        "year": 2014,
        "organism": "Human",
        "mission": "ISS",
    },
    {
        "id": "astro-2",
        "title": "Plant Growth Dynamics in Spaceflight",
        "abstract": "Arabidopsis exhibits altered root morphology and gene expression in microgravity. Light directionality affects auxin transport and growth.",
        "year": 2018,
        "organism": "Plant",
        "mission": "ISS",
    },
    {
        "id": "astro-3",
        "title": "Immune Response Modulation under Space Conditions",
        "abstract": "Spaceflight suppresses certain immune pathways while upregulating stress responses. Findings inform crew health risk assessments.",
        "year": 2019,
        "organism": "Human",
        "mission": "ISS",
    },
    {
        "id": "astro-4",
        "title": "Microbial Behavior in Low-Shear Environments",
        "abstract": "Microgravity-like conditions influence biofilm formation and antibiotic resistance in select microbes.",
        "year": 2016,
        "organism": "Microbe",
        "mission": "Ground Analog",
    },
    {
        "id": "astro-5",
        "title": "Radiation Effects on Plant Seeds",
        "abstract": "Chronic low-dose radiation impacts germination rates and early development in crop seeds, with species-specific sensitivity.",
        "year": 2012,
        "organism": "Plant",
        "mission": "ISS",
    },
]


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    text = (req.text or "").strip()
    lang = (req.language or "en").lower()
    if not text:
        return SummarizeResponse(abstract="", key_takeaways=[], ai_tags=[])

# If Gemini is configured, ask an LLM for a short abstract, takeaways, and tags
    if configure_gemini():
        sys = (
            "You are AstroBio Buddy, assisting with NASA bioscience literature. "
            "Return a concise abstract (~2-3 sentences), 3-5 bullet key takeaways, and 3-6 topical tags. "
            "If a non-English language is requested, translate outputs to that language. Target language code: "
            + lang
        )
        user = f"Summarize the following text. Language: {lang}.\n\n{text}"
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=sys)
            resp = model.generate_content(user)
            content = getattr(resp, "text", None) or ""
            # Heuristic parse: split sections by headers if present
            abstract = content
            key_takeaways = []
            ai_tags = []
            parts = re.split(r"\n\s*\n", content)
            if parts:
                abstract = parts[0].strip()
                for p in parts[1:]:
                    if len(key_takeaways) < 1 and re.search(r"takeaways|bullets|key points", p, re.I):
                        key_takeaways = [re.sub(r"^[-•\s]+", "", x).strip() for x in p.splitlines() if x.strip()][:5]
                    if len(ai_tags) < 1 and re.search(r"tags|topics|labels", p, re.I):
                        ai_tags = [re.sub(r"^[#-\s]+", "", x).strip() for x in re.split(r",|\n", p) if x.strip()][:6]
            if not key_takeaways:
                kws = _top_keywords(text, k=6)
                key_takeaways = [f"Keyword: {w}" for w in kws[:3]]
            if not ai_tags:
                ai_tags = [w.title() for w in _top_keywords(text, k=5)]
            return SummarizeResponse(abstract=abstract, key_takeaways=key_takeaways, ai_tags=ai_tags)
        except Exception:
            # fall through to naive path
            pass

    # Naive local summarization
    sents = _sentences(text)
    abstract = " ".join(sents[:2]) if sents else text[:280]
    keywords = _top_keywords(text, k=6)
    key_takeaways = [f"Keyword: {w}" for w in keywords[:3]] or ["Review source text for key points."]
    ai_tags = [w.title() for w in keywords[:5]]
    return SummarizeResponse(abstract=abstract, key_takeaways=key_takeaways, ai_tags=ai_tags)


@app.post("/search", response_model=PublicationListResponse)
def search(req: SearchRequest, db: Session = Depends(get_database)):
    db_service = get_database_service(db)
    
    # Convert old filter format to new format
    db_filters = {}
    if req.filters:
        if "organism" in req.filters:
            db_filters["organism_type"] = req.filters["organism"]
        if "mission" in req.filters:
            # For now, we'll search in research_domain
            db_filters["research_domain"] = req.filters["mission"]
        if "year" in req.filters:
            db_filters["publication_year"] = int(req.filters["year"])
    
    # Search database
    search_result = db_service.search_publications(
        query=req.query,
        filters=db_filters,
        limit=req.limit,
        offset=req.offset
    )
    
    # Convert to response format
    publications = []
    for pub in search_result['publications']:
        pub_response = PublicationResponse(
            id=pub.id,
            title=pub.title,
            abstract=pub.abstract,
            authors=[author.name for author in pub.authors],
            publication_year=pub.publication_year,
            organism_type=pub.organism_type,
            research_domain=pub.research_domain,
            url=pub.url
        )
        publications.append(pub_response)
    
    return PublicationListResponse(
        publications=publications,
        total=search_result['total'],
        offset=search_result['offset'],
        limit=search_result['limit']
    )


# -----------------------------
# NASA Data Management endpoints
# -----------------------------

@app.post("/nasa-data/ingest")
def ingest_nasa_data(req: NASAIngestRequest, db: Session = Depends(get_database)):
    """Ingest data from NASA sources"""
    db_service = get_database_service(db)
    
    result = db_service.ingest_nasa_data(
        source_name=req.source,
        limit=req.limit
    )
    
    return result


@app.get("/nasa-data/stats")
def get_nasa_data_stats(db: Session = Depends(get_database)):
    """Get statistics about stored NASA data"""
    db_service = get_database_service(db)
    return db_service.get_publication_stats()


@app.get("/publications/{publication_id}")
def get_publication(publication_id: int, db: Session = Depends(get_database)):
    """Get a specific publication by ID"""
    db_service = get_database_service(db)
    publication = db_service.get_publication(publication_id)
    
    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    return PublicationResponse(
        id=publication.id,
        title=publication.title,
        abstract=publication.abstract,
        authors=[author.name for author in publication.authors],
        publication_year=publication.publication_year,
        organism_type=publication.organism_type,
        research_domain=publication.research_domain,
        url=publication.url
    )


# -----------------------------
# Extra AI-backed endpoints
# -----------------------------

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system: Optional[str] = None

@app.post("/chat")
def chat(req: ChatRequest):
    if configure_gemini():
        sys = req.system or (
            "You are AstroBio Buddy, an assistant for NASA bioscience exploration. "
            "Be concise, cite concepts from the provided demo corpus when relevant, and avoid fabricating sources."
        )
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=sys)
            # Format a lightweight transcript
            convo = []
            for m in req.messages[-10:]:
                role = m.role.lower()
                if role not in ("system", "user", "assistant"):
                    continue
                convo.append(f"{role.title()}: {m.content}")
            prompt = "\n".join(convo) if convo else "User: Hello\nAssistant:"
            resp = model.generate_content(prompt)
            return {"reply": getattr(resp, "text", None) or ""}
        except Exception:
            return {"reply": "AstroBio Buddy is temporarily unavailable. Please check your GEMINI_API_KEY or try again later. Meanwhile, use Search and Summarize above."}
    # Fallback: simple echo with suggested queries
    return {"reply": "AstroBio Buddy is not configured. Set GEMINI_API_KEY to enable chat, or use Search and Summarize."}


class GapAnalysisRequest(BaseModel):
    topic: str

@app.post("/gap_analyze")
def gap_analyze(req: GapAnalysisRequest):
    topic = (req.topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    if configure_gemini():
        prompt = (
            "Identify underexplored research gaps in NASA bioscience related to the topic. "
            "Use only general knowledge and the following demo corpus items (titles only). "
            "Return 3-5 gaps with short rationales.\n\nDemo corpus titles:\n- "
            + "\n- ".join(d["title"] for d in _SAMPLE_DOCS)
            + f"\n\nTopic: {topic}"
        )
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction="You analyze gaps succinctly.")
            resp = model.generate_content(prompt)
            return {"gaps": getattr(resp, "text", None) or ""}
        except Exception:
            # Graceful fallback
            return {"gaps": "Example gaps:\n- Few studies on microbial mutation on long-duration Mars missions.\n- Limited longitudinal human immune profiling across mission phases.\n- Sparse cross-organism comparisons for radiation dose-response in plants vs microbes."}
    # Fallback
    return {"gaps": "Example gap: Few studies on microbial mutation on long-duration Mars missions."}


@app.get("/timeline")
def timeline():
    # Group sample docs by mission and provide optional LLM summary
    missions: Dict[str, List[Dict[str, Any]]] = {}
    for d in _SAMPLE_DOCS:
        missions.setdefault(d["mission"], []).append(d)
    out = []
    for m, items in missions.items():
        summary = ""
        if configure_gemini():
            try:
                prompt = "Summarize the following mission-related studies in ~2 sentences:\n" + "\n".join(f"- {i['title']}" for i in items)
                model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction="You summarize crisply.")
                resp = model.generate_content(prompt)
                summary = getattr(resp, "text", None) or ""
            except Exception:
                summary = ""
        out.append({
            "mission": m,
            "count": len(items),
            "items": [{"id": i["id"], "title": i["title"], "year": i["year"], "organism": i["organism"]} for i in items],
            "summary": summary,
        })
    return {"missions": out}


# To run locally (once dependencies are installed):
#   uvicorn services.api.main:app --reload
#   uvicorn services.api.main:app --reload

# CORS for local dev (frontend on port 5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)