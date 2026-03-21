import { useRef, useEffect } from "react";
import { Card, Typography } from "antd";
import { useChat } from "../hooks/useChat";
import MessageList from "../components/chat/MessageList";
import MessageInput from "../components/chat/MessageInput";

const { Title } = Typography;

const ChatPage = () => {
  const { messages, isStreaming, input, setInput, sendMessage } = useChat();
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
        <MessageList
          messages={messages}
          loading={isStreaming}
          messagesEndRef={messagesEndRef}
        />
        <MessageInput
          input={input}
          loading={isStreaming}
          onInputChange={setInput}
          onSend={handleSend}
        />
      </Card>
    </div>
  );
};

export default ChatPage;
