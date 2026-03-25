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

- 功能名称：数据处理工作台七步预览主链路
- 验收目标：验证 `pipeline` 在固定七步中返回结构化预览，并保留共享模型映射门禁、人工放行与回退主路径
- 对应需求：`docs/superpowers/plans/2026-03-25-pipeline-ingestion-closure-wave-1.md`
- 对应任务：Task 4、Task 5、Task 7
- 当前版本 / 日期：Wave 1 / 2026-03-25

## 2. 验收范围

### 包含

- `source_ingest`、`source_preview`、`normalize`、`extract`、`map_to_knowledge_model`、`human_review`、`export` 七步预览
- `manual`、`jsonl`、`csv`、`huggingface` 四类来源在入口阶段的最小预览分发
- 第 5 步共享模型映射未通过时禁止 `confirm`
- 回退到早期步骤后，后续步骤状态被重置

### 不包含

- 真实 HuggingFace 远端抓取
- 批量文件导入执行
- 前端页面交互细节的重新截图验收

## 3. 前置条件

### 环境

- 工作目录：仓库 worktree 根目录
- 后端依赖：`packages/api`
- 样例数据：`packages/db/import/herbs.csv`、`packages/db/import/herbs.jsonl`
- 共享模型：`packages/knowledge_model/knowledge_model/`

### 最小验证命令

```bash
cd packages/api
uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q
```

## 4. 验收步骤

### Step 1：创建 pipeline run

- 操作：创建一条 `manual` 或文件来源的工作台 run
- 命令 / 页面入口：

```bash
curl -sS -X POST http://localhost:8000/api/v1/pipeline/runs \
  -H 'Content-Type: application/json' \
  -d '{"source_type":"manual","source_locator":"候选实体：陈皮（药材）"}'
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

- 操作：分别以 `manual`、`jsonl`、`csv`、`huggingface` 创建 run，并请求 `source_ingest`
- 期望检查点：
  - `manual` 返回文本摘要
  - `jsonl` / `csv` 返回本地文件预览行
  - `huggingface` 返回 locator 摘要与格式校验结果

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

- 返回 `id`、`source_type`、`source_locator`、`current_step`
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

### Step 4 预期

- 空白来源的映射预览返回 `validation.is_valid = false`
- `confirm` 返回 400，错误信息为“当前映射结果未通过共享图模型校验，不能进入下一步”

### Step 5 预期

- `confirm` 后 `current_step` 前进到下一步
- `rollback` 后目标步骤及其后续步骤状态重置为 `pending`

## 6. 证据记录

### 实现证据

- `packages/api/app/pipeline/service.py:1` — 用步骤注册表替代统一 summary 占位
- `packages/api/app/pipeline/steps/__init__.py:1` — 固定七步 handler 注册入口
- `packages/api/app/pipeline/steps/map_to_knowledge_model.py:1` — 共享模型映射与校验门禁
- `packages/api/app/pipeline/adapters/__init__.py:1` — 来源 adapter 分发入口
- `packages/api/tests/unit/pipeline/test_service.py:1` — 七步预览与 adapter 分发单测
- `packages/api/tests/api/test_pipeline_routes.py:1` — route 层多步预览与 map 门禁验证

### 运行证据

```bash
cd packages/api
uv run ruff check app/pipeline tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py
uv run pytest tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py -q
```

- 当前结果：`ruff` 通过；`pytest` 结果为 `24 passed in 0.97s`

### 结果证据

- `source_ingest` 预览现在包含 `adapter` 和 `source_summary`
- `extract` 预览现在包含 `candidates`
- `map_to_knowledge_model` 继续输出 `knowledge_model.HerbNodeModel` 边界与 `validation`
- `human_review` / `export` 现在返回结构化决策与导出计划，不再是通用 summary

## 7. 风险与未覆盖项

- 本文档对应的本轮 fresh 证据来自 API / unit 测试；页面级交互表现未在本 wave 重新做浏览器验收
- `huggingface` 仍为 locator 校验与摘要预览，不代表远端数据抓取已接入
- 文件来源仍是最小预览路径，不代表批量导入链路已在工作台内执行

## 8. 结论

- 结果：`risk`
- 结论一句话：数据处理工作台后端七步预览主链路已具备可复现证据，页面级人工验收仍需在集成阶段补一轮
- 后续动作：由主代理在合并后补目录索引与跨模块统一验收结论
