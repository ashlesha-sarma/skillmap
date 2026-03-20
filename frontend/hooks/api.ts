import type { SearchResult, Roadmap, SkillSummary, SkillDetail, Level } from "../types";

// Ensure the base URL ends with /api (normalized for local and production)
let API_ROOT = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
if (API_ROOT.endsWith("/")) API_ROOT = API_ROOT.slice(0, -1);
if (!API_ROOT.endsWith("/api")) API_ROOT += "/api";

const BASE = API_ROOT;

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function searchSkills(query: string, limit = 8): Promise<SearchResult[]> {
  const q = encodeURIComponent(query.trim());
  return apiFetch<SearchResult[]>(`/skills/search?q=${q}&limit=${limit}`);
}

export async function getAllSkills(): Promise<SkillSummary[]> {
  return apiFetch<SkillSummary[]>("/skills/all");
}

export async function getRoadmap(skillId: string, level: Level = "advanced"): Promise<Roadmap> {
  return apiFetch<Roadmap>(`/roadmap/${skillId}?level=${level}`);
}

export async function getSkillDetail(skillId: string): Promise<SkillDetail> {
  return apiFetch<SkillDetail>(`/skills/${skillId}`);
}
