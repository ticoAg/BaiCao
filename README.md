# 白草药坛 BaiCao ShiTan

面向中医药场景的 Agent 驱动可信知识搜集与利用平台。

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

以用户问「黄芪的性味归经是什么？」为例。问答模型负责查图和写结论；每到菱形处，它调用 `judge`，由决策模型（TypeSafe）回答写死的判定题，运行时再把答案换算成下一步。实线是这个问题实际走的路，虚线是换个问法时的走向。

```mermaid
flowchart TD
    ask["用户：黄芪的性味归经是什么？"] --> intake{"查图之前<br/>judge(intake)"}
    intake -.->|"要求诊断或开方<br/>例：帮我开一张方"| decline["不查图，说明只回答图谱里已有的知识，不诊断、不开方"]
    intake -.->|"需要澄清<br/>例：它能治什么？"| clarify["不查图，追问要查哪味药"]
    intake -->|"图谱检索；需要检索 0.95；名称具体程度 2"| s1["search_nodes(query=黄芪)<br/>找到药材「黄芪」，标识 药材-黄芪"]
    s1 --> e1{"查完<br/>judge(evidence)"}
    e1 -.->|"查不到<br/>例：图谱里没有的药"| missing["写明当前没有图谱证据"]
    e1 -->|"只有名称，缺性味和归经：继续检索"| s2["expand_neighbors(药材-黄芪, depth=2)<br/>饮片「黄芪」：性味 甘；归经 肺经、脾经<br/>证据「黄芪条目证据」"]
    s2 --> e2{"查完<br/>judge(evidence)"}
    e2 -->|"证据够了：可以作答"| draft["草稿：黄芪性味甘，归肺经、脾经。"]
    draft --> claim{"发布前<br/>judge(claim)"}
    missing -.-> claim
    claim -.->|"草稿多写了「常与当归配伍」：不通过"| fix["删掉查图结果里没有的内容"]
    fix -.-> claim
    claim -->|"没超出子图，没编造：可以发布"| answer["用户看到：结论和出处<br/>证据摘录：黄芪条目证据原文<br/>来源：national-standard-2022-pharmacopoeia"]
```

几点说明：

- 带个人情况的问题，比如「我气虚，该吃黄芪吗？」，也走实线：按图谱里黄芪的功效和主治作答，不替用户决定该不该吃，并说明是否适用需由医生判断。
- 第二次查图要看两层（`depth=2`），因为药典数据里性味和归经挂在饮片上，不在药材上。
- 药典数据没有「来源于」关系，所以来源取节点上的导入源。

查图结果按药典数据在图里的实际结构做了简化，判定数值只是示意。

判定题、查图工具和出处规则的完整说明见 [架构文档](docs/architecture/README.md#图谱-agent)。

## 快速开始

需要 Python 3.12+、Node.js 22+、pnpm、Docker。推荐 `uv`。

```bash
cp .env.schema .env
cp infra/.env.schema infra/.env
make deps up
make stack up
```

环境变量（含 Infisical）、访问地址、手动启动、样例数据和验证命令见 [docs/local-development.md](docs/local-development.md)。

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
