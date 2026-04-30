import { useState, useEffect } from "react";
import {
  Card,
  Typography,
  Table,
  Tag,
  Space,
  Form,
  message,
  Row,
  Col,
  Statistic,
} from "../components/ui/index";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  PlusOutlined,
} from "../components/ui/icons";
import { useSearchParams } from "react-router-dom";
import { verificationApi, Verification } from "../services/api";
import ModalDialog from "../components/ui/Dialog";
import AppButton from "../components/ui/Button";
import AppSelect from "../components/ui/Select";
import { TextArea, TextInput } from "../components/ui/Field";

const { Title, Text } = Typography;

const statusColors: Record<string, string> = {
  pending: "gold",
  verified: "green",
  rejected: "red",
};

const statusLabels: Record<string, string> = {
  pending: "待验证",
  verified: "已验证",
  rejected: "已拒绝",
};

const entityTypeLabels: Record<string, string> = {
  herb: "药材",
  efficacy: "功效",
  relation: "关系",
  flavor: "性味",
  meridian: "归经",
  component: "成分",
};

const entityTypeOptions = Object.entries(entityTypeLabels).map(([value, label]) => ({
  value,
  label,
}));

const VerificationPage = () => {
  const [searchParams] = useSearchParams();
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const prefilledEntityType = searchParams.get("entity_type");
  const prefilledEntityId = searchParams.get("entity_id");
  const prefilledValue = searchParams.get("value");

  const loadVerifications = async () => {
    setLoading(true);
    try {
      const data = await verificationApi.list({ status: "pending" });
      setVerifications(data.items);
    } catch {
      message.error("加载验证列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadVerifications();
  }, []);

  useEffect(() => {
    if (prefilledEntityType && prefilledEntityId && prefilledValue) {
      form.setFieldsValue({
        entity_type: prefilledEntityType,
        entity_id: prefilledEntityId,
        claimed_value: prefilledValue,
      });
      setModalVisible(true);
    }
  }, [form, prefilledEntityType, prefilledEntityId, prefilledValue]);

  const handleVerify = async (id: string, status: "verified" | "rejected", verdict: string) => {
    try {
      await verificationApi.verify(id, undefined, status, verdict);
      message.success(`已${status === "verified" ? "通过" : "拒绝"}验证`);
      void loadVerifications();
    } catch {
      message.error("操作失败");
    }
  };

  const handleApply = async (values: any) => {
    try {
      await verificationApi.create(values);
      message.success("验证申请已提交");
      setModalVisible(false);
      form.resetFields();
      void loadVerifications();
    } catch {
      message.error("提交失败");
    }
  };

  const pendingCount = verifications.filter((v) => v.status === "pending").length;

  const columns = [
    {
      title: "实体类型",
      dataIndex: "entity_type",
      key: "entity_type",
      width: 120,
      render: (type: string) => (
        <Tag style={{ borderRadius: 6 }}>{entityTypeLabels[type] || type}</Tag>
      ),
    },
    {
      title: "声明内容",
      dataIndex: "claimed_value",
      key: "claimed_value",
      ellipsis: true,
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (status: string) => (
        <Tag color={statusColors[status]} style={{ borderRadius: 6 }}>
          {statusLabels[status] || status}
        </Tag>
      ),
    },
    {
      title: "申请时间",
      dataIndex: "created_at",
      key: "created_at",
      width: 180,
      render: (date: string) => (
        <Text type="secondary" style={{ fontSize: 13 }}>
          {new Date(date).toLocaleString("zh-CN")}
        </Text>
      ),
    },
    {
      title: "操作",
      key: "action",
      width: 140,
      render: (_: any, record: Verification) =>
        record.status === "pending" && (
          <Space size={4}>
            <AppButton
              variant="primary"
              size="sm"
              icon={<CheckCircleOutlined />}
              onClick={() => handleVerify(record.id, "verified", "验证通过")}
            >
              通过
            </AppButton>
            <AppButton
              size="sm"
              variant="danger"
              icon={<CloseCircleOutlined />}
              onClick={() => handleVerify(record.id, "rejected", "证据不足")}
            >
              拒绝
            </AppButton>
          </Space>
        ),
    },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 20 }}>
        <Col xs={24} sm={8}>
          <Card
            style={{
              borderRadius: 12,
              border: "none",
              boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
            }}
          >
            <Statistic
              title="待验证"
              value={pendingCount}
              prefix={<ClockCircleOutlined style={{ color: "#faad14" }} />}
              valueStyle={{ color: "#faad14" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card
            style={{
              borderRadius: 12,
              border: "none",
              boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
            }}
          >
            <Statistic
              title="总条目"
              value={verifications.length}
              prefix={<CheckCircleOutlined style={{ color: "#2e7d32" }} />}
              valueStyle={{ color: "#2e7d32" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card
            style={{
              borderRadius: 12,
              border: "none",
              boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
            onClick={() => setModalVisible(true)}
          >
            <div style={{ textAlign: "center" }}>
              <PlusOutlined
                style={{ fontSize: 28, color: "#2e7d32", marginBottom: 8, display: "block" }}
              />
              <Text strong style={{ color: "#2e7d32" }}>
                申请验证
              </Text>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 验证列表 */}
      <Card
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>
              验证管理
            </Title>
            {pendingCount > 0 && (
              <Tag color="gold" style={{ borderRadius: 10 }}>
                {pendingCount} 条待处理
              </Tag>
            )}
          </Space>
        }
        extra={
          <AppButton
            variant="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            申请验证
          </AppButton>
        }
        style={{
          borderRadius: 12,
          border: "none",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
        }}
      >
        <Table
          columns={columns}
          dataSource={verifications}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          style={{ marginTop: -8 }}
        />
      </Card>

      <ModalDialog
        title="验证申请"
        open={modalVisible}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setModalVisible(false);
            form.resetFields();
          }
        }}
      >
        <Form form={form} layout="vertical" onFinish={handleApply}>
          <Form.Item
            name="entity_type"
            label="实体类型"
            rules={[{ required: true }]}
            initialValue={prefilledEntityType}
          >
            <AppSelect aria-label="实体类型" options={entityTypeOptions} />
          </Form.Item>

          <Form.Item
            name="entity_id"
            label="实体ID"
            rules={[{ required: true }]}
            initialValue={prefilledEntityId}
          >
            <TextInput />
          </Form.Item>

          <Form.Item
            name="claimed_value"
            label="声明内容"
            rules={[{ required: true }]}
            initialValue={prefilledValue}
          >
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item name="source_id" label="来源">
            <TextInput placeholder="来源 ID（可选）" />
          </Form.Item>

          <Form.Item name="field_name" label="验证字段">
            <TextInput placeholder="具体字段名（可选）" />
          </Form.Item>

          <Form.Item>
            <div className="bc-dialog-actions">
              <AppButton variant="primary" type="submit">
                提交申请
              </AppButton>
              <AppButton
                onClick={() => {
                  setModalVisible(false);
                  form.resetFields();
                }}
              >
                取消
              </AppButton>
            </div>
          </Form.Item>
        </Form>
      </ModalDialog>
    </div>
  );
};

export default VerificationPage;
