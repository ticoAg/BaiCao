# Integration Plan: 事件驱动与模块集成设计

**Framework Reference**: @../guidance-specification.md

---

## 1. Integration Architecture Overview

### 1.1 Integration Principles

| 原则 | 说明 | 实施方式 |
|------|------|----------|
| **松耦合** | 模块间无直接依赖 | 通过事件总线通信 |
| **事件优先** | 同步命令作为补充 | DomainEvent + Command |
| **可追踪** | 事件链路可追溯 | correlation_id 透传 |
| **幂等性** | 事件处理可重复执行 | 幂等处理器设计 |
| **最终一致** | 跨模块数据最终一致 | 补偿事务 + 重试 |

### 1.2 Module Dependency Graph

```
        ┌─────────────────────────────────────────┐
        │              API Gateway               │
        └──────────────────┬────────────────────┘
                           │
        ┌──────────────────┼────────────────────┐
        │                  │                    │
        ▼                  ▼                    ▼
   ┌─────────┐       ┌─────────┐        ┌─────────┐
   │   kg    │       │   qa    │        │ review  │
   │  模块   │       │  模块   │        │  模块   │
   └────┬────┘       └────┬────┘        └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Event Bus   │
                    │ (Redis Pub/  │
                    │  Sub+Queue)  │
                    └──────▲──────┘
                           │
        ┌──────────────────┼────────────────────┐
        │                  │                    │
        ▼                  ▼                    ▼
   ┌─────────┐       ┌─────────┐        ┌─────────┐
   │provenance│      │  cache  │        │notify   │
   │  模块   │       │  handler│        │handler  │
   └────┬────┘       └─────────┘        └─────────┘
        │
        ▼
   ┌─────────┐
   │  Neo4j  │
   └─────────┘
```

---

## 2. Event Bus Implementation

### 2.1 Event Bus Architecture

**开发阶段**: Redis Pub/Sub (简单、快速)
**生产阶段**: Redis + 持久化队列 (如 Celery + Redis)

```
┌─────────────────────────────────────────────────────┐
│                    Event Bus                         │
│  ┌─────────────┐    ┌─────────────┐                │
│  │ Publisher   │───►│  Subscriber │                │
│  │ (Module)    │    │ (Handler)   │                │
│  └─────────────┘    └─────────────┘                │
│         │                 ▲                         │
│         │                 │                         │
│         ▼                 │                         │
│  ┌─────────────────────────────────────┐           │
│  │         Redis Pub/Sub               │           │
│  │    (Channel: domain_events)         │           │
│  └─────────────────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

### 2.2 Event Schema Definition

```python
# shared/events/base.py
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from enum import Enum

class EventType(str, Enum):
    # Knowledge events
    HERB_CREATED = "herb.created"
    HERB_UPDATED = "herb.updated"
    HERB_DELETED = "herb.deleted"
    RELATIONSHIP_ADDED = "relationship.added"

    # QA events
    QUESTION_ASKED = "question.asked"
    ANSWER_GENERATED = "answer.generated"

    # Review events
    REVIEW_REQUESTED = "review.requested"
    REVIEW_COMPLETED = "review.completed"

    # Provenance events
    EVIDENCE_LINKED = "evidence.linked"
    CHAIN_REBUILT = "chain.rebuilt"

class DomainEvent(BaseModel):
    """Base class for all domain events"""
    event_id: UUID
    event_type: EventType
    aggregate_id: str  # entity ID this event relates to
    payload: dict
    metadata: EventMetadata
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EventMetadata(BaseModel):
    """Metadata attached to every event for tracing"""
    correlation_id: UUID | None = None
    causation_id: UUID | None = None
    user_id: UUID | None = None
    source: str  # originating module name
    version: str = "1.0"
```

### 2.3 Event Example Payloads

```python
# Knowledge Events
class HerbCreatedEvent(DomainEvent):
    payload: {
        "herb_id": "uuid",
        "name": "人参",
        "latin_name": "Panax ginseng",
        "category": "补气药",
        "properties": [...],
        "relationships": [...]
    }

class RelationshipAddedEvent(DomainEvent):
    payload: {
        "source_herb_id": "uuid",
        "target_herb_id": "uuid",
        "relationship_type": "相似功效",
        "evidence_id": "uuid",
        "confidence": 0.85
    }

# QA Events
class AnswerGeneratedEvent(DomainEvent):
    payload: {
        "question": "人参有哪些功效？",
        "answer": "人参大补元气...",
        "herb_id": "uuid",
        "reasoning_chain": [
            {
                "step": 1,
                "inference": "人参具有大补元气功效",
                "evidence_id": "uuid",
                "confidence": 0.95
            }
        ],
        "requires_review": true  # low confidence triggers review
    }

# Review Events
class ReviewRequestedEvent(DomainEvent):
    payload: {
        "evidence_id": "uuid",
        "review_type": "quality_assurance",
        "priority": "normal",
        "triggered_by": "answer_generation",
        "context": {...}
    }

# Provenance Events
class EvidenceLinkedEvent(DomainEvent):
    payload: {
        "herb_id": "uuid",
        "evidence_id": "uuid",
        "source_id": "uuid",
        "link_type": "property_attribute"
    }
```

---

## 3. Module Integration Patterns

### 3.1 KG Module Integration

**职责**: 知识图谱的 CRUD 操作与图查询

**发布的事件**:
- `HerbCreatedEvent`
- `HerbUpdatedEvent`
- `RelationshipAddedEvent`

**订阅的事件**:
- `ReviewCompletedEvent` (更新知识状态)
- `ChainRebuiltEvent` (更新关联)

```python
# kg/events.py
class KGEventPublisher:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def create_herb(self, herb_data: HerbCreate) -> Herb:
        herb = await self.kg_service.create(herb_data)
        await self.event_bus.publish(HerbCreatedEvent(
            event_id=uuid4(),
            event_type=EventType.HERB_CREATED,
            aggregate_id=str(herb.herb_id),
            payload=herb.model_dump(),
            metadata=EventMetadata(source="kg")
        ))
        return herb
```

### 3.2 QA Module Integration

**职责**: 问答生成、推理链构建

**发布的事件**:
- `QuestionAskedEvent`
- `AnswerGeneratedEvent`

**订阅的事件**:
- `HerbUpdatedEvent` (更新缓存)
- `ReviewCompletedEvent` (重新生成答案)

```python
# qa/events.py
class QAEventHandler:
    def __init__(self, event_bus: EventBus, kg_service: KGService):
        self.event_bus = event_bus
        self.kg_service = kg_service

    @event_bus.subscribe(EventType.HERB_UPDATED)
    async def on_herb_updated(self, event: HerbUpdatedEvent):
        # Invalidate cached Q&A related to this herb
        await self.cache.invalidate(f"qa:herb:{event.aggregate_id}")

    @event_bus.subscribe(EventType.REVIEW_COMPLETED)
    async def on_review_completed(self, event: ReviewCompletedEvent):
        if event.payload.get("regenerate_answer"):
            # Trigger answer regeneration for reviewed evidence
            await self.regenerate_answer(event.payload["evidence_id"])
```

### 3.3 Review Module Integration

**职责**: 专家审查工作流

**发布的事件**:
- `ReviewRequestedEvent`
- `ReviewCompletedEvent`

**订阅的事件**:
- `AnswerGeneratedEvent` (低置信度自动触发审查)
- `EvidenceLinkedEvent` (新证据触发审查)

```python
# review/events.py
class ReviewWorkflow:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def submit_for_review(self, evidence_id: UUID, context: dict):
        # Create review task
        task = await self.create_task(evidence_id, context)

        # Publish event for downstream handlers
        await self.event_bus.publish(ReviewRequestedEvent(
            event_id=uuid4(),
            event_type=EventType.REVIEW_REQUESTED,
            aggregate_id=str(task.task_id),
            payload={
                "task_id": str(task.task_id),
                "evidence_id": str(evidence_id),
                "context": context
            },
            metadata=EventMetadata(source="review")
        ))

        return task

    async def complete_review(self, task_id: UUID, decision: ReviewDecision):
        task = await self.update_task_status(task_id, decision)

        await self.event_bus.publish(ReviewCompletedEvent(
            event_id=uuid4(),
            event_type=EventType.REVIEW_COMPLETED,
            aggregate_id=str(task.task_id),
            payload={
                "task_id": str(task.task_id),
                "decision": decision.value,
                "regenerate_answer": decision == ReviewDecision.REJECTED
            },
            metadata=EventMetadata(source="review")
        ))

        return task
```

### 3.4 Provenance Module Integration

**职责**: 证据链构建与溯源查询

**发布的事件**:
- `EvidenceLinkedEvent`
- `ChainRebuiltEvent`

**订阅的事件**:
- `HerbUpdatedEvent` (重建受影响链)
- `RelationshipAddedEvent` (扩展链)
- `ReviewCompletedEvent` (验证链)

```python
# provenance/events.py
class ProvenanceEventHandler:
    def __init__(self, event_bus: EventBus, neo4j_client: Neo4jClient):
        self.event_bus = event_bus
        self.neo4j_client = neo4j_client

    @event_bus.subscribe(EventType.HERB_UPDATED)
    async def on_herb_updated(self, event: HerbUpdatedEvent):
        # Rebuild provenance chains for affected herb
        herb_id = event.aggregate_id
        await self.provenance_service.rebuild_chains(herb_id)

        await self.event_bus.publish(ChainRebuiltEvent(
            event_id=uuid4(),
            event_type=EventType.CHAIN_REBUILT,
            aggregate_id=herb_id,
            payload={"herb_id": herb_id, "chain_version": "new"},
            metadata=EventMetadata(source="provenance")
        ))

    @event_bus.subscribe(EventType.REVIEW_COMPLETED)
    async def on_review_completed(self, event: ReviewCompletedEvent):
        # Validate chains containing reviewed evidence
        evidence_id = event.payload.get("evidence_id")
        if evidence_id:
            await self.validate_chains(evidence_id)
```

---

## 4. Cross-Cutting Concerns

### 4.1 Event Tracing

**Correlation ID Flow**:

```
User Request
    │
    │  X-Correlation-ID: uuid
    ▼
API Gateway ──► Parse correlation_id
    │              │
    │              ▼
    │         Set in context
    │              │
    ▼              ▼
Handler ────────► Emit event with correlation_id
    │              │
    │              ▼
    │         EventHandler receives
    │         event with correlation_id
    │              │
    ▼              ▼
Response ◄────── Log with correlation_id
```

**实现代码**:

```python
# shared/events/tracing.py
from contextvars import ContextVar
from uuid import UUID

correlation_id: ContextVar[UUID | None] = ContextVar("correlation_id", default=None)

class EventBus:
    async def publish(self, event: DomainEvent):
        # Attach correlation ID from context
        if event.metadata.correlation_id is None:
            event.metadata.correlation_id = correlation_id.get()

        # Publish to Redis
        await self.redis.publish(
            "domain_events",
            event.model_dump_json()
        )

    def subscribe(self, event_type: EventType):
        def decorator(handler):
            async def wrapper(event: DomainEvent):
                # Set correlation ID in context for handler
                token = correlation_id.set(event.metadata.correlation_id)
                try:
                    await handler(event)
                finally:
                    correlation_id.reset(token)
            return wrapper
        return decorator
```

### 4.2 Error Handling & Retry

**重试策略**:

```python
# shared/events/retry.py
from tenacity import retry, stop_after_attempt, wait_exponential

class EventHandler:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def handle_with_retry(self, event: DomainEvent):
        try:
            await self.process(event)
        except TransientError as e:
            # Re-queue for retry
            await self.requeue(event)
            raise
        except Exception as e:
            # Log and send to dead letter queue
            await self.send_to_dlq(event, e)
            raise
```

**死信队列 (DLQ)**:

```python
# Events that fail after max retries go to DLQ for manual inspection
DLQ_KEY = "events:dlq"

async def send_to_dlq(self, event: DomainEvent, error: Exception):
    await self.redis.zadd(DLQ_KEY, {
        json.dumps({
            "event": event.model_dump(),
            "error": str(error),
            "failed_at": datetime.utcnow().isoformat()
        }): time.time()
    })
```

### 4.3 Idempotency

**幂等事件处理**:

```python
class IdempotentEventHandler:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.processed_key = "events:processed:{event_id}"

    async def handle(self, event: DomainEvent):
        # Check if already processed
        processed = await self.redis.get(self.processed_key.format(event_id=event.event_id))
        if processed:
            return  # Skip already processed events

        # Process the event
        await self.do_handle(event)

        # Mark as processed with TTL (e.g., 7 days)
        await self.redis.setex(
            self.processed_key.format(event_id=event.event_id),
            7 * 24 * 3600,
            "processed"
        )
```

---

## 5. Data Synchronization Strategy

### 5.1 Neo4j-PostgreSQL Sync

**写入路径**:

```
API Request (Create/Update)
    │
    ▼
┌─────────────────┐
│ PostgreSQL      │  ← Primary write
│ (Transaction)   │
└────────┬────────┘
         │ emit: DomainEvent
         ▼
┌─────────────────┐
│ Event Bus       │
│ (Redis Pub/Sub) │
└────────┬────────┘
         │ subscribe: Neo4jSyncHandler
         ▼
┌─────────────────┐
│ Neo4j           │  ← Secondary write (async)
│ (Eventual)      │
└─────────────────┘
```

**同步处理器**:

```python
class Neo4jSyncHandler:
    async def on_herb_created(self, event: HerbCreatedEvent):
        # Sync herb entity to Neo4j
        await self.neo4j.execute("""
            CREATE (h:Herb {
                herb_id: $herb_id,
                name: $name,
                latin_name: $latin_name,
                category: $category,
                created_at: datetime()
            })
        """, event.payload)

    async def on_relationship_added(self, event: RelationshipAddedEvent):
        # Sync relationship to Neo4j
        await self.neo4j.execute("""
            MATCH (s:Herb {herb_id: $source_id})
            MATCH (t:Herb {herb_id: $target_id})
            CREATE (s)-[:RELATED_TO {
                type: $relationship_type,
                evidence_id: $evidence_id,
                confidence: $confidence
            }]->(t)
        """, event.payload)
```

### 5.2 Consistency Guarantees

| 操作类型 | 一致性模型 | 说明 |
|----------|------------|------|
| 知识写入 | 最终一致 | PostgreSQL 先写，Neo4j 异步同步 |
| 问答查询 | 会话一致 | 同一 session 内的查询看到一致状态 |
| 审查流程 | 强一致 | 审查状态变更在同一事务内 |
| 溯源查询 | 最终一致 | 依赖 Neo4j 数据同步完成 |

---

## 6. API Integration

### 6.1 Internal Service Calls

**服务间调用模式**:

```python
# 同一进程内的模块调用 (直接方法调用)
class KGService:
    async def get_herb(self, herb_id: UUID) -> Herb:
        return await self.repo.find_by_id(herb_id)

# 跨模块通信 (通过事件)
class QAService:
    async def on_review_completed(self, event: ReviewCompletedEvent):
        # Re-generate answer based on reviewed evidence
        evidence = await self.provenance_service.get_evidence(
            event.payload["evidence_id"]
        )
        await self.regenerate(evidence)
```

### 6.2 External API Integration

**LLM 集成 (LangChain)**:

```python
# qa/llm.py
from langchain import LangChain

class LLMService:
    def __init__(self, config: LLMConfig):
        self.chain = LangChain(
            provider=config.provider,
            model=config.model,
            api_key=config.api_key
        )

    async def generate_answer(
        self,
        question: str,
        context: list[dict]
    ) -> AnswerResult:
        prompt = self.build_prompt(question, context)
        response = await self.chain.agenerate([prompt])

        return AnswerResult(
            answer=response.text,
            reasoning_chain=self.extract_chain(response),
            confidence=response.confidence
        )
```

---

## 7. Testing Strategy

### 7.1 Integration Testing

**事件流测试**:

```python
# tests/integration/test_event_flow.py
import pytest

@pytest.mark.asyncio
async def test_herb_update_triggers_provenance_rebuild(
    event_bus, kg_service, provenance_service
):
    # Arrange
    herb = await kg_service.create_herb(test_herb_data)

    # Act
    await kg_service.update_herb(herb.id, {"properties": ["new_prop"]})

    # Assert - wait for event processing
    await eventually(
        provenance_service.is_chain_rebuilt,
        herb.id,
        timeout=5
    )
```

### 7.2 Event Contract Testing

```python
# tests/contracts/test_events.py
from pydantic import ValidationError

def test_herb_created_event_schema():
    event = HerbCreatedEvent(
        event_id=uuid4(),
        event_type=EventType.HERB_CREATED,
        aggregate_id="test-id",
        payload={
            "herb_id": "test-id",
            "name": "人参"
        },
        metadata=EventMetadata(source="kg")
    )

    # Validate against schema
    assert event.event_type == EventType.HERB_CREATED
    assert "herb_id" in event.payload
```

---

## 8. Implementation Roadmap

### Phase 1: Event Bus Foundation (Week 1-2)
- [ ] Event schema definitions in shared
- [ ] Redis Pub/Sub event bus implementation
- [ ] Base event handler with retry/DLQ
- [ ] Correlation ID propagation

### Phase 2: Module Integration (Week 3-5)
- [ ] KG module publishes events
- [ ] Provenance module subscribes to KG events
- [ ] QA module integrates with event flow
- [ ] Review module event workflow

### Phase 3: Data Sync (Week 6-7)
- [ ] Neo4j sync handlers
- [ ] PostgreSQL-Neo4j consistency
- [ ] Idempotency implementation
- [ ] DLQ monitoring

### Phase 4: hardening (Week 8)
- [ ] Integration tests
- [ ] Performance testing
- [ ] Failure scenario testing
- [ ] Documentation
