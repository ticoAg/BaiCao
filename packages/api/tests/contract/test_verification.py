"""
Verification API TDD Tests

Red Phase: These tests define the expected behavior of Verification API.
They should FAIL initially if implementation is incomplete.
Green Phase: Implement methods to make tests pass.
Refactor Phase: Improve code quality while keeping tests green.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from tests.conftest import MockVerification

pytestmark = pytest.mark.contract


# ============ Test Cases ============

@pytest.mark.asyncio
async def test_create_verification(client, mock_db):
    """Test POST /api/v1/verifications/ creates a verification record"""
    applicant_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="herb",
        entity_id="herb-123",
        field_name="efficacy",
        claimed_value="人参能大补元气",
        status="pending",
        applicant_id=applicant_id
    )

    async def mock_refresh(obj):
        # Update the object with actual values after "creation"
        obj.id = verification_id
        obj.status = "pending"

    mock_db.refresh = mock_refresh

    with patch("app.api.verification.graph_service") as mock_graph:
        mock_graph.verify_node = AsyncMock(return_value={"status": "verified"})
        with patch("app.api.verification.VerificationModel") as MockModel:
            MockModel.return_value = mock_verification
            response = await client.post(
                "/api/v1/verifications/",
                params={
                    "entity_type": "herb",
                    "entity_id": "herb-123",
                    "claimed_value": "人参能大补元气",
                    "applicant_id": str(applicant_id),
                    "field_name": "efficacy"
                }
            )

    assert response.status_code == 200
    data = response.json()
    assert data["entity_type"] == "herb"
    assert data["entity_id"] == "herb-123"
    assert data["claimed_value"] == "人参能大补元气"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_verification_with_evidence(client, mock_db):
    """Test POST /api/v1/verifications/ with evidence attachment"""
    applicant_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="herb",
        entity_id="herb-456",
        field_name="nature",
        claimed_value="人参性温",
        status="pending",
        applicant_id=applicant_id
    )

    async def mock_refresh(obj):
        obj.id = verification_id
        obj.status = "pending"

    mock_db.refresh = mock_refresh

    with patch("app.api.verification.graph_service") as mock_graph:
        mock_graph.verify_node = AsyncMock(return_value={"status": "verified"})
        with patch("app.api.verification.VerificationModel") as MockModel:
            MockModel.return_value = mock_verification
            with patch("app.api.verification.VerificationEvidenceModel") as MockEvidence:
                MockEvidence.return_value = MagicMock()
                response = await client.post(
                    "/api/v1/verifications/",
                    params={
                        "entity_type": "herb",
                        "entity_id": "herb-456",
                        "claimed_value": "人参性温",
                        "applicant_id": str(applicant_id),
                        "field_name": "nature",
                    }
                )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_verification_found(client, mock_db):
    """Test GET /api/v1/verifications/{id} returns verification data"""
    applicant_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="component",
        entity_id="comp-789",
        claimed_value="人参含人参皂苷",
        status="pending",
        applicant_id=applicant_id
    )

    # Mock the select query result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_verification)
    mock_db.execute = AsyncMock(return_value=mock_result)

    response = await client.get(f"/api/v1/verifications/{verification_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(verification_id)
    assert data["entity_type"] == "component"
    assert data["claimed_value"] == "人参含人参皂苷"


@pytest.mark.asyncio
async def test_get_verification_not_found(client, mock_db):
    """Test GET /api/v1/verifications/{id} returns 404 for non-existent"""
    fake_id = uuid4()

    # Mock the select query result - not found
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db.execute = AsyncMock(return_value=mock_result)

    response = await client.get(f"/api/v1/verifications/{fake_id}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_list_verifications_default(client, mock_db):
    """Test GET /api/v1/verifications/ returns paginated list"""
    applicant_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="herb",
        entity_id="herb-list-0",
        claimed_value="验证内容0",
        status="pending",
        applicant_id=applicant_id
    )

    # Mock the select query result
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=[mock_verification])
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_scalars)
    mock_result.scalar = MagicMock(return_value=1)

    mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result])

    response = await client.get("/api/v1/verifications/")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "has_more" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_verifications_with_filters(client, mock_db):
    """Test GET /api/v1/verifications/ with status and entity_type filters"""
    applicant_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="herb",
        entity_id="herb-pending",
        claimed_value="待验证",
        status="pending",
        applicant_id=applicant_id
    )

    # Mock the select query result
    mock_scalars = MagicMock()
    mock_scalars.all = MagicMock(return_value=[mock_verification])
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=mock_scalars)
    mock_result.scalar = MagicMock(return_value=1)

    mock_db.execute = AsyncMock(side_effect=[mock_result, mock_result])

    # Filter by entity_type=herb
    response = await client.get("/api/v1/verifications/?entity_type=herb")

    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["entity_type"] == "herb"


@pytest.mark.asyncio
async def test_verify_verification_accept(client, mock_db):
    """Test POST /api/v1/verifications/{id}/verify accepts verification"""
    applicant_id = uuid4()
    verifier_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="herb",
        entity_id="herb-verify-accept",
        claimed_value="验证通过内容",
        status="pending",
        applicant_id=applicant_id
    )

    async def mock_refresh(obj):
        obj.status = "verified"
        obj.verifier_id = verifier_id
        obj.verdict = "证据充分，验证通过"
        obj.verified_at = datetime.now(timezone.utc)

    mock_db.refresh = mock_refresh

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_verification)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.verification.graph_service") as mock_graph:
        mock_graph.verify_node = AsyncMock(return_value={"status": "verified"})

        verify_response = await client.post(
            f"/api/v1/verifications/{verification_id}/verify",
            params={
                "verifier_id": str(verifier_id),
                "status": "verified",
                "verdict": "证据充分，验证通过"
            }
        )

    assert verify_response.status_code == 200
    data = verify_response.json()
    assert data["status"] == "verified"
    assert data["verifier_id"] == str(verifier_id)
    assert data["verdict"] == "证据充分，验证通过"


@pytest.mark.asyncio
async def test_verify_verification_reject(client, mock_db):
    """Test POST /api/v1/verifications/{id}/verify rejects verification"""
    applicant_id = uuid4()
    verifier_id = uuid4()
    verification_id = uuid4()

    mock_verification = MockVerification(
        id=verification_id,
        entity_type="herb",
        entity_id="herb-verify-reject",
        claimed_value="验证拒绝内容",
        status="pending",
        applicant_id=applicant_id
    )

    async def mock_refresh(obj):
        obj.status = "rejected"
        obj.verifier_id = verifier_id
        obj.verdict = "证据不足，拒绝验证"
        obj.verified_at = datetime.now(timezone.utc)

    mock_db.refresh = mock_refresh

    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_verification)
    mock_db.execute = AsyncMock(return_value=mock_result)

    with patch("app.api.verification.graph_service") as mock_graph:
        mock_graph.verify_node = AsyncMock(return_value={"status": "rejected"})

        verify_response = await client.post(
            f"/api/v1/verifications/{verification_id}/verify",
            params={
                "verifier_id": str(verifier_id),
                "status": "rejected",
                "verdict": "证据不足，拒绝验证"
            }
        )

    assert verify_response.status_code == 200
    data = verify_response.json()
    assert data["status"] == "rejected"
    assert data["verifier_id"] == str(verifier_id)
    assert data["verdict"] == "证据不足，拒绝验证"
