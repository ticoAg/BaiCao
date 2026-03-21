// 消息列表组件
import { List, Card, Space, Typography, Spin, Collapse, Tag, Button } from "antd";
import { RobotOutlined, UserOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { Message, ChatGraphData, Source } from "../../types/chat";
import ReasoningChain from "./ReasoningChain";

const { Text, Paragraph } = Typography;

const labelColors: Record<string, string> = {
  Herb: "blue",
  Efficacy: "green",
  Flavor: "orange",
  Meridian: "purple",
  Disease: "red",
  Component: "cyan",
};

interface MessageListProps {
  messages: Message[];
  loading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

const renderSources = (sources: Source[]) => {
  if (!sources || sources.length === 0) return null;
  return (
    <Space style={{ marginTop: 8 }}>
      <Text type="secondary" style={{ fontSize: 12 }}>
        来源：
      </Text>
      {sources.map((source) => (
        <Tag key={source.id}>{source.name}</Tag>
      ))}
    </Space>
  );
};

const GraphPreview = ({ graphData }: { graphData: ChatGraphData }) => {
  const navigate = useNavigate();

  if (!graphData || !graphData.center) return null;

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
              <Text strong>{graphData.center.name}</Text>
              <Tag
                color={labelColors[graphData.center.labels?.[0]] || "default"}
                style={{ marginLeft: 8 }}
              >
                {graphData.center.labels?.[0] || "Unknown"}
              </Tag>
              <div style={{ marginTop: 8 }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  状态：
                </Text>
                <Tag
                  color={
                    graphData.center.status === "verified"
                      ? "green"
                      : graphData.center.status === "rejected"
                        ? "red"
                        : "gold"
                  }
                  style={{ marginLeft: 4 }}
                >
                  {graphData.center.status === "verified"
                    ? "已验证"
                    : graphData.center.status === "rejected"
                      ? "已拒绝"
                      : "待验证"}
                </Tag>
              </div>
              <Button
                type="link"
                size="small"
                onClick={() =>
                  navigate(`/graph/${encodeURIComponent(graphData.center.name)}`)
                }
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

const MessageList = ({ messages, loading, messagesEndRef }: MessageListProps) => (
  <div style={{ flex: 1, overflow: "auto", padding: "16px 24px" }}>
    <List
      dataSource={messages}
      renderItem={(msg) => (
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
                <Paragraph style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                  {msg.content}
                </Paragraph>
                {msg.role === "assistant" &&
                  msg.reasoningChain &&
                  <ReasoningChain chain={msg.reasoningChain} />}
                {msg.role === "assistant" &&
                  msg.graphData &&
                  <GraphPreview graphData={msg.graphData} />}
                {msg.role === "assistant" &&
                  msg.sources &&
                  renderSources(msg.sources)}
              </div>
            </Space>
          </Card>
        </List.Item>
      )}
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
);

export default MessageList;
