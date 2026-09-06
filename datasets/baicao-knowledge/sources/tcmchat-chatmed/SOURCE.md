# TCMChat ChatMed 问答

## 身份

- `source_id`: `tcmchat-chatmed`
- 载体：`.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/opendata/ChatMed_TCM-v0.2_.txt`
- 上游：[ZJUFanLab/TCMChat-dataset-600k](https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k)
- 状态：`imported`（已入本地图，仅词表提及）；`publish: false`
- 许可：整包 Dataset Card 为 Apache-2.0；对话文本不当已验证临床事实

模型生成问答。只保留国标词表命中的提及，升格为「对话提及」。品牌名隔离。不把问答升格为治疗关系。

## 抽取口径

- 扫描全部有效行（长度 ≥ 24），2026-08-20 取消 8000 行上限
- 用国标术语词表最长匹配；名称短于 3 字跳过
- `contains_brand` 命中丢弃
- 节点类型沿用词表：`病证` / `方剂`；`tcm_type=对话提及`
- 不生成边；不当已验证事实

## 产量

`processed/latest/stats.json`：1043 records（病证 902、方剂 141），0 edges。`scanned_lines=535240`。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/opendata` |
| `batch_id` | `2026-08-19-tcmchat-chatmed-v1` |
| `processor` | `pending_extract` |
