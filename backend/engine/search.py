"""
Skill Search Engine — SkillMap
Pure-Python TF-IDF implementation. 
100% deterministic, no AI/randomness.
"""
from __future__ import annotations
import re
import math
from collections import defaultdict

def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())

class SkillSearch:
    """TF-IDF Search Engine for skills.
    Matches skill title, description, and tags with specific weighting.
    """
    def __init__(self, skills: list[dict]):
        self.skills = skills
        self.skills_map = {s["id"]: s for s in skills}
        self.idf = {}
        self.vectors = {}
        self._build_index()

    def _build_index(self):
        """Build TF-IDF index for skill title+description+tags."""
        docs = {}
        for s in self.skills:
            # We weight the title twice as much to prefer direct name hits
            text = f"{s['title']} {s['title']} {s.get('description', '')} {' '.join(s.get('career_tags', []))}"
            docs[s["id"]] = tokenize(text)

        # Calculate IDF
        N = len(docs)
        df = defaultdict(int)
        for tokens in docs.values():
            for t in set(tokens):
                df[t] += 1
        
        self.idf = {t: math.log((N + 1) / (cnt + 1)) + 1 for t, cnt in df.items()}

        # Build TF-IDF vectors
        for doc_id, tokens in docs.items():
            tf = defaultdict(int)
            for t in tokens:
                tf[t] += 1
            
            vec = {t: (c / len(tokens)) * self.idf.get(t, 0) for t, c in tf.items()}
            # L2 Normalize
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.vectors[doc_id] = {t: v / norm for t, v in vec.items()}

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Return top-k results based on cosine similarity."""
        tokens = tokenize(query)
        if not tokens: return []

        # Build Query Vector
        tf = defaultdict(int)
        for t in tokens:
            tf[t] += 1
        
        q_vec = {t: (c / len(tokens)) * self.idf.get(t, 0) for t, c in tf.items()}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        q_vec = {t: v / q_norm for t, v in q_vec.items()}

        # Compute Similarity
        scores = []
        for doc_id, d_vec in self.vectors.items():
            score = sum(q_vec.get(t, 0) * d_vec.get(t, 0) for t in q_vec)
            if score > 0:
                scores.append((doc_id, score))

        # Sort and Format
        scores.sort(key=lambda x: -x[1])
        results = []
        for doc_id, score in scores[:top_k]:
            skill = self.skills_map[doc_id]
            results.append({
                "id": doc_id,
                "title": skill["title"],
                "category": skill.get("category", ""),
                "score": round(score, 4),
                "match_method": "tfidf",
            })
        return results

    def exact_match(self, query: str) -> str | None:
        """Return exact skill ID if query matches a skill title or ID directly."""
        q = query.lower().strip()
        for skill in self.skills:
            if skill["title"].lower() == q or skill["id"].lower() == q:
                return skill["id"]
        return None
