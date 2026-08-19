"""Provenance API route tests - mock ProvenanceService for unit testing"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


STORAGE_KEYS = {"标识", "名称", "证据原文", "状态", "原文", "来源", "页码"}


@pytest.fixture
def mock_provenance():
    """Mock provenance_service for all tests"""
    with patch("app.api.provenance.provenance_service") as mock:
        yield mock


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


def _assert_frontend_payload(payload):
    if isinstance(payload, dict):
        assert STORAGE_KEYS.isdisjoint(payload)
        for value in payload.values():
            _assert_frontend_payload(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_frontend_payload(item)


# ============ POST /provenance/evidence ============


@pytest.mark.asyncio
async def test_create_evidence(client, mock_provenance):
    mock_provenance.create_evidence = AsyncMock(
        return_value={
            "id": "ev-001",
            "content": "人参补气",
            "source_name": "本草纲目",
            "page_reference": "卷十二",
            "status": "pending",
        }
    )

    resp = await client.post(
        "/api/v1/provenance/evidence",
        json={
            "content": "人参补气",
            "source_name": "本草纲目",
            "page_reference": "卷十二",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "ev-001"
    assert data["content"] == "人参补气"
    assert data["source_name"] == "本草纲目"
    assert data["page_reference"] == "卷十二"
    _assert_frontend_payload(data)
    mock_provenance.create_evidence.assert_awaited_once_with(
        content="人参补气",
        source_name="本草纲目",
        page_reference="卷十二",
    )


@pytest.mark.asyncio
async def test_create_evidence_missing_fields(client, mock_provenance):
    resp = await client.post("/api/v1/provenance/evidence", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_evidence_rejects_name_evidence_text_fields(client, mock_provenance):
    resp = await client.post(
        "/api/v1/provenance/evidence",
        json={
            "name": "本草纲目摘录",
            "evidence_text": "人参补气",
        },
    )
    assert resp.status_code == 422
    mock_provenance.create_evidence.assert_not_called()


# ============ GET /provenance/evidence/{id} ============


@pytest.mark.asyncio
async def test_get_evidence_found(client, mock_provenance):
    mock_provenance.get_evidence = AsyncMock(
        return_value={
            "id": "ev-001",
            "content": "人参补气",
            "source_name": "本草纲目",
            "status": "pending",
        }
    )

    resp = await client.get("/api/v1/provenance/evidence/ev-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "ev-001"
    assert data["content"] == "人参补气"
    assert data["source_name"] == "本草纲目"
    _assert_frontend_payload(data)


@pytest.mark.asyncio
async def test_get_evidence_not_found(client, mock_provenance):
    mock_provenance.get_evidence = AsyncMock(return_value=None)

    resp = await client.get("/api/v1/provenance/evidence/nonexistent")
    assert resp.status_code == 404


# ============ POST /provenance/evidence/{id}/link-source ============


@pytest.mark.asyncio
async def test_link_evidence_to_source(client, mock_provenance):
    mock_provenance.link_evidence_to_source = AsyncMock(
        return_value={
            "type": "来源于",
            "status": "pending",
            "source_id": "src-001",
            "evidence_id": "ev-001",
        }
    )

    resp = await client.post(
        "/api/v1/provenance/evidence/ev-001/link-source",
        json={
            "source_id": "src-001",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Evidence linked to source"
    assert data["relationship"]["type"] == "来源于"
    assert data["relationship"]["status"] == "pending"
    assert data["relationship"]["evidence_id"] == "ev-001"
    assert data["relationship"]["source_id"] == "src-001"
    _assert_frontend_payload(data)


@pytest.mark.asyncio
async def test_link_evidence_to_source_not_found(client, mock_provenance):
    mock_provenance.link_evidence_to_source = AsyncMock(return_value={})

    resp = await client.post(
        "/api/v1/provenance/evidence/ev-missing/link-source",
        json={"source_id": "src-missing"},
    )
    assert resp.status_code == 404


# ============ GET /provenance/entity/{id}/lineage ============


@pytest.mark.asyncio
async def test_get_entity_lineage_found(client, mock_provenance):
    mock_provenance.query_entity_lineage = AsyncMock(
        return_value={
            "entity": {"id": "herb-001", "name": "人参", "status": "pending"},
            "evidence": {
                "id": "ev-001",
                "content": "补气",
                "source_name": "本草纲目",
                "status": "pending",
            },
            "source": {"id": "src-001", "name": "本草纲目", "status": "pending"},
        }
    )

    resp = await client.get("/api/v1/provenance/entity/herb-001/lineage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"]["name"] == "人参"
    assert data["source"]["name"] == "本草纲目"
    assert data["evidence"]["content"] == "补气"
    _assert_frontend_payload(data)


@pytest.mark.asyncio
async def test_get_entity_lineage_not_found(client, mock_provenance):
    mock_provenance.query_entity_lineage = AsyncMock(return_value=None)

    resp = await client.get("/api/v1/provenance/entity/nonexistent/lineage")
    assert resp.status_code == 404


# ============ GET /provenance/source/{id}/derivations ============


@pytest.mark.asyncio
async def test_get_source_derivations(client, mock_provenance):
    mock_provenance.query_source_derivations = AsyncMock(
        return_value=[
            {
                "entity": {"id": "herb-001", "name": "人参", "status": "pending"},
                "evidence": {
                    "id": "ev-001",
                    "content": "补气",
                    "source_name": "本草纲目",
                    "status": "pending",
                },
                "source": {"id": "src-001", "name": "本草纲目", "status": "pending"},
            }
        ]
    )

    resp = await client.get("/api/v1/provenance/source/src-001/derivations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert len(data["derivations"]) == 1
    _assert_frontend_payload(data)


# ============ GET /provenance/entity/{id}/evidence ============


@pytest.mark.asyncio
async def test_collect_entity_evidence(client, mock_provenance):
    mock_provenance.collect_evidence_for_entity = AsyncMock(
        return_value=[
            {
                "evidence": {
                    "id": "ev-001",
                    "content": "补气",
                    "source_name": "本草纲目",
                    "status": "pending",
                },
                "source": {"id": "src-001", "name": "本草纲目", "status": "pending"},
            }
        ]
    )

    resp = await client.get("/api/v1/provenance/entity/herb-001/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert data["evidence"][0]["evidence"]["content"] == "补气"
    _assert_frontend_payload(data)


# ============ GET /provenance/entity/{id}/completeness ============


@pytest.mark.asyncio
async def test_check_completeness_complete(client, mock_provenance):
    mock_provenance.lineage_chain_completeness = AsyncMock(
        return_value={
            "entity": {"id": "herb-001", "name": "人参", "status": "pending"},
            "evidence": {
                "id": "ev-001",
                "content": "补气",
                "source_name": "本草纲目",
                "status": "pending",
            },
            "source": {"id": "src-001", "name": "本草纲目", "status": "pending"},
            "has_evidence": True,
            "has_source": True,
            "chain_complete": True,
        }
    )

    resp = await client.get("/api/v1/provenance/entity/herb-001/completeness")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chain_complete"] is True
    _assert_frontend_payload(data)


@pytest.mark.asyncio
async def test_check_completeness_not_found(client, mock_provenance):
    mock_provenance.lineage_chain_completeness = AsyncMock(return_value=None)

    resp = await client.get("/api/v1/provenance/entity/nonexistent/completeness")
    assert resp.status_code == 404
