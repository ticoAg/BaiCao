# Pipeline Source Ingestion Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `/data/pipeline` 的 `source_ingest` 升级为统一来源录入入口，第一版同时支持 Hugging Face repo、远程直链和本地上传文件/压缩包，并在固定目录中完成缓存、解压、README 预览与本地工作目录物化。

**Architecture:** 采用 contract-first 路径：先定义结构化来源契约，再在 API 侧新增上传与来源物化能力，让 `source_ingest` / `source_preview` 统一消费本地工作目录，最后把前端从字符串 locator 表单升级为类型化来源录入与结构化预览。为降低迁移风险，保留 `source_locator` 作为展示摘要字段，并新增 `source_payload` 作为真实结构化来源真源。

**Tech Stack:** TypeScript, React 18, Zustand, Ant Design, FastAPI, Pydantic v2, SQLAlchemy, pytest, Vitest

---

## Execution Status

- 当前状态：已完成
- 执行模式：当前会话内联执行
- 结果摘要：
  - 已落地结构化来源契约 `source_payload`
  - 已新增上传接口与固定来源存储目录
  - 已实现 `local_upload`、`remote_url`、`huggingface_repo` 的来源物化、缓存 / 解压与 README 预览
  - 已把 `/data/pipeline` 升级为来源类型切换 + 结构化预览面板

## File Map

### Shared Contract

- Modify: `packages/shared/types/index.ts`
  - 新增 pipeline 来源类型、来源输入联合类型、上传响应和结构化预览字段类型

### API Contract And Persistence

- Modify: `packages/api/app/core/config.py`
  - 新增固定数据目录配置
- Modify: `packages/api/app/models/pipeline.py`
  - 为 `pipeline_runs` 增加 `source_payload` JSON 列
- Modify: `packages/api/app/pipeline/models.py`
  - 新增结构化来源 Pydantic 模型
- Modify: `packages/api/app/pipeline/schemas.py`
  - 创建 run 请求支持结构化来源；新增上传响应 schema
- Modify: `packages/api/app/pipeline/storage.py`
  - 持久化 / 反序列化 `source_payload`
- Modify: `packages/api/app/api/pipeline.py`
  - 增加上传接口与新请求序列化
- Modify: `packages/api/app/api/pipeline_dependencies.py`
  - 注入来源物化服务

### API Source Materialization

- Create: `packages/api/app/pipeline/materialization.py`
  - 统一来源物化服务：缓存、工作目录、README 识别、候选文件识别、解压分发
- Create: `packages/api/app/pipeline/uploads.py`
  - 上传文件保存、`upload_token` 解析
- Modify: `packages/api/app/pipeline/adapters/huggingface.py`
  - 从 locator 摘要升级为 repo 结构化输入摘要
- Modify: `packages/api/app/pipeline/steps/source_ingest.py`
  - 改为执行真实来源物化
- Modify: `packages/api/app/pipeline/steps/source_preview.py`
  - 从本地工作目录读取 README 和候选文件内容
- Modify: `packages/api/app/pipeline/service.py`
  - `create_run` 与 preview 过程改为使用结构化来源

### API Tests

- Create: `packages/api/tests/unit/pipeline/test_materialization.py`
  - 物化、解压、README 识别、候选文件识别
- Modify: `packages/api/tests/unit/pipeline/test_models.py`
  - 结构化来源模型
- Modify: `packages/api/tests/unit/pipeline/test_service.py`
  - `source_ingest` / `source_preview` 新 payload
- Modify: `packages/api/tests/api/test_pipeline_routes.py`
  - 上传接口与结构化来源路由
- Create: `packages/api/tests/contract/test_pipeline_source_ingestion_contract.py`
  - API 契约覆盖

### Web

- Modify: `packages/web/src/types/pipeline.ts`
  - 引入结构化来源类型和上传响应
- Modify: `packages/web/src/services/pipelineApi.ts`
  - 新增上传 API；创建 run 发送结构化来源对象
- Modify: `packages/web/src/stores/pipelineStore.ts`
  - 用结构化来源状态替代字符串 locator
- Create: `packages/web/src/components/pipeline/SourceIngestionForm.tsx`
  - 来源类型切换、repo/url 输入、本地上传控件
- Modify: `packages/web/src/components/pipeline/PipelineActionPanel.tsx`
  - 嵌入 `SourceIngestionForm`
- Modify: `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
  - 结构化展示来源落盘结果、README 预览和 Hugging Face 链接
- Modify: `packages/web/src/components/pipeline/PipelineShell.tsx`
  - 传递新表单状态和事件
- Modify: `packages/web/src/hooks/usePipelineRun.ts`
  - 管理上传与 run 创建流程
- Modify: `packages/web/src/pages/DataPipelinePage.test.tsx`
  - 页面主链路回归

### Docs And Acceptance

- Modify: `docs/acceptance/data-pipeline-workbench-mainline.md`
  - 更新来源录入主链路验收
- Modify: `docs/superpowers/plans/2026-03-30-pipeline-source-ingestion-wave-1.md`
  - 实施过程中回填状态、证据与验证结果

## Task 1: Define Structured Source Contract

**Files:**
- Modify: `packages/shared/types/index.ts`
- Modify: `packages/api/app/pipeline/models.py`
- Modify: `packages/api/app/pipeline/schemas.py`
- Modify: `packages/api/app/models/pipeline.py`
- Test: `packages/api/tests/unit/pipeline/test_models.py`
- Test: `packages/api/tests/contract/test_pipeline_source_ingestion_contract.py`

- [ ] **Step 1: Write the failing model and contract tests**

```python
# packages/api/tests/unit/pipeline/test_models.py
from app.pipeline.models import PipelineSourceDefinition


def test_pipeline_source_definition_accepts_huggingface_repo():
    source = PipelineSourceDefinition.model_validate(
        {
            "source_type": "huggingface_repo",
            "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
        }
    )
    assert source.source_type == "huggingface_repo"
    assert source.source_input["repo_id"] == "ZJUFanLab/TCMChat-dataset-600k"


def test_pipeline_source_definition_rejects_missing_repo_id():
    try:
        PipelineSourceDefinition.model_validate(
            {"source_type": "huggingface_repo", "source_input": {}}
        )
    except Exception as exc:
        assert "repo_id" in str(exc)
    else:
        raise AssertionError("expected validation error")
```

```python
# packages/api/tests/contract/test_pipeline_source_ingestion_contract.py
async def test_create_run_accepts_structured_source(client):
    resp = await client.post(
        "/api/v1/pipeline/runs",
        json={
            "source_type": "huggingface_repo",
            "source_locator": "ZJUFanLab/TCMChat-dataset-600k",
            "source_payload": {
                "source_type": "huggingface_repo",
                "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
            },
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["source_type"] == "huggingface_repo"
    assert data["source_payload"]["source_input"]["repo_id"] == "ZJUFanLab/TCMChat-dataset-600k"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_models.py tests/contract/test_pipeline_source_ingestion_contract.py -q
```

Expected:

- `PipelineSourceDefinition` 未定义
- `source_payload` 未出现在请求 / 响应 schema 中

- [ ] **Step 3: Implement the structured source models and schema**

```python
# packages/api/app/pipeline/models.py
class PipelineSourceType(StrEnum):
    HUGGINGFACE_REPO = "huggingface_repo"
    REMOTE_URL = "remote_url"
    LOCAL_UPLOAD = "local_upload"


class PipelineSourceDefinition(BaseModel):
    source_type: PipelineSourceType
    source_input: dict[str, Any] = Field(default_factory=dict)

    @property
    def display_locator(self) -> str:
        if self.source_type == PipelineSourceType.HUGGINGFACE_REPO:
            return str(self.source_input.get("repo_id", ""))
        if self.source_type == PipelineSourceType.REMOTE_URL:
            return str(self.source_input.get("url", ""))
        return str(self.source_input.get("upload_token", ""))
```

```python
# packages/api/app/pipeline/schemas.py
class CreatePipelineRunRequest(BaseModel):
    source_type: str
    source_locator: str
    source_payload: dict[str, Any] = Field(default_factory=dict)
```

```python
# packages/api/app/models/pipeline.py
source_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
```

- [ ] **Step 4: Run targeted tests to verify the contract passes**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_models.py tests/contract/test_pipeline_source_ingestion_contract.py -q
```

Expected:

- 新增模型测试通过
- 契约测试通过，响应体包含 `source_payload`

- [ ] **Step 5: Commit**

```bash
git add packages/shared/types/index.ts packages/api/app/pipeline/models.py packages/api/app/pipeline/schemas.py packages/api/app/models/pipeline.py packages/api/tests/unit/pipeline/test_models.py packages/api/tests/contract/test_pipeline_source_ingestion_contract.py
git commit -m "feat(pipeline): add structured source contract"
```

## Task 2: Add Fixed Storage Dir And Upload Endpoint

**Files:**
- Modify: `packages/api/app/core/config.py`
- Modify: `packages/api/app/api/pipeline.py`
- Modify: `packages/api/app/api/pipeline_dependencies.py`
- Create: `packages/api/app/pipeline/uploads.py`
- Test: `packages/api/tests/api/test_pipeline_routes.py`

- [ ] **Step 1: Write the failing upload route test**

```python
async def test_upload_source_file_returns_upload_token(client):
    files = {"file": ("sample.csv", b"node_name,source\n陈皮,本草纲目\n", "text/csv")}
    resp = await client.post("/api/v1/pipeline/uploads", files=files)

    assert resp.status_code == 201
    data = resp.json()
    assert data["upload_token"]
    assert data["filename"] == "sample.csv"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd packages/api && uv run pytest tests/api/test_pipeline_routes.py -q
```

Expected:

- `POST /api/v1/pipeline/uploads` 返回 404

- [ ] **Step 3: Implement config and upload storage**

```python
# packages/api/app/core/config.py
pipeline_source_storage_dir: str = "tmp/data"
```

```python
# packages/api/app/pipeline/uploads.py
class UploadedSourceFile(BaseModel):
    upload_token: str
    filename: str
    stored_path: str
    content_type: str | None = None


class SourceUploadService:
    async def save_upload(self, upload_file: UploadFile) -> UploadedSourceFile:
        suffix = Path(upload_file.filename or "upload.bin").suffix
        upload_token = f"upload-{uuid4().hex}{suffix}"
        target = self.upload_root / upload_token
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(await upload_file.read())
        return UploadedSourceFile(
            upload_token=upload_token,
            filename=upload_file.filename or upload_token,
            stored_path=str(target),
            content_type=upload_file.content_type,
        )
```

```python
# packages/api/app/api/pipeline.py
@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_pipeline_source_file(
    file: UploadFile,
    upload_service: SourceUploadService = Depends(get_source_upload_service),
):
    return await upload_service.save_upload(file)
```

- [ ] **Step 4: Run API test to verify upload works**

Run:

```bash
cd packages/api && uv run pytest tests/api/test_pipeline_routes.py::TestPipelineUploads::test_upload_source_file_returns_upload_token -q
```

Expected:

- 单测通过
- 返回 `upload_token`、`filename`、`content_type`

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/core/config.py packages/api/app/api/pipeline.py packages/api/app/api/pipeline_dependencies.py packages/api/app/pipeline/uploads.py packages/api/tests/api/test_pipeline_routes.py
git commit -m "feat(pipeline): add source upload endpoint"
```

## Task 3: Build Source Materialization Service

**Files:**
- Create: `packages/api/app/pipeline/materialization.py`
- Modify: `packages/api/app/pipeline/adapters/huggingface.py`
- Test: `packages/api/tests/unit/pipeline/test_materialization.py`

- [ ] **Step 1: Write the failing materialization tests**

```python
async def test_materialize_uploaded_zip_extracts_archive(tmp_path):
    service = SourceMaterializationService(storage_root=tmp_path)
    uploaded = tmp_path / "uploads" / "dataset.zip"
    uploaded.parent.mkdir(parents=True, exist_ok=True)
    build_zip(uploaded, {"README.md": "# demo\n", "data.jsonl": '{"name":"陈皮"}\n'})

    result = await service.materialize(
        run_id="pipeline-1",
        source_type="local_upload",
        source_input={"upload_token": uploaded.name, "stored_path": str(uploaded)},
    )

    assert result.is_archive is True
    assert result.readme_path.endswith("README.md")
    assert any(path.endswith("data.jsonl") for path in result.candidate_files)
```

```python
async def test_materialize_huggingface_repo_returns_repo_urls(tmp_path):
    service = SourceMaterializationService(storage_root=tmp_path)
    result = await service._build_huggingface_metadata("ZJUFanLab/TCMChat-dataset-600k")

    assert result["repo_url"] == "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k"
    assert result["readme_url"].endswith("/resolve/main/README.md")
```

- [ ] **Step 2: Run the unit tests to verify they fail**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_materialization.py -q
```

Expected:

- `SourceMaterializationService` 未定义
- README / candidate file assertions 失败

- [ ] **Step 3: Implement materialization, archive handling, and metadata detection**

```python
# packages/api/app/pipeline/materialization.py
class MaterializedSource(BaseModel):
    run_workdir: str
    source_dir: str
    extracted_dir: str | None = None
    cache_hit: bool = False
    is_archive: bool = False
    archive_format: str | None = None
    readme_path: str | None = None
    readme_content: str | None = None
    candidate_files: list[str] = Field(default_factory=list)
    repo_url: str | None = None
    readme_url: str | None = None


class SourceMaterializationService:
    async def materialize(self, run_id: str, source_type: str, source_input: dict[str, Any]) -> MaterializedSource:
        if source_type == "local_upload":
            return await self._materialize_local_upload(run_id, source_input)
        if source_type == "remote_url":
            return await self._materialize_remote_url(run_id, source_input)
        if source_type == "huggingface_repo":
            return await self._materialize_huggingface_repo(run_id, source_input)
        raise ValueError(f"unsupported source_type: {source_type}")
```

Implementation rules:

- `huggingface_repo`:
  - 生成 `repo_url` 与 `readme_url`
  - 缓存目录放在 `cache/huggingface/<repo_id>/`
- `remote_url`:
  - 只接受 `http/https`
  - 缓存目录放在 `cache/remote/<url_hash>/`
- `local_upload`:
  - 从 `stored_path` 复制到 `runs/<run_id>/source/`
- Archive detection:
  - 支持 `zip`、`tar.gz`、`tgz`
  - 解压前过滤路径穿越
- README detection:
  - 优先 `extracted/README.md`，再回退 `source/README.md`
- Candidate priority:
  - `jsonl > csv > txt > md`

- [ ] **Step 4: Run materialization tests**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_materialization.py -q
```

Expected:

- 本地上传 / 解压 / README 识别测试通过
- Hugging Face 链接生成测试通过

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/materialization.py packages/api/app/pipeline/adapters/huggingface.py packages/api/tests/unit/pipeline/test_materialization.py
git commit -m "feat(pipeline): add source materialization service"
```

## Task 4: Integrate Materialization Into `source_ingest` And `source_preview`

**Files:**
- Modify: `packages/api/app/pipeline/service.py`
- Modify: `packages/api/app/pipeline/storage.py`
- Modify: `packages/api/app/pipeline/steps/source_ingest.py`
- Modify: `packages/api/app/pipeline/steps/source_preview.py`
- Modify: `packages/api/tests/unit/pipeline/test_service.py`
- Modify: `packages/api/tests/api/test_pipeline_routes.py`

- [ ] **Step 1: Write the failing service and route tests**

```python
@pytest.mark.asyncio
async def test_source_ingest_preview_returns_materialized_paths(tmp_path):
    materialization_service = StubMaterializationService(
        run_workdir=str(tmp_path / "runs" / "pipeline-1"),
        source_dir=str(tmp_path / "runs" / "pipeline-1" / "source"),
        repo_url="https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k",
        readme_url="https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k/resolve/main/README.md",
    )
    service = PipelineService(materialization_service=materialization_service)
    run = await service.create_run(
        source_type="huggingface_repo",
        source_locator="ZJUFanLab/TCMChat-dataset-600k",
        source_payload={
            "source_type": "huggingface_repo",
            "source_input": {"repo_id": "ZJUFanLab/TCMChat-dataset-600k"},
        },
    )

    preview = await service.preview_step(run.id, PipelineStepKey.SOURCE_INGEST)
    assert preview.preview_payload["run_workdir"]
    assert "repo_url" in preview.preview_payload
```

```python
@pytest.mark.asyncio
async def test_source_preview_returns_readme_content(client):
    create_resp = await client.post(
        "/api/v1/pipeline/runs",
        json={
            "source_type": "local_upload",
            "source_locator": "upload-demo",
            "source_payload": {
                "source_type": "local_upload",
                "source_input": {"upload_token": "upload-demo"},
            },
        },
    )
    run_id = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/pipeline/runs/{run_id}/steps/source_preview/preview")
    assert resp.status_code == 200
    assert "readme_content" in resp.json()["preview_payload"]
```

- [ ] **Step 2: Run targeted tests to verify they fail**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q
```

Expected:

- `create_run()` 不接受 `source_payload`
- `source_ingest` payload 仍只有 locator 摘要

- [ ] **Step 3: Implement run persistence and step integration**

```python
# packages/api/app/pipeline/service.py
async def create_run(self, source_type: str, source_locator: str, source_payload: dict[str, Any] | None = None) -> PipelineRun:
    run = PipelineRun(
        source_type=source_type,
        source_locator=source_locator,
        source_payload=source_payload or {},
        status=PipelineRunStatus.PENDING,
        current_step=PipelineStepKey.SOURCE_INGEST,
        steps={key: PipelineStepState(key=key) for key in PIPELINE_STEP_ORDER},
    )
    return await self.storage.save_run(run)
```

```python
# packages/api/app/pipeline/steps/source_ingest.py
preview_payload = {
    "resolved_source_type": descriptor.source_type,
    "run_workdir": materialized.run_workdir,
    "source_dir": materialized.source_dir,
    "extracted_dir": materialized.extracted_dir,
    "cache_hit": materialized.cache_hit,
    "repo_url": materialized.repo_url,
    "readme_url": materialized.readme_url,
    "readme_path": materialized.readme_path,
    "candidate_files": materialized.candidate_files,
}
```

```python
# packages/api/app/pipeline/steps/source_preview.py
preview_payload = {
    "readme_path": materialized.readme_path,
    "readme_content": materialized.readme_content,
    "content_root": materialized.extracted_dir or materialized.source_dir,
    "primary_candidate": materialized.candidate_files[0] if materialized.candidate_files else None,
}
```

- [ ] **Step 4: Run API and service tests**

Run:

```bash
cd packages/api && uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py tests/contract/test_pipeline_source_ingestion_contract.py -q
```

Expected:

- `source_ingest` 与 `source_preview` 返回结构化 payload
- 上传与 run 创建接口联通

- [ ] **Step 5: Commit**

```bash
git add packages/api/app/pipeline/service.py packages/api/app/pipeline/storage.py packages/api/app/pipeline/steps/source_ingest.py packages/api/app/pipeline/steps/source_preview.py packages/api/tests/unit/pipeline/test_service.py packages/api/tests/api/test_pipeline_routes.py
git commit -m "feat(pipeline): materialize sources in preview steps"
```

## Task 5: Upgrade `/data/pipeline` To Structured Source Input

**Files:**
- Modify: `packages/web/src/types/pipeline.ts`
- Modify: `packages/web/src/services/pipelineApi.ts`
- Modify: `packages/web/src/stores/pipelineStore.ts`
- Create: `packages/web/src/components/pipeline/SourceIngestionForm.tsx`
- Modify: `packages/web/src/components/pipeline/PipelineActionPanel.tsx`
- Modify: `packages/web/src/components/pipeline/PipelineShell.tsx`
- Modify: `packages/web/src/hooks/usePipelineRun.ts`
- Modify: `packages/web/src/pages/DataPipelinePage.test.tsx`

- [ ] **Step 1: Write the failing page test**

```tsx
it("switches source type and uploads a local archive before preview", async () => {
  const user = userEvent.setup();
  renderWithProviders(<App />, "/data/pipeline");

  await user.click(await screen.findByRole("radio", { name: "本地上传" }));
  expect(screen.getByLabelText("上传文件")).toBeInTheDocument();
});
```

```tsx
it("shows Hugging Face repo input and sends structured source payload", async () => {
  const user = userEvent.setup();
  renderWithProviders(<App />, "/data/pipeline");

  await user.clear(screen.getByLabelText("Repo ID"));
  await user.type(screen.getByLabelText("Repo ID"), "ZJUFanLab/TCMChat-dataset-600k");
  await user.click(screen.getByRole("button", { name: "运行预览" }));

  expect(pipelineApi.createRun).toHaveBeenCalledWith(
    expect.objectContaining({
      sourceType: "huggingface_repo",
      sourcePayload: {
        source_type: "huggingface_repo",
        source_input: { repo_id: "ZJUFanLab/TCMChat-dataset-600k" },
      },
    }),
  );
});
```

- [ ] **Step 2: Run the page test to verify it fails**

Run:

```bash
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
```

Expected:

- 页面中不存在来源类型切换器 / 上传控件
- `createRun` 仍只接收 `sourceType + sourceLocator`

- [ ] **Step 3: Implement source form, upload flow, and structured request**

```tsx
// packages/web/src/components/pipeline/SourceIngestionForm.tsx
<Radio.Group value={sourceType} onChange={(event) => onSourceTypeChange(event.target.value)}>
  <Radio.Button value="huggingface_repo">Hugging Face Repo</Radio.Button>
  <Radio.Button value="remote_url">远程直链</Radio.Button>
  <Radio.Button value="local_upload">本地上传</Radio.Button>
</Radio.Group>
```

```ts
// packages/web/src/services/pipelineApi.ts
createRun: async (payload: CreatePipelineRunRequest): Promise<PipelineRun> => {
  const { data } = await api.post("/pipeline/runs", {
    source_type: payload.sourceType,
    source_locator: payload.sourceLocator,
    source_payload: payload.sourcePayload,
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
}
```

```ts
// packages/web/src/hooks/usePipelineRun.ts
const activeRun = run ?? (await pipelineApi.createRun(buildCreateRunPayload(sourceFormState)));
```

- [ ] **Step 4: Run the page test to verify the form flow passes**

Run:

```bash
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
```

Expected:

- 页面测试通过
- 结构化来源请求与上传流程已接线

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/types/pipeline.ts packages/web/src/services/pipelineApi.ts packages/web/src/stores/pipelineStore.ts packages/web/src/components/pipeline/SourceIngestionForm.tsx packages/web/src/components/pipeline/PipelineActionPanel.tsx packages/web/src/components/pipeline/PipelineShell.tsx packages/web/src/hooks/usePipelineRun.ts packages/web/src/pages/DataPipelinePage.test.tsx
git commit -m "feat(web): add structured source ingestion form"
```

## Task 6: Render Structured Source Preview And README Content

**Files:**
- Modify: `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
- Modify: `packages/web/src/pages/DataPipelinePage.test.tsx`
- Test: `packages/web/src/pages/DataPipelinePage.test.tsx`

- [ ] **Step 1: Write the failing UI assertions**

```tsx
it("renders Hugging Face links and README content in the preview panel", async () => {
  renderWithProviders(<App />, "/data/pipeline");

  expect(await screen.findByText("README 预览")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "打开仓库页" })).toHaveAttribute(
    "href",
    "https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k",
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
```

Expected:

- 预览面板只显示原始 JSON，没有 README 分区和链接

- [ ] **Step 3: Implement structured preview rendering**

```tsx
// packages/web/src/components/pipeline/PipelinePreviewPanel.tsx
{preview.previewPayload.repo_url ? (
  <a href={String(preview.previewPayload.repo_url)} target="_blank" rel="noreferrer">
    打开仓库页
  </a>
) : null}

{preview.previewPayload.readme_content ? (
  <Card size="small" title="README 预览">
    <Paragraph style={{ whiteSpace: "pre-wrap" }}>
      {String(preview.previewPayload.readme_content)}
    </Paragraph>
  </Card>
) : null}
```

- [ ] **Step 4: Run web verification**

Run:

```bash
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

Expected:

- 页面测试通过
- `typecheck` 通过
- `build` 通过

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/components/pipeline/PipelinePreviewPanel.tsx packages/web/src/pages/DataPipelinePage.test.tsx
git commit -m "feat(web): render source materialization preview"
```

## Task 7: Acceptance And Final Verification

**Files:**
- Modify: `docs/acceptance/data-pipeline-workbench-mainline.md`
- Modify: `docs/superpowers/plans/2026-03-30-pipeline-source-ingestion-wave-1.md`

- [ ] **Step 1: Update acceptance doc with the new source-ingest mainline**

```md
- `huggingface_repo`：创建 run，运行 `source_ingest`，返回 repo 链接、README 链接、本地工作目录
- `remote_url`：创建 run，运行 `source_ingest`，返回缓存命中与解压状态
- `local_upload`：先上传文件，再创建 run，运行 `source_preview`，页面显示 README 或主候选文件预览
```

- [ ] **Step 2: Run final verification**

Run:

```bash
cd packages/api && uv run ruff check app tests
cd packages/api && uv run ty check
cd packages/api && uv run pytest -m "not integration" -q
pnpm --dir packages/shared typecheck
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web exec vp build
```

Expected:

- API 静态检查通过
- API 非集成测试通过
- `packages/shared` typecheck 通过
- 页面测试通过
- Web build 通过

- [ ] **Step 3: Record evidence in this plan**

```md
## 实现证据
- `packages/api/app/pipeline/materialization.py`
- `packages/api/app/pipeline/uploads.py`
- `packages/web/src/components/pipeline/SourceIngestionForm.tsx`

## 验证结果
- `cd packages/api && uv run pytest -m "not integration" -q` → 记录通过数
- `pnpm --dir packages/web exec vp build` → 记录通过
```

- [ ] **Step 4: Commit**

```bash
git add docs/acceptance/data-pipeline-workbench-mainline.md docs/superpowers/plans/2026-03-30-pipeline-source-ingestion-wave-1.md
git commit -m "docs(acceptance): record pipeline source ingestion wave 1"
```

## Self-Review

### Spec coverage

- 统一来源录入入口：Task 5
- 固定目录与懒下载缓存：Task 2、Task 3、Task 4
- 支持三类来源：Task 1、Task 3、Task 5
- 支持压缩包解压：Task 3
- 页面 README 预览与 Hugging Face 链接：Task 4、Task 6
- 验收与验证边界：Task 7

### Placeholder scan

- 未保留待补全占位语句
- 每个任务都包含明确文件路径、测试命令与最小代码草图

### Type consistency

- 统一使用 `source_payload` 作为结构化来源字段
- 统一使用 `huggingface_repo`、`remote_url`、`local_upload` 作为来源类型
- 前后端都保留 `source_locator` 作为展示摘要，不再作为结构化真源

## Implementation Evidence

- `packages/api/app/pipeline/materialization.py`
- `packages/api/app/pipeline/uploads.py`
- `packages/api/app/pipeline/service.py`
- `packages/api/app/pipeline/steps/source_ingest.py`
- `packages/api/app/pipeline/steps/source_preview.py`
- `packages/api/app/api/pipeline.py`
- `packages/shared/types/index.ts`
- `packages/web/src/components/pipeline/SourceIngestionForm.tsx`
- `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
- `packages/web/src/hooks/usePipelineRun.ts`

## Verification Results

已通过：

```bash
cd packages/api && uv run ruff check app tests
cd packages/api && uv run ty check
cd packages/api && uv run pytest -m "not integration" -q
pnpm --dir packages/shared typecheck
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

结果摘要：

- API `ruff`：通过
- API `ty`：通过
- API 非集成测试：`240 passed, 3 deselected`
- `packages/shared` typecheck：通过
- `DataPipelinePage` 页面测试：`8 passed`
- `packages/web` typecheck：通过
- `packages/web` build：通过
