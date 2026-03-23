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
        minHeight: "calc(100vh - 64px)",
        background:
          "radial-gradient(circle at 24% 18%, rgba(228, 240, 233, 0.95) 0%, rgba(245, 248, 246, 0.92) 30%, rgba(238, 244, 240, 0.9) 100%)",
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

export default GraphCanvasWorkspace;
