# 医部类书样本（tcm-reference-compendia）

## 身份

- `source_id`: `tcm-reference-compendia`
- Hugging Face：[wangekxy/tcm-reference-compendia](https://huggingface.co/datasets/wangekxy/tcm-reference-compendia)
- 本地：`.cache/huggingface/wangekxy/tcm-reference-compendia/sample.jsonl`
- 状态：`imported`（公开样本已入本地图）；`publish: false`

仅持有 HF 公开 sample 的 3 卷切片，不是 3 部完整书，也不是 CONTENTS 宣称的 14 部全量。全量 unpaid-full-set-not-held，未购买、未下载。本轮按非商用本地使用处理样本，版权过滤后置。

抽样卷题（见 `work/notes/suitability.md`）：`医部全录卷170至卷170`（肩门）、`医部全录卷171至卷171`（腋门）、`医部全录卷226至卷226`（懊憹门）。`title` 是卷切片，不纠正为完整书名。`author` 字段是门类名，不可当作可靠人物身份。不发明类书卷/门类型，也不把类书引文升级为独立古籍节点。

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
| `import_scope_key` | `huggingface:wangekxy/tcm-reference-compendia` |
| `batch_id` | `2026-08-20-tcm-reference-compendia-sample-v1` |
