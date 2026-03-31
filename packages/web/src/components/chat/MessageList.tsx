// 消息列表组件
import { useState } from "react";
import { List, Card, Space, Typography, Spin, Collapse, Tag, Button, Drawer, Divider } from "antd";
import { RobotOutlined, UserOutlined, AuditOutlined, FormOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { Message, ChatGraphData, Source, Entity } from "../../types/chat";
import { getGraphNodeLabelDisplayName, getGraphNodeTagColor } from "../../types/graph";
import ReasoningChain from "./ReasoningChain";
import EntityHighlighter from "./EntityHighlighter";
import EvidenceList from "../provenance/EvidenceList";
import LineageChain from "../provenance/LineageChain";
import { useProvenance } from "../../hooks/useProvenance";
import ReviewRequestModal from "./ReviewRequestModal";

const { Text } = Typography;

interface MessageListProps {
  messages: Message[];
  loading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

// 从 sources 中提取首个实体 ID（用于溯源 Drawer）
function getFirstEntityId(sources?: Source[]): string | undefined {
  if (!sources || sources.length === 0) return undefined;
  return sources[0].id;
}

// 从 ReasoningStep entities 提取全部唯一实体字符串（向后兼容：ReasoningStep.entities 为 string[]）
// 用于在没有结构化 entities 字段时的 fallback
function extractEntitiesFromSources(sources?: Source[]): Entity[] {
  if (!sources || sources.length === 0) return [];
  return sources.map((s) => ({
    id: s.id,
    name: s.name,
    type: "Herb",
  }));
}

interface ProvenanceDrawerProps {
  entityId?: string;
  entityName?: string;
  open: boolean;
  onClose: () => void;
}

const ProvenanceDrawer = ({
  entityId,
  entityName,
  open,
  onClose,
}: ProvenanceDrawerProps) => {
  const { lineage, evidence, loading } = useProvenance(entityId, {
    enabled: open && !!entityId,
  });

  const evidenceItems = (evidence as Record<string, unknown>[]).map((e) => ({
    id: String(e.id ?? ""),
    content: String(e.content ?? ""),
    source_name: String(e.source_name ?? ""),
    page_reference: e.page_reference != null ? String(e.page_reference) : undefined,
    status: String(e.status ?? "pending"),
    ...e,
  }));

  return (
    <Drawer
      title={entityName ? `证据溯源：${entityName}` : "证据溯源"}
      placement="right"
      width={480}
      open={open}
      onClose={onClose}
    >
      <LineageChain lineage={lineage} loading={loading} />
      <Divider />
      <EvidenceList evidence={evidenceItems} loading={loading} />
    </Drawer>
  );
};

const GraphPreview = ({ graphData }: { graphData: ChatGraphData }) => {
  const navigate = useNavigate();

  if (!graphData || !graphData.center) return null;

  const center = graphData.center;
  const nodeCount = graphData.nodes?.length || 0;
  const edgeCount = graphData.edges?.length || 0;

  return (
    <Collapse
      ghost
      items={[
        {
          key: "graph",
          label: (
            <Text type="secondary">
              相关图谱数据 ({nodeCount} 节点, {edgeCount} 关系)
            </Text>
          ),
          children: (
            <div>
              <Text strong>{center.name}</Text>
              <Tag
                color={getGraphNodeTagColor(center.labels?.[0])}
                style={{ marginLeft: 8 }}
              >
                {getGraphNodeLabelDisplayName(center.labels?.[0])}
              </Tag>
              <div style={{ marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  状态：
                </Text>
                <Tag
                  color={
                    center.status === "verified"
                      ? "green"
                      : center.status === "rejected"
                        ? "red"
                        : "gold"
                  }
                  style={{ marginLeft: 4 }}
                >
                  {center.status === "verified"
                    ? "已验证"
                    : center.status === "rejected"
                      ? "已拒绝"
                      : "待验证"}
                </Tag>
              </div>
              <Button
                type="link"
                size="small"
                onClick={() => navigate(`/graph/${encodeURIComponent(center.name)}`)}
                style={{ padding: 0, marginTop: 8 }}
              >
                查看完整图谱 →
              </Button>
            </div>
          ),
        },
      ]}
    />
  );
};

const WorkbenchResultPreview = ({ frames }: { frames: Message["workbenchFrames"] }) => {
  const navigate = useNavigate();

  if (!frames || frames.length === 0) return null;

  return (
    <Collapse
      ghost
      defaultActiveKey={["workbench"]}
      items={[
        {
          key: "workbench",
          label: <Text type="secondary">Workbench 结果</Text>,
          children: (
            <Space direction="vertical" size={10} style={{ width: "100%" }}>
              {frames.map((frame) => (
                <Card
                  key={frame.id}
                  size="small"
                  styles={{ body: { padding: "10px 12px" } }}
                  extra={<Tag style={{ margin: 0 }}>{frame.type}</Tag>}
                >
                  <Text strong>{frame.title}</Text>
                  {frame.command ? (
                    <Text type="secondary" style={{ display: "block", marginTop: 4 }}>
                      {frame.command}
                    </Text>
                  ) : null}
                  {frame.type === "graph" ? (
                    <Button
                      type="link"
                      size="small"
                      style={{ padding: 0, marginTop: 8 }}
                      onClick={() => navigate("/graph/workbench")}
                    >
                      在工作台中继续查看 →
                    </Button>
                  ) : null}
                </Card>
              ))}
            </Space>
          ),
        },
      ]}
    />
  );
};

const MessageList = ({ messages, loading, messagesEndRef }: MessageListProps) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerEntityId, setDrawerEntityId] = useState<string | undefined>();
  const [drawerEntityName, setDrawerEntityName] = useState<string | undefined>();
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewPrefill, setReviewPrefill] = useState<{
    entityType?: string;
    entityId?: string;
    content?: string;
    sourceId?: string;
  }>({});

  const handleOpenProvenance = (sources?: Source[]) => {
    const firstSource = sources?.[0];
    if (firstSource) {
      setDrawerEntityId(firstSource.id);
      setDrawerEntityName(firstSource.name);
      setDrawerOpen(true);
    }
  };

  const handleOpenReview = (sources?: Source[], content?: string) => {
    const firstSource = sources?.[0];
    setReviewPrefill({
      entityType: "herb",
      entityId: firstSource?.id || "",
      content: content ? content.slice(0, 500) : "",
      sourceId: firstSource?.id,
    });
    setReviewOpen(true);
  };

  const renderSources = (sources: Source[], msgContent?: string) => {
    if (!sources || sources.length === 0) return null;
    return (
      <Space style={{ marginTop: 8 }} wrap>
        <Text type="secondary" style={{ fontSize: 12 }}>
          来源：
        </Text>
        {sources.map((source) => (
          <Tag key={source.id}>{source.name}</Tag>
        ))}
        <Button
          type="link"
          size="small"
          icon={<AuditOutlined />}
          onClick={() => handleOpenProvenance(sources)}
          style={{ padding: "0 4px", fontSize: 12 }}
        >
          查看溯源
        </Button>
        <Button
          type="link"
          size="small"
          icon={<FormOutlined />}
          onClick={() => handleOpenReview(sources, msgContent)}
          style={{ padding: "0 4px", fontSize: 12 }}
        >
          申请审查
        </Button>
      </Space>
    );
  };

  return (
    <>
      <div style={{ flex: 1, overflow: "auto", padding: "16px 24px" }}>
        <List
          dataSource={messages}
          renderItem={(msg) => {
            // 优先使用 msg.entities；若为空则从 sources 中 fallback 提取
            const entities: Entity[] =
              msg.entities && msg.entities.length > 0
                ? msg.entities
                : extractEntitiesFromSources(msg.sources);

            return (
              <List.Item
                style={{
                  justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                  border: "none",
                  padding: "8px 0",
                }}
              >
                <Card
                  size="small"
                  style={{
                    maxWidth: "80%",
                    background: msg.role === "user" ? "#e6f7ff" : "#fafafa",
                    borderRadius:
                      msg.role === "user"
                        ? "16px 16px 4px 16px"
                        : "16px 16px 16px 4px",
                  }}
                  styles={{ body: { padding: "12px 16px" } }}
                >
                  <Space align="start">
                    {msg.role === "assistant" ? (
                      <RobotOutlined style={{ fontSize: 20, color: "#1890ff" }} />
                    ) : (
                      <UserOutlined style={{ fontSize: 20, color: "#52c41a" }} />
                    )}
                    <div>
                      <EntityHighlighter content={msg.content} entities={entities} />
                      {msg.role === "assistant" &&
                        msg.reasoningChain &&
                        <ReasoningChain chain={msg.reasoningChain} />}
                      {msg.role === "assistant" &&
                        msg.graphData &&
                        <GraphPreview graphData={msg.graphData} />}
                      {msg.role === "assistant" &&
                        msg.workbenchFrames &&
                        <WorkbenchResultPreview frames={msg.workbenchFrames} />}
                      {msg.role === "assistant" &&
                        msg.sources &&
                        renderSources(msg.sources, msg.content)}
                    </div>
                  </Space>
                </Card>
              </List.Item>
            );
          }}
        />
        {loading && (
          <div style={{ textAlign: "center", padding: 16 }}>
            <Space direction="vertical" size="small">
              <Spin />
              <Text type="secondary">思考中...</Text>
            </Space>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <ProvenanceDrawer
        entityId={drawerEntityId}
        entityName={drawerEntityName}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
      <ReviewRequestModal
        open={reviewOpen}
        onClose={() => setReviewOpen(false)}
        prefill={reviewPrefill}
      />
    </>
  );
};

export default MessageList;
