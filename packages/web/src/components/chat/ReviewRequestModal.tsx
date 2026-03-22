// 审查申请弹窗组件
import { useEffect } from "react";
import { Modal, Form, Select, Input, Button, Space, message } from "antd";
import { verificationApi } from "../../services/api";

interface ReviewRequestModalProps {
  open: boolean;
  onClose: () => void;
  prefill?: {
    entityType?: string;
    entityId?: string;
    content?: string;
    sourceId?: string;
  };
}

const ReviewRequestModal = ({ open, onClose, prefill }: ReviewRequestModalProps) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (open && prefill) {
      form.setFieldsValue({
        entity_type: prefill.entityType,
        entity_id: prefill.entityId,
        claimed_value: prefill.content,
        source_id: prefill.sourceId,
      });
    }
    if (!open) {
      form.resetFields();
    }
  }, [open, prefill, form]);

  const handleFinish = async (values: {
    entity_type: string;
    entity_id: string;
    claimed_value: string;
    source_id?: string;
  }) => {
    try {
      await verificationApi.create({
        entity_type: values.entity_type,
        entity_id: values.entity_id,
        claimed_value: values.claimed_value,
        applicant_id: "anonymous",
        source_id: values.source_id || undefined,
      });
      message.success("审查申请已提交");
      onClose();
    } catch {
      message.error("提交失败，请稍后重试");
    }
  };

  return (
    <Modal
      title="申请审查"
      open={open}
      onCancel={onClose}
      footer={null}
      styles={{ body: { paddingTop: 16 } }}
    >
      <Form form={form} layout="vertical" onFinish={handleFinish}>
        <Form.Item
          name="entity_type"
          label="实体类型"
          rules={[{ required: true, message: "请选择实体类型" }]}
        >
          <Select placeholder="请选择实体类型">
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
          rules={[{ required: true, message: "请填写实体ID" }]}
        >
          <Input placeholder="实体ID" />
        </Form.Item>

        <Form.Item
          name="claimed_value"
          label="审查内容"
          rules={[{ required: true, message: "请填写审查内容" }]}
        >
          <Input.TextArea rows={4} placeholder="待审查的内容" />
        </Form.Item>

        <Form.Item name="source_id" label="来源ID">
          <Input placeholder="来源ID（可选）" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" style={{ borderRadius: 8 }}>
              提交申请
            </Button>
            <Button onClick={onClose} style={{ borderRadius: 8 }}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ReviewRequestModal;
