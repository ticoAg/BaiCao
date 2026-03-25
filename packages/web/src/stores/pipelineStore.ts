import { create } from "zustand";
import type { ExportRecord, PipelinePreview, PipelineRun, ReviewSession } from "../types/pipeline";

interface PipelineState {
  sourceType: string;
  sourceLocator: string;
  run: PipelineRun | null;
  recentRuns: PipelineRun[];
  preview: PipelinePreview | null;
  previewHistory: PipelinePreview[];
  reviewSession: ReviewSession | null;
  latestExport: ExportRecord | null;
  isSubmitting: boolean;
  setSourceType: (value: string) => void;
  setSourceLocator: (value: string) => void;
  setRun: (run: PipelineRun | null) => void;
  setRecentRuns: (runs: PipelineRun[]) => void;
  setPreview: (preview: PipelinePreview | null) => void;
  setPreviewHistory: (previews: PipelinePreview[]) => void;
  setReviewSession: (reviewSession: ReviewSession | null) => void;
  setLatestExport: (latestExport: ExportRecord | null) => void;
  setSubmitting: (value: boolean) => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  sourceType: "huggingface",
  sourceLocator: "ZJUFanLab/TCMChat-dataset-600k",
  run: null,
  recentRuns: [],
  preview: null,
  previewHistory: [],
  reviewSession: null,
  latestExport: null,
  isSubmitting: false,
  setSourceType: (value) => set({ sourceType: value }),
  setSourceLocator: (value) => set({ sourceLocator: value }),
  setRun: (run) => set({ run }),
  setRecentRuns: (runs) => set({ recentRuns: runs }),
  setPreview: (preview) => set({ preview }),
  setPreviewHistory: (previews) => set({ previewHistory: previews }),
  setReviewSession: (reviewSession) => set({ reviewSession }),
  setLatestExport: (latestExport) => set({ latestExport }),
  setSubmitting: (value) => set({ isSubmitting: value }),
}));
