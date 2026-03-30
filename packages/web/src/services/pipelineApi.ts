import axios from "axios";
import type {
  CreatePipelineRunRequest,
  ExportRecord,
  PipelinePreview,
  PipelineRun,
  PipelineUploadResponse,
  PipelineStepKey,
  PipelineStepState,
  ReviewSession,
  UpdateReviewItemRequest,
} from "../types/pipeline";

const API_BASE = "/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

const mapSteps = (steps: Record<string, {
  key: string;
  status: string;
  summary: string | null;
  preview_version: number;
}>): Partial<Record<PipelineStepKey, PipelineStepState>> => {
  return Object.fromEntries(
    Object.entries(steps).map(([key, value]) => [
      key,
      {
        key: value.key as PipelineStepKey,
        status: value.status as PipelineStepState["status"],
        summary: value.summary,
        previewVersion: value.preview_version,
      },
    ]),
  ) as Partial<Record<PipelineStepKey, PipelineStepState>>;
};

const mapPreview = (data: Record<string, any>): PipelinePreview => ({
  runId: data.run_id,
  step: data.step,
  status: data.status,
  summary: data.summary,
  previewKind: data.preview_kind,
  previewPayload: data.preview_payload,
  warnings: data.warnings,
  errors: data.errors,
  artifacts: data.artifacts,
  nextStepReady: data.next_step_ready,
});

const mapReviewSession = (data: Record<string, any>): ReviewSession => ({
  id: data.id,
  run_id: data.run_id,
  step: data.step,
  status: data.status,
  items: data.items,
  comment: data.comment,
  confirmed_at: data.confirmed_at,
});

const mapExportRecord = (data: Record<string, any>): ExportRecord => ({
  id: data.id,
  run_id: data.run_id,
  review_session_id: data.review_session_id,
  status: data.status,
  graph_write_status: data.graph_write_status,
  snapshot_bucket: data.snapshot_bucket,
  snapshot_object_key: data.snapshot_object_key,
  snapshot_checksum: data.snapshot_checksum,
  snapshot_size: data.snapshot_size,
  error_message: data.error_message,
  retry_count: data.retry_count,
});

export const pipelineApi = {
  listRuns: async (): Promise<PipelineRun[]> => {
    const { data } = await api.get("/pipeline/runs");
    return data.map((item: Record<string, unknown>) => ({
      id: item.id as string,
      sourceType: item.source_type as string,
      sourceLocator: item.source_locator as string,
      sourcePayload: item.source_payload as PipelineRun["sourcePayload"],
      status: item.status as PipelineRun["status"],
      currentStep: item.current_step as PipelineRun["currentStep"],
      steps: mapSteps(item.steps as Record<string, {
        key: string;
        status: string;
        summary: string | null;
        preview_version: number;
      }>),
    }));
  },

  createRun: async (payload: CreatePipelineRunRequest): Promise<PipelineRun> => {
    const { data } = await api.post("/pipeline/runs", {
      source_type: payload.sourceType,
      source_locator: payload.sourceLocator,
    });

    return {
      id: data.id,
      sourceType: data.source_type,
      sourceLocator: data.source_locator,
      sourcePayload: data.source_payload,
      status: data.status,
      currentStep: data.current_step,
      steps: mapSteps(data.steps),
    };
  },

  getRun: async (runId: string): Promise<PipelineRun> => {
    const { data } = await api.get(`/pipeline/runs/${runId}`);
    return {
      id: data.id,
      sourceType: data.source_type,
      sourceLocator: data.source_locator,
      sourcePayload: data.source_payload,
      status: data.status,
      currentStep: data.current_step,
      steps: mapSteps(data.steps),
    };
  },

  getLatestPreview: async (runId: string, step: PipelineStepKey): Promise<PipelinePreview> => {
    const { data } = await api.get(`/pipeline/runs/${runId}/steps/${step}/preview`);
    return mapPreview(data);
  },

  listPreviewArtifacts: async (runId: string, step: PipelineStepKey): Promise<PipelinePreview[]> => {
    const { data } = await api.get(`/pipeline/runs/${runId}/steps/${step}/artifacts`);
    return data.map((item: Record<string, any>) => mapPreview(item));
  },

  previewStep: async (runId: string, step: PipelineStepKey): Promise<PipelinePreview> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/steps/${step}/preview`);
    return mapPreview(data);
  },

  rerunStep: async (runId: string, step: PipelineStepKey): Promise<PipelinePreview> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/steps/${step}/rerun`);
    return mapPreview(data);
  },

  confirmStep: async (runId: string, step: PipelineStepKey): Promise<PipelineRun> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/steps/${step}/confirm`);
    return {
      id: data.id,
      sourceType: data.source_type,
      sourceLocator: data.source_locator,
      sourcePayload: data.source_payload,
      status: data.status,
      currentStep: data.current_step,
      steps: mapSteps(data.steps),
    };
  },

  rollbackStep: async (runId: string, step: PipelineStepKey): Promise<PipelineRun> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/steps/${step}/rollback`);
    return {
      id: data.id,
      sourceType: data.source_type,
      sourceLocator: data.source_locator,
      sourcePayload: data.source_payload,
      status: data.status,
      currentStep: data.current_step,
      steps: mapSteps(data.steps),
    };
  },

  uploadSourceFile: async (file: File): Promise<PipelineUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post("/pipeline/uploads", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data as PipelineUploadResponse;
  },

  createReviewSession: async (runId: string): Promise<ReviewSession> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/review-session`);
    return mapReviewSession(data);
  },

  getReviewSession: async (runId: string): Promise<ReviewSession> => {
    const { data } = await api.get(`/pipeline/runs/${runId}/review-session`);
    return mapReviewSession(data);
  },

  updateReviewItem: async (
    runId: string,
    itemKey: string,
    payload: UpdateReviewItemRequest,
  ): Promise<ReviewSession> => {
    const { data } = await api.patch(`/pipeline/runs/${runId}/review-session/items/${itemKey}`, {
      decision: payload.decision,
      revised_payload: payload.revisedPayload,
      comment: payload.comment,
    });
    return mapReviewSession(data);
  },

  confirmReviewSession: async (runId: string): Promise<ReviewSession> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/review-session/confirm`, {});
    return mapReviewSession(data);
  },

  buildExportPlan: async (runId: string): Promise<PipelinePreview> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/export-plan`);
    return {
      runId,
      step: "export",
      status: "preview_ready",
      summary: data.blocking_issues?.length ? "导出/入库预览存在阻塞" : "导出/入库预览已生成",
      previewKind: "export_plan",
      previewPayload: data,
      warnings: [],
      errors: data.blocking_issues ?? [],
      artifacts: [],
      nextStepReady: !(data.blocking_issues?.length ?? 0),
    };
  },

  executeExport: async (runId: string): Promise<ExportRecord> => {
    const { data } = await api.post(`/pipeline/runs/${runId}/export-executions`);
    return mapExportRecord(data);
  },

  getLatestExportExecution: async (runId: string): Promise<ExportRecord> => {
    const { data } = await api.get(`/pipeline/runs/${runId}/export-executions/latest`);
    return mapExportRecord(data);
  },
};
