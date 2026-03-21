"""Shared test helpers and fixtures for API route integration tests.

Refactoring 1: Extract route testing helpers into shared module.
Refactoring 2: Add response validation helpers.
Refactoring 3: Create consistent mock fixtures.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone


# ===========================================================================
# Refactoring 1: Route testing helpers
# ===========================================================================

def assert_status(response, expected_status: int):
    """Assert HTTP response status code with informative message."""
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}: {response.text}"
    )


def assert_json_keys(data: dict, required_keys: set):
    """Assert that a JSON response dict contains all required keys."""
    missing = required_keys - set(data.keys())
    assert not missing, f"Response missing keys: {missing}"


# ===========================================================================
# Refactoring 2: Response validation helpers
# ===========================================================================

def assert_pagination(data: dict):
    """Assert that a response contains standard pagination fields."""
    assert_json_keys(data, {"items", "total", "page", "page_size", "has_more"})
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["page_size"], int)
    assert isinstance(data["has_more"], bool)


def assert_graph_response(data: dict):
    """Assert that a graph endpoint response has the expected structure."""
    assert_json_keys(data, {"center", "nodes", "edges"})
    assert isinstance(data["nodes"], list)
    assert isinstance(data["edges"], list)


def assert_list_response(data: dict, *, min_items: int = 0):
    """Assert that a list endpoint response has items and total."""
    assert_json_keys(data, {"items", "total"})
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert len(data["items"]) >= min_items


def assert_qa_response(data: dict):
    """Assert that a QA/chat answer response has the expected structure."""
    assert_json_keys(data, {"answer", "reasoning_chain", "sources", "graph_data", "session_id"})
    assert isinstance(data["answer"], str)
    assert isinstance(data["reasoning_chain"], list)
    assert isinstance(data["sources"], list)
    assert isinstance(data["graph_data"], dict)
    assert isinstance(data["session_id"], str)


# ===========================================================================
# Refactoring 3: Consistent mock fixtures
# ===========================================================================

class MockHerb:
    """Mock HerbModel for FastAPI serialization."""

    def __init__(self, herb_id=None, name="ginseng", category="supplement"):
        self.id = herb_id or uuid4()
        self.name = name
        self.latin_name = "Panax ginseng"
        self.category = category
        self.description = "A well-known herb"
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self._sa_instance_state = MagicMock()

    def __getitem__(self, key):
        return getattr(self, key)


def make_herb(**kwargs) -> MockHerb:
    """Build a MockHerb instance."""
    return MockHerb(**kwargs)


def make_answer_response(session_id: str = None) -> dict:
    """Build a standard ChatService.answer_question return value."""
    return {
        "answer": "Test answer about herbs",
        "reasoning_chain": [
            {
                "step": 1,
                "description": "step desc",
                "entities": ["herb"],
                "relations": [],
                "confidence": 0.9,
            }
        ],
        "sources": [{"id": "src-1", "name": "source", "citation": "cite"}],
        "graph_data": {"center": None, "nodes": [], "edges": []},
        "session_id": session_id or str(uuid4()),
    }


def make_session_data(session_id: str = None) -> dict:
    """Build a standard session dict."""
    sid = session_id or str(uuid4())
    return {
        "id": sid,
        "user_id": None,
        "messages": [],
        "created_at": "now",
    }


def make_herb_graph(name: str = "ginseng") -> dict:
    """Build a standard get_herb_graph return value."""
    return {
        "center": {"id": "herb-1", "name": name, "status": "pending"},
        "nodes": [{"id": "eff-1", "name": "efficacy-1"}],
        "edges": [{"type": "HAS_EFFICACY", "source": "herb-1", "target": "eff-1"}],
    }


def make_search_results() -> list:
    """Build standard search_nodes return value."""
    return [
        {"node": {"id": "n1", "name": "ginseng"}, "labels": ["Herb"]},
        {"node": {"id": "n2", "name": "licorice"}, "labels": ["Herb"]},
    ]
