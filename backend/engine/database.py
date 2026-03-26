"""
Database layer — PostgreSQL storage for skills, roadmaps, and embeddings cache.
Uses connection pool from db_utils. Every connection is returned to the pool
in a finally block to prevent leaks.
"""
import json
import hashlib

import psycopg2
import psycopg2.extras

from engine.db_utils import get_connection, release_connection


# ──────────────────────────────────────────────
# Schema initialisation
# ──────────────────────────────────────────────

def init_db() -> None:
    """Create all tables if they don't exist."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_user")
            current_user = cur.fetchone()[0]
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{current_user}" AUTHORIZATION "{current_user}"')
            cur.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id            TEXT PRIMARY KEY,
                    title         TEXT NOT NULL,
                    category      TEXT NOT NULL,
                    description   TEXT NOT NULL,
                    resources     TEXT NOT NULL,
                    career_tags   TEXT NOT NULL,
                    prerequisites TEXT NOT NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS skill_edges (
                    prereq_id   TEXT NOT NULL REFERENCES skills(id),
                    skill_id    TEXT NOT NULL REFERENCES skills(id),
                    PRIMARY KEY (prereq_id, skill_id)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roadmap_cache (
                    cache_key    TEXT PRIMARY KEY,
                    skill_id     TEXT NOT NULL,
                    level        TEXT NOT NULL,
                    roadmap_json TEXT NOT NULL,
                    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    skill_id    TEXT PRIMARY KEY,
                    embedding   BYTEA NOT NULL,
                    model_hash  TEXT NOT NULL
                );
            """)

            # Indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_skill    ON skill_edges(skill_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_edges_prereq   ON skill_edges(prereq_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_cache_skill    ON roadmap_cache(skill_id);")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


# ──────────────────────────────────────────────
# Bulk loading
# ──────────────────────────────────────────────

def load_skills_to_db(graph) -> None:
    """Populate DB from SkillGraph object (clears existing data first)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM skill_edges")
            cur.execute("DELETE FROM skills")

            for node in graph.nodes.values():
                cur.execute(
                    """INSERT INTO skills (id, title, category, description,
                                          resources, career_tags, prerequisites)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET
                           title=EXCLUDED.title,
                           category=EXCLUDED.category,
                           description=EXCLUDED.description,
                           resources=EXCLUDED.resources,
                           career_tags=EXCLUDED.career_tags,
                           prerequisites=EXCLUDED.prerequisites""",
                    (
                        node.id,
                        node.title,
                        node.category,
                        node.description,
                        json.dumps(node.resources),
                        json.dumps(node.career_tags),
                        json.dumps(node.prerequisites),
                    ),
                )

            for src, targets in graph.adj.items():
                for tgt in targets:
                    cur.execute(
                        """INSERT INTO skill_edges (prereq_id, skill_id)
                           VALUES (%s, %s)
                           ON CONFLICT DO NOTHING""",
                        (src, tgt),
                    )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        release_connection(conn)


# ──────────────────────────────────────────────
# Read helpers (accept a connection from the caller)
# ──────────────────────────────────────────────

def get_all_skills(conn) -> list[dict]:
    """Return all skills (lightweight summary)."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, title, category, career_tags FROM skills ORDER BY category, title"
        )
        rows = cur.fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "career_tags": json.loads(row["career_tags"]),
        }
        for row in rows
    ]


def get_skill(conn, skill_id: str) -> dict | None:
    """Return full skill record or None."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM skills WHERE id = %s", (skill_id,))
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["category"],
        "description": row["description"],
        "resources": json.loads(row["resources"]),
        "career_tags": json.loads(row["career_tags"]),
        "prerequisites": json.loads(row["prerequisites"]),
    }


# ──────────────────────────────────────────────
# Roadmap cache
# ──────────────────────────────────────────────

def cache_roadmap(conn, skill_id: str, level: str, roadmap: dict) -> None:
    """Upsert a roadmap into the cache."""
    key = hashlib.sha256(f"{skill_id}:{level}".encode()).hexdigest()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO roadmap_cache (cache_key, skill_id, level, roadmap_json)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (cache_key)
                   DO UPDATE SET roadmap_json = EXCLUDED.roadmap_json,
                                 created_at   = NOW()""",
                (key, skill_id, level, json.dumps(roadmap)),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_cached_roadmap(conn, skill_id: str, level: str) -> dict | None:
    """Return cached roadmap or None."""
    key = hashlib.sha256(f"{skill_id}:{level}".encode()).hexdigest()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT roadmap_json FROM roadmap_cache WHERE cache_key = %s", (key,)
        )
        row = cur.fetchone()
    if row:
        return json.loads(row["roadmap_json"])
    return None


# ──────────────────────────────────────────────
# Embeddings
# ──────────────────────────────────────────────

def store_embedding(conn, skill_id: str, embedding_bytes: bytes, model_hash: str) -> None:
    """Upsert a skill embedding."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO embeddings (skill_id, embedding, model_hash)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (skill_id)
                   DO UPDATE SET embedding  = EXCLUDED.embedding,
                                 model_hash = EXCLUDED.model_hash""",
                (skill_id, psycopg2.Binary(embedding_bytes), model_hash),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_all_embeddings(conn, model_hash: str) -> dict[str, bytes]:
    """Return all embeddings for a given model hash."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT skill_id, embedding FROM embeddings WHERE model_hash = %s",
            (model_hash,),
        )
        rows = cur.fetchall()
    return {row["skill_id"]: bytes(row["embedding"]) for row in rows}
