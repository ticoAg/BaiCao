import type { ExportRecord, ReviewItemDecision, ReviewSession } from "@bai-cao/shared";

export type PipelineRunStatus =
  | "pending"
  | "running"
  | "pending_review"
  | "completed"
  | "failed"
  | "archived";

export type PipelineStepStatus =
  | "pending"
  | "running"
  | "preview_ready"
  | "pending_confirmation"
  | "confirmed"
  | "skipped"
  | "failed";

export type PipelineStepKey =
  | "source_ingest"
  | "source_preview"
  | "normalize"
  | "extract"
  | "map_to_knowledge_model"
  | "human_review"
  | "export";

export interface PipelineStepState {
  key: PipelineStepKey;
  status: PipelineStepStatus;
  summary: string | null;
  previewVersion: number;
}

export interface PipelineRun {
  id: string;
  sourceType: string;
  sourceLocator: string;
  status: PipelineRunStatus;
  currentStep: PipelineStepKey;
  steps: Partial<Record<PipelineStepKey, PipelineStepState>>;
}

export interface PipelineArtifactReference {
  key: string;
  label: string;
  uri?: string | null;
}

export interface PipelinePreview {
  runId: string;
  step: PipelineStepKey;
  status: PipelineStepStatus;
  summary: string;
  previewKind: string;
  previewPayload: Record<string, unknown>;
  warnings: string[];
  errors: string[];
  artifacts: PipelineArtifactReference[];
  nextStepReady: boolean;
}

export interface CreatePipelineRunRequest {
  sourceType: string;
  sourceLocator: string;
}

export interface UpdateReviewItemRequest {
  decision?: ReviewItemDecision;
  revisedPayload?: Record<string, unknown>;
  comment?: string | null;
}

export type { ExportRecord, ReviewSession };
