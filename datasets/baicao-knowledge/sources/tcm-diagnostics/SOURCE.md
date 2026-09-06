# 中医诊法样本（tcm-diagnostics）

## 身份

- `source_id`: `tcm-diagnostics`
- Hugging Face：[wangekxy/tcm-diagnostics](https://huggingface.co/datasets/wangekxy/tcm-diagnostics)
- 本地：`.cache/huggingface/wangekxy/tcm-diagnostics/sample.jsonl`
- 状态：`imported`（公开样本已入本地图）；`publish: false`

仅持有 HF 公开 3 部样本，未持有未付费全量。本轮按非商用本地使用处理样本，版权过滤后置。

样本书目（见 `work/notes/suitability.md`）：察舌辨症新法、脉象统类、咽喉脉证通论。图模型无 `脉象` / `舌象` 节点类型，不把脉名、苔名提升为独立节点；只抽现有枚举（`来源` 及词表可匹配的病证 / 药材 / 方剂等）提及。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:wangekxy/tcm-diagnostics` |
| `batch_id` | `2026-08-20-tcm-diagnostics-sample-v1` |
