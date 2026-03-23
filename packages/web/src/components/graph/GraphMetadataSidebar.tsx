import { Alert, Button, Divider, Empty, Space, Tag, Typography } from "antd";
import type {
  GraphWorkbenchLabelMetaItem,
  GraphWorkbenchMetaSummary,
  GraphWorkbenchPropertyKeyMetaItem,
  GraphWorkbenchRelationshipTypeMetaItem,
  GraphWorkbenchSchemaResponse,
} from "@bai-cao/shared";

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
        minWidth: 280,
        width: 320,
        borderRight: "1px solid #e7ece9",
        background: "#f8fbf9",
        padding: 20,
        overflow: "auto",
      }}
    >
      <Text strong style={{ display: "block", fontSize: 20, color: "#203127" }}>
        Database information
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
          <Text type="secondary">Database information 加载中...</Text>
        </div>
      ) : null}

      {summary ? (
        <div style={{ marginTop: 20 }}>
          <Text strong style={{ color: "#203127" }}>
            Summary
          </Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 12 }}>
            <Tag>Nodes · {summary.nodeCount}</Tag>
            <Tag>Relationships · {summary.relationshipCount}</Tag>
            <Tag>Labels · {summary.labelCount}</Tag>
            <Tag>Property keys · {summary.propertyKeyCount}</Tag>
            <Tag>Indexes · {summary.indexCount}</Tag>
            <Tag>Constraints · {summary.constraintCount}</Tag>
          </Space>
        </div>
      ) : null}

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          Labels
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
                <span>{item.name}</span>
                <span>{item.count}</span>
              </Button>
            ))
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 labels" />
          )}
        </Space>
      </section>

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          Relationship types
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
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无 relationship types" />
          )}
        </Space>
      </section>

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          Property keys
        </Text>
        <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 12 }}>
          {propertyKeys.length ? (
            propertyKeys.map((item) => <Tag key={item.name}>{item.name}</Tag>)
          ) : (
            <Text type="secondary">暂无 property keys</Text>
          )}
        </Space>
      </section>

      <Divider />

      <section>
        <Text strong style={{ color: "#203127" }}>
          Schema
        </Text>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">Indexes</Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 8 }}>
            {schema?.indexes.length ? (
              schema.indexes.map((item) => <Tag key={item.name || `${item.type}-${item.properties.join("-")}`}>{item.name || item.type}</Tag>)
            ) : (
              <Text type="secondary">暂无 indexes</Text>
            )}
          </Space>
        </div>
        <div style={{ marginTop: 12 }}>
          <Text type="secondary">Constraints</Text>
          <Space size={[8, 8]} wrap style={{ display: "flex", marginTop: 8 }}>
            {schema?.constraints.length ? (
              schema.constraints.map((item) => <Tag key={item.name || `${item.type}-${item.properties.join("-")}`}>{item.name || item.type}</Tag>)
            ) : (
              <Text type="secondary">暂无 constraints</Text>
            )}
          </Space>
        </div>
      </section>
    </aside>
  );
};

export default GraphMetadataSidebar;
