// 推理链展示组件
import { Collapse, List, Space, Tag, Typography } from "antd";
import { InfoCircleOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import type { ReasoningStep } from "../../types/chat";

const { Text } = Typography;

interface ReasoningChainProps {
  chain: ReasoningStep[];
}

const ReasoningChain = ({ chain }: ReasoningChainProps) => {
  const navigate = useNavigate();

  return (
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
                  <Space direction="vertical" size={4} style={{ width: "100%" }}>
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
                    {item.entities && item.entities.length > 0 && (
                      <Space size={[4, 4]} wrap style={{ paddingLeft: 24 }}>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          实体:
                        </Text>
                        {item.entities.map((entity) => (
                          <Tag
                            key={entity}
                            color="blue"
                            style={{ cursor: "pointer", fontSize: 11 }}
                            onClick={() =>
                              navigate(`/graph/${encodeURIComponent(entity)}`)
                            }
                          >
                            {entity}
                          </Tag>
                        ))}
                      </Space>
                    )}
                    {item.relations && item.relations.length > 0 && (
                      <Space size={[4, 4]} wrap style={{ paddingLeft: 24 }}>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          关系:
                        </Text>
                        {item.relations.map((relation) => (
                          <Tag
                            key={relation}
                            color="geekblue"
                            style={{ fontSize: 11 }}
                          >
                            {relation}
                          </Tag>
                        ))}
                      </Space>
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
};

export default ReasoningChain;
