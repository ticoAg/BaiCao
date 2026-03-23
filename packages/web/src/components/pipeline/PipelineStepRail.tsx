import { Tag, Typography } from "antd";
import type { PipelineRun, PipelineStepKey } from "../../types/pipeline";

const { Text } = Typography;

interface PipelineStepRailProps {
  steps: Array<{ key: PipelineStepKey; label: string }>;
  run: PipelineRun | null;
  recentRuns: PipelineRun[];
  currentStep: PipelineStepKey;
  onRestoreRun: (runId: string) => void;
}

const PipelineStepRail = ({ steps, run, recentRuns, currentStep, onRestoreRun }: PipelineStepRailProps) => {
  return (
    <aside data-testid="pipeline-step-rail" style={{ display: "grid", gap: 12 }}>
      {steps.map((step, index) => {
        const status = run?.steps[step.key]?.status ?? "pending";
        const isActive = currentStep === step.key;

        return (
          <div
            key={step.key}
            data-testid={`pipeline-step-${step.key}`}
            style={{
              border: isActive ? "1px solid #28553c" : "1px solid #d9e3db",
              borderRadius: 12,
              padding: 12,
              background: isActive ? "#f3fbf5" : "#fff",
            }}
          >
            <Text type="secondary" style={{ display: "block", marginBottom: 6 }}>
              步骤 {index + 1}
            </Text>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <Text strong>{step.label}</Text>
              <Tag color={isActive ? "green" : "default"}>{status}</Tag>
            </div>
          </div>
        );
      })}
      <div
        style={{
          border: "1px solid #d9e3db",
          borderRadius: 12,
          padding: 12,
          background: "#fff",
          display: "grid",
          gap: 8,
        }}
      >
        <Text strong>最近任务</Text>
        {recentRuns.length === 0 ? (
          <Text type="secondary">暂无可恢复任务</Text>
        ) : (
          recentRuns.map((recentRun) => (
            <button
              key={recentRun.id}
              type="button"
              onClick={() => onRestoreRun(recentRun.id)}
              style={{
                textAlign: "left",
                padding: "8px 10px",
                borderRadius: 10,
                border: "1px solid #d9e3db",
                background: "#f8fbf8",
                cursor: "pointer",
              }}
              aria-label={`恢复任务 ${recentRun.id}`}
            >
              <div style={{ fontWeight: 600 }}>{recentRun.id}</div>
              <div style={{ fontSize: 12, color: "#5f6f63" }}>{recentRun.sourceLocator}</div>
            </button>
          ))
        )}
      </div>
    </aside>
  );
};

export default PipelineStepRail;
