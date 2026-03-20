# System Architect Analysis: 图谱数据驱动的中药材知识问答产品

**Framework Reference**: @../guidance-specification.md

**Session**: WFS-2026-03-19-001
**Role**: System Architect
**Date**: 2026-03-19

---

## Architecture Assessment

### System Design Patterns

本产品采用 **Modular Monolith** 架构模式，结合 **Event-Driven** 通信模式，在保持系统简单性的同时实现领域模块化拆分和异步流程解耦。

**架构核心特征**:
- **单一部署单元**: 所有模块打包在同一进程，简化部署和运维
- **领域边界清晰**: kg (知识图谱)、qa (问答)、review (审查)、provenance (溯源) 四大领域模块
- **事件总线解耦**: 模块间通过事件总线异步通信，降低耦合度

### Scalability Considerations

| 维度 | 当前设计 | 扩展方向 |
|------|----------|----------|
| 用户规模 | 初期小规模 | 水平扩展 API 服务 |
| 数据规模 | 万级实体 | Neo4j 分片 / PostgreSQL 分库 |
| 并发查询 | 图谱查询为主 | 引入 Redis 缓存热点数据 |
| 异步任务 | 事件驱动 | 独立 Worker 服务分离 |

### Integration Patterns

模块间通信采用 **事件驱动架构**，核心事件包括:

```python
# 知识更新事件
KnowledgeUpdatedEvent(herb_id, changes, source, timestamp)

# 审查触发事件
ReviewRequestedEvent(evidence_id, review_type, priority)

# 溯源查询事件
ProvenanceQueryEvent(session_id, entity_id, depth)
```

---

## Technology Stack Evaluation

### Technology Selection

| 层级 | 技术选型 | 理由 |
|------|----------|------|
| API 层 | FastAPI | 高性能异步框架，与现有项目一致 |
| 前端 | React | 已有项目结构，生态成熟 |
| 图数据库 | Neo4j | 中药材实体关系建模天然适配图结构 |
| 关系数据库 | PostgreSQL | 结构化数据、用户数据、对话历史 |
| 事件总线 | Redis Pub/Sub + 持久化队列 | 轻量级实现，满足异步通信需求 |
| 缓存层 | Redis | 图查询结果缓存、Session 存储 |

### Infrastructure Requirements

- **部署环境**: 私有服务器单机部署
- **容器化**: Docker Compose 统一编排
- **监控**: Prometheus + Grafana (可选，轻量级)
- **日志**: 结构化日志 + ELK Stack (可选)

---

## Technical Feasibility Analysis

### Implementation Complexity

| 模块 | 复杂度 | 关键挑战 |
|------|--------|----------|
| kg 图谱 | 中 | Neo4j Schema 设计、Cypher 查询优化 |
| qa 问答 | 高 | LLM 集成、推理链生成、溯源关联 |
| review 审查 | 低 | 状态机、工作流引擎 |
| provenance 溯源 | 中 | 证据链构建、多源关联 |

### Risk Assessment

| 风险 | 等级 | 缓解策略 |
|------|------|----------|
| 图查询延迟高 | 中 | 索引优化、热点缓存 |
| LLM 响应质量不稳定 | 高 | 提示词工程、审查流程兜底 |
| 数据一致性 | 中 | 最终一致性 + 补偿事务 |
| 知识更新丢失 | 低 | 事件持久化 + 重试机制 |

---

## Quality and Performance Framework

### Non-Functional Requirements

| 指标 | 目标值 | 说明 |
|------|--------|------|
| API 响应时间 | P95 < 500ms | 图谱查询类接口 |
| 前端加载时间 | < 3s | 首屏渲染 |
| 系统可用性 | 99.9% | 单机部署降级目标 |
| 数据一致性 | 最终一致 | 事件驱动架构 |

### Monitoring Strategy

- **健康检查**: `/health` 端点检测 Neo4j/PostgreSQL 连接
- **请求追踪**: request_id 透传，关联全链路日志
- **指标采集**: Prometheus metrics 暴露关键指标
- **告警规则**: 错误率、延迟阈值、连接池状态

---

## Recommendations

### Architectural Approach

1. **分层模块化**: API 层 → Service 层 → Domain 层，依赖方向单一
2. **事件优先**: 模块间通信优先使用事件，命令作为补充
3. **数据库分离**: Neo4j 与 PostgreSQL 职责明确，避免跨库事务

### Implementation Strategy

**Phase 1 - Foundation**:
- 搭建 Modular Monolith 骨架
- 实现事件总线基础设施
- 部署 Docker Compose 环境

**Phase 2 - Core Features**:
- kg 模块: 实体管理、关系操作
- qa 模块: 问答 API、溯源关联
- provenance 模块: 证据链查询

**Phase 3 - Enhanced Features**:
- review 模块: 专家审查工作流
- 缓存优化
- 监控完善

### Key Architectural Decisions

1. **事件总线选型**: Redis Pub/Sub (开发阶段) → 持久化队列 (生产)
2. **图数据库角色**: 知识图谱存储与查询，不做事务性存储
3. **双写一致性**: 通过事件补偿实现最终一致
4. **LLM 集成**: LangChain 抽象，保持可替换性

---

## Sub-Documents

- @architecture-design.md - Detailed architecture design
- @integration-plan.md - Integration and event-driven design
