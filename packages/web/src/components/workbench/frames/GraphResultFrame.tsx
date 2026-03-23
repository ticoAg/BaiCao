import { useCallback, useMemo, useRef, useState } from "react";
import { Button, Empty, Space, Tag, Typography } from "antd";
import { AimOutlined, BorderOutlined, MinusOutlined, PlusOutlined } from "@ant-design/icons";
import { NetworkGraph } from "@ant-design/graphs/es/components/network-graph";
import type { WorkbenchFrame } from "../../../types/workbench";
import type { GraphData, GraphEdge, GraphNode, SelectedItem } from "../../../types/graph";
import {
  defaultNodeStyle,
  nodeStyleMap,
  relTypeLabels,
} from "../../../types/graph";
import FrameChrome from "./FrameChrome";
import NodeDetail from "../../graph/NodeDetail";
import EdgeDetail from "../../graph/EdgeDetail";

const { Paragraph, Text } = Typography;

type GraphResultFrameProps = {
  frame: WorkbenchFrame;
  onDismiss?: () => void;
  onRerun?: () => void;
};

function getGraphEventId(event: unknown) {
  const target = event as {
    target?: { id?: string };
    item?: { id?: string };
    id?: string;
  };

  return target?.target?.id || target?.item?.id || target?.id;
}

function isGraphNode(value: unknown): value is GraphNode {
  return Boolean(
    value &&
      typeof value === "object" &&
      "name" in value &&
      "id" in value,
  );
}

function isGraphEdge(value: unknown): value is GraphEdge & {
  sourceName?: string;
  targetName?: string;
} {
  return Boolean(value && typeof value === "object");
}

function normalizeGraphData(payload: Record<string, unknown>): GraphData | null {
  const graphRecord =
    payload.graph && typeof payload.graph === "object"
      ? (payload.graph as Record<string, unknown>)
      : null;

  if (!graphRecord) {
    return null;
  }

  const center = isGraphNode(graphRecord.center) ? graphRecord.center : null;
  const nodes = Array.isArray(graphRecord.nodes)
    ? graphRecord.nodes.filter(isGraphNode)
    : [];
  const edges = Array.isArray(graphRecord.edges)
    ? graphRecord.edges.filter(isGraphEdge)
    : [];

  return {
    center,
    nodes,
    edges,
  };
}

const GraphResultFrame = ({ frame, onDismiss, onRerun }: GraphResultFrameProps) => {
  const graphRef = useRef<any | null>(null);
  const [selected, setSelected] = useState<SelectedItem | null>(null);
  const [hoveredItem, setHoveredItem] = useState<SelectedItem | null>(null);
  const graphData = useMemo(() => normalizeGraphData(frame.payload), [frame.payload]);
  const summary =
    typeof frame.payload.summary === "string" ? frame.payload.summary : "";
  const mode =
    typeof frame.payload.mode === "string" ? frame.payload.mode : "exact";
  const inspectorItem = hoveredItem ?? selected;
  const centerId =
    graphData?.center?.id || graphData?.center?.name || graphData?.nodes[0]?.id;

  const graphOverview = useMemo(() => {
    if (!graphData) {
      return {
        nodeCount: 0,
        edgeCount: 0,
        labelStats: [] as Array<{ key: string; count: number }>,
      };
    }

    const labelCounts = new Map<string, number>();

    graphData.nodes.forEach((node) => {
      const label = node.labels?.[0] || "Unknown";
      labelCounts.set(label, (labelCounts.get(label) ?? 0) + 1);
    });

    return {
      nodeCount: graphData.nodes.length,
      edgeCount: graphData.edges.length,
      labelStats: Array.from(labelCounts.entries()).map(([key, count]) => ({
        key,
        count,
      })),
    };
  }, [graphData]);

  const g6Data = useMemo(() => {
    if (!graphData) {
      return { nodes: [], edges: [] };
    }

    const computedCenterId = graphData.center?.id || graphData.center?.name;

    const nodes = graphData.nodes.map((node) => {
      const nodeId = node.id || node.name;
      const primaryLabel = node.labels?.[0] || "Unknown";
      const isCenter = nodeId === computedCenterId;
      const style = nodeStyleMap[primaryLabel] || defaultNodeStyle;

      return {
        id: nodeId,
        data: { ...node },
        style: {
          size: isCenter ? 76 : 52,
          fill: style.fill,
          stroke: style.stroke,
          lineWidth: isCenter ? 4 : 2,
          labelText: node.name,
          labelPlacement: "center" as const,
          labelFill: style.textColor,
          labelFontSize: isCenter ? 16 : 11,
          labelMaxWidth: isCenter ? 60 : 44,
          labelFontWeight: isCenter ? 700 : 500,
          shadowColor: style.stroke,
          shadowBlur: isCenter ? 22 : 12,
          shadowOffsetX: 0,
          shadowOffsetY: 4,
        },
      };
    });

    const edges = graphData.edges.map((edge, index) => ({
      id: edge.id || `workbench-edge-${index}`,
      source: edge.source?.id || edge.source?.name || "",
      target: edge.target?.id || edge.target?.name || "",
      data: {
        ...edge,
        sourceName: edge.source?.name,
        targetName: edge.target?.name,
      },
      style: {
        stroke: edge.status === "verified" ? "#8DCC93" : "#A5ABB6",
        lineWidth: edge.status === "verified" ? 2.5 : 1.5,
        labelText: relTypeLabels[edge.rel_type || ""] || edge.rel_type || "",
        labelFill: "#526158",
        labelFontSize: 12,
        labelBackground: true,
        labelBackgroundFill: "rgba(255,255,255,0.94)",
        labelBackgroundRadius: 999,
        endArrow: true,
        endArrowSize: 8,
      },
    }));

    return { nodes, edges };
  }, [graphData]);

  const clearSelection = useCallback(() => {
    setHoveredItem(null);
    setSelected(null);
  }, []);

  const handleReady = useCallback(
    (graph: any) => {
      if (!graphData) return;

      graphRef.current = graph;

      graph.on("canvas:click", clearSelection);

      graph.on("node:click", (event: unknown) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;

        const node = graphData.nodes.find((item) => (item.id || item.name) === nodeId);
        if (node) {
          setHoveredItem(null);
          setSelected({ type: "node", data: node });
        }
      });

      graph.on("edge:click", (event: unknown) => {
        const edgeId = getGraphEventId(event);
        if (!edgeId) return;

        const edgeModel = graph.getEdgeData?.(edgeId);
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

      graph.on("node:mouseenter", (event: unknown) => {
        const nodeId = getGraphEventId(event);
        if (!nodeId) return;

        const node = graphData.nodes.find((item) => (item.id || item.name) === nodeId);
        if (node) {
          setHoveredItem({ type: "node", data: node });
        }
      });

      graph.on("node:mouseleave", () => {
        setHoveredItem(null);
      });

      graph.on("edge:mouseenter", (event: unknown) => {
        const edgeId = getGraphEventId(event);
        if (!edgeId) return;

        const edgeModel = graph.getEdgeData?.(edgeId);
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
        } catch {
          // ignore graph fit failures
        }
      }, 120);
    },
    [clearSelection, graphData],
  );

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
    try {
      graphRef.current?.fitView?.();
    } catch {
      // ignore graph fit failures
    }
  }, []);

  const focusCenterNode = useCallback(() => {
    if (!centerId) return;

    try {
      graphRef.current?.focusElement?.(centerId, true);
    } catch {
      fitCanvas();
    }
  }, [centerId, fitCanvas]);

  return (
    <FrameChrome frame={frame} onDismiss={onDismiss} onRerun={onRerun}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.5fr) minmax(280px, 0.85fr)",
          gap: 0,
        }}
      >
        <div
          style={{
            minHeight: 420,
            padding: 18,
            borderRight: "1px solid rgba(15, 23, 42, 0.08)",
            background:
              "radial-gradient(circle at 24% 18%, rgba(228, 240, 233, 0.9) 0%, rgba(247, 250, 248, 0.92) 46%, rgba(240, 245, 242, 0.94) 100%)",
          }}
        >
          <Space size={[8, 8]} wrap style={{ marginBottom: 14, width: "100%", justifyContent: "space-between" }}>
            <Space size={[8, 8]} wrap>
              <Tag color="processing" style={{ borderRadius: 999, marginInlineEnd: 0 }}>
                图谱概览
              </Tag>
              <Tag style={{ borderRadius: 999, marginInlineEnd: 0 }}>{graphOverview.nodeCount} 节点</Tag>
              <Tag style={{ borderRadius: 999, marginInlineEnd: 0 }}>{graphOverview.edgeCount} 关系</Tag>
              <Tag style={{ borderRadius: 999, marginInlineEnd: 0 }}>{mode}</Tag>
            </Space>
            <Space.Compact>
              <Button aria-label="放大图谱" icon={<PlusOutlined />} onClick={() => zoomCanvas(0.15)} />
              <Button aria-label="缩小图谱" icon={<MinusOutlined />} onClick={() => zoomCanvas(-0.15)} />
              <Button aria-label="适应画布" icon={<BorderOutlined />} onClick={fitCanvas} />
              <Button aria-label="回到中心节点" icon={<AimOutlined />} onClick={focusCenterNode} />
            </Space.Compact>
          </Space>

          {summary ? (
            <Paragraph style={{ marginBottom: 14, color: "#526158" }}>{summary}</Paragraph>
          ) : null}

          {graphOverview.labelStats.length ? (
            <Space size={[8, 8]} wrap style={{ marginBottom: 14 }}>
              {graphOverview.labelStats.map((item) => (
                <Tag key={item.key} style={{ borderRadius: 999, marginInlineEnd: 0 }}>
                  {item.key} · {item.count}
                </Tag>
              ))}
            </Space>
          ) : null}

          {graphData?.nodes.length ? (
            <div style={{ height: 320 }}>
              <NetworkGraph data={g6Data} onReady={handleReady} />
            </div>
          ) : (
            <div style={{ height: 320, display: "grid", placeItems: "center" }}>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="当前结果没有可渲染的图谱节点。"
              />
            </div>
          )}
        </div>

        <div style={{ padding: 18, background: "#fcfdfc" }}>
          {inspectorItem?.type === "node" ? (
            <NodeDetail node={inspectorItem.data} />
          ) : null}
          {inspectorItem?.type === "edge" ? (
            <EdgeDetail edge={inspectorItem.data} />
          ) : null}
          {!inspectorItem ? (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={
                <Space direction="vertical" size={6}>
                  <Text strong style={{ color: "#203127" }}>
                    点击或悬停图谱元素查看详情
                  </Text>
                  <Text type="secondary">
                    Inspector 会跟随 hover 预览，点击后锁定到右侧。
                  </Text>
                </Space>
              }
            />
          ) : null}
        </div>
      </div>
    </FrameChrome>
  );
};

export default GraphResultFrame;
