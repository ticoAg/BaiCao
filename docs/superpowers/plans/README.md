# 实施计划索引

仓库级任务真源。执行前先看本页状态，再打开对应 plan。

**规则：** checkbox 是历史拆解。若顶部 `Status` 为 `done`，不要再执行。新工作只走 `active` plan。

## 当前入口

- [2026-08-19-data-source-quality-ingestion.md](2026-08-19-data-source-quality-ingestion.md)：逐个处理现有候选源；当前执行 `CAND-04 TCM-MKG`。

dataset、可信问答与第三数据源结构清洗计划均已完成并归档；后续数据源统一进入当前 active plan，不恢复历史 checkbox。

数据集台账（计划/完成量）：[`../../../datasets/baicao-knowledge/`](../../../datasets/baicao-knowledge/)

## 已完成归档

- [archive/README.md](archive/README.md)：已完成计划、毕业去向与替代关系；只用于回溯，不再执行。

## 明确不在当前主链

- `packages/graph_runtime/`：早期 graph runtime 探索，已被 `packages/api/app/services/chat_agent_runtime/` 取代。不要按旧 graph-agent / graph-runtime plan 继续加功能。
