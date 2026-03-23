import axios from "axios";
import type {
  CreatePipelineRunRequest,
  PipelinePreview,
  PipelineRun,
  PipelineStepKey,
  PipelineStepState,
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

export const pipelineApi = {
  listRuns: async (): Promise<PipelineRun[]> => {
    const { data } = await api.get("/pipeline/runs");
    return data.map((item: Record<string, unknown>) => ({
      id: item.id as string,
      sourceType: item.source_type as string,
      sourceLocator: item.source_locator as string,
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
      status: data.status,
      currentStep: data.current_step,
      steps: mapSteps(data.steps),
    };
  },
};
