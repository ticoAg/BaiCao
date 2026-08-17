# 验收 · 白草知识数据集

**状态：** pass（2026-08-17）  
**范围：** 药典 2022 + 道医苏子阳 v3 入图与筛选

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

## 证据

- latest stats：`datasets/baicao-knowledge/sources/*/processed/latest/stats.json`（不进 git）
- HF：`ticoAg/baicao-knowledge`（private；publish CLI 已就绪，本机实际上传受 Infisical TLS 证书过期阻塞）
