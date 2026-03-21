import { useCallback, useMemo } from "react";
import { Typography, Spin, Space, Button, Card, Tag, Divider } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";
import { NetworkGraph } from "@ant-design/graphs";
import { useGraph } from "../hooks/useGraph";
import {
  labelColorMap,
  labelTagColors,
  defaultNodeColor,
  relTypeLabels,
} from "../types/graph";
import NodeDetail from "../components/graph/NodeDetail";
import EdgeDetail from "../components/graph/EdgeDetail";

const { Title, Text } = Typography;

const GraphPage = () => {
  const { name } = useParams<{ name: string }>();
  const {
    graphData,
    loading,
    selected,
    setSelected,
    depth,
    setDepth,
    refetch,
  } = useGraph(name);

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

  // 处理节点/边点击
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
              sourceName:
                edgeModel.data.sourceName || edgeModel.data.source?.name,
              targetName:
                edgeModel.data.targetName || edgeModel.data.target?.name,
            },
          });
        }
      });
    },
    [graphData, setSelected],
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
            style={{
              padding: "4px 8px",
              borderRadius: 4,
              border: "1px solid #d9d9d9",
            }}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
          <Button icon={<ReloadOutlined />} size="small" onClick={refetch}>
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
          {selected?.type === "node" && <NodeDetail node={selected.data} />}
          {selected?.type === "edge" && <EdgeDetail edge={selected.data} />}
          {!selected && (
            <Text type="secondary">点击节点或关系查看详情</Text>
          )}

          <Divider />

          {/* 图例 */}
          <div>
            <Text strong>图例</Text>
            <div
              style={{
                marginTop: 8,
                display: "flex",
                flexWrap: "wrap",
                gap: 4,
              }}
            >
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

export default GraphPage;
