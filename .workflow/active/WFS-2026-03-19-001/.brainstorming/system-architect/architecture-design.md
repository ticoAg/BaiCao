# Architecture Design: 图谱数据驱动的中药材知识问答产品

**Framework Reference**: @../guidance-specification.md

---

## 1. System Architecture Overview

### 1.1 Architecture Pattern: Modular Monolith

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                        │
│                    (FastAPI / Uvicorn)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │   kg     │  │   qa     │  │  review  │  │provenance│        │
│  │  模块    │  │  模块    │  │   模块   │  │   模块   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│         │            │            │            │               │
│         └────────────┴────────────┴────────────┘               │
│                          │                                      │
│              ┌───────────▼───────────┐                         │
│              │     Event Bus         │                         │
│              │  (Redis Pub/Sub)       │                         │
│              └───────────▲───────────┘                         │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                     Data Layer                                  │
│  ┌──────────────────┐    │    ┌──────────────────┐             │
│  │     Neo4j        │◄───┴───►│   PostgreSQL    │             │
│  │  (知识图谱)      │         │  (结构化数据)    │             │
│  └──────────────────┘         └──────────────────┘             │
│                                                              ───┘
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │     Redis        │         │   File Storage   │             │
│  │  (缓存/会话)     │         │   (证据文件)      │             │
│  └──────────────────┘         └──────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Domain Module Boundaries

| 模块 | 职责 | 核心实体 | 主要接口 |
|------|------|----------|----------|
| **kg** | 知识图谱管理 | Herb, Property, Relationship, Source | CRUD, Graph Query |
| **qa** | 问答引擎 | Question, Answer, ReasoningChain | Ask, Explain, Trace |
| **review** | 专家审查 | ReviewTask, ReviewComment, Approval | Submit, Approve, Reject |
| **provenance** | 溯源追踪 | Evidence, Source, ProvenanceChain | Query, Link, Validate |

---

## 2. Data Architecture

### 2.1 Neo4j Role (Knowledge Graph)

**数据模型**:

```cypher
// 实体类型
(:Herb {herb_id, name, latin_name, category, ...})
(:Property {property_id, name, value, unit, ...})
(:Source {source_id, title, author, published_date, ...})
(:Evidence {evidence_id, description, confidence, ...})

// 关系类型
(:Herb)-[:HAS_PROPERTY {evidence_id}]->(:Property)
(:Herb)-[:RELATED_TO {relationship_type, evidence_id}]->(:Herb)
(:Evidence)-[:FROM_SOURCE]->(:Source)
(:Property)-[:ATTRIBUTED_TO]->(:Evidence)
```

**索引策略**:
```cypher
CREATE INDEX herb_name FOR (h:Herb) ON (h.name);
CREATE INDEX herb_id FOR (h:Herb) ON (h.herb_id);
CREATE INDEX source_id FOR (s:Source) ON (s.source_id);
```

### 2.2 PostgreSQL Role (Relational Data)

**核心表结构**:

```sql
-- 用户与会话
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(100),
    role VARCHAR(20), -- 'user', 'expert', 'admin'
    created_at TIMESTAMP
);

CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    created_at TIMESTAMP,
    context JSONB
);

-- 问答历史
CREATE TABLE qa_history (
    history_id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id),
    question TEXT,
    answer TEXT,
    reasoning_chain JSONB,
    herb_id UUID,
    created_at TIMESTAMP
);

-- 审查任务
CREATE TABLE review_tasks (
    task_id UUID PRIMARY KEY,
    evidence_id UUID,
    status VARCHAR(20), -- 'pending', 'approved', 'rejected'
    reviewer_id UUID REFERENCES users(user_id),
    comments TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 2.3 Redis Role (Cache & Session)

| 用途 | Key Pattern | TTL | 说明 |
|------|-------------|-----|------|
| 图查询缓存 | `cache:kg:{herb_id}` | 1h | 热点药材数据 |
| 会话存储 | `session:{session_id}` | 24h | 用户对话上下文 |
| 事件分发 | `queue:events` | - | 事件持久化队列 |
| 分布式锁 | `lock:{resource}` | 30s | 跨容器协调 |

### 2.4 Data Consistency Strategy

**双写一致性**: 采用 **Eventual Consistency** + **补偿事务**

```
1. 请求写入 PostgreSQL
2. 发布 DomainEvent 到 Event Bus
3. Event Handler 异步更新 Neo4j
4. 失败时重试 (指数退避)
5. 补偿事件修正不一致状态
```

---

## 3. Event-Driven Architecture

### 3.1 Event Bus Design

**事件类型分类**:

| 类别 | 事件 | 触发时机 |
|------|------|----------|
| **Knowledge** | `HerbCreated`, `HerbUpdated`, `RelationshipAdded` | kg 模块 |
| **Review** | `ReviewRequested`, `ReviewCompleted` | review 模块 |
| **Provenance** | `EvidenceLinked`, `ChainValidated` | provenance 模块 |
| **QA** | `QuestionAsked`, `AnswerGenerated` | qa 模块 |

**事件结构**:

```python
class DomainEvent(BaseModel):
    event_id: UUID
    event_type: str
    aggregate_id: str
    payload: dict
    metadata: EventMetadata
    timestamp: datetime

class EventMetadata(BaseModel):
    correlation_id: UUID
    causation_id: UUID | None
    user_id: UUID | None
    source: str  # module name
```

### 3.2 Event Flow Examples

**知识更新触发溯源重建**:

```
User Update Request
       │
       ▼
┌──────────────┐
│   kg 模块     │
│ UpdateEntity  │
└──────┬───────┘
       │ emit: HerbUpdatedEvent
       ▼
┌──────────────┐
│  Event Bus   │
│ (Redis Pub/Sub)│
└──────┬───────┘
       │ subscribe: ProvenanceHandler
       ▼
┌──────────────┐
│provenance模块 │
│RebuildChain  │
└──────────────┘
```

**问答触发审查流程**:

```
User Question
       │
       ▼
┌──────────────┐
│   qa 模块     │
│ GenerateAnswer│
└──────┬───────┘
       │ emit: AnswerGeneratedEvent
       ▼
┌──────────────┐     emit:     ┌──────────────┐
│  Event Bus   │──────────────►│ review 模块  │
│              │               │CreateReviewTask│
└──────────────┘               └──────────────┘
```

---

## 4. API Layer Design

### 4.1 API Structure

```
/api/v1/
├── kg/                    # 知识图谱接口
│   ├── herbs/             # 药材管理
│   ├── properties/        # 属性管理
│   ├── relationships/     # 关系管理
│   └── graph/            # 图谱查询
│
├── qa/                    # 问答接口
│   ├── ask/              # 提问
│   ├── history/          # 历史记录
│   └── trace/            # 推理链追踪
│
├── review/               # 审查接口
│   ├── tasks/            # 审查任务
│   ├── approve/          # 审批
│   └── comments/         # 审查意见
│
├── provenance/           # 溯源接口
│   ├── evidence/         # 证据查询
│   ├── chains/           # 溯源链
│   └── sources/          # 来源管理
│
└── auth/                 # 认证接口
```

### 4.2 Core API Contracts

**POST /api/v1/qa/ask**

```python
# Request
{
    "question": "人参有哪些主要功效？",
    "session_id": "uuid",  # optional
    "include_provenance": true
}

# Response
{
    "answer_id": "uuid",
    "answer": "人参的主要功效包括...",
    "reasoning_chain": [
        {
            "step": 1,
            "herb": "人参",
            "property": "大补元气",
            "evidence_id": "uuid",
            "confidence": 0.95
        }
    ],
    "provenance": {
        "chains": [...],
        "sources": [...]
    }
}
```

---

## 5. Deployment Architecture

### 5.1 Docker Compose Structure

```yaml
# infra/docker-compose.yml
services:
  api:
    build: ./packages/api
    ports:
      - "8000:8000"
    depends_on:
      - neo4j
      - postgres
      - redis
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - POSTGRES_URI=postgresql://user:pass@postgres:5432/baicao

  web:
    build: ./packages/web
    ports:
      - "3000:3000"
    environment:
      - API_BASE_URL=http://api:8000

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  neo4j_data:
  postgres_data:
  redis_data:
```

### 5.2 Environment Configuration

| 环境变量 | 说明 | 示例值 |
|----------|------|--------|
| `NEO4J_URI` | Neo4j 连接地址 | `bolt://neo4j:7687` |
| `POSTGRES_URI` | PostgreSQL 连接字符串 | `postgresql://...` |
| `REDIS_URL` | Redis 连接地址 | `redis://redis:6379` |
| `LLM_API_KEY` | LLM API 密钥 | (敏感) |
| `LLM_PROVIDER` | LLM 提供商 | `openai` / `local` |

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

- **认证**: JWT Token (短期) + Refresh Token (长期)
- **授权**: RBAC (user/expert/admin 三级)
- **API 安全**: 速率限制、输入校验、HTTPS

### 6.2 Data Protection

| 层级 | 措施 |
|------|------|
| 传输层 | TLS 1.3 |
| 存储层 | 敏感字段加密 |
| API 层 | 输入校验、SQL 注入防护 |
| 敏感输出 | 脱敏、限长 |

---

## 7. Monitoring & Observability

### 7.1 Health Checks

```python
# /health endpoint
{
    "status": "healthy",
    "dependencies": {
        "neo4j": "connected",
        "postgres": "connected",
        "redis": "connected"
    },
    "version": "1.0.0"
}
```

### 7.2 Metrics Strategy

| 指标类别 | 指标项 | 采集方式 |
|----------|--------|----------|
| **请求指标** | QPS, 延迟 P95/P99 | 中间件 |
| **业务指标** | 问答数, 审查通过率 | 业务事件 |
| **资源指标** | CPU, 内存, 连接池 | 系统采集 |
| **图谱指标** | 节点数, 查询延迟 | Neo4j metrics |

### 7.3 Logging Strategy

- **格式**: JSON structured logging
- **级别**: DEBUG/INFO/WARN/ERROR
- **追踪**: request_id 透传，关联整个请求生命周期
- **持久化**: 文件日志 + 结构化日志收集 (可选 ELK)

---

## 8. Implementation Phases

### Phase 1: Foundation (2-3 weeks)
- [ ] Modular Monolith 项目骨架搭建
- [ ] Docker Compose 环境配置
- [ ] 事件总线基础设施实现
- [ ] 基础 API 骨架与健康检查

### Phase 2: Core Modules (4-6 weeks)
- [ ] kg 模块: Neo4j 集成，基础 CRUD
- [ ] qa 模块: 问答 API，LangChain 集成
- [ ] provenance 模块: 证据链管理

### Phase 3: Review & Polish (2-3 weeks)
- [ ] review 模块: 审查工作流
- [ ] 前端界面完善
- [ ] 监控与日志集成

### Phase 4: Production Hardening (1-2 weeks)
- [ ] 性能优化 (缓存、索引)
- [ ] 安全加固
- [ ] 文档完善
