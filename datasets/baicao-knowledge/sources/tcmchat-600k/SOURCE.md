# TCMChat-dataset-600k

## 身份

- `source_id`: `tcmchat-600k`
- Hugging Face：[ZJUFanLab/TCMChat-dataset-600k](https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k)
- 本地只读入口：`.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/`（仓库 gitignore，不提交原文）
- Dataset Card / API：`Apache-2.0`
- 状态：`cleaned_local` 为整包盘点；子文件尚未全部抽成图记录
- `publish: false`：公开面仍只允许脱敏结构化结果，不发布教材、医案、百科或 SFT 原文

此前清单只把其中的 `2022年中药药典.txt` 登记为 `BC-01`。同目录还有国标术语、成方制剂、教材、名医验案、ChatMed 问答、百科网页和整套 SFT。

## 使用与过滤

上游明确以 Apache-2.0 开源，允许本地使用和派生。整理时必须去掉：

- 患者姓氏+年龄+身份、住院号、电话、身份证号
- 药品商品名、企业品牌、国药准字
- `pretrain/test` 中与 train 重复的国标副本

作者署名（如医案集书名中的「丁光迪」）保留为文献来源，不当作患者标识。

## 子集

| 分组 | 文件 | 大小 | 本轮结论 |
|---|---:|---:|---|
| 国标 | 药典、临床诊疗术语疾病/证候、中药成方制剂 | 7.3 MB | 纳入图谱候选。药典已入图；其余三份待结构清洗 |
| 教材 | 中药学、方剂学、伤寒论、中医基础理论、饮片卷、资格考试、药理学 | 11.0 MB | 纳入为原文证据。`伤寒论.txt` 仅 8 KB 歌诀摘录，不是全书；`药理学.txt` 偏西药教材 |
| 医案 | 18 本验案 | 8.8 MB | 纳入为医案证据，必须去标识。正文含「汤某女22岁」一类姓氏病例 |
| ChatMed | `ChatMed_TCM-v0.2_.txt` | 93.2 MB | 模型生成问答，只作抽取候选，不升格为事实 |
| 网页 | 百度百科 285 MB、`daiy_data.txt` 30.5 MB | 315.6 MB | 百科/词条抽取候选，滤品牌 |
| 论文 | `pretrain/train/papers/` | 未持有 | 官方清单有 `fix_abstract_segmentation.txt`，本地目录为空 |
| pretrain/test | 4 个国标文件 | 7.3 MB | 疾病/证候/成方与 train 哈希相同；药典差 100 字节。禁止当第二源 |
| SFT knowledge / NER | `knowledge.json` 70,309、`entity_extraction.json` 1,997 | 54.3 MB | 结构化候选。NER 含说明书商品名和批准文号，必须过滤 |
| SFT 医案 | `medical_case.json` 48,040 | 84.6 MB | 与 TCM-SD 临床叙述同源痕迹（新冠检测、气虚不摄证）。去标识后只作评测 |
| SFT 推荐/选择/ADMET | 其余 train+test | 约 493 MB | 评测与推荐语料，不作为图谱事实 |
| Baichuan 对话 | `train_baichuan.json` | 497.2 MB | 对话 SFT，不入图 |

整包 61 个内容文件、约 1.57 GB。本轮盘点输出 0 条图记录。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:ZJUFanLab/TCMChat-dataset-600k` |
| `batch_id` | `2026-08-19-tcmchat-600k-v1` |
