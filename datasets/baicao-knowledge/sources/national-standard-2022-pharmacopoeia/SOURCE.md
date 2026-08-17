# 2022年中药药典

## 身份

- `source_id`: `national-standard-2022-pharmacopoeia`
- 标题：2022年中药药典
- 原始载体：`ZJUFanLab/TCMChat-dataset-600k` 内 `pretrain/train/books/national_standard/2022年中药药典.txt`
- 许可：跟随上游 Hugging Face 数据集条款；白草侧只做抽取与再发布结构化结果
- 状态：`imported`（605/605 条目已抽并 merge 入库）

## 筛选该源

图里实际写入的 scope 用竖线分隔（与 2026-04 首轮导入一致）：

```cypher
MATCH (n)
WHERE n.import_scope_key = 'huggingface|ZJUFanLab/TCMChat-dataset-600k|pretrain/train/books/national_standard/2022年中药药典.txt'
   OR 'huggingface|ZJUFanLab/TCMChat-dataset-600k|pretrain/train/books/national_standard/2022年中药药典.txt' IN coalesce(n.import_scope_keys, [])
RETURN n
```

等价属性：

| 字段 | 值 |
|------|-----|
| `source_provider` | `huggingface` |
| `dataset_name` | `ZJUFanLab/TCMChat-dataset-600k` |
| `file_path` | `pretrain/train/books/national_standard/2022年中药药典.txt` |

重置该源：`packages/api` 的 `app.importers.dataset_reset_cli`，传入同一组 provider/dataset/file_path。

## 处理链

原文 → `pharmacopoeia` 切段 → section 解析 → LLM 抽取 → `GraphImportRecord` → Neo4j
