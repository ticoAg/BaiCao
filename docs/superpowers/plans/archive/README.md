# 已完成实施计划归档

本目录只保存已完成的历史执行计划，供追溯决策、实施证据和毕业去向。新工作不得从这里恢复执行，应以 [`../README.md`](../README.md) 的 active plan 为准。

| 日期 | 文档 | 毕业去向 / 替代关系 |
|------|------|---------------------|
| 2026-08-19 | [fengxi177-tcm-kg-cleaning](2026-08-19-fengxi177-tcm-kg-cleaning.md) | `docs/architecture/data-sources.md`、`docs/acceptance/baicao-knowledge-dataset.md`；本地结构清洗完成，因无许可证保持 `publish: false` |
| 2026-08-19 | [trusted-chat-provenance-closure](2026-08-19-trusted-chat-provenance-closure.md) | `docs/architecture/system-overview.md`、`docs/acceptance/chat-mainline.md`；可信问答与 public HF Viewer 已闭环 |
| 2026-08-16 | [baicao-knowledge-dataset](2026-08-16-baicao-knowledge-dataset.md) | `docs/architecture/knowledge-dataset.md`、`docs/acceptance/baicao-knowledge-dataset.md`；后续数据源由当前 active plan 接管 |
| 2026-04-20 | [chat-deepagents-graph-agent](2026-04-20-chat-deepagents-graph-agent.md) | `docs/acceptance/chat-mainline.md`、`docs/architecture/system-overview.md`；runtime 已由 OpenAI Agents 方案替代 |
| 2026-04-19 | [pharmacopoeia-bulk-ingestion-wave-1](2026-04-19-pharmacopoeia-bulk-ingestion-wave-1.md) | `packages/data_ingestion/` CLI；后续发布收口由当前 active plan 接管 |
| 2026-04-01 | [chinese-graph-relations-breaking](2026-04-01-chinese-graph-relations-breaking.md) | `packages/knowledge_model/` 中文关系真源 |
| 2026-03-31 | [pharmacopoeia-llm-dry-run-wave-1](2026-03-31-pharmacopoeia-llm-dry-run-wave-1.md) | `data_ingestion` dry-run CLI |
| 2026-03-31 | [pharmacopoeia-ingestion-wave-1](2026-03-31-pharmacopoeia-ingestion-wave-1.md) | 药典处理器与共享模型扩展 |
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
