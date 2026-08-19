# classical-tcm-canon

## 身份

- `source_id`: `classical-tcm-canon`
- Hugging Face：[wangekxy/classical-tcm-canon](https://huggingface.co/datasets/wangekxy/classical-tcm-canon)
- 本地只读入口：`.cache/huggingface/wangekxy/classical-tcm-canon/classical-tcm-canon.parquet`
- 状态：`cleaned_local`；`publish: false`

Dataset Card 声明原作公版，但 `license: other` 且 `license_name: proprietary-commercial`。115 部、9,401,166 字与本地 Parquet 一致。本轮只做书目审计，不发布全文，也不把正文写入图谱。

## 质量边界

输出 0 records / 0 edges。`ship_tier` A=54、B=61。标题与 id 均唯一，无空正文。现代标点和异体字未规范化。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:wangekxy/classical-tcm-canon` |
| `batch_id` | `2026-08-19-classical-tcm-canon-v1` |
