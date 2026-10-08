# 白草药坛 BaiCao ShiTan

面向中医药场景的 Agent 驱动可信知识搜集与利用平台。

![Status](https://img.shields.io/badge/status-MVP%20early-f59e0b)
![Architecture](https://img.shields.io/badge/architecture-Modular%20Monolith-2563eb)
![Stack](https://img.shields.io/badge/stack-FastAPI%20%7C%20React%20%7C%20Neo4j%20%7C%20PostgreSQL-0f766e)
![LLM](https://img.shields.io/badge/LLM-Agent%20Workflow%20%2B%20OpenAI-7c3aed)

> 白草不是再做一个中医药聊天页，而是把高密度、强关联的中医药知识，变成可搜集、可利用、可沉淀、结果可信的知识资产。

## 做什么

中医药知识密度高、来源散、关系复杂，检索和复用成本高。白草把图谱和 Agent 绑在一起：

- 图谱表达药材、功效、成分、配伍等实体与路径
- Agent 把查、串、比、整、用做成任务流
- 来源、证据、验证状态跟着走，结论可复核

适合研究 / 知识工程团队，以及需要在中医药场景里做检索与探索的专业用户。

## 一轮问答怎么走

以用户问「黄芪的性味归经是什么？」为例。问答模型负责查图和写结论，每到关键一步就调用 `judge`，由决策模型（TypeSafe）回答写死的判定题，再按换算出的下一步行动。查图返回的内容按药典数据在图里的实际结构做了简化，判定的数值只是示意。

**1. 查图之前**：问答模型调用 `judge(intake)`。决策模型只看到用户原话，这时还没有查图记录。

- 答案：任务是「图谱检索」；需要检索 0.95（算是）；名称具体程度 2（「黄芪」是明确的名称）。
- 下一步：先用 `search_nodes` 找到「黄芪」，不要直接作答。

**2. 第一次查图**：`search_nodes(query="黄芪")`，找到药材「黄芪」，标识 `药材-黄芪`。

**3. 查完判定**：`judge(evidence)`。

- 答案：实体已找到；证据不够（只有名称，还没看到性味和归经）；下一步「继续检索」。
- 下一步：不要作答，补查缺的那部分。

**4. 第二次查图**：`expand_neighbors(node_id="药材-黄芪", depth=2)`。药典数据里，性味和归经挂在饮片上，不在药材上，所以要向外看两层：

```text
药材 黄芪 ─具有饮片→ 饮片 黄芪 ─具有性味→ 甘
                                ─归于经脉→ 肺经、脾经
药材 黄芪 ─由证据支持→ 证据「黄芪条目证据」（药典原文）
```

**5. 再次查完判定**：实体已找到；证据够了；下一步「可以作答」，性味、归经和出处都在查到的内容里。

**6. 发布前判定**：问答模型写好草稿，把全文放进 `judge(claim)` 的 `draft`：

> 黄芪性味甘，归肺经、脾经。

- 三道题：没有写出查图结果之外的内容；没有新编剂量或出处；可以发布。三道都通过，发布。
- 如果草稿多写一句「常与当归配伍」，查到的内容里没有这条关系，判定不通过。问答模型要删掉这句，再判一次。

**7. 用户看到的**：结论，加上一条出处。证据摘录取自「黄芪条目证据」的原文。药典数据没有「来源于」关系，所以来源取节点上的导入源 `national-standard-2022-pharmacopoeia`。

### 换个问法会怎样

| 用户问 | 哪一步拦下 | 结果 |
| --- | --- | --- |
| 我气虚，该吃黄芪吗？ | 查图之前：超出图谱问答 | 不查图，说明只回答图谱里已有的知识，不给个人用药建议 |
| 它能治什么？（前面没有提过任何药） | 查图之前：需要澄清 | 不查图，追问要查哪味药或哪张方 |
| 问一味图谱里没有的药 | 查完之后：说明没有图谱证据 | 换名称再查仍然没有，就写明当前没有图谱证据；写明了才能通过发布判定 |

判定题、查图工具和出处规则的完整说明见 [架构文档](docs/architecture/README.md#图谱-agent)。

## 当前阶段

`MVP early`。已经能跑：monorepo 本地开发栈、图谱问答主链路、数据验证与处理工作台。2022 年药典（605 条目）和道医苏子阳 v3 已导入图谱。

问答基于 pydantic-ai-slim，用只读工具查 Neo4j，出处从查到的子图生成。知识数据集放在 Hugging Face 私有仓库，其中脱敏后的公开层已通过 Dataset Viewer 验收。第三个数据源 DragonTCM 已在本地完成清洗；上游没有许可证，不进公开层。

多 worker 会话共享、专家治理、鉴权、事件驱动与监控还没做。这是研发仓库，不是生产系统。

## 快速开始

需要 Python 3.12+、Node.js 22+、pnpm、Docker。推荐 `uv`。

```bash
cp .env.schema .env
cp infra/.env.schema infra/.env
make deps up
make stack up
```

`.env` 里补 Universal Auth（`INFISICAL_CLIENT_ID` / `INFISICAL_CLIENT_SECRET`）。API 用官方 Python SDK 拉 secret，不需要安装 Infisical CLI。不用 Infisical、改端口、手动起进程、样例数据和验证命令见 [docs/local-development.md](docs/local-development.md)。

- Web: <http://localhost:3000>
- API: <http://localhost:8000>

## 仓库结构

```text
BaiCao/
├── packages/
│   ├── api/              # FastAPI 后端
│   ├── web/              # React 前端
│   ├── shared/           # 跨端共享类型
│   ├── knowledge_model/  # 共享知识模型
│   ├── data_ingestion/   # 数据采集
│   └── db/               # Cypher、导入样例
├── infra/                # Docker Compose
├── datasets/             # 本地数据集工作目录（不进 Git，发布到 Hugging Face）
└── docs/                 # 架构、验收、计划
```

## 文档

| 想看什么 | 去哪 |
| --- | --- |
| 文档门户 | [docs/README.md](docs/README.md) |
| 本地开发 | [docs/local-development.md](docs/local-development.md) |
| 架构 | [docs/architecture/README.md](docs/architecture/README.md) |
| 验收 | [docs/acceptance/README.md](docs/acceptance/README.md) |
| Agent 规范 | [AGENTS.md](AGENTS.md) |
