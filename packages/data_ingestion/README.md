# `data_ingestion`

`packages/data_ingestion/` 是 BaiCao 的数据采集边界包，负责把来源适配、原始材料整理、候选抽取这类“进入知识图谱之前”的工作收敛到一个最小可复用边界。

## 边界规则

- 这里只放来源适配、抽取候选、统一中间格式相关模型
- 图谱节点 / 边 / 导入记录真源来自 `packages/knowledge_model/`
- 需要进入 API / importer / exporter 的统一记录时，直接复用共享 `GraphImportRecord`
- 不在这里重复声明 `NodeType`、`EdgeType`、节点模型或图谱状态枚举

## Agent 协作口径

- 改动采集候选结构时，先确认是否仍属于“图谱前”边界
- 若影响 API / importer / exporter 消费的统一记录，先更新共享知识模型，再更新消费者
- 文档、测试、实现都应围绕“共享图模型 + 数据采集辅助模型”这条主线写证据

## 当前最小模型

- `ExtractionCandidate`：候选抽取结果，携带目标 `NodeType`、名称、来源和可选属性
- `SourceDocument`：来源适配后得到的最小文本单元

## 药典条目 LLM dry-run

可以对 `2022年中药药典.txt` 先做小范围 dry-run，观察条目切段、section 解析、LLM 输出和图谱 bundle 摘要：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_dry_run \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path /abs/path/to/BaiCao/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --limit 10 \
  --concurrency 10
```

当前 prompt 会要求模型返回完整 JSON 字段集合；若证据块里没有对应内容，字段也必须保留并返回 `null` 或空数组。

CLI 会把每条条目的 LLM 耗时和原始响应摘要打印到终端，并在 `summary.json` 中落盘聚合统计。若要专门调试真实上游链路，建议先跑一条并显式设置硬超时：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_dry_run \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path /abs/path/to/BaiCao/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --limit 1 \
  --timeout-seconds 45 \
  --output-dir tmp/pharmacopoeia-dry-run/real-run-1
```

如果当前环境没有 `OPENAI_API_KEY`，可以先用假响应检查各环节落盘是否正常：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_dry_run \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path /abs/path/to/BaiCao/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --limit 10 \
  --use-fake-response
```

## 药典条目切分评估

如果当前要先验证“每个药材条目是否能稳定切成完整原文块”，可以先跑切分评估，不经过 LLM：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_segmentation_assessment \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path /abs/path/to/BaiCao/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --output-dir tmp/pharmacopoeia-segmentation-assessment/manual-run \
  --sample-limit 30
```

它会输出：

- `segmentation_summary.json`：条目总数、起始规则分布、排除标题分布、可疑样本
- `duplicate_title_counts`：同一中文标题重复出现的分布，便于排查源文本重复或标题错配
- `segmented_entries.jsonl`：每个药材的完整原文块
- `suspicious_entries.jsonl`：需要人工抽样复核的切分样本

## 药典条目大批量 ingest

当需要把 `2022年中药药典.txt` 经过真实 LLM 抽取后落成统一 `GraphImportRecord` 快照时，可以直接跑大批量 ingest CLI：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_ingest \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path /abs/path/to/BaiCao/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --limit 100 \
  --concurrency 10 \
  --timeout-seconds 90 \
  --output-dir tmp/pharmacopoeia-ingestion/full-run
```

如果希望直接吃 Infisical 中的模型配置，建议从仓库根目录执行：

```bash
infisical run --project-config-dir="$PWD" -- \
  bash -lc 'ROOT="$PWD"; cd packages/data_ingestion && uv run python -m data_ingestion.cli.pharmacopoeia_ingest \
    --dataset ZJUFanLab/TCMChat-dataset-600k \
    --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
    --local-path "$ROOT/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt" \
    --limit 100 \
    --concurrency 10 \
    --timeout-seconds 90 \
    --output-dir tmp/pharmacopoeia-ingestion/full-run'
```

产物目录会继续保留每个阶段的中间文件，并新增：

- `graph_import_records.jsonl`：后续可直接交给 `packages/api` 导入 Neo4j 的统一快照

## 将快照导入 Neo4j

拿到 `graph_import_records.jsonl` 后，可以复用 `packages/api` 现有导入 CLI 直接写图谱：

```bash
cd packages/api
uv run python -m app.importers.cli \
  ../data_ingestion/tmp/pharmacopoeia-ingestion/full-run/manual-run/graph_import_records.jsonl \
  --neo4j
```

同样，如果 Neo4j 连接配置也来自 Infisical，推荐从仓库根目录执行：

```bash
infisical run --project-config-dir="$PWD" -- \
  bash -lc 'cd packages/api && uv run python -m app.importers.cli \
    ../data_ingestion/tmp/pharmacopoeia-ingestion/full-run/manual-run/graph_import_records.jsonl \
    --neo4j'
```

## 只重跑失败条目

如果一次大批量运行中部分条目因为上游限流、超时或 schema 校验失败未成功，可以使用上一轮产物里的 `validated_extractions.jsonl` 自动筛选失败条目，只重跑失败集合：

```bash
cd packages/data_ingestion
uv run python -m data_ingestion.cli.pharmacopoeia_ingest \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --local-path /abs/path/to/BaiCao/.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt \
  --retry-failed-from tmp/pharmacopoeia-ingestion/full-run/manual-run \
  --concurrency 1 \
  --max-attempts 3 \
  --retry-backoff-seconds 5 \
  --timeout-seconds 90 \
  --output-dir tmp/pharmacopoeia-ingestion/retry-failed
```

未传 `--limit` 时，`--retry-failed-from` 会默认处理上一轮所有失败条目；如果只想先验证一小批，可以额外加 `--limit 20`。

如果当前 provider 使用的是带版本路径的 OpenAI 兼容地址，例如：

```text
https://ark.cn-beijing.volces.com/api/v3
```

当前实现会保留该版本路径，不再额外追加 `/v1`。同时，如果上游不支持 `enable_thinking` 这类扩展字段，会在首次 400 失败后自动去掉该扩展并重试。

## 重置某个数据集后重跑

如果处理方法优化后需要对某个数据集重新处理，推荐顺序是：

1. 用数据集 scope 清理新版带 scope 属性的关系和孤立节点
2. 对历史不带 scope 属性的快照，补传 `--snapshot-jsonl` 做精确边清理
3. 重新执行 `pharmacopoeia_ingest`
4. 重新执行 `app.importers.cli ... --neo4j`

示例：

```bash
cd packages/api
uv run python -m app.importers.dataset_reset_cli \
  --provider huggingface \
  --dataset ZJUFanLab/TCMChat-dataset-600k \
  --file-path pretrain/train/books/national_standard/2022年中药药典.txt \
  --snapshot-jsonl ../data_ingestion/tmp/pharmacopoeia-ingestion/full-run/manual-run/graph_import_records.jsonl
```

说明：

- 新版药典 ingest 会在节点和边属性中写入 `source_provider`、`dataset_name`、`file_path` 与 `import_scope_key`
- 关系写入时会用 `import_scope_key` 参与 `MERGE`，因此同一语义关系可以按数据集 scope 安全重置
- 历史快照若没有 scope 属性，必须通过 `--snapshot-jsonl` 清理旧边，避免遗留旧格式关系
