import { useStore } from "../hooks/useStore";
import { getRoadmap } from "../hooks/api";
import type { Level } from "../types";

const LEVELS: { value: Level; label: string }[] = [
  { value: "beginner",     label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced",     label: "Advanced" },
];

export default function Controls() {
  const {
    roadmap, level, setLevel,
    setRoadmap, setIsLoadingRoadmap, setRoadmapError,
  } = useStore();

  if (!roadmap) return null;

  const handleLevelChange = async (newLevel: Level) => {
    if (newLevel === level) return;
    setLevel(newLevel);
    setIsLoadingRoadmap(true);
    setRoadmapError(null);
    try {
      const updated = await getRoadmap(roadmap.skill_id, newLevel);
      setRoadmap(updated);
    } catch (err: any) {
      setRoadmapError(err.message);
    } finally {
      setIsLoadingRoadmap(false);
    }
  };

  const visibleLevels = LEVELS.filter(l => roadmap.available_levels.includes(l.value));

  return (
    <div className="header-responsive animate-fade" style={{
      display: "flex",
      alignItems: "center",
      gap: 16,
      padding: "10px 24px",
      background: "var(--surface-1)",
      borderBottom: "1px solid var(--border)",
      flexWrap: "wrap",
    }}>
      {/* Dynamic Level selector */}
      {visibleLevels.length > 1 && (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="hide-mobile" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.1em", fontWeight: 600 }}>
            Depth
          </span>
          <div style={{ display: "flex", gap: 3, background: "var(--surface-2)", padding: 3, borderRadius: 8, border: "1px solid var(--border)" }}>
            {visibleLevels.map((l) => (
              <button
                key={l.value}
                onClick={() => handleLevelChange(l.value)}
                style={{
                  padding: "6px 16px",
                  borderRadius: "6px",
                  border: "none",
                  cursor: "pointer",
                  fontSize: 12,
                  fontWeight: level === l.value ? 700 : 500,
                  background: level === l.value ? "var(--accent)" : "transparent",
                  color: level === l.value ? "#fff" : "var(--text-secondary)",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                  fontFamily: "inherit",
                }}
              >
                {l.label}
              </button>
            ))}
          </div>
          <div className="hide-mobile" style={{ width: 1, height: 16, background: "var(--border)", marginLeft: 8 }} />
        </div>
      )}

      {/* Stats */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, background: "rgba(108, 99, 255, 0.08)", padding: "4px 10px", borderRadius: 6, border: "1px solid rgba(108, 99, 255, 0.15)" }}>
          <span style={{ color: "#8b85ff", fontWeight: 800, fontSize: 14 }}>{roadmap.total_steps}</span>
          <span style={{ color: "var(--text-muted)", fontSize: 10, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>steps</span>
        </div>
        <span className="hide-mobile" style={{ color: "var(--text-muted)", opacity: 0.3 }}>•</span>
        <span style={{ color: "var(--text-primary)", fontWeight: 600, fontSize: 13 }}>{roadmap.skill_title}</span>
      </div>
    </div>
  );
}
