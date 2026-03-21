import { useCallback, useMemo, useEffect } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from "reactflow";
import "reactflow/dist/style.css";
import type { Roadmap, RoadmapNode } from "../types";
import SkillNode from "./SkillNode";
import { useStore } from "../hooks/useStore";

interface Props {
  roadmap: Roadmap;
}

// Simple hierarchical layout without dagre
function computeLayout(
  nodes: RoadmapNode[],
  edges: { source: string; target: string }[]
): Record<string, { x: number; y: number }> {
  // Build level assignment: BFS from roots
  const inDegree: Record<string, number> = {};
  const adjMap: Record<string, string[]> = {};

  for (const n of nodes) {
    inDegree[n.id] = 0;
    adjMap[n.id] = [];
  }
  for (const e of edges) {
    inDegree[e.target] = (inDegree[e.target] || 0) + 1;
    if (!adjMap[e.source]) adjMap[e.source] = [];
    adjMap[e.source].push(e.target);
  }

  // BFS level assignment
  const level: Record<string, number> = {};
  const queue: string[] = [];
  for (const n of nodes) {
    if (inDegree[n.id] === 0) {
      level[n.id] = 0;
      queue.push(n.id);
    }
  }

  let qi = 0;
  while (qi < queue.length) {
    const cur = queue[qi++];
    for (const next of adjMap[cur] || []) {
      level[next] = Math.max(level[next] ?? 0, (level[cur] ?? 0) + 1);
      queue.push(next);
    }
  }

  // Group by level
  const byLevel: Record<number, string[]> = {};
  for (const n of nodes) {
    const lv = level[n.id] ?? 0;
    if (!byLevel[lv]) byLevel[lv] = [];
    byLevel[lv].push(n.id);
  }

  const positions: Record<string, { x: number; y: number }> = {};
  const NODE_W = 220;
  const NODE_H = 120;

  for (const [lv, ids] of Object.entries(byLevel)) {
    const lvNum = Number(lv);
    const count = ids.length;
    const totalWidth = count * NODE_W;
    ids.forEach((id, i) => {
      positions[id] = {
        x: i * NODE_W - totalWidth / 2 + NODE_W / 2,
        y: lvNum * NODE_H,
      };
    });
  }

  return positions;
}

const nodeTypes = { skillNode: SkillNode };

const categoryColors: Record<string, string> = {
  tech: "#6c63ff",
  science: "#22d3ee",
  business: "#f59e0b",
  creative: "#ec4899",
  soft_skills: "#10b981",
};

export default function GraphView({ roadmap }: Props) {
  const { selectedNode, setSelectedNode } = useStore();
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);



  // Effect 1: Handle initial roadmap load and layout
  useEffect(() => {
    const { nodes, edges } = roadmap;
    const positions = computeLayout(nodes, edges);

    const newNodes = nodes.map((skill) => ({
      id: skill.id,
      type: "skillNode",
      position: positions[skill.id] || { x: 0, y: 0 },
      data: {
        skill,
        isSelected: selectedNode?.id === skill.id,
        onSelect: setSelectedNode,
      },
    }));

    const newEdges = edges.map((e) => {
      const sourceNode = nodes.find((n) => n.id === e.source);
      const color = categoryColors[sourceNode?.category || "tech"] || "#6c63ff";
      return {
        id: `${e.source}->${e.target}`,
        source: e.source,
        target: e.target,
        type: "smoothstep",
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color,
          width: 12,
          height: 12,
        },
        style: {
          stroke: `${color}60`,
          strokeWidth: 1.5,
        },
        animated: selectedNode?.id === e.target || selectedNode?.id === e.source,
      };
    });

    setRfNodes(newNodes);
    setRfEdges(newEdges);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roadmap, setRfNodes, setRfEdges, setSelectedNode]);

  // Effect 2: Handle selection changes without resetting positions
  useEffect(() => {
    setRfNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          isSelected: selectedNode?.id === node.id,
        },
      }))
    );

    setRfEdges((eds) =>
      eds.map((edge) => ({
        ...edge,
        animated: selectedNode?.id === edge.target || selectedNode?.id === edge.source,
      }))
    );
  }, [selectedNode, setRfNodes, setRfEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: any) => {
      setSelectedNode(node.data.skill);
    },
    [setSelectedNode]
  );

  return (
    <div style={{ width: "100%", height: "100%", background: "var(--surface-0)" }}>
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="#ffffff08"
        />
        <Controls
          showInteractive={false}
          style={{ bottom: 20, left: 20 }}
        />
        <MiniMap
          nodeColor={(node) => {
            const skill = (node.data as any)?.skill as RoadmapNode;
            return categoryColors[skill?.category || "tech"] + "80";
          }}
          maskColor="rgba(10,10,15,0.7)"
          style={{ bottom: 20, right: 20, width: 140, height: 90 }}
        />

        {/* Stats panel */}
        <Panel position="top-left">
          <div style={{
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "8px 12px",
            fontSize: 12,
            color: "var(--text-secondary)",
            display: "flex",
            gap: 16,
          }}>
            <span>
              <span style={{ color: "#8b85ff", fontWeight: 600 }}>{roadmap.nodes.length}</span> steps
            </span>
            <span>
              <span style={{ color: "#8b85ff", fontWeight: 600 }}>{roadmap.edges.length}</span> dependencies
            </span>
            <span style={{ textTransform: "capitalize" }}>
              {roadmap.level}
            </span>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
