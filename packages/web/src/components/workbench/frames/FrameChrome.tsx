import { Button, Card, Space, Tag, Typography } from "antd";
import { CloseOutlined, ReloadOutlined } from "@ant-design/icons";
import type { ReactNode } from "react";
import type { WorkbenchFrame } from "../../../types/workbench";

const { Text } = Typography;

type FrameChromeProps = {
  frame: WorkbenchFrame;
  children: ReactNode;
  onDismiss?: () => void;
  onRerun?: () => void;
};

const statusColors = {
  ok: "success",
  warning: "warning",
  error: "error",
} as const;

const FrameChrome = ({ frame, children, onDismiss, onRerun }: FrameChromeProps) => {
  return (
    <Card
      className="workbench-frame"
      style={{
        borderRadius: 20,
        boxShadow: "0 12px 32px rgba(15, 23, 42, 0.08)",
      }}
      styles={{
        header: {
          paddingBlock: 14,
          paddingInline: 18,
          borderBottom: "1px solid rgba(15, 23, 42, 0.08)",
        },
        body: { padding: 0 },
      }}
      title={
        <div className="workbench-frame__title">
          <Text className="workbench-frame__eyebrow">结果帧</Text>
          <Space size={8} wrap>
            <Text strong style={{ color: "#13261d", fontSize: 16 }}>
              {frame.title}
            </Text>
            <Tag style={{ margin: 0, borderRadius: 999 }}>{frame.type}</Tag>
            <Tag color={statusColors[frame.status]} style={{ margin: 0, borderRadius: 999 }}>
              {frame.status}
            </Tag>
          </Space>
          <Text className="workbench-frame__meta">命令来源 workbench</Text>
        </div>
      }
      extra={
        <Space className="workbench-frame__actions" size={10} align="center">
          <Text className="workbench-frame__command" type="secondary" style={{ fontSize: 12, fontFamily: "ui-monospace, monospace" }}>
            {frame.command || "system"}
          </Text>
          {frame.command ? (
            <Button
              size="small"
              type="text"
              icon={<ReloadOutlined />}
              aria-label={`重新执行命令 ${frame.command}`}
              onClick={onRerun}
            />
          ) : null}
          <Button
            size="small"
            type="text"
            icon={<CloseOutlined />}
            aria-label={`关闭结果 ${frame.id}`}
            onClick={onDismiss}
          />
        </Space>
      }
    >
      {children}
    </Card>
  );
};

export default FrameChrome;
