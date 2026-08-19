<!--
---
doc_kind: architecture
status: stable
tags: ["knowledge-graph", "frontend", "neo4j", "workbench"]
summary: "`/graph` Graph Workbench 的稳定架构口径"
audience: developer
---
-->

# Graph Workbench 架构

## 1. 目标与定位

`/graph` 现在的统一定位不是“药材图谱详情页”，而是 BaiCao 的 Graph Workbench。

它面向两类稳定场景：

- 以数据库视角浏览当前图谱与元数据
- 以业务视角执行 herb graph、advanced query 与局部展开

这意味着 `/graph` 同时承担两层职责：

- `Database information`：展示数据库级 labels、relationship types、property keys、indexes、constraints 和计数
- `Graph result view`：展示当前 herb graph、advanced query 或 expand graph 的子图结果

## 2. 当前稳定结构

Graph Workbench 采用三栏稳定结构：

1. 左侧 `Database information`
2. 中央 D3 图谱结果视图
3. 右侧 `Overview / Details` 检查器

页面主路径由 [packages/web/src/pages/GraphPage.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/pages/GraphPage.tsx) 承接。

### 2.1 左侧：Database information

左侧展示数据库级元数据，而不是当前子图统计。

当前稳定来源：

- `GET /api/v1/graph/meta/summary`
- `GET /api/v1/graph/meta/labels`
- `GET /api/v1/graph/meta/relationship-types`
- `GET /api/v1/graph/meta/property-keys`
- `GET /api/v1/graph/meta/schema`

对应实现位于：

- [packages/api/app/kg/graph_metadata_service.py](/Users/ticoag/Documents/myws/BaiCao/packages/api/app/kg/graph_metadata_service.py)
- [packages/web/src/components/graph/GraphMetadataSidebar.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/GraphMetadataSidebar.tsx)

### 2.2 中央：Graph result view

中央区域使用仓库内自维护的 D3 可视化实现，而不是继续依赖旧图库结果壳层。

当前稳定职责：

- 渲染 herb graph / query graph / expand graph 的统一视图
- 维护缩放、平移、适配视图和空白点击清空选中
- 保持节点 / 关系选中、高亮和弱化行为一致
- 支持局部展开与 scene 提示

对应实现位于：

- [packages/web/src/components/graph/GraphCanvasWorkspace.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/GraphCanvasWorkspace.tsx)
- [packages/web/src/lib/graph-viz/Visualization.ts](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/lib/graph-viz/Visualization.ts)
- [packages/web/src/components/graph/GraphToolbar.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/GraphToolbar.tsx)
- [packages/web/src/components/graph/MiniGraphCanvas.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/MiniGraphCanvas.tsx)

### 2.3 右侧：Inspector

右侧检查器有两个稳定模式：

- `Overview`
- `Details`

它负责把“当前图谱整体信息”和“当前选中节点 / 关系详情”分开，而不是把所有信息都塞进画布浮层。

对应实现位于：

- [packages/web/src/components/graph/GraphInspectorPanel.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/GraphInspectorPanel.tsx)
- [packages/web/src/components/graph/NodeDetail.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/NodeDetail.tsx)
- [packages/web/src/components/graph/EdgeDetail.tsx](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/components/graph/EdgeDetail.tsx)

## 3. 后端协议边界

Graph Workbench 依赖两类后端事实。

### 3.1 DatabaseMeta

数据库级元数据只服务左侧栏，不和当前子图结果混在同一个响应里。

这样做的目的：

- 元数据刷新不会拖动中央画布抖动
- `/graph/meta/*` 可以独立失败或重试
- 页面状态能清晰拆成“数据库级事实”和“当前图谱事实”

### 3.2 GraphScene

当前图谱结果统一携带 `scene`，用于表达结果是否被截断、是否触发 node / relationship limit，以及当前提示信息。

当前稳定来源：

- `GET /api/v1/graph/herb/{name}`
- `POST /api/v1/graph/query`
- `GET /api/v1/graph/node/{node_id}/expand`

对应实现位于：

- [packages/api/app/kg/graph_service.py](/Users/ticoag/Documents/myws/BaiCao/packages/api/app/kg/graph_service.py)
- [packages/web/src/hooks/useGraphWorkspace.ts](/Users/ticoag/Documents/myws/BaiCao/packages/web/src/hooks/useGraphWorkspace.ts)

## 4. Neo4j 运行时口径

Graph Workbench 当前 Neo4j 访问口径已经统一到 `neomodel` 连接层：

- 连接真源：`packages/api/app/kg/db.py`
- 运行时单例：`neomodel.adb`
- 声明式模型：`packages/api/app/kg/models.py`

稳定规则：

- 声明式节点 / 简单关系创建优先走 `neomodel`
- 复杂路径查询仍允许保留手写 Cypher
- 手写 Cypher 统一经 `adb.cypher_query(...)` 执行
- metadata 与 provenance 不再各自维护独立 driver 生命周期

这条边界的目标不是“去掉所有 Cypher”，而是让连接管理、简单关系创建和复杂查询执行路径各自有明确归属。

## 5. 前端状态分层

前端当前采用两层状态：

- 页面级编排与远端数据：`useGraphWorkbenchPage`、`useGraphWorkspace`
- 组件级展示与交互：sidebar、canvas、inspector、toolbar

稳定原则：

- 远端协议与本地 view model 在边界处适配一次
- 中央画布不重复定义数据库级元数据
- `scene` 与 `graphData` 分开暴露，不混成一个“万能 graph 对象”

## 6. 已完成与未完成边界

### 已完成

- `/graph` 已升级为三栏 Graph Workbench
- 数据库级 metadata 接口已落地
- D3 图谱结果视图已替代旧结果壳层
- `scene` 已成为图谱结果稳定契约的一部分
- Neo4j 连接管理已统一到 `neomodel.adb`
- 浏览器页面事实检查与本地 API spot-check 已补齐

### 仍未完成

- 与 Neo4j Browser 更细的交互 parity
- 完整 Cypher workbench / 写操作 / 数据库管理能力

## 7. 相关文档

- [system-overview.md](system-overview.md)
- [data-model.md](data-model.md)
- [../acceptance/graph-workbench-mainline.md](../acceptance/graph-workbench-mainline.md)
- [../superpowers/specs/archive/2026-03-23-graph-workbench-design.md](../superpowers/specs/archive/2026-03-23-graph-workbench-design.md)
- [../superpowers/plans/archive/2026-03-23-graph-workbench.md](../superpowers/plans/archive/2026-03-23-graph-workbench.md)
