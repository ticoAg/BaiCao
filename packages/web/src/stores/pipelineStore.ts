import { create } from "zustand";
import type { PipelinePreview, PipelineRun } from "../types/pipeline";

interface PipelineState {
  sourceType: string;
  sourceLocator: string;
  run: PipelineRun | null;
  preview: PipelinePreview | null;
  isSubmitting: boolean;
  setSourceType: (value: string) => void;
  setSourceLocator: (value: string) => void;
  setRun: (run: PipelineRun | null) => void;
  setPreview: (preview: PipelinePreview | null) => void;
  setSubmitting: (value: boolean) => void;
}

export const usePipelineStore = create<PipelineState>((set) => ({
  sourceType: "huggingface",
  sourceLocator: "ZJUFanLab/TCMChat-dataset-600k",
  run: null,
  preview: null,
  isSubmitting: false,
  setSourceType: (value) => set({ sourceType: value }),
  setSourceLocator: (value) => set({ sourceLocator: value }),
  setRun: (run) => set({ run }),
  setPreview: (preview) => set({ preview }),
  setSubmitting: (value) => set({ isSubmitting: value }),
}));
