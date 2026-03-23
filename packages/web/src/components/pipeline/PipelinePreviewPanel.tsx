import { Card, Empty, Typography } from "antd";
import type { PipelinePreview } from "../../types/pipeline";

const { Paragraph, Text } = Typography;

interface PipelinePreviewPanelProps {
  preview: PipelinePreview | null;
}

const PipelinePreviewPanel = ({ preview }: PipelinePreviewPanelProps) => {
  return (
    <Card data-testid="pipeline-preview-panel" bordered={false}>
      {!preview ? (
        <Empty description="运行预览后，这里会展示当前步骤的结果摘要。" />
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          <Text strong>{preview.summary}</Text>
          <Text type="secondary">{`预览类型：${preview.previewKind}`}</Text>
          <Paragraph style={{ marginBottom: 0, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(preview.previewPayload, null, 2)}
          </Paragraph>
        </div>
      )}
    </Card>
  );
};

export default PipelinePreviewPanel;
