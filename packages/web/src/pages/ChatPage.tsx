import { useState, useRef, useEffect } from "react";
import { Card, Typography, Input, Button, List, Space, Tag, Spin, message, Collapse } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { chatApi } from "../services/api";

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  reasoningChain?: ReasoningStep[];
  sources?: Source[];
  graphData?: GraphData;
}

interface ReasoningStep {
  step: number;
  description: string;
  entities?: string[];
  relations?: string[];
  confidence?: number;
}

interface Source {
  id: string;
  name: string;
  citation: string;
}

interface GraphData {
  center: any;
  nodes: any[];
  edges: any[];
}

const labelColors: Record<string, string> = {
  Herb: "blue",
  Efficacy: "green",
  Flavor: "orange",
  Meridian: "purple",
  Disease: "red",
  Component: "cyan",
};

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await chatApi.ask(userMessage.content, sessionId || undefined);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        reasoningChain: response.reasoning_chain,
        sources: response.sources,
        graphData: response.graph_data,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.session_id) {
        setSessionId(response.session_id);
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || "提问失败");
      // 添加错误消息
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "抱歉，我遇到了一些问题，请稍后再试。",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderReasoningChain = (chain: ReasoningStep[]) => (
    <Collapse
      ghost
      items={[
        {
          key: "reasoning",
          label: (
            <Text type="secondary">
              <InfoCircleOutlined /> 推理链
            </Text>
          ),
          children: (
            <List
              size="small"
              dataSource={chain}
              renderItem={(item) => (
                <List.Item style={{ padding: "4px 0" }}>
                  <Space>
                    <Tag color="blue">{item.step}</Tag>
                    <Text>{item.description}</Text>
                    {item.confidence && (
                      <Tag
                        color={
                          item.confidence > 0.8 ? "green" : item.confidence > 0.5 ? "orange" : "red"
                        }
                      >
                        {(item.confidence * 100).toFixed(0)}%
                      </Tag>
                    )}
                  </Space>
                </List.Item>
              )}
            />
          ),
        },
      ]}
    />
  );

  const renderGraphPreview = (graphData: GraphData) => {
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
                  onClick={() => navigate(`/graph/${encodeURIComponent(graphData.center.name)}`)}
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

  return (
    <div
      style={{
        maxWidth: 900,
        margin: "0 auto",
        height: "calc(100vh - 180px)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Card
        title={
          <Title level={4} style={{ margin: 0 }}>
            智能问答
          </Title>
        }
        style={{ flex: 1, display: "flex", flexDirection: "column" }}
        styles={{ body: { flex: 1, display: "flex", flexDirection: "column", padding: 0 } }}
      >
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
                    borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
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
                        renderReasoningChain(msg.reasoningChain)}
                      {msg.role === "assistant" &&
                        msg.graphData &&
                        renderGraphPreview(msg.graphData)}
                      {msg.role === "assistant" && msg.sources && renderSources(msg.sources)}
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

        <div style={{ padding: "16px 24px", borderTop: "1px solid #f0f0f0" }}>
          <Space.Compact style={{ width: "100%" }}>
            <TextArea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  void handleSend();
                }
              }}
              placeholder="输入您的问题，例如：陈皮有什么功效？"
              autoSize={{ minRows: 1, maxRows: 4 }}
              style={{ flex: 1 }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              disabled={!input.trim()}
            >
              发送
            </Button>
          </Space.Compact>
          <div style={{ marginTop: 8, textAlign: "center" }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              示例问题：
            </Text>
            <Space size="small" style={{ marginTop: 4 }}>
              <Button size="small" onClick={() => setInput("陈皮有什么功效？")}>
                陈皮功效
              </Button>
              <Button size="small" onClick={() => setInput("人参的成分有哪些？")}>
                人参成分
              </Button>
              <Button size="small" onClick={() => setInput("黄芪的主治是什么？")}>
                黄芪主治
              </Button>
              <Button size="small" onClick={() => setInput("陈皮的性味归经？")}>
                陈皮性味
              </Button>
            </Space>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChatPage;
