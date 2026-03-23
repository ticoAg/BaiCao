import { memo } from "react";
import { Empty, Button, Space, Typography } from "antd";
import { NetworkGraph } from "@ant-design/graphs/es/components/network-graph";

const { Text } = Typography;

const graphContainerStyle = {
  width: "100%",
  height: "100%",
} as const;

interface GraphCanvasWorkspaceProps {
  graphOptions: Record<string, unknown>;
  onReady: (graph: any) => void;
  hasGraphData: boolean;
  onOpenQuery: () => void;
}

const GraphCanvasWorkspace = ({
  graphOptions,
  onReady,
  hasGraphData,
  onOpenQuery,
}: GraphCanvasWorkspaceProps) => {
  return (
    <div
      data-testid="graph-canvas-workspace"
      style={{
        position: "relative",
        height: "100%",
        minHeight: "100%",
        borderRadius: 22,
        overflow: "hidden",
        background:
          "radial-gradient(circle at 24% 18%, rgba(228, 240, 233, 0.96) 0%, rgba(247, 250, 248, 0.94) 34%, rgba(239, 245, 241, 0.92) 100%)",
        boxShadow: "inset 0 0 0 1px rgba(183, 201, 188, 0.38)",
      }}
    >
      {hasGraphData ? (
        <NetworkGraph {...graphOptions} onReady={onReady} containerStyle={graphContainerStyle} />
      ) : (
        <div style={{ height: "100%", display: "grid", placeItems: "center" }}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical" size={8}>
                <Text strong style={{ color: "#203127", fontSize: 16 }}>
                  等待一张新图谱进入工作区
                </Text>
                <Button type="primary" onClick={onOpenQuery}>
                  立即开始查询
                </Button>
              </Space>
            }
          />
        </div>
      )}
    </div>
  );
};

const MemoizedGraphCanvasWorkspace = memo(GraphCanvasWorkspace);

MemoizedGraphCanvasWorkspace.displayName = "GraphCanvasWorkspace";

export default MemoizedGraphCanvasWorkspace;
