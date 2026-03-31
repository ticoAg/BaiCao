import { Alert, Button, Divider, Empty, Space, Tag, Typography } from "antd";
import type {
  GraphWorkbenchLabelMetaItem,
  GraphWorkbenchMetaSummary,
  GraphWorkbenchPropertyKeyMetaItem,
  GraphWorkbenchRelationshipTypeMetaItem,
  GraphWorkbenchSchemaResponse,
} from "@bai-cao/shared";
import { getGraphNodeLabelDisplayName } from "../../types/graph";

const { Text } = Typography;

interface GraphMetadataSidebarProps {
  summary: GraphWorkbenchMetaSummary | null;
  labels: GraphWorkbenchLabelMetaItem[];
  relationshipTypes: GraphWorkbenchRelationshipTypeMetaItem[];
  propertyKeys: GraphWorkbenchPropertyKeyMetaItem[];
  schema: GraphWorkbenchSchemaResponse | null;
  loading?: boolean;
  error?: unknown;
  onHighlightLabel?: (label: string) => void;
  onHighlightRelationshipType?: (relType: string) => void;
}

const GraphMetadataSidebar = ({
  summary,
  labels,
  relationshipTypes,
  propertyKeys,
  schema,
  loading = false,
  error,
  onHighlightLabel,
  onHighlightRelationshipType,
}: GraphMetadataSidebarProps) => {
  return (
    <aside
      data-testid="graph-metadata-sidebar"
      style={{
        minWidth: 260,
        width: 288,
        border: "1px solid rgba(170, 190, 176, 0.42)",
        borderRadius: 24,
        background: "linear-gradient(180deg, rgba(249, 251, 249, 0.98) 0%, rgba(244, 248, 245, 0.96) 100%)",
        boxShadow:
          "0 1px 0 rgba(255, 255, 255, 0.75) inset, 0 12px 30px rgba(27, 56, 36, 0.05)",
        padding: 20,
        overflow: "auto",
      }}
    >
      <Text strong style={{ display: "block", fontSize: 20, color: "#203127" }}>
        图数据库信息
      </Text>
      <Text type="secondary" style={{ display: "block", marginTop: 6, lineHeight: 1.6 }}>
        数据库级元信息独立于当前图谱结果加载，可用于侧栏浏览和高亮导航。
      </Text>

      {error ? (
        <Alert
          type="warning"
          showIcon
          style={{ marginTop: 16 }}
          message="元信息加载失败"
          description={(error as Error)?.message || "请稍后重试"}
        />
      ) : null}

      {loading && !summary ? (
        <div style={{ marginTop: 24 }}>
          <Text type="secondary">图数据库信息加载中...</Text>
        </div>
      ) : null}

      {summary ? (
        <div style={{ marginTop: 20 }}>
          <Text strong style={{ color: "#203127" }}>
            概览摘要
          </Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 12 }}>
            <Tag>节点 · {summary.nodeCount}</Tag>
            <Tag>关系 · {summary.relationshipCount}</Tag>
            <Tag>标签 · {summary.labelCount}</Tag>
            <Tag>属性键 · {summary.propertyKeyCount}</Tag>
            <Tag>索引 · {summary.indexCount}</Tag>
            <Tag>约束 · {summary.constraintCount}</Tag>
          </Space>
        </div>
      ) : null}

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          节点标签
        </Text>
        <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
          {labels.length ? (
            labels.map((item) => (
              <Button
                key={item.name}
                block
                style={{ justifyContent: "space-between" }}
                onClick={() => onHighlightLabel?.(item.name)}
              >
                <span>{getGraphNodeLabelDisplayName(item.name)}</span>
                <span>{item.count}</span>
              </Button>
            ))
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无节点标签" />
          )}
        </Space>
      </section>

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          关系类型
        </Text>
        <Space direction="vertical" size={8} style={{ width: "100%", marginTop: 12 }}>
          {relationshipTypes.length ? (
            relationshipTypes.map((item) => (
              <Button
                key={item.name}
                block
                style={{ justifyContent: "space-between" }}
                onClick={() => onHighlightRelationshipType?.(item.name)}
              >
                <span>{item.name}</span>
                <span>{item.count}</span>
              </Button>
            ))
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无关系类型" />
          )}
        </Space>
      </section>

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          属性键
        </Text>
        <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 12 }}>
          {propertyKeys.length ? (
            propertyKeys.map((item) => <Tag key={item.name}>{item.name}</Tag>)
          ) : (
            <Text type="secondary">暂无属性键</Text>
          )}
        </Space>
      </section>

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          结构信息
        </Text>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">索引</Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 8 }}>
            {schema?.indexes.length ? (
              schema.indexes.map((item) => <Tag key={item.name || `${item.type}-${item.properties.join("-")}`}>{item.name || item.type}</Tag>)
            ) : (
              <Text type="secondary">暂无索引</Text>
            )}
          </Space>
        </div>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">约束</Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 8 }}>
            {schema?.constraints.length ? (
              schema.constraints.map((item) => <Tag key={item.name || `${item.type}-${item.properties.join("-")}`}>{item.name || item.type}</Tag>)
            ) : (
              <Text type="secondary">暂无约束</Text>
            )}
          </Space>
        </div>
      </section>
    </aside>
  );
};

export default GraphMetadataSidebar;
