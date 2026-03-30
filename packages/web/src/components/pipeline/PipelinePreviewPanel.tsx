import { useEffect, useState } from "react";
import { Button, Card, Empty, Input, Select, Space, Typography, message } from "antd";
import type { ExportRecord, PipelinePreview, ReviewSession, UpdateReviewItemRequest } from "../../types/pipeline";

const { Paragraph, Text } = Typography;
const { TextArea } = Input;

interface ReviewItemEditorProps {
  item: ReviewSession["items"][number];
  onSave: (itemKey: string, payload: UpdateReviewItemRequest) => void;
}

const ReviewItemEditor = ({ item, onSave }: ReviewItemEditorProps) => {
  const [decision, setDecision] = useState(item.decision);
  const [comment, setComment] = useState(item.comment ?? "");
  const [payloadText, setPayloadText] = useState(JSON.stringify(item.revised_payload, null, 2));

  useEffect(() => {
    setDecision(item.decision);
    setComment(item.comment ?? "");
    setPayloadText(JSON.stringify(item.revised_payload, null, 2));
  }, [item.comment, item.decision, item.revised_payload]);

  return (
    <Card size="small" title={String(item.revised_payload.name ?? item.original_payload.name ?? item.item_key)}>
      <Space direction="vertical" size={10} style={{ width: "100%" }}>
        <Select
          value={decision}
          options={[
            { value: "pending", label: "待处理" },
            { value: "confirm", label: "确认" },
            { value: "edit", label: "编辑后确认" },
            { value: "reject", label: "驳回" },
          ]}
          onChange={setDecision}
        />
        <TextArea rows={6} value={payloadText} onChange={(event) => setPayloadText(event.target.value)} />
        <Input value={comment} placeholder="审阅备注" onChange={(event) => setComment(event.target.value)} />
        <Button
          onClick={() => {
            try {
              const revisedPayload = JSON.parse(payloadText) as Record<string, unknown>;
              onSave(item.item_key, {
                decision,
                revisedPayload,
                comment,
              });
            } catch (error) {
              message.error("修订 JSON 不是合法对象");
            }
          }}
        >
          保存修订
        </Button>
      </Space>
    </Card>
  );
};

interface PipelinePreviewPanelProps {
  preview: PipelinePreview | null;
  previewHistory: PipelinePreview[];
  reviewSession: ReviewSession | null;
  latestExport: ExportRecord | null;
  onSaveReviewItem: (itemKey: string, payload: UpdateReviewItemRequest) => void;
}

const PipelinePreviewPanel = ({
  preview,
  previewHistory,
  reviewSession,
  latestExport,
  onSaveReviewItem,
}: PipelinePreviewPanelProps) => {
  const repoUrl = preview?.previewPayload.repo_url;
  const readmeUrl = preview?.previewPayload.readme_url;
  const readmeContent = preview?.previewPayload.readme_content;

  return (
    <Card data-testid="pipeline-preview-panel" variant="borderless">
      {!preview ? (
        <Empty description="运行预览后，这里会展示当前步骤的结果摘要。" />
      ) : (
        <div style={{ display: "grid", gap: 12 }}>
          <Text strong>{preview.summary}</Text>
          <Text type="secondary">{`预览类型：${preview.previewKind}`}</Text>
          <Text type="secondary">{`预览版本：v${String(preview.previewPayload.preview_version ?? "-")}`}</Text>
          {reviewSession ? (
            <div style={{ display: "grid", gap: 10 }}>
              <Text strong>{`人工确认会话：${reviewSession.status}`}</Text>
              {reviewSession.items.map((item) => (
                <ReviewItemEditor key={item.item_key} item={item} onSave={onSaveReviewItem} />
              ))}
            </div>
          ) : null}
          {latestExport ? (
            <div style={{ display: "grid", gap: 6 }}>
              <Text strong>{`最近导出状态：${latestExport.status}`}</Text>
              <Text type="secondary">{`图谱写入：${latestExport.graph_write_status}`}</Text>
              <Text type="secondary">{`快照对象：${latestExport.snapshot_object_key ?? "-"}`}</Text>
              {latestExport.error_message ? <Text type="danger">{latestExport.error_message}</Text> : null}
            </div>
          ) : null}
          {repoUrl || readmeUrl ? (
            <div style={{ display: "grid", gap: 6 }}>
              <Text strong>来源链接</Text>
              {repoUrl ? (
                <a href={String(repoUrl)} target="_blank" rel="noreferrer">
                  打开仓库页
                </a>
              ) : null}
              {readmeUrl ? (
                <a href={String(readmeUrl)} target="_blank" rel="noreferrer">
                  打开 README 原文
                </a>
              ) : null}
            </div>
          ) : null}
          {typeof readmeContent === "string" && readmeContent.length > 0 ? (
            <Card size="small" title="README 预览" variant="borderless">
              <Paragraph style={{ marginBottom: 0, whiteSpace: "pre-wrap" }}>{readmeContent}</Paragraph>
            </Card>
          ) : null}
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
