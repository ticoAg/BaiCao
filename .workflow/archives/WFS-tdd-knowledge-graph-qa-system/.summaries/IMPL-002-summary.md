# Task: IMPL-002 ChatService TDD - QA Service with Knowledge Graph Integration

## Implementation Summary

### Files Modified
- `packages/api/tests/services/__init__.py`: Created empty init for test package
- `packages/api/tests/services/test_chat_service.py`: Created 9 test cases covering full QA pipeline

### Files Verified (no changes needed)
- `packages/api/app/services/chat_service.py`: All 3 refactorings already applied (HERB_KEYWORDS constant, EntityPattern dataclass, _validate_response)

### Content Added

**Test File** (`packages/api/tests/services/test_chat_service.py`):

- **mock_graph_data fixture**: Predefined herb graph data with center node, edges (HAS_EFFICACY, HAS_FLAVOR)
- **mock_graph_service fixture**: AsyncMock of graph_service singleton returning predefined data
- **TestChatServiceAnswerQuestion** (4 tests):
  - `test_answer_question_basic`: Full pipeline structure verification (answer, reasoning_chain, sources, graph_data, session_id)
  - `test_answer_question_with_entities`: Entity extraction integration with graph_service call verification
  - `test_session_id_generation`: UUID generation when no session_id provided
  - `test_session_id_preserved`: Provided session_id passthrough
- **TestChatServiceExtractEntities** (2 tests):
  - `test_extract_entities_finds_herbs`: Detects multiple herb keywords in question
  - `test_extract_entities_no_match`: Falls back to DEFAULT_HERB for unrecognized input
- **TestChatServiceBuildReasoningChain** (1 test):
  - `test_build_reasoning_chain`: Chain structure validation (step numbers, descriptions, confidence range)
- **TestChatServiceGenerateAnswer** (1 test):
  - `test_generate_answer`: Answer string contains herb name
- **TestChatServiceCollectSources** (1 test):
  - `test_collect_sources`: Source aggregation from graph_data center node

### Refactorings Verified (already applied in source)

1. **HERB_KEYWORDS constant** (line 18-21): Module-level list of 20 herb keywords
2. **EntityPattern dataclass** (line 61-73): Reusable regex-based entity extraction pattern
3. **_validate_response method** (line 139-168): Response structure validation with detailed error messages

## Outputs for Dependent Tasks

### Available Test Fixtures
```python
# From tests/services/test_chat_service.py
mock_graph_data      # Predefined herb graph with center/nodes/edges
mock_graph_service   # AsyncMock of graph_service singleton
mock_db              # AsyncMock of AsyncSession
```

### Integration Points
- **ChatService**: `from app.services.chat_service import ChatService` - requires AsyncSession in constructor
- **graph_service mock**: `patch("app.services.chat_service.graph_service", mock_svc)` for test isolation
- **HERB_KEYWORDS**: `from app.services.chat_service import HERB_KEYWORDS` - list of recognized herb names
- **DEFAULT_HERB**: `from app.services.chat_service import DEFAULT_HERB` - fallback herb ("陈皮")

### Test Execution
```bash
# Run tests
cd packages/api && .venv/bin/python -m pytest tests/services/test_chat_service.py -v --tb=short

# Run with coverage
cd packages/api && .venv/bin/python -m pytest tests/services/test_chat_service.py --cov=app.services.chat_service --cov-report=term-missing
```

## Test Results
- **Total tests**: 9
- **All passing**: Yes
- **Coverage**: 83% (target: >=80%)
- **Uncovered lines**: Validation error branches, multi-entity query loop, question classifier branches, empty-entity/no-center edge cases, create_session/get_session stubs
- **No real LLM/Neo4j calls**: All external dependencies mocked

## Status: Complete
