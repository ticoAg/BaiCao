import { Button, Empty, Space, Tag, Typography } from "antd";
import type { SelectedItem } from "../../types/graph";
import EdgeDetail from "./EdgeDetail";
import NodeDetail from "./NodeDetail";

const { Text } = Typography;

interface GraphInspectorPanelProps {
  selectedItem: SelectedItem | null;
  nodeCount: number;
  relationshipCount: number;
  labelStats: Array<{ key: string; count: number }>;
  relTypeStats: Array<{ key: string; count: number; label: string }>;
  onHighlightLabel?: (label: string) => void;
  onHighlightRelationshipType?: (relType: string) => void;
}

const GraphInspectorPanel = ({
  selectedItem,
  nodeCount,
  relationshipCount,
  labelStats,
  relTypeStats,
  onHighlightLabel,
  onHighlightRelationshipType,
}: GraphInspectorPanelProps) => {
  return (
    <aside
      data-testid="graph-inspector-panel"
      style={{
        minWidth: 320,
        width: 360,
        borderLeft: "1px solid #e7ece9",
        background: "#fcfdfc",
        padding: 20,
        overflow: "auto",
      }}
    >
      {selectedItem?.type === "node" ? <NodeDetail node={selectedItem.data} /> : null}
      {selectedItem?.type === "edge" ? <EdgeDetail edge={selectedItem.data} /> : null}

      {!selectedItem ? (
        <div data-testid="graph-overview-panel">
          <Text type="secondary" style={{ fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Overview
          </Text>
          <Text strong style={{ display: "block", marginTop: 6, fontSize: 20, color: "#203127" }}>
            图谱概览
          </Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 14 }}>
            <Tag>{nodeCount} 个节点</Tag>
            <Tag>{relationshipCount} 条关系</Tag>
          </Space>

          <div style={{ marginTop: 18 }}>
            <Text strong style={{ color: "#203127" }}>
              节点类型
            </Text>
            <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 10 }}>
              {labelStats.length ? (
                labelStats.map((item) => (
                  <Button
                    key={item.key}
                    block
                    style={{ justifyContent: "space-between" }}
                    onClick={() => onHighlightLabel?.(item.key)}
                  >
                    <span>{item.key}</span>
                    <span>{item.count}</span>
                  </Button>
                ))
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无节点类型" />
              )}
            </Space>
          </div>

          <div style={{ marginTop: 18 }}>
            <Text strong style={{ color: "#203127" }}>
              关系类型
            </Text>
            <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 10 }}>
              {relTypeStats.length ? (
                relTypeStats.map((item) => (
                  <Button
                    key={item.key}
                    block
                    style={{ justifyContent: "space-between" }}
                    onClick={() => onHighlightRelationshipType?.(item.key)}
                  >
                    <span>{item.label}</span>
                    <span>{item.count}</span>
                  </Button>
                ))
              ) : (
                <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无关系类型" />
              )}
            </Space>
          </div>
        </div>
      ) : null}
    </aside>
  );
};

export default GraphInspectorPanel;
