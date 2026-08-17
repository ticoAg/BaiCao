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

期望：`3431`。条目终态 605/605，`failures.jsonl` 空。`人参.source=huggingface`，`latin_name=GINSENGRADIXETRHIZOMA`。

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

## 证据

- latest stats：`datasets/baicao-knowledge/sources/*/processed/latest/stats.json`（不进 git）
- HF：`ticoAg/baicao-knowledge`（private）
