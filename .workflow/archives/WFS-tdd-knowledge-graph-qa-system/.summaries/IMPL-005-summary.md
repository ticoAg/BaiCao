# Task: IMPL-005 API Routes TDD - Integration Tests for Chat, Graph, and Herb Endpoints

## Implementation Summary

### Files Verified (already implemented by prior sessions)
- `packages/api/tests/api/test_chat_routes.py`: 6 integration tests for Chat API routes
- `packages/api/tests/api/test_graph_routes.py`: 6 integration tests for Graph API routes
- `packages/api/tests/api/test_herb_routes.py`: 3 integration tests for Herb API routes
- `packages/api/tests/api/helpers.py`: Shared test helpers, validation helpers, mock fixtures

### Test Coverage Results
- `app/api/chat.py`: 97% (31 stmts, 1 miss)
- `app/api/graph.py`: 85% (34 stmts, 5 miss)
- `app/api/herb.py`: 81% (27 stmts, 5 miss)
- **TOTAL (chat+graph+herb)**: 88% (92 stmts, 11 miss)

### Test Cases (15 total, exceeds 10 minimum)

**Chat API (6 tests)**:
- `test_ask_question_with_body`: POST /api/v1/chat/question with JSON body
- `test_ask_question_missing_question`: POST without question returns 422
- `test_ask_question_with_session_id`: POST with session_id forwarded to service
- `test_get_session_found`: GET /api/v1/chat/session/{id} returns session
- `test_get_session_not_found`: GET non-existent session returns 404
- `test_create_session`: POST /api/v1/chat/session creates session

**Graph API (6 tests)**:
- `test_get_herb_graph_found`: GET /api/v1/graph/herb/{name} returns graph
- `test_get_herb_graph_not_found`: GET non-existent herb returns 404
- `test_search_nodes`: GET /api/v1/graph/search returns items+total
- `test_get_node_found`: GET /api/v1/graph/node/{id} returns node
- `test_get_node_not_found`: GET non-existent node returns 404
- `test_get_pending_nodes`: GET /api/v1/graph/pending returns pending items

**Herb API (3 tests)**:
- `test_get_herb_found`: GET /api/v1/herbs/{id} returns herb
- `test_get_herb_not_found`: GET non-existent herb returns 404
- `test_list_herbs_returns_paginated`: GET /api/v1/herbs/ returns paginated list

### Refactorings Applied (3/3)
1. **Route testing helpers** (`helpers.py`): `assert_status()`, `assert_json_keys()`
2. **Response validation helpers** (`helpers.py`): `assert_pagination()`, `assert_graph_response()`, `assert_list_response()`, `assert_qa_response()`
3. **Consistent mock fixtures** (`helpers.py`): `MockHerb`, `make_herb()`, `make_answer_response()`, `make_session_data()`, `make_herb_graph()`, `make_search_results()`

## Outputs for Dependent Tasks

### Available Test Helpers
```python
from tests.api.helpers import (
    assert_status,
    assert_json_keys,
    assert_pagination,
    assert_graph_response,
    assert_list_response,
    assert_qa_response,
    make_herb,
    make_answer_response,
    make_session_data,
    make_herb_graph,
    make_search_results,
    MockHerb,
)
```

### Integration Points
- **Chat route tests**: Mock `ChatService` class via `patch("app.api.chat.ChatService")`
- **Graph route tests**: Mock `graph_service` singleton via `patch("app.api.graph.graph_service")`
- **Herb route tests**: Mock `HerbService` class via `patch("app.api.herb.HerbService")`
- **DB fixture**: `conftest.py` provides `mock_db` + `client` fixtures with dependency override

### Verification Commands
```bash
# Run all IMPL-005 tests
cd packages/api && .venv/bin/python -m pytest tests/api/test_chat_routes.py tests/api/test_graph_routes.py tests/api/test_herb_routes.py -v --tb=short

# Coverage report
cd packages/api && .venv/bin/python -m pytest tests/api/test_chat_routes.py tests/api/test_graph_routes.py tests/api/test_herb_routes.py --cov=app.api.chat --cov=app.api.graph --cov=app.api.herb --cov-report=term-missing
```

## Status: Complete
