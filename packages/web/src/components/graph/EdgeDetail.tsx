// 关系详情面板
import { Descriptions, Tag, Typography } from "antd";
import type { GraphEdge } from "../../types/graph";
import { relTypeLabels } from "../../types/graph";
import { statusColors, statusLabels } from "../../types/index";

const { Text } = Typography;

interface EdgeDetailProps {
  edge: GraphEdge & { sourceName?: string; targetName?: string };
}

const EdgeDetail = ({ edge }: EdgeDetailProps) => (
  <div>
    <Text strong style={{ fontSize: 16 }}>
      关系详情
    </Text>
    <Descriptions column={1} size="small" bordered style={{ marginTop: 12 }}>
      <Descriptions.Item label="关系类型">
        {relTypeLabels[edge.rel_type || ""] || edge.rel_type || "\u2014"}
      </Descriptions.Item>
      <Descriptions.Item label="起始节点">
        {edge.sourceName || "\u2014"}
      </Descriptions.Item>
      <Descriptions.Item label="目标节点">
        {edge.targetName || "\u2014"}
      </Descriptions.Item>
      <Descriptions.Item label="状态">
        <Tag color={statusColors[edge.status]}>{statusLabels[edge.status]}</Tag>
      </Descriptions.Item>
      {edge.verification_id && (
        <Descriptions.Item label="验证ID">{edge.verification_id}</Descriptions.Item>
      )}
      {edge.verified_at && (
        <Descriptions.Item label="验证时间">
          {new Date(edge.verified_at).toLocaleString("zh-CN")}
        </Descriptions.Item>
      )}
    </Descriptions>
  </div>
);

export default EdgeDetail;
