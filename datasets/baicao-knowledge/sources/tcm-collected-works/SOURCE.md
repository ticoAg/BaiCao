# 中医医论样本（tcm-collected-works）

## 身份

- `source_id`: `tcm-collected-works`
- Hugging Face：[wangekxy/tcm-collected-works](https://huggingface.co/datasets/wangekxy/tcm-collected-works)
- 本地：`.cache/huggingface/wangekxy/tcm-collected-works/sample.jsonl`
- 状态：`imported`（公开样本已入本地图）；`publish: false`

仅持有 HF 公开 sample，不是 171 部全量。全量 unpaid-full-set-not-held，未购买、未下载。本轮按非商用本地使用处理样本，版权过滤后置。

抽样书名（见 `work/notes/suitability.md`）：《医学举要》（清·徐镛）、《上池杂说》（明·冯元成）、《三消论》（金·刘完素）。医论不是已验证临床事实，记录保持 `pending`。不发明医话/医论专类。

## 输入与处理链

```text
sample.jsonl（title + text）
  -> wangekxy_topic_sample
  -> 来源节点 + 现有词表最长匹配提及 + 来源于
  -> processed/latest/records.jsonl + stats.json
```

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:wangekxy/tcm-collected-works` |
| `batch_id` | `2026-08-20-tcm-collected-works-sample-v1` |
