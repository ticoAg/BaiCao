# 中医养生样本（tcm-health-cultivation）

## 身份

- `source_id`: `tcm-health-cultivation`
- Hugging Face：[wangekxy/tcm-health-cultivation](https://huggingface.co/datasets/wangekxy/tcm-health-cultivation)
- 本地：`.cache/huggingface/wangekxy/tcm-health-cultivation/sample.jsonl`
- 状态：`imported`（公开样本已入本地图）；`publish: false`

仅持有 HF 公开 sample，不是 18 部全量。全量 unpaid-full-set-not-held，未购买、未下载。本轮按非商用本地使用处理样本，版权过滤后置。

抽样书名（见 `work/notes/suitability.md`）：《万氏家传养生四要》（明·万全）、《养生肤语》（明·陈继儒）、《陆地仙经》（清·马齐）。只抽现有类型提及；不发明 `导引`、功法、食谱节点。养生口诀不是已验证临床事实，记录保持 `pending`。

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
| `import_scope_key` | `huggingface:wangekxy/tcm-health-cultivation` |
| `batch_id` | `2026-08-20-tcm-health-cultivation-sample-v1` |
