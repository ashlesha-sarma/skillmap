"""
SkillMap — FastAPI Backend
Deterministic learning roadmap engine.
"""
import sys
import os

# Load .env FIRST — before any module that reads env vars
from dotenv import load_dotenv
load_dotenv()

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from engine.database import init_db, load_skills_to_db, get_all_skills
from engine.db_utils import get_connection, release_connection, close_pool
from engine.state import state
from graph.engine import GraphLoader, RoadmapEngine
from engine.search import SkillSearch
from api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skillmap")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "datasets", "skills_graph.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SkillMap engine...")

    # 1. Init DB tables
    init_db()
    state.db = get_connection()

    # 2. Load graph
    loader = GraphLoader(DATASET_PATH)
    state.graph = loader.load()
    logger.info(f"Loaded graph: {len(state.graph.nodes)} skills, {sum(len(v) for v in state.graph.adj.values())} edges")

    # 3. Persist skills to PostgreSQL
    load_skills_to_db(state.graph)
    with state.db.cursor() as cur:
        cur.execute("DELETE FROM roadmap_cache")
    state.db.commit()
    logger.info("Skills stored in PostgreSQL")

    # 4. Roadmap engine
    state.roadmap_engine = RoadmapEngine(state.graph)

    # 5. Search engine
    all_skills = get_all_skills(state.db)
    state.matcher = SkillSearch(all_skills)
    logger.info("Skill search engine ready (TF-IDF)")

    logger.info("SkillMap ready!")
    yield

    # Shutdown: release the long-lived connection, then close pool
    if state.db:
        release_connection(state.db)
        state.db = None
    close_pool()


app = FastAPI(
    title="SkillMap API",
    description="Deterministic learning roadmap engine powered by knowledge graphs.",
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────
# ✅ FINAL CORS CONFIG (FIXED)
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://skillmap-eight.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "skills_loaded": len(state.graph.nodes) if state.graph else 0,
        "matcher_method": "tfidf",
    }