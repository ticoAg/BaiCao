<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "graph", "neo4j"]
summary: 图谱查询主链路验收
audience: developer
---
-->

# 图谱查询主链路验收

## 1. 概述

- 功能名称：图谱查询主链路
- 验收目标：验证首页入口、搜索、图谱详情和后端图谱接口形成完整闭环
- 对应需求：可信图谱探索
- 对应任务：`IMPL-004`、`IMPL-005`
- 当前版本 / 日期：MVP / 2026-03-20

## 2. 验收范围

### 包含

- 搜索页搜索药材
- 跳转图谱详情页
- 图谱详情页展示节点与关系
- 图谱 API 返回完整中心节点、节点列表和边列表

### 不包含

- 复杂路径查询
- 图谱布局动画质量
- 图数据库权限控制

## 3. 前置条件

### 环境

- 操作系统：macOS / Linux
- 运行方式：本地 tmux demo
- 依赖服务：PostgreSQL、Neo4j、Redis、FastAPI、Vite
- 样例数据：`scripts/seed_demo_data.py`

### 启动命令

```bash
pnpm run demo
pnpm run test:e2e
```

## 4. 验收步骤

### Step 1

- 操作：打开首页并进入搜索页
- 命令 / 页面入口：`http://localhost:3000`

### Step 2

- 操作：搜索“人参”
- 命令 / 页面入口：搜索页输入框

### Step 3

- 操作：点击搜索结果，进入图谱页
- 命令 / 页面入口：`/graph/人参`

### Step 4

- 操作：验证后端图谱接口
- 命令 / 页面入口：

```bash
curl -sS 'http://localhost:8000/api/v1/graph/herb/%E4%BA%BA%E5%8F%82?depth=1' | python3 -m json.tool
```

## 5. 期望结果

### Step 1 预期

- 首页可见“知识搜索”和“图谱浏览”

### Step 2 预期

- 搜索结果中出现“人参”

### Step 3 预期

- 图谱页显示“人参 的知识图谱”
- 页面可见节点列表、关系列表和节点详情卡片

### Step 4 预期

- 接口返回 `center`、`nodes`、`edges`
- `center.name` 为“人参”
- `edges` 内包含 `rel_type`

## 6. 证据记录

### 实现证据

- `packages/api/app/api/graph.py:10`
- `packages/api/app/kg/graph_service.py:596`
- `packages/web/src/pages/SearchPage.tsx:17`
- `packages/web/src/pages/GraphPage.tsx:26`

### 运行证据

```bash
pnpm run demo
pnpm exec playwright test tests/e2e/mainline.spec.ts
```

### 结果证据

- 页面可见结果：搜索“人参”后可进入图谱页
- 接口返回摘要：`center.name = 人参`
- 图谱结果：节点和关系均存在

## 7. 风险与未覆盖项

- 暂未覆盖复杂路径查询和大图谱性能

## 8. 结论

- 结果：`pass`
- 结论一句话：图谱查询主链路在 demo 数据下可复现、可浏览、可验证
- 后续动作：补充路径查询与真实大数据量场景验收
