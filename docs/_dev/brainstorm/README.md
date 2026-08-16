# Brainstorm 文档索引

本目录存放产品设计阶段的 Brainstorming 产出物。

---

## Product Owner 分析

**主题**: 图谱数据驱动的中药材知识问答产品 - 核心价值、功能与前端视图

**生成日期**: 2026-03-19

**文档列表**:

| 文件 | 内容 |
|------|------|
| [guidance-specification.md](./product-owner/guidance-specification.md) | 产品讨论框架与议题定义 |
| [analysis.md](./product-owner/analysis.md) | 主索引文档 |
| [analysis-value-assessment.md](./product-owner/analysis-value-assessment.md) | 核心价值评估、OKR框架 |
| [analysis-user-stories.md](./product-owner/analysis-user-stories.md) | 14个用户故事含验收标准 |
| [analysis-feature-prioritization.md](./product-owner/analysis-feature-prioritization.md) | MoSCoW/RICE优先级、三版发布计划 |
| [analysis-stakeholder-requirements.md](./product-owner/analysis-stakeholder-requirements.md) | 7类用户分析、功能/非功能需求 |
| [analysis-recommendations.md](./product-owner/analysis-recommendations.md) | 界面原型草稿、风险缓解、里程碑 |

---

## System Architect 分析

**主题**: 图谱数据驱动的中药材知识问答产品 - 系统架构设计

**生成日期**: 2026-03-19

**架构决策**:
- **架构模式**: Modular Monolith (模块化单体)
- **通信模式**: Event-Driven (事件驱动)
- **数据存储**: Neo4j (图谱) + PostgreSQL (结构化) + Redis (缓存)
- **部署环境**: 私有服务器

**文档列表**:

| 文件 | 内容 |
|------|------|
| [system-architect-context.md](./system-architect/system-architect-context.md) | 架构上下文与决策 |
| [analysis.md](./system-architect/analysis.md) | 主索引与评估概览 |
| [architecture-design.md](./system-architect/architecture-design.md) | 详细架构设计 |
| [integration-plan.md](./system-architect/integration-plan.md) | 集成与事件驱动设计 |

**核心架构图**:
```
┌─────────────────────────────────────────────────────┐
│                   API Gateway Layer                  │
│                      (FastAPI)                       │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│              Application Layer (kg/qa/review/provenance) │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │   kg   │  │   qa   │  │ review │  │provan. │   │
│  └────────┘  └────────┘  └────────┘  └────────┘   │
│                      │                               │
│              ┌───────▼───────┐                      │
│              │   Event Bus   │                      │
│              │ (Redis Pub/Sub)│                      │
│              └───────────────┘                      │
└─────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                    Data Layer                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  Neo4j  │  │postgres │  │  Redis  │            │
│  │ (图谱)  │  │ (结构化) │  │ (缓存)  │            │
│  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────┘
```

---

**状态**: 已归档。2026-03 产品/架构分析，稳定口径已毕业到 `docs/architecture/` 与根 `README.md`。不要当当前任务真源。当前任务看 `docs/superpowers/plans/README.md`。
**工作流会话**: WFS-2026-03-19-001
