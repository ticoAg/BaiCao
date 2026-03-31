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
