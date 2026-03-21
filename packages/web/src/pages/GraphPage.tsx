import { useState, useEffect, useCallback, useMemo } from "react";
import { Typography, Spin, message, Descriptions, Tag, Space, Button, Card, Divider } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { NetworkGraph } from "@ant-design/graphs";
import { graphApi, GraphData, GraphNode, GraphEdge } from "../services/api";

const { Title, Text } = Typography;

// 状态颜色映射
const statusColors: Record<string, string> = {
  pending: "gold",
  verified: "green",
  rejected: "red",
};

const statusLabels: Record<string, string> = {
  pending: "待验证",
  verified: "已验证",
  rejected: "已拒绝",
};

// 节点类型颜色（G6 需要 hex/rgb 值）
const labelColorMap: Record<string, string> = {
  Herb: "#1677ff",
  Efficacy: "#52c41a",
  Flavor: "#fa8c16",
  Meridian: "#722ed1",
  Disease: "#f5222d",
  Component: "#13c2c2",
  Variant: "#2f54eb",
  Process: "#a0d911",
  Trait: "#fa541c",
  TimePoint: "#eb2f96",
};

// 节点类型 Ant Tag 颜色
const labelTagColors: Record<string, string> = {
  Herb: "blue",
  Efficacy: "green",
  Flavor: "orange",
  Meridian: "purple",
  Disease: "red",
  Component: "cyan",
  Variant: "geekblue",
  Process: "lime",
  Trait: "volcano",
  TimePoint: "magenta",
};

const defaultNodeColor = "#8c8c8c";

// 关系类型中文映射
const relTypeLabels: Record<string, string> = {
  CONTAINS: "含有",
  TREATS: "主治",
  HAS_FLAVOR: "味",
  ENTERS_MERIDIAN: "归经",
  HAS_EFFICACY: "功效",
  HAS_COMPONENT: "成分",
  BELONGS_TO: "属于",
  VARIANT_OF: "变种",
  PROCESSED_BY: "炮制",
  HAS_TRAIT: "特征",
  HARVESTED_AT: "采收",
};

type SelectedItem =
  | { type: "node"; data: GraphNode }
  | { type: "edge"; data: GraphEdge & { sourceName?: string; targetName?: string } };

const GraphPage = () => {
  const { name } = useParams<{ name: string }>();
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selected, setSelected] = useState<SelectedItem | null>(null);
  const [depth, setDepth] = useState(1);

  const loadGraph = useCallback(async () => {
    if (!name) return;
    setLoading(true);
    try {
      const data = await graphApi.getHerbGraph(name, depth);
      setGraphData(data);
      if (data.center) {
        setSelected({ type: "node", data: data.center });
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || "加载图谱失败");
    } finally {
      setLoading(false);
    }
  }, [name, depth]);

  useEffect(() => {
    void loadGraph();
  }, [loadGraph]);

  // 将后端数据转为 G6 格式
  const g6Data = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] };

    const centerId = graphData.center?.id || graphData.center?.name;

    const nodes = graphData.nodes.map((n) => {
      const nodeId = n.id || n.name;
      const primaryLabel = n.labels?.[0] || "Unknown";
      const isCenter = nodeId === centerId;
      const color = labelColorMap[primaryLabel] || defaultNodeColor;

      return {
        id: nodeId,
        data: { ...n },
        style: {
          size: isCenter ? 48 : primaryLabel === "Herb" ? 36 : 28,
          fill: color,
          stroke: isCenter ? "#000" : color,
          lineWidth: isCenter ? 3 : 1,
          labelText: n.name,
          labelFontSize: isCenter ? 14 : 11,
          labelFill: "#333",
          labelPlacement: "bottom" as const,
          labelOffsetY: 4,
        },
      };
    });

    const edges = graphData.edges.map((e, i) => {
      const sourceId = e.source?.id || e.source?.name || "";
      const targetId = e.target?.id || e.target?.name || "";
      const isVerified = e.status === "verified";

      return {
        id: e.id || `edge-${i}`,
        source: sourceId,
        target: targetId,
        data: {
          ...e,
          sourceName: e.source?.name,
          targetName: e.target?.name,
        },
        style: {
          stroke: isVerified ? "#52c41a" : "#bfbfbf",
          lineWidth: isVerified ? 2 : 1,
          labelText: relTypeLabels[e.rel_type || ""] || e.rel_type || "",
          labelFontSize: 10,
          labelFill: "#666",
          endArrow: true,
        },
      };
    });

    return { nodes, edges };
  }, [graphData]);

  // NetworkGraph 配置
  const graphOptions = useMemo(
    () => ({
      data: g6Data,
      behaviors: (behaviors: any[]) => [
        ...behaviors,
        { key: "drag-element", type: "drag-element" },
        { key: "hover-activate", type: "hover-activate" },
      ],
      animation: false,
    }),
    [g6Data],
  );

  // 处理节点点击
  const handleReady = useCallback(
    (graph: any) => {
      if (!graphData) return;

      graph.on("node:click", (evt: any) => {
        const nodeId = evt.target?.id;
        if (!nodeId) return;
        const node = graphData.nodes.find((n) => (n.id || n.name) === nodeId);
        if (node) {
          setSelected({ type: "node", data: node });
        }
      });

      graph.on("edge:click", (evt: any) => {
        const edgeId = evt.target?.id;
        if (!edgeId) return;
        const edgeModel = graph.getEdgeData(edgeId);
        if (edgeModel?.data) {
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
    },
    [graphData],
  );

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 50 }}>
        <Space direction="vertical" size="middle">
          <Spin size="large" />
          <Text type="secondary">加载图谱中...</Text>
        </Space>
      </div>
    );
  }

  if (!graphData) {
    return (
      <Card>
        <Text>未找到相关图谱数据</Text>
      </Card>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* 顶部工具栏 */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #f0f0f0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#fff",
        }}
      >
        <Space>
          <Title level={4} style={{ margin: 0 }}>
            {name} 的知识图谱
          </Title>
          <Tag>{graphData.nodes.length} 节点</Tag>
          <Tag>{graphData.edges.length} 关系</Tag>
        </Space>
        <Space>
          <span>深度:</span>
          <select
            value={depth}
            onChange={(e) => setDepth(Number(e.target.value))}
            style={{ padding: "4px 8px", borderRadius: 4, border: "1px solid #d9d9d9" }}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
          <Button icon={<ReloadOutlined />} size="small" onClick={() => void loadGraph()}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 主体：左图右详情 */}
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        {/* 左侧力导向图 */}
        <div style={{ flex: 1, position: "relative", minHeight: 500 }}>
          <NetworkGraph {...graphOptions} onReady={handleReady} />
        </div>

        {/* 右侧详情面板 */}
        <div
          style={{
            width: 320,
            borderLeft: "1px solid #f0f0f0",
            overflowY: "auto",
            padding: 16,
            background: "#fafafa",
          }}
        >
          {/* 详情区 */}
          {selected?.type === "node" && <NodeDetail node={selected.data} />}
          {selected?.type === "edge" && <EdgeDetail edge={selected.data} />}
          {!selected && <Text type="secondary">点击节点或关系查看详情</Text>}

          <Divider />

          {/* 图例 */}
          <div>
            <Text strong>图例</Text>
            <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 4 }}>
              {Object.entries(labelColorMap).map(([label, color]) => (
                <Tag key={label} color={labelTagColors[label] || "default"}>
                  <span
                    style={{
                      display: "inline-block",
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: color,
                      marginRight: 4,
                    }}
                  />
                  {label}
                </Tag>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/** 节点详情面板 */
const NodeDetail = ({ node }: { node: GraphNode }) => {
  const primaryLabel = node.labels?.[0] || "Unknown";
  return (
    <div>
      <Text strong style={{ fontSize: 16 }}>
        节点详情
      </Text>
      <Descriptions column={1} size="small" bordered style={{ marginTop: 12 }}>
        <Descriptions.Item label="名称">
          <Text strong>{node.name}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          <Tag color={labelTagColors[primaryLabel] || "default"}>{primaryLabel}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={statusColors[node.status]}>{statusLabels[node.status]}</Tag>
        </Descriptions.Item>
        {node.source && <Descriptions.Item label="来源">{node.source}</Descriptions.Item>}
        {node.category && <Descriptions.Item label="分类">{node.category}</Descriptions.Item>}
        {node.description && <Descriptions.Item label="描述">{node.description}</Descriptions.Item>}
        {node.latin_name && <Descriptions.Item label="拉丁名">{node.latin_name}</Descriptions.Item>}
        {node.verification_id && (
          <Descriptions.Item label="验证ID">{node.verification_id}</Descriptions.Item>
        )}
        {node.verified_by && (
          <Descriptions.Item label="验证人">{node.verified_by}</Descriptions.Item>
        )}
        {node.verified_at && (
          <Descriptions.Item label="验证时间">
            {new Date(node.verified_at).toLocaleString("zh-CN")}
          </Descriptions.Item>
        )}
      </Descriptions>
      {node.status === "pending" && (
        <div style={{ marginTop: 12 }}>
          <a onClick={() => message.info("跳转到验证申请页面")}>申请验证</a>
        </div>
      )}
    </div>
  );
};

/** 关系详情面板 */
const EdgeDetail = ({
  edge,
}: {
  edge: GraphEdge & { sourceName?: string; targetName?: string };
}) => (
  <div>
    <Text strong style={{ fontSize: 16 }}>
      关系详情
    </Text>
    <Descriptions column={1} size="small" bordered style={{ marginTop: 12 }}>
      <Descriptions.Item label="关系类型">
        {relTypeLabels[edge.rel_type || ""] || edge.rel_type || "—"}
      </Descriptions.Item>
      <Descriptions.Item label="起始节点">{edge.sourceName || "—"}</Descriptions.Item>
      <Descriptions.Item label="目标节点">{edge.targetName || "—"}</Descriptions.Item>
      <Descriptions.Item label="状态">
        <Tag color={statusColors[edge.status]}>{statusLabels[edge.status]}</Tag>
      </Descriptions.Item>
      {edge.verification_id && (
        <Descriptions.Item label="验证ID">{edge.verification_id}</Descriptions.Item>
      )}
      {edge.verified_at && (
        <Descriptions.Item label="验证时间">
          {new Date(edge.verified_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
      )}
    </Descriptions>
  </div>
);

export default GraphPage;
