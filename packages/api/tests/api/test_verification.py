"""
Verification API TDD - Review Module End-to-End Testing

Tests for POST /verifications/, GET /verifications/{id},
GET /verifications/, POST /verifications/{id}/verify

8 test cases covering all Verification API endpoints.
Validates response model shape, Neo4j sync behavior, and pagination.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID
from datetime import datetime, timezone

import pytest


# ---------------------------------------------------------------------------
# Response model validation
# ---------------------------------------------------------------------------

VERIFICATION_RESPONSE_KEYS = {
    "id", "entity_type", "entity_id", "field_name", "claimed_value",
    "source_id", "status", "applicant_id", "verifier_id", "verdict",
    "verified_at", "created_at",
}

PAGINATED_RESPONSE_KEYS = {"items", "total", "page", "page_size", "has_more"}


def _assert_verification_shape(body: dict) -> None:
    """Validate that the response matches VerificationResponse schema."""
    assert set(body.keys()) == VERIFICATION_RESPONSE_KEYS, (
        f"Response keys mismatch: got {set(body.keys())}"
    )


def _assert_paginated_shape(body: dict) -> None:
    """Validate that the response matches PaginatedVerificationsResponse schema."""
    assert set(body.keys()) == PAGINATED_RESPONSE_KEYS
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)
    assert isinstance(body["page"], int)
    assert isinstance(body["page_size"], int)
    assert isinstance(body["has_more"], bool)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_row(user_id: UUID, role: str = "user", is_active: bool = True):
    """Build a lightweight mock that behaves like a UserModel row."""
    row = MagicMock()
    row.id = user_id
    row.role = role
    row.is_active = is_active
    return row


def _make_verification_row(
    *,
    verification_id: UUID | None = None,
    entity_type: str = "herb",
    entity_id: str = "herb-001",
    field_name: str | None = None,
    claimed_value: str = "test claim",
    source_id: UUID | None = None,
    status: str = "pending",
    applicant_id: UUID | None = None,
    verifier_id: UUID | None = None,
    verdict: str | None = None,
    verified_at: datetime | None = None,
    created_at: datetime | None = None,
):
    """Build a mock that looks like a VerificationModel ORM row."""
    row = MagicMock()
    row.id = verification_id or uuid4()
    row.entity_type = entity_type
    row.entity_id = entity_id
    row.field_name = field_name
    row.claimed_value = claimed_value
    row.source_id = source_id
    row.status = status
    row.applicant_id = applicant_id or uuid4()
    row.verifier_id = verifier_id
    row.verdict = verdict
    row.verified_at = verified_at
    row.created_at = created_at or datetime.now(timezone.utc)
    return row


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def expert_id():
    return uuid4()


@pytest.fixture
def source_id():
    return uuid4()


@pytest.fixture
def mock_db(user_id):
    """Async mock for SQLAlchemy AsyncSession.

    By default, the session's execute returns a result whose
    scalar_one_or_none yields a demo user (needed by _resolve_active_user_id).
    """
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.close = AsyncMock()

    # Default execute returns a user
    user_row = _make_user_row(user_id)
    default_result = MagicMock()
    default_result.scalar_one_or_none.return_value = user_row
    session.execute = AsyncMock(return_value=default_result)

    return session


@pytest.fixture
async def client(mock_db):
    """httpx AsyncClient wired to the FastAPI app with mocked DB."""
    from app.main import app
    from app.core.database import get_db

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. test_create_verification
# ---------------------------------------------------------------------------

async def test_create_verification(client, mock_db, user_id):
    """POST /api/v1/verifications/ creates a verification record."""
    vid = uuid4()
    now = datetime.now(timezone.utc)

    # After flush + refresh, the session should expose the newly created row.
    # We capture the object added via session.add and patch its id/created_at
    # through the refresh side-effect.
    def _refresh_side_effect(obj, **kw):
        obj.id = vid
        obj.created_at = now
        obj.status = "pending"
        obj.verifier_id = None
        obj.verdict = None
        obj.verified_at = None

    mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

    payload = {
        "entity_type": "herb",
        "entity_id": "herb-001",
        "claimed_value": "ginseng boosts qi",
        "applicant_id": str(user_id),
    }

    resp = await client.post(
        "/api/v1/verifications/",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    _assert_verification_shape(body)
    assert body["entity_type"] == "herb"
    assert body["entity_id"] == "herb-001"
    assert body["status"] == "pending"
    assert body["claimed_value"] == "ginseng boosts qi"

    # Verify DB was called
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# 2. test_create_verification_with_evidence
# ---------------------------------------------------------------------------

async def test_create_verification_with_evidence(client, mock_db, user_id, source_id):
    """POST /api/v1/verifications/ with evidence list attaches evidence records."""
    vid = uuid4()
    now = datetime.now(timezone.utc)

    added_objects = []

    def _track_add(obj):
        added_objects.append(obj)

    mock_db.add = MagicMock(side_effect=_track_add)

    def _refresh_side_effect(obj, **kw):
        obj.id = vid
        obj.created_at = now
        obj.status = "pending"
        obj.verifier_id = None
        obj.verdict = None
        obj.verified_at = None

    mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

    payload = {
        "entity_type": "herb",
        "entity_id": "herb-002",
        "claimed_value": "astragalus strengthens immune system",
        "applicant_id": str(user_id),
        "evidence": [
            {
                "source_id": str(source_id),
                "quote": "The evidence from ancient texts",
                "page_reference": "p.42",
                "relevance_score": 0.95,
            }
        ],
    }

    resp = await client.post(
        "/api/v1/verifications/",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 200, resp.text

    # VerificationModel + 1 VerificationEvidenceModel = 2 add calls
    assert len(added_objects) == 2, (
        f"Expected 2 objects added (verification + evidence), got {len(added_objects)}"
    )


# ---------------------------------------------------------------------------
# 3. test_get_verification_found
# ---------------------------------------------------------------------------

async def test_get_verification_found(client, mock_db, user_id):
    """GET /api/v1/verifications/{id} returns verification when found."""
    vid = uuid4()
    now = datetime.now(timezone.utc)
    row = _make_verification_row(
        verification_id=vid,
        entity_type="herb",
        entity_id="herb-003",
        claimed_value="licorice harmonizes",
        applicant_id=user_id,
        created_at=now,
    )

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = row
    mock_db.execute = AsyncMock(return_value=result_mock)

    resp = await client.get(f"/api/v1/verifications/{vid}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    _assert_verification_shape(body)
    assert body["id"] == str(vid)
    assert body["entity_type"] == "herb"
    assert body["claimed_value"] == "licorice harmonizes"


# ---------------------------------------------------------------------------
# 4. test_get_verification_not_found
# ---------------------------------------------------------------------------

async def test_get_verification_not_found(client, mock_db):
    """GET /api/v1/verifications/{id} returns 404 for missing record."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    mock_db.execute = AsyncMock(return_value=result_mock)

    missing_id = uuid4()
    resp = await client.get(f"/api/v1/verifications/{missing_id}")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 5. test_list_verifications_default
# ---------------------------------------------------------------------------

async def test_list_verifications_default(client, mock_db, user_id):
    """GET /api/v1/verifications/ returns paginated list."""
    now = datetime.now(timezone.utc)
    rows = [
        _make_verification_row(
            entity_type="herb",
            entity_id=f"herb-{i}",
            claimed_value=f"claim-{i}",
            applicant_id=user_id,
            created_at=now,
        )
        for i in range(3)
    ]

    # First execute -> items query, second execute -> count query
    items_result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    items_result.scalars.return_value = scalars_mock

    count_result = MagicMock()
    count_result.scalar.return_value = 3

    mock_db.execute = AsyncMock(side_effect=[items_result, count_result])

    resp = await client.get("/api/v1/verifications/")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    _assert_paginated_shape(body)
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert body["has_more"] is False


# ---------------------------------------------------------------------------
# 6. test_list_verifications_with_filters
# ---------------------------------------------------------------------------

async def test_list_verifications_with_filters(client, mock_db, user_id):
    """GET /api/v1/verifications/?status=pending&entity_type=herb applies filters."""
    now = datetime.now(timezone.utc)
    row = _make_verification_row(
        entity_type="herb",
        entity_id="herb-filtered",
        claimed_value="filtered claim",
        applicant_id=user_id,
        created_at=now,
    )

    items_result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [row]
    items_result.scalars.return_value = scalars_mock

    count_result = MagicMock()
    count_result.scalar.return_value = 1

    mock_db.execute = AsyncMock(side_effect=[items_result, count_result])

    resp = await client.get(
        "/api/v1/verifications/",
        params={"status": "pending", "entity_type": "herb"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    _assert_paginated_shape(body)
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["entity_type"] == "herb"


# ---------------------------------------------------------------------------
# 7. test_verify_verification_accept
# ---------------------------------------------------------------------------

@patch("app.api.verification.graph_service")
async def test_verify_verification_accept(
    mock_graph_svc, client, mock_db, user_id, expert_id
):
    """POST /api/v1/verifications/{id}/verify with status=verified syncs to Neo4j."""
    vid = uuid4()
    now = datetime.now(timezone.utc)
    row = _make_verification_row(
        verification_id=vid,
        entity_type="herb",
        entity_id="herb-accept",
        claimed_value="accepted claim",
        status="pending",
        applicant_id=user_id,
        created_at=now,
    )

    # First execute -> find verification, second execute -> find expert user
    ver_result = MagicMock()
    ver_result.scalar_one_or_none.return_value = row

    expert_row = _make_user_row(expert_id, role="expert")
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = expert_row

    mock_db.execute = AsyncMock(side_effect=[ver_result, user_result])

    mock_graph_svc.verify_node = AsyncMock()

    def _refresh_side_effect(obj, **kw):
        # After commit, the status should have been updated in-memory already
        pass

    mock_db.refresh = AsyncMock(side_effect=_refresh_side_effect)

    resp = await client.post(
        f"/api/v1/verifications/{vid}/verify",
        params={"status": "verified", "verdict": "Confirmed by expert"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    _assert_verification_shape(body)
    assert body["status"] == "verified"
    assert body["verdict"] == "Confirmed by expert"

    # Verify Neo4j sync was called for herb entity type
    mock_graph_svc.verify_node.assert_awaited_once_with(
        "herb-accept", str(vid), str(expert_id), "verified"
    )


# ---------------------------------------------------------------------------
# 8. test_verify_verification_reject
# ---------------------------------------------------------------------------

@patch("app.api.verification.graph_service")
async def test_verify_verification_reject(
    mock_graph_svc, client, mock_db, user_id, expert_id
):
    """POST /api/v1/verifications/{id}/verify with status=rejected does NOT sync to Neo4j."""
    vid = uuid4()
    now = datetime.now(timezone.utc)
    row = _make_verification_row(
        verification_id=vid,
        entity_type="herb",
        entity_id="herb-reject",
        claimed_value="rejected claim",
        status="pending",
        applicant_id=user_id,
        created_at=now,
    )

    ver_result = MagicMock()
    ver_result.scalar_one_or_none.return_value = row

    expert_row = _make_user_row(expert_id, role="expert")
    user_result = MagicMock()
    user_result.scalar_one_or_none.return_value = expert_row

    mock_db.execute = AsyncMock(side_effect=[ver_result, user_result])

    mock_graph_svc.verify_node = AsyncMock()

    mock_db.refresh = AsyncMock()

    resp = await client.post(
        f"/api/v1/verifications/{vid}/verify",
        params={"status": "rejected", "verdict": "Insufficient evidence"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    _assert_verification_shape(body)
    assert body["status"] == "rejected"
    assert body["verdict"] == "Insufficient evidence"

    # Neo4j sync should NOT be called for rejected status
    mock_graph_svc.verify_node.assert_not_awaited()
