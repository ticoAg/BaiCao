# Neo4j neomodel 渐进迁移 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `packages/api/` 中渐进引入 `neomodel 6.x`，统一 Neo4j 连接管理，消除高重复关系创建逻辑，并在不改动 API 契约的前提下保留复杂路径查询。

**Architecture:** 以 `app/kg/db.py` 作为 Neo4j 连接真源，统一通过 `neomodel.adb` 执行查询。声明式节点与关系模型承接简单 CRUD / 关系创建；复杂路径查询和 metadata / provenance 的复杂查询继续保留手写 Cypher，但经统一连接层执行。外部 `schemas`、路由与返回结构保持兼容，尤其保留现有 `id` 契约。

**Tech Stack:** FastAPI、Neo4j 5+/6 driver、`neomodel`、pytest、ruff、ty

---

### Task 1: 建立依赖与连接真源

**Files:**
- Modify: `packages/api/pyproject.toml`
- Modify: `packages/api/app/main.py`
- Create: `packages/api/app/kg/db.py`
- Test: `packages/api/tests/unit/kg/test_db.py`

- [ ] **Step 1: 写连接初始化失败测试**

```python
import pytest
from unittest.mock import AsyncMock, patch

from app.kg.db import build_neomodel_url, init_kg_db


def test_build_neomodel_url_includes_auth():
    assert build_neomodel_url(
        "bolt://localhost:7687",
        "neo4j",
        "password",
    ) == "bolt://neo4j:password@localhost:7687"


@pytest.mark.asyncio
async def test_init_kg_db_calls_set_connection():
    with patch("app.kg.db.adb.set_connection", new=AsyncMock()) as mock_set:
        await init_kg_db()
    mock_set.assert_awaited_once()
```

- [ ] **Step 2: 运行测试确认红灯**

Run: `uv run pytest tests/unit/kg/test_db.py -v`
Expected: FAIL，提示 `app.kg.db` 或 `init_kg_db` 尚不存在

- [ ] **Step 3: 写最小实现**

```python
from neomodel import adb

from ..core.config import get_settings


def build_neomodel_url(uri: str, user: str, password: str) -> str:
    return uri.replace("://", f"://{user}:{password}@")


async def init_kg_db() -> None:
    settings = get_settings()
    await adb.set_connection(
        build_neomodel_url(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password,
        )
    )
```

- [ ] **Step 4: 接入应用生命周期**

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_kg_db()
    yield
```

- [ ] **Step 5: 运行测试确认绿灯**

Run: `uv run pytest tests/unit/kg/test_db.py -v`
Expected: PASS


### Task 2: 建立 OGM 节点 / 关系模型

**Files:**
- Create: `packages/api/app/kg/models.py`
- Test: `packages/api/tests/unit/kg/test_models.py`

- [ ] **Step 1: 写模型映射失败测试**

```python
from app.kg.models import NODE_MODEL_MAP, REL_TYPE_TO_ATTR


def test_node_model_map_covers_runtime_labels():
    for label in [
        "Herb",
        "Component",
        "Variant",
        "Process",
        "Trait",
        "TimePoint",
        "Efficacy",
        "Flavor",
        "Meridian",
        "Disease",
        "Source",
        "Evidence",
    ]:
        assert label in NODE_MODEL_MAP


def test_rel_type_mapping_covers_runtime_links():
    assert REL_TYPE_TO_ATTR["HAS_EFFICACY"] == "has_efficacy"
    assert REL_TYPE_TO_ATTR["DERIVED_FROM"] == "derived_from"
```

- [ ] **Step 2: 运行测试确认红灯**

Run: `uv run pytest tests/unit/kg/test_models.py -v`
Expected: FAIL，提示 `app.kg.models` 或映射不存在

- [ ] **Step 3: 写最小声明式模型**

```python
class GraphNodeBase(AsyncStructuredNode):
    id = StringProperty(required=True, unique_index=True, db_property="id")
    name = StringProperty(required=True, unique_index=True)
    source = StringProperty()
    status = StringProperty(default="pending")
```

并扩展：

- `HerbNode`
- `ComponentNode`
- `VariantNode`
- `ProcessNode`
- `TraitNode`
- `TimePointNode`
- `EfficacyNode`
- `FlavorNode`
- `MeridianNode`
- `DiseaseNode`
- `SourceNode`
- `EvidenceNode`

以及最少必要的关系属性模型：

- `BaseRel`
- `ContainsRel`
- `ProcessedByRel`
- `HasTraitRel`
- `StoredForRel`
- `DerivedFromRel`
- `SimilarToRel`

- [ ] **Step 4: 建立模型注册表**

```python
NODE_MODEL_MAP = {"Herb": HerbNode, ...}
REL_TYPE_TO_ATTR = {"HAS_EFFICACY": "has_efficacy", ...}
```

- [ ] **Step 5: 运行测试确认绿灯**

Run: `uv run pytest tests/unit/kg/test_models.py -v`
Expected: PASS


### Task 3: GraphService 切到统一连接与通用关系创建

**Files:**
- Modify: `packages/api/app/kg/graph_service.py`
- Test: `packages/api/tests/unit/kg/test_graph_service.py`
- Test: `packages/api/tests/kg/test_graph_service.py`

- [ ] **Step 1: 写关系抽象失败测试**

```python
@pytest.mark.asyncio
async def test_create_relationship_uses_model_map_and_manager():
    service = GraphService()
    from_node = MagicMock()
    rel_manager = MagicMock()
    rel_manager.aconnect = AsyncMock(return_value={"status": "pending"})
    from_node.has_efficacy = rel_manager
    to_node = MagicMock()

    with patch("app.kg.graph_service.NODE_MODEL_MAP") as model_map:
        model_map.__getitem__.side_effect = {
            "Herb": MagicMock(nodes=MagicMock(aget=AsyncMock(return_value=from_node))),
            "Efficacy": MagicMock(nodes=MagicMock(aget=AsyncMock(return_value=to_node))),
        }.__getitem__
        result = await service.create_relationship("Herb", "当归", "Efficacy", "补血", "HAS_EFFICACY")

    assert result["status"] == "pending"
    rel_manager.aconnect.assert_awaited_once()
```

- [ ] **Step 2: 运行测试确认红灯**

Run: `uv run pytest tests/unit/kg/test_graph_service.py -k create_relationship -v`
Expected: FAIL，提示 `create_relationship` 不存在

- [ ] **Step 3: 实现统一关系创建**

实现点：

- 删除 `driver/connect/close/ensure_connected`
- 引入 `adb`, `NODE_MODEL_MAP`, `REL_TYPE_TO_ATTR`
- 新增 `_default_relationship_props()`
- 新增 `create_relationship(...)`
- 将 16 个 `link_xxx` 收缩为 1–3 行调用

- [ ] **Step 4: 将简单查询切到 `adb.cypher_query`**

包括：

- `create_node`
- `get_node`
- `get_node_by_name`
- `expand_node_graph`
- `get_herb_graph`
- `query_graph`
- `search_nodes`
- `find_path`
- `verify_node`
- `verify_relationship`

要求：

- 保持现有返回结构
- 保持复杂路径查询为手写 Cypher
- 不再自行管理 driver session

- [ ] **Step 5: 运行图谱服务单测**

Run: `uv run pytest tests/unit/kg/test_graph_service.py tests/kg/test_graph_service.py -v`
Expected: PASS


### Task 4: metadata / provenance 切到 adb

**Files:**
- Modify: `packages/api/app/kg/graph_metadata_service.py`
- Modify: `packages/api/app/provenance/__init__.py`
- Test: `packages/api/tests/unit/provenance/test_provenance.py`
- Test: `packages/api/tests/api/test_provenance_routes.py`

- [ ] **Step 1: 写统一连接失败测试**

```python
@pytest.mark.asyncio
async def test_graph_metadata_summary_uses_adb():
    svc = GraphMetadataService()
    with patch("app.kg.graph_metadata_service.adb.cypher_query", new=AsyncMock(return_value=([[]], None))):
        await svc.get_summary()
```

```python
@pytest.mark.asyncio
async def test_create_evidence_uses_adb():
    svc = ProvenanceService()
    with patch("app.provenance.adb.cypher_query", new=AsyncMock()) as mock_query:
        await svc.create_evidence("内容", "来源")
    mock_query.assert_awaited()
```

- [ ] **Step 2: 运行测试确认红灯**

Run: `uv run pytest tests/unit/provenance/test_provenance.py -k adb -v`
Expected: FAIL，提示仍依赖旧 driver 模式

- [ ] **Step 3: 实现 adb 查询适配**

实现点：

- 移除 `driver/connect/close/ensure_connected`
- 新增 `cypher_rows()` / `cypher_single()` 类 helper
- 将 metadata 和 provenance 的所有查询改为 `adb.cypher_query`
- 保持原有字典映射和 API 返回结构

- [ ] **Step 4: 运行溯源与路由测试**

Run: `uv run pytest tests/unit/provenance/test_provenance.py tests/api/test_provenance_routes.py -v`
Expected: PASS


### Task 5: 统一验证与文档收尾

**Files:**
- Modify: `packages/api/uv.lock`
- Modify: `docs/superpowers/plans/2026-03-24-neomodel-migration.md`

- [ ] **Step 1: 安装依赖并刷新锁文件**

Run: `uv lock`
Expected: `uv.lock` 纳入 `neomodel` 及其依赖

- [ ] **Step 2: 运行最小静态检查**

Run: `uv run ruff check app tests`
Expected: PASS

- [ ] **Step 3: 运行目标测试集**

Run: `uv run pytest tests/unit/kg/test_db.py tests/unit/kg/test_models.py tests/unit/kg/test_graph_service.py tests/kg/test_graph_service.py tests/unit/provenance/test_provenance.py tests/api/test_graph_routes.py tests/api/test_provenance_routes.py -v`
Expected: PASS

- [ ] **Step 4: 运行 API 最低验证**

Run: `uv run pytest tests/contract/test_routes.py tests/contract/test_graph_workbench_schema.py -v`
Expected: PASS

- [ ] **Step 5: 追加未完成验证说明**

若未执行：

- `uv run ty check`
- `curl "http://localhost:8000/api/v1/graph/meta/relationship-types?limit=20&offset=0"`
- `curl "http://localhost:8000/api/v1/graph/herb/当归"`
- `uv run pytest tests/ -v`

则在最终交付中明确写出原因与复现命令。
