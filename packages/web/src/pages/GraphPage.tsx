import { useCallback, useMemo, useRef, useState } from "react";
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
  const graphRef = useRef<any | null>(null);
  const displayGraphData = useMemo(
    () => mergeGraphData(graphData, Object.values(expandedSubgraphs)),
    [expandedSubgraphs, graphData],
  );

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

    return {
      data: {
        nodes: displayGraphData.nodes.map((node) => {
          const primaryLabel = node.labels?.[0] || "Unknown";
          const nodeId = node.id || node.name;
          const style = nodeStyleMap[primaryLabel] || defaultNodeStyle;
          const opacity = highlightedLabel && primaryLabel !== highlightedLabel ? 0.24 : 1;

          return {
            id: nodeId,
            data: { ...node },
            style: {
              size: 48,
              fill: style.fill,
              stroke: style.stroke,
              lineWidth: 2,
              labelText: node.name,
              labelFill: style.textColor,
              labelPlacement: "center" as const,
              opacity,
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
      animation: true,
    };
  }, [displayGraphData, highlightedLabel, highlightedRelationshipType]);

  const handleReady = useCallback(
    (graph: any) => {
      graphRef.current = graph;

      graph.on("canvas:click", () => {
        clearSelection();
      });

      graph.on("node:click", (event: any) => {
        const nodeId = getGraphEventId(event);
        const node = displayGraphData?.nodes.find((item) => (item.id || item.name) === nodeId);
        if (node) {
          selectNode(node);
        }
      });

      graph.on("edge:click", (event: any) => {
        const edgeId = getGraphEventId(event);
        const edgeModel = graph.getEdgeData?.(edgeId);
        if (edgeModel?.data) {
          selectEdge(edgeModel.data);
        }
      });

      graph.on("node:dblclick", async (event: any) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;

        if (expandedSubgraphs[nodeId]) {
          setExpandedSubgraphs((current) => {
            const next = { ...current };
            delete next[nodeId];
            return next;
          });
          return;
        }

        const expansionGraph = await graphApi.expandNodeGraph(nodeId, 1, 20);
        if (!expansionGraph.center) return;

        setExpandedSubgraphs((current) => ({
          ...current,
          [nodeId]: expansionGraph,
        }));
      });

      setTimeout(() => {
        graph.fitView?.();
      }, 50);
    },
    [clearSelection, displayGraphData, expandedSubgraphs, selectEdge, selectNode],
  );

  if (loading) {
    return (
      <div style={{ height: "calc(100vh - 64px)", display: "grid", placeItems: "center" }}>
        <Text type="secondary">图谱工作台加载中...</Text>
      </div>
    );
  }

  return (
    <div data-testid="graph-workbench-page" style={{ height: "calc(100vh - 64px)", display: "grid", gridTemplateColumns: "320px minmax(0, 1fr) 360px" }}>
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

      <div style={{ position: "relative", minWidth: 0 }}>
        <div
          style={{
            position: "absolute",
            top: 16,
            left: 16,
            right: 16,
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
            <Button onClick={() => setIsQueryDrawerOpen(true)}>打开查询器</Button>
            <Button icon={<ReloadOutlined />} onClick={refetch}>
              刷新
            </Button>
          </Space>
        </div>

        <GraphCanvasWorkspace
          graphOptions={graphOptions}
          onReady={handleReady}
          hasGraphData={Boolean(displayGraphData)}
          onOpenQuery={() => setIsQueryDrawerOpen(true)}
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
        onClose={() => setIsQueryDrawerOpen(false)}
        width={420}
      >
        <GraphQueryPanel
          depth={depth}
          loading={loading}
          onDepthChange={setDepth}
          onSubmit={async (request) => {
            await runAdvancedQuery(request);
            setIsQueryDrawerOpen(false);
          }}
          onReset={() => {
            resetAdvancedQuery();
            setIsQueryDrawerOpen(false);
          }}
        />
      </Drawer>
    </div>
  );
};

export default GraphPage;
