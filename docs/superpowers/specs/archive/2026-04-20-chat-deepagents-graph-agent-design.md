# Chat 单入口 DeepAgents 图谱 Agent 设计

## 概览

本规格定义 BaiCao 如何把当前“`chat` 与 `graph-agent` 双入口并存”的图谱问答链路，重构为一个**只保留 `chat` 主入口**、内部由 `deepagents` 驱动的统一图谱 agent。

本轮设计的核心不是继续扩展当前 `GraphExplorationAgent` 的规则分支，而是把“怎么思考、先调用什么工具、工具参数如何组织”交给 agent runtime 自主决策；代码层只提供：

- 唯一的 chat 流式入口
- 一组基础图工具
- 稳定的 system prompt
- 透明的过程事件输出

同时，本轮明确要求：

- 页面只显示 provider 真正返回的 reasoning，不伪造、不补写
- 如果 provider 没返回 reasoning，则页面不显示 reasoning 区块
- 工具调用、参数、结果、子图 patch 和最终回答仍然完整展示

## 背景

当前仓库里与图谱问答相关的实现已经包含几条能力链：

- `packages/api/app/services/chat_service.py` 提供基于规则抽实体 + 图谱查询 + LLM/规则回答的 chat 流程
- `packages/api/app/api/chat.py` 提供 `/api/v1/chat/question` 与 `/api/v1/chat/stream`
- `packages/api/app/services/graph_agent_service.py` 与 `/api/v1/graph-agent/*` 提供独立 graph agent 入口
- `packages/graph_runtime/` 已经具备一套 graph runtime / planner / graph agent / tool call contracts
- `packages/web/src/pages/ChatPage.tsx` 与 `GraphAgentBasisPanel.tsx` 已可展示子图、工具调用摘要和推理摘要

但当前图谱 agent 仍存在这些问题：

- 工具决策仍然是代码硬分支，而不是统一入口下的 agent 自主决策
- `chat` 与 `graph-agent` 是两套入口，产品和协议边界分裂
- 当前 planner 依赖规则分类，不符合“统一入口 + 工具自决策”的目标
- 页面展示的是执行摘要，不是 provider 原生 reasoning
- 多轮上下文管理还不是 agent thread 视角

用户已经明确确认，本轮目标是：

- **只保留 `chat` 主入口**
- **内部接入 `deepagents`**
- **不再保留“抽象问题走某工具、其他问题走某工具”的硬分支**
- **只暴露基础图工具，不暴露高阶黑盒问答工具**
- **provider 有 reasoning 就显示，没有就不显示**
- **会话上下文直接交给 `deepagents` 管理，不手动删减历史**

## 目标

### 主要目标

1. 把 `POST /api/v1/chat/stream` 变成唯一的图谱问答主入口
2. 用 `deepagents` 构建一个 graph specialist agent，替代当前规则分流 runtime
3. 向 agent 注册一组基础图工具，而不是继续走高阶黑盒图问答工具
4. 用 system prompt 注入场景上下文、工具说明和建议使用方法
5. 让 agent 在统一入口下自主决定工具选择、顺序和参数
6. 页面流式展示：
   - provider 原生 reasoning（如果有）
   - 工具调用、参数、结果
   - 子图 patch
   - 最终回答
7. 保留轻量多轮 thread，但不做数据库持久化 memory

### 非目标

- 本轮不做长期持久化 memory / checkpoint 存储
- 本轮不做多 agent supervisor / specialist 分层
- 本轮不接入图谱之外的通用外部工具
- 本轮不人工生成可展示 reasoning 文本
- 本轮不保留 `/api/v1/graph-agent/*` 作为主路径
- 本轮不继续强化旧 `GraphExplorationAgent` 的规则 planner

## 用户确认后的稳定边界

基于本轮沟通，以下约束已确认：

- 对外只保留 `chat` 主入口；`graph-agent` 接口族将退役
- 首选框架是 `deepagents`
- 页面期望为流式过程展示，而不是结束后一次性显示
- 推理显示只接受 provider 原生 reasoning；没有就不显示
- 会话采用轻量多轮 thread，不做持久化
- thread 历史直接交给 `deepagents`，不做人工裁剪、摘要或删减
- 首批工具集是**基础图工具集**
- `graph_cypher_qa` 这类高阶黑盒工具第一版移除
- system prompt 需要明确场景上下文和推荐工具使用方法，例如先模糊找锚点，再围绕锚点做图游走

## 方案对比

### 方案 1：直接上 `deepagents`，构建单一 Graph Specialist Agent

做法：

- `/api/v1/chat/stream` 直接接到 `deepagents` runtime
- 只注册图谱基础工具
- 用统一 system prompt 驱动 agent 自主决策

优点：

- 最符合“统一入口、少分支、工具自决策”的目标
- 架构清晰，产品边界简单
- 后续最容易扩展流式过程和 thread 管理

缺点：

- 首版需要同时处理 runtime、事件桥接和工具说明质量

### 方案 2：保留旧 runtime 外壳，内部偷偷切到 `deepagents`

做法：

- 保留 `GraphExplorationAgent`、planner、旧 service 外形
- 内部只替换具体实现为 `deepagents`

优点：

- 改造入口最小
- 兼容性看起来最好

缺点：

- 会把旧的规则分流思维继续残留在架构里
- 代码职责不清，后续更难物理清理旧路径

### 方案 3：先做自研轻量 agent loop，后续再迁 `deepagents`

做法：

- 当前先自己实现 tool registry + runtime loop
- 设计对齐 `deepagents`，后续再迁移

优点：

- 依赖最少
- 对事件格式完全可控

缺点：

- 要自己补 runtime 能力
- 会多一次无谓迁移

## 推荐方案

推荐采用 **方案 1：直接上 `deepagents`，构建单一 Graph Specialist Agent**。

### 推荐原因

1. 这最符合本轮已确认的目标：统一入口、工具自决策、少逻辑分支
2. 这可以把“怎么想”从代码逻辑转移到 runtime + prompt
3. 这最容易与流式过程展示、thread 管理和工具调用追踪结合
4. 这能把现有图能力沉淀为稳定、可组合、可说明的基础工具层

## 设计决策

### 决策 1：`/api/v1/chat/stream` 是唯一主入口

最终对外接口收敛为：

- 保留：`POST /api/v1/chat/stream`
- 废弃：`POST /api/v1/chat/question`
- 退役：`/api/v1/graph-agent/*`

`chat/stream` 将成为：

- 唯一的图谱问答入口
- 唯一的 agent 流式过程入口
- 唯一的多轮 thread 承载入口

### 决策 2：内部执行内核切到单一 Graph Specialist Agent

`chat/stream` 背后不再走当前 `ChatService` 的“规则抽实体 + 图谱拼上下文 + LLM补全”路径，而是进入一个由 `deepagents` 驱动的 graph specialist agent。

这个 agent 的输入包括：

- 最近完整 thread 历史
- system prompt 中的场景上下文和约束
- 注册好的基础图工具

这个 agent 的职责是：

- 决定先用什么工具
- 决定工具参数
- 决定是否继续缩小范围或扩展子图
- 组织最终回答

### 决策 3：移除前置问题分类，不再硬编码工具分流

当前 `abstract_graph_query -> graph_cypher_qa`、其他问题 -> `search_nodes` 的硬分支将被移除。

这一轮明确不再保留：

- 问题意图前置分类驱动的工具选择
- 规则 planner 决定初始工具
- 高阶黑盒问答工具作为默认主路径

取而代之的是：

- 统一入口
- 工具注册
- system prompt 中的推荐工作方法
- agent runtime 自主决策

### 决策 4：首批只暴露基础图工具，不暴露高阶黑盒图问答工具

第一版 agent 工具面固定为以下 5 类基础图工具：

1. `search_nodes`
   - 按关键词模糊查询节点
   - 支持可选节点类型过滤和结果上限

2. `search_edges`
   - 按关系类型或关系关键词查询关系
   - 支持起点/终点类型过滤

3. `expand_neighbors`
   - 围绕某个节点做 1-hop / 2-hop 邻居展开
   - 支持边类型、节点类型与上限过滤

4. `lookup_nodes`
   - 按 node ids 精确读取节点详情

5. `read_cypher`
   - 受限的只读 Cypher 工具
   - 作为低层 escape hatch，而不是默认主路径

第一版不向 agent 暴露：

- `graph_cypher_qa`
- 其他把“图查询 + 结论生成”封装在同一个高阶黑盒中的工具

### 决策 5：system prompt 负责建立工作语境，而不是做代码分流

system prompt 至少包含 4 块内容：

1. 角色与任务
   - 你是中药知识图谱专家
   - 优先依赖图谱工具而不是凭空回答

2. 场景上下文
   - 当前场景是中药知识图谱
   - 数据中存在别名、歧义、自然语言不稳定表达
   - 用户问题可能不直接命中实体，需要先定位锚点

3. 推荐工作策略
   - 先用模糊查询找锚点
   - 再围绕锚点做关系查询和邻居游走
   - 优先缩小范围，不要一上来抓大图
   - 基础工具不足时再考虑更低层工具

4. 行为约束
   - 不编造结论
   - 不伪造 reasoning
   - 不回显内部 prompt
   - 工具失败时要明确失败原因

### 决策 6：provider reasoning 只透传，不生成

reasoning 显示规则明确为：

- provider 返回原生 reasoning，则原样透传
- provider 不返回，则页面完全不显示 reasoning 区块
- 不生成 `rationale`
- 不补写 `step notes`
- 不写“可展示 reasoning”的替代文本

工具调用、参数和结果展示不受此限制，仍然按真实执行过程完整显示。

### 决策 7：thread 历史直接交给 `deepagents`

上下文策略明确为：

- 使用 `session_id` 作为 thread 标识
- 不做数据库持久化 memory
- 不做人为历史裁剪
- 不人工删减消息
- 不手写工具结果摘要回填
- 直接把完整 thread 历史、工具调用和工具输出交给 `deepagents`

也就是说，上下文管理责任归于 `deepagents` runtime，我们不再维护一套手工删减过的“简化上下文模型”。

### 决策 8：继续使用 SSE，但事件模型升级为 agent 事件流

保留 `chat/stream` 的 SSE 方向，但事件集合升级为：

1. `session`
   - 包含 `session_id`、`turn_id`

2. `provider_reasoning`
   - 只在 provider 真返回 reasoning chunk 时发送

3. `tool_start`
   - 包含 `tool_name`、`call_id`、`arguments`

4. `tool_result`
   - 包含 `tool_name`、`call_id`、`result_summary`、可选 `payload_preview`

5. `subgraph_patch`
   - 用于增量更新依据子图

6. `answer_chunk`
   - 最终回答正文流式文本片段

7. `final`
   - 返回本轮最终结构化结果

8. `error`
   - 返回错误信息并终止本轮

### 决策 9：页面展示四条并行信息流

Chat 页面中的 assistant message 在流式过程中逐步形成，包含 4 个展示区：

1. `provider reasoning`
   - 只在有原生 reasoning 时出现

2. `tool timeline`
   - 显示工具名、参数、结果、状态

3. `subgraph`
   - 随着 `subgraph_patch` 渐进更新

4. `final answer`
   - 随 `answer_chunk` 增长

最终由 `final` 事件把流式中的草稿态固化为最终消息对象。

## 模块拆分与代码落点

### 1. 新增 `packages/api/app/services/chat_agent_runtime/`

该目录作为新 runtime 真源，建议至少拆成：

- `runtime.py`
  - 创建和执行 deepagents graph specialist agent
  - 暴露统一的 `stream_turn(...)`

- `thread_store.py`
  - 管理运行期 thread / session 状态
  - 不做数据库持久化

- `system_prompt.py`
  - 维护 graph specialist 的 system prompt

- `event_adapter.py`
  - 把 deepagents/langgraph 内部事件转换为前端 SSE 事件

- `provider_reasoning.py`
  - 从 provider 响应中提取原生 reasoning

### 2. 新增 `packages/api/app/services/graph_tools/`

该目录作为基础图工具层，建议至少拆成：

- `registry.py`
  - 统一注册工具给 deepagents

- `search_nodes.py`
- `search_edges.py`
- `expand_neighbors.py`
- `lookup_nodes.py`
- `read_cypher.py`

每个工具文件只负责：

- tool schema
- tool description
- 调底层 graph service / runtime backend
- 返回 agent 友好的结构

### 3. 改造 `packages/api/app/api/chat.py`

`chat.py` 保留为唯一入口路由，但 `stream` 实现改为接到新的 `chat_agent_runtime.stream_turn(...)`，不再走当前旧 `ChatService.answer_question_stream(...)` 主路径。

### 4. 改造 `packages/web/src/hooks/useChat.ts`

职责变为：

- 消费新的 agent SSE 事件
- 维护流式中的 assistant message 草稿态
- 组装 provider reasoning、tool timeline、subgraph、answer
- 在 `final` 到达后固化消息

### 5. 改造 `packages/web/src/components/chat/GraphAgentBasisPanel.tsx`

继续复用当前组件，但升级为：

- 同时支持流式中间态和最终态
- 可显示 provider reasoning
- 可显示实时工具调用
- 可显示实时子图 patch

## 旧模块退役方案

### 第一批：立即退出主路径

以下模块不再作为主执行路径：

- `packages/graph_runtime/graph_runtime/agent/graph_agent.py`
- `packages/graph_runtime/graph_runtime/planner/query_intent.py`
- `packages/graph_runtime/graph_runtime/planner/tool_plan_builder.py`
- `packages/api/app/services/graph_agent_service.py`
- `packages/api/app/services/graph_cypher_agent.py`
- `/api/v1/graph-agent/*`

### 第二批：保留底层能力供工具层复用

以下能力仍可作为工具层基础：

- API 当前的 graph service
- graph runtime facade / backend / primitives
- 现有节点搜索、邻居展开、路径查找、只读 Cypher 等图查询能力

也就是说，本轮不是把图谱能力推翻，而是把“由谁决定用哪个能力”从规则 runtime 切到 agent runtime。

## 测试策略

### 1. 工具层单测

覆盖：

- `search_nodes`
- `search_edges`
- `expand_neighbors`
- `lookup_nodes`
- `read_cypher`

验证：

- 参数校验
- 空结果
- 类型过滤
- limit 行为
- 只读 Cypher 安全约束

### 2. runtime 层单测

覆盖：

- system prompt 注入
- 工具 registry 注入
- thread/session 绑定
- provider reasoning 有/无两种分支
- deepagents 事件到 SSE 事件的转换

### 3. API contract 测试

覆盖：

- `/api/v1/chat/stream` 新 SSE 事件集合
- 每类事件 payload 结构
- `final` 的最终消息结构
- `error` 事件格式

### 4. 前端 UI 测试

覆盖：

- 有 reasoning 时显示 reasoning
- 无 reasoning 时不显示 reasoning 区
- 工具参数展示
- 工具结果展示
- 子图 patch 累积更新
- 最终答案 chunk 流式拼接
- 多轮 thread 连续提问

## 迁移顺序

### 阶段 1：先落 runtime 与 graph tools

- 新建 `chat_agent_runtime/`
- 新建 `graph_tools/`
- 先不切换主流量

### 阶段 2：把 `/api/v1/chat/stream` 接到新 runtime

- 只保留 chat 主入口
- 打通 agent 事件流

### 阶段 3：前端切换到新的 agent SSE 协议

- Chat 页面开始实时显示 reasoning / tools / subgraph / answer

### 阶段 4：废弃旧 `graph-agent` 路径

- 标记 `/graph-agent/*` 退役
- 旧 graph agent service 退出主路径

### 阶段 5：新链路稳定后物理删除旧路径

- 删除旧 planner 分流
- 删除旧 graph-agent route / service / 测试

## 最小可上线版本

第一版上线标准建议为：

- 唯一入口为 `POST /api/v1/chat/stream`
- deepagents graph specialist 可工作
- 首批 5 个基础图工具可工作
- thread 可延续完整历史
- provider reasoning 有就显示，没有就不显示
- 工具调用、参数、结果和子图可流式展示
- 最终答案可正常流式输出
- 旧 `/graph-agent/*` 不再是主路径

## 风险与应对

### 风险 1：provider reasoning 字段不稳定

应对：

- reasoning 显示完全可选
- 协议允许 reasoning 事件缺席

### 风险 2：deepagents 内部事件与前端需求不对齐

应对：

- 加 `event_adapter.py` 作为协议隔离层
- 前端只依赖仓库内部定义的 SSE 事件

### 风险 3：工具太原子导致 agent 试错过多

应对：

- 优先优化 system prompt 与 tool description
- 不急于回退到代码硬分支

### 风险 4：完整 thread 历史导致上下文变大

应对：

- 第一版严格尊重已确认边界，不手工裁剪
- 如果后续实测存在成本或性能问题，再单独评估压缩策略

## 结论

推荐把 BaiCao 的图谱问答链路重构为：

- **唯一 chat 流式入口**
- **deepagents 单一 Graph Specialist Agent**
- **基础图工具注册**
- **provider reasoning 只透传不生成**
- **完整 thread 历史交给 deepagents**
- **页面实时展示 reasoning / tools / subgraph / answer**

这条路线最符合当前已经确认的产品目标，也能把“规则驱动图问答”真正升级为“agent 驱动图探索问答”。
