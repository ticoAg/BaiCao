import { useCallback, useMemo, useState } from "react";
import { Button, Card, Collapse, Empty, List, Space, Tag, Typography } from "antd";
import {
  BranchesOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  FunctionOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type {
  ChatGraphData,
  GraphAgentEvidence,
  GraphAgentReasoningTraceItem,
  GraphAgentSubgraphMeta,
  GraphAgentToolCall,
} from "../../types/chat";
import type { GraphData, GraphEdge, GraphNode, SelectedItem } from "../../types/graph";
import { getGraphNodeLabelDisplayName, getGraphNodeTagColor, relTypeLabels } from "../../types/graph";
import type { VizNode, VizRelationship } from "../../lib/graph-viz";
import MiniGraphCanvas from "../graph/MiniGraphCanvas";
import NodeDetail from "../graph/NodeDetail";
import EdgeDetail from "../graph/EdgeDetail";

const { Paragraph, Text } = Typography;

function formatToolArguments(argumentsValue?: Record<string, unknown>) {
  if (!argumentsValue || Object.keys(argumentsValue).length === 0) {
    return null;
  }
  return JSON.stringify(argumentsValue, null, 2);
}

interface GraphAgentBasisPanelProps {
  graphData?: ChatGraphData;
  evidence?: GraphAgentEvidence[];
  subgraphMeta?: GraphAgentSubgraphMeta;
  reasoningTrace?: GraphAgentReasoningTraceItem[];
  toolCalls?: GraphAgentToolCall[];
}

function isGraphNode(node: Partial<GraphNode>): node is GraphNode {
  return Boolean(node.id && node.name && node.status);
}

function isGraphEdge(edge: Partial<GraphEdge>): edge is GraphEdge {
  return Boolean(edge.source?.id && edge.target?.id);
}

function normalizeRenderableGraph(graphData?: ChatGraphData): GraphData {
  if (!graphData) {
    return { center: null, nodes: [], edges: [] };
  }

  const nodes = graphData.nodes.filter(isGraphNode);
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = graphData.edges
    .filter(isGraphEdge)
    .filter((edge) => nodeIds.has(edge.source?.id ?? "") && nodeIds.has(edge.target?.id ?? ""));
  const center = graphData.center && isGraphNode(graphData.center) ? graphData.center : nodes[0] ?? null;

  return { center, nodes, edges };
}

function getEdgeLabel(edge: GraphEdge) {
  return relTypeLabels[edge.rel_type || ""] || edge.rel_type || "相关";
}

function getEvidenceNodeName(evidence: GraphAgentEvidence, nodeById: Map<string, GraphNode>) {
  return evidence.node_id ? nodeById.get(evidence.node_id)?.name ?? evidence.node_id : "图谱证据";
}

const GraphAgentBasisPanel = ({
  graphData,
  evidence = [],
  subgraphMeta,
  reasoningTrace = [],
  toolCalls = [],
}: GraphAgentBasisPanelProps) => {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<SelectedItem | null>(null);
  const [hoveredItem, setHoveredItem] = useState<SelectedItem | null>(null);
  const renderableGraph = useMemo(() => normalizeRenderableGraph(graphData), [graphData]);
  const nodeById = useMemo(
    () => new Map(renderableGraph.nodes.map((node) => [node.id, node])),
    [renderableGraph.nodes],
  );
  const inspectorItem = hoveredItem ?? selected;
  const hasGraph = renderableGraph.nodes.length > 0;
  const hasEvidence = evidence.length > 0;
  const hasTraceOrTools = reasoningTrace.length > 0 || toolCalls.length > 0;

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
    setHoveredItem(vizNode ? { type: "node", data: vizNode.data } : null);
  }, []);

  const handleEdgeHover = useCallback((vizRel: VizRelationship | null) => {
    setHoveredItem(
      vizRel
        ? {
            type: "edge",
            data: {
              ...vizRel.data,
              sourceName: vizRel.data.source?.name,
              targetName: vizRel.data.target?.name,
            },
          }
        : null,
    );
  }, []);

  const collapseKeys = [
    hasGraph || subgraphMeta ? "subgraph" : null,
    hasEvidence ? "evidence" : null,
    hasTraceOrTools ? "trace" : null,
  ].filter((key): key is string => Boolean(key));

  if (collapseKeys.length === 0) {
    return null;
  }

  return (
    <Collapse
      ghost
      data-testid="graph-agent-basis-panel"
      defaultActiveKey={collapseKeys}
      items={[
        {
          key: "subgraph",
          label: (
            <Space size={8} wrap>
              <DatabaseOutlined />
              <Text type="secondary">依据子图</Text>
              <Tag style={{ marginInlineEnd: 0 }}>{subgraphMeta?.node_count ?? renderableGraph.nodes.length} 节点</Tag>
              <Tag style={{ marginInlineEnd: 0 }}>{subgraphMeta?.edge_count ?? renderableGraph.edges.length} 关系</Tag>
            </Space>
          ),
          children: (
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              <Space size={[8, 8]} wrap>
                {renderableGraph.center ? (
                  <Tag color={getGraphNodeTagColor(renderableGraph.center.labels?.[0])}>
                    中心：{renderableGraph.center.name}
                  </Tag>
                ) : null}
                <Tag>深度：{subgraphMeta?.actual_depth ?? 0}</Tag>
                <Tag color={subgraphMeta?.fallback_used ? "gold" : "green"}>
                  {subgraphMeta?.fallback_used ? "已使用 fallback" : "标准探索"}
                </Tag>
                {renderableGraph.center ? (
                  <Button
                    type="link"
                    size="small"
                    style={{ padding: 0 }}
                    onClick={() => navigate(`/graph/${encodeURIComponent(renderableGraph.center?.name ?? "")}`)}
                  >
                    查看完整图谱 →
                  </Button>
                ) : null}
              </Space>

              {hasGraph ? (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "minmax(0, 1.4fr) minmax(220px, 0.8fr)",
                    gap: 12,
                  }}
                >
                  <Card size="small" styles={{ body: { padding: 10 } }}>
                    <div style={{ height: 260 }}>
                      <MiniGraphCanvas
                        graphData={renderableGraph}
                        onNodeClick={handleNodeClick}
                        onEdgeClick={handleEdgeClick}
                        onNodeHover={handleNodeHover}
                        onEdgeHover={handleEdgeHover}
                        onCanvasClick={() => {
                          setHoveredItem(null);
                          setSelected(null);
                        }}
                      />
                    </div>
                  </Card>
                  <Card size="small" styles={{ body: { padding: 12 } }}>
                    {inspectorItem?.type === "node" ? <NodeDetail node={inspectorItem.data} /> : null}
                    {inspectorItem?.type === "edge" ? <EdgeDetail edge={inspectorItem.data} /> : null}
                    {!inspectorItem ? (
                      <Empty
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        description="点击或悬停子图节点 / 关系查看详情"
                      />
                    ) : null}
                  </Card>
                </div>
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="本轮回答没有可渲染子图" />
              )}

              <Card size="small" title="节点与关系摘要" styles={{ body: { padding: "8px 12px" } }}>
                <Space direction="vertical" size={8} style={{ width: "100%" }}>
                  <Space size={[6, 6]} wrap>
                    {renderableGraph.nodes.slice(0, 12).map((node) => (
                      <Tag key={node.id} color={getGraphNodeTagColor(node.labels?.[0])}>
                        {node.name} · {getGraphNodeLabelDisplayName(node.labels?.[0])}
                      </Tag>
                    ))}
                    {renderableGraph.nodes.length > 12 ? <Tag>+{renderableGraph.nodes.length - 12}</Tag> : null}
                  </Space>
                  <List
                    size="small"
                    dataSource={renderableGraph.edges.slice(0, 8)}
                    locale={{ emptyText: "暂无关系" }}
                    renderItem={(edge) => (
                      <List.Item style={{ padding: "4px 0" }}>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {edge.source?.name ?? edge.source?.id} → {getEdgeLabel(edge)} → {edge.target?.name ?? edge.target?.id}
                        </Text>
                      </List.Item>
                    )}
                  />
                </Space>
              </Card>
            </Space>
          ),
        },
        {
          key: "evidence",
          label: (
            <Space size={8}>
              <ExperimentOutlined />
              <Text type="secondary">证据摘要</Text>
              <Tag style={{ marginInlineEnd: 0 }}>{evidence.length}</Tag>
            </Space>
          ),
          children: (
            <List
              size="small"
              data-testid="graph-agent-evidence-list"
              dataSource={evidence}
              renderItem={(item) => (
                <List.Item style={{ padding: "6px 0" }}>
                  <Space direction="vertical" size={2} style={{ width: "100%" }}>
                    <Text strong>{getEvidenceNodeName(item, nodeById)}</Text>
                    <Paragraph style={{ marginBottom: 0 }}>{item.snippet}</Paragraph>
                  </Space>
                </List.Item>
              )}
            />
          ),
        },
        {
          key: "trace",
          label: (
            <Space size={8}>
              <BranchesOutlined />
              <Text type="secondary">推理与工具</Text>
              <Tag style={{ marginInlineEnd: 0 }}>{reasoningTrace.length + toolCalls.length}</Tag>
            </Space>
          ),
          children: (
            <Space direction="vertical" size={10} style={{ width: "100%" }}>
              {reasoningTrace.length ? (
                <List
                  size="small"
                  header={<Text strong>reasoning_trace</Text>}
                  dataSource={reasoningTrace}
                  renderItem={(item, index) => (
                    <List.Item style={{ padding: "4px 0" }}>
                      <Space>
                        <Tag color="blue">{item.kind ?? `step-${index + 1}`}</Tag>
                        <Text>{item.summary}</Text>
                      </Space>
                    </List.Item>
                  )}
                />
              ) : null}
              {toolCalls.length ? (
                <List
                  size="small"
                  header={
                    <Space>
                      <FunctionOutlined />
                      <Text strong>tool_calls</Text>
                    </Space>
                  }
                  dataSource={toolCalls}
                  renderItem={(item) => (
                    <List.Item style={{ padding: "4px 0" }}>
                      <Space direction="vertical" size={4} style={{ width: "100%" }}>
                        <Space wrap>
                          <Tag color="geekblue">{item.tool_name}</Tag>
                          {item.status ? <Tag>{item.status}</Tag> : null}
                          <Text>{item.summary}</Text>
                        </Space>
                        {item.result_summary ? (
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {item.result_summary}
                          </Text>
                        ) : null}
                        {formatToolArguments(item.arguments) ? (
                          <Paragraph
                            code
                            style={{ marginBottom: 0, whiteSpace: "pre-wrap", fontSize: 12 }}
                          >
                            {formatToolArguments(item.arguments)}
                          </Paragraph>
                        ) : null}
                      </Space>
                    </List.Item>
                  )}
                />
              ) : null}
            </Space>
          ),
        },
      ].filter((item) => collapseKeys.includes(item.key))}
    />
  );
};

export default GraphAgentBasisPanel;
