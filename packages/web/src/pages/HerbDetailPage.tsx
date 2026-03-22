// 药材详情页
import {
  Card,
  Typography,
  Descriptions,
  Tag,
  List,
  Breadcrumb,
  Skeleton,
  Result,
  Button,
  Space,
  Empty,
  Divider,
} from "antd";
import {
  ArrowLeftOutlined,
  ExperimentOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  WarningOutlined,
  ApartmentOutlined,
  InfoCircleOutlined,
} from "@ant-design/icons";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useHerbDetail } from "../hooks/useHerbDetail";

const { Title, Text, Paragraph } = Typography;

const cardStyle = {
  borderRadius: 12,
  border: "none",
  boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
  marginBottom: 16,
};

const sectionTitleStyle = {
  margin: 0,
  fontSize: 16,
};

const HerbDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { herb, evidence, evidenceCount, loading, error } = useHerbDetail(id);

  if (loading) {
    return (
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <Skeleton active paragraph={{ rows: 2 }} style={{ marginBottom: 16 }} />
        <Skeleton active paragraph={{ rows: 4 }} style={{ marginBottom: 16 }} />
        <Skeleton active paragraph={{ rows: 3 }} style={{ marginBottom: 16 }} />
        <Skeleton active paragraph={{ rows: 2 }} />
      </div>
    );
  }

  if (error || !herb) {
    return (
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <Result
          status="error"
          title="无法加载药材信息"
          subTitle={error ? String(error) : "未找到该药材"}
          extra={
            <Button type="primary" onClick={() => navigate(-1)}>
              返回
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      {/* 面包屑导航 */}
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <Link to="/">首页</Link> },
          { title: <Link to="/search">搜索</Link> },
          { title: herb.name },
        ]}
      />

      {/* 基本信息 */}
      <Card
        style={cardStyle}
        title={
          <Space>
            <InfoCircleOutlined style={{ color: "#1677ff" }} />
            <Text strong style={sectionTitleStyle}>基本信息</Text>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ApartmentOutlined />}
              onClick={() => navigate(`/graph/${encodeURIComponent(herb.name)}`)}
            >
              查看图谱
            </Button>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate(-1)}
            >
              返回
            </Button>
          </Space>
        }
      >
        <Descriptions column={{ xs: 1, sm: 2 }} bordered size="small">
          <Descriptions.Item label="名称">
            <Text strong>{herb.name}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="分类">
            <Tag color="blue">{herb.category}</Tag>
          </Descriptions.Item>
          {herb.latin_name && (
            <Descriptions.Item label="拉丁名">
              <Text italic>{herb.latin_name}</Text>
            </Descriptions.Item>
          )}
          {herb.alias && herb.alias.length > 0 && (
            <Descriptions.Item label="别名">
              <Space size={[4, 4]} wrap>
                {herb.alias.map((a) => (
                  <Tag key={a}>{a}</Tag>
                ))}
              </Space>
            </Descriptions.Item>
          )}
        </Descriptions>
        {herb.description && (
          <Paragraph style={{ marginTop: 12, marginBottom: 0, color: "#595959" }}>
            {herb.description}
          </Paragraph>
        )}
      </Card>

      {/* 功效 */}
      <Card
        style={cardStyle}
        title={
          <Space>
            <ExperimentOutlined style={{ color: "#52c41a" }} />
            <Text strong style={sectionTitleStyle}>功效</Text>
          </Space>
        }
      >
        {herb.efficacy && herb.efficacy.length > 0 ? (
          <Space size={[8, 8]} wrap>
            {herb.efficacy.map((e) => (
              <Tag key={e} color="green" style={{ borderRadius: 6 }}>
                {e}
              </Tag>
            ))}
          </Space>
        ) : (
          <Empty description="暂无功效信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      {/* 性味归经 */}
      <Card
        style={cardStyle}
        title={
          <Space>
            <MedicineBoxOutlined style={{ color: "#722ed1" }} />
            <Text strong style={sectionTitleStyle}>性味归经</Text>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: "100%" }}>
          <div>
            <Text type="secondary">性味: </Text>
            {herb.flavor && herb.flavor.length > 0 ? (
              <Space size={[4, 4]} wrap>
                {herb.flavor.map((f) => (
                  <Tag key={f} color="orange" style={{ borderRadius: 6 }}>
                    {f}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">暂无</Text>
            )}
          </div>
          <div>
            <Text type="secondary">归经: </Text>
            {herb.meridian && herb.meridian.length > 0 ? (
              <Space size={[4, 4]} wrap>
                {herb.meridian.map((m) => (
                  <Tag key={m} color="purple" style={{ borderRadius: 6 }}>
                    {m}
                  </Tag>
                ))}
              </Space>
            ) : (
              <Text type="secondary">暂无</Text>
            )}
          </div>
        </Space>
      </Card>

      {/* 用法用量 */}
      <Card
        style={cardStyle}
        title={
          <Space>
            <FileTextOutlined style={{ color: "#1677ff" }} />
            <Text strong style={sectionTitleStyle}>用法用量</Text>
          </Space>
        }
      >
        {herb.dosage ? (
          <Paragraph style={{ margin: 0 }}>{herb.dosage}</Paragraph>
        ) : (
          <Empty description="暂无用法用量信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      {/* 禁忌 */}
      <Card
        style={cardStyle}
        title={
          <Space>
            <WarningOutlined style={{ color: "#f5222d" }} />
            <Text strong style={sectionTitleStyle}>禁忌</Text>
          </Space>
        }
      >
        {herb.contraindications ? (
          <Paragraph style={{ margin: 0, color: "#cf1322" }}>
            {herb.contraindications}
          </Paragraph>
        ) : (
          <Empty description="暂无禁忌信息" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      {/* 关联证据 */}
      <Card
        style={cardStyle}
        title={
          <Space>
            <FileTextOutlined style={{ color: "#fa8c16" }} />
            <Text strong style={sectionTitleStyle}>
              关联证据 {evidenceCount > 0 && `(${evidenceCount})`}
            </Text>
          </Space>
        }
      >
        {evidence.length > 0 ? (
          <List
            dataSource={evidence}
            renderItem={(item: Record<string, unknown>, index: number) => (
              <List.Item key={index}>
                <List.Item.Meta
                  title={
                    <Text>
                      {(item.source_name as string) || `证据 ${index + 1}`}
                    </Text>
                  }
                  description={
                    <Space direction="vertical" size={4}>
                      {item.content && (
                        <Text type="secondary">{item.content as string}</Text>
                      )}
                      {item.page_reference && (
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          页码: {item.page_reference as string}
                        </Text>
                      )}
                      {item.status && (
                        <Tag
                          color={item.status === "verified" ? "green" : "gold"}
                          style={{ borderRadius: 6 }}
                        >
                          {item.status === "verified" ? "已验证" : "待验证"}
                        </Tag>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty description="暂无关联证据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Card>

      <Divider />
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <Space>
          <Button
            type="primary"
            icon={<ApartmentOutlined />}
            onClick={() => navigate(`/graph/${encodeURIComponent(herb.name)}`)}
          >
            在图谱中查看
          </Button>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
            返回
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default HerbDetailPage;
