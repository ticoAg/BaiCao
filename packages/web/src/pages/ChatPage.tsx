import { useRef, useEffect } from "react";
import { Typography, Tag, Button, Tooltip } from "antd";
import { MessageOutlined, PlusOutlined } from "@ant-design/icons";
import { useChat } from "../hooks/useChat";
import MessageList from "../components/chat/MessageList";
import MessageInput from "../components/chat/MessageInput";

const { Title, Text } = Typography;

const ChatPage = () => {
  const { messages, sessionId, isStreaming, input, setInput, sendMessage, startNewTopic } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    void sendMessage(input);
  };

  return (
    <div
      style={{
        maxWidth: 900,
        margin: "0 auto",
        height: "calc(100vh - 150px)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          background: "#fff",
          borderRadius: 12,
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          overflow: "hidden",
        }}
      >
        {/* 标题栏 */}
        <div
          style={{
            padding: "14px 24px",
            borderBottom: "1px solid #f0f0f0",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <MessageOutlined style={{ fontSize: 18, color: "#2e7d32" }} />
          <Title level={4} style={{ margin: 0 }}>
            智能问答
          </Title>
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
            {sessionId && (
              <>
                <Tag color="green" style={{ margin: 0 }}>对话进行中</Tag>
                <Tooltip title="新话题">
                  <Button
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={startNewTopic}
                    disabled={isStreaming}
                  >
                    新话题
                  </Button>
                </Tooltip>
              </>
            )}
            <Text type="secondary" style={{ fontSize: 12 }}>
              基于 deepagents 图谱专家的中药材问答
            </Text>
          </div>
        </div>

        {/* 消息区域 */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
          {messages.length === 0 && !isStreaming ? (
            <WelcomeView onQuestionClick={(q) => {
              setInput(q);
              void sendMessage(q);
            }} />
          ) : (
            <MessageList
              messages={messages}
              loading={isStreaming}
              messagesEndRef={messagesEndRef}
            />
          )}
        </div>

        {/* 输入区域 */}
        <MessageInput
          input={input}
          loading={isStreaming}
          onInputChange={setInput}
          onSend={handleSend}
        />
      </div>
    </div>
  );
};

/** 空状态欢迎视图 */
const welcomeQuestions = [
  { icon: "🌿", label: "甘草有什么功效？" },
  { icon: "🔬", label: "人参的主要成分有哪些？" },
  { icon: "💊", label: "黄芪和当归可以搭配使用吗？" },
  { icon: "📖", label: "陈皮的性味归经是什么？" },
];

const WelcomeView = ({ onQuestionClick }: { onQuestionClick: (q: string) => void }) => (
  <div
    style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: 32,
    }}
  >
    <div style={{ fontSize: 48, marginBottom: 16 }}>🌿</div>
    <Title level={3} style={{ marginBottom: 8, color: "#1a3a2a" }}>
      你好！我是白草药坛 AI 助手
    </Title>
    <Text
      type="secondary"
      style={{ marginBottom: 32, fontSize: 14, textAlign: "center" }}
    >
      我可以回答关于中药材的功效、成分、归经等问题，并展开每轮回答的依据子图：
    </Text>
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 12,
        maxWidth: 500,
        width: "100%",
      }}
    >
      {welcomeQuestions.map((q) => (
        <div
          key={q.label}
          onClick={() => onQuestionClick(q.label)}
          style={{
            padding: "12px 16px",
            background: "#f6ffed",
            borderRadius: 10,
            cursor: "pointer",
            border: "1px solid #e8f5e9",
            transition: "all 0.2s",
            fontSize: 13,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#e8f5e9";
            e.currentTarget.style.borderColor = "#c8e6c9";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "#f6ffed";
            e.currentTarget.style.borderColor = "#e8f5e9";
          }}
        >
          <span>{q.icon}</span>
          <span>{q.label}</span>
        </div>
      ))}
    </div>
  </div>
);

export default ChatPage;
