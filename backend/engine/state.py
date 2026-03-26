"""
Application state — shared singletons initialized at startup.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graph.engine import SkillGraph, RoadmapEngine
    from engine.search import SkillSearch


class AppState:
    graph: "SkillGraph" = None
    roadmap_engine: "RoadmapEngine" = None
    matcher: "SkillSearch" = None
    db: Any = None  # psycopg2 connection


state = AppState()
