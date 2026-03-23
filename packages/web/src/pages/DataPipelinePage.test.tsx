import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { renderWithProviders } from "../test/render-with-providers";

vi.mock("../services/pipelineApi", () => ({
  pipelineApi: {
    createRun: vi.fn().mockResolvedValue({
      id: "pipeline-1",
      sourceType: "huggingface",
      sourceLocator: "ZJUFanLab/TCMChat-dataset-600k",
      status: "pending",
      currentStep: "source_ingest",
      steps: {
        source_ingest: {
          key: "source_ingest",
          status: "pending",
          summary: null,
          previewVersion: 0,
        },
      },
    }),
    previewStep: vi.fn().mockResolvedValue({
      runId: "pipeline-1",
      step: "source_ingest",
      status: "preview_ready",
      summary: "步骤预览已生成",
      previewKind: "summary",
      previewPayload: {
        source_type: "huggingface",
        source_locator: "ZJUFanLab/TCMChat-dataset-600k",
        step: "source_ingest",
        preview_version: 1,
      },
      warnings: [],
      errors: [],
      artifacts: [],
      nextStepReady: false,
    }),
    confirmStep: vi.fn().mockResolvedValue({
      id: "pipeline-1",
      sourceType: "huggingface",
      sourceLocator: "ZJUFanLab/TCMChat-dataset-600k",
      status: "running",
      currentStep: "source_preview",
      steps: {
        source_ingest: {
          key: "source_ingest",
          status: "confirmed",
          summary: "source_ingest confirmed",
          previewVersion: 1,
        },
      },
    }),
    getRun: vi.fn().mockResolvedValue({
      id: "pipeline-restore",
      sourceType: "jsonl",
      sourceLocator: "packages/db/import/herbs.jsonl",
      status: "running",
      currentStep: "source_preview",
      steps: {
        source_ingest: {
          key: "source_ingest",
          status: "confirmed",
          summary: "source_ingest confirmed",
          previewVersion: 1,
        },
        source_preview: {
          key: "source_preview",
          status: "pending",
          summary: null,
          previewVersion: 0,
        },
      },
    }),
    getLatestPreview: vi.fn().mockResolvedValue({
      runId: "pipeline-restore",
      step: "source_preview",
      status: "preview_ready",
      summary: "已恢复最近预览",
      previewKind: "summary",
      previewPayload: {
        source_type: "jsonl",
        source_locator: "packages/db/import/herbs.jsonl",
        step: "source_preview",
        preview_version: 1,
      },
      warnings: [],
      errors: [],
      artifacts: [],
      nextStepReady: false,
    }),
    listPreviewArtifacts: vi.fn().mockResolvedValue([
      {
        runId: "pipeline-restore",
        step: "source_preview",
        status: "preview_ready",
        summary: "已恢复最近预览",
        previewKind: "summary",
        previewPayload: {
          source_type: "jsonl",
          source_locator: "packages/db/import/herbs.jsonl",
          step: "source_preview",
          preview_version: 2,
        },
        warnings: [],
        errors: [],
        artifacts: [{ key: "source_preview-preview-v2", label: "source_preview 预览快照 v2", uri: null }],
        nextStepReady: false,
      },
      {
        runId: "pipeline-restore",
        step: "source_preview",
        status: "preview_ready",
        summary: "已恢复最近预览",
        previewKind: "summary",
        previewPayload: {
          source_type: "jsonl",
          source_locator: "packages/db/import/herbs.jsonl",
          step: "source_preview",
          preview_version: 1,
        },
        warnings: [],
        errors: [],
        artifacts: [{ key: "source_preview-preview-v1", label: "source_preview 预览快照 v1", uri: null }],
        nextStepReady: false,
      },
    ]),
    listRuns: vi.fn().mockResolvedValue([
      {
        id: "pipeline-restore",
        sourceType: "jsonl",
        sourceLocator: "packages/db/import/herbs.jsonl",
        status: "running",
        currentStep: "source_preview",
        steps: {
          source_ingest: {
            key: "source_ingest",
            status: "confirmed",
            summary: "source_ingest confirmed",
            previewVersion: 1,
          },
        },
      },
    ]),
    rerunStep: vi.fn().mockResolvedValue({
      runId: "pipeline-restore",
      step: "source_preview",
      status: "preview_ready",
      summary: "步骤预览已生成",
      previewKind: "summary",
      previewPayload: {
        source_type: "jsonl",
        source_locator: "packages/db/import/herbs.jsonl",
        step: "source_preview",
        preview_version: 2,
      },
      warnings: [],
      errors: [],
      artifacts: [],
      nextStepReady: false,
    }),
    rollbackStep: vi.fn().mockResolvedValue({
      id: "pipeline-restore",
      sourceType: "jsonl",
      sourceLocator: "packages/db/import/herbs.jsonl",
      status: "running",
      currentStep: "source_ingest",
      steps: {
        source_ingest: {
          key: "source_ingest",
          status: "pending",
          summary: null,
          previewVersion: 0,
        },
        source_preview: {
          key: "source_preview",
          status: "pending",
          summary: null,
          previewVersion: 0,
        },
      },
    }),
  },
}));

describe("DataPipelinePage", () => {
  it("renders the pipeline workbench route with fixed steps", async () => {
    renderWithProviders(<App />, "/data/pipeline");

    expect(await screen.findByTestId("pipeline-shell")).toBeInTheDocument();
    expect(screen.getByTestId("pipeline-step-rail")).toBeInTheDocument();
    expect(screen.getByTestId("pipeline-action-panel")).toBeInTheDocument();
    expect(screen.getByTestId("pipeline-preview-panel")).toBeInTheDocument();
    expect(screen.getByText("接入来源")).toBeInTheDocument();
    expect(screen.getByText("映射到共享图模型")).toBeInTheDocument();
  });

  it("creates a run and shows preview summary when preview is triggered", async () => {
    const user = userEvent.setup();

    renderWithProviders(<App />, "/data/pipeline");

    await user.click(await screen.findByRole("button", { name: "运行预览" }));

    await waitFor(() => {
      expect(screen.getByText("步骤预览已生成")).toBeInTheDocument();
    });
    expect(screen.getByText("当前步骤：接入来源")).toBeInTheDocument();
  });

  it("restores an existing run from the URL query", async () => {
    renderWithProviders(<App />, "/data/pipeline?runId=pipeline-restore");

    expect(await screen.findByText("当前步骤：原始内容预览")).toBeInTheDocument();
    expect(screen.getByText("来源类型：jsonl")).toBeInTheDocument();
    expect(await screen.findByText("已恢复最近预览")).toBeInTheDocument();
    expect(await screen.findByText("历史快照")).toBeInTheDocument();
    expect(screen.getByText("source_preview 预览快照 v2")).toBeInTheDocument();
  });

  it("shows recent runs in the step rail", async () => {
    renderWithProviders(<App />, "/data/pipeline");

    expect(await screen.findByRole("button", { name: "恢复任务 pipeline-restore" })).toBeInTheDocument();
  });

  it("rolls back the current run to the previous step", async () => {
    const user = userEvent.setup();

    renderWithProviders(<App />, "/data/pipeline?runId=pipeline-restore");

    expect(await screen.findByText("当前步骤：原始内容预览")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "回退到上一步" }));

    expect(await screen.findByText("当前步骤：接入来源")).toBeInTheDocument();
  });
});
