import { useState, useEffect } from "react";
import {
  Card,
  Typography,
  Table,
  Tag,
  Space,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
} from "antd";
import { useSearchParams } from "react-router-dom";
import { verificationApi, Verification } from "../services/api";

const { Title } = Typography;

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

const VerificationPage = () => {
  const [searchParams] = useSearchParams();
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 预填参数
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

  // 如果有预填参数，自动打开申请模态框
  useEffect(() => {
    if (prefilledEntityType && prefilledEntityId && prefilledValue) {
      setModalVisible(true);
    }
  }, [prefilledEntityType, prefilledEntityId, prefilledValue]);

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

  const columns = [
    {
      title: "实体类型",
      dataIndex: "entity_type",
      key: "entity_type",
      render: (type: string) => <Tag>{entityTypeLabels[type] || type}</Tag>,
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
      render: (status: string) => (
        <Tag color={statusColors[status]}>{statusLabels[status] || status}</Tag>
      ),
    },
    {
      title: "申请时间",
      dataIndex: "created_at",
      key: "created_at",
      render: (date: string) => new Date(date).toLocaleString("zh-CN"),
    },
    {
      title: "操作",
      key: "action",
      render: (_: any, record: Verification) =>
        record.status === "pending" && (
          <Space>
            <Button
              type="link"
              size="small"
              onClick={() => handleVerify(record.id, "verified", "验证通过")}
            >
              通过
            </Button>
            <Button
              type="link"
              size="small"
              danger
              onClick={() => handleVerify(record.id, "rejected", "证据不足")}
            >
              拒绝
            </Button>
          </Space>
        ),
    },
  ];

  return (
    <div>
      <Card
        title={<Title level={3}>验证管理</Title>}
        extra={
          <Button type="primary" onClick={() => setModalVisible(true)}>
            申请验证
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={verifications}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="验证申请"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleApply}>
          <Form.Item
            name="entity_type"
            label="实体类型"
            rules={[{ required: true }]}
            initialValue={prefilledEntityType}
          >
            <Select>
              <Select.Option value="herb">药材</Select.Option>
              <Select.Option value="efficacy">功效</Select.Option>
              <Select.Option value="relation">关系</Select.Option>
              <Select.Option value="flavor">性味</Select.Option>
              <Select.Option value="meridian">归经</Select.Option>
              <Select.Option value="component">成分</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="entity_id"
            label="实体ID"
            rules={[{ required: true }]}
            initialValue={prefilledEntityId}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="claimed_value"
            label="声明内容"
            rules={[{ required: true }]}
            initialValue={prefilledValue}
          >
            <Input.TextArea rows={3} />
          </Form.Item>

          <Form.Item name="source_id" label="来源">
            <Input placeholder="来源 ID（可选）" />
          </Form.Item>

          <Form.Item name="field_name" label="验证字段">
            <Input placeholder="具体字段名（可选）" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                提交申请
              </Button>
              <Button onClick={() => setModalVisible(false)}>取消</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default VerificationPage;
