// LineageChain - entity->evidence->source lineage visualization
import { Timeline, Tag, Typography, Empty, Space, Card } from "../ui/index";
import {
  DatabaseOutlined,
  FileSearchOutlined,
  BookOutlined,
} from "../ui/icons";
import type { LineageChain as LineageChainType } from "../../services/api";
import { statusIcon, getNodeName, getNodeType, getNodeStatus } from "../../types/provenance";

const { Text } = Typography;

interface LineageChainProps {
  lineage: LineageChainType | null;
  loading?: boolean;
}

const LineageChainComponent = ({
  lineage,
  loading = false,
}: LineageChainProps) => {
  if (loading) {
    return (
      <Card loading style={{ borderRadius: 8 }} />
    );
  }

  if (!lineage) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无溯源链路"
      />
    );
  }

  const { entity, evidence, source } = lineage;

  const items = [
    {
      key: "entity",
      icon: <DatabaseOutlined />,
      label: "实体",
      node: entity,
      color: "#1677ff" as const,
    },
    {
      key: "evidence",
      icon: <FileSearchOutlined />,
      label: "证据",
      node: evidence,
      color: "#2e7d32" as const,
    },
    {
      key: "source",
      icon: <BookOutlined />,
      label: "来源",
      node: source,
      color: "#722ed1" as const,
    },
  ];

  return (
    <Timeline
      items={items.map((item) => {
        const name = getNodeName(item.node);
        const type = getNodeType(item.node);
        const status = getNodeStatus(item.node);

        return {
          key: item.key,
          color: item.color,
          dot: item.icon,
          children: (
            <Space direction="vertical" size={2}>
              <Space size={6}>
                <Tag
                  color={item.color}
                  style={{ borderRadius: 6 }}
                >
                  {item.label}
                </Tag>
                <Text strong>{name}</Text>
                {status && statusIcon(status)}
              </Space>
              {type && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {type}
                </Text>
              )}
            </Space>
          ),
        };
      })}
    />
  );
};

export default LineageChainComponent;
