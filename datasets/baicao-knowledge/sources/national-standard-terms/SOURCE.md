# 国标临床术语与成方制剂

## 身份

- `source_id`: `national-standard-terms`
- 载体：`ZJUFanLab/TCMChat-dataset-600k` 的 `pretrain/train/books/national_standard/`
- 消费：`中医临床诊疗术语疾病.txt`、`中医临床诊疗术语证候.txt`、`中药成方制剂.txt`
- 药典文件仍只属于 `BC-01`，本源不重复消费
- 状态：`cleaned_local`；`publish: false`（公开面只允许后续脱敏结构，不含原文）

整包 Dataset Card 为 Apache-2.0。整理时过滤电话、证件、住院号和国药准字。

## 实体身份与消歧

共用 `data_ingestion/entity_identity.py`：

- 身份键 = `节点类型 + 规范名 + 稳定 ID`（疾病/证候用国标编号，成方用拼音串）
- 只在三键全同时合并；属性冲突直接失败
- 别名、拼音、近义和 LLM 不参与身份
- 同名不同码保持独立，并用父类名限定展示名
- 本批唯一需要限定的是两条「痞气」：`痞气（痞病）` 与 `痞气（积聚类病）`
- 疾病与证候主名无交叉；别名不升格为独立节点

## 映射

| 源 | 节点 | 属性 |
|---|---|---|
| 疾病术语 | `病证`，`tcm_type=来源国标疾病` | `term_code`、别名、定义、父类名 |
| 证候术语 | `病证`，`tcm_type=来源国标证候` | 同上 |
| 成方制剂各论 | `方剂`，`tcm_type=来源国标成方` | 拼音、组成、功能主治 |

本轮不生成边。层次关系只保留 `parent_term`，因为导入器尚未接受 `父类` 边。

## 质量边界

输出 5,219 records / 0 edges：病证 3,358（疾病 1,308 + 证候 2,050）、方剂 1,861。前言声称疾病 1,369、成方 2,620；差额记为未解析缺口，不补猜。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/books/national_standard` |
| `batch_id` | `2026-08-19-national-standard-terms-v1` |
