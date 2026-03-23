import { Tag, Typography } from "antd";
import type { PipelineRun, PipelineStepKey } from "../../types/pipeline";

const { Text } = Typography;

interface PipelineStepRailProps {
  steps: Array<{ key: PipelineStepKey; label: string }>;
  run: PipelineRun | null;
  currentStep: PipelineStepKey;
}

const PipelineStepRail = ({ steps, run, currentStep }: PipelineStepRailProps) => {
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
    </aside>
  );
};

export default PipelineStepRail;
