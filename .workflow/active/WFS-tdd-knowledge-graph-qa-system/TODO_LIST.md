# Tasks: TDD - 中药材知识图谱智能问答系统

## TDD Task Progress

- [ ] **IMPL-001**: GraphService TDD - Neo4j Knowledge Graph Core Operations (10 test cases)
  - Target: packages/api/app/kg/graph_service.py
  - Tests: packages/api/tests/kg/test_graph_service.py
  - Status: pending
  - TDD Phase: Red-Green-Refactor
  - Link: [📋](./.task/IMPL-001.json)

- [ ] **IMPL-002**: ChatService TDD - QA Service with Knowledge Graph Integration (8 test cases)
  - Target: packages/api/app/services/chat_service.py
  - Tests: packages/api/tests/services/test_chat_service.py
  - Status: pending
  - TDD Phase: Red-Green-Refactor
  - Depends on: IMPL-001
  - Link: [📋](./.task/IMPL-002.json)

- [ ] **IMPL-003**: Verification API TDD - Review Module End-to-End Testing (8 test cases)
  - Target: packages/api/app/api/verification.py
  - Tests: packages/api/tests/api/test_verification.py
  - Status: pending
  - TDD Phase: Red-Green-Refactor
  - Link: [📋](./.task/IMPL-003.json)

- [ ] **IMPL-004**: Provenance Module TDD - New Implementation with Evidence-Source Lineage (7 test cases)
  - Target: packages/api/app/溯源/__init__.py
  - Tests: packages/api/tests/溯源/test_provenance.py
  - Status: pending
  - TDD Phase: Red-Green-Refactor
  - Link: [📋](./.task/IMPL-004.json)

- [ ] **IMPL-005**: API Routes TDD - Integration Tests for Chat, Graph, and Herb Endpoints (10 test cases)
  - Targets: packages/api/app/api/chat.py, graph.py, herb.py
  - Tests: packages/api/tests/api/test_routes.py (or separate files)
  - Status: pending
  - TDD Phase: Red-Green-Refactor
  - Depends on: IMPL-001, IMPL-002
  - Link: [📋](./.task/IMPL-005.json)

## TDD Phase Progress

### Phase 1: Core Services TDD
- [ ] IMPL-001 GraphService - Red Phase (write failing tests)
- [ ] IMPL-001 GraphService - Green Phase (implement to pass)
- [ ] IMPL-001 GraphService - Refactor Phase (improve quality)
- [ ] IMPL-002 ChatService - Red Phase (write failing tests)
- [ ] IMPL-002 ChatService - Green Phase (implement to pass)
- [ ] IMPL-002 ChatService - Refactor Phase (improve quality)

### Phase 2: Module TDD (Parallel with Phase 1)
- [ ] IMPL-003 Verification - Red Phase (write failing tests)
- [ ] IMPL-003 Verification - Green Phase (implement to pass)
- [ ] IMPL-003 Verification - Refactor Phase (improve quality)
- [ ] IMPL-004 Provenance - Red Phase (write failing tests)
- [ ] IMPL-004 Provenance - Green Phase (implement to pass)
- [ ] IMPL-004 Provenance - Refactor Phase (improve quality)

### Phase 3: Integration TDD
- [ ] IMPL-005 API Routes - Red Phase (write failing tests)
- [ ] IMPL-005 API Routes - Green Phase (implement to pass)
- [ ] IMPL-005 API Routes - Refactor Phase (improve quality)

## Summary Statistics
- **Total Tasks**: 5
- **Total Test Cases**: 43 (10+8+8+7+10)
- **Target Coverage**: >=80%
- **TDD Workflow**: Red-Green-Refactor with max 3 iterations per task

## Status Legend
- `- [ ]` = Pending task
- `- [x]` = Completed task
- `- [/]` = In progress

## Dependencies
```
IMPL-001 (GraphService)
    └── IMPL-002 (ChatService)
            └── IMPL-005 (API Routes)

IMPL-003 (Verification) [parallel with IMPL-001]
IMPL-004 (Provenance) [parallel with IMPL-002]
```
