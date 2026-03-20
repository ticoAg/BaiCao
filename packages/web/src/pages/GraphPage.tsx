import { useState, useEffect, useCallback } from "react";
import { Card, Typography, Spin, message, Descriptions, Tag, Space, Row, Col } from "antd";
import { useParams } from "react-router-dom";
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

// 节点类型颜色
const labelColors: Record<string, string> = {
  Herb: "blue",
  Efficacy: "green",
  Flavor: "orange",
  Meridian: "purple",
  Disease: "red",
  Component: "cyan",
};

const GraphPage = () => {
  const { name } = useParams<{ name: string }>();
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [depth, setDepth] = useState(1);

  const loadGraph = useCallback(async () => {
    if (!name) return;
    setLoading(true);
    try {
      const data = await graphApi.getHerbGraph(name, depth);
      setGraphData(data);
      if (data.center) {
        setSelectedNode(data.center);
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

  const renderNode = (node: GraphNode, index: number) => {
    const primaryLabel = node.labels?.[0] || "Unknown";
    const isCenter = graphData?.center?.id === node.id;

    return (
      <div
        key={node.id || index}
        style={{
          padding: "12px 16px",
          margin: "8px 0",
          background: isCenter ? "#e6f7ff" : "#fafafa",
          border: `2px solid ${labelColors[primaryLabel] || "gray"}`,
          borderRadius: 8,
          cursor: "pointer",
          transform: isCenter ? "scale(1.02)" : "scale(1)",
          transition: "all 0.2s",
        }}
        onClick={() => setSelectedNode(node)}
      >
        <Space>
          <Tag color={labelColors[primaryLabel] || "default"}>{primaryLabel}</Tag>
          <Text strong={isCenter}>{node.name}</Text>
          <Tag color={statusColors[node.status] || "default"}>
            {statusLabels[node.status] || node.status}
          </Tag>
        </Space>
      </div>
    );
  };

  const renderEdge = (edge: GraphEdge, index: number) => {
    return (
      <div
        key={index}
        style={{
          padding: "8px 12px",
          margin: "4px 0",
          background: "#f5f5f5",
          borderRadius: 4,
          borderLeft: `3px solid ${statusColors[edge.status] || "gray"}`,
        }}
      >
        <Space>
          <Text type="secondary">{edge.rel_type || "RELATION"}</Text>
          <Tag color={statusColors[edge.status] || "default"}>
            {statusLabels[edge.status] || edge.status}
          </Tag>
        </Space>
      </div>
    );
  };

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
    <div>
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              {name} 的知识图谱
            </Title>
            <Tag>{graphData.nodes.length} 节点</Tag>
            <Tag>{graphData.edges.length} 关系</Tag>
          </Space>
        }
        extra={
          <Space>
            <span>深度:</span>
            <select
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              style={{ padding: "4px 8px", borderRadius: 4 }}
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
            </select>
            <a onClick={() => void loadGraph()}>刷新</a>
          </Space>
        }
      >
        <Row gutter={16}>
          {/* 左侧：图谱节点和关系列表 */}
          <Col span={14}>
            <Card size="small" title="节点" style={{ marginBottom: 16 }}>
              {graphData.nodes.map((node, i) => renderNode(node, i))}
            </Card>
            <Card size="small" title="关系">
              {graphData.edges.map((edge, i) => renderEdge(edge, i))}
            </Card>
          </Col>

          {/* 右侧：选中节点详情 */}
          <Col span={10}>
            <Card
              title="节点详情"
              style={{
                position: "sticky",
                top: 80,
                background: selectedNode ? "#fafafa" : "#fff",
              }}
            >
              {selectedNode ? (
                <Descriptions column={1} size="small" bordered>
                  <Descriptions.Item label="名称">
                    <Text strong>{selectedNode.name}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="类型">
                    <Tag color={labelColors[selectedNode.labels?.[0] || ""]}>
                      {selectedNode.labels?.[0] || "Unknown"}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="状态">
                    <Tag color={statusColors[selectedNode.status]}>
                      {statusLabels[selectedNode.status]}
                    </Tag>
                  </Descriptions.Item>
                  {selectedNode.source && (
                    <Descriptions.Item label="来源">{selectedNode.source}</Descriptions.Item>
                  )}
                  {selectedNode.verification_id && (
                    <Descriptions.Item label="验证ID">
                      {selectedNode.verification_id}
                    </Descriptions.Item>
                  )}
                  {selectedNode.verified_at && (
                    <Descriptions.Item label="验证时间">
                      {new Date(selectedNode.verified_at).toLocaleString("zh-CN")}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              ) : (
                <Text type="secondary">点击左侧节点查看详情</Text>
              )}

              {selectedNode && selectedNode.status === "pending" && (
                <div style={{ marginTop: 16 }}>
                  <a
                    onClick={() => {
                      // TODO: 跳转到验证申请页面
                      message.info("跳转到验证申请页面");
                    }}
                  >
                    申请验证
                  </a>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default GraphPage;
