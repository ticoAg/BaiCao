import { Button, Card, Space, Typography } from "antd";

const { Paragraph, Text, Title } = Typography;

interface PipelineActionPanelProps {
  currentStepLabel: string;
  sourceType: string;
  sourceLocator: string;
  hasRun: boolean;
  hasPreview: boolean;
  isSubmitting: boolean;
  onPreview: () => void;
  onConfirm: () => void;
  onRerun: () => void;
  onRollback: () => void;
}

const PipelineActionPanel = ({
  currentStepLabel,
  sourceType,
  sourceLocator,
  hasRun,
  hasPreview,
  isSubmitting,
  onPreview,
  onConfirm,
  onRerun,
  onRollback,
}: PipelineActionPanelProps) => {
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
        <div>
          <Text type="secondary">{`来源类型：${sourceType}`}</Text>
          <br />
          <Text type="secondary">{`来源定位：${sourceLocator}`}</Text>
        </div>
        <Space wrap>
          <Button type="primary" loading={isSubmitting} onClick={onPreview}>
            运行预览
          </Button>
          <Button disabled={!hasPreview || isSubmitting} onClick={onConfirm}>
            确认进入下一步
          </Button>
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
