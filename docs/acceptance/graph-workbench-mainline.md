<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "graph", "workbench"]
summary: Graph Workbench `/graph` 主链路验收
audience: developer
---
-->

# Graph Workbench 主链路验收

## 1. 概述

- 功能名称：Graph Workbench `/graph`
- 验收目标：验证 `/graph` 已升级为三栏 Graph Workbench，能够同时展示数据库级 `Database information`、中央 D3 图谱结果视图与右侧检查器，并覆盖原图谱查询工作区主链路
- 对应 spec：[../superpowers/specs/2026-03-23-graph-workbench-design.md](../superpowers/specs/2026-03-23-graph-workbench-design.md)
- 对应 plan：[../superpowers/plans/2026-03-23-graph-workbench.md](../superpowers/plans/2026-03-23-graph-workbench.md)
- 当前版本 / 日期：graph workbench / 2026-03-24

## 2. 验收范围

### 包含

- `/graph` 页面三栏工作台布局
- 左侧 `Database information`
- 中央 D3 图谱结果视图
- 右侧 `Overview / Details` 检查器
- `/api/v1/graph/meta/*` 元数据接口
- `/api/v1/graph/herb/{name}` 与 `POST /api/v1/graph/query` 返回 `scene`
- 查询入口、query summary 与属性 / 关系过滤高级查询
- 图中节点双击展开与再次双击收起增量子图

### 不包含

- 完整 Cypher workbench
- 聊天页复用
- 数据库写操作

## 3. 前置条件

- 后端已运行在 `http://localhost:8000`
- 前端 dev server 已运行在 `http://localhost:3000`
- Neo4j 中已加载样例图谱数据，至少包含“人参”

## 4. 验收步骤

### Step 1

- 操作：打开 `http://localhost:3000/graph`

### Step 2

- 操作：确认左侧出现 `Database information`，中央出现结果区，右侧出现 `Overview`

### Step 3

- 操作：打开查询器并提交一组高级查询
- 推荐输入：
  - 节点名称包含：`人参`
  - 属性键：`category`
  - 属性值包含：`补气`
  - 关系类型：`HAS_EFFICACY`
  - 深度：`2`

### Step 4

- 操作：打开 `http://localhost:3000/graph/人参`

### Step 5

- 操作：点击左侧某个 label，例如 `Herb`

### Step 6

- 操作：点击图谱中的节点或关系

### Step 7

- 操作：在 `/graph/人参` 中双击中心节点，再双击一次

### Step 8

- 操作：验证元数据接口
- 命令：

```bash
curl -sS http://localhost:8000/api/v1/graph/meta/summary | python3 -m json.tool
curl -sS 'http://localhost:8000/api/v1/graph/meta/labels?limit=20' | python3 -m json.tool
curl -sS http://localhost:8000/api/v1/graph/meta/schema | python3 -m json.tool
```

### Step 9

- 操作：验证图谱结果接口包含 `scene`
- 命令：

```bash
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","label":"Herb"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' | python3 -m json.tool
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","property_key":"category","property_value_contains":"补气"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' | python3 -m json.tool
```

### Step 10

- 操作：执行 Web 最小验证
- 命令：

```bash
pnpm run test:web
pnpm --dir packages/web typecheck
```

## 5. 期望结果

### Step 1-4 预期

- `/graph` 可直接进入 Graph Workbench
- 左侧为 `Database information`
- 中央为 D3 图谱结果视图
- 右侧为检查器，默认显示 `Overview`
- 提交高级查询后，工作区切换到 query result 语义
- query summary 会体现名称 / 属性 / 关系过滤摘要

### Step 5-6 预期

- 点击 label 后不会清空当前图谱
- 当前图谱中不匹配的节点会被弱化
- 点击节点后右侧切换到节点详情
- 点击关系后右侧切换到关系详情

### Step 7-8 预期

- `/graph/人参` 仍会加载默认 herb graph，而不是停在空工作台
- 第一次双击节点时，请求并合并该节点的一跳邻居
- 第二次双击同一节点时，只收起该节点本次展开出来的增量子图

### Step 8 预期

- `/graph/meta/summary` 返回数据库级计数
- `/graph/meta/labels` 返回 `items + total`
- `/graph/meta/schema` 返回 `indexes + constraints`

### Step 9 预期

- herb graph 与 advanced query 响应都包含 `scene`
- `scene` 至少包含：
  - `truncated`
  - `node_limit_hit`
  - `relationship_limit_hit`
  - `info_message`
- 高级查询响应返回 `summary` 与 `graph`
- 属性过滤查询返回的 `active_filters` 中体现“分类包含: 补气”之类摘要

### Step 10 预期

- `pnpm run test:web` 通过
- `packages/web` typecheck 退出码为 `0`

## 6. 证据记录

### 实现证据

- `packages/api/app/api/graph.py`
- `packages/api/app/kg/graph_metadata_service.py`
- `packages/api/app/kg/graph_service.py`
- `packages/api/app/kg/db.py`
- `packages/api/app/kg/models.py`
- `packages/web/src/hooks/useGraphWorkbenchPage.ts`
- `packages/web/src/pages/GraphPage.tsx`
- `packages/web/src/components/graph/GraphMetadataSidebar.tsx`
- `packages/web/src/components/graph/GraphCanvasWorkspace.tsx`
- `packages/web/src/components/graph/GraphToolbar.tsx`
- `packages/web/src/components/graph/MiniGraphCanvas.tsx`
- `packages/web/src/components/graph/GraphInspectorPanel.tsx`
- `packages/web/src/components/workbench/frames/GraphResultFrame.tsx`
- `packages/web/src/lib/graph-viz/Visualization.ts`
- `packages/web/src/components/graph/GraphQueryPanel.tsx`
- `packages/web/src/hooks/useGraphWorkspace.test.tsx`
- `packages/web/src/pages/GraphPage.test.tsx`

### 运行证据

```bash
./scripts/test_api.sh
pnpm run test:web
pnpm --dir packages/web typecheck
GitHub Actions: ci-fast run 23497811413
```

执行日期：`2026-03-25`

### 结果证据

- `uv run pytest tests/unit/kg/test_db.py tests/api/test_graph_routes.py -q` 结果为 `15 passed`
- `pnpm --dir packages/web test --run src/pages/GraphPage.test.tsx` 结果为 `3 passed`
- `pnpm --dir packages/web typecheck` 退出码为 `0`
- `curl http://127.0.0.1:8000/api/v1/graph/meta/summary`、`/meta/labels`、`/meta/schema` 与 `/graph/herb/人参?depth=1` 均返回有效 JSON
- Playwright 页面事实检查显示 `/graph/人参` 页面正文同时包含：
  - `Database information`
  - `当前图谱12 个节点11 条关系`
  - `Overview`
  - `图谱概览`
  - `Component7 | Efficacy10 | Flavor5 | Herb3 ...`
- 本轮 spot-check 额外暴露并修复了 `packages/api/app/kg/db.py` 中 `neomodel.adb` 连接可能回落到默认 `7687` 的问题，现已由 `ensure_kg_db()` 在查询前兜底

## 7. 风险与未覆盖项

- 当前图谱视图已切到 D3 自绘实现，但仍未追求与 Neo4j Browser 的全部交互细节完全对齐
- 本轮补的是最小页面事实检查，不是完整视觉回归截图集

## 8. 结论

- 结果：`pass`
- 结论一句话：Graph Workbench 的协议、后端接口、D3 结果视图、本地接口 spot-check 与页面事实检查已形成可复现闭环
