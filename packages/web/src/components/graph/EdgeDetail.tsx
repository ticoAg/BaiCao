// 关系详情面板
import { Button, Descriptions, Space, Tag, Tooltip, Typography, message } from "antd";
import { CopyOutlined } from "@ant-design/icons";
import type { GraphEdge } from "../../types/graph";
import { relTypeLabels } from "../../types/graph";
import { statusColors, statusLabels } from "../../types/index";

const { Text } = Typography;

interface EdgeDetailProps {
  edge: GraphEdge & { sourceName?: string; targetName?: string };
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
        <Text code>{truncateMiddle(value)}</Text>
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

const EdgeDetail = ({ edge }: EdgeDetailProps) => (
  <div>
    <Text type="secondary" style={{ fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
      关系
    </Text>
    <Text strong style={{ display: "block", fontSize: 18, color: "#203127", marginTop: 6, textWrap: "balance" }}>
      {relTypeLabels[edge.rel_type || ""] || edge.rel_type || "未命名关系"}
    </Text>

    <Space size={[8, 8]} wrap style={{ marginTop: 10 }}>
      <Tag color={statusColors[edge.status]} style={{ borderRadius: 999, marginInlineEnd: 0 }}>
        {statusLabels[edge.status]}
      </Tag>
    </Space>

    <Descriptions column={1} size="small" style={{ marginTop: 18 }} styles={detailStyles}>
      {edge.id ? (
        <Descriptions.Item label="ID">
          <InlineMetaValue label="关系ID" value={edge.id} />
        </Descriptions.Item>
      ) : null}
      <Descriptions.Item label="起始节点">{edge.sourceName || "\u2014"}</Descriptions.Item>
      <Descriptions.Item label="目标节点">{edge.targetName || "\u2014"}</Descriptions.Item>
      {edge.verification_id ? (
        <Descriptions.Item label="验证ID">
          <InlineMetaValue label="验证ID" value={edge.verification_id} />
        </Descriptions.Item>
      ) : null}
      {edge.verified_by ? (
        <Descriptions.Item label="验证人">
          <InlineMetaValue label="验证人" value={edge.verified_by} />
        </Descriptions.Item>
      ) : null}
      {edge.verified_at ? (
        <Descriptions.Item label="验证时间">
          {new Date(edge.verified_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
      ) : null}
    </Descriptions>
  </div>
);

export default EdgeDetail;
