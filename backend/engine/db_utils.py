"""
Database utilities — PostgreSQL connection pool for SkillMap.
"""
import os
from dotenv import load_dotenv

load_dotenv()

import psycopg2
from psycopg2 import pool

_connection_pool = None


def _init_pool():
    """Initialize the connection pool (called once at module load)."""
    global _connection_pool
    try:
        _connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("PG_HOST", "localhost"),
            port=int(os.getenv("PG_PORT", "5432")),
            dbname=os.getenv("PG_DB", "skillmap"),
            user=os.getenv("PG_USER", "skillmap_user"),
            password=os.getenv("PG_PASSWORD", ""),
        )
        print("PostgreSQL connection pool created (min=1, max=10)")
    except psycopg2.Error as e:
        print(f"Failed to create PostgreSQL connection pool: {e}")
        raise


# Initialize pool on import
_init_pool()


def get_connection():
    """Fetch a connection from the pool."""
    if _connection_pool is None:
        raise RuntimeError("Connection pool is not initialized")
    return _connection_pool.getconn()


def release_connection(conn):
    """Return a connection to the pool."""
    if _connection_pool is not None and conn is not None:
        _connection_pool.putconn(conn)


def close_pool():
    """Close all connections in the pool (call at app shutdown)."""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        print("PostgreSQL connection pool closed")
