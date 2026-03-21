"""
Provenance Module TDD Tests

Red Phase: These tests define the expected behavior of ProvenanceService.
They should FAIL initially because the implementation is incomplete.
Green Phase: Implement methods to make tests pass.
Refactor Phase: Improve code quality while keeping tests green.

Data Model: Entity -> has_evidence -> Evidence -> derived_from -> Source
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.provenance import ProvenanceService

pytestmark = pytest.mark.unit


# ============ Fixtures ============

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver"""
    driver = MagicMock()
    session = MagicMock()
    session.run = AsyncMock()
    session.close = AsyncMock()
    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()
    return driver


@pytest.fixture
def provenance_service(mock_neo4j_driver):
    """ProvenanceService with mocked Neo4j driver"""
    service = ProvenanceService()
    service.driver = mock_neo4j_driver
    return service


# ============ Test Cases ============

@pytest.mark.asyncio
async def test_create_evidence(provenance_service, mock_neo4j_driver):
    """Test creating an evidence node with required fields"""
    evidence_id = str(uuid4())
    mock_evidence = {
        "id": evidence_id,
        "content": "本草纲目记载人参主补五脏",
        "source_name": "Bencao Gangmu",
        "page_reference": "卷十二",
        "status": "pending"
    }
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "e": mock_evidence
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.create_evidence(
        content="本草纲目记载人参主补五脏",
        source_name="Bencao Gangmu",
        page_reference="卷十二"
    )

    assert result["content"] == "本草纲目记载人参主补五脏"
    assert result["source_name"] == "Bencao Gangmu"
    assert result["page_reference"] == "卷十二"
    assert result["status"] == "pending"
    mock_session.run.assert_called_once()


@pytest.mark.asyncio
async def test_get_evidence(provenance_service, mock_neo4j_driver):
    """Test retrieving an evidence node by ID"""
    evidence_id = str(uuid4())
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "e": {
            "id": evidence_id,
            "content": "人参主补五脏",
            "source_name": "Bencao Gangmu",
            "page_reference": "卷十二",
            "status": "pending"
        }
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.get_evidence(evidence_id)

    assert result["id"] == evidence_id
    assert result["content"] == "人参主补五脏"
    assert result["source_name"] == "Bencao Gangmu"


@pytest.mark.asyncio
async def test_get_evidence_not_found(provenance_service, mock_neo4j_driver):
    """Test that get_evidence returns None when evidence does not exist"""
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=None)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.get_evidence("nonexistent-id")

    assert result is None


@pytest.mark.asyncio
async def test_link_evidence_to_source(provenance_service, mock_neo4j_driver):
    """Test linking evidence to source using DERIVED_FROM relationship"""
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "r": {
            "type": "DERIVED_FROM",
            "status": "pending",
            "source_id": "source-123",
            "evidence_id": "evidence-456"
        }
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.link_evidence_to_source(
        evidence_id="evidence-456",
        source_id="source-123"
    )

    assert result["type"] == "DERIVED_FROM"
    assert result["status"] == "pending"
    mock_session.run.assert_called_once()


@pytest.mark.asyncio
async def test_query_entity_lineage(provenance_service, mock_neo4j_driver):
    """Test querying entity lineage: Entity -> Evidence -> Source chain"""
    entity_id = str(uuid4())
    evidence_id = str(uuid4())
    source_id = str(uuid4())

    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "entity": {"id": entity_id, "name": "RenShen"},
        "evidence": {"id": evidence_id, "content": "人参主补五脏"},
        "source": {"id": source_id, "name": "Bencao Gangmu", "author": "Li Shizhen"}
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.query_entity_lineage(
        entity_id=entity_id
    )

    assert result["entity"]["id"] == entity_id
    assert result["evidence"]["id"] == evidence_id
    assert result["source"]["id"] == source_id
    assert result["entity"]["name"] == "RenShen"
    assert result["source"]["author"] == "Li Shizhen"


@pytest.mark.asyncio
async def test_query_source_derivations(provenance_service, mock_neo4j_driver):
    """Test querying all entities derived from a specific source"""
    source_id = str(uuid4())
    entity1_id = str(uuid4())
    entity2_id = str(uuid4())

    mock_record1 = MagicMock()
    mock_record1.__getitem__ = lambda self, key: {
        "entity": {"id": entity1_id, "name": "RenShen"},
        "evidence": {"id": "ev-1", "content": "补气"},
        "source": {"id": source_id, "name": "Bencao Gangmu"}
    }[key]

    mock_record2 = MagicMock()
    mock_record2.__getitem__ = lambda self, key: {
        "entity": {"id": entity2_id, "name": "DangShen"},
        "evidence": {"id": "ev-2", "content": "补血"},
        "source": {"id": source_id, "name": "Bencao Gangmu"}
    }[key]

    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[mock_record1, mock_record2])
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.query_source_derivations(source_id=source_id)

    assert len(result) == 2
    assert result[0]["entity"]["name"] == "RenShen"
    assert result[1]["entity"]["name"] == "DangShen"


@pytest.mark.asyncio
async def test_collect_evidence_for_entity(provenance_service, mock_neo4j_driver):
    """Test collecting all evidence for a given entity"""
    entity_id = str(uuid4())
    evidence1_id = str(uuid4())
    evidence2_id = str(uuid4())

    mock_record1 = MagicMock()
    mock_record1.__getitem__ = lambda self, key: {
        "evidence": {"id": evidence1_id, "content": "补气养血"},
        "source": {"id": "src-1", "name": "Bencao Gangmu"}
    }[key]

    mock_record2 = MagicMock()
    mock_record2.__getitem__ = lambda self, key: {
        "evidence": {"id": evidence2_id, "content": "健脾益肺"},
        "source": {"id": "src-2", "name": "Shanghai Herbal"}
    }[key]

    mock_result = MagicMock()
    mock_result.data = AsyncMock(return_value=[mock_record1, mock_record2])
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.collect_evidence_for_entity(entity_id=entity_id)

    assert len(result) == 2
    assert result[0]["evidence"]["content"] == "补气养血"
    assert result[1]["evidence"]["content"] == "健脾益肺"


@pytest.mark.asyncio
async def test_lineage_chain_completeness(provenance_service, mock_neo4j_driver):
    """Test verifying lineage chain completeness: Entity has Evidence linked to Source"""
    entity_id = str(uuid4())
    evidence_id = str(uuid4())
    source_id = str(uuid4())

    # Mock the complete chain check
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: {
        "entity": {"id": entity_id, "name": "RenShen"},
        "evidence": {"id": evidence_id, "content": "人参主补五脏"},
        "source": {"id": source_id, "name": "Bencao Gangmu"},
        "has_evidence": True,
        "has_source": True,
        "chain_complete": True
    }[key]

    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=mock_record)
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)

    result = await provenance_service.lineage_chain_completeness(entity_id=entity_id)

    assert result["chain_complete"] is True
    assert result["has_evidence"] is True
    assert result["has_source"] is True
    assert result["entity"]["name"] == "RenShen"
