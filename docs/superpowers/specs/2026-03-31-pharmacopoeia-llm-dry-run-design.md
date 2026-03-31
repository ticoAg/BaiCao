# 药典条目 LLM 抽取 dry-run 设计

## 背景

在 `2026-03-31-pharmacopoeia-ingestion-design.md` 中，仓库已经完成了首版药典条目图谱化主链路：

- `packages/knowledge_model/` 已补齐 `饮片`、`证据` 以及中文关系真源
- `packages/data_ingestion/` 已具备文件路由、条目切段、章节解析与图谱 bundle 映射骨架
- `packages/api/app/pipeline/` 已能将 `2022年中药药典.txt` 的首条样例条目映射为 `药材 / 饮片 / 证据 / 性味 / 归经 / 功效`

但当前抽取环节仍然依赖规则型 `_build_rule_based_extraction()`：

- 只能处理少量固定字段
- 无法充分利用条目级 section 结构
- 很难对异常表述、缺字段、轻度噪声条目做更稳健的抽取

用户已经明确希望下一步切换为 **LLM 抽取**，但不是直接把它接进正式图谱导入主路径，而是先做一个可诊断的、小范围的 `dry-run`：

- 触发方式优先选择 `CLI`
- 只抽样固定数量的条目，而不是整文件全量跑
- 本轮抽样规模固定为 `10` 条
- 以离线结果目录形式输出每个环节的中间产物
- 暂不写数据库或 Neo4j，不直接进入正式导入

## 目标

### 主要目标

1. 为 `2022年中药药典.txt` 提供一个独立的 `LLM dry-run CLI`
2. 对固定 `10` 条条目执行：
   - 规则切段
   - section 解析
   - LLM 抽取
   - 文件专属 Pydantic 校验
   - 共享图谱映射
3. 让每个环节的输入、输出、错误都落盘，便于人工 review
4. 保持现有模块边界清晰，不把试验性 dry-run 逻辑提前塞回正式 pipeline 主路径
5. 为后续把 LLM 抽取接回 `packages/api/app/pipeline/` 提供可验证依据

### 非目标

- 本轮不直接替换正式 pipeline 中的默认抽取路径
- 本轮不对整份药典文件全量执行 LLM 抽取
- 本轮不执行正式图谱写入
- 本轮不引入章节级证据节点或断言级证据节点
- 本轮不扩展到 `national_standard` 目录下其他文件

## 用户确认后的边界

基于本轮沟通，已确认以下约束：

- 先做 `CLI`，不先做 UI 或 pipeline 开关
- 抽样条目数固定为 `10`
- dry-run 必须输出每个环节的中间结果
- 继续保持：
  - 模块化设计
  - `protocol-first`
  - 仅在边界处做一次数据校验

## 方案对比

### 方案 1：独立 `CLI dry-run`

做法：

- 在 `packages/data_ingestion/` 内部新增 CLI
- 只对本地缓存文件执行条目抽样和 LLM 抽取
- 落盘中间结果与聚合统计

优点：

- 最利于快速观察抽取质量
- 不会把正式 pipeline 主路径提前复杂化
- 易于反复运行、比较 prompt 调整前后的效果

缺点：

- 首版结果不会直接在 UI 中可见

### 方案 2：在现有 pipeline 中增加 `dry-run` 模式

做法：

- 直接在 `packages/api/app/pipeline/` 中扩展 dry-run 分支
- 通过 API 或工作台触发小批量 LLM 抽取

优点：

- 后续更容易接 UI

缺点：

- 第一轮调试会被 API、preview payload、run 状态和工作台交互噪音放大
- 不利于单纯聚焦抽取质量

### 方案 3：临时脚本

做法：

- 在仓库中写一个一次性 Python 脚本
- 跑完 10 条后手动查看输出

优点：

- 初始编码最快

缺点：

- 容易演变成不可维护的临时逻辑
- 不符合 `protocol-first` 和后续复用目标

## 推荐方案

推荐采用 **方案 1：独立 `CLI dry-run`**。

### 推荐原因

1. 最适合先观察 LLM 抽取效果，而不是先解决 UI 或 API 交互问题
2. 最便于保存中间结果并对比 prompt / schema 调整前后的差异
3. 最符合“先验证质量，再接正式主路径”的节奏

## 设计决策

### 决策 1：dry-run 继续放在 `packages/data_ingestion/`

本轮仍属于“图谱前”处理能力演进，因此 dry-run 主体不放到 `packages/api/`，而继续放在：

```text
packages/data_ingestion/
```

`packages/api/app/pipeline/structured_extraction.py` 暂时仅作为后续回接 pipeline 的桥接层，不作为本轮主入口。

### 决策 2：CLI 只做触发层

CLI 不承担业务逻辑，只负责：

- 参数解析
- 调用 dry-run 编排器
- 输出运行结果目录路径与摘要

建议入口：

```text
packages/data_ingestion/data_ingestion/cli/pharmacopoeia_dry_run.py
```

### 决策 3：dry-run 编排器与 LLM 边界分离

新增两层清晰职责：

1. `llm_extraction.py`
   单条条目的 LLM 抽取边界：
   - 输入：`PharmacopoeiaEntrySections`
   - 输出：原始 JSON + `PharmacopoeiaExtractionResult`

2. `dry_run.py`
   批量 dry-run 编排层：
   - 读取本地文件
   - 切段
   - section 解析
   - 调用 LLM 抽取
   - 校验
   - 映射 bundle
   - 落盘结果

### 决策 4：LLM 仅输出文件专属抽取模型

LLM 不直接输出共享图谱模型，也不直接输出 `GraphImportRecord`。

LLM 输出限定为文件专属模型：

- `PharmacopoeiaHerbExtraction`
- `PharmacopoeiaPreparedPieceExtraction`
- `PharmacopoeiaExtractionResult`

共享图谱模型仍由 `mapping.py` 负责构造。

### 决策 5：dry-run 输出固定目录结构

默认输出目录为：

```text
tmp/pharmacopoeia-dry-run/<timestamp>/
```

固定包含：

- `run_config.json`
- `entries.jsonl`
- `parsed_sections.jsonl`
- `llm_requests.jsonl`
- `llm_responses.jsonl`
- `validated_extractions.jsonl`
- `graph_bundles.jsonl`
- `summary.json`
- `README.md`

### 决策 6：统一使用 `entry_key` 串联各环节

每条记录都带统一 `entry_key`，建议格式：

```text
<entry_title>:<start_line>-<end_line>
```

用于跨文件对照：

- `entries.jsonl`
- `parsed_sections.jsonl`
- `llm_requests.jsonl`
- `llm_responses.jsonl`
- `validated_extractions.jsonl`
- `graph_bundles.jsonl`

## LLM 输入输出边界

### 输入

LLM 输入是单条条目的 section 化 payload，建议至少包含：

- `entry_title`
- `header_lines`
- `base_description`
- `sections`
- `piece_sections`
- `raw_text`

### 输出

建议扩展后的模型至少包含：

#### `PharmacopoeiaHerbExtraction`

- `herb_name`
- `pinyin_name`
- `latin_name`
- `base_description`

#### `PharmacopoeiaPreparedPieceExtraction`

- `piece_name`
- `parent_herb_name`
- `processing_text`
- `flavors`
- `nature`
- `meridians`
- `efficacies`
- `usage_text`
- `storage_text`
- `caution_text`

#### `PharmacopoeiaExtractionResult`

- `herb`
- `prepared_piece`
- `warnings`
- `confidence_notes`

### Prompt 约束

Prompt 必须显式要求：

- 只根据输入文本抽取
- 不补充中医常识
- 不创建新字段
- 无法确定时返回 `null` 或空数组
- 如 `饮片` section 存在，优先把 `性味与归经`、`功能与主治`、`用法与用量`、`贮藏` 归给 `prepared_piece`
- 不把 `饮片` 字段无依据复制给主药材
- 只返回 JSON，不输出解释性文字

## dry-run 输出格式

### `run_config.json`

记录本次试跑参数：

- `provider`
- `dataset`
- `file_path`
- `local_path`
- `limit`
- `entry_offset`
- `model_name`
- `started_at`
- `git_commit`

说明：

- `entry_offset` 先于 `limit` 生效，用于控制从第几条切段结果开始抽样
- `model_name`、`git_commit` 若当前运行环境无法稳定获取，应显式写 `null`，不要省略字段

### `entries.jsonl`

每行一个 `RawEntryBlock`，用于检查条目切段是否正确。

### `parsed_sections.jsonl`

每行一个 `PharmacopoeiaEntrySections`，用于检查：

- `饮片` section 是否稳定抽出
- `性味与归经` / `功能与主治` 是否归到 `piece_sections`

### `llm_requests.jsonl`

每行一条实际发送给 LLM 的 payload。

### `llm_responses.jsonl`

每行一条 LLM 原始响应，不做解释性改写。

### `validated_extractions.jsonl`

每条包含：

- `entry_key`
- `entry_title`
- `status`
- `error_type`
- `error_message`
- `validated_extraction`

其中 `status` 枚举建议为：

- `llm_json_invalid`
- `llm_schema_invalid`
- `mapping_invalid`
- `success`

补充约束：

- `llm_json_invalid` / `llm_schema_invalid` 由 `llm_extraction.py` 负责产出
- `mapping_invalid` 由 dry-run 编排阶段在 `validated_extraction -> graph bundle` 映射失败时补记，不能让单条映射异常直接中断整批试跑

### `graph_bundles.jsonl`

每条包含映射摘要：

- `entry_key`
- `entry_title`
- `node_count`
- `edge_count`
- `node_names`
- `edge_types`
- `record_count`
- `bundle_errors`

### `summary.json`

聚合统计至少包含：

- `entries_total`
- `entries_attempted`
- `entries_succeeded`
- `entries_failed`
- `llm_json_invalid_count`
- `llm_schema_invalid_count`
- `mapping_invalid_count`
- `success_rate`
- `error_examples`

## 模块与文件落位

建议新增或调整：

```text
packages/data_ingestion/data_ingestion/
├── cli/
│   └── pharmacopoeia_dry_run.py
└── processors/huggingface/zjufanlab_tcmchat_dataset_600k/national_standard_2022_pharmacopoeia/
    ├── extraction_models.py
    ├── prompts.py
    ├── llm_extraction.py
    ├── dry_run.py
    ├── normalization.py
    ├── parsing.py
    ├── segmentation.py
    └── mapping.py
```

其中：

- `extraction_models.py`：文件专属抽取模型真源
- `prompts.py`：prompt 与 payload 构造
- `llm_extraction.py`：单条 LLM 边界
- `dry_run.py`：10 条 dry-run 编排器
- `mapping.py`：共享图谱映射

## 首版成功标准

对 `10` 条抽样条目：

1. 全部完成规则切段
2. 大多数完成 section 解析
3. 至少 `7/10` 返回合法 JSON
4. 至少 `5/10` 通过 `PharmacopoeiaExtractionResult` 校验
5. 至少 `5/10` 映射成 bundle
6. `一枝黄花` 必须成功
7. 所有失败都具有明确错误分类和原始响应记录

## 风险与后续扩展

### 风险

- 某些条目 section 不完整，LLM 可能输出大量空字段
- 原始药典文本存在轻度 OCR / 排版噪声，可能影响模型稳定性
- `10` 条样本能暴露趋势，但不能完全代表全量文件

### 后续扩展

- 将 dry-run 中验证通过的 LLM 抽取逻辑替换正式规则抽取
- 将 `CLI` 能力接回 `packages/api/app/pipeline/`
- 扩展到 `national_standard` 目录下其他文件
