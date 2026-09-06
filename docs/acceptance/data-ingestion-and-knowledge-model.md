<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "knowledge-model", "data-ingestion", "import-export"]
summary: 共享知识模型到 API、导入导出与数据采集边界的主线验收
audience: developer
---
-->

# 共享知识模型与数据采集主链路验收

## 1. 概述

- 功能名称：共享图模型 / 导入记录 / 数据采集边界闭环
- 验收目标：验证 `packages/knowledge_model/` 已成为 API 图谱 schema、导入导出记录以及 `packages/data_ingestion/` 的共享真源
- 对应需求：让共享知识模型消费者迁移形成最小可验证闭环
- 对应计划：[../superpowers/plans/archive/2026-03-25-pipeline-ingestion-closure-wave-1.md](../superpowers/plans/archive/2026-03-25-pipeline-ingestion-closure-wave-1.md)
- 当前版本 / 日期：shared-model-ingestion-closure / 2026-03-25

## 2. 验收范围

### 包含

- API graph schema 直接复用共享 `NodeType` / `NodeStatus`
- API `EdgeType` 保持 superset，同时用 contract test 锁住共享子集
- importer / exporter 统一消费共享导入记录 `GraphImportRecord`
- `app.importers` 继续兼容导出 `GraphRecord` / `EdgeRecord`
- `packages/data_ingestion/` 直接消费共享图模型，而不是重新定义图谱枚举

### 不包含

- pipeline 七步预览链路
- `docs/acceptance/README.md` 索引更新
- 全量 API / web / integration 验证
- 非共享子集的 API-only edge 语义调整

## 3. 前置条件

### 环境

- 仓库 worktree：`/Users/ticoag/Documents/myws/BaiCao/.worktrees/shared-model-ingestion-closure`
- Python：`>=3.12`
- 依赖：`packages/api/` 与 `packages/data_ingestion/` 可通过 `uv` 解析本地 `packages/knowledge_model/`

### 启动命令

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q

cd ../data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

## 4. 验收步骤

### Step 1

- 操作：验证 API graph schema 使用共享图模型枚举
- 命令：

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/unit/kg/test_models.py -q
```

### Step 2

- 操作：验证 importer / exporter 统一消费共享导入记录，并保持兼容导出
- 命令：

```bash
cd packages/api
uv run pytest tests/contract/test_import_record_contract.py -q
```

### Step 3

- 操作：验证数据采集边界直接消费共享图模型
- 命令：

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

## 5. 期望结果

### Step 1 预期

- `HerbNode.type` 字段注解直接指向共享 `NodeType`
- `BaseNode.status` 字段注解直接指向共享 `NodeStatus`
- API `EdgeType` 仍保留 `PARENT_OF` / `CHILD_OF`
- 共享图模型中的 edge 子集全部存在于 API `EdgeType`

### Step 2 预期

- `JSONLImporter` 返回共享 `GraphImportRecord`
- `JSONLExporter` 能直接导出共享导入记录
- `app.importers.GraphRecord` / `app.importers.EdgeRecord` 继续可用，并与共享类型保持同一对象

### Step 3 预期

- `ExtractionCandidate.node_type` 直接使用共享 `NodeType`
- 数据采集边界只定义来源适配 / 抽取候选模型，不复制图谱节点与边模型

## 6. 证据记录

### 实现证据

- `packages/knowledge_model/knowledge_model/constants.py`
- `packages/knowledge_model/knowledge_model/import_records.py`
- `packages/api/app/models/enums.py`
- `packages/api/app/schemas/graph.py`
- `packages/api/app/importers/base.py`
- `packages/api/app/importers/__init__.py`
- `packages/api/app/importers/jsonl_importer.py`
- `packages/api/app/importers/csv_importer.py`
- `packages/api/app/exporters/base.py`
- `packages/api/app/exporters/jsonl_exporter.py`
- `packages/api/app/exporters/csv_exporter.py`
- `packages/data_ingestion/data_ingestion/models.py`

### 运行证据

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q
uv run pytest tests/contract/test_import_record_contract.py tests/api/test_graph_routes.py -q

cd ../data_ingestion
uv run --with pytest pytest tests/test_models.py -q
```

执行日期：`2026-03-25`

```bash
cd packages/api
uv run pytest tests/contract/test_graph_shared_model_contract.py \
  tests/contract/test_import_record_contract.py \
  tests/api/test_graph_routes.py \
  tests/unit/kg/test_models.py -q

cd ../knowledge_model
uv run --with pytest pytest tests -q
```

- 当前结果：API contract + route + unit 聚焦验证 `21 passed`；共享模型包测试 `8 passed`；`data_ingestion` 测试 `1 passed`

```bash
cd packages/api
uv run python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from app.importers.jsonl_importer import JSONLImporter
from app.exporters.jsonl_exporter import JSONLExporter
from knowledge_model.import_records import GraphImportRecord

source = Path("../db/import/herbs.jsonl")
records = list(JSONLImporter().load(str(source)))
print(type(records[0]).__name__, records[0].node_name, records[0].node_type)
with TemporaryDirectory() as tmpdir:
    output = Path(tmpdir) / "roundtrip.jsonl"
    JSONLExporter().export(records[:2], str(output))
    first = GraphImportRecord.model_validate_json(output.read_text(encoding="utf-8").splitlines()[0])
    print(type(first).__name__, first.node_name, len(first.edges))
PY
```

- 当前结果：样例 `packages/db/import/herbs.jsonl` 导入后直接得到 `GraphImportRecord`；导出到临时 JSONL 后可再次由共享 `GraphImportRecord` 成功回读

```bash
cd packages/data_ingestion
uv run python - <<'PY'
from data_ingestion.models import ExtractionCandidate
from knowledge_model.constants import NodeType

candidate = ExtractionCandidate(node_type=NodeType.HERB, node_name="陈皮", source_name="demo")
print(candidate.node_type is NodeType.HERB, candidate.node_type)
PY
```

- 当前结果：`ExtractionCandidate` 在真实运行中直接消费共享 `NodeType.HERB`

```bash
curl -sS http://127.0.0.1:8000/api/v1/graph/meta/schema
```

- 当前结果：API graph 元信息接口在本地集成环境可正常返回 schema 摘要，证明共享图模型迁移后的 graph 主路径仍可工作

### 结果证据

- `tests/contract/test_graph_shared_model_contract.py` 通过，锁住共享图模型枚举绑定与 edge 子集
- `tests/unit/kg/test_models.py` 通过，锁住 API-only `PARENT_OF` / `CHILD_OF` 未被删除
- `tests/contract/test_import_record_contract.py` 通过，锁住共享导入记录与 importer `__init__` 兼容导出
- `packages/data_ingestion/tests/test_models.py` 通过，证明数据采集边界直接复用共享图模型

## 7. 风险与未覆盖项

- 当前 importer / exporter 的手工 round-trip 主要覆盖 JSONL 主路径；CSV 仍依赖同一共享导入记录抽象，但未在本文单独展开样例
- 本轮没有补真实 Neo4j 导入执行，也没有补浏览器端人工验收；这条验收聚焦的是共享结构真源与消费者边界
- API `EdgeType` 仍保留 superset 策略；shared 与 API-only edge 的完全收敛不在本轮范围

## 8. 结论

- 结果：`pass`
- 结论一句话：共享知识模型已经成为 API schema、导入导出与数据采集边界的单一事实来源，并已补齐样例 round-trip 与本地集成环境复核
- 后续动作：后续只需在真实导入执行与更广覆盖的 CSV / integration 层补更多样例证据

## 9. 2026-03-31 药典条目图谱化补充证据

### 本轮新增范围

- 共享图模型新增 `饮片`、`证据` 节点及 `具有饮片`、`由证据支持` 关系
- `packages/data_ingestion/` 新增文件级路由、条目块协议、统一 bundle 输出
- `2022年中药药典.txt` 新增专属切段、章节解析、条目映射逻辑
- API pipeline 新增 `processor_runtime`，能把药典条目映射结果接入 `MAP_TO_KNOWLEDGE_MODEL` 预览

## 10. 2026-04-19 药典大批量导入与重置补充证据

### 本轮新增范围

- `packages/data_ingestion/` 新增通用异步批量执行器
- 药典 ingest 支持真实 LLM 大批量执行、失败条目筛选重跑、`GraphImportRecord` 快照落盘
- `packages/api/` 的导入 CLI 支持把 JSONL 快照真实写入 Neo4j
- 新增数据集级重置能力，支持按 scope 清理新版导入关系，也支持按历史快照精确清理旧关系

### 运行证据

```bash
cd packages/data_ingestion
uv run --with pytest pytest \
  tests/test_async_batch.py \
  tests/test_record_snapshots.py \
  tests/test_pharmacopoeia_ingestion.py \
  tests/test_pharmacopoeia_dry_run.py \
  tests/test_pharmacopoeia_llm_extraction.py \
  tests/test_pharmacopoeia_mapping.py -q
```

- 当前结果：相关数据采集测试通过

```bash
cd packages/api
uv run --extra dev pytest \
  tests/unit/importers/test_neo4j_import.py \
  tests/unit/importers/test_dataset_reset.py \
  tests/unit/export/test_neo4j_graph_writer.py \
  tests/contract/test_import_record_contract.py -q
```

- 当前结果：导入、重置、Neo4j 关系 scope 与导入记录契约测试通过

### 真实运行证据

- Infisical 注入确认：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`NEO4J_URI`、`NEO4J_USER`、`NEO4J_PASSWORD` 均已注入
- `2022年中药药典.txt` 切分条目数：`605`
- 第一次真实全量尝试：
  - `entries_attempted=605`
  - `entries_succeeded=287`
  - `entries_failed=318`
  - 主要失败原因：上游 `429 rate limit`
  - `records_generated=3225`
- 切换新版 provider 后的失败重跑：
  - `10` 条窗口：`10 / 10` 成功
  - `50` 条窗口：`50 / 50` 成功
  - `100` 条窗口 A：`99 / 100` 成功
  - `100` 条窗口 B：`97 / 100` 成功
  - `62` 条最终窗口：`62 / 62` 成功
  - 总计重跑成功：`318 / 318`
- 当前完成状态：
  - 全文件 `605 / 605` 条目已成功完成结构化抽取与映射
  - 重跑阶段残留的 `4` 次失败已在后续窗口中全部清空
- 累计导入快照：
  - 首次成功批次：`3225` 记录
  - 重跑 `10` 条样本：`159` 记录
  - 重跑 `50` 条窗口：`726` 记录
  - 重跑 `100` 条窗口 A：`1346` 记录
  - 重跑 `100` 条窗口 B：`1320` 记录
  - 重跑最终 `62` 条窗口：`867` 记录
- 当前图内按数据集属性统计：
  - `Herb=309`
  - `PreparedHerb=250`
  - `Evidence=314`
  - `Disease=860`
  - `Efficacy=409`
  - `Meridian=11`
  - `Flavor=11`

### 风险与未覆盖项

- 初版 provider `openrouter/elephant-alpha` 在运行时触发上游限流，已通过切换 provider 完成剩余失败条目回填
- 新 provider `https://ark.cn-beijing.volces.com/api/v3` 需要保持原始版本路径，且不支持 `enable_thinking` 扩展字段；当前代码已兼容自动降级
- 历史已导入但不带 `import_scope_key` 的关系，需要通过 `--snapshot-jsonl` 做一次精确清理

### 对应实现

- `packages/knowledge_model/knowledge_model/constants.py`
- `packages/knowledge_model/knowledge_model/node_models.py`
- `packages/knowledge_model/knowledge_model/import_records.py`
- `packages/data_ingestion/data_ingestion/source_models.py`
- `packages/data_ingestion/data_ingestion/routing.py`
- `packages/data_ingestion/data_ingestion/bundles.py`
- `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/segmentation.py`
- `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/parsing.py`
- `packages/data_ingestion/data_ingestion/processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/mapping.py`
- `packages/api/app/pipeline/processor_runtime.py`
- `packages/api/app/pipeline/service.py`
- `packages/api/app/pipeline/steps/map_to_knowledge_model.py`

### 补充验证命令

```bash
cd packages/knowledge_model
uv run --with pytest pytest tests/test_constants.py tests/test_schema.py -q

cd ../data_ingestion
uv run --with pytest pytest tests -q

cd ../api
uv run --extra dev pytest tests/unit/pipeline/test_processor_runtime.py tests/unit/pipeline/test_service.py tests/contract/test_import_record_contract.py -q
```

### 预期闭环

- `一枝黄花` 这类药典条目能被切成单个 `证据` 节点
- `饮片` 以独立节点形式进入 bundle，而不是作为 `药材` 附属字段
- `MAP_TO_KNOWLEDGE_MODEL` 预览可返回 `药材 / 饮片 / 证据 / 性味 / 归经 / 功效` 及中文关系

## 11. 2026-04-20 Graph Runtime / Agent Wave 1 补充证据

> 历史证据。`packages/graph_runtime/` 已于 2026-09-06 从仓库删除；当前问答走 `chat_agent_runtime` + Knowledge MCP，不要再跑本节命令。

### 本轮新增范围

- 新增 `packages/graph_runtime/`，提供 contracts、backend 协议、facade、traversal primitives、schema-aware planner、默认 graph exploration agent 与 CLI 薄壳
- `packages/api/` 新增 runtime backend adapter、`GraphAgentService` 与 `/api/v1/graph-agent/ask` 最小 HTTP 入口
- API adapter 负责把既有 `graph_service.search_nodes()` 的嵌套结果归一化为 runtime 可消费的扁平节点
- CLI 保持 terminal tool 薄壳定位，只提供渐进式发现、help 与友好错误提示

### 运行证据

```bash
cd packages/graph_runtime
uv run --with pytest pytest tests -q

cd ../api
uv run --extra dev pytest tests/services/test_graph_agent_service.py tests/api/test_graph_agent_routes.py -q
```

- 当前结果：graph runtime 包内 contracts / service / primitives / planner / agent / CLI 测试通过；API service 与 route 接线测试通过

### 对应实现

- `packages/graph_runtime/graph_runtime/contracts/inputs.py`
- `packages/graph_runtime/graph_runtime/contracts/outputs.py`
- `packages/graph_runtime/graph_runtime/service/graph_facade.py`
- `packages/graph_runtime/graph_runtime/primitives/bfs.py`
- `packages/graph_runtime/graph_runtime/primitives/dfs.py`
- `packages/graph_runtime/graph_runtime/planner/plan_builder.py`
- `packages/graph_runtime/graph_runtime/agent/graph_agent.py`
- `packages/graph_runtime/graph_runtime/cli/main.py`
- `packages/api/app/graph_runtime_backend.py`
- `packages/api/app/services/graph_agent_service.py`
- `packages/api/app/api/graph_agent.py`
- `packages/api/app/main.py`

### 风险与未覆盖项

- 本轮只覆盖 runtime 与 API 接线的最小主路径，未执行真实 Neo4j 数据库上的端到端 graph agent 问答
- 默认 agent 目前采用规则化 schema-aware planning 与图谱邻接探索，LLM synthesis / LangChain adapter 不在本轮范围
- 只读 Cypher fallback 已在 runtime facade 中保留校验入口，但默认 agent 尚未主动触发 fallback

## 12. 2026-08-19 ShenNong TCM-KG 保守清洗补充证据

### 本轮范围

- 严格解析 `head<TAB>tail<TAB>relation`，未知关系、坏列和空字段直接失败
- 排除化学关系，隔离跨语言映射和功能/临床类型冲突
- 临床 head 保留为未分类 `病证`，来源标注证候只记录来源类型
- `中药`、`治法`、`证候` 映射为中性 `关联药材`、`关联治法`、`关联证候`，不提升为治疗、诊断或因果关系
- importer 以 100 条为一个 managed transaction，并用已解析名称连接同批次目标，避免逐记录事务和动态目标扫描

### 结构与隔离结果

- 输入：123,358 行
- 输出：19,066 节点记录、52,247 条物化关系
- 节点：药材 947、功效 846、性味 22、归经 12、病证 15,965、治法 1,274
- 关系：具有功效 2,180、具有性味 2,231、归于经脉 1,954、关联证候 35,444、关联药材 7,832、关联治法 2,606
- 隔离：化学关系 67,481、`TS_MS` 245、功能/临床冲突 337、证候自环 9
- 来源类型：来源标注证候 3,278、未分类临床概念 12,687

### 隔离 Neo4j smoke

使用无持久卷 `neo4j:5-community` 临时容器，端口 `30687`，未连接或修改现有图库。导入结果：

```text
created=19066
edges=52247
nodes=19066
relationships=52247
```

Cypher 语义校验：

- `关联证候=35,444`，非 `病证` source/target 均为 0
- `关联药材=7,832`，非 `病证` source、非 `药材` target 均为 0
- `关联治法=2,606`，非 `病证` source、非 `治法` target 均为 0
- `病证.中医类型=来源标注证候` 为 3,278
- `治疗病证=0`
- 药材/病证跨类型同名合并为 0
- 关系 scope 缺失或错误为 0

验证后已停止临时容器；容器带 `--rm`，未保留临时图数据。

### 回归证据

```text
data_ingestion: 97 passed, 1 skipped
knowledge_model: 27 passed
API graph contract/routes: 16 passed
shared typecheck: passed
web production build: passed
changed-file Ruff: passed
```

### 结论与边界

- 结果：结构清洗与隔离入图 `pass`，内容状态继续为 `pending`
- 两个上游缺少再发布许可证，且 ShenNong README 限定仅供学术研究并禁止商业用途；固定 `publish:false`
- 疾病、症状和证候仍不得按名称后缀、编辑距离、跨语言候选或 LLM 推断自动拆分或合并

## 13. 2026-08-19 tcm-db 只读清洗补充证据

### 本轮范围

- 使用标准库 `sqlite3`，以 `mode=ro` 打开并设置 `PRAGMA query_only=ON`
- 严格校验并只消费药材、方剂、症状、证候、治法 5 个实体表和 3 个显式关系表
- 新增共享 `症状` 节点与 `关联症状` 边；关系方向固定为方剂到药材、方剂到病证、病证到症状
- 长文本字段只作属性，不从 `indication`、`composition`、代表方或 `related_*` 推导临床边
- 同类型仅按规范名精确且非空属性无冲突时聚合；跨类型同名不合并

### 结构与隔离结果

- 输入：1,746 个主域实体行、655 条显式关系
- 输出：1,715 节点记录、654 条关系
- 节点：药材 470、方剂 205、病证 194、症状 727、治法 119
- 关系：组成药材 196、关联证候 19、关联症状 439
- 隔离：29 个异常方剂行（32 warnings）、2 条冲突白芷、1 条 `乳癌 -> 乳癌` 同名跨类型边
- `乳癌`、`肾衰竭`、`胰脏癌` 的症状/证候节点分别保留，没有跨类型实体合并

### 隔离 Neo4j smoke

使用无持久卷 `neo4j:5-community` 临时容器，端口 `30687`，未连接或修改现有图库。导入结果：

```text
created=1715
edges=654
nodes=1715
relationships=654
```

Cypher 语义校验：

- `组成药材=196`、`关联证候=19`、`关联症状=439`
- 三类关系 source/target 类型错误均为 0
- 症状/病证跨类型同名节点对为 3，同名 `关联症状` 为 0
- `治疗病证=0`
- 缺失关系 `证据定位=0`
- 节点/边 scope 缺失或错误均为 0
- “白芷”药材节点为 0
- 核心属性落图：药材 `药性` 340、方剂 `组成原文` 66、症状 `分类` 695

验证后已停止临时容器；容器带 `--rm`，未保留临时图数据。

### 回归证据

```text
data_ingestion: 103 passed, 1 skipped
knowledge_model: 28 passed
API graph contract/routes/kg: 19 passed
shared typecheck: passed
web production build: passed
changed-file Ruff: passed
```

### 结论与边界

- 结果：结构清洗、实体消歧和隔离入图 `pass`；内容继续为 `pending`
- 混合数据库只有一个上游核实为 MulanPSL-2.0，其余来源缺少明确再发布许可；固定 `publish:false`
- 方剂组成关系没有剂量，角色全为“未知”；不补造剂量或君臣佐使
- 医学语义仍需专家抽样，当前只证明结构、方向、隔离和溯源门禁成立

## 14. 2026-08-19 DragonTCM 保守清洗补充证据

### 本轮范围

- 严格校验 herbs、formulas、conditions、relations 四个 Parquet 的 schema 和嵌套 JSON 类型
- 仅将来源标记为 SNOMED `disorder` 的 condition 映射为病证；其他语义类型显式隔离
- 同类型只合并确定性表面重复；中文 alias、跨语言候选和跨类型同名不参与自动合并
- `contains` 映射为组成药材；condition-herb `treats` 降级为中性关联药材；condition-formula `treats` 隔离
- disorder 的 clinical manifestations 投影为关联症状，并保留原始嵌套 JSON、pattern 和逐项证据定位

### 结构与隔离结果

- 输入：4,743 个实体行、28,735 条显式关系
- 输出：11,598 节点记录、46,666 条关系
- 节点：药材 1,027、方剂 2,574、病证 803、症状/临床表现 7,194
- 关系：组成药材 14,608、关联药材 2,197、关联症状 29,861
- condition 隔离：316 行；关系隔离：被隔离端点 5,576、condition-to-formula 6,354
- manifestation 隔离：截断 45、空 2、缺失 list 3、非 list 1；重复病证/症状边折叠 7,281
- 同名门禁：药材 17 组和方剂 6 组无冲突表面重复合并；1 组药材属性冲突、20 组 herb/formula 跨类型同名保持独立

### 隔离 Neo4j smoke

使用无持久卷 `neo4j:5-community` 临时容器，未连接或修改现有图库。导入结果：

```text
created=11598
edges=46666
nodes=11598
relationships=46666
```

Cypher 语义校验：

- `组成药材=14,608`、`关联药材=2,197`、`关联症状=29,861`
- 三类关系 source/target 类型错误均为 0
- 关系缺失 `证据定位=0`
- 节点/边 scope 缺失或错误均为 0
- 同标签同名重复为 0，非 `pending` 状态为 0
- SNOMED 病证节点 227，herb/formula 跨类型同名 20 组
- `FUSHI` / `FU SHI` 保持两个独立药材节点
- `治疗病证`、`使用方剂`、`关联证候` 均为 0

验证后临时容器已停止并自动删除。

### 回归证据

```text
data_ingestion: 108 passed
knowledge_model: 28 passed
API non-integration: 293 passed, 4 deselected
importer dry-run: 11598 records / 46666 edges
changed-file Ruff: passed
changed-file ty: passed
```

### 结论与边界

- 结果：结构清洗、实体消歧和隔离入图 `pass`；全部医学内容继续为 `pending`
- clinical manifestations 可能同时包含症状与体征，当前只表达来源中性关联，不是因果、诊断标准或已验证分类
- Dataset Card 为 `CC-BY-NC-4.0`，且 American Dragon、书籍和 SNOMED CT 的完整上游权利链未闭合；固定 `publish:false`

## 15. 2026-08-19 TCM-MKG 主域子图保守清洗补充证据

### 本轮范围

- 使用标准 CSV TSV 解析器消费 D1-D7 与 D18，支持 quoted multiline，并严格校验 schema、稳定 ID 和跨表端点
- 只映射方剂、饮片、病证、治法、性味、归经；化学、靶点、跨本体映射、SD1 预测关系和未持有的完整边文件全部排除
- D3 传统医学疾病和 D5 indication 降级为中性 `适用于`，传统医学证候映射 `关联证候`；不生成 `治疗病证`
- 同类型规范中文名精确且属性无冲突时才聚合；跨类型同名、拼音、英文、alias、编辑距离和 LLM 判断不参与合并

### 结构与隔离结果

- 输入：D1-D7/D18 共 213,655 个逻辑记录
- 输出：19,519 节点记录、177,672 条关系
- 节点：方剂 8,977、饮片 6,207、病证 3,963、治法 349、性味 11、归经 12
- 关系：`适用于=73,514`、`关联证候=2,032`、`采用治法=4,525`、`组成药材=74,084`、`具有性味=15,225`、`归于经脉=8,292`
- 隔离：D5 chapter 21 症状 13、chapter 22 损伤 421；D1/D3 病因、病机不进入当前契约
- 合并门禁：10 个 TCMT/ICD-11 精确同名病证合并并保留双 ID；13 组方剂/饮片同名保持独立
- 结构修复：D6 `CHP01717 黄芪` 一行固定错位模式修复；其他额外列仍失败

### 隔离 Neo4j smoke

使用无持久卷 `neo4j:5-community` 临时容器，未连接或修改现有图库。导入结果：

```text
created=19519
edges=177672
nodes=19519
relationships=177672
```

Cypher 语义校验：

- 六类关系 source/target 类型错误均为 0
- `治疗病证=0`，缺失关系 `证据定位=0`
- 节点/边 scope 错误均为 0，非 `待验证` 节点为 0
- 稳定 ID：方剂 CPM 8,977、饮片 CHP 6,207、病证 TCMT 1,248、病证 ICD-11 2,725、治法 TCMT 349
- 双 ID 病证 10；方剂/饮片跨类型同名 13 组
- `CHP01717 黄芪` 落图为拼音 `huang qi`、分类 `Viridiplantae`

验证后临时容器已停止并自动删除。

### 回归证据

```text
data_ingestion: 108 passed, 2 skipped
knowledge_model: 28 passed
API non-integration: 293 passed, 4 deselected
importer dry-run: 19519 records / 19519 graph_records
changed-file Ruff: passed
changed-file ty: passed
```

### 结论与边界

- 结果：结构清洗、实体消歧、关系降级和隔离入图 `pass`；全部医学内容继续为 `pending`
- `适用于` 只表达上游结构化 indication/疾病关联，不是已验证疗效、治疗建议或因果关系
- 精确同名双 ID 合并只减少当前导入范围内的重复节点，不声明 TCMT 与 ICD-11 一般等价
- Zenodo、WHO 术语、ICD-11 和其他聚合上游条款不能支持当前 public 派生发布；固定 `publish:false`

## 16. 2026-08-19 TCM-SD / ZY-BERT 证候术语保守清洗补充证据

### 本轮范围

- 只读消费 `tmp/qibo-datasets/TCM-SD/` 的词表与 train/dev/test JSONL
- 只提升 148 个 `norm_syndrome` 词表项为 `病证` / `来源标注证候`
- 病例原文、病名节点、病-证共现、知识库定义和 `医案` 节点全部隔离
- 不生成 `关联证候` 或 `治疗病证`

### 结构与隔离结果

- 输入：标注 54,152 行，与论文一致
- 输出：148 节点记录、0 条关系
- 隔离：临床文本 59,638 行、病名 451、病-证共现 2,023、知识库 1,027
- 隐私：住院号 77、手机号 1、医院名 11,626
- 泄漏：user_id 跨 split 50，全文跨 split 626
- 跨类型同名：`风寒湿痹证` 只保留证候节点

### 隔离 Neo4j smoke

使用无持久卷 `neo4j:5-community` 临时容器，未连接或修改现有图库。导入结果：

```text
created=148
nodes=148
relationships=0
```

Cypher 语义校验：

- 节点全部为 `病证`，`中医类型=来源标注证候` 148
- `治疗病证=0`，`关联证候=0`
- 节点 scope 错误为 0，非 `待验证` 节点为 0

验证后临时容器已停止并删除。

### 回归证据

```text
data_ingestion: 113 passed, 2 skipped
knowledge_model: 28 passed
API non-integration: 294 passed
importer dry-run: 148 records / 148 graph_records
changed-file Ruff: passed
changed-file ty: passed
```

### 结论与边界

- 结果：结构清洗、隐私门禁、关系不提升和隔离入图 `pass`；全部医学内容继续为 `pending`
- 三路 Grok 审查均超时，未计作有效结论；最终验收以本地测试和隔离图库为准
- 病例标签不是疾病定义上的证候知识
- 数据集 `CC-BY-NC-SA-4.0` 且残留病历标识，固定 `publish:false`

## 17. 2026-08-19 TCM-NER / DeepNER 抽取评测审计补充证据

### 本轮范围

- 只读消费 `tmp/qibo-datasets/TCM-NER/DeepNER-raw/` 的 train/dev JSON
- 确认 stack 为 train∪dev、test 无标签、13 类跨度与原文对齐
- 不把 NER 跨度或说明书共现提升为图节点/边

### 结构与隔离结果

- 输入：标注 1,000 篇、17,757 条跨度；无标签测试 500 篇
- 输出：0 节点记录、0 条关系
- 隔离：stack 1,000、跨类型同名表面 260、药厂/公司名 904 篇
- 许可：DeepNER 无许可证，官方包未持有

### 隔离 Neo4j smoke

无图记录，未启动临时容器。空 `records.jsonl` 不跑 importer dry-run。

### 回归证据

```text
data_ingestion: 119 passed, 2 skipped
knowledge_model: 28 passed
changed-file Ruff: passed
changed-file ty: passed
cleaner CLI: 0 records / 0 edges, publish=false
```

### 结论与边界

- 结果：结构审计和隔离入图门禁 `pass`；该源不得作为图谱真源
- 本轮未发起 Grok 审查；最终验收以本地测试和统计为准
- 固定 `publish:false`

## 18. 2026-08-19 TCM-Ancient-Books 书目审计补充证据

### 本轮范围

- 只读消费编号 `000`–`699` 的 TXT
- 校验书名唯一、编号连续、编码和未完成下载
- 不把全文或书目节点写入图谱

### 结构与隔离结果

- 输出：0 节点记录、0 条关系
- 可解码 699 本，全部 GB18030
- 隔离：`203-婴童类萃.txt` 解码失败、`700.李培生老中医经验集.txt`、2 个下载残留

### 隔离 Neo4j smoke

无图记录，未启动临时容器。

### 回归证据

```text
data_ingestion: 124 passed, 2 skipped
changed-file Ruff: passed
changed-file ty: passed
cleaner CLI: 0 records / 0 edges, publish=false
```

### 结论与边界

- 结果：书目审计 `pass`；全文不得作为图谱真源
- 仓库无许可证，固定 `publish:false`
- 统一纳入决策见 `docs/architecture/data-sources.md`

## 19. 2026-08-19 剩余已收录源审计补充证据

### 本轮范围

- `classical-tcm-canon`、SylvanL 预训练三份 JSON、ZY-BERT 预训练 RAR
- 全部只做结构/许可审计，不入图

### 结构与隔离结果

- 经典 115 部 / 9,401,166 字，全文隔离
- 预训练文本 177,054 行；串文 `source2` index 11949；医案文件未持有
- RAR 成员 1 个，约 821 MB，未解压

### 结论与边界

- 三源 `records=0`，`publish:false`
- 本地已收录独立候选已全部处理
- `data_ingestion`：134 passed

## 20. 2026-08-19 TCMChat-600k 补登与隐私原则修正

### 本轮范围

- 审查 `.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/` 的 books、opendata、web、sft，而不是只看药典
- 使用原则改为：未明确禁止即可本地使用；整理时过滤品牌与个人标识

### 结构事实

- 61 个内容文件，约 1.57 GB，Dataset Card 为 Apache-2.0
- `pretrain/test` 中 3 个国标文件与 train 哈希相同；药典差 100 字节
- 论文目录未持有；SFT 医案与 TCM-SD 叙述同源

### 结论

- 整包登记为 `tcmchat-600k`，0 图记录
- 下一步优先清洗国标术语、成方制剂、教材和去标识医案
- `data_ingestion`：135 passed

## 21. 2026-08-19 国标术语消歧清洗补充证据

### 本轮范围

- 抽出共用身份门禁 `entity_identity.py`
- 清洗疾病、证候术语和成方制剂各论

### 结果

- 5,219 records / 0 edges；病证 3,358、方剂 1,861
- 同名不同码：`痞气（痞病）` 与 `痞气（积聚类病）`
- 隔离 Neo4j：5219 节点，待验证/scope 错误 0，两条痞气未合并
- 未解析缺口：疾病 61、成方 759
- `data_ingestion`：139 passed

## 22. 2026-08-19 规则-agent 整理合同与验案切分

### 本轮范围

- 增加 `organize prepare/accept`，让规则、脚本、agent 和图库走同一合同
- 对 18 本名医验案做去标识切分，生成 461 条 agent 队列

### 结果

- 姓氏病例已替换；agent 回写必须经 `entity_identity`
- 本轮未跑 LLM，图记录仍为 0
- `data_ingestion`：142 passed

## 23. 2026-08-19 验案保留性别年龄并规则入图

- 姓氏替换为患者，保留 `女22岁` / `男40岁`
- 461 医案 + 3189 病证提及 + 339 方剂提及 = 3989 records
- 113 案解析到性别；importer dry-run 3989
- `data_ingestion`：143 passed；`knowledge_model`：28 passed

## 24. 2026-08-19 剩余可用源与工作目录

- 每源 `work/{queue,extracts,notes}` + `processed/latest`
- PEND-01/02/03/06/08 已出记录；PEND-04/05/07 与专有 canon 书面跳过

## 25. 2026-08-19 TCMChat 剩余子集与 SFT 扩抽

- `tmp/qibo-datasets` 只留指针；正文在 `.cache/{huggingface,github,dropbox}`
- 剩余 SFT（recommend/choice/admet/baichuan/百科全文）已审计跳过，不独立登记
- `knowledge.json` 扩抽：7,459 records / 75,949 edges（方剂 5,906、药材 659、病证提及 894）
- 清理 `tmp/data/runs` 与 `packages/data_ingestion/tmp` 约 667 MB
- `data_ingestion` 指定测试 11 passed（pending_extract + source_layout）





