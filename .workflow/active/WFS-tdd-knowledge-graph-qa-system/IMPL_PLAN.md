---
identifier: WFS-tdd-knowledge-graph-qa-system
source: "User requirements"
analysis: .workflow/active/WFS-tdd-knowledge-graph-qa-system/.process/context-package.json
artifacts: .workflow/active/WFS-tdd-knowledge-graph-qa-system/.brainstorming/
context_package: .workflow/active/WFS-tdd-knowledge-graph-qa-system/.process/context-package.json
workflow_type: "tdd"
verification_history:
  concept_verify: "skipped"
  action_plan_verify: "pending"
phase_progression: "brainstorm -> context -> analysis -> planning"
---

# Implementation Plan: TDD - 中药材知识图谱智能问答系统

## 1. Summary

为 BaiCao ShiTan 知识图谱核心功能模块建立完整的 TDD（测试驱动开发）实现计划。通过 TDD 方法论，确保 kg 图谱模块、qa 问答模块、review 审查模块、provenance 溯源模块的测试覆盖率达到 80% 以上。

**Core Objectives**:
- 为 5 个核心模块建立 TDD 测试体系
- 实现 GraphService 的完整单元测试（Neo4j 操作）
- 实现 ChatService 的 QA 逻辑测试（LangChain 集成）
- 实现 Verification API 的端到端测试
- 实现 Provenance 模块的新功能 TDD 开发
- 实现 API Routes 集成测试

**Technical Approach**:
- 使用 pytest-asyncio 进行异步测试，asyncio_mode="auto"
- Mock Neo4j AsyncGraphDatabase driver 进行单元测试
- Mock LLM responses 隔离业务逻辑测试
- 使用 SQLite in-memory (StaticPool) 进行 PostgreSQL 相关测试
- 遵循 Red-Green-Refactor TDD 周期

## 2. Context Analysis

### CCW Workflow Context
**Phase Progression**:
- Phase 1: Brainstorming - skipped (user requirements already clear)
- Phase 2: Context Gathering (context-package.json: 13 source files, 5 modules analyzed)
- Phase 3: Enhanced Analysis (4 exploration angles: architecture, patterns, testing, integration-points)
- Phase 4: Concept Verification - skipped (clarifications documented in context)
- Phase 5: Action Planning (current phase - generating IMPL_PLAN.md)

**Quality Gates**:
- concept-verify: Skipped (user decision - requirements clear)
- action-plan-verify: Pending (recommended before /workflow:execute)

**Context Package Summary**:
- **Focus Paths**: packages/api/app/kg/, packages/api/app/services/, packages/api/app/api/, packages/api/app/溯源/
- **Key Files**: graph_service.py, chat_service.py, verification.py, chat.py, graph.py, herb.py
- **Smart Context**: 13 files analyzed, 5 modules identified, 12 internal dependencies tracked

### Project Profile
- **Type**: Enhancement (TDD for existing codebase)
- **Scale**: Medium complexity, 5 core modules
- **Tech Stack**: Python 3.12+, FastAPI, SQLAlchemy 2.0 async, Neo4j async driver, LangChain
- **Timeline**: Sequential TDD cycles per module

### Module Structure
```
packages/api/
├── app/
│   ├── kg/
│   │   └── graph_service.py       # GraphService singleton (Neo4j operations)
│   ├── services/
│   │   └── chat_service.py        # ChatService (QA logic)
│   ├── api/
│   │   ├── graph.py               # /graph/* routes
│   │   ├── chat.py                # /chat/* routes
│   │   ├── herb.py                # /herb/* routes
│   │   └── verification.py        # /verifications/* routes
│   └── 溯源/
│       └── __init__.py            # Provenance module (EMPTY - new implementation)
└── tests/
    ├── conftest.py                # test_db, client fixtures
    ├── kg/
    │   └── test_graph_service.py  # TDD Feature 1
    ├── services/
    │   └── test_chat_service.py   # TDD Feature 2
    ├── api/
    │   ├── test_verification.py    # TDD Feature 3
    │   └── test_routes.py          # TDD Feature 5
    └── 溯源/
        └── test_provenance.py      # TDD Feature 4
```

### Dependencies
**Primary**: neo4j>=5.28.0 (async), sqlalchemy>=2.0.36, fastapi>=0.115.0, langchain>=0.3.0
**APIs**: OpenAI API (mocked in tests)
**Development**: pytest>=8.3.0, pytest-asyncio>=0.25.0, httpx>=0.28.0, aiosqlite

### Patterns & Conventions
- **Architecture**: GraphService singleton pattern, Service Layer pattern
- **Component Design**: API Router pattern with FastAPI Depends
- **State Management**: AsyncSession dependency injection
- **Code Style**: Python 3.12+ with StrEnum, Pydantic v2 strict mode
- **TDD Pattern**: Red-Green-Refactor with max 3 iterations per task

## 3. TDD Workflow Specification

### TDD Phase Definitions

Each task implements 3 TDD phases:

**Phase 1: Red (tdd_phase: "red")**
- Write failing tests that define expected behavior
- Test count: N test cases with explicit names
- All tests MUST fail before implementation

**Phase 2: Green (tdd_phase: "green")**
- Implement minimal code to pass all tests
- Focus on passing tests, not optimization
- Include test-fix cycle if tests fail

**Phase 3: Refactor (tdd_phase: "refactor")**
- Improve code quality without breaking tests
- Apply N refactorings explicitly listed
- Maintain >=80% code coverage

### Testing Strategy
- **Unit Testing**: Mock external dependencies (Neo4j driver, LLM calls)
- **Integration Testing**: Use httpx.AsyncClient with ASGITransport
- **Coverage Target**: >=80% line coverage
- **Async Pattern**: @pytest.mark.asyncio, async fixtures from conftest.py

## 4. Implementation Strategy

### Execution Strategy
**Execution Model**: Sequential TDD Cycles

**Rationale**: Each module depends on understanding previous patterns. Sequential execution ensures consistent TDD methodology across all modules.

**Parallelization Opportunities**:
- None - modules must be tested sequentially to maintain TDD discipline

**Serialization Requirements**:
- IMPL-001 (GraphService) must complete before IMPL-002 (ChatService)
- IMPL-002 (ChatService) must complete before IMPL-005 (API Routes)
- IMPL-003 (Verification) and IMPL-004 (Provenance) can be developed in parallel with IMPL-001/002

### Task Dependency Graph
```
IMPL-001 (GraphService TDD)
    └── IMPL-002 (ChatService TDD)
            └── IMPL-005 (API Routes TDD)

IMPL-003 (Verification TDD) [parallel with IMPL-001]
IMPL-004 (Provenance TDD) [parallel with IMPL-002]
```

## 5. Task Breakdown Summary

### Task Count
**5 tasks** (flat hierarchy, sequential execution with parallel opportunities)

### Task Structure
- **IMPL-001**: GraphService TDD (kg module) - 10 test cases
- **IMPL-002**: ChatService TDD (qa module) - 8 test cases
- **IMPL-003**: Verification API TDD (review module) - 8 test cases
- **IMPL-004**: Provenance Module TDD (new implementation) - 7 test cases
- **IMPL-005**: API Routes TDD (integration tests) - 10 test cases

### Complexity Assessment
- **High**: GraphService TDD (Neo4j mocking complexity), ChatService TDD (LLM integration mocking)
- **Medium**: Verification API TDD (API + DB + Neo4j sync), Provenance TDD (new module design)
- **Low**: API Routes TDD (follows established patterns)

## 6. Implementation Plan (Detailed Phased Breakdown)

### Execution Strategy

**Phase 1: Core Services TDD (IMPL-001, IMPL-002)**
- **Tasks**: IMPL-001 (GraphService), IMPL-002 (ChatService) in sequence
- **Deliverables**:
  - test_graph_service.py with 10 test cases
  - test_chat_service.py with 8 test cases
  - Mocked Neo4j driver infrastructure
- **Success Criteria**:
  - All tests pass with >=80% coverage
  - GraphService methods: create_node, get_node, create_herb, link_herb_*, get_herb_graph
  - ChatService methods: answer_question, _extract_entities, _build_reasoning_chain, _generate_answer

**Phase 2: Module TDD (IMPL-003, IMPL-004)**
- **Tasks**: IMPL-003 (Verification), IMPL-004 (Provenance) in parallel
- **Deliverables**:
  - test_verification.py with 8 test cases
  - test_provenance.py with 7 test cases (new module)
- **Success Criteria**:
  - All tests pass with >=80% coverage
  - Verification API endpoints fully tested
  - Provenance module implements Evidence->Source链路

**Phase 3: Integration TDD (IMPL-005)**
- **Tasks**: IMPL-005 (API Routes)
- **Deliverables**:
  - test_chat.py, test_graph.py, test_herb.py with 10 combined test cases
- **Success Criteria**:
  - All tests pass with >=80% coverage
  - API routes integrated with mocked services

## 7. Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation Strategy | Owner |
|------|--------|-------------|---------------------|-------|
| Neo4j driver mocking complexity | High | High | Use mock_async_driver fixture with predefined responses | Agent |
| LLM integration test isolation | High | Medium | Mock all LangChain calls, test business logic only | Agent |
| Provenance module design ambiguity | Medium | Medium | Start with TDD Red phase to define requirements | Agent |
| GraphService singleton in tests | Medium | Low | Reset singleton state in test fixtures | Agent |

**Critical Risks** (High impact + High probability):
- Neo4j driver mocking: Implement comprehensive mock responses for all Cypher queries

**Monitoring Strategy**:
- Run pytest with --cov on each task completion
- Review coverage reports before moving to next task

## 8. Success Criteria

**Functional Completeness**:
- [ ] All 5 TDD tasks implemented with passing tests
- [ ] GraphService: 10 test cases covering all public methods
- [ ] ChatService: 8 test cases covering answer pipeline
- [ ] Verification: 8 test cases covering all endpoints
- [ ] Provenance: 7 test cases defining new module behavior
- [ ] API Routes: 10 integration test cases

**Technical Quality**:
- [ ] Test coverage >=80% for all implemented modules
- [ ] All tests follow pytest-asyncio pattern
- [ ] Mock infrastructure reusable across modules
- [ ] No external service dependencies in unit tests

**TDD Discipline**:
- [ ] Red phase: All tests fail before implementation
- [ ] Green phase: Minimal implementation to pass tests
- [ ] Refactor phase: Code quality improvements without breaking tests
- [ ] max_iterations=3 enforced per task

**Quality Gates**:
- [ ] pytest packages/api --cov reports >=80% coverage
- [ ] pytest packages/api --cov --tb=short passes all tests
- [ ] No warnings in test execution output
