# 实施计划索引

仓库级任务真源。执行前先看本页状态，再打开对应 plan。

**规则：** checkbox 是历史拆解。若顶部 `Status` 为 `done`，不要再执行。新工作只走 `active` plan。

## 当前入口

- [2026-08-20-remaining-held-extract.md](2026-08-20-remaining-held-extract.md)：剩余已持有原文词表抽取。`Status: done`。古籍全文、ChatMed 全量提及、ZY-BERT 非索引已入本地图。
- [2026-08-20-wangekxy-hf-samples.md](2026-08-20-wangekxy-hf-samples.md)：wangekxy 13 源 roadmap。`Status: done`。
- [2026-08-19-data-source-quality-ingestion.md](2026-08-19-data-source-quality-ingestion.md)：既有候选源审计。`Status: done`，不要再执行其 checkbox。

dataset、可信问答与第三数据源结构清洗计划均已完成并归档；后续数据源统一进入当前 active plan，不恢复历史 checkbox。

新的按日落盘执行计划改走 [`docs/plans/`](../../plans/README.md)。当前一篇：[问答 chat 走最新 MCP 并清适配](../../plans/2026/09-06/问答-chat-走最新-mcp-并清适配-b042.md)。

数据集台账（计划/完成量）：[`../../../datasets/baicao-knowledge/`](../../../datasets/baicao-knowledge/)

## 已完成归档

- [archive/README.md](archive/README.md)：已完成计划、毕业去向与替代关系；只用于回溯，不再执行。

## 明确不在当前主链

- 早期 `packages/graph_runtime/` 已删除。不要按旧 graph-agent / graph-runtime plan 恢复该包或把它接回 chat。
