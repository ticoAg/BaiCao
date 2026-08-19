# TCMChat-dataset-600k

## 身份

- `source_id`: `tcmchat-600k`
- Hugging Face：[ZJUFanLab/TCMChat-dataset-600k](https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k)
- 本地只读入口：`.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/`（仓库 gitignore，不提交原文）
- Dataset Card / API：`Apache-2.0`
- 状态：`cleaned_local` 为整包盘点（0 条整包图记录）；可入图子集已分源；剩余 SFT 已审计跳过
- `publish: false`：公开面仍只允许脱敏结构化结果，不发布教材、医案、百科或 SFT 原文

此前清单只把其中的 `2022年中药药典.txt` 登记为 `BC-01`。国标术语/成方、教材、医案、daiy、ChatMed、`knowledge.json` 已分源登记。`recommend_*` / `choice_*` / `admet*` / `baichuan` / 百度百科全文不独立登记。

## 使用与过滤

上游明确以 Apache-2.0 开源，允许本地使用和派生。整理时必须去掉：

- 患者姓氏+年龄+身份、住院号、电话、身份证号
- 药品商品名、企业品牌、国药准字
- `pretrain/test` 中与 train 重复的国标副本

作者署名（如医案集书名中的「丁光迪」）保留为文献来源，不当作患者标识。

## 子集

| 分组 | 文件 | 大小 | 本轮结论 |
|---|---:|---:|---|
| 国标 | 药典、临床诊疗术语疾病/证候、中药成方制剂 | 7.3 MB | 药典已入图（`BC-01`）；术语/成方已清洗为 `national-standard-terms` |
| 教材 | 中药学、方剂学、伤寒论、中医基础理论、饮片卷、资格考试、药理学 | 11.0 MB | 已清洗为 `tcmchat-textbooks`。`伤寒论.txt` 仅歌诀摘录；`药理学.txt` 偏西药 |
| 医案 | 18 本验案 | 8.8 MB | 已清洗为 `tcmchat-medical-cases`。去姓氏、留性别年龄 |
| ChatMed | `ChatMed_TCM-v0.2_.txt` | 93.2 MB | 已清洗为 `tcmchat-chatmed`。模型生成问答，只作提及，不升格为事实 |
| daiy | `daiy_data.txt` | 30.5 MB | 已清洗为 `tcmchat-web`。只取中医病名/病证名行，滤品牌 |
| 百度百科 | `2019_baidubaike.txt` | 285 MB | 已审计跳过。无稳定词条边界，不独立登记 |
| 论文 | `pretrain/train/papers/` | 未持有 | 官方清单有 `fix_abstract_segmentation.txt`，本地目录为空 |
| pretrain/test | 4 个国标文件 | 7.3 MB | 疾病/证候/成方与 train 哈希相同；药典差 100 字节。禁止当第二源 |
| SFT knowledge | `knowledge.json` 70,309 | 48.9 MB | 已清洗为 `tcmchat-sft-knowledge`：7,459 records / 75,949 edges，不当事实 |
| SFT NER | `entity_extraction.json` 1,997；test `ner_480.json` | 约 3.6 MB | 已审计跳过。说明书商品名和批准文号，只作评测，不独立登记 |
| SFT 医案 | `medical_case.json` 48,040；test `medical_case_500_val.json` | 约 81.5 MB | 已审计跳过。与 TCM-SD 临床叙述同源，不升格事实，不独立登记 |
| SFT recommend_* | `recommend_disease/formula/herb.json`；test `recommend_500.json` | 约 344 MB | 已审计跳过。化学相似谱/靶标谱或证候推荐评测，不独立登记 |
| SFT 选择题 | `choice_herb_formula.json` 及 test 选择题 | 约 90.4 MB | 已审计跳过。考题，不入图，不独立登记 |
| SFT 阅读理解 | `reading_comprehension.json`；test `rc_500.json` | 约 24.0 MB | 已审计跳过。评测语料，不入图，不独立登记 |
| SFT ADMET | `admet.json` 及 test `admet_*` | 约 12.3 MB | 已审计跳过。分子 ADMET 预测，不入图，不独立登记 |
| Baichuan 对话 | `train_baichuan.json` | 497.2 MB | 已审计跳过。对话 SFT，不入图，不独立登记 |

整包 61 个内容文件、约 1.57 GB。本源盘点输出 0 条图记录；子集产量记在各分源 `processed/latest/stats.json`。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:ZJUFanLab/TCMChat-dataset-600k` |
| `batch_id` | `2026-08-19-tcmchat-600k-v1` |
