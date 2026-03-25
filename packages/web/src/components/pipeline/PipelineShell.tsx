import PipelineActionPanel from "./PipelineActionPanel";
import PipelinePreviewPanel from "./PipelinePreviewPanel";
import PipelineStepRail from "./PipelineStepRail";
import { usePipelineRun } from "../../hooks/usePipelineRun";
import { usePipelineStore } from "../../stores/pipelineStore";
import { useEffect } from "react";

const PipelineShell = () => {
  const { sourceType, sourceLocator } = usePipelineStore();
  const {
    fixedSteps,
    run,
    recentRuns,
    preview,
    previewHistory,
    reviewSession,
    latestExport,
    isSubmitting,
    currentStep,
    currentStepLabel,
    runPreview,
    confirmCurrentStep,
    restoreRun,
    loadRecentRuns,
    rerunCurrentStep,
    rollbackCurrentStep,
    saveReviewItem,
    lockReviewSession,
    executeExport,
  } = usePipelineRun();

  useEffect(() => {
    void loadRecentRuns();
  }, [loadRecentRuns]);

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
      <PipelineStepRail
        steps={fixedSteps}
        run={run}
        recentRuns={recentRuns}
        currentStep={currentStep}
        onRestoreRun={(runId) => {
          void restoreRun(runId);
        }}
      />
      <PipelineActionPanel
        currentStep={currentStep}
        currentStepLabel={currentStepLabel}
        sourceType={run?.sourceType ?? sourceType}
        sourceLocator={run?.sourceLocator ?? sourceLocator}
        hasRun={Boolean(run)}
        hasPreview={Boolean(preview)}
        isSubmitting={isSubmitting}
        reviewSession={reviewSession}
        latestExport={latestExport}
        onPreview={() => {
          void runPreview();
        }}
        onConfirm={() => {
          void confirmCurrentStep();
        }}
        onRerun={() => {
          void rerunCurrentStep();
        }}
        onRollback={() => {
          void rollbackCurrentStep();
        }}
        onLockReview={() => {
          void lockReviewSession();
        }}
        onExecuteExport={() => {
          void executeExport();
        }}
      />
      <PipelinePreviewPanel
        preview={preview}
        previewHistory={previewHistory}
        reviewSession={reviewSession}
        latestExport={latestExport}
        onSaveReviewItem={(itemKey, payload) => {
          void saveReviewItem(itemKey, payload);
        }}
      />
    </div>
  );
};

export default PipelineShell;
