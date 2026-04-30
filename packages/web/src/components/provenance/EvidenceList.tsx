// EvidenceList - provenance evidence list component
import { List, Tag, Typography, Empty, Button, Space } from "../ui/index";
import {
  FileTextOutlined,
  EyeOutlined,
  BookOutlined,
} from "../ui/icons";
import { statusColors, statusLabels, type EvidenceItemBase } from "../../types/provenance";

const { Text, Paragraph } = Typography;

export type EvidenceItem = EvidenceItemBase;

interface EvidenceListProps {
  evidence: EvidenceItem[];
  loading?: boolean;
  onViewDetail?: (id: string) => void;
}

const EvidenceList = ({
  evidence,
  loading = false,
  onViewDetail,
}: EvidenceListProps) => {
  if (!loading && evidence.length === 0) {
    return (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无溯源证据"
      />
    );
  }

  return (
    <List
      loading={loading}
      dataSource={evidence}
      renderItem={(item) => (
        <List.Item
          key={item.id}
          actions={
            onViewDetail
              ? [
                  <Button
                    key="view"
                    type="link"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => onViewDetail(item.id)}
                  >
                    查看详情
                  </Button>,
                ]
              : undefined
          }
        >
          <List.Item.Meta
            avatar={<FileTextOutlined style={{ fontSize: 20, color: "#2e7d32" }} />}
            title={
              <Space size={8}>
                <Tag
                  color={statusColors[item.status] || "default"}
                  style={{ borderRadius: 6 }}
                >
                  {statusLabels[item.status] || item.status}
                </Tag>
                <Text strong>
                  <BookOutlined style={{ marginRight: 4 }} />
                  {item.source_name}
                </Text>
                {item.page_reference && (
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    p.{item.page_reference}
                  </Text>
                )}
              </Space>
            }
            description={
              <Paragraph
                ellipsis={{ rows: 2, expandable: true, symbol: "展开" }}
                style={{ marginBottom: 0, marginTop: 4 }}
              >
                {item.content}
              </Paragraph>
            }
          />
        </List.Item>
      )}
    />
  );
};

export default EvidenceList;
