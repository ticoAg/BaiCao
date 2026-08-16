# Chinese Graph Relations Breaking Migration Implementation Plan

> **Status:** done（2026-04-01，已 merge）。`EdgeType` 中文真源已落地。下方 checkbox 是历史拆解，不要再执行。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将全仓图谱关系枚举、共享类型、API/Web 合同与 Neo4j 底层关系类型一次性迁移为中文真源。

**Architecture:** 先在 `knowledge_model` 中建立完整的中文关系真源与 Neo4j 标签/关系映射，再把 `shared`、`api`、`web` 全部切到中文关系字面量，最后执行 Neo4j 模型、种子数据、导入样例和迁移脚本的底层中文化。整个迁移是明确的 breaking change，不保留中英文兼容层。

**Tech Stack:** Python, TypeScript, Pydantic, pytest, neomodel, Neo4j/Cypher, pnpm

---

### Task 1: 建立中文关系真源与映射 SSOT

**Files:**
- Modify: `packages/knowledge_model/knowledge_model/constants.py`
- Modify: `packages/knowledge_model/knowledge_model/labels.py`
- Test: `packages/knowledge_model/tests/test_constants.py`

- [ ] **Step 1: 写失败测试，要求 `EdgeType` 与映射全面中文化**

在 `packages/knowledge_model/tests/test_constants.py` 增加断言：

```python
def test_edge_type_uses_chinese_literals():
    assert EdgeType.CONTAINS == "包含成分"
    assert EdgeType.HAS_EFFICACY == "具有功效"
    assert EdgeType.HAS_FLAVOR == "具有性味"
    assert EdgeType.ENTERS_MERIDIAN == "归于经脉"
    assert EdgeType.TREATS == "治疗病证"


def test_edge_type_has_neo4j_relation_mapping():
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.CONTAINS] == "CONTAINS"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.HAS_EFFICACY] == "HAS_EFFICACY"
```

- [ ] **Step 2: 跑测试确认失败**

Run:

```bash
cd packages/knowledge_model
uv run --with pytest pytest tests/test_constants.py -q
```

Expected: 至少一条断言失败，因为当前 `EdgeType` 仍有英文值，且映射表不存在。

- [ ] **Step 3: 最小实现中文关系真源**

在 `packages/knowledge_model/knowledge_model/constants.py`：
- 将 `EdgeType` 的值统一改为中文关系值
- 增加 `EDGE_TYPE_TO_NEO4J_REL`
- 增加 `NEO4J_REL_TO_EDGE_TYPE`
- 增加 `parse_edge_type()` 等辅助函数

在 `packages/knowledge_model/knowledge_model/labels.py`：
- 让 `EDGE_TYPE_LABELS` 与 `EdgeType` 真源一致，不再作为另一套语义来源

- [ ] **Step 4: 跑知识模型测试确认通过**

Run:

```bash
cd packages/knowledge_model
uv run --with pytest pytest tests/test_constants.py tests/test_schema.py -q
```

Expected: PASS


### Task 2: 迁移共享合同与前后端关系字面量

**Files:**
- Modify: `packages/shared/types/index.ts`
- Modify: `packages/api/app/models/enums.py`
- Modify: `packages/web/src/types/graph.ts`
- Modify: 关系相关消费测试文件

- [ ] **Step 1: 写失败测试，要求共享类型和 API/Web 使用中文关系字面量**

在现有测试中增加/调整断言，确保：
- `packages/shared/types/index.ts` 的 `EdgeType` 联合字面量改为中文
- API `EdgeType` 枚举值改为中文
- Web 关系筛选和显示使用中文关系值，而不是英文常量

- [ ] **Step 2: 跑最小相关测试确认失败**

Run:

```bash
cd packages/api
uv run --with pytest pytest tests/contract/test_import_record_contract.py tests/unit/kg/test_models.py -q
```

Run:

```bash
cd packages/web
pnpm test --run src/components/graph/GraphInspectorPanel.test.tsx src/pages/GraphPage.test.tsx
```

Expected: 因枚举值/字面量仍是英文而失败。

- [ ] **Step 3: 最小实现共享合同中文化**

修改：
- `packages/shared/types/index.ts`
- `packages/api/app/models/enums.py`
- `packages/web/src/types/graph.ts`

要求：
- 统一使用中文关系值
- `relTypeLabels`、过滤条件、GraphEdge 类型全部同步
- 不保留中英文并存

- [ ] **Step 4: 跑相关测试确认通过**

Run:

```bash
cd packages/api
uv run --with pytest pytest tests/contract/test_import_record_contract.py tests/unit/kg/test_models.py -q
```

Run:

```bash
cd packages/web
pnpm test --run src/components/graph/GraphInspectorPanel.test.tsx src/pages/GraphPage.test.tsx
```

Expected: PASS


### Task 3: 迁移 API 图谱服务与 Neo4j 模型关系名

**Files:**
- Modify: `packages/api/app/kg/models.py`
- Modify: `packages/api/app/kg/graph_service.py`
- Modify: `packages/api/app/schemas/graph.py`
- Modify: `packages/api/tests/kg/`
- Modify: `packages/api/tests/api/`

- [ ] **Step 1: 写失败测试，要求 API 关系查询/创建全部使用中文关系**

补或改测试断言：
- Graph 查询条件 `rel_type` 为中文值
- `REL_TYPE_TO_ATTR` 使用中文关系键
- `QUERY_REL_TYPE_DISPLAY` 与中文关系值一致

- [ ] **Step 2: 跑相关 API/KG 测试确认失败**

Run:

```bash
cd packages/api
uv run --with pytest pytest tests/kg/test_graph_service.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py -q
```

Expected: 因关系类型仍为英文而失败。

- [ ] **Step 3: 最小实现 API/KG 中文关系迁移**

修改：
- Neo4j model relationship name
- `REL_TYPE_TO_ATTR`
- graph query / response schema
- service 中所有 `EdgeType.*.value`

要求：
- API 对外、内部图谱服务、查询过滤全部改中文
- 仍通过 `knowledge_model` 映射找到 Neo4j label / relation

- [ ] **Step 4: 跑 API/KG 测试确认通过**

Run:

```bash
cd packages/api
uv run --with pytest pytest tests/kg/test_graph_service.py tests/api/test_graph_routes.py tests/unit/kg/test_models.py tests/contract/test_import_record_contract.py -q
```

Expected: PASS


### Task 4: 底层存储与导入样例中文化

**Files:**
- Modify: `packages/db/import/*.jsonl`
- Modify: `packages/db/import/*.csv`
- Modify: `packages/db/neo4j/*.cql`
- Modify: `packages/api/app/importers/*.py`
- Create: `packages/db/neo4j/migrations/2026-04-01-rename-rel-types-to-chinese.cql`

- [ ] **Step 1: 写失败测试或最小校验脚本，锁定底层关系已改中文**

至少增加一条可复现检查：
- 导入样例里的 `type` 应为中文关系值
- Neo4j seed 文件中的关系类型改为中文

- [ ] **Step 2: 跑检查确认当前失败**

Run:

```bash
rg -n 'HAS_EFFICACY|HAS_FLAVOR|ENTERS_MERIDIAN|TREATS|CONTAINS' packages/db packages/api/app/importers
```

Expected: 仍能搜到大量英文关系常量。

- [ ] **Step 3: 最小实现底层中文化**

修改导入样例、Neo4j seed 与 importer。
新增迁移脚本，负责把库中的英文关系改成中文关系，例如：

```cypher
MATCH (a)-[r:HAS_EFFICACY]->(b)
CREATE (a)-[r2:具有功效]->(b)
SET r2 = properties(r)
DELETE r
```

对每种关系类型重复这一模式。

- [ ] **Step 4: 跑底层检查确认通过**

Run:

```bash
rg -n 'HAS_EFFICACY|HAS_FLAVOR|ENTERS_MERIDIAN|TREATS|CONTAINS' packages/db packages/api/app/importers
```

Expected: 不再出现这些 legacy 英文关系名，或只存在于迁移文档说明中。


### Task 5: 迁移药典 dry-run 与跨模块验证

**Files:**
- Modify: `packages/data_ingestion/.../mapping.py`
- Modify: `packages/data_ingestion/tests/`
- Modify: `docs/acceptance/`（如需要）

- [ ] **Step 1: 写失败测试，要求药典 dry-run 输出中文关系值**

在 `packages/data_ingestion/tests/test_pharmacopoeia_mapping.py` / `test_pharmacopoeia_dry_run.py` 中锁定：
- bundle 内关系枚举值为中文真源
- `graph_bundles.jsonl` 的 `edge_types` 为中文

- [ ] **Step 2: 跑数据处理测试确认失败**

Run:

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_pharmacopoeia_cli.py tests/test_pharmacopoeia_dry_run.py tests/test_pharmacopoeia_mapping.py -q
```

Expected: 若仍有 legacy 常量依赖，应失败。

- [ ] **Step 3: 最小实现数据处理层中文真源收口**

保证 `data_ingestion` 只消费 `knowledge_model` 的中文关系真源，不再自行解释 legacy 英文关系。

- [ ] **Step 4: 跑跨模块最小验证**

Run:

```bash
cd packages/knowledge_model
uv run --with pytest pytest tests/test_constants.py tests/test_schema.py -q
```

Run:

```bash
cd packages/data_ingestion
uv run --with pytest pytest tests/test_pharmacopoeia_cli.py tests/test_pharmacopoeia_dry_run.py tests/test_pharmacopoeia_llm_contract.py tests/test_pharmacopoeia_llm_extraction.py tests/test_pharmacopoeia_parsing.py tests/test_pharmacopoeia_mapping.py -q
```

Run:

```bash
cd packages/api
uv run --with pytest pytest tests/contract/test_import_record_contract.py tests/unit/kg/test_models.py tests/kg/test_graph_service.py tests/api/test_graph_routes.py -q
```

Run:

```bash
cd packages/web
pnpm test --run src/components/graph/GraphInspectorPanel.test.tsx src/pages/GraphPage.test.tsx
```

Expected: 全部 PASS，且各层统一使用中文关系真源。

