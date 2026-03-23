import { Card, Empty, Typography } from "antd";
import type { PipelinePreview } from "../../types/pipeline";

const { Paragraph, Text } = Typography;

interface PipelinePreviewPanelProps {
  preview: PipelinePreview | null;
  previewHistory: PipelinePreview[];
}

const PipelinePreviewPanel = ({ preview, previewHistory }: PipelinePreviewPanelProps) => {
  return (
    <Card data-testid="pipeline-preview-panel" bordered={false}>
      {!preview ? (
        <Empty description="运行预览后，这里会展示当前步骤的结果摘要。" />
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          <Text strong>{preview.summary}</Text>
          <Text type="secondary">{`预览类型：${preview.previewKind}`}</Text>
          <Text type="secondary">{`预览版本：v${String(preview.previewPayload.preview_version ?? "-")}`}</Text>
          <Paragraph style={{ marginBottom: 0, whiteSpace: "pre-wrap" }}>
            {JSON.stringify(preview.previewPayload, null, 2)}
          </Paragraph>
          {previewHistory.length > 0 ? (
            <div style={{ display: "grid", gap: 8 }}>
              <Text strong>历史快照</Text>
              {previewHistory.map((item, index) => {
                const firstArtifact = item.artifacts[0];
                return (
                  <Text key={`${item.step}-${index}`} type="secondary">
                    {firstArtifact?.label ?? `${item.step} v${String(item.previewPayload.preview_version ?? "-")}`}
                  </Text>
                );
              })}
            </div>
          ) : null}
        </div>
      )}
    </Card>
  );
};

export default PipelinePreviewPanel;
