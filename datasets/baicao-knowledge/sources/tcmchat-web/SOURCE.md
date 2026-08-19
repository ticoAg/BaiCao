# TCMChat web 百科

## 身份

- `source_id`: `tcmchat-web`
- 消费：`.cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/web/daiy_data.txt`
- 跳过：同目录 `2019_baidubaike.txt`（约 285 MB，无稳定词条边界）
- 上游：[ZJUFanLab/TCMChat-dataset-600k](https://huggingface.co/datasets/ZJUFanLab/TCMChat-dataset-600k)
- 状态：`cleaned_local`；`publish: false`
- 许可：整包 Apache-2.0；百科原文不进 public

只取 daiy 中「中医病名 / 中医病证名」行作为病证术语。百度百科全文不整包入图，也不独立登记。

## 抽取口径

- 行内必须含「中医病名」或「中医病证名」
- 标题取逗号前片段；长度 < 2 或品牌命中丢弃
- 同名去重；节点类型 `病证`，`tcm_type=来源百科病名`
- 不生成边

## 产量

`processed/latest/stats.json`：2,290 records / 0 edges，全部为病证。

## 筛选

| 字段 | 值 |
|---|---|
| `import_scope_key` | `huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/web` |
| `batch_id` | `2026-08-19-tcmchat-web-v1` |
| `processor` | `pending_extract` |
