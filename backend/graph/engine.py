"""
Graph Engine — SkillMap
Implements DAG construction, cycle detection, and Kahn's topological sort.
100% deterministic. No LLM calls.
"""
from __future__ import annotations
import json
import sqlite3
from collections import deque, defaultdict
from pathlib import Path
from typing import Any


# ──────────────────────────────────────────────
# Graph Data Structures
# ──────────────────────────────────────────────

class SkillNode:
    __slots__ = ("id", "title", "category", "description", "resources", "career_tags", "prerequisites")

    def __init__(self, data: dict):
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.category: str = data["category"]
        self.description: str = data["description"]
        self.resources: list[dict] = data.get("resources", [])
        self.career_tags: list[str] = data.get("career_tags", [])
        self.prerequisites: list[str] = data.get("prerequisites", [])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "resources": self.resources,
            "career_tags": self.career_tags,
            "prerequisites": self.prerequisites,
        }


class SkillGraph:
    """Directed Acyclic Graph of skills.
    Nodes = skills; Edges = prerequisite relationships (A→B means A is prereq for B).
    """

    def __init__(self):
        self.nodes: dict[str, SkillNode] = {}
        # adjacency list: node_id → set of nodes that depend on it
        self.adj: dict[str, set[str]] = defaultdict(set)
        # reverse adjacency: node_id → its prerequisites
        self.rev_adj: dict[str, set[str]] = defaultdict(set)

    def add_node(self, node: SkillNode) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adj:
            self.adj[node.id] = set()
        if node.id not in self.rev_adj:
            self.rev_adj[node.id] = set()

    def add_edge(self, prereq_id: str, skill_id: str) -> None:
        """Edge: prereq_id → skill_id (prereq must come before skill)."""
        self.adj[prereq_id].add(skill_id)
        self.rev_adj[skill_id].add(prereq_id)

    def validate_dag(self) -> tuple[bool, list[str]]:
        """Kahn's algorithm to detect cycles. Returns (is_valid, cycle_info)."""
        in_degree = {nid: len(prereqs) for nid, prereqs in self.rev_adj.items()}
        for nid in self.nodes:
            if nid not in in_degree:
                in_degree[nid] = 0

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            node = queue.popleft()
            visited_count += 1
            for dependent in self.adj.get(node, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if visited_count == len(self.nodes):
            return True, []
        else:
            # Find nodes still in cycles
            cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
            return False, cycle_nodes

    def get_subgraph(self, target_id: str) -> "SkillGraph":
        """Extract the subgraph of all prerequisites needed for target skill."""
        if target_id not in self.nodes:
            raise ValueError(f"Skill '{target_id}' not found in graph")

        visited = set()
        subgraph = SkillGraph()

        def dfs(nid: str):
            if nid in visited:
                return
            visited.add(nid)
            node = self.nodes[nid]
            subgraph.add_node(node)
            for prereq_id in node.prerequisites:
                if prereq_id in self.nodes:
                    dfs(prereq_id)
                    subgraph.add_edge(prereq_id, nid)

        dfs(target_id)
        return subgraph

    def get_subgraph_from_nodes(self, node_ids: list[str]) -> "SkillGraph":
        """Build a subgraph from a specific list of node IDs."""
        subgraph = SkillGraph()
        ids = set(node_ids)
        for nid in node_ids:
            if nid in self.nodes:
                subgraph.add_node(self.nodes[nid])
        
        for nid in node_ids:
            for dep in self.adj.get(nid, set()):
                if dep in ids:
                    subgraph.add_edge(nid, dep)
        return subgraph

    def topological_sort(self) -> list[str]:
        """Kahn's algorithm topological sort. Returns ordered list of node IDs."""
        in_degree = {nid: 0 for nid in self.nodes}
        for nid in self.nodes:
            for prereq in self.rev_adj.get(nid, set()):
                if prereq in self.nodes:
                    in_degree[nid] += 1

        # Process zero in-degree first; break ties by node id (determinism)
        queue = deque(sorted([nid for nid, deg in in_degree.items() if deg == 0]))
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            # Process in sorted order for determinism
            for dependent in sorted(self.adj.get(node, set())):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    def transitive_reduction(self) -> None:
        """Remove redundant edges (A→C when A→B→C exists) for clean UI."""
        for src in list(self.nodes.keys()):
            direct_deps = set(self.adj.get(src, set()))
            redundant = set()
            for dep in direct_deps:
                # Find all nodes reachable from dep (excluding dep itself)
                reachable = self._reachable_from(dep, exclude_start=True)
                redundant |= direct_deps & reachable
            for r in redundant:
                self.adj[src].discard(r)
                self.rev_adj[r].discard(src)

    def _reachable_from(self, start: str, exclude_start: bool = False) -> set[str]:
        visited = set()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            for nxt in self.adj.get(node, set()):
                queue.append(nxt)
        if exclude_start:
            visited.discard(start)
        return visited


# ──────────────────────────────────────────────
# Graph Loader
# ──────────────────────────────────────────────

class GraphLoader:
    """Loads skill data from datasets, normalizes, and builds DAG."""

    def __init__(self, dataset_path: str):
        self.dataset_path = Path(dataset_path)

    def load(self) -> SkillGraph:
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        graph = SkillGraph()
        skills_data = data["skills"]

        # Pass 1: add all nodes
        for skill_id, skill_data in skills_data.items():
            skill_data["id"] = skill_id
            node = SkillNode(skill_data)
            graph.add_node(node)

        # Pass 2: add edges
        for skill_id, skill_data in skills_data.items():
            for prereq_id in skill_data.get("prerequisites", []):
                if prereq_id in graph.nodes:
                    graph.add_edge(prereq_id, skill_id)

        # Validate
        is_valid, cycle_nodes = graph.validate_dag()
        if not is_valid:
            raise ValueError(f"Graph contains cycles involving: {cycle_nodes}")

        return graph


# ──────────────────────────────────────────────
# Roadmap Engine
# ──────────────────────────────────────────────

class RoadmapEngine:
    """Generates deterministic, ordered learning roadmaps from the DAG.

    Provides a comprehensive prerequisite graph for any target skill,
    ordered topologically to ensure foundational concepts are presented first.
    """

    def __init__(self, graph: SkillGraph):
        self.graph = graph

    def generate(self, skill_id: str, level: str = "advanced") -> dict[str, Any]:
        """Generate a deterministic learning roadmap.

        Levels:
        - beginner: Foundations (First 3 layers) + Goal
        - intermediate: Intermediate depth (First 6 layers) + Goal
        - advanced: Full Graph
        """
        if skill_id not in self.graph.nodes:
            raise ValueError(f"Unknown skill: {skill_id}")

        target_node = self.graph.nodes[skill_id]
        full_subgraph = self.graph.get_subgraph(skill_id)
        layers = self._compute_layers(full_subgraph)
        max_layer = max(layers.values()) if layers else 0

        # Calculate nodes for each level based on documentation filters
        # beginner=3 layers, intermediate=6 layers, advanced=all
        beginner_ids = [nid for nid, lay in layers.items() if lay < 3 or nid == skill_id]
        intermediate_ids = [nid for nid, lay in layers.items() if lay < 6 or nid == skill_id]
        
        # Available levels logic based on actual complexity
        avail = ["beginner"]
        if max_layer >= 3 and len(intermediate_ids) > len(beginner_ids):
            avail.append("intermediate")
        if max_layer >= 6 and len(layers) > len(intermediate_ids):
            avail.append("advanced")
        elif "advanced" not in avail and len(layers) > len(beginner_ids):
            # Ensure advanced is present if it's actually larger than beginner
            if "intermediate" not in avail:
                avail.append("advanced")
            else:
                avail.append("advanced")
        
        # Deduplicate and ensure at least one level
        avail = sorted(list(set(avail)), key=lambda x: ["beginner", "intermediate", "advanced"].index(x))

        if level not in avail:
            level = avail[-1]

        # Filter nodes based on requested level
        if level == "beginner":
            visible_ids = beginner_ids
        elif level == "intermediate":
            visible_ids = intermediate_ids
        else:
            visible_ids = list(layers.keys())

        # Topological sort for order
        sub_subgraph = full_subgraph.get_subgraph_from_nodes(visible_ids)
        ordered_ids = sub_subgraph.topological_sort()

        nodes = []
        for i, nid in enumerate(ordered_ids):
            node = full_subgraph.nodes[nid]
            nodes.append({
                **node.to_dict(),
                "order": i + 1,
                "is_target": nid == skill_id,
            })

        # Compute bridged edges for connectivity
        edges = self._compute_visible_edges(full_subgraph, ordered_ids)

        return {
            "skill_id": skill_id,
            "skill_title": target_node.title,
            "category": target_node.category,
            "level": level,
            "available_levels": avail,
            "total_steps": len(nodes),
            "nodes": nodes,
            "edges": edges,
        }

    def _compute_visible_edges(self, full_subgraph: SkillGraph, visible_ids: list[str]) -> list[dict]:
        """Ensures connectivity by bridging gaps between visible nodes."""
        visible_set = set(visible_ids)
        edges = []
        
        for nid in visible_ids:
            # Find nearest visible ancestors
            visited = {nid}
            queue = deque([nid])
            while queue:
                curr = queue.popleft()
                for prereq in full_subgraph.rev_adj.get(curr, set()):
                    if prereq in visited: continue
                    visited.add(prereq)
                    if prereq in visible_set:
                        edges.append({"source": prereq, "target": nid})
                    else:
                        queue.append(prereq)
        
        # Deduplicate edges (multiple paths might lead to the same ancestor)
        unique_edges = []
        seen = set()
        for e in edges:
            pair = (e["source"], e["target"])
            if pair not in seen:
                unique_edges.append(e)
                seen.add(pair)
        return unique_edges

    def _compute_layers(self, subgraph: SkillGraph) -> dict[str, int]:
        """Compute the layer of each node (longest path from any root)."""
        in_degree = {nid: 0 for nid in subgraph.nodes}
        for nid in subgraph.nodes:
            for prereq in subgraph.rev_adj.get(nid, set()):
                if prereq in subgraph.nodes:
                    in_degree[nid] += 1

        layers = {nid: 0 for nid in subgraph.nodes}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])

        while queue:
            node = queue.popleft()
            for dep in subgraph.adj.get(node, set()):
                if dep not in subgraph.nodes: continue
                layers[dep] = max(layers[dep], layers[node] + 1)
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
        return layers
