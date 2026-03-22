// 节点详情面板
import { Descriptions, Tag, Typography, Button, Space, message } from "antd";
import { EyeOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { GraphNode } from "../../types/graph";
import { labelTagColors } from "../../types/graph";
import { statusColors, statusLabels } from "../../types/index";

const { Text } = Typography;

interface NodeDetailProps {
  node: GraphNode;
}

const NodeDetail = ({ node }: NodeDetailProps) => {
  const navigate = useNavigate();
  const primaryLabel = node.labels?.[0] || "Unknown";
  const isHerbNode = primaryLabel === "Herb";
  return (
    <div>
      <Text strong style={{ fontSize: 16 }}>
        节点详情
      </Text>
      <Descriptions column={1} size="small" bordered style={{ marginTop: 12 }}>
        <Descriptions.Item label="名称">
          <Text strong>{node.name}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="类型">
          <Tag color={labelTagColors[primaryLabel] || "default"}>{primaryLabel}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="状态">
          <Tag color={statusColors[node.status]}>{statusLabels[node.status]}</Tag>
        </Descriptions.Item>
        {node.source && <Descriptions.Item label="来源">{node.source}</Descriptions.Item>}
        {node.category && <Descriptions.Item label="分类">{node.category}</Descriptions.Item>}
        {node.description && (
          <Descriptions.Item label="描述">{node.description}</Descriptions.Item>
        )}
        {node.latin_name && (
          <Descriptions.Item label="拉丁名">{node.latin_name}</Descriptions.Item>
        )}
        {node.verification_id && (
          <Descriptions.Item label="验证ID">{node.verification_id}</Descriptions.Item>
        )}
        {node.verified_by && (
          <Descriptions.Item label="验证人">{node.verified_by}</Descriptions.Item>
        )}
        {node.verified_at && (
          <Descriptions.Item label="验证时间">
            {new Date(node.verified_at).toLocaleString("zh-CN")}
          </Descriptions.Item>
        )}
      </Descriptions>
      {node.status === "pending" && (
        <div style={{ marginTop: 12 }}>
          <a onClick={() => message.info("跳转到验证申请页面")}>申请验证</a>
        </div>
      )}
      {isHerbNode && (
        <div style={{ marginTop: 12 }}>
          <Button
            type="primary"
            icon={<EyeOutlined />}
            size="small"
            style={{ borderRadius: 6 }}
            onClick={() => navigate(`/herb/${node.id}`)}
          >
            查看完整详情
          </Button>
        </div>
      )}
    </div>
  );
};

export default NodeDetail;
