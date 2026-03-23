<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "graph", "neo4j"]
summary: 图谱查询工作区主链路验收
audience: developer
---
-->

# 图谱查询主链路验收

## 1. 概述

- 功能名称：图谱查询工作区主链路
- 验收目标：验证 `/graph` 进入画布优先工作区，高级查询通过抽屉唤出并返回子图结果，且 `/graph/人参` 仍保持默认药材图谱入口
- 对应需求：可信图谱探索 / 图谱高级查询工作区
- 对应计划：`docs/superpowers/plans/2026-03-21-graph-page-query-workspace.md`
- 当前版本 / 日期：graph workspace / 2026-03-21

## 2. 验收范围

### 包含

- `/graph` 直接进入图谱查询工作区，而不是先经过搜索页
- 通过左上查询入口卡打开查询抽屉，输入名称 / 属性 / 边过滤条件后返回图谱子图结果
- `/graph/人参` 继续按药材详情模式加载默认图谱
- 查询入口卡展示当前图谱或当前查询摘要
- 右下浮卡展示节点 / 边详情，左下悬浮图例始终可见
- 双击节点可展开一跳邻居，再次双击同一节点可收起本次增量子图
- 后端同时保留 `GET /api/v1/graph/herb/{name}`、`POST /api/v1/graph/query` 与 `GET /api/v1/graph/node/{node_id}/expand` 三条主链路

### 不包含

- 浏览器内手工点击节点 / 边后的交互细节回归
- 大图谱性能、布局质量和动画体验
- 路径查询、权限控制与非主链路图谱接口

## 3. 前置条件

### 环境

- 后端已运行在 `http://localhost:8000`，并加载当前 demo 图谱数据
- demo 数据至少包含药材“人参”、`HAS_EFFICACY` 关系，以及 `category` 含“补气”的节点属性
- `packages/web` 依赖已安装，可执行 Vitest 与 TypeScript typecheck
- 如需做人工浏览器验收，前端 dev server 需运行在 `http://localhost:3000`

### 启动 / 准备命令

```bash
pnpm --dir packages/web exec vp dev
```

补充说明：

- 本轮 Task 5 仅执行 API + Web 自动化最小验证，不包含浏览器人工操作

## 4. 验收步骤

### Step 1

- 操作：打开图谱工作区入口
- 页面入口：`http://localhost:3000/graph`

### Step 2

- 操作：点击左上“打开查询器”，在查询抽屉中填写高级查询条件并提交
- 推荐输入：
  - 节点名称包含：`人参`
  - 属性键：`category`
  - 属性值包含：`补气`
  - 关系类型：`HAS_EFFICACY`
  - 深度：`2`

### Step 3

- 操作：验证默认药材图谱入口仍可用
- 页面入口：`http://localhost:3000/graph/人参`

### Step 4

- 操作：验证后端药材图谱接口
- 命令：

```bash
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
```

### Step 5

- 操作：验证后端高级查询接口
- 命令：

```bash
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","label":"Herb"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' | python3 -m json.tool
```

### Step 6

- 操作：补充 spot-check，确认属性过滤在当前 demo 数据下可命中
- 命令：

```bash
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","property_key":"category","property_value_contains":"补气"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' | python3 -m json.tool
```

### Step 7

- 操作：执行 web 最小验证
- 命令：

```bash
pnpm --dir packages/web exec vp test run src/components/graph/GraphQueryPanel.test.tsx src/pages/GraphPage.test.tsx src/components/graph/NodeDetail.test.tsx src/hooks/useGraphWorkspace.test.tsx
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

### Step 8

- 操作：在 `/graph/人参` 中双击中心节点“人参”，再双击一次
- 页面入口：`http://localhost:3000/graph/人参`

## 5. 期望结果

### Step 1 预期

- `/graph` 不需要 `:name` 参数即可进入工作区
- 页面默认先看到图谱画布和左上查询入口卡，而不是常驻左侧表单
- 工作区容器使用整屏高度布局，高度为 `calc(100vh - 64px)`

### Step 2 预期

- 提交后工作区切换到“当前查询”模式
- 中间画布渲染命中子图，右下浮卡仍可查看节点 / 边详情
- 左上查询入口卡显示命中节点数和过滤条件摘要
- 当同时输入名称 / 属性 / 边条件时，摘要中应体现对应过滤项

### Step 3 预期

- `/graph/人参` 仍会加载默认药材图谱，而不是停留在空白工作区
- 左上查询入口卡体现“当前图谱 / 人参”语义

### Step 4 预期

- `GET /api/v1/graph/herb/人参?depth=1` 返回 `center`、`nodes`、`edges`
- `center.name` 为“人参”
- 返回结果可作为 `/graph/人参` 的默认药材图谱数据源

### Step 5 预期

- `POST /api/v1/graph/query` 返回 `summary` 与 `graph`
- `summary.mode` 为 `advanced-query`
- `summary.matched_nodes`、`summary.matched_edges` 与 `summary.active_filters` 均有值
- `graph.center` 可为空，`graph.nodes` 与 `graph.edges` 承载命中子图

### Step 6 预期

- 属性过滤的查询仍可返回图谱结果
- `active_filters` 中出现“分类包含: 补气”之类的属性过滤摘要

### Step 7 预期

- 指定的 web 测试文件全部通过
- `packages/web` typecheck 与 build 退出码均为 0

### Step 8 预期

- 第一次双击节点时，画布会请求并合并该节点的一跳关联节点与关系
- 第二次双击同一节点时，只收起该节点本次展开出来的增量子图，不影响基础图谱

## 6. 证据记录

### 实现证据

- `packages/api/app/api/graph.py:11`
- `packages/api/app/api/graph.py:17`
- `packages/api/app/kg/graph_service.py:1053`
- `packages/web/src/hooks/useGraphWorkspace.ts:22`
- `packages/web/src/pages/GraphPage.tsx:1`
- `packages/web/src/components/graph/GraphQueryPanel.tsx:1`
- `packages/web/src/components/graph/NodeDetail.tsx:1`
- `packages/web/src/components/graph/EdgeDetail.tsx:1`
- `packages/web/src/pages/GraphPage.test.tsx:1`
- `packages/web/src/components/graph/GraphQueryPanel.test.tsx:1`
- `packages/web/src/components/graph/NodeDetail.test.tsx:1`
- `packages/web/src/hooks/useGraphWorkspace.test.tsx:122`

### 运行证据

执行日期：`2026-03-21`

```bash
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","label":"Herb"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' | python3 -m json.tool
curl -sS -X POST 'http://localhost:8000/api/v1/graph/query' -H 'Content-Type: application/json' -d '{"node":{"name_contains":"人参","property_key":"category","property_value_contains":"补气"},"edge":{"rel_type":"HAS_EFFICACY"},"depth":2,"limit":20}' | python3 -m json.tool
pnpm --dir packages/web exec vp test run src/components/graph/GraphQueryPanel.test.tsx src/pages/GraphPage.test.tsx src/components/graph/NodeDetail.test.tsx src/hooks/useGraphWorkspace.test.tsx
pnpm --dir packages/web typecheck
pnpm --dir packages/web exec vp build
```

### 结果证据

- 药材图谱接口返回 `center / nodes / edges`，其中 `center.name = 人参`；本次返回 `12` 个节点、`11` 条边
- 高级查询接口返回 `summary / graph`；本次 `name + label + edge` 查询返回 `matched_nodes = 1`、`matched_edges = 4`，`active_filters` 为“名称包含: 人参 / 节点类型: 药材 / 关系类型: 功效”
- 属性 spot-check 查询同样返回 `matched_nodes = 1`、`matched_edges = 4`，且 `active_filters` 包含“分类包含: 补气”
- `pnpm --dir packages/web exec vp test run ...` 结果为 `3 passed` / `9 passed`
- `pnpm --dir packages/web typecheck` 退出码为 `0`
- 本轮未执行浏览器人工验收，因此本次证据仅覆盖 API 返回与 Web 自动化最小验证

## 7. 风险与未覆盖项

- 本轮未直接在浏览器中操作 `/graph` 与 `/graph/人参`，因此画布高度、点击交互和详情面板联动未做人工复核
- 当前结果计数依赖 demo 数据集 `demo-20260320`；如样例数据变更，节点数、边数和摘要内容会随之变化
- 未覆盖空结果查询、超大图谱性能、路径查询和权限相关场景

## 8. 结论

- 结果：`risk`
- 结论一句话：API 与 Web 自动化最小验证已证明图谱工作区主链路接通，但浏览器人工验收尚未在本轮执行
- 当前结论边界：本结论覆盖 `/api/v1/graph/herb/{name}`、`/api/v1/graph/query` 与指定 Web tests / typecheck，不覆盖浏览器人工操作结果
