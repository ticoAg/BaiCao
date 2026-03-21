// 推理链展示组件
import { Collapse, List, Space, Tag, Typography } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import type { ReasoningStep } from "../../types/chat";

const { Text } = Typography;

interface ReasoningChainProps {
  chain: ReasoningStep[];
}

const ReasoningChain = ({ chain }: ReasoningChainProps) => (
  <Collapse
    ghost
    items={[
      {
        key: "reasoning",
        label: (
          <Text type="secondary">
            <InfoCircleOutlined /> 推理链
          </Text>
        ),
        children: (
          <List
            size="small"
            dataSource={chain}
            renderItem={(item) => (
              <List.Item style={{ padding: "4px 0" }}>
                <Space>
                  <Tag color="blue">{item.step}</Tag>
                  <Text>{item.description}</Text>
                  {item.confidence && (
                    <Tag
                      color={
                        item.confidence > 0.8
                          ? "green"
                          : item.confidence > 0.5
                            ? "orange"
                            : "red"
                      }
                    >
                      {(item.confidence * 100).toFixed(0)}%
                    </Tag>
                  )}
                </Space>
              </List.Item>
            )}
          />
        ),
      },
    ]}
  />
);

export default ReasoningChain;
