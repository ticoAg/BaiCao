import { lazy, Suspense } from "react";
import { Card, Empty, Skeleton, Space, Typography } from "../ui/index";
import type { WorkbenchFrame } from "../../types/workbench";
import ErrorResultFrame from "./frames/ErrorResultFrame";
import TableResultFrame from "./frames/TableResultFrame";
import TextResultFrame from "./frames/TextResultFrame";
const GraphResultFrame = lazy(() => import("./frames/GraphResultFrame"));
const { Text } = Typography;

type FrameStreamProps = {
  frames: WorkbenchFrame[];
  isExecuting: boolean;
  onDismissFrame: (frameId: string) => void;
  onRerunFrame: (command?: string) => void;
};

const FrameStream = ({ frames, isExecuting, onDismissFrame, onRerunFrame }: FrameStreamProps) => {
  return (
    <div
      data-testid="workbench-frame-stream"
      style={{
        display: "grid",
        gap: 14,
      }}
    >
      {frames.length === 0 ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="运行第一条命令后，结果会以 frame 的方式出现在这里。"
          />
        </Card>
      ) : null}

      {isExecuting ? (
        <Card className="workbench-frame workbench-frame--pending">
          <div style={{ padding: 18 }}>
            <Space direction="vertical" size={8}>
              <Text strong style={{ color: "#203127" }}>
                正在执行命令...
              </Text>
              <Text type="secondary">结果会以新的 frame 追加到 stream 顶部。</Text>
              <Skeleton active title={{ width: "42%" }} paragraph={{ rows: 2 }} />
            </Space>
          </div>
        </Card>
      ) : null}

      {[...frames].reverse().map((frame) => {
        switch (frame.type) {
          case "graph":
            return (
              <Suspense
                key={frame.id}
                fallback={
                  <Card className="workbench-frame workbench-frame--pending">
                    <div style={{ padding: 18 }}>
                      <Skeleton active title={{ width: "38%" }} paragraph={{ rows: 3 }} />
                    </div>
                  </Card>
                }
              >
                <GraphResultFrame
                  frame={frame}
                  onDismiss={() => onDismissFrame(frame.id)}
                  onRerun={() => onRerunFrame(frame.command)}
                />
              </Suspense>
            );
          case "table":
            return (
              <TableResultFrame
                key={frame.id}
                frame={frame}
                onDismiss={() => onDismissFrame(frame.id)}
                onRerun={() => onRerunFrame(frame.command)}
              />
            );
          case "error":
            return (
              <ErrorResultFrame
                key={frame.id}
                frame={frame}
                onDismiss={() => onDismissFrame(frame.id)}
                onRerun={() => onRerunFrame(frame.command)}
              />
            );
          case "text":
          default:
            return (
              <TextResultFrame
                key={frame.id}
                frame={frame}
                onDismiss={() => onDismissFrame(frame.id)}
                onRerun={() => onRerunFrame(frame.command)}
              />
            );
        }
      })}
    </div>
  );
};

export default FrameStream;
