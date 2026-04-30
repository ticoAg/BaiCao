// 审查申请弹窗组件
import { useEffect } from "react";
import { Form, message } from "../ui/index";
import { verificationApi } from "../../services/api";
import ModalDialog from "../ui/Dialog";
import AppButton from "../ui/Button";
import AppSelect from "../ui/Select";
import { TextArea, TextInput } from "../ui/Field";

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

const entityTypeOptions = [
  { value: "herb", label: "药材" },
  { value: "efficacy", label: "功效" },
  { value: "relation", label: "关系" },
  { value: "flavor", label: "性味" },
  { value: "meridian", label: "归经" },
  { value: "component", label: "成分" },
];

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
    <ModalDialog
      title="申请审查"
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onClose();
      }}
    >
      <Form form={form} layout="vertical" onFinish={handleFinish}>
        <Form.Item
          name="entity_type"
          label="实体类型"
          rules={[{ required: true, message: "请选择实体类型" }]}
        >
          <AppSelect
            aria-label="实体类型"
            placeholder="请选择实体类型"
            options={entityTypeOptions}
          />
        </Form.Item>

        <Form.Item
          name="entity_id"
          label="实体ID"
          rules={[{ required: true, message: "请填写实体ID" }]}
        >
          <TextInput placeholder="实体ID" />
        </Form.Item>

        <Form.Item
          name="claimed_value"
          label="审查内容"
          rules={[{ required: true, message: "请填写审查内容" }]}
        >
          <TextArea rows={4} placeholder="待审查的内容" />
        </Form.Item>

        <Form.Item name="source_id" label="来源ID">
          <TextInput placeholder="来源ID（可选）" />
        </Form.Item>

        <Form.Item>
          <div className="bc-dialog-actions">
            <AppButton variant="primary" type="submit">
              提交申请
            </AppButton>
            <AppButton onClick={onClose}>
              取消
            </AppButton>
          </div>
        </Form.Item>
      </Form>
    </ModalDialog>
  );
};

export default ReviewRequestModal;
