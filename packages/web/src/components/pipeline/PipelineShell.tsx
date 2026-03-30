import PipelineActionPanel from "./PipelineActionPanel";
import PipelinePreviewPanel from "./PipelinePreviewPanel";
import PipelineStepRail from "./PipelineStepRail";
import { usePipelineRun } from "../../hooks/usePipelineRun";
import { usePipelineStore } from "../../stores/pipelineStore";
import { useEffect } from "react";

const PipelineShell = () => {
  const { sourceType, sourceLocator, uploadedSource, setSourceType, setSourceLocator, setUploadedSource } = usePipelineStore();
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
    uploadSourceFile,
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
        formSourceType={sourceType}
        formSourceLocator={sourceLocator}
        displaySourceType={run?.sourceType ?? sourceType}
        displaySourceLocator={run?.sourceLocator ?? sourceLocator}
        uploadedSource={uploadedSource}
        hasRun={Boolean(run)}
        hasPreview={Boolean(preview)}
        isSubmitting={isSubmitting}
        reviewSession={reviewSession}
        latestExport={latestExport}
        onSourceTypeChange={(value) => {
          setSourceType(value);
          setUploadedSource(null);
        }}
        onSourceLocatorChange={setSourceLocator}
        onUploadFile={(file) => {
          void uploadSourceFile(file);
        }}
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
