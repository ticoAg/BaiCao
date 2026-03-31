<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "pipeline", "workbench", "knowledge-model"]
summary: 数据处理工作台七步预览主链路验收
audience: developer
---
-->

# 数据处理工作台主链路验收

## 1. 概述

- 功能名称：数据处理工作台七步预览主链路与统一来源录入
- 验收目标：验证 `pipeline` 在固定七步中返回结构化预览，并支持 `huggingface_repo`、`remote_url`、`local_upload` 三类来源在 `source_ingest` / `source_preview` 的录入、落盘、README 预览与回退主路径
- 对应需求：`docs/superpowers/plans/2026-03-30-pipeline-source-ingestion-wave-1.md`
- 对应任务：Task 1 至 Task 7
- 当前版本 / 日期：Wave 1 / 2026-03-30

## 2. 验收范围

### 包含

- `source_ingest`、`source_preview`、`normalize`、`extract`、`map_to_knowledge_model`、`human_review`、`export` 七步预览
- `manual`、`jsonl`、`csv`、`huggingface` 四类来源在入口阶段的最小预览分发
- `huggingface_repo`、`remote_url`、`local_upload` 三类结构化来源录入
- 上传接口、固定数据目录、压缩包解压、README 与候选文件预览
- 第 5 步共享模型映射未通过时禁止 `confirm`
- 回退到早期步骤后，后续步骤状态被重置

### 不包含

- 真实生产环境的大体量数据集下载压测
- 批量文件导入执行
- 完整 E2E 或页面截图回归

## 3. 前置条件

### 环境

- 工作目录：仓库 worktree 根目录
- 后端依赖：`packages/api`
- 样例数据：`packages/db/import/herbs.csv`、`packages/db/import/herbs.jsonl`
- 共享模型：`packages/knowledge_model/knowledge_model/`
- 来源存储目录：`tmp/data`

### 最小验证命令

```bash
cd packages/api
uv run pytest tests/unit/pipeline/test_materialization.py tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py tests/contract/test_pipeline_source_ingestion_contract.py -q
```

## 4. 验收步骤

### Step 1：创建结构化来源 pipeline run

- 操作：创建一条 `huggingface_repo`、`remote_url`、`local_upload`、`manual` 或文件来源的工作台 run
- 命令 / 页面入口：

```bash
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "source_type":"huggingface_repo",
    "source_locator":"ZJUFanLab/TCMChat-dataset-600k",
    "source_payload":{
      "source_type":"huggingface_repo",
      "source_input":{"repo_id":"ZJUFanLab/TCMChat-dataset-600k"}
    }
  }'
```

### Step 2：顺序请求七步预览

- 操作：依次请求七个固定步骤的 preview
- 命令 / 页面入口：

```bash
for step in source_ingest source_preview normalize extract map_to_knowledge_model human_review export; do
  curl -sS -X POST "http://localhost:8000/api/v1/pipeline/runs/$RUN_ID/steps/$step/preview"
done
```

### Step 3：验证入口来源分发

- 操作：分别以 `manual`、`jsonl`、`csv`、`huggingface`、`huggingface_repo`、`remote_url`、`local_upload` 创建 run，并请求 `source_ingest`
- 期望检查点：
  - `manual` 返回文本摘要
  - `jsonl` / `csv` 返回本地文件预览行
  - `huggingface` 返回 locator 摘要与格式校验结果
  - `huggingface_repo` 返回 `repo_url`、`readme_url`、本地 `run_workdir`
  - `remote_url` / `local_upload` 返回 `source_dir`、`extracted_dir`、`is_archive`

### Step 4：验证共享模型门禁

- 操作：创建空白 `manual` 来源，先请求 `map_to_knowledge_model/preview`，再请求 `confirm`
- 命令 / 页面入口：

```bash
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"manual","source_locator":"   "}'
curl -sS -X POST "http://localhost:8000/api/v1/pipeline/runs/$RUN_ID/steps/map_to_knowledge_model/preview"
curl -sS -X POST "http://localhost:8000/api/v1/pipeline/runs/$RUN_ID/steps/map_to_knowledge_model/confirm"
```

### Step 5：验证人工放行与回退

- 操作：对已生成预览的步骤执行 `confirm`，再执行 `rollback`
- 命令 / 页面入口：

```bash
curl -sS -X POST "http://localhost:8000/api/v1/pipeline/runs/$RUN_ID/steps/source_ingest/confirm"
curl -sS -X POST "http://localhost:8000/api/v1/pipeline/runs/$RUN_ID/steps/source_ingest/rollback"
```

## 5. 期望结果

### Step 1 预期

- 返回 `id`、`source_type`、`source_locator`、`source_payload`、`current_step`
- `current_step` 初始为 `source_ingest`

### Step 2 预期

- 七步不再统一返回 `summary` 占位，而是分别返回：
  - `source_descriptor`
  - `source_contents`
  - `normalized_content`
  - `extraction_candidates`
  - `graph_mapping`
  - `review_decision`
  - `export_plan`
- `extract.preview_payload.candidates` 至少提供一个可用于映射的候选实体
- `map_to_knowledge_model.preview_payload.validation.is_valid` 为 `true` 时才允许下一步准备完成

### Step 3 预期

- `manual` 的 `source_summary.kind` 为 `text`
- `jsonl` / `csv` 的 `source_summary.kind` 为 `file`
- `huggingface` 的 `source_summary.kind` 为 `remote_locator`
- `huggingface_repo` 的 `source_ingest.preview_payload` 提供 `repo_url`、`readme_url`、`run_workdir`
- `remote_url` / `local_upload` 在压缩包场景提供 `is_archive = true`、`archive_format`、`readme_path`
- `source_preview.preview_payload` 可返回 `readme_content` 与 `primary_candidate`

### Step 4 预期

- 空白来源的映射预览返回 `validation.is_valid = false`
- `confirm` 返回 400，错误信息为“当前映射结果未通过共享图模型校验，不能进入下一步”

### Step 5 预期

- `confirm` 后 `current_step` 前进到下一步
- `rollback` 后目标步骤及其后续步骤状态重置为 `pending`

## 6. 证据记录

### 实现证据

- `packages/api/app/pipeline/service.py:1` — 用步骤注册表替代统一 summary 占位
- `packages/api/app/pipeline/materialization.py:1` — 统一来源物化、缓存、解压、README 与候选文件识别
- `packages/api/app/pipeline/uploads.py:1` — 本地上传来源落盘与 `upload_token`
- `packages/api/app/pipeline/steps/__init__.py:1` — 固定七步 handler 注册入口
- `packages/api/app/pipeline/steps/source_ingest.py:1` — 结构化来源物化预览
- `packages/api/app/pipeline/steps/source_preview.py:1` — README 与主候选文件预览
- `packages/api/app/pipeline/steps/map_to_knowledge_model.py:1` — 共享模型映射与校验门禁
- `packages/api/app/pipeline/adapters/__init__.py:1` — 来源 adapter 分发入口
- `packages/web/src/components/pipeline/SourceIngestionForm.tsx:1` — 来源类型切换、Repo/URL 输入和本地上传入口
- `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx:1` — Hugging Face 链接与 README 结构化展示
- `packages/api/tests/unit/pipeline/test_service.py:1` — 七步预览与 adapter 分发单测
- `packages/api/tests/unit/pipeline/test_materialization.py:1` — 物化、解压、远程 URL / Hugging Face 缓存单测
- `packages/api/tests/api/test_pipeline_routes.py:1` — route 层多步预览与 map 门禁验证
- `packages/api/tests/contract/test_pipeline_source_ingestion_contract.py:1` — 结构化来源契约验证

### 运行证据

```bash
cd packages/api
uv run ruff check app tests
uv run ty check
uv run pytest -m "not integration" -q
```

- 当前结果：`ruff` 通过；`ty` 通过；`pytest` 结果为 `240 passed, 3 deselected`

```bash
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

- 当前结果：页面测试 `8 passed`；`typecheck` 通过；`build` 通过

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"manual","source_locator":"候选实体：陈皮（药材）"}'
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/source_ingest/preview"
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/source_preview/preview"
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/normalize/preview"
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/extract/preview"
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/map_to_knowledge_model/preview"
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/human_review/preview"
curl -sS -X POST "http://127.0.0.1:8000/api/v1/pipeline/runs/$RUN_ID/steps/export/preview"
```

- 当前结果：七步分别返回 `source_descriptor`、`source_contents`、`normalized_content`、`extraction_candidates`、`graph_mapping`、`review_decision`、`export_plan`
- `extract.preview_payload.candidates` 在本轮手工验证中返回 1 个候选项；`map_to_knowledge_model.preview_payload.validation.is_valid = true`

```bash
curl -sS -X POST http://127.0.0.1:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"jsonl","source_locator":"packages/db/import/herbs.jsonl"}'
curl -sS -X POST http://127.0.0.1:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"csv","source_locator":"packages/db/import/herbs.csv"}'
curl -sS -X POST http://127.0.0.1:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"huggingface","source_locator":"datasets/ticoag/herbs-demo"}'
```

- 当前结果：`manual` 的 `source_summary.kind = text`；`jsonl` / `csv` 的 `kind = file`；`huggingface` 的 `kind = remote_locator`
- 结构化来源路径：`huggingface_repo` 返回 repo / README 链接与固定 `run_workdir`；`local_upload` 可在 `source_preview` 返回 `readme_content`
- 空白 `manual` 来源在 `map_to_knowledge_model/confirm` 返回 `400`，错误信息仍为“当前映射结果未通过共享图模型校验，不能进入下一步”
- `source_ingest` 在 `confirm` 后推进到 `source_preview`；`rollback` 后 `source_ingest` 到 `export` 全部恢复为 `pending`
- 浏览器页面 spot-check：本地打开 `/data/pipeline` 与 `/data/pipeline?runId=<id>`，可见固定七步、最近任务列表、当前步骤切到“原始内容预览”、来源类型 `jsonl` 与恢复后的预览内容文本

### 结果证据

- `source_ingest` 预览现在包含 `adapter` 和 `source_summary`
- `source_ingest` 预览现在还能包含 `run_workdir`、`source_dir`、`extracted_dir`、`repo_url`、`readme_url`
- `source_preview` 现在可输出 `readme_content`、`primary_candidate` 与 README / 仓库链接
- `extract` 预览现在包含 `candidates`
- `map_to_knowledge_model` 继续输出 `knowledge_model.HerbNodeModel` 边界与 `validation`
- `human_review` / `export` 现在返回结构化决策与导出计划，不再是通用 summary

## 7. 风险与未覆盖项

- 本轮页面验收是本地浏览器事实检查，不是完整截图回归或 E2E 套件
- 旧 `huggingface` 来源仍为 locator 校验与摘要预览；真正的 repo 下载链路在 `huggingface_repo` 下实现
- `remote_url` 与 `huggingface_repo` 的 live 网络下载本轮由单测桩覆盖与本地构建验证支撑，未做独立手工联网验收
- 文件来源仍是最小预览路径，不代表批量导入链路已在工作台内执行

## 8. 结论

- 结果：`pass`
- 结论一句话：数据处理工作台已经支持结构化来源录入、上传、固定目录物化、README 预览和七步主链路验证，Wave 1 的主目标成立
- 后续动作：后续只需补更高层的 live 远端下载验收、批量导入执行与更完整的页面回归证据
