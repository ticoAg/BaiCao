<!--
---
doc_kind: acceptance
status: draft
tags: ["acceptance", "graph", "workbench"]
summary: Graph Workbench `/graph` 主链路验收
audience: developer
---
-->

# Graph Workbench 主链路验收

## 1. 概述

- 功能名称：Graph Workbench `/graph`
- 验收目标：验证 `/graph` 已升级为三栏 Graph Workbench，能够同时展示数据库级 `Database information`、中央图谱结果视图与右侧检查器
- 对应 spec：[../superpowers/specs/2026-03-23-graph-workbench-design.md](../superpowers/specs/2026-03-23-graph-workbench-design.md)
- 对应 plan：[../superpowers/plans/2026-03-23-graph-workbench.md](../superpowers/plans/2026-03-23-graph-workbench.md)
- 当前版本 / 日期：graph workbench / 2026-03-23

## 2. 验收范围

### 包含

- `/graph` 页面三栏工作台布局
- 左侧 `Database information`
- 中央图谱结果视图
- 右侧 `Overview / Details` 检查器
- `/api/v1/graph/meta/*` 元数据接口
- `/api/v1/graph/herb/{name}` 与 `POST /api/v1/graph/query` 返回 `scene`

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

- 操作：打开 `http://localhost:3000/graph/人参`

### Step 2

- 操作：确认左侧出现 `Database information`

### Step 3

- 操作：确认中央出现图谱结果视图，右侧出现 `Overview`

### Step 4

- 操作：点击左侧某个 label，例如 `Herb`

### Step 5

- 操作：点击图谱中的节点或关系

### Step 6

- 操作：验证元数据接口
- 命令：

```bash
curl -sS http://localhost:8000/api/v1/graph/meta/summary | python3 -m json.tool
curl -sS 'http://localhost:8000/api/v1/graph/meta/labels?limit=20' | python3 -m json.tool
curl -sS http://localhost:8000/api/v1/graph/meta/schema | python3 -m json.tool
```

### Step 7

- 操作：验证图谱结果接口包含 `scene`
- 命令：

```bash
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","label":"Herb"},"depth":1,"limit":20}' | python3 -m json.tool
```

## 5. 期望结果

### Step 1-3 预期

- `/graph/人参` 以三栏工作台布局呈现
- 左侧为 `Database information`
- 中央为图谱结果视图
- 右侧为检查器，默认显示 `Overview`

### Step 4 预期

- 点击 label 后不会清空当前图谱
- 当前图谱中不匹配的节点会被弱化

### Step 5 预期

- 点击节点后右侧切换到节点详情
- 点击关系后右侧切换到关系详情

### Step 6 预期

- `/graph/meta/summary` 返回数据库级计数
- `/graph/meta/labels` 返回 `items + total`
- `/graph/meta/schema` 返回 `indexes + constraints`

### Step 7 预期

- herb graph 与 advanced query 响应都包含 `scene`
- `scene` 至少包含：
  - `truncated`
  - `node_limit_hit`
  - `relationship_limit_hit`
  - `info_message`

## 6. 证据记录

### 实现证据

- `packages/api/app/api/graph.py`
- `packages/api/app/kg/graph_metadata_service.py`
- `packages/api/app/kg/graph_service.py`
- `packages/web/src/hooks/useGraphWorkbenchPage.ts`
- `packages/web/src/pages/GraphPage.tsx`
- `packages/web/src/components/graph/GraphMetadataSidebar.tsx`
- `packages/web/src/components/graph/GraphCanvasWorkspace.tsx`
- `packages/web/src/components/graph/GraphInspectorPanel.tsx`

### 运行证据

```bash
uv run pytest tests/contract/test_graph_workbench_schema.py tests/api/test_graph_routes.py tests/kg/test_graph_service.py -v
pnpm --dir packages/web exec vp test run src/hooks/useGraphWorkbenchPage.test.tsx src/pages/GraphPage.test.tsx src/components/graph/GraphMetadataSidebar.test.tsx src/components/graph/GraphInspectorPanel.test.tsx
pnpm --dir packages/web typecheck
```

## 7. 风险与未覆盖项

- 当前验收文档仍是 draft；浏览器人工交互证据尚未补截图
- 当前图谱视图只补了第一档高亮弱化，还未对齐 Neo4j Browser 的全部细节

## 8. 结论

- 结果：`risk`
- 结论一句话：Graph Workbench 主链路已形成协议、接口和页面壳层闭环，但仍需继续补齐更细的图谱交互 parity 和人工浏览器验收
