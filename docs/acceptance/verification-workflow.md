<!--
---
doc_kind: acceptance
status: stable
tags: ["acceptance", "verification", "review"]
summary: 验证申请与审核闭环验收
audience: developer
---
-->

# 验证申请与审核闭环验收

## 1. 概述

- 功能名称：验证申请与审核闭环
- 验收目标：验证前端申请、后端写库、审核通过、Neo4j 状态同步形成闭环
- 对应需求：知识可验证与状态透明
- 对应任务：`IMPL-004`、`IMPL-005`
- 当前版本 / 日期：MVP / 2026-03-20

## 2. 验收范围

### 包含

- 验证列表加载
- 创建验证申请
- 审核通过
- 审核结果同步到图谱节点

### 不包含

- 专家权限体系
- 多证据复杂评审流

## 3. 前置条件

### 环境

- 运行方式：本地 tmux demo
- 依赖服务：FastAPI、PostgreSQL、Neo4j、Vite
- 样例数据：demo_user、demo_expert、pending verifications

### 启动命令

```bash
pnpm run demo
pnpm run test:web
```

## 4. 验收步骤

### Step 1

- 操作：打开验证管理页
- 命令 / 页面入口：`http://localhost:3000/verification`

### Step 2

- 操作：创建一条新的验证申请
- 命令 / 页面入口：

```bash
curl -sS -X POST http://localhost:8000/api/v1/verifications/ \
  -H 'Content-Type: application/json' \
  -d '{"entity_type":"herb","entity_id":"aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2","claimed_value":"黄芪补气固表。","field_name":"description"}'
```

### Step 3

- 操作：审核通过
- 命令 / 页面入口：

```bash
curl -sS -X POST "http://localhost:8000/api/v1/verifications/<VERIFICATION_ID>/verify?status=verified&verdict=%E6%BC%94%E7%A4%BA%E9%80%9A%E8%BF%87"
```

### Step 4

- 操作：查询图谱节点状态
- 命令 / 页面入口：

```bash
curl -sS http://localhost:8000/api/v1/graph/node/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2 | python3 -m json.tool
```

## 5. 期望结果

### Step 1 预期

- 页面可见 pending 记录和“通过/拒绝”按钮

### Step 2 预期

- 返回新建 verification，`status = pending`
- `applicant_id` 自动填充 demo 用户

### Step 3 预期

- 返回 `status = verified`
- `verifier_id` 自动填充 demo expert

### Step 4 预期

- Neo4j 节点状态变成 `verified`
- 节点上的 `verification_id` 与审核记录一致

## 6. 证据记录

### 实现证据

- `packages/api/app/api/verification.py:112`
- `packages/api/app/api/verification.py:178`
- `packages/api/app/kg/graph_service.py:760`
- `packages/web/src/pages/VerificationPage.tsx:87`

### 运行证据

```bash
pnpm run test:web
curl -sS 'http://localhost:8000/api/v1/verifications/?status=pending'
```

### 结果证据

- 验证记录可创建、可审核
- 图谱节点状态同步为 `verified`

## 7. 风险与未覆盖项

- 暂未接入真实登录态与权限模型

## 8. 结论

- 结果：`pass`
- 结论一句话：验证申请与审核闭环已具备可复现主链路
- 后续动作：补角色权限、审计日志和关系级审核
