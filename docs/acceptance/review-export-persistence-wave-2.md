<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "pipeline", "review", "export", "minio", "neo4j"]
summary: 数据处理工作台第二波主链路验收：人工确认持久化与显式导出执行
audience: developer
---
-->

# 数据工作台人工确认与显式导出验收

## 1. 概述

- 功能名称：数据处理工作台第二波主链路
- 验收目标：验证 `human_review` 已升级为可持久化的逐项修订流程，`export` 已升级为显式执行链路，并在导出时先写 JSONL snapshot 再写 Neo4j
- 对应需求：`docs/superpowers/plans/2026-03-25-review-export-persistence-wave-2.md`
- 当前版本 / 日期：Wave 2 / 2026-03-25

## 2. 验收范围

### 包含

- review session 创建、读取、逐项修订、锁定确认
- `human_review` 步骤确认前必须完成 review session 锁定
- `export` 的 `preview -> confirm -> execute export` 显式执行语义
- JSONL snapshot 元数据记录到 `export_records`
- Neo4j 写入失败时保留 snapshot，并支持后续 retry graph write
- MinIO 本地开发配置与对象存储抽象

### 不包含

- 浏览器级 E2E 截图或录像
- 真实远端对象存储服务凭证验证
- 多 bucket 策略、生命周期管理、预签名 URL

## 3. 前置条件

### 环境

- 工作目录：仓库根目录
- 后端依赖：`packages/api`
- 前端依赖：`packages/web`
- 共享类型：`packages/shared/types/index.ts`

### 最小验证命令

```bash
cd packages/api
uv run pytest tests/unit/review/test_review_service.py tests/unit/export/test_object_storage.py tests/unit/export/test_export_service.py tests/contract/test_pipeline_review_export_contract.py -q
```

## 4. 验收步骤

### Step 1：创建 review session

- 操作：创建 `manual` pipeline run，请求 `map_to_knowledge_model/preview`，然后创建 review session
- 期望检查点：
  - review session 返回 `id`、`run_id`、`status`
  - `items[]` 中每一条都有 `item_key`、`original_payload`、`revised_payload`

### Step 2：逐项修订并锁定人工确认

- 操作：更新某条 review item 的 `decision` 和 `revised_payload`，再调用 review confirm
- 期望检查点：
  - review item 决策不再停留在 `pending`
  - review session 状态切到 `confirmed`
  - 未锁定 review session 时，`POST /steps/human_review/confirm` 会被拒绝

### Step 3：生成 export plan 并确认 export step

- 操作：请求 `POST /pipeline/runs/{run_id}/export-plan`，再请求 `POST /steps/export/confirm`
- 期望检查点：
  - export plan 使用 review 后的最终 payload，而不是 map preview 原始结果
  - confirm export 只改变 pipeline step 状态，不自动产生导出记录

### Step 4：显式执行 export

- 操作：请求 `POST /pipeline/runs/{run_id}/export-executions`
- 期望检查点：
  - 返回独立 `export record`
  - record 中包含 `snapshot_bucket` / `snapshot_object_key` / `snapshot_checksum`
  - graph write 成功时 `status=completed`
  - graph write 失败时 `status=partial_failed`

### Step 5：读取导出执行结果

- 操作：请求 `GET /pipeline/runs/{run_id}/export-executions/latest`
- 期望检查点：
  - 能读到最近一次 export record
  - 显式执行前，该接口应返回 404

## 5. 期望结果

- review 与 export 都拥有独立领域真源，而不是只留在 `pipeline preview_payload`
- `human_review` 与 `export` 的 pipeline preview 继续存在，但已经以 review/export 领域状态为准
- JSONL snapshot 先落对象存储，再尝试 Neo4j；即使图谱写入失败，也能保留补写真源
- 前端工作台可读取 review session、保存逐项修订、锁定人工确认，并显式执行导出

## 6. 证据记录

### 实现证据

- `packages/api/app/review/service.py:1` — review session 的创建、逐项修订、锁定确认与 preview 集成
- `packages/api/app/export/service.py:1` — export plan、JSONL snapshot、Neo4j 写入与 retry graph write
- `packages/api/app/api/pipeline_review.py:1` — review 领域 API
- `packages/api/app/api/pipeline_export.py:1` — export 领域 API
- `packages/api/app/storage/objects/minio.py:1` — MinIO backend
- `packages/api/app/models/review.py:1` — `review_sessions` / `review_items` 表
- `packages/api/app/models/export.py:1` — `export_records` 表
- `packages/shared/types/index.ts:1` — review/export 跨端契约
- `packages/web/src/hooks/usePipelineRun.ts:1` — 页面侧 review/export 行为接线
- `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx:1` — review item 编辑与导出结果展示

### 运行证据

```bash
cd packages/api
uv run pytest tests/unit/review/test_review_service.py tests/unit/export/test_object_storage.py tests/unit/export/test_export_service.py tests/contract/test_pipeline_review_export_contract.py -q
uv run ruff check app tests
uv run ty check
uv run pytest -m "not integration" -q
pnpm --dir packages/shared typecheck
pnpm --dir packages/web typecheck
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web exec vp build
docker compose -f infra/docker-compose.yml config
```

- 当前结果：
  - 定向 API 测试：`31 passed`
  - API 非集成：`229 passed, 3 deselected`
  - `ruff` / `ty`：通过
- `packages/shared` / `packages/web` typecheck：通过
  - `DataPipelinePage`：`5 passed`
  - `vp build`：通过
  - `docker compose config`：通过
  - `./scripts/test_integration.sh`：`3 passed, 229 deselected`

### 结果证据

- contract 测试证明：
  - review item 可以逐项 `edit`
  - 未执行 `export-executions` 前，latest export 仍为 404
  - 显式执行后，latest export 带回 `snapshot_object_key`
- unit 测试证明：
  - graph write 失败时，snapshot 仍然先写入对象存储
  - retry graph write 会复用已有 snapshot，而不是重建 payload

## 7. 风险与未覆盖项

- 前端本轮只补最小工作台接线，没有补独立 E2E
- `scripts/test_integration.sh` 为了保证 schema 与对象存储环境稳定，当前采用了 fresh volumes + health wait + Neo4j connectivity wait；更适合集成验证，不适合作为轻量日常脚本

## 8. 结论

- 结果：`pass`
- 结论一句话：review/export 第二波主链路的代码、契约、页面接线与 live MinIO/Neo4j 集成验证均已完成，具备可复现交付证据
