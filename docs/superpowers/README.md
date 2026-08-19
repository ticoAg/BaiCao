# Superpowers 文档

这里是 BaiCao 仓库内与 superpowers 协作体系直接相关的入口目录，负责回答三个问题：

1. 仓库级任务系统现在以什么为准
2. 设计 spec、实施 plan 和执行 skill 之间是什么关系
3. 新任务开始时，应该先读哪个 plan / spec

## 一页看懂

- `specs/`：设计规格文档，记录某轮方案的目标、边界、约束和设计决策
- `plans/`：实施计划文档，记录可执行任务拆解、文件范围、验证步骤和执行顺序
- 仓库级任务系统：以 `writing-plans` 产出的 `plans/*.md` 为准
- 执行阶段：有计划后，优先衔接 `subagent-driven-development` 或 `executing-plans`

## 推荐阅读顺序

1. `../AGENTS.md`
2. `../workflow.md`
3. `../agent-skill-routing.md`
4. 相关 `specs/*.md`
5. 相关 `plans/*.md`

## 目录说明

| 路径 | 定位 | 何时阅读 |
|---|---|---|
| `specs/` | 设计规格真源 | 需要理解某轮方案为什么这样设计时 |
| `plans/` | 仓库级实施任务系统 | 需要开始执行、交接进度、追踪验证时 |

## 工作方式

### 1. 先 spec，后 plan

- 方向仍在收敛时，先通过 `brainstorming` 形成 spec
- spec 写入 `specs/*.md`
- 再通过 `writing-plans` 形成实施计划
- plan 写入 `plans/*.md`

### 2. plan 是任务真源

在 BaiCao 仓库内：

- 高层阶段目标与当前阶段说明看 `README.md`
- 某轮任务的可执行拆解、进度勾选、验证步骤看 `plans/*.md`
- 不再使用仓库自定义 JSON task 文件或单独的 TODO 台账作为任务真源

### 3. 执行围绕 plan 展开

- 已有明确计划时，优先按 `plans/*.md` 执行
- 执行过程中新增拆解、调整验证或改变文件范围时，先回写 plan，再继续实现
- 交接时优先引用对应 plan 文档，而不是口头描述

## 文档维护规则

- 新增 `specs/*.md` 或 `plans/*.md` 时，文件名使用 `YYYY-MM-DD-<topic>.md`
- 若某个 plan 已成为当前任务入口，相关 README / workflow / acceptance 文档应优先引用该 plan
- 稳定规则不要只写在 plan 里；需要长期维护的规则应毕业到 `AGENTS.md`、`workflow.md` 或 `docs/` 下稳定文档

## 完成后的毕业 / 归档规则

`superpowers` 的 `spec` / `plan` 默认是过程真源，不是长期稳定真源。

当对应任务完成后，按下面的规则收口：

1. 已落地且需要长期维护的边界、结构、术语和运行时约束，毕业到 `docs/architecture/`
2. 验收步骤、验证命令、结果判定和实现证据，毕业到 `docs/acceptance/`
3. 影响仓库默认研发动作的规则，毕业到 `AGENTS.md`、`workflow.md`、`docs/verification-matrix.md` 等稳定协作文档
4. `docs/superpowers/` 继续保留设计决策、任务拆解和执行回溯价值

删除规则：

- 若新的 spec / plan 已完整覆盖旧需求，旧文档直接删除，不并行保留
- 若旧文档仍有独立回溯价值且未被覆盖，可以继续保留

完成这一步时，还必须同步：

- 相关目录 `README.md`
- 稳定文档的状态字段
- 验收文档和计划文档中的引用路径

## 当前入口

- 任务索引：`plans/README.md`（先看状态再打开 plan）
- 规格索引：`specs/README.md`
- 已完成计划：`plans/archive/README.md`
- 已落地规格：`specs/archive/README.md`
- **当前 active：** 无
- 已完成 dataset / 可信问答计划：`plans/archive/README.md`
- 已落地 dataset spec：`specs/archive/README.md`
- 数据台账：`../../datasets/baicao-knowledge/`

已完成 plan / spec 保留回溯，不要再执行。`packages/graph_runtime/` 不是 chat 主链。

## 当前关系

- 仓库级工作流：`../workflow.md`
- skill 路由：`../agent-skill-routing.md`
- 项目总入口：`../../README.md`
- 验收入口：`../acceptance/README.md`
