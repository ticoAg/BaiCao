"""Provenance API route tests - mock ProvenanceService for unit testing"""
import pytest
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from app.main import app


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


# ============ POST /provenance/evidence ============


@pytest.mark.asyncio
async def test_create_evidence(client, mock_provenance):
    mock_provenance.create_evidence = AsyncMock(return_value={
        "id": "ev-001",
        "content": "人参补气",
        "source_name": "本草纲目",
        "page_reference": "卷十二",
        "status": "pending",
    })

    resp = await client.post("/api/v1/provenance/evidence", json={
        "content": "人参补气",
        "source_name": "本草纲目",
        "page_reference": "卷十二",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "ev-001"
    assert data["content"] == "人参补气"
    mock_provenance.create_evidence.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_evidence_missing_fields(client, mock_provenance):
    resp = await client.post("/api/v1/provenance/evidence", json={})
    assert resp.status_code == 422


# ============ GET /provenance/evidence/{id} ============


@pytest.mark.asyncio
async def test_get_evidence_found(client, mock_provenance):
    mock_provenance.get_evidence = AsyncMock(return_value={
        "id": "ev-001",
        "content": "人参补气",
        "source_name": "本草纲目",
        "status": "pending",
    })

    resp = await client.get("/api/v1/provenance/evidence/ev-001")
    assert resp.status_code == 200
    assert resp.json()["id"] == "ev-001"


@pytest.mark.asyncio
async def test_get_evidence_not_found(client, mock_provenance):
    mock_provenance.get_evidence = AsyncMock(return_value=None)

    resp = await client.get("/api/v1/provenance/evidence/nonexistent")
    assert resp.status_code == 404


# ============ POST /provenance/evidence/{id}/link-source ============


@pytest.mark.asyncio
async def test_link_evidence_to_source(client, mock_provenance):
    mock_provenance.link_evidence_to_source = AsyncMock(return_value={
        "status": "pending",
        "source_id": "src-001",
        "evidence_id": "ev-001",
    })

    resp = await client.post("/api/v1/provenance/evidence/ev-001/link-source", json={
        "source_id": "src-001",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Evidence linked to source"


# ============ GET /provenance/entity/{id}/lineage ============


@pytest.mark.asyncio
async def test_get_entity_lineage_found(client, mock_provenance):
    mock_provenance.query_entity_lineage = AsyncMock(return_value={
        "entity": {"id": "herb-001", "name": "人参"},
        "evidence": {"id": "ev-001", "content": "补气"},
        "source": {"id": "src-001", "name": "本草纲目"},
    })

    resp = await client.get("/api/v1/provenance/entity/herb-001/lineage")
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"]["name"] == "人参"
    assert data["source"]["name"] == "本草纲目"


@pytest.mark.asyncio
async def test_get_entity_lineage_not_found(client, mock_provenance):
    mock_provenance.query_entity_lineage = AsyncMock(return_value=None)

    resp = await client.get("/api/v1/provenance/entity/nonexistent/lineage")
    assert resp.status_code == 404


# ============ GET /provenance/source/{id}/derivations ============


@pytest.mark.asyncio
async def test_get_source_derivations(client, mock_provenance):
    mock_provenance.query_source_derivations = AsyncMock(return_value=[
        {
            "entity": {"id": "herb-001", "name": "人参"},
            "evidence": {"id": "ev-001"},
            "source": {"id": "src-001"},
        }
    ])

    resp = await client.get("/api/v1/provenance/source/src-001/derivations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1
    assert len(data["derivations"]) == 1


# ============ GET /provenance/entity/{id}/evidence ============


@pytest.mark.asyncio
async def test_collect_entity_evidence(client, mock_provenance):
    mock_provenance.collect_evidence_for_entity = AsyncMock(return_value=[
        {"evidence": {"id": "ev-001", "content": "补气"}, "source": {"id": "src-001"}}
    ])

    resp = await client.get("/api/v1/provenance/entity/herb-001/evidence")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 1


# ============ GET /provenance/entity/{id}/completeness ============


@pytest.mark.asyncio
async def test_check_completeness_complete(client, mock_provenance):
    mock_provenance.lineage_chain_completeness = AsyncMock(return_value={
        "entity": {"id": "herb-001"},
        "evidence": {"id": "ev-001"},
        "source": {"id": "src-001"},
        "has_evidence": True,
        "has_source": True,
        "chain_complete": True,
    })

    resp = await client.get("/api/v1/provenance/entity/herb-001/completeness")
    assert resp.status_code == 200
    assert resp.json()["chain_complete"] is True


@pytest.mark.asyncio
async def test_check_completeness_not_found(client, mock_provenance):
    mock_provenance.lineage_chain_completeness = AsyncMock(return_value=None)

    resp = await client.get("/api/v1/provenance/entity/nonexistent/completeness")
    assert resp.status_code == 404
