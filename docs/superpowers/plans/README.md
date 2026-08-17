# 实施计划索引

仓库级任务真源。执行前先看本页状态，再打开对应 plan。

**规则：** 底部 checkbox 是历史拆解。若顶部 `Status` 为 `done`，不要再执行。新工作只走 `active` plan。

## 当前入口

| 状态 | 文档 | 目标 |
|------|------|------|
| **partial** | [2026-08-16-baicao-knowledge-dataset.md](2026-08-16-baicao-knowledge-dataset.md) | CLI 与查询消费已落地；private HF 实际上传待 Infisical 证书修复 |

设计规格：[../specs/2026-08-16-baicao-knowledge-dataset-design.md](../specs/2026-08-16-baicao-knowledge-dataset-design.md)

数据集台账（计划/完成量）：[`../../../datasets/baicao-knowledge/`](../../../datasets/baicao-knowledge/)

## 已完成（保留回溯，不再执行）

| 日期 | 文档 | 毕业去向 |
|------|------|----------|
| 2026-04-20 | [chat-deepagents-graph-agent](2026-04-20-chat-deepagents-graph-agent.md) | `docs/acceptance/chat-mainline.md`、`docs/architecture/system-overview.md` |
| 2026-04-19 | [pharmacopoeia-bulk-ingestion-wave-1](2026-04-19-pharmacopoeia-bulk-ingestion-wave-1.md) | `packages/data_ingestion/` CLI；全量收口并入当前 active plan |
| 2026-04-01 | [chinese-graph-relations-breaking](2026-04-01-chinese-graph-relations-breaking.md) | `packages/knowledge_model/` 中文关系真源 |
| 2026-03-31 | [pharmacopoeia-llm-dry-run-wave-1](2026-03-31-pharmacopoeia-llm-dry-run-wave-1.md) | `data_ingestion` dry-run CLI |
| 2026-03-31 | [pharmacopoeia-ingestion-wave-1](2026-03-31-pharmacopoeia-ingestion-wave-1.md) | 药典处理器 + 共享模型扩展 |
| 2026-03-30 | [pipeline-source-ingestion-wave-1](2026-03-30-pipeline-source-ingestion-wave-1.md) | `/data/pipeline` 结构化来源 |
| 2026-03-29 | [infisical-cli-env-injection](2026-03-29-infisical-cli-env-injection.md) | `scripts/dev_runtime.py` |
| 2026-03-25 | [acceptance-closure-wave-3](2026-03-25-acceptance-closure-wave-3.md) | 六条主链路验收 `pass` |
| 2026-03-25 | [review-export-persistence-wave-2](2026-03-25-review-export-persistence-wave-2.md) | `docs/acceptance/review-export-persistence-wave-2.md` |
| 2026-03-25 | [pipeline-ingestion-closure-wave-1](2026-03-25-pipeline-ingestion-closure-wave-1.md) | 数据处理工作台验收 |
| 2026-03-24 | [backend-uv-ruff-ty-toolchain](2026-03-24-backend-uv-ruff-ty-toolchain.md) | `scripts/test_api.sh` |
| 2026-03-24 | [neomodel-migration](2026-03-24-neomodel-migration.md) | `packages/api/app/kg/db.py` |
| 2026-03-23 | [graph-workbench](2026-03-23-graph-workbench.md) | `docs/architecture/graph-workbench.md` |
| 2026-03-23 | [data-pipeline-workbench](2026-03-23-data-pipeline-workbench.md) | `docs/architecture/data-pipeline-workbench.md` |
| 2026-03-23 | [knowledge-model-and-data-ingestion](2026-03-23-knowledge-model-and-data-ingestion.md) | `docs/architecture/knowledge-model-and-ingestion.md` |
| 2026-03-22 | [local-dev-makefile-runtime](2026-03-22-local-dev-makefile-runtime.md) | 根 `Makefile` |
| 2026-03-21 | [full-phase-completion](2026-03-21-full-phase-completion.md) | 早期主骨架 |
| 2026-03-21 | [writing-plans-task-system-migration](2026-03-21-writing-plans-task-system-migration.md) | 本目录成为任务真源；`IMPL_PLAN.md` / `.task/` 已删除 |

## 明确不在当前主链

- `packages/graph_runtime/`：早期 graph runtime 探索，已被 `packages/api/app/services/chat_agent_runtime/` 取代。不要按旧 graph-agent / graph-runtime plan 继续加功能。
