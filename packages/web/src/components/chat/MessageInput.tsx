// 消息输入组件
import { Input, Button, Space, Typography } from "antd";
import { SendOutlined } from "@ant-design/icons";

const { Text } = Typography;
const { TextArea } = Input;

interface MessageInputProps {
  input: string;
  loading: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
}

const exampleQuestions = [
  { label: "陈皮功效", question: "陈皮有什么功效？" },
  { label: "人参成分", question: "人参的成分有哪些？" },
  { label: "黄芪主治", question: "黄芪的主治是什么？" },
  { label: "陈皮性味", question: "陈皮的性味归经？" },
];

const MessageInput = ({ input, loading, onInputChange, onSend }: MessageInputProps) => (
  <div style={{ padding: "16px 24px", borderTop: "1px solid #f0f0f0" }}>
    <Space.Compact style={{ width: "100%" }}>
      <TextArea
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        onPressEnter={(e) => {
          if (!e.shiftKey) {
            e.preventDefault();
            onSend();
          }
        }}
        placeholder="输入您的问题，例如：陈皮有什么功效？"
        autoSize={{ minRows: 1, maxRows: 4 }}
        style={{ flex: 1 }}
      />
      <Button
        type="primary"
        icon={<SendOutlined />}
        onClick={onSend}
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
        {exampleQuestions.map((eq) => (
          <Button key={eq.label} size="small" onClick={() => onInputChange(eq.question)}>
            {eq.label}
          </Button>
        ))}
      </Space>
    </div>
  </div>
);

export default MessageInput;
