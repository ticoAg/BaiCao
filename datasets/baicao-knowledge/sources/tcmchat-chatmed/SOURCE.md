# TCMChat ChatMed 问答

## 身份

- `source_id`: `tcmchat-chatmed`
- 载体：`.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/opendata/ChatMed_TCM-v0.2_.txt`
- 上游：[ZJUFanLab/TCMChat-dataset-600k](https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k)
- 状态：`cleaned_local`；`publish: false`
- 许可：整包 Dataset Card 为 Apache-2.0；对话文本不当已验证临床事实

模型生成问答。只保留国标词表命中的提及，升格为「对话提及」。品牌名隔离。不把问答升格为治疗关系。

## 抽取口径

- 扫描有效行（长度 ≥ 24）前 8000 条
- 用国标术语词表最长匹配；名称短于 3 字跳过
- `contains_brand` 命中丢弃
- 节点类型沿用词表：`病证` / `方剂`；`tcm_type=对话提及`
- 不生成边

## 产量

`processed/latest/stats.json`：133 records（病证 100、方剂 33），0 edges。`scanned_lines=8000`。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/opendata` |
| `batch_id` | `2026-08-19-tcmchat-chatmed-v1` |
| `processor` | `pending_extract` |
