# 本机缓存清理 · 2026-08-20

对「已持有但未整包入图」的文件逐项复核。确认对当前图谱**不可用**的从 `.cache/` 删除，约 **8.03 GB / 47 个文件**。Git 跟踪文件未动。

## 删除（不可用）

| 类别 | 路径 | 原因 |
|---|---|---|
| TCM-MKG 化学/PPI | `original_kg/edges.tsv`、`nodes.tsv`，D8–D17、D19–D24、SD1 | 基因/化合物/预测边，主域已用 D1–D7+D18 |
| TCMChat 对话 SFT | `sft/final_train_data_for_baichuan_format/train_baichuan.json` | 对话微调，非图事实 |
| TCMChat 评测 | `recommend_disease/formula`、`choice_*`、`reading_comprehension`、`admet*`、对应 test | 推荐/选择题/ADMET，非图事实 |
| TCMChat SFT 医案 | `sft/train/medical_case.json` 及 test | 与 TCM-SD 叙述同源，未作入图输入 |
| TCMChat 国标 test 副本 | `pretrain/test/` 4 文件 | 与 train 重复或差 100 字节，禁止第二源 |
| 古籍下载残留 | `290-外科证治全书.txt.baiduyun.downloading*` | 未完成下载；正文 TXT 已在 |

## 留下（仍要用或还能抽）

| 类别 | 原因 |
|---|---|
| 古籍 699 本 TXT | 已入书目节点；正文仍可另立抽取，不是废数据 |
| ZY-BERT rar + 解压 txt | 方剂索引从这里抽；同一文件里的非索引行无法单独拆走 |
| ChatMed / daiy / knowledge.json | 分源已入图，溯源需要原文 |
| `entity_extraction.json`、`recommend_herb.json`、百科、论文摘要 | `tcmchat-600k` 已抽提及/相似边，溯源需要原文 |
| TCM-MKG D1–D7、D18、README、PDF | 主域清洗输入 |
| TCM-SD JSON、DeepNER JSON | 已入图源文件 |

未购买的 wangekxy 全量本来就不在本机。
