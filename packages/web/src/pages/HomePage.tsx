import { Card, Typography, Space, Tag, Row, Col } from "antd";
import { useNavigate } from "react-router-dom";
import { SearchOutlined, NodeIndexOutlined, CheckCircleOutlined } from "@ant-design/icons";

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <Title level={2}>欢迎使用白草药坛</Title>
      <Paragraph>
        白草药坛是一个<strong>可溯源的中药材知识图谱智能问答系统</strong>。
      </Paragraph>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card
            hoverable
            style={{ textAlign: "center", height: 160 }}
            onClick={() => navigate("/search")}
            cover={
              <div style={{ padding: 24 }}>
                <SearchOutlined style={{ fontSize: 48, color: "#1890ff" }} />
              </div>
            }
          >
            <Title level={4}>知识搜索</Title>
            <Paragraph type="secondary">搜索药材、功效、归经等</Paragraph>
          </Card>
        </Col>

        <Col span={8}>
          <Card
            hoverable
            style={{ textAlign: "center", height: 160 }}
            onClick={() => navigate("/graph/人参")}
            cover={
              <div style={{ padding: 24 }}>
                <NodeIndexOutlined style={{ fontSize: 48, color: "#52c41a" }} />
              </div>
            }
          >
            <Title level={4}>图谱浏览</Title>
            <Paragraph type="secondary">可视化知识图谱</Paragraph>
          </Card>
        </Col>

        <Col span={8}>
          <Card
            hoverable
            style={{ textAlign: "center", height: 160 }}
            onClick={() => navigate("/verification")}
            cover={
              <div style={{ padding: 24 }}>
                <CheckCircleOutlined style={{ fontSize: 48, color: "#faad14" }} />
              </div>
            }
          >
            <Title level={4}>验证管理</Title>
            <Paragraph type="secondary">申请或审核知识</Paragraph>
          </Card>
        </Col>
      </Row>

      <Card title="核心特性" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <div>
            <Tag color="green">知识图谱</Tag>
            基于 Neo4j 的中药材实体、关系、功效知识图谱
          </div>
          <div>
            <Tag color="blue">智能问答</Tag>
            基于大语言模型的智能问答，支持推理链展示
          </div>
          <div>
            <Tag color="orange">数据溯源</Tag>
            每个答案都可追溯到原始文献和数据来源
          </div>
          <div>
            <Tag color="purple">专家验证</Tag>
            知识可由专家审核验证，状态透明
          </div>
        </Space>
      </Card>

      <Card title="技术栈">
        <Space direction="vertical" style={{ width: "100%" }}>
          <Paragraph>
            <strong>后端</strong>：Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Neo4j
          </Paragraph>
          <Paragraph>
            <strong>前端</strong>：React 18 / TypeScript / Ant Design 5 / TanStack Query
          </Paragraph>
          <Paragraph>
            <strong>基础设施</strong>：PostgreSQL 15 / Neo4j 5 / Docker Compose
          </Paragraph>
        </Space>
      </Card>
    </div>
  );
};

export default HomePage;
