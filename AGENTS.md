---
language: zh
type: agent guide doc
note: agent-facing repo entry guide. English or mixed wording is allowed when it improves precision.
---

# BaiCao Agent Entry (Monorepo)

This repo contains `packages/api/`, `packages/web/`, `packages/shared/`, `packages/db/`, `infra/`, and `docs/`. This file is the repo-level agent entry guide for repository-wide behavior and routing. More specific engineering constraints should live in deeper docs or future module-local `AGENTS.md` files.

## Navigation

| Need to know...                             | Read...                       |
| ------------------------------------------- | ----------------------------- |
| 项目定位与受众                              | `README.md`                   |
| 当前阶段与目标                              | `docs/architecture/README.md` |
| 本地开发栈 / 环境变量 / 验证命令            | `docs/local-development.md`   |
| 仓库级工作流、任务分流、contract-first 顺序 | `workflow.md`                 |
| Skill 选择与多代理路由                      | `docs/agent-skill-routing.md` |
| 各类改动的最低验证标准                      | `docs/verification-matrix.md` |
| 文档系统入口与放置规则                      | `docs/README.md`              |
| 稳定架构口径                                | `docs/architecture/README.md` |
| 验收入口与证据格式                          | `docs/acceptance/README.md`   |
| 仓库级任务系统与实施计划                    | `docs/plans/`                 |

## Core Principles

Evidence first · SSOT first · Contract first · Progressive disclosure · Small diff first · Verify before done

## Language Policy

- 面向开发者和 agent 的新增文档默认使用中文；英文或中英混合仅在能明显降低歧义时使用。
- agent 对用户的回复默认使用中文；除非用户明确要求英文，或当前上下文有更高优先级语言约束。
- 代码注释、架构说明注释、developer-facing README 默认中文；若文件本身长期以英文为主，保持一致性优先。
- 对外协议字段、标准名词、第三方 API 语义，保留最准确的原始英文表达。

## Repo SSOT

- **产品定位与受众**：`README.md`
- **当前阶段与目标**：`docs/architecture/README.md`
- **任务计划与实施颗粒度**：`docs/plans/`
- **跨端共享协议入口**：`packages/shared/types/`
- **后端领域模型 / API Schema / 服务真源**：`packages/api/app/models/`、`packages/api/app/schemas/`、`packages/api/app/services/`
- **图模型（节点类型 / 关系类型 / 属性）真源**：`packages/graph_schema/`（`constants.py`、节点/关系属性模型、`graph_i18n.py`）
- **图谱与导入结构真源**：`packages/db/neo4j/`、`packages/db/import/`
- **数据源 agent 工作目录**：`datasets/baicao-knowledge/sources/<source_id>/`（`SOURCE.md`、`VIEW.md`、`work/`、`processed/latest/`）
- **前端消费与展示态适配真源**：`packages/web/src/services/`、`packages/web/src/pages/`
- **运行编排与环境事实**：`infra/docker-compose.yml`、`infra/.env.schema`
- **长期维护文档**：`docs/architecture/`、`docs/acceptance/`
- **当轮执行计划**：`docs/plans/`

## Agent Behavior

- Read context before acting: inspect the active-scope `AGENTS.md`, root `workflow.md`, and the most relevant README / architecture / acceptance docs before choosing an implementation path.
- Identify the primary scope first: decide whether the task belongs to `packages/api/`, `packages/web/`, `packages/shared/`, `packages/db/`, `infra/`, `docs/`, or a cross-module path instead of patching the easiest surface.
- Choose the workflow before writing code: for any non-trivial task, determine the right process skill / workflow first rather than coding immediately.
- Treat shared contract changes as contract-first work: if API fields, graph payloads, verification status, or cross-end DTOs change, update the contract source first, then service logic, then consumers.
- Because the repo is still in early evolution, prefer clean boundary corrections over temporary compatibility shims; if a breaking change is intentional, state the impact explicitly in code and docs.
- The main agent owns orchestration: it is responsible for shaping the split, sequencing work, integrating results, organizing verification, and producing the final answer.
- Keep diffs small and intentional: fix root causes, avoid incidental refactors, avoid broad renames, and avoid repo-wide formatting unless explicitly required.
- Proceed on low-risk assumptions by default; pause only when the branch in direction would materially affect architecture, contracts, data, or UX.
- Use progressive disclosure in communication: report conclusions, impact, verification, and next steps first; do not dump raw logs or long internal reasoning.
- Never claim completion without evidence. If verification is incomplete, state what is unverified, why, and how to reproduce the check.

## Skill 决策入口

- 开始任何非琐碎任务前，先根据 `docs/agent-skill-routing.md` 判断本轮应先使用哪类 skill。
- 默认顺序：先流程型 skill，再领域型 skill，最后协作 / 收尾型 skill。
- 新功能、行为变更、方向未完全收敛时，默认先看是否需要 `brainstorming`。
- Bug、回归、接口异常、图谱查询异常、链路不稳定时，默认先看是否需要 `systematic-debugging`。
- 多步骤、跨模块、需要拆阶段落地的任务，默认先用 `writing-plans`；只有在需要额外会话级私有笔记时才补 `planning-with-files`。
- 收到 review 评论时优先 `receiving-code-review`；准备宣称完成前默认补 `verification-before-completion`。

## Multi-Agent Collaboration

- For complex tasks, prefer multi-agent execution through collaboration skills instead of one serial agent path when subproblems are actually independent.
- Multi-agent routing, collaboration-skill selection, fork-context preference, and main/sub-agent responsibilities are defined in `docs/agent-skill-routing.md` as the repo-level single source of truth; this file intentionally does not duplicate those details.
- The main agent always owns boundary decisions, integration, unified verification, and final delivery.

## Instruction Priority

系统安全策略 > 用户当轮指令 > 最近的 `AGENTS.md` > 根目录 `AGENTS.md` > `workflow.md` > `docs/` / `README.md`

补充口径：判断“项目目标 / 阶段任务”时，以 `README.md` 与 `docs/plans/` 为准；判断“当前已实现事实”时，以仓库代码、配置、脚本为准。

## 图谱随数据进化

BaiCao 的知识图谱跟随具体数据结构逐渐进化。清洗新源时增改实体类型、关系类型、属性是正常迭代。

每次迭代的真源：

- **实体类型、关系类型、属性** 的单一真源是 `packages/graph_schema/`（`constants.py` 中的 `NodeType` / `EdgeType`、节点/关系属性模型、`graph_i18n.py`）。
- 先改该共享图模型包，再让来源适配器产出记录。
- 来源适配器（`packages/data_ingestion/`）不得私自发明节点类型、关系类型或对外属性名。
- 产出记录里的 `node_type` / `edge.type` 只能是真源枚举里已声明的值。
- 每个数据源有一份结构一致的 agent 工作目录：`SOURCE.md`（身份）、`VIEW.md`（展示口径）、`work/`（队列与抽取中间态）、`processed/latest/`（可导入快照）。布局由 `data_ingestion.source_layout` 校验。

## Red Lines

- 不提交密钥、密码、token、PII 或未脱敏配置
- 错误必须可见，不允许静默吞错或伪造结果
- 不执行破坏性回滚（`git reset --hard`、`git checkout --`）；未经明确要求不 push
- 不把规划中的能力写成“当前事实”
- 不在未更新 `docs/plans/` 实施证据和验收结果的情况下把计划或验收文档标记为完成
- 无法验证时必须写出未验证项、原因及可复现命令

## Delivery

- 最终回复包含：改了什么 / 为什么、影响范围、如何验证、回滚点
- 若本轮未完成，需明确说明当前进度、下一步、已验证项与阻塞 / 风险
- 引用文件使用可定位路径（如 `packages/api/app/schemas/chat.py`）
- 默认中文；简洁、直接、可执行
