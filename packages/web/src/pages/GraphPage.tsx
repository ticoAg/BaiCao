import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Drawer, Space, Tag, Typography } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { graphApi } from "../services/api";
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage";
import type { GraphData, GraphEdge, GraphNode } from "../types/graph";
import { defaultNodeStyle, labelColorMap, nodeStyleMap, relTypeLabels } from "../types/graph";
import GraphCanvasWorkspace from "../components/graph/GraphCanvasWorkspace";
import GraphInspectorPanel from "../components/graph/GraphInspectorPanel";
import GraphMetadataSidebar from "../components/graph/GraphMetadataSidebar";
import GraphQueryPanel from "../components/graph/GraphQueryPanel";

const { Text } = Typography;
const EXPANSION_RING_RADIUS = 170;
const INITIAL_RELAX_MS = 1100;
const EXPANSION_RELAX_MS = 650;
const RELAX_LAYOUT_START_DELAY_MS = 120;

type GraphPoint = { x: number; y: number };
type ForceLayoutBurstOptions = {
  centerViewportAfter?: boolean;
};

function getGraphNodeId(node: Pick<GraphNode, "id" | "name">) {
  return node.id || node.name;
}

function getGraphEdgeId(edge: GraphEdge) {
  return [
    edge.source?.id || edge.source?.name || "",
    edge.rel_type || "",
    edge.target?.id || edge.target?.name || "",
  ].join("::");
}

function mergeGraphData(baseGraphData: GraphData | null, expansionGraphs: GraphData[]): GraphData | null {
  if (!baseGraphData) {
    return null;
  }

  const nodeMap = new Map<string, GraphNode>();
  const edgeMap = new Map<string, GraphEdge>();

  const registerGraph = (graph: GraphData) => {
    graph.nodes.forEach((node) => {
      nodeMap.set(getGraphNodeId(node), node);
    });
    graph.edges.forEach((edge) => {
      edgeMap.set(getGraphEdgeId(edge), edge);
    });
  };

  registerGraph(baseGraphData);
  expansionGraphs.forEach(registerGraph);

  return {
    center: baseGraphData.center,
    nodes: Array.from(nodeMap.values()),
    edges: Array.from(edgeMap.values()),
  };
}

function getGraphEventId(event: any) {
  return event?.target?.id || event?.item?.id || event?.id;
}

function readGraphNodePosition(graph: any, nodeId: string): GraphPoint | null {
  const nodeData = graph.getNodeData?.(nodeId) as
    | {
        data?: Record<string, unknown>;
        style?: { x?: unknown; y?: unknown };
      }
    | undefined;
  const x = nodeData?.data?.x ?? nodeData?.style?.x;
  const y = nodeData?.data?.y ?? nodeData?.style?.y;
  if (Number.isFinite(x) && Number.isFinite(y)) {
    return { x: x as number, y: y as number };
  }

  const position = graph.getElementPosition?.(nodeId);
  if (position && Number.isFinite(position.x) && Number.isFinite(position.y)) {
    return { x: position.x, y: position.y };
  }

  return null;
}

function captureRenderedNodePositions(graph: any): Record<string, GraphPoint> {
  const nodes = (graph.getNodeData?.() ?? []) as Array<{ id?: unknown }>;

  return nodes.reduce((acc, node) => {
    const nodeId = String(node?.id ?? "");
    if (!nodeId) {
      return acc;
    }

    const position = readGraphNodePosition(graph, nodeId);
    if (position) {
      acc[nodeId] = position;
    }

    return acc;
  }, {} as Record<string, GraphPoint>);
}

function createExpansionPositions(
  anchorId: string,
  expansionGraph: GraphData,
  currentPositions: Record<string, GraphPoint>,
): Record<string, GraphPoint> {
  const anchorPosition = currentPositions[anchorId] ?? { x: 0, y: 0 };
  const newNodes = expansionGraph.nodes.filter((node) => !currentPositions[getGraphNodeId(node)]);

  if (!newNodes.length) {
    return {};
  }

  return newNodes.reduce<Record<string, GraphPoint>>((acc, node, index) => {
    const angle = (-Math.PI / 2) + (Math.PI * 2 * index) / newNodes.length;
    const nodeId = getGraphNodeId(node);

    acc[nodeId] = {
      x: anchorPosition.x + Math.cos(angle) * EXPANSION_RING_RADIUS,
      y: anchorPosition.y + Math.sin(angle) * EXPANSION_RING_RADIUS,
    };

    return acc;
  }, {});
}

const GraphPage = () => {
  const { name } = useParams<{ name: string }>();
  const {
    graphData,
    querySummary,
    mode,
    loading,
    scene,
    metaSummary,
    metaLabels,
    metaRelationshipTypes,
    metaPropertyKeys,
    metaSchema,
    metaLoading,
    metaError,
    selectedItem,
    highlightedLabel,
    highlightedRelationshipType,
    highlightLabel,
    highlightRelationshipType,
    selectNode,
    selectEdge,
    clearSelection,
    depth,
    setDepth,
    refetch,
    runAdvancedQuery,
    resetAdvancedQuery,
  } = useGraphWorkbenchPage(name);
  const [isQueryDrawerOpen, setIsQueryDrawerOpen] = useState(false);
  const [expandedSubgraphs, setExpandedSubgraphs] = useState<Record<string, GraphData>>({});
  const [nodePositions, setNodePositions] = useState<Record<string, GraphPoint>>({});
  const [freeNodeIds, setFreeNodeIds] = useState<Record<string, true>>({});
  const graphRef = useRef<any | null>(null);
  const boundGraphRef = useRef<any | null>(null);
  const displayGraphDataRef = useRef<GraphData | null>(null);
  const expandedSubgraphsRef = useRef<Record<string, GraphData>>({});
  const nodePositionsRef = useRef<Record<string, GraphPoint>>({});
  const forceLayoutStarterTimerRef = useRef<number | null>(null);
  const forceLayoutTimerRef = useRef<number | null>(null);
  const viewportCenterTimerRef = useRef<number | null>(null);
  const layoutCycleRef = useRef(0);
  const autoFitSceneKeyRef = useRef<string | null>(null);
  const pendingViewportCenterSceneKeyRef = useRef<string | null>(null);
  const didRunInitialLayoutRef = useRef<string | null>(null);
  const displayGraphData = useMemo(
    () => mergeGraphData(graphData, Object.values(expandedSubgraphs)),
    [expandedSubgraphs, graphData],
  );

  useEffect(() => {
    displayGraphDataRef.current = displayGraphData;
  }, [displayGraphData]);

  useEffect(() => {
    expandedSubgraphsRef.current = expandedSubgraphs;
  }, [expandedSubgraphs]);

  useEffect(() => {
    nodePositionsRef.current = nodePositions;
  }, [nodePositions]);

  const baseGraphSceneKey = useMemo(() => {
    if (!graphData) {
      return null;
    }

    const nodeKey = graphData.nodes.map((node) => getGraphNodeId(node)).join("|");
    const edgeKey = graphData.edges.map((edge) => getGraphEdgeId(edge)).join("|");
    return `${nodeKey}::${edgeKey}`;
  }, [graphData]);

  useEffect(() => {
    if (!baseGraphSceneKey) {
      return;
    }

    setExpandedSubgraphs((current) => (Object.keys(current).length ? {} : current));
    setNodePositions((current) => (Object.keys(current).length ? {} : current));
    setFreeNodeIds((current) => (Object.keys(current).length ? {} : current));
    if (Object.keys(nodePositionsRef.current).length) {
      nodePositionsRef.current = {};
    }
    autoFitSceneKeyRef.current = null;
    pendingViewportCenterSceneKeyRef.current = null;
    didRunInitialLayoutRef.current = null;

    if (forceLayoutStarterTimerRef.current) {
      window.clearTimeout(forceLayoutStarterTimerRef.current);
      forceLayoutStarterTimerRef.current = null;
    }

    if (forceLayoutTimerRef.current) {
      window.clearTimeout(forceLayoutTimerRef.current);
      forceLayoutTimerRef.current = null;
    }

    if (viewportCenterTimerRef.current) {
      window.clearTimeout(viewportCenterTimerRef.current);
      viewportCenterTimerRef.current = null;
    }

    graphRef.current?.stopLayout?.();
  }, [baseGraphSceneKey]);

  const graphOverview = useMemo(() => {
    if (!displayGraphData) {
      return {
        labelStats: [] as Array<{ key: string; count: number }>,
        relTypeStats: [] as Array<{ key: string; count: number; label: string }>,
      };
    }

    const labelCounts = new Map<string, number>();
    const relTypeCounts = new Map<string, number>();

    displayGraphData.nodes.forEach((node) => {
      const label = node.labels?.[0] || "Unknown";
      labelCounts.set(label, (labelCounts.get(label) ?? 0) + 1);
    });

    displayGraphData.edges.forEach((edge) => {
      const relType = edge.rel_type || "UNKNOWN";
      relTypeCounts.set(relType, (relTypeCounts.get(relType) ?? 0) + 1);
    });

    return {
      labelStats: Array.from(labelCounts.entries()).map(([key, count]) => ({ key, count })),
      relTypeStats: Array.from(relTypeCounts.entries()).map(([key, count]) => ({
        key,
        count,
        label: relTypeLabels[key] || key,
      })),
    };
  }, [displayGraphData]);

  const graphOptions = useMemo(() => {
    if (!displayGraphData) {
      return { data: { nodes: [], edges: [] } };
    }

    const hasPinnedLayout = Object.keys(nodePositions).length > 0;

    return {
      data: {
        nodes: displayGraphData.nodes.map((node) => {
          const primaryLabel = node.labels?.[0] || "Unknown";
          const nodeId = node.id || node.name;
          const style = nodeStyleMap[primaryLabel] || defaultNodeStyle;
          const opacity = highlightedLabel && primaryLabel !== highlightedLabel ? 0.24 : 1;
          const position = nodePositions[nodeId];
          const isFree = Boolean(freeNodeIds[nodeId]);
          const shouldPin = Boolean(position) && !isFree;
          const nodeData: Record<string, unknown> = {
            ...node,
            ...(position ? { x: position.x, y: position.y } : {}),
            ...(shouldPin && position ? { fx: position.x, fy: position.y } : {}),
          };

          return {
            id: nodeId,
            data: nodeData,
            style: {
              size: 48,
              fill: style.fill,
              stroke: style.stroke,
              lineWidth: 2,
              labelText: node.name,
              labelFill: style.textColor,
              labelPlacement: "center" as const,
              opacity,
              ...(position ? { x: position.x, y: position.y } : {}),
            },
          };
        }),
        edges: displayGraphData.edges.map((edge, index) => ({
          id: edge.id || `edge-${index}`,
          source: edge.source?.id || edge.source?.name || "",
          target: edge.target?.id || edge.target?.name || "",
          data: {
            ...edge,
            sourceName: edge.source?.name,
            targetName: edge.target?.name,
          },
          style: {
            stroke: "#8DCC93",
            lineWidth: 2,
            labelText: relTypeLabels[edge.rel_type || ""] || edge.rel_type || "",
            labelFill: "#555",
            endArrow: true,
            opacity:
              highlightedRelationshipType &&
              edge.rel_type !== highlightedRelationshipType
                ? 0.2
                : 1,
          },
        })),
      },
      behaviors: [
        { key: "zoom-canvas", type: "zoom-canvas" },
        { key: "drag-canvas", type: "drag-canvas" },
        { key: "drag-element", type: "drag-element" },
      ],
      layout: hasPinnedLayout
        ? ({ type: "preset" } as const)
        : {
            type: "d3-force" as const,
            alpha: 1,
            alphaMin: 0.08,
            alphaDecay: 0.12,
            velocityDecay: 0.35,
            nodeSize: 48,
            center: { x: 0, y: 0, strength: 0.05 },
            collide: { radius: 56, strength: 0.8, iterations: 1 },
            manyBody: { strength: -220, distanceMin: 40, distanceMax: 900 },
            link: { distance: 140, strength: 0.9, iterations: 1 },
            x: {},
            y: {},
          },
      animation: !hasPinnedLayout,
    };
  }, [displayGraphData, freeNodeIds, highlightedLabel, highlightedRelationshipType, nodePositions]);

  const openQueryDrawer = useCallback(() => {
    setIsQueryDrawerOpen(true);
  }, []);

  const closeQueryDrawer = useCallback(() => {
    setIsQueryDrawerOpen(false);
  }, []);

  const getCanvasCenter = useCallback((graph: any) => {
    const [width = 0, height = 0] = graph.getSize?.() ?? [];
    return {
      x: width / 2,
      y: height / 2,
    };
  }, []);

  const stopForceLayoutSimulation = useCallback(() => {
    layoutCycleRef.current += 1;

    if (forceLayoutStarterTimerRef.current) {
      window.clearTimeout(forceLayoutStarterTimerRef.current);
      forceLayoutStarterTimerRef.current = null;
    }

    if (forceLayoutTimerRef.current) {
      window.clearTimeout(forceLayoutTimerRef.current);
      forceLayoutTimerRef.current = null;
    }

    if (viewportCenterTimerRef.current) {
      window.clearTimeout(viewportCenterTimerRef.current);
      viewportCenterTimerRef.current = null;
    }

    graphRef.current?.stopLayout?.();
  }, []);

  const freezeLayout = useCallback(() => {
    stopForceLayoutSimulation();
    setFreeNodeIds({});
  }, [stopForceLayoutSimulation]);

  const runForceLayoutBurst = useCallback(
    (durationMs: number, options?: ForceLayoutBurstOptions) => {
      const graph = graphRef.current;
      if (!graph) {
        return;
      }

      stopForceLayoutSimulation();

      const currentCycle = layoutCycleRef.current + 1;
      layoutCycleRef.current = currentCycle;
      const center = getCanvasCenter(graph);

      graph.layout?.({
        type: "d3-force",
        alpha: 1,
        alphaMin: 0.08,
        alphaDecay: 0.12,
        velocityDecay: 0.35,
        nodeSize: 48,
        center: { x: center.x, y: center.y, strength: 0.08 },
        collide: { radius: 56, strength: 0.8, iterations: 1 },
        manyBody: { strength: -220, distanceMin: 40, distanceMax: 900 },
        link: { distance: 140, strength: 0.9, iterations: 1 },
        x: { x: center.x, strength: 0.04 },
        y: { y: center.y, strength: 0.04 },
        animation: true,
      });

      forceLayoutTimerRef.current = window.setTimeout(() => {
        if (layoutCycleRef.current !== currentCycle) {
          return;
        }

        graph.stopLayout?.();

        const positions = captureRenderedNodePositions(graph);
        if (Object.keys(positions).length) {
          setNodePositions((current) => ({ ...current, ...positions }));
        }

        setFreeNodeIds({});
        if (options?.centerViewportAfter && autoFitSceneKeyRef.current !== baseGraphSceneKey) {
          pendingViewportCenterSceneKeyRef.current = baseGraphSceneKey;
        }
        forceLayoutTimerRef.current = null;
      }, durationMs);
    },
    [baseGraphSceneKey, getCanvasCenter, stopForceLayoutSimulation],
  );

  const scheduleForceLayoutBurst = useCallback(
    (durationMs: number, options?: ForceLayoutBurstOptions) => {
      if (forceLayoutStarterTimerRef.current) {
        window.clearTimeout(forceLayoutStarterTimerRef.current);
      }

      forceLayoutStarterTimerRef.current = window.setTimeout(() => {
        forceLayoutStarterTimerRef.current = null;
        runForceLayoutBurst(durationMs, options);
      }, RELAX_LAYOUT_START_DELAY_MS);
    },
    [runForceLayoutBurst],
  );

  useEffect(() => () => stopForceLayoutSimulation(), [stopForceLayoutSimulation]);

  useEffect(() => {
    if (!baseGraphSceneKey || !Object.keys(nodePositions).length) {
      return;
    }

    if (pendingViewportCenterSceneKeyRef.current !== baseGraphSceneKey) {
      return;
    }

    if (viewportCenterTimerRef.current) {
      window.clearTimeout(viewportCenterTimerRef.current);
    }

    viewportCenterTimerRef.current = window.setTimeout(() => {
      viewportCenterTimerRef.current = null;

      if (autoFitSceneKeyRef.current === baseGraphSceneKey) {
        return;
      }

      autoFitSceneKeyRef.current = baseGraphSceneKey;
      pendingViewportCenterSceneKeyRef.current = null;
      graphRef.current?.fitCenter?.();
    }, 180);
  }, [baseGraphSceneKey, nodePositions]);

  useEffect(() => {
    const graph = graphRef.current;
    if (!graph || !baseGraphSceneKey || !displayGraphData) {
      return;
    }

    if (didRunInitialLayoutRef.current === baseGraphSceneKey) {
      return;
    }

    if (Object.keys(nodePositionsRef.current).length) {
      didRunInitialLayoutRef.current = baseGraphSceneKey;
      return;
    }

    didRunInitialLayoutRef.current = baseGraphSceneKey;
    scheduleForceLayoutBurst(INITIAL_RELAX_MS, {
      centerViewportAfter: true,
    });
  }, [baseGraphSceneKey, displayGraphData, scheduleForceLayoutBurst]);

  const handleReady = useCallback(
    (graph: any) => {
      graphRef.current = graph;

      if (boundGraphRef.current === graph) {
        return;
      }

      boundGraphRef.current = graph;
      (window as any).__BAICAO_GRAPH__ = graph;

      if (
        baseGraphSceneKey &&
        didRunInitialLayoutRef.current !== baseGraphSceneKey &&
        !Object.keys(nodePositionsRef.current).length
      ) {
        didRunInitialLayoutRef.current = baseGraphSceneKey;
        scheduleForceLayoutBurst(INITIAL_RELAX_MS, {
          centerViewportAfter: true,
        });
      }

      graph.on("canvas:click", () => {
        freezeLayout();
        clearSelection();
      });

      graph.on("node:click", (event: any) => {
        freezeLayout();
        const nodeId = getGraphEventId(event);
        const node = displayGraphDataRef.current?.nodes.find(
          (item) => (item.id || item.name) === nodeId,
        );
        if (node) {
          selectNode(node);
        }
      });

      graph.on("edge:click", (event: any) => {
        freezeLayout();
        const edgeId = getGraphEventId(event);
        const edgeModel = graph.getEdgeData?.(edgeId);
        if (edgeModel?.data) {
          selectEdge(edgeModel.data);
        }
      });

      graph.on("node:dblclick", async (event: any) => {
        freezeLayout();
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;

        if (expandedSubgraphsRef.current[nodeId]) {
          setExpandedSubgraphs((current) => {
            const next = { ...current };
            delete next[nodeId];
            return next;
          });
          return;
        }

        const expansionGraph = await graphApi.expandNodeGraph(nodeId, 1, 20);
        if (!expansionGraph.center) return;

        const currentGraph = graphRef.current;
        const fallbackPositions = currentGraph ? captureRenderedNodePositions(currentGraph) : {};
        const stablePositions = {
          ...fallbackPositions,
          ...nodePositionsRef.current,
        };

        const nextExpansionPositions = createExpansionPositions(
          nodeId,
          expansionGraph,
          stablePositions,
        );
        const newlyAddedNodeIds = Object.keys(nextExpansionPositions);

        setNodePositions((current) => {
          const next = { ...current };

          Object.entries(fallbackPositions).forEach(([id, position]) => {
            if (!next[id]) {
              next[id] = position;
            }
          });

          Object.entries(nextExpansionPositions).forEach(([id, position]) => {
            next[id] = position;
          });

          return next;
        });

        setExpandedSubgraphs((current) => ({
          ...current,
          [nodeId]: expansionGraph,
        }));

        if (newlyAddedNodeIds.length) {
          setFreeNodeIds((current) => {
            const next = { ...current };
            newlyAddedNodeIds.forEach((id) => {
              next[id] = true;
            });
            return next;
          });

          scheduleForceLayoutBurst(EXPANSION_RELAX_MS);
        }
      });

      graph.on("node:dragend", (event: any) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) {
          return;
        }

        freezeLayout();

        const position = readGraphNodePosition(graph, nodeId);
        if (!position) return;

        setNodePositions((current) => ({
          ...current,
          [nodeId]: position,
        }));
      });
    },
    [baseGraphSceneKey, clearSelection, freezeLayout, scheduleForceLayoutBurst, selectEdge, selectNode],
  );

  if (loading) {
    return (
      <div style={{ height: "calc(100vh - 64px)", display: "grid", placeItems: "center" }}>
        <Text type="secondary">图谱工作台加载中...</Text>
      </div>
    );
  }

  return (
    <div
      data-testid="graph-workbench-page"
      style={{
        height: "calc(100vh - 64px)",
        display: "grid",
        gridTemplateColumns: "288px minmax(0, 1fr) 312px",
        gap: 16,
        padding: 16,
        background:
          "linear-gradient(180deg, rgba(244, 248, 245, 0.96) 0%, rgba(239, 245, 241, 0.98) 100%)",
        boxSizing: "border-box",
      }}
    >
      <GraphMetadataSidebar
        summary={metaSummary}
        labels={metaLabels}
        relationshipTypes={metaRelationshipTypes}
        propertyKeys={metaPropertyKeys}
        schema={metaSchema}
        loading={metaLoading}
        error={metaError}
        onHighlightLabel={highlightLabel}
        onHighlightRelationshipType={highlightRelationshipType}
      />

      <div
        style={{
          position: "relative",
          minWidth: 0,
          minHeight: 0,
          padding: 14,
          border: "1px solid rgba(163, 185, 169, 0.45)",
          borderRadius: 28,
          background:
            "linear-gradient(180deg, rgba(252, 253, 252, 0.98) 0%, rgba(247, 250, 248, 0.96) 100%)",
          boxShadow:
            "0 1px 0 rgba(255, 255, 255, 0.75) inset, 0 18px 44px rgba(27, 56, 36, 0.08), 0 2px 10px rgba(27, 56, 36, 0.06)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: 26,
            left: 26,
            right: 26,
            zIndex: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            pointerEvents: "none",
          }}
        >
          <div style={{ pointerEvents: "auto" }}>
            <Text strong style={{ fontSize: 20, color: "#203127" }}>
              {mode === "advanced-query" ? "当前查询" : "当前图谱"}
            </Text>
            <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 10 }}>
              <Tag>{displayGraphData?.nodes.length ?? 0} 个节点</Tag>
              <Tag>{displayGraphData?.edges.length ?? 0} 条关系</Tag>
              {scene.truncated || querySummary?.truncated ? <Tag color="warning">结果已截断</Tag> : null}
            </Space>
          </div>
            <Space style={{ pointerEvents: "auto" }}>
            <Button onClick={openQueryDrawer}>打开查询器</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch}>
              刷新
            </Button>
          </Space>
        </div>

        <GraphCanvasWorkspace
          graphOptions={graphOptions}
          onReady={handleReady}
          hasGraphData={Boolean(displayGraphData)}
          onOpenQuery={openQueryDrawer}
        />
      </div>

      <GraphInspectorPanel
        selectedItem={selectedItem}
        nodeCount={displayGraphData?.nodes.length ?? 0}
        relationshipCount={displayGraphData?.edges.length ?? 0}
        labelStats={graphOverview.labelStats}
        relTypeStats={graphOverview.relTypeStats}
        onHighlightLabel={highlightLabel}
        onHighlightRelationshipType={highlightRelationshipType}
      />

      <Drawer
        title="图谱查询器"
        placement="left"
        open={isQueryDrawerOpen}
        onClose={closeQueryDrawer}
        width={420}
      >
        <GraphQueryPanel
          depth={depth}
          loading={loading}
          onDepthChange={setDepth}
          onSubmit={async (request) => {
            await runAdvancedQuery(request);
            closeQueryDrawer();
          }}
          onReset={() => {
            resetAdvancedQuery();
            closeQueryDrawer();
          }}
        />
      </Drawer>
    </div>
  );
};

export default GraphPage;
