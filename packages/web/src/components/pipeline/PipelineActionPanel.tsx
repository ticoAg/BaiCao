import type { ExportRecord, PipelineStepKey, ReviewSession } from "../../types/pipeline";
import { Button, Card, Space, Typography } from "antd";
import SourceIngestionForm from "./SourceIngestionForm";
import type { PipelineSourceType, PipelineUploadResponse } from "../../types/pipeline";

const { Paragraph, Text, Title } = Typography;

interface PipelineActionPanelProps {
  currentStep: PipelineStepKey;
  currentStepLabel: string;
  formSourceType: PipelineSourceType;
  formSourceLocator: string;
  displaySourceType: string;
  displaySourceLocator: string;
  uploadedSource: PipelineUploadResponse | null;
  hasRun: boolean;
  hasPreview: boolean;
  isSubmitting: boolean;
  reviewSession: ReviewSession | null;
  latestExport: ExportRecord | null;
  onSourceTypeChange: (value: PipelineSourceType) => void;
  onSourceLocatorChange: (value: string) => void;
  onUploadFile: (file: File) => void;
  onPreview: () => void;
  onConfirm: () => void;
  onRerun: () => void;
  onRollback: () => void;
  onLockReview: () => void;
  onExecuteExport: () => void;
}

const PipelineActionPanel = ({
  currentStep,
  currentStepLabel,
  formSourceType,
  formSourceLocator,
  displaySourceType,
  displaySourceLocator,
  uploadedSource,
  hasRun,
  hasPreview,
  isSubmitting,
  reviewSession,
  latestExport,
  onSourceTypeChange,
  onSourceLocatorChange,
  onUploadFile,
  onPreview,
  onConfirm,
  onRerun,
  onRollback,
  onLockReview,
  onExecuteExport,
}: PipelineActionPanelProps) => {
  const confirmLabel = currentStep === "export" ? "确认允许执行" : "确认进入下一步";
  const previewLabel = currentStep === "export" ? "生成导出计划" : "运行预览";

  return (
    <Card data-testid="pipeline-action-panel" bordered={false}>
      <Space direction="vertical" size={14} style={{ width: "100%" }}>
        <div>
          <Title level={4} style={{ marginBottom: 8 }}>
            数据处理工作台
          </Title>
          <Text strong>{`当前步骤：${currentStepLabel}`}</Text>
        </div>
        <Paragraph style={{ marginBottom: 0 }}>
          当前以固定步骤模板执行处理任务。来源适配可以变化，但步骤顺序保持一致，并在关键步骤间等待人工放行。
        </Paragraph>
        <SourceIngestionForm
          sourceType={formSourceType}
          sourceLocator={formSourceLocator}
          uploadedSource={uploadedSource}
          disabled={isSubmitting}
          onSourceTypeChange={onSourceTypeChange}
          onSourceLocatorChange={onSourceLocatorChange}
          onUploadFile={onUploadFile}
        />
        <div>
          <Text type="secondary">{`来源类型：${displaySourceType}`}</Text>
          <br />
          <Text type="secondary">{`来源定位：${displaySourceLocator}`}</Text>
        </div>
        <Space wrap>
          <Button type="primary" loading={isSubmitting} onClick={onPreview}>
            {previewLabel}
          </Button>
          <Button disabled={!hasPreview || isSubmitting} onClick={onConfirm}>
            {confirmLabel}
          </Button>
          {currentStep === "human_review" ? (
            <Button disabled={!reviewSession || isSubmitting} onClick={onLockReview}>
              {reviewSession?.status === "confirmed" ? "人工审阅已锁定" : "锁定人工审阅"}
            </Button>
          ) : null}
          {currentStep === "export" ? (
            <Button disabled={!hasRun || isSubmitting} onClick={onExecuteExport}>
              {latestExport ? "重新执行导出" : "执行导出"}
            </Button>
          ) : null}
          <Button disabled={!hasRun || isSubmitting} onClick={onRerun}>
            重新运行当前步骤
          </Button>
          <Button disabled={!hasRun || isSubmitting} onClick={onRollback}>
            回退到上一步
          </Button>
        </Space>
      </Space>
    </Card>
  );
};

export default PipelineActionPanel;
