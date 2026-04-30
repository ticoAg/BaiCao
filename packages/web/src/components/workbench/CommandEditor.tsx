import { Button, Input, Space, Typography } from "../ui/index";
import type { KeyboardEvent } from "react";

type CommandEditorProps = {
  value: string;
  loading: boolean;
  showStarterCommands: boolean;
  onChange: (value: string) => void;
  onRun: () => void;
  onFavorite: () => void;
  onClear: () => void;
};

const { Text } = Typography;

const starterCommands = [":help", ":clear", "查人参的功效"];

const CommandEditor = ({
  value,
  loading,
  showStarterCommands,
  onChange,
  onRun,
  onFavorite,
  onClear,
}: CommandEditorProps) => {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      onRun();
    }
  };

  return (
    <div
      data-testid="workbench-editor"
      style={{
        borderRadius: 20,
        background: "#111827",
        padding: 20,
        color: "#fff",
      }}
    >
      <Text style={{ color: "rgba(255,255,255,0.72)", display: "block", marginBottom: 10 }}>
        Graph Workbench
      </Text>
      {showStarterCommands ? (
        <Space size={[8, 8]} wrap style={{ marginBottom: 12 }}>
          {starterCommands.map((command) => (
            <Button
              key={command}
              size="small"
              type="default"
              aria-label={`插入起手命令 ${command}`}
              onClick={() => onChange(command)}
              style={{
                borderRadius: 999,
                background: "rgba(148, 163, 184, 0.14)",
                borderColor: "rgba(148, 163, 184, 0.3)",
                color: "#d7e2f0",
                boxShadow: "none",
              }}
            >
              {command}
            </Button>
          ))}
        </Space>
      ) : null}
      <Input.TextArea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="输入 :help、Cypher，或自然语言查询"
        autoSize={{ minRows: 5, maxRows: 10 }}
        styles={{
          textarea: {
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            background: "#0b1220",
            color: "#e5eef7",
          },
        }}
      />
      <Space style={{ marginTop: 12 }}>
        <Button type="primary" loading={loading} onClick={onRun}>
          运行
        </Button>
        <Button aria-label="收藏当前命令" onClick={onFavorite}>
          收藏
        </Button>
        <Button aria-label="清空编辑器与结果" onClick={onClear}>
          清空
        </Button>
        <Text style={{ color: "rgba(255,255,255,0.52)", fontSize: 12 }}>
          Ctrl/Cmd + Enter 运行
        </Text>
      </Space>
    </div>
  );
};

export default CommandEditor;
