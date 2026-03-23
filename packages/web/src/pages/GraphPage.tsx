import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Collapse,
  Divider,
  Drawer,
  Empty,
  message,
  Space,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import {
  AimOutlined,
  BorderOutlined,
  CloseOutlined,
  LeftOutlined,
  RightOutlined,
  MinusOutlined,
  PlusOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { NetworkGraph } from "@ant-design/graphs/es/components/network-graph";
import { useGraphWorkspace } from "../hooks/useGraphWorkspace";
import { graphApi } from "../services/api";
import {
  type GraphData,
  type GraphEdge,
  type GraphNode,
  labelColorMap,
  nodeStyleMap,
  defaultNodeStyle,
  relTypeLabels,
  type SelectedItem,
} from "../types/graph";
import NodeDetail from "../components/graph/NodeDetail";
import EdgeDetail from "../components/graph/EdgeDetail";
import GraphQueryPanel from "../components/graph/GraphQueryPanel";
import PathExplorer from "../components/graph/PathExplorer";

const { Text } = Typography;

function clampFilterPreview(filters: string[]) {
  return filters.slice(0, 3);
}

function remainingFilterCount(filters: string[]) {
  return Math.max(0, filters.length - clampFilterPreview(filters).length);
}

function getGraphEventId(event: any) {
  return event?.target?.id || event?.item?.id || event?.id;
}

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

function mergeGraphData(
  baseGraphData: GraphData | null,
  expansionGraphs: GraphData[],
): GraphData | null {
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

const graphContainerStyle = {
  width: "100%",
  height: "100%",
} as const;

const GraphCanvas = memo(function GraphCanvas({
  graphOptions,
  onReady,
}: {
  graphOptions: Record<string, unknown>;
  onReady: (graph: any) => void;
}) {
  return (
    <NetworkGraph
      {...graphOptions}
      onReady={onReady}
      containerStyle={graphContainerStyle}
    />
  );
});

const GraphPage = () => {
  const { name } = useParams<{ name: string }>();
  const {
    graphData,
    querySummary,
    mode,
    loading,
    selected,
    setSelected,
    depth,
    setDepth,
    refetch,
    runAdvancedQuery,
    resetAdvancedQuery,
  } = useGraphWorkspace(name);
  const [isQueryDrawerOpen, setIsQueryDrawerOpen] = useState(false);
  const [hoveredItem, setHoveredItem] = useState<SelectedItem | null>(null);
  const [isInspectorExpanded, setIsInspectorExpanded] = useState(true);
  const [showCanvasHint, setShowCanvasHint] = useState(true);
  const [expandedSubgraphs, setExpandedSubgraphs] = useState<Record<string, GraphData>>({});
  const graphRef = useRef<any | null>(null);
  const selectedRef = useRef(selected);
  const hoveredItemRef = useRef(hoveredItem);
  const displayGraphDataRef = useRef<GraphData | null>(graphData);
  const expandingNodeIdsRef = useRef(new Set<string>());

  useEffect(() => {
    selectedRef.current = selected;
  }, [selected]);

  useEffect(() => {
    hoveredItemRef.current = hoveredItem;
  }, [hoveredItem]);

  useEffect(() => {
    setExpandedSubgraphs({});
  }, [graphData]);

  const displayGraphData = useMemo(
    () => mergeGraphData(graphData, Object.values(expandedSubgraphs)),
    [expandedSubgraphs, graphData],
  );

  useEffect(() => {
    displayGraphDataRef.current = displayGraphData;
  }, [displayGraphData]);

  const nodeCount = displayGraphData?.nodes.length ?? 0;
  const edgeCount = displayGraphData?.edges.length ?? 0;
  const centerId =
    displayGraphData?.center?.id ||
    displayGraphData?.center?.name ||
    displayGraphData?.nodes[0]?.id;
  const currentTitle =
    mode === "advanced-query"
      ? "当前查询"
      : "当前图谱";
  const currentHeadline =
    mode === "advanced-query"
      ? "高级图谱查询结果"
      : name || displayGraphData?.center?.name || "等待一张图谱进入工作区";
  const currentSubline =
    mode === "advanced-query"
      ? `${querySummary?.matched_nodes ?? 0} 个命中节点 · ${querySummary?.matched_edges ?? 0} 条命中关系`
      : name
        ? `默认加载 ${name} 的知识图谱`
        : "打开查询器后，用条件构建一张新的探索图谱";
  const inspectorItem = hoveredItem ?? selected;

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

  const g6Data = useMemo(() => {
    if (!displayGraphData) {
      return { nodes: [], edges: [] };
    }

    const computedCenterId = displayGraphData.center?.id || displayGraphData.center?.name;

    const nodes = displayGraphData.nodes.map((node) => {
      const nodeId = node.id || node.name;
      const primaryLabel = node.labels?.[0] || "Unknown";
      const isCenter = nodeId === computedCenterId;
      const style = nodeStyleMap[primaryLabel] || defaultNodeStyle;

      return {
        id: nodeId,
        data: { ...node },
        style: {
          size: isCenter ? 72 : primaryLabel === "Herb" ? 54 : 40,
          fill: style.fill,
          stroke: style.stroke,
          lineWidth: isCenter ? 4 : 2,
          labelText: node.name,
          labelFontSize: isCenter ? 16 : 11,
          labelFill: style.textColor,
          labelFontWeight: isCenter ? 600 : 500,
          labelPlacement: "center" as const,
          labelMaxWidth: isCenter ? 58 : 42,
          shadowColor: style.stroke,
          shadowBlur: isCenter ? 24 : 12,
          shadowOffsetX: 0,
          shadowOffsetY: 4,
        },
      };
    });

    const edges = displayGraphData.edges.map((edge, index) => {
      const sourceId = edge.source?.id || edge.source?.name || "";
      const targetId = edge.target?.id || edge.target?.name || "";
      const isVerified = edge.status === "verified";

      return {
        id: edge.id || `edge-${index}`,
        source: sourceId,
        target: targetId,
        data: {
          ...edge,
          sourceName: edge.source?.name,
          targetName: edge.target?.name,
        },
        style: {
          stroke: isVerified ? "#8DCC93" : "#A5ABB6",
          lineWidth: isVerified ? 2.5 : 1.5,
          ...(isVerified ? {} : { lineDash: [4, 4] }),
          labelText: relTypeLabels[edge.rel_type || ""] || edge.rel_type || "",
          labelFontSize: 12,
          labelFill: "#555",
          labelBackground: true,
          labelBackgroundFill: "rgba(255, 255, 255, 0.92)",
          labelBackgroundOpacity: 1,
          labelBackgroundRadius: 999,
          endArrow: true,
          endArrowSize: 8,
          cursor: "pointer" as const,
        },
      };
    });

    return { nodes, edges };
  }, [displayGraphData]);

  const graphOptions = useMemo(
    () => ({
      data: g6Data,
      animation: true,
      behaviors: (behaviors: any[]) => [
        ...behaviors,
        { key: "drag-element", type: "drag-element" },
        { key: "zoom-canvas", type: "zoom-canvas" },
        { key: "drag-canvas", type: "drag-canvas" },
        { key: "hover-activate", type: "hover-activate" },
      ],
      plugins: [
        {
          key: "tooltip",
          type: "tooltip",
          getContent: (_evt: any, items: any[]) => {
            const item = items?.[0];
            if (!item) return "";
            const data = item.data || {};

            if (item.source !== undefined && item.target !== undefined) {
              const relLabel = relTypeLabels[data.rel_type || ""] || data.rel_type || "";
              return `<div style="padding:8px 12px;font-size:13px;line-height:1.6;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.12);background:rgba(255,255,255,0.95);backdrop-filter:blur(10px);">
                <b style="color:#203127">${relLabel}</b><br/>
                <span style="color:#666">${data.sourceName || "?"} <span style="color:#ccc">→</span> ${data.targetName || "?"}</span>
              </div>`;
            }

            const label = data.labels?.[0] || "";
            return `<div style="padding:8px 12px;font-size:13px;line-height:1.6;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.12);background:rgba(255,255,255,0.95);backdrop-filter:blur(10px);">
              <b style="color:#203127;font-size:14px;">${data.name || item.id}</b>
              ${label ? `<span style="margin-left:8px;padding:2px 8px;border-radius:999px;background:#f0f4f1;font-size:11px;color:#3D5A48">${label}</span>` : ""}
            </div>`;
          },
        },
      ],
    }),
    [g6Data],
  );

  const clearSelection = useCallback(() => {
    const hasHoveredItem = hoveredItemRef.current !== null;
    const hasSelectedItem = selectedRef.current !== null;

    if (!hasHoveredItem && !hasSelectedItem) {
      return;
    }

    if (hasHoveredItem) {
      setHoveredItem(null);
    }

    if (hasSelectedItem) {
      setSelected(null);
    }
  }, [setSelected]);

  const toggleNodeExpansion = useCallback(
    async (nodeId: string) => {
      if (!graphData) {
        return;
      }

      if (expandedSubgraphs[nodeId]) {
        setExpandedSubgraphs((current) => {
          const next = { ...current };
          delete next[nodeId];
          return next;
        });
        return;
      }

      if (expandingNodeIdsRef.current.has(nodeId)) {
        return;
      }

      expandingNodeIdsRef.current.add(nodeId);
      try {
        const expansionGraph = await graphApi.expandNodeGraph(nodeId, 1, 20);
        if (!expansionGraph.center) {
          return;
        }

        setExpandedSubgraphs((current) => ({
          ...current,
          [nodeId]: expansionGraph,
        }));
      } catch (error) {
        const detail =
          (error as any)?.response?.data?.detail || "节点展开失败，请稍后重试";
        message.error(detail);
      } finally {
        expandingNodeIdsRef.current.delete(nodeId);
      }
    },
    [expandedSubgraphs, graphData],
  );

  const handleReady = useCallback(
    (graph: any) => {
      graphRef.current = graph;

      graph.on("canvas:click", () => {
        clearSelection();
      });

      graph.on("node:click", (event: any) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;
        const node = displayGraphDataRef.current?.nodes.find(
          (item) => (item.id || item.name) === nodeId,
        );
        if (node) {
          setHoveredItem(null);
          setSelected({ type: "node", data: node });
        }
      });

      graph.on("node:dblclick", (event: any) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;
        void toggleNodeExpansion(nodeId);
      });

      graph.on("edge:click", (event: any) => {
        const edgeId = getGraphEventId(event);
        if (!edgeId) return;
        const edgeModel = graph.getEdgeData(edgeId);
        if (edgeModel?.data) {
          setHoveredItem(null);
          setSelected({
            type: "edge",
            data: {
              ...edgeModel.data,
              sourceName: edgeModel.data.sourceName || edgeModel.data.source?.name,
              targetName: edgeModel.data.targetName || edgeModel.data.target?.name,
            },
          });
        }
      });

      graph.on("node:mouseenter", (event: any) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;
        const node = displayGraphDataRef.current?.nodes.find(
          (item) => (item.id || item.name) === nodeId,
        );
        if (node) {
          setHoveredItem({ type: "node", data: node });
        }
      });

      graph.on("node:mouseleave", () => {
        setHoveredItem(null);
      });

      graph.on("edge:mouseenter", (event: any) => {
        const edgeId = getGraphEventId(event);
        if (!edgeId) return;
        const edgeModel = graph.getEdgeData(edgeId);
        if (edgeModel?.data) {
          setHoveredItem({
            type: "edge",
            data: {
              ...edgeModel.data,
              sourceName: edgeModel.data.sourceName || edgeModel.data.source?.name,
              targetName: edgeModel.data.targetName || edgeModel.data.target?.name,
            },
          });
        }
      });

      graph.on("edge:mouseleave", () => {
        setHoveredItem(null);
      });

      setTimeout(() => {
        try {
          graph.fitView?.();
          const currentZoom = graph.getZoom?.();
          if (typeof currentZoom === "number") {
            graph.zoomTo?.(Math.min(currentZoom * 1.24, currentZoom + 0.24));
          }
        } catch {
          // ignore graph fit failures
        }
      }, 200);
    },
    [clearSelection, setSelected, toggleNodeExpansion],
  );

  const handleRunAdvancedQuery = useCallback(
    async (request: any) => {
      await runAdvancedQuery(request);
      setIsQueryDrawerOpen(false);
    },
    [runAdvancedQuery],
  );

  const handleResetWorkspace = useCallback(() => {
    resetAdvancedQuery();
    clearSelection();
    setIsQueryDrawerOpen(false);
  }, [clearSelection, resetAdvancedQuery]);

  const zoomCanvas = useCallback((delta: number) => {
    const graph = graphRef.current;
    if (!graph) return;

    try {
      const currentZoom = graph.getZoom?.() ?? 1;
      graph.zoomTo?.(Math.max(0.3, currentZoom + delta));
    } catch {
      // ignore graph zoom failures
    }
  }, []);

  const fitCanvas = useCallback(() => {
    const graph = graphRef.current;
    if (!graph) return;

    try {
      graph.fitView?.();
    } catch {
      // ignore graph fit failures
    }
  }, []);

  const focusCenterNode = useCallback(() => {
    const graph = graphRef.current;
    if (!graph || !centerId) return;

    try {
      graph.focusElement?.(centerId, true);
    } catch {
      try {
        graph.fitView?.();
      } catch {
        // ignore fallback failures
      }
    }
  }, [centerId]);

  if (loading) {
    return (
      <div style={{ height: "calc(100vh - 64px)", display: "grid", placeItems: "center" }}>
        <Space direction="vertical" size="large" align="center">
          <Text type="secondary" style={{ fontSize: 16 }}>
            图谱工作区初始化加载中...
          </Text>
        </Space>
      </div>
    );
  }

  return (
    <div
      data-testid="graph-workspace"
      className="graph-workspace-shell"
      style={{
        position: "relative",
        height: "calc(100vh - 64px)",
        width: "100%",
        overflow: "hidden",
        background:
          "radial-gradient(circle at 24% 18%, rgba(228, 240, 233, 0.95) 0%, rgba(245, 248, 246, 0.92) 30%, rgba(238, 244, 240, 0.9) 100%)",
      }}
    >
      <div className="graph-canvas-surface" style={{ position: "absolute", inset: 18 }}>
        {displayGraphData ? (
          <GraphCanvas graphOptions={graphOptions} onReady={handleReady} />
        ) : (
          <div style={{ height: "100%", display: "grid", placeItems: "center" }}>
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Space direction="vertical" size={8}>
                  <Text strong style={{ color: "#23362B", fontSize: 16 }}>
                    等待一张新图谱进入工作区
                  </Text>
                  <Text type="secondary">
                    点击左上角“打开查询器”，用节点、关系和属性条件开始探索。
                  </Text>
                  <Button type="primary" size="large" onClick={() => setIsQueryDrawerOpen(true)}>
                    立即开始查询
                  </Button>
                </Space>
              }
            />
          </div>
        )}
      </div>

      <div className="graph-top-strip">
        <Space size={8} wrap>
          <Tag color={mode === "advanced-query" ? "processing" : "blue"} style={{ borderRadius: 999 }}>
            {mode === "advanced-query" ? "查询结果视图" : "默认图谱视图"}
          </Tag>
          <Tag className="graph-metric-tag" style={{ borderRadius: 999 }}>
            <span style={{ color: "#2e7d32", fontWeight: 700 }}>{nodeCount}</span> 节点
          </Tag>
          <Tag className="graph-metric-tag" style={{ borderRadius: 999 }}>
            <span style={{ color: "#2e7d32", fontWeight: 700 }}>{edgeCount}</span> 关系
          </Tag>
          {querySummary?.truncated ? (
            <Tag color="warning" style={{ borderRadius: 999 }}>
              结果已截断
            </Tag>
          ) : null}
        </Space>

        <Divider type="vertical" style={{ margin: "0 4px" }} />

        <Button
          type="primary"
          shape="round"
          icon={<ReloadOutlined />}
          onClick={refetch}
          disabled={mode === "idle"}
        >
          刷新
        </Button>
      </div>

      <div className="graph-query-entry-card">
        <Space size={[8, 8]} wrap style={{ width: "100%", justifyContent: "space-between" }}>
          <Tag className="graph-subtle-tag" style={{ marginInlineEnd: 0 }}>
            {currentTitle}
          </Tag>
          <Tag className="graph-subtle-tag graph-metric-tag" style={{ marginInlineEnd: 0 }}>
            查询深度 {depth} 层
          </Tag>
        </Space>
        <Text strong style={{ display: "block", marginTop: 10, fontSize: 22, color: "#203127", textWrap: "balance" }}>
          {currentHeadline}
        </Text>
        <Text type="secondary" style={{ display: "block", marginTop: 8, lineHeight: 1.6, textWrap: "pretty" }}>
          {currentSubline}
        </Text>

        {mode === "advanced-query" && querySummary ? (
          <div style={{ marginTop: 14 }}>
            <Space size={[8, 8]} wrap>
              {clampFilterPreview(querySummary.active_filters).map((filter) => (
                <Tag key={filter} className="graph-filter-tag" style={{ marginInlineEnd: 0 }}>
                  {filter}
                </Tag>
              ))}
              {remainingFilterCount(querySummary.active_filters) ? (
                <Tag className="graph-filter-tag graph-filter-tag--muted" style={{ marginInlineEnd: 0 }}>
                  +{remainingFilterCount(querySummary.active_filters)} 条筛选
                </Tag>
              ) : null}
            </Space>
          </div>
        ) : (
          <Space size={[8, 8]} wrap style={{ marginTop: 14 }}>
            <Tag className="graph-filter-tag graph-metric-tag" style={{ marginInlineEnd: 0 }}>
              {nodeCount} 个节点
            </Tag>
            <Tag className="graph-filter-tag graph-metric-tag" style={{ marginInlineEnd: 0 }}>
              {edgeCount} 条关系
            </Tag>
          </Space>
        )}

        <Space style={{ marginTop: 16 }} wrap>
          <Button type="primary" size="large" className="graph-primary-cta" onClick={() => setIsQueryDrawerOpen(true)}>
            打开查询器
          </Button>
          {mode === "advanced-query" ? (
            <>
              <Button size="large" onClick={() => setIsQueryDrawerOpen(true)}>编辑查询</Button>
              <Button size="large" onClick={handleResetWorkspace}>重置查询</Button>
            </>
          ) : null}
        </Space>
      </div>

      <div className="graph-floating-legend" data-testid="graph-floating-legend">
        <Text strong style={{ display: "block", marginBottom: 10, color: "#203127" }}>
          图例
        </Text>
        <div className="graph-legend-list">
          {Object.entries(labelColorMap).map(([label, color]) => (
            <span key={label} className="graph-legend-item">
              <span
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: color,
                  marginRight: 6,
                }}
              />
              {label}
            </span>
          ))}
        </div>
      </div>

      <div
        className={`graph-selection-shell ${isInspectorExpanded ? "" : "graph-selection-shell--collapsed"}`.trim()}
      >
        <Button
          type="default"
          shape="circle"
          className="graph-selection-toggle"
          aria-label={isInspectorExpanded ? "收起详情面板" : "展开详情面板"}
          aria-expanded={isInspectorExpanded}
          onClick={() => setIsInspectorExpanded((expanded) => !expanded)}
          icon={isInspectorExpanded ? <RightOutlined /> : <LeftOutlined />}
        />
        <div className="graph-selection-card" data-testid="graph-selection-card">
          {inspectorItem?.type === "node" ? <NodeDetail node={inspectorItem.data} /> : null}
          {inspectorItem?.type === "edge" ? <EdgeDetail edge={inspectorItem.data} /> : null}
          {!inspectorItem && displayGraphData ? (
            <div data-testid="graph-overview-panel">
              <Text type="secondary" style={{ fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                Overview
              </Text>
              <Text strong style={{ display: "block", fontSize: 18, color: "#203127", marginTop: 6 }}>
                图谱概览
              </Text>
              <Text type="secondary" style={{ display: "block", marginTop: 10, lineHeight: 1.7 }}>
                悬停节点或关系可即时预览详情，点击后会锁定在这里继续查看。
              </Text>

              <Space size={[8, 8]} wrap style={{ marginTop: 14 }}>
                <Tag className="graph-filter-tag graph-metric-tag" style={{ marginInlineEnd: 0 }}>
                  {nodeCount} 个节点
                </Tag>
                <Tag className="graph-filter-tag graph-metric-tag" style={{ marginInlineEnd: 0 }}>
                  {edgeCount} 条关系
                </Tag>
              </Space>

              {graphOverview.labelStats.length ? (
                <div className="graph-overview-section">
                  <Text strong style={{ color: "#203127" }}>
                    节点类型
                  </Text>
                  <div className="graph-overview-chip-list">
                    {graphOverview.labelStats.map(({ key, count }) => (
                      <Tag key={key} className="graph-filter-tag" style={{ marginInlineEnd: 0 }}>
                        {key} · {count}
                      </Tag>
                    ))}
                  </div>
                </div>
              ) : null}

              {graphOverview.relTypeStats.length ? (
                <div className="graph-overview-section">
                  <Text strong style={{ color: "#203127" }}>
                    关系类型
                  </Text>
                  <div className="graph-overview-chip-list">
                    {graphOverview.relTypeStats.map(({ key, count, label }) => (
                      <Tag key={key} className="graph-filter-tag" style={{ marginInlineEnd: 0 }}>
                        {key} · {count}
                        {label !== key ? ` · ${label}` : ""}
                      </Tag>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
          {!inspectorItem && !graphData ? (
            <div>
              <Text strong style={{ display: "block", fontSize: 16, color: "#203127" }}>
                图谱上下文详情
              </Text>
              <Text type="secondary" style={{ display: "block", marginTop: 10, lineHeight: 1.7 }}>
                生成图谱后，悬停或点击节点、关系，即可在这里查看上下文详情。
              </Text>
            </div>
          ) : null}
        </div>
      </div>

      {showCanvasHint && graphData ? (
        <div className="graph-canvas-hint" data-testid="graph-canvas-hint">
          <Text style={{ color: "#355244", lineHeight: 1.5 }}>
            滚轮缩放，拖拽平移，悬停预览详情
          </Text>
          <Button
            type="text"
            size="small"
            aria-label="关闭画布操作提示"
            className="graph-canvas-hint-close"
            icon={<CloseOutlined />}
            onClick={() => setShowCanvasHint(false)}
          />
        </div>
      ) : null}

      <div className="graph-canvas-toolbar">
        <Tooltip title="放大">
          <Button
            aria-label="放大"
            shape="circle"
            size="large"
            icon={<PlusOutlined />}
            onClick={() => zoomCanvas(0.1)}
          />
        </Tooltip>
        <Tooltip title="缩小">
          <Button
            aria-label="缩小"
            shape="circle"
            size="large"
            icon={<MinusOutlined />}
            onClick={() => zoomCanvas(-0.1)}
          />
        </Tooltip>
        <Tooltip title="适应画布">
          <Button aria-label="适应画布" size="large" shape="circle" icon={<BorderOutlined />} onClick={fitCanvas} />
        </Tooltip>
        <Tooltip title="回到中心节点">
          <Button aria-label="回到中心节点" size="large" shape="circle" icon={<AimOutlined />} onClick={focusCenterNode} />
        </Tooltip>
      </div>

      <Drawer
        title="图谱查询器"
        placement="left"
        width="min(420px, calc(100vw - 24px))"
        open={isQueryDrawerOpen}
        onClose={() => setIsQueryDrawerOpen(false)}
        destroyOnClose={false}
      >
        {mode === "advanced-query" && querySummary ? (
          <div style={{ marginBottom: 20 }}>
            <Text strong style={{ display: "block", fontSize: 16, color: "#203127" }}>
              当前查询
            </Text>
            <Text type="secondary" style={{ display: "block", marginTop: 4 }}>
              {querySummary.matched_nodes} 个命中节点 · {querySummary.matched_edges} 条命中关系
            </Text>
            <Space size={[8, 8]} wrap style={{ marginTop: 10 }}>
              {querySummary.active_filters.map((filter) => (
                <Tag key={filter} style={{ borderRadius: 999 }}>
                  {filter}
                </Tag>
              ))}
            </Space>
          </div>
        ) : null}

        <GraphQueryPanel
          depth={depth}
          loading={loading}
          onSubmit={handleRunAdvancedQuery}
          onDepthChange={setDepth}
          onReset={handleResetWorkspace}
        />

        <Divider style={{ margin: "24px 0" }} />

        <Collapse
          ghost
          defaultActiveKey={[]}
          items={[
            {
              key: "path-explorer",
              label: <Text strong style={{ fontSize: 14, color: "#2e7d32" }}>路径探索</Text>,
              children: <PathExplorer />,
            },
          ]}
        />
      </Drawer>
    </div>
  );
};

export default GraphPage;
