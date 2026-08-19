# Review Export Persistence Wave 2 Implementation Plan

> **执行模式：** 本轮按 `executing-plans` 在独立 worktree 内联执行，目标是把 Wave 1 的“结构化 review/export 预览”补齐成“review 持久化 + export 显式执行 + MinIO 快照 + Neo4j 真写入”的第二波闭环。

## 目标

- 把 `human_review` 从一次性 preview 升级为独立 review 领域：支持逐项修订、锁定确认、按 `pipeline run` 聚合回读。
- 把 `export` 从纯 `export_plan` 预览升级为显式执行链路：`preview -> confirm -> execute export`。
- 让 JSONL snapshot 先落对象存储，再尝试写 Neo4j；Neo4j 失败时保留 snapshot 作为补写真源。
- 在本地开发环境中补齐 MinIO 编排、配置项与最小验证路径。

## 关键设计决策

- review 真源采用独立领域模型与独立表；pipeline 侧保留摘要和 preview artifact。
- export 真源采用独立 `export_records` 表；不把执行状态直接塞回 `pipeline_runs.steps`。
- JSONL snapshot 放对象存储，数据库只保存 bucket / object key / checksum / size / 状态元数据。
- 导出顺序固定为：`JSONL snapshot -> Neo4j graph write`。
- `confirm export` 只代表允许执行，不自动落库；真实写入必须走显式 `execute export`。

## 实施清单

- [x] Task 1：补 `object_storage` 抽象、内存实现、MinIO backend、API 配置项、`infra/docker-compose.yml`、`infra/.env.example`、`scripts/test_integration.sh`
- [x] Task 2：新增 review 领域模型、持久化模型、服务、schemas 和 `pipeline human_review` 集成
- [x] Task 3：新增 export 领域模型、持久化模型、服务、JSONL snapshot 序列化、Neo4j 写入器、retry graph write
- [x] Task 4：补 `pipeline review/export` 独立 API 路由与依赖装配
- [x] Task 5：补 `packages/shared/types/` 契约与 `packages/web` 最小接线，支持逐项修订和显式执行导出
- [x] Task 6：补 contract / unit 测试、静态检查、页面测试与构建验证
- [x] Task 7：补验收文档与索引

## 实现证据

- `packages/api/app/review/service.py`
- `packages/api/app/export/service.py`
- `packages/api/app/api/pipeline_review.py`
- `packages/api/app/api/pipeline_export.py`
- `packages/api/app/storage/objects/minio.py`
- `packages/api/app/models/review.py`
- `packages/api/app/models/export.py`
- `packages/shared/types/index.ts`
- `packages/web/src/components/pipeline/PipelinePreviewPanel.tsx`
- `packages/web/src/hooks/usePipelineRun.ts`

## 验证结果

已通过：

```bash
cd packages/api && uv run pytest tests/unit/review/test_review_service.py tests/unit/export/test_object_storage.py tests/unit/export/test_export_service.py tests/unit/pipeline/test_service.py tests/api/test_pipeline_routes.py tests/contract/test_pipeline_review_export_contract.py -q
cd packages/api && uv run ruff check app tests
cd packages/api && uv run ty check
cd packages/api && uv run pytest -m "not integration" -q
./scripts/test_integration.sh
pnpm --dir packages/shared typecheck
pnpm --dir packages/web typecheck
pnpm --dir packages/web test --run src/pages/DataPipelinePage.test.tsx
pnpm --dir packages/web exec vp build
docker compose -f infra/docker-compose.yml config
```

结果摘要：

- API 定向回归：`31 passed`
- API 非集成：`229 passed, 3 deselected`
- API 集成：`3 passed, 229 deselected`
- `ruff` / `ty`：通过
- `packages/shared` / `packages/web` typecheck：通过
- `DataPipelinePage` 页面测试：`5 passed`
- `vp build`：通过
- `docker compose config`：通过
- MinIO 镜像固定为 `registry.cn-beijing.aliyuncs.com/ticoag/minio:RELEASE.amd64.2025-04-22T22-12-26Z`
- 集成脚本补了 fresh volumes、容器健康检查和 Neo4j Bolt connectivity wait

## 结论

- 本轮目标已实现：review/export 从 preview-only 升级为真实持久化与显式执行链路。
- 当前验证覆盖了静态检查、非集成、页面定向回归和 live integration，已具备合并条件。
