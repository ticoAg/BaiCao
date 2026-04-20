# 图谱 Runtime / Agent / CLI 设计

## 背景

当前仓库已经具备几条与图谱相关的基础能力：

- `packages/api/app/kg/graph_service.py` 已提供节点搜索、药材中心子图、路径查找、节点扩展与高级图谱查询
- `packages/api/app/api/graph.py` 已把图谱查询与 metadata 能力暴露为 HTTP 接口
- `packages/api/app/services/chat_service.py` 已存在一条“问题 -> 抽实体 -> 查图 -> 回答”的问答链路
- `packages/api/app/services/llm_client.py` 已封装 OpenAI / Anthropic 风格的大模型接入
- `packages/web/` 已具备图谱工作台与 chat 页面

但当前这些能力更偏“面向页面和 API 路由的产品链路”，而不是“面向 agent runtime 的知识系统工具层”。主要缺口包括：

- 图查询能力虽然存在，但没有整理成 agent 友好的稳定 primitives
- 当前 chat 更像单次问答服务，而不是一个可自主探索、自主决策、多步查询的 graph agent
- 图查询、agent 编排、CLI/terminal tool 入口尚未形成清晰的三层边界
- 当前没有一个渐进式发现、错误友好、适合 terminal tool 调用的 graph CLI
- 当前 schema 与图查询之间缺少“面向自然语言问题的语义模糊增强层”

用户已经明确希望下一步把这些图谱数据“用起来”，形成一套：

- **首发入口在仓库内 agent runtime**
- **`graph service`、`agent runtime`、`cli` 分层分包**
- **CLI 作为 terminal tool 的薄壳入口**
- **CLI 设计遵循渐进式发现，参考 `lark-cli` 风格**
- **默认场景面向开放探索型问答**
- **默认输出采用双轨并行：回答 + 结构化子图结果**
- **默认 agent 自适应探索，自主决定何时扩展、何时回收、何时降级到只读 Cypher**

## 目标

### 主要目标

1. 建立一个独立的 `graph runtime` 包，作为图谱知识系统的 agent-first 工具层
2. 让图谱查询能力以 **高层组合工具 + 底层 primitives** 双层方式暴露
3. 为开放探索型问题提供一个默认 `graph agent`
4. 默认 `graph agent` 输出：
   - `answer`
   - `evidence`
   - `related_nodes`
   - `related_edges`
   - `subgraph_meta`
   - `reasoning_trace`
   - `tool_calls`
5. 支持 schema-aware query planning：
   - 第一阶段优先做 **schema 语义模糊增强**
   - 第二阶段补 **实体名模糊增强**
6. 支持图遍历与探索策略：
   - `BFS`
   - `DFS`
   - 深度限制
   - 节点预算
   - 自适应渐进式升级
7. 提供一个 terminal-friendly 的 CLI 薄壳，保持 help 渐进式发现、参数指引和友好错误提示

### 非目标

- 本轮不把 graph runtime 直接做成 Web UI 主入口
- 本轮不支持写 Cypher、写图库或自动修改图谱数据
- 本轮不做复杂的多 agent 协作问答系统
- 本轮不做完整的自然语言到任意 Cypher planner
- 本轮不把所有 API / Web 路由都迁移到新 runtime 上
- 本轮不引入新的向量数据库或全文检索基础设施作为硬依赖

## 用户确认后的边界

基于本轮沟通，已确认以下稳定约束：

- 首个主入口是 **仓库内 agent runtime**
- `graph service`、`agent runtime`、`cli` 三层必须分开
- CLI 只是调用层，不是逻辑真源
- CLI 必须遵循 **渐进式发现**
- 默认问题类型是 **开放探索型问答**
- 默认输出是 **双轨并行**
- 默认探索策略是 **渐进式、自适应、探索型、agent 自主决策**
- 工具面采用 **高层组合工具 + 底层 primitives 并存**
- agent 默认不能执行写 Cypher；只允许在必要时降级到 **只读 Cypher**

## 方案对比

### 方案 1：全部放在 `packages/api/`

做法：

- 在 `packages/api/` 内继续扩展 `graph_service`、`chat_service` 和路由
- 把 graph agent、CLI 接线与 schema-aware planner 都作为 API 内部模块实现

优点：

- 接线最快
- 复用现有依赖最直接

缺点：

- `graph service / agent runtime / CLI` 容易重新耦合
- 不利于在 API 外被 agent / CLI / 本地脚本复用
- 后续会继续把“产品服务层”和“知识系统工具层”缠在一起

### 方案 2：只做底层 primitives，不做默认 agent

做法：

- 只抽出图谱 primitives 和 schema-aware recall
- 不提供默认 graph QA agent

优点：

- 最小、最稳
- 易于测试

缺点：

- 用户价值释放慢
- 后续每个上层入口都要自己重新编排

### 方案 3：独立 runtime 包 + API 接线 + CLI 薄壳

做法：

- 新建独立包承载 graph runtime / graph agent
- API 只作为对外接线与集成入口
- CLI 只作为 terminal tool 薄壳

优点：

- 最符合当前边界要求
- 最利于 agent runtime、API 和 CLI 三方复用
- 最利于把 primitives、高层工具与默认 agent 做成统一知识系统层

缺点：

- 初版结构设计成本更高
- 需要更明确地定义分包与 contracts

## 推荐方案

推荐采用 **方案 3：独立 runtime 包 + API 接线 + CLI 薄壳**。

### 推荐原因

1. 这最符合用户已经明确确认的边界：`graph service`、`agent runtime`、`cli` 分层
2. 这能把“知识系统工具层”从当前 API / 页面导向逻辑中解耦出来
3. 这最适合后续继续扩展 terminal tool、agent 工具面和产品接线
4. 双层工具面（高层 + primitives）在独立 runtime 包里更容易保持清晰

## 设计决策

### 决策 1：采用三层调用关系

本轮按以下关系组织：

1. `graph service`
   - 面向图数据库查询事实
   - 不关心 agent 推理
   - 不关心 CLI help 或命令面

2. `graph runtime / graph agent`
   - 面向 agent 使用
   - 编排 primitives、探索策略、schema-aware recall、子图回收与双轨输出

3. `CLI`
   - 面向 terminal tool
   - 只负责编排参数、help、错误提示和输出格式选择

### 决策 2：新建独立包作为 runtime 真源

建议新增：

```text
packages/graph_runtime/
```

这个包负责承载：

- agent-friendly graph service facade
- 底层 graph primitives
- schema-aware query planning
- 默认 graph exploration agent
- 统一 contracts

`packages/api/` 只负责接线，不再作为这套 runtime 的真源。

### 决策 3：高层工具与 primitives 双层并存

本轮工具面分两层：

#### 高层组合工具

- `ask_graph`
- `explore_graph`
- `find_subgraph`

#### 底层 primitives

- `search_nodes`
- `expand_neighbors`
- `bfs_walk`
- `dfs_walk`
- `read_cypher`
- `collect_evidence`

默认 graph agent 优先走高层组合工具；若高层工具不足，再下探到底层 primitives。

### 决策 4：只读 Cypher 是 escape hatch，不是主路径

本轮允许：

- 生成并执行 **只读 Cypher**

本轮禁止：

- 写 Cypher
- 写图库
- 自动修改节点/关系

默认执行顺序：

1. schema-aware recall
2. 结构化 primitives
3. BFS / DFS
4. 只读 Cypher fallback

### 决策 5：默认输出采用双轨并行

默认 graph agent 输出模型建议至少包含：

#### `answer`

- 面向用户的自然语言回答

#### `evidence`

- 关键证据节点
- 关键证据文本摘要
- 与回答强相关的出处

#### `related_nodes`

- 与当前问题最相关的节点集合

#### `related_edges`

- 与问题直接相关的关系集合

#### `subgraph_meta`

- 子图中心节点
- 查询预算
- 实际探索深度
- 命中策略
- 是否发生 fallback

#### `reasoning_trace`

- 精简版推理轨迹
- 不泄露内部原始思维，但保留“做了哪些工具调用和为什么”

#### `tool_calls`

- 结构化记录：
  - 工具名
  - 参数
  - 结果摘要

### 决策 6：默认探索策略采用渐进式、自适应、自主决策

默认 graph agent 不做“一次性激进大展开”，而采用：

1. 从小预算开始
2. 先浅层模糊召回 + 近邻扩展
3. 若证据不足，再自动升级探索预算
4. 必要时切换 BFS / DFS
5. 仍不足时，降级到只读 Cypher

建议默认预算参数：

- `max_depth`
- `node_budget`
- `edge_budget`
- `tool_call_budget`
- `allow_read_cypher`

### 决策 7：模糊增强先做 schema 语义，再做实体名

本轮 schema-aware query planning 先做：

#### Phase 1：schema 语义模糊增强

把用户表达映射到：

- 节点类型
- 关系类型
- 属性键
- 常见图问题模式

例如：

- “功效 / 主治 / 作用” → `功效` / `治疗病证`
- “归经 / 走什么经” → `归经` / `归于经脉`
- “饮片 / 炮制后 / 切片后” → `饮片` / `具有饮片`
- “证据 / 原文 / 出处” → `证据` / `由证据支持`

#### Phase 2：实体名模糊增强

后续再补：

- 部分匹配
- 拼音
- 拉丁名
- 常见别名
- 轻度错别字

### 决策 8：CLI 设计遵循渐进式发现

CLI 设计原则参考 `lark-cli` 的使用体验，但保持本项目 own style。

建议命令面：

```text
graph
graph help
graph ask
graph search
graph explore
graph walk
graph cypher
graph schema
```

#### help 设计原则

- 根命令 `graph --help` 只展示最常用子命令
- `graph ask --help` 再展示 agent 问答相关参数
- `graph walk --help` 再细化 BFS / DFS / 深度 / 预算参数

#### 报错设计原则

- 参数缺失时提示下一步怎么补
- 子命令错误时给候选命令
- 不仅报“错了”，还告诉用户“你可以试试什么”

示例：

```text
缺少问题内容。可以试试：
  graph ask "黄芩的功效和归经是什么？"
  graph ask --help
```

### 决策 9：graph service、runtime、CLI 分别测试

测试分层建议：

#### graph service

- 图查询主路径
- BFS / DFS 结果
- 只读 Cypher 安全约束

#### graph runtime

- schema-aware planner
- 自适应探索升级
- 双轨输出契约

#### CLI

- help
- 参数错误提示
- 子命令渐进式发现

## 推荐包结构

建议：

```text
packages/graph_runtime/
├── pyproject.toml
└── graph_runtime/
    ├── __init__.py
    ├── contracts/
    │   ├── inputs.py
    │   ├── outputs.py
    │   └── tool_calls.py
    ├── service/
    │   ├── graph_facade.py
    │   ├── graph_queries.py
    │   └── cypher_readonly.py
    ├── primitives/
    │   ├── search.py
    │   ├── expand.py
    │   ├── bfs.py
    │   ├── dfs.py
    │   └── evidence.py
    ├── planner/
    │   ├── schema_semantic_mapping.py
    │   ├── entity_fuzzy_recall.py
    │   └── plan_builder.py
    ├── agent/
    │   ├── graph_agent.py
    │   ├── exploration_policy.py
    │   └── answer_synthesis.py
    └── cli/
        ├── main.py
        ├── help.py
        ├── commands/
        └── formatters/
```

## 默认 agent 最顺手需要的工具

从“让 agent 最顺手使用本知识系统”的角度，MVP 最重要的工具不是越多越好，而是**边界稳定、语义明确、可组合**。

建议首批工具：

1. `search_nodes`
   - 负责模糊召回候选实体

2. `get_node_detail`
   - 负责读取节点详情与核心属性

3. `expand_neighbors`
   - 负责一跳或有限深度邻居扩展

4. `bfs_walk`
   - 适合找“最短层次相关上下文”

5. `dfs_walk`
   - 适合找“沿一条关系链继续深挖”

6. `find_path`
   - 适合回答“两者如何关联”

7. `collect_evidence`
   - 把证据节点和原文回收回来

8. `read_cypher`
   - 只读 fallback

9. `summarize_subgraph`
   - 把图查询结果压缩成可回答的上下文

10. `schema_help`
   - 让 agent 先知道有哪些 label、relationship type、property key

## 与现有仓库能力的衔接

### 复用点

- 复用 `packages/api/app/kg/graph_service.py` 的现有查询能力
- 复用 `packages/api/app/kg/graph_metadata_service.py` 的 schema / metadata 能力
- 复用 `packages/api/app/services/llm_client.py` 的模型接入事实

### 不直接复用为真源的部分

- 现有 `chat_service` 不应直接变成 graph runtime 真源
- 现有 API route 不应承担 CLI 风格 help 和 tool discovery 逻辑

## 风险与未覆盖项

- 当前图谱数据属性和节点类型还在持续扩展，planner 的 schema 语义映射需要留可扩展表驱动结构
- 只读 Cypher fallback 若没有严格白名单与限制，后续可能被滥用成默认路径
- CLI 的“渐进式发现”如果没有单独测试，容易在后续演进中退化成普通 argparse 输出
- 开放探索型问答的效果高度依赖子图回收质量，MVP 需要控制预算与输出规模

## 结论

- 结果：采用 **独立 runtime 包 + API 接线 + CLI 薄壳**
- 默认场景：开放探索型问答
- 默认输出：双轨并行
- 默认策略：渐进式、自适应、自主探索
- 下一步：基于本 spec 写 implementation plan，再进入实现
