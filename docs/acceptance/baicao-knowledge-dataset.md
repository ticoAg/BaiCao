# 验收 · 白草知识数据集

**状态：** pass（入图、查询与 public Viewer，2026-08-19）
**范围：** 药典 2022 + 道医苏子阳 v3 的脱敏 public HF 发布；fengxi177 图谱的本地结构清洗与隔离 smoke

## 药典

```cypher
MATCH (n)
WHERE n.导入范围键 = '抱抱脸:中药药典2022'
   OR '抱抱脸:中药药典2022' IN coalesce(n.导入范围键列表, [])
RETURN count(n)
```

期望：约 `3427`（原 3431；`干/成/淫/湿疹、湿疮` 四个近重复词条并入已有节点）。条目终态 605/605，`failures.jsonl` 空。`人参.来源=2022年中药药典`，`人参.拉丁名=GINSENGRADIXETRHIZOMA`。

图存储口径（2026-08-17）：标签、关系类型、属性键均为中文；`CALL db.propertyKeys()` 英文键为 `0`。近重复只合标点/OCR，贮藏条件差不合。全图 `4175` 节点 / `12575` 边。

## 苏子阳

```cypher
MATCH (n)
WHERE n.导入源 = '道医苏子阳'
   OR '道医苏子阳' IN coalesce(n.导入源列表, [])
RETURN count(n)
```

期望：触达节点含苏子阳溯源（导入时 923；药典补导后同名节点会同时带两个 source id）。边：

```cypher
MATCH ()-[r]->()
WHERE r.导入范围键 = '人工:白草知识:道医苏子阳'
RETURN count(r)
```

期望：`3355`。

## 查询消费

```http
POST /api/v1/graph/query
{"node":{"label":"方剂"},"limit":5}
```

期望：200，节点 `labels` 含 `方剂`。Workbench `/graph` 查询下拉含方剂、医案、穴位、治法；关系下拉含组成药材、使用方剂、取用穴位、采用治法、记载于医案。

契约测试：`packages/api/tests/api/test_graph_routes.py::TestGraphQuery::test_query_graph_accepts_formula_and_case_filters`

## fengxi177 图谱（local only）

- 输入：药材 3,335 + 方剂 16,588 = 19,923 条关系
- 输出：4,996 records；方剂 742、药材 1,117
- 边：11,445；组成药材 6,521，其中 dosage 5,784；安全来源边 436
- 完整源测试：`21 passed`（含 importer/provenance 回归），Ruff 通过
- 临时 Neo4j 真实导入：4,996 created / 11,445 edges；各关系目标 label 错误均为 0；临时容器已删除，现有图库未修改
- 上游 `license=null` 且无许可证文件，catalog 固定 `publish: false`；public Parquet 重导仍为 5,118 / 11,202

## 证据

- latest stats：`datasets/baicao-knowledge/sources/*/processed/latest/stats.json`（不进 git）
- HF：[`ticoAg/baicao-knowledge`](https://huggingface.co/datasets/ticoAg/baicao-knowledge)（public；2026-08-19 真实发布成功）
- 远端清单：12 个允许文件 + `.gitattributes`；第三源只含 SOURCE/VIEW 元数据，无其 records；无原文、JSONL、`processed/latest`、work 或 exports
- 远端 Parquet 直读：`records=5,118`，`edges=11,202`
- public 导出：保留 `evidence_text`；`properties_json` 不含全书字段 `raw_text`、`source_text`、`content`、`text`（2026-09-06 起；此前曾清空证据片段）
- public Viewer：匿名 `/is-valid`、`/splits`、`records`/`edges` 首行读取均返回 200；总行数 5,118 / 11,202
- 真实主链使用 `graph-zh-live.json` 导入 4,179 节点 / 12,673 关系；fresh-volume integration `4 passed, 293 deselected`
