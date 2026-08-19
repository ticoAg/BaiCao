# SylvanL TCM Pretrain

## 身份

- `source_id`: `sylvanl-tcm-pretrain`
- Hugging Face：[SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain](https://huggingface.co/datasets/SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain)
- 本地只读入口：`.cache/huggingface/SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain/` 中的 3 个 JSON
- 未持有：4 个 `CPT_medicalRecord_*` 医案文件
- 状态：`cleaned_local`；`publish: false`

Dataset Card 为 `apache-2.0`，但本地三份都是 `{text}` 自由文本，混有西药、医疗美容、保健问答。`CPT_tcmKnowledge_source2_12889.json` 第 11949 条把「注射用亚锡葡庚糖酸钠Ⅰ」的药理段落串入氨苄西林/舒巴坦。不能整包当中医知识图。

## 质量边界

输出 0 records / 0 edges。持有行：书籍 146,244、百科 17,921、国标/百科 12,889。医案 4 个文件未下载，保持隔离。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain` |
| `batch_id` | `2026-08-19-sylvanl-tcm-pretrain-v1` |
