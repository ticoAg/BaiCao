import { useCallback, useMemo, useRef, useState } from "react";
import { Button, Empty, Space, Tag, Typography } from "antd";
import { AimOutlined, BorderOutlined, MinusOutlined, PlusOutlined } from "@ant-design/icons";
import type { WorkbenchFrame } from "../../../types/workbench";
import type { GraphData, GraphEdge, GraphNode, SelectedItem } from "../../../types/graph";
import {
  getGraphNodeLabelDisplayName,
  relTypeLabels,
} from "../../../types/graph";
import FrameChrome from "./FrameChrome";
import NodeDetail from "../../graph/NodeDetail";
import EdgeDetail from "../../graph/EdgeDetail";
import MiniGraphCanvas from "../../graph/MiniGraphCanvas";
import type { VizNode, VizRelationship } from "../../../lib/graph-viz";

const { Paragraph, Text } = Typography;

type GraphResultFrameProps = {
  frame: WorkbenchFrame;
  onDismiss?: () => void;
  onRerun?: () => void;
};

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
  const [selected, setSelected] = useState<SelectedItem | null>(null);
  const [hoveredItem, setHoveredItem] = useState<SelectedItem | null>(null);
  const graphData = useMemo(() => normalizeGraphData(frame.payload), [frame.payload]);
  const summary =
    typeof frame.payload.summary === "string" ? frame.payload.summary : "";
  const mode =
    typeof frame.payload.mode === "string" ? frame.payload.mode : "exact";
  const inspectorItem = hoveredItem ?? selected;

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

  const handleNodeClick = useCallback((vizNode: VizNode) => {
    setHoveredItem(null);
    setSelected({ type: "node", data: vizNode.data });
  }, []);

  const handleEdgeClick = useCallback((vizRel: VizRelationship) => {
    setHoveredItem(null);
    setSelected({
      type: "edge",
      data: {
        ...vizRel.data,
        sourceName: vizRel.data.source?.name,
        targetName: vizRel.data.target?.name,
      },
    });
  }, []);

  const handleNodeHover = useCallback((vizNode: VizNode | null) => {
    if (vizNode) {
      setHoveredItem({ type: "node", data: vizNode.data });
    } else {
      setHoveredItem(null);
    }
  }, []);

  const handleEdgeHover = useCallback((vizRel: VizRelationship | null) => {
    if (vizRel) {
      setHoveredItem({
        type: "edge",
        data: {
          ...vizRel.data,
          sourceName: vizRel.data.source?.name,
          targetName: vizRel.data.target?.name,
        },
      });
    } else {
      setHoveredItem(null);
    }
  }, []);

  const handleCanvasClick = useCallback(() => {
    setHoveredItem(null);
    setSelected(null);
  }, []);

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
          </Space>

          {summary ? (
            <Paragraph style={{ marginBottom: 14, color: "#526158" }}>{summary}</Paragraph>
          ) : null}

          {graphOverview.labelStats.length ? (
            <Space size={[8, 8]} wrap style={{ marginBottom: 14 }}>
              {graphOverview.labelStats.map((item) => (
                <Tag key={item.key} style={{ borderRadius: 999, marginInlineEnd: 0 }}>
                  {getGraphNodeLabelDisplayName(item.key)} · {item.count}
                </Tag>
              ))}
            </Space>
          ) : null}

          {graphData?.nodes.length ? (
            <div style={{ height: 320 }}>
              <MiniGraphCanvas
                graphData={graphData}
                onNodeClick={handleNodeClick}
                onEdgeClick={handleEdgeClick}
                onNodeHover={handleNodeHover}
                onEdgeHover={handleEdgeHover}
                onCanvasClick={handleCanvasClick}
              />
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
