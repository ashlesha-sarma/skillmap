import Head from "next/head";
import dynamic from "next/dynamic";
import { useStore } from "../hooks/useStore";
import Header from "../components/Header";
import Controls from "../components/Controls";
import Sidebar from "../components/Sidebar";
import EmptyState from "../components/EmptyState";

// React Flow must be client-only (uses browser APIs)
const GraphView = dynamic(() => import("../components/GraphView"), {
  ssr: false,
  loading: () => (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "center",
      height: "100%", color: "var(--text-muted)", fontSize: 14,
    }}>
      Loading graph engine...
    </div>
  ),
});

export default function Home() {
  const { roadmap, isLoadingRoadmap, roadmapError, selectedNode } = useStore();

  return (
    <>
      <Head>
        <title>SkillMap — Deterministic Learning Roadmaps</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="responsive-container" style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        overflow: "hidden",
        background: "var(--surface-0)",
      }}>
        {/* Header with search */}
        <Header />

        {/* Controls bar (only when roadmap loaded) */}
        {roadmap && <Controls />}

        {/* Main content area */}
        <div className="main-content-area" style={{ flex: 1, display: "flex", overflow: "hidden" }}>

          {/* Graph area */}
          <div style={{ flex: 1, position: "relative", overflow: "hidden" }}>
            {isLoadingRoadmap && (
              <div style={{
                position: "absolute", inset: 0, zIndex: 20,
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                background: "rgba(10,10,15,0.8)", backdropFilter: "blur(4px)",
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: "50%",
                  border: "2px solid var(--surface-3)",
                  borderTop: "2px solid var(--accent)",
                  animation: "spin 0.8s linear infinite",
                  marginBottom: 14,
                }} />
                <style>{`@keyframes spin { to { transform: rotate(360deg); }}`}</style>
                <div style={{ fontSize: 14, color: "var(--text-secondary)" }}>
                  Computing roadmap...
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>
                  Topological sort in progress
                </div>
              </div>
            )}

            {roadmapError && (
              <div style={{
                position: "absolute", inset: 0, zIndex: 10,
                display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                gap: 12,
              }}>
                <div style={{
                  background: "rgba(239,68,68,0.1)",
                  border: "1px solid rgba(239,68,68,0.3)",
                  borderRadius: 10,
                  padding: "20px 28px",
                  textAlign: "center",
                }}>
                  <div style={{ fontSize: 13, color: "#f87171", fontWeight: 600, marginBottom: 6 }}>
                    Error loading roadmap
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {roadmapError}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8 }}>
                    Make sure the backend is reachable
                  </div>
                </div>
              </div>
            )}
            {roadmap && !isLoadingRoadmap ? (
              <GraphView roadmap={roadmap} />
            ) : !isLoadingRoadmap && !roadmapError ? (
              <EmptyState />
            ) : null}
          </div>

          {/* Sidebar */}
          {selectedNode && (
            <div className="sidebar-responsive" style={{ width: 400, borderLeft: "1px solid var(--border)", background: "var(--surface-1)", zIndex: 10 }}>
              <Sidebar node={selectedNode} />
            </div>
          )}
        </div>
      </div>
    </>
  );
}
