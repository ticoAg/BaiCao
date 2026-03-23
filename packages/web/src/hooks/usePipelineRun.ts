import { useCallback, useMemo } from "react";
import { message } from "antd";
import { pipelineApi } from "../services/pipelineApi";
import { usePipelineStore } from "../stores/pipelineStore";
import type { PipelineStepKey } from "../types/pipeline";

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
    run,
    preview,
    isSubmitting,
    setRun,
    setPreview,
    setSubmitting,
  } = usePipelineStore();

  const currentStep = run?.currentStep ?? FIXED_STEPS[0].key;

  const currentStepLabel = useMemo(
    () => FIXED_STEPS.find((step) => step.key === currentStep)?.label ?? "接入来源",
    [currentStep],
  );

  const runPreview = useCallback(async () => {
    setSubmitting(true);
    try {
      const activeRun =
        run ??
        (await pipelineApi.createRun({
          sourceType,
          sourceLocator,
        }));
      if (!run) {
        setRun(activeRun);
      }

      const nextPreview = await pipelineApi.previewStep(activeRun.id, activeRun.currentStep);
      setPreview(nextPreview);
    } catch (error) {
      message.error("运行预览失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [run, setPreview, setRun, setSubmitting, sourceLocator, sourceType]);

  const confirmCurrentStep = useCallback(async () => {
    if (!run) {
      return;
    }

    setSubmitting(true);
    try {
      const updatedRun = await pipelineApi.confirmStep(run.id, run.currentStep);
      setRun(updatedRun);
      setPreview(null);
    } catch (error) {
      message.error("确认步骤失败，请稍后重试");
    } finally {
      setSubmitting(false);
    }
  }, [run, setPreview, setRun, setSubmitting]);

  const restoreRun = useCallback(
    async (runId: string) => {
      setSubmitting(true);
      try {
        const restored = await pipelineApi.getRun(runId);
        setRun(restored);
        setPreview(null);
      } catch (error) {
        message.error("加载处理任务失败，请稍后重试");
      } finally {
        setSubmitting(false);
      }
    },
    [setPreview, setRun, setSubmitting],
  );

  return {
    fixedSteps: FIXED_STEPS,
    run,
    preview,
    isSubmitting,
    currentStep,
    currentStepLabel,
    runPreview,
    confirmCurrentStep,
    restoreRun,
  };
};
