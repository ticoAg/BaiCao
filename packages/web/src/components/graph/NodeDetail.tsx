// 节点详情面板
import { Button, Descriptions, Space, Tag, Tooltip, Typography, message } from "antd";
import { CopyOutlined, EyeOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { GraphNode } from "../../types/graph";
import { labelTagColors } from "../../types/graph";
import { statusColors, statusLabels } from "../../types/index";

const { Paragraph, Text } = Typography;

interface NodeDetailProps {
  node: GraphNode;
}

function truncateMiddle(value: string, start = 6, end = 4) {
  if (value.length <= start + end + 3) {
    return value;
  }

  return `${value.slice(0, start)}...${value.slice(-end)}`;
}

async function copyText(value: string, successLabel: string) {
  try {
    await navigator.clipboard.writeText(value);
    message.success(`${successLabel}已复制`);
  } catch {
    message.error("复制失败，请稍后重试");
  }
}

function InlineMetaValue({ label, value }: { label: string; value: string }) {
  return (
    <Space size={8}>
      <Tooltip title={value}>
        <Text code style={{ margin: 0 }}>
          {truncateMiddle(value)}
        </Text>
      </Tooltip>
      <Tooltip title={`复制${label}`}>
        <Button
          type="text"
          size="small"
          aria-label={`复制${label}`}
          icon={<CopyOutlined />}
          onClick={() => copyText(value, label)}
        />
      </Tooltip>
    </Space>
  );
}

const detailStyles = {
  label: { color: "#7A867F", width: 72, fontSize: 13 },
  content: { color: "#1f2a24", fontWeight: 500, fontSize: 14 },
};

const NodeDetail = ({ node }: NodeDetailProps) => {
  const navigate = useNavigate();
  const primaryLabel = node.labels?.[0] || "Unknown";
  const isHerbNode = primaryLabel === "Herb";

  return (
    <div>
      <Text type="secondary" style={{ fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        节点
      </Text>
      <Text strong style={{ display: "block", fontSize: 18, color: "#203127", marginTop: 6, textWrap: "balance" }}>
        {node.name}
      </Text>

      <Space size={[8, 8]} wrap style={{ marginTop: 10 }}>
        <Tag color={labelTagColors[primaryLabel] || "default"} style={{ borderRadius: 999, marginInlineEnd: 0 }}>
          {primaryLabel}
        </Tag>
        <Tag color={statusColors[node.status]} style={{ borderRadius: 999, marginInlineEnd: 0 }}>
          {statusLabels[node.status]}
        </Tag>
      </Space>

      <Descriptions
        column={1}
        size="small"
        style={{ marginTop: 18 }}
        styles={detailStyles}
      >
        <Descriptions.Item label="ID">
          <InlineMetaValue label="节点ID" value={node.id} />
        </Descriptions.Item>
        {node.source ? <Descriptions.Item label="来源">{node.source}</Descriptions.Item> : null}
        {node.category ? <Descriptions.Item label="分类">{node.category}</Descriptions.Item> : null}
        {node.description ? (
          <Descriptions.Item label="描述">
            <Paragraph style={{ marginBottom: 0, color: "inherit" }}>{node.description}</Paragraph>
          </Descriptions.Item>
        ) : null}
        {node.latin_name ? <Descriptions.Item label="拉丁名">{node.latin_name}</Descriptions.Item> : null}
        {node.verification_id ? (
          <Descriptions.Item label="验证ID">
            <InlineMetaValue label="验证ID" value={node.verification_id} />
          </Descriptions.Item>
        ) : null}
        {node.verified_by ? (
          <Descriptions.Item label="验证人">
            <InlineMetaValue label="验证人" value={node.verified_by} />
          </Descriptions.Item>
        ) : null}
        {node.verified_at ? (
          <Descriptions.Item label="验证时间">
            {new Date(node.verified_at).toLocaleString("zh-CN")}
          </Descriptions.Item>
        ) : null}
      </Descriptions>

      {node.status === "pending" ? (
        <div style={{ marginTop: 14 }}>
          <Button type="link" style={{ padding: 0 }} onClick={() => message.info("跳转到验证申请页面")}>
            申请验证
          </Button>
        </div>
      ) : null}

      {isHerbNode ? (
        <div style={{ marginTop: 14 }}>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            size="small"
            style={{ borderRadius: 999 }}
            onClick={() => navigate(`/herb/${node.id}`)}
          >
            查看完整详情
          </Button>
        </div>
      ) : null}
    </div>
  );
};

export default NodeDetail;
