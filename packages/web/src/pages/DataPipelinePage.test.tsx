import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../App";
import { renderWithProviders } from "../test/render-with-providers";

vi.mock("../services/pipelineApi", () => ({
  pipelineApi: {
    uploadSourceFile: vi.fn().mockResolvedValue({
      upload_token: "upload-demo.zip",
      filename: "demo.zip",
      stored_path: ".tmp/pipeline_sources/uploads/upload-demo.zip",
      content_type: "application/zip",
    }),
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
        source_type: "huggingface_repo",
        source_locator: "ZJUFanLab/TCMChat-dataset-600k",
        repo_url: "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k",
        readme_url: "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k/resolve/main/README.md",
        readme_content: "# TCMChat dataset\n",
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

  it("shows source type options and local upload control", async () => {
    renderWithProviders(<App />, "/data/pipeline");

    expect(await screen.findByLabelText("来源类型")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Hugging Face Repo" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "远程直链" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "本地上传" })).toBeInTheDocument();
    expect(screen.getByLabelText("Repo ID")).toBeInTheDocument();
  });

  it("sends structured source payload when creating a Hugging Face run", async () => {
    const user = userEvent.setup();
    const { pipelineApi } = await import("../services/pipelineApi");

    renderWithProviders(<App />, "/data/pipeline");

    await user.clear(await screen.findByLabelText("Repo ID"));
    await user.type(screen.getByLabelText("Repo ID"), "ZJUFanLab/TCMChat-dataset-600k");
    await user.click(screen.getByRole("button", { name: "运行预览" }));

    await waitFor(() => {
      expect(pipelineApi.createRun).toHaveBeenCalledWith(
        expect.objectContaining({
          sourceType: "huggingface_repo",
          sourceLocator: "ZJUFanLab/TCMChat-dataset-600k",
          sourcePayload: {
            source_type: "huggingface_repo",
            source_input: { repo_id: "ZJUFanLab/TCMChat-dataset-600k" },
          },
        }),
      );
    });
  });

  it("renders Hugging Face links and README content in the preview panel", async () => {
    const user = userEvent.setup();

    renderWithProviders(<App />, "/data/pipeline");

    await user.click(await screen.findByRole("button", { name: "运行预览" }));

    expect(await screen.findByText("README 预览")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "打开仓库页" })).toHaveAttribute(
      "href",
      "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k",
    );
    expect(screen.getByText("# TCMChat dataset")).toBeInTheDocument();
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
