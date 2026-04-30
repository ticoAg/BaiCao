// EvidenceDetail - evidence detail drawer with source navigation
import { Drawer, Descriptions, Tag, Typography, Button, Space, Divider } from "../ui/index";
import {
  LinkOutlined,
  BookOutlined,
  FileTextOutlined,
} from "../ui/icons";
import { useNavigate } from "react-router-dom";
import { statusColors, statusLabels } from "../../types/provenance";

const { Paragraph, Text } = Typography;

export interface EvidenceDetailData {
  id: string;
  content: string;
  source_name: string;
  page_reference?: string;
  status: string;
  source_url?: string;
  source_id?: string;
  relevance_score?: number;
  [key: string]: unknown;
}

interface EvidenceDetailProps {
  evidence: EvidenceDetailData | null;
  open: boolean;
  onClose: () => void;
}

function isExternalUrl(url: string): boolean {
  try { return new URL(url).protocol.startsWith("http"); } catch { return false; }
}

const EvidenceDetail = ({ evidence, open, onClose }: EvidenceDetailProps) => {
  const navigate = useNavigate();

  if (!evidence) {
    return (
      <Drawer
        title="证据详情"
        open={open}
        onClose={onClose}
        width={480}
      >
        <Text type="secondary">未选择证据</Text>
      </Drawer>
    );
  }

  const handleSourceNavigation = () => {
    if (!evidence) return;

    const url = evidence.source_url as string | undefined;

    // external link: open in new tab
    if (url && isExternalUrl(url)) {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }

    // internal source: navigate within app
    if (evidence.source_id) {
      navigate(`/herb/${evidence.source_id}`);
      onClose();
      return;
    }

    // fallback: navigate by source_name search
    if (evidence.source_name) {
      navigate(
        `/search?q=${encodeURIComponent(evidence.source_name)}`,
      );
      onClose();
    }
  };

  return (
    <Drawer
      title={
        <Space>
          <FileTextOutlined />
          <span>证据详情</span>
          <Tag
            color={statusColors[evidence.status] || "default"}
            style={{ borderRadius: 6 }}
          >
            {statusLabels[evidence.status] || evidence.status}
          </Tag>
        </Space>
      }
      open={open}
      onClose={onClose}
      width={480}
      footer={
        <Space>
          <Button
            type="primary"
            icon={<LinkOutlined />}
            onClick={handleSourceNavigation}
            style={{ borderRadius: 8 }}
          >
            查看来源
          </Button>
          <Button onClick={onClose} style={{ borderRadius: 8 }}>
            关闭
          </Button>
        </Space>
      }
    >
      <Descriptions column={1} bordered size="small">
        <Descriptions.Item label="来源">
          <Space>
            <BookOutlined />
            <Text strong>{evidence.source_name}</Text>
          </Space>
        </Descriptions.Item>

        {evidence.page_reference && (
          <Descriptions.Item label="页码引用">
            <Text>p.{evidence.page_reference}</Text>
          </Descriptions.Item>
        )}

        {evidence.relevance_score !== undefined && (
          <Descriptions.Item label="关联度">
            <Tag
              color={
                evidence.relevance_score > 0.8
                  ? "green"
                  : evidence.relevance_score > 0.5
                    ? "orange"
                    : "red"
              }
              style={{ borderRadius: 6 }}
            >
              {(evidence.relevance_score * 100).toFixed(0)}%
            </Tag>
          </Descriptions.Item>
        )}

        <Descriptions.Item label="状态">
          <Tag
            color={statusColors[evidence.status] || "default"}
            style={{ borderRadius: 6 }}
          >
            {statusLabels[evidence.status] || evidence.status}
          </Tag>
        </Descriptions.Item>
      </Descriptions>

      <Divider orientation="left" plain>
        证据内容
      </Divider>

      <Paragraph
        style={{
          background: "#f5f5f5",
          padding: 12,
          borderRadius: 8,
          lineHeight: 1.8,
        }}
      >
        {evidence.content}
      </Paragraph>
    </Drawer>
  );
};

export default EvidenceDetail;
