import PipelineActionPanel from "./PipelineActionPanel";
import PipelinePreviewPanel from "./PipelinePreviewPanel";
import PipelineStepRail from "./PipelineStepRail";
import { usePipelineRun } from "../../hooks/usePipelineRun";
import { usePipelineStore } from "../../stores/pipelineStore";

const PipelineShell = () => {
  const { sourceType, sourceLocator } = usePipelineStore();
  const {
    fixedSteps,
    run,
    preview,
    isSubmitting,
    currentStep,
    currentStepLabel,
    runPreview,
    confirmCurrentStep,
  } = usePipelineRun();

  return (
    <div
      data-testid="pipeline-shell"
      style={{
        minHeight: "calc(100vh - 96px)",
        display: "grid",
        gridTemplateColumns: "280px minmax(320px, 1fr) minmax(320px, 1fr)",
        gap: 16,
        alignItems: "start",
      }}
    >
      <PipelineStepRail steps={fixedSteps} run={run} currentStep={currentStep} />
      <PipelineActionPanel
        currentStepLabel={currentStepLabel}
        sourceType={run?.sourceType ?? sourceType}
        sourceLocator={run?.sourceLocator ?? sourceLocator}
        hasPreview={Boolean(preview)}
        isSubmitting={isSubmitting}
        onPreview={() => {
          void runPreview();
        }}
        onConfirm={() => {
          void confirmCurrentStep();
        }}
      />
      <PipelinePreviewPanel preview={preview} />
    </div>
  );
};

export default PipelineShell;
