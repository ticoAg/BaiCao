# 道医苏子阳

## 身份

- `source_id`: `daoyi-suyang`
- 标题：道医苏子阳
- 形态：389 章叙事文本（医案 / 诊疗过程），不是结构化药典
- 本地入口：`/Users/ticoag/Downloads/道医苏子阳.md`（69423 行，3389883 bytes）
- 原站目录页（收集时标注）：<https://www.biquge.tw/book/1270739/>
- 许可：**未获公开转载授权**。只进 private dataset / 本地 staging，不进 git，不上公开 HF
- 状态：`extracted`（v3 `2026-08-16-suyang-v3-*`，已进 `processed/latest`；Neo4j 未重导）

## 筛选该源

```cypher
MATCH (n)
WHERE n.import_source_id = 'daoyi-suyang'
   OR 'daoyi-suyang' IN coalesce(n.import_source_ids, [])
RETURN n
```

| 字段 | 值 |
|------|-----|
| `source_provider` | `manual` |
| `dataset_name` | `baicao-knowledge` |
| `file_path` | `sources/daoyi-suyang/source/道医苏子阳.md` |
| `import_scope_key` | `manual:baicao-knowledge:daoyi-suyang` |

## 处理链（规划）

原文 → 按章切段 → 医案/对话块识别 → 专属抽取（禁止套用药典 prompt） → `GraphImportRecord` → Neo4j

是否新增 `方剂` / `医案` / `穴位` / `治法` 节点，等 wave-1 抽样后再改 `knowledge_model`。
