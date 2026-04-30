import { useCallback, useMemo } from "react";
import { message } from "../components/ui/index";
import { pipelineApi } from "../services/pipelineApi";
import { usePipelineStore } from "../stores/pipelineStore";
import type { CreatePipelineRunRequest, PipelineSourceType, PipelineStepKey, UpdateReviewItemRequest } from "../types/pipeline";

const FIXED_STEPS: Array<{ key: PipelineStepKey; label: string }> = [
  { key: "source_ingest", label: "接入来源" },
  { key: "source_preview", label: "原始内容预览" },
  { key: "normalize", label: "规范化清洗" },
  { key: "extract", label: "结构抽取" },
  { key: "map_to_knowledge_model", label: "映射到共享图模型" },
  { key: "human_review", label: "人工确认与修订" },
  { key: "export", label: "导出 / 入库" },
];

export const usePipelineRun = () => {
  const {
    sourceType,
    sourceLocator,
    uploadedSource,
    run,
    recentRuns,
    preview,
    previewHistory,
    reviewSession,
    latestExport,
    isSubmitting,
    setRun,
    setSourceLocator,
    setRecentRuns,
    setPreview,
    setPreviewHistory,
    setReviewSession,
    setLatestExport,
    setSubmitting,
    setUploadedSource,
  } = usePipelineStore();

  const currentStep = run?.currentStep ?? FIXED_STEPS[0].key;

  const currentStepLabel = useMemo(
    () => FIXED_STEPS.find((step) => step.key === currentStep)?.label ?? "接入来源",
    [currentStep],
  );

  const loadStepSidecars = useCallback(
    async (runId: string, step: PipelineStepKey) => {
      if (step === "human_review") {
        try {
          setReviewSession(await pipelineApi.getReviewSession(runId));
        } catch (error) {
          setReviewSession(null);
        }
        setLatestExport(null);
        return;
      }

      if (step === "export") {
        try {
          setReviewSession(await pipelineApi.getReviewSession(runId));
        } catch (error) {
          setReviewSession(null);
        }
        try {
          setLatestExport(await pipelineApi.getLatestExportExecution(runId));
        } catch (error) {
          setLatestExport(null);
        }
        return;
      }

      setReviewSession(null);
      setLatestExport(null);
    },
    [setLatestExport, setReviewSession],
  );

  const buildCreateRunPayload = useCallback((): CreatePipelineRunRequest => {
    const currentSourceType = sourceType as PipelineSourceType;
    if (currentSourceType === "huggingface_repo") {
      return {
        sourceType: currentSourceType,
        sourceLocator,
        sourcePayload: {
          source_type: currentSourceType,
          source_input: { repo_id: sourceLocator },
        },
      };
    }

    if (currentSourceType === "remote_url") {
      return {
        sourceType: currentSourceType,
        sourceLocator,
        sourcePayload: {
          source_type: currentSourceType,
          source_input: { url: sourceLocator },
        },
      };
    }

    if (!uploadedSource) {
      throw new Error("请先上传本地文件");
    }

    return {
      sourceType: currentSourceType,
      sourceLocator: uploadedSource.upload_token,
      sourcePayload: {
        source_type: currentSourceType,
        source_input: {
          upload_token: uploadedSource.upload_token,
          stored_path: uploadedSource.stored_path,
        },
      },
    };
  }, [sourceLocator, sourceType, uploadedSource]);

  const runPreview = useCallback(async () => {
    setSubmitting(true);
    try {
      const activeRun =
        run ??
        (await pipelineApi.createRun(buildCreateRunPayload()));
      if (!run) {
        setRun(activeRun);
      }

      const nextPreview = await pipelineApi.previewStep(activeRun.id, activeRun.currentStep);
      setPreview(nextPreview);
      const history = await pipelineApi.listPreviewArtifacts(activeRun.id, activeRun.currentStep);
      setPreviewHistory(history);
      await loadStepSidecars(activeRun.id, activeRun.currentStep);
    } catch (error) {
      message.error("运行预览失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [buildCreateRunPayload, loadStepSidecars, run, setPreview, setPreviewHistory, setRun, setSubmitting]);

  const uploadSourceFile = useCallback(
    async (file: File) => {
      setSubmitting(true);
      try {
        const uploaded = await pipelineApi.uploadSourceFile(file);
        setUploadedSource(uploaded);
        setSourceLocator(uploaded.upload_token);
        message.success(`已上传 ${uploaded.filename}`);
      } catch (error) {
        message.error("上传来源文件失败，请稍后重试");
      } finally {
        setSubmitting(false);
      }
    },
    [setSourceLocator, setSubmitting, setUploadedSource],
  );

  const confirmCurrentStep = useCallback(async () => {
    if (!run) {
      return;
    }

    setSubmitting(true);
    try {
      const updatedRun = await pipelineApi.confirmStep(run.id, run.currentStep);
      setRun(updatedRun);
      setPreview(null);
      setPreviewHistory([]);
      await loadStepSidecars(updatedRun.id, updatedRun.currentStep);
    } catch (error) {
      message.error("确认步骤失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [loadStepSidecars, run, setPreview, setPreviewHistory, setRun, setSubmitting]);

  const restoreRun = useCallback(
    async (runId: string) => {
      setSubmitting(true);
      try {
        const restored = await pipelineApi.getRun(runId);
        setRun(restored);
        try {
          const latestPreview = await pipelineApi.getLatestPreview(runId, restored.currentStep);
          setPreview(latestPreview);
          const history = await pipelineApi.listPreviewArtifacts(runId, restored.currentStep);
          setPreviewHistory(history);
        } catch (error) {
          setPreview(null);
          setPreviewHistory([]);
        }
        await loadStepSidecars(runId, restored.currentStep);
      } catch (error) {
        message.error("加载处理任务失败，请稍后重试");
      } finally {
        setSubmitting(false);
      }
    },
    [loadStepSidecars, setPreview, setPreviewHistory, setRun, setSubmitting],
  );

  const loadRecentRuns = useCallback(async () => {
    try {
      const runs = await pipelineApi.listRuns();
      setRecentRuns(runs);
    } catch (error) {
      message.error("加载最近任务失败，请稍后重试");
    }
  }, [setRecentRuns]);

  const rerunCurrentStep = useCallback(async () => {
    if (!run) {
      return;
    }
    setSubmitting(true);
    try {
      const nextPreview = await pipelineApi.rerunStep(run.id, run.currentStep);
      setPreview(nextPreview);
      const history = await pipelineApi.listPreviewArtifacts(run.id, run.currentStep);
      setPreviewHistory(history);
      await loadStepSidecars(run.id, run.currentStep);
    } catch (error) {
      message.error("重跑当前步骤失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [loadStepSidecars, run, setPreview, setPreviewHistory, setSubmitting]);

  const rollbackCurrentStep = useCallback(async () => {
    if (!run) {
      return;
    }
    const currentIndex = FIXED_STEPS.findIndex((step) => step.key === run.currentStep);
    const targetStep = currentIndex > 0 ? FIXED_STEPS[currentIndex - 1].key : FIXED_STEPS[0].key;

    setSubmitting(true);
    try {
      const updatedRun = await pipelineApi.rollbackStep(run.id, targetStep);
      setRun(updatedRun);
      setPreview(null);
      setPreviewHistory([]);
      await loadStepSidecars(updatedRun.id, updatedRun.currentStep);
    } catch (error) {
      message.error("回退步骤失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [loadStepSidecars, run, setPreview, setPreviewHistory, setRun, setSubmitting]);

  const saveReviewItem = useCallback(
    async (itemKey: string, payload: UpdateReviewItemRequest) => {
      if (!run) {
        return;
      }
      setSubmitting(true);
      try {
        const session = await pipelineApi.updateReviewItem(run.id, itemKey, payload);
        setReviewSession(session);
        const refreshedPreview = await pipelineApi.previewStep(run.id, "human_review");
        setPreview(refreshedPreview);
      } catch (error) {
        message.error("保存人工修订失败，请稍后重试");
      } finally {
        setSubmitting(false);
      }
    },
    [run, setPreview, setReviewSession, setSubmitting],
  );

  const lockReviewSession = useCallback(async () => {
    if (!run) {
      return;
    }
    setSubmitting(true);
    try {
      const session = await pipelineApi.confirmReviewSession(run.id);
      setReviewSession(session);
      const refreshedPreview = await pipelineApi.previewStep(run.id, "human_review");
      setPreview(refreshedPreview);
    } catch (error) {
      message.error("锁定人工确认会话失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [run, setPreview, setReviewSession, setSubmitting]);

  const executeExport = useCallback(async () => {
    if (!run) {
      return;
    }
    setSubmitting(true);
    try {
      const record = await pipelineApi.executeExport(run.id);
      setLatestExport(record);
      const refreshedPreview = await pipelineApi.buildExportPlan(run.id);
      setPreview(refreshedPreview);
    } catch (error) {
      message.error("执行导出失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [run, setLatestExport, setPreview, setSubmitting]);

  return {
    fixedSteps: FIXED_STEPS,
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
  };
};
