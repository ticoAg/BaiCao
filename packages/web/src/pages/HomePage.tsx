import { Card, Typography, Space, Tag, Row, Col } from "antd";
import { useNavigate } from "react-router-dom";
import {
  SearchOutlined,
  NodeIndexOutlined,
  CheckCircleOutlined,
  MessageOutlined,
  ExperimentOutlined,
  SafetyCertificateOutlined,
  ApartmentOutlined,
  FileSearchOutlined,
} from "@ant-design/icons";

const { Title, Paragraph, Text } = Typography;

const featureCards = [
  {
    icon: <SearchOutlined style={{ fontSize: 32 }} />,
    title: "知识搜索",
    desc: "搜索药材、功效、归经等中药材知识",
    path: "/search",
    gradient: "linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)",
    iconColor: "#2e7d32",
  },
  {
    icon: <ApartmentOutlined style={{ fontSize: 32 }} />,
    title: "图谱浏览",
    desc: "可视化探索药材知识关系网络",
    path: "/graph/人参",
    gradient: "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
    iconColor: "#1565c0",
  },
  {
    icon: <MessageOutlined style={{ fontSize: 32 }} />,
    title: "智能问答",
    desc: "AI 驱动的中药材知识智能问答",
    path: "/chat",
    gradient: "linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)",
    iconColor: "#e65100",
  },
  {
    icon: <CheckCircleOutlined style={{ fontSize: 32 }} />,
    title: "验证管理",
    desc: "专家审核验证，确保知识可信",
    path: "/verification",
    gradient: "linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%)",
    iconColor: "#7b1fa2",
  },
];

const highlights = [
  {
    icon: <NodeIndexOutlined />,
    tag: "知识图谱",
    tagColor: "green",
    text: "基于 Neo4j 的中药材实体、关系、功效知识图谱",
  },
  {
    icon: <ExperimentOutlined />,
    tag: "智能问答",
    tagColor: "blue",
    text: "基于大语言模型的智能问答，支持推理链展示",
  },
  {
    icon: <FileSearchOutlined />,
    tag: "数据溯源",
    tagColor: "orange",
    text: "每个答案都可追溯到原始文献和数据来源",
  },
  {
    icon: <SafetyCertificateOutlined />,
    tag: "专家验证",
    tagColor: "purple",
    text: "知识可由专家审核验证，状态透明",
  },
];

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Hero 区域 */}
      <div
        style={{
          textAlign: "center",
          padding: "48px 24px 40px",
          background: "linear-gradient(180deg, #e8f5e9 0%, transparent 100%)",
          borderRadius: 16,
          marginBottom: 32,
        }}
      >
        <div style={{ fontSize: 48, marginBottom: 12 }}>🌿</div>
        <Title
          level={1}
          style={{
            fontSize: 36,
            marginBottom: 8,
            color: '#1a3a2a',
          }}
        >
          白草药坛
        </Title>
        <Paragraph
          style={{
            fontSize: 18,
            color: "#555",
            maxWidth: 600,
            margin: "0 auto 24px",
            lineHeight: 1.8,
          }}
        >
          可溯源的中药材知识图谱智能问答系统
        </Paragraph>
        <Space size="middle">
          <Tag color="green" style={{ fontSize: 13, padding: "4px 12px" }}>
            知识可溯源
          </Tag>
          <Tag color="blue" style={{ fontSize: 13, padding: "4px 12px" }}>
            AI 驱动
          </Tag>
          <Tag color="orange" style={{ fontSize: 13, padding: "4px 12px" }}>
            专家验证
          </Tag>
        </Space>
      </div>

      {/* 功能卡片 */}
      <Row gutter={[20, 20]} style={{ marginBottom: 40 }}>
        {featureCards.map((card) => (
          <Col xs={24} sm={12} lg={6} key={card.title}>
            <Card
              hoverable
              onClick={() => navigate(card.path)}
              style={{
                height: "100%",
                borderRadius: 12,
                border: "none",
                overflow: "hidden",
                transition: "all 0.3s ease",
              }}
              styles={{
                body: {
                  padding: 24,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  textAlign: "center",
                },
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 16,
                  background: card.gradient,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: card.iconColor,
                  marginBottom: 16,
                }}
              >
                {card.icon}
              </div>
              <Title level={4} style={{ marginBottom: 8 }}>
                {card.title}
              </Title>
              <Text type="secondary" style={{ fontSize: 13 }}>
                {card.desc}
              </Text>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 核心特性 */}
      <Card
        style={{
          borderRadius: 12,
          border: "none",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
        }}
      >
        <Title level={4} style={{ marginBottom: 24, textAlign: "center" }}>
          核心特性
        </Title>
        <Row gutter={[24, 20]}>
          {highlights.map((h) => (
            <Col xs={24} sm={12} key={h.tag}>
              <Space align="start" size={12}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: "#f6ffed",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#2e7d32",
                    fontSize: 18,
                    flexShrink: 0,
                  }}
                >
                  {h.icon}
                </div>
                <div>
                  <Tag color={h.tagColor} style={{ marginBottom: 4 }}>
                    {h.tag}
                  </Tag>
                  <br />
                  <Text style={{ fontSize: 13, color: "#555" }}>{h.text}</Text>
                </div>
              </Space>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
};

export default HomePage;
