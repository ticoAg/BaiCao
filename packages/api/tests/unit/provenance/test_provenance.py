"""ProvenanceService tests against the current Chinese Neo4j graph model."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.provenance import (
    ORIGINATED_FROM_REL,
    QUERY_COLLECT_ENTITY_EVIDENCE,
    QUERY_CREATE_EVIDENCE,
    QUERY_ENTITY_LINEAGE,
    QUERY_GET_EVIDENCE_BY_ID,
    QUERY_LINEAGE_COMPLETENESS,
    QUERY_LINK_EVIDENCE_TO_SOURCE,
    QUERY_SOURCE_DERIVATIONS,
    SUPPORTED_BY_REL,
    ProvenanceService,
    to_frontend_node,
    to_frontend_relationship,
)

pytestmark = pytest.mark.unit


def _record(**fields):
    mock_record = MagicMock()
    mock_record.__getitem__ = lambda self, key: fields[key]
    return mock_record


def _ready_session(mock_neo4j_driver, record=None, records=None):
    mock_result = MagicMock()
    mock_result.single = AsyncMock(return_value=record)
    mock_result.data = AsyncMock(return_value=records or [])
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_neo4j_driver.session = MagicMock(return_value=mock_session)
    return mock_session


@pytest.fixture
def mock_neo4j_driver():
    driver = MagicMock()
    session = MagicMock()
    session.run = AsyncMock()
    session.close = AsyncMock()
    driver.session = MagicMock(return_value=session)
    driver.close = AsyncMock()
    return driver


@pytest.fixture
def provenance_service(mock_neo4j_driver):
    service = ProvenanceService()
    service.driver = mock_neo4j_driver
    return service


def _compact(query: str) -> str:
    return "".join(query.split())


def test_queries_use_chinese_graph_model():
    assert "证据" in QUERY_CREATE_EVIDENCE
    assert "标识" in QUERY_GET_EVIDENCE_BY_ID
    assert SUPPORTED_BY_REL == "由证据支持"
    assert ORIGINATED_FROM_REL == "来源于"
    lineage = _compact(QUERY_ENTITY_LINEAGE)
    collect = _compact(QUERY_COLLECT_ENTITY_EVIDENCE)
    completeness = _compact(QUERY_LINEAGE_COMPLETENESS)
    derivations = _compact(QUERY_SOURCE_DERIVATIONS)
    assert "-[:由证据支持]->" in lineage
    assert "(entity)-[:来源于]->" in lineage
    assert "(evidence)-[:来源于]->" in lineage
    assert "coalesce(entity_source,evidence_source)" in lineage
    assert "标识:$source_id" in derivations
    assert "(entity)-[:来源于]->" in collect
    assert "coalesce(entity_source,evidence_source)" in collect
    assert "(entity)-[:来源于]->" in completeness
    assert "coalesce(entity_source,evidence_source)" in completeness
    assert "来源于" in QUERY_LINK_EVIDENCE_TO_SOURCE
    assert "entity{标识:$entity_id}" in completeness
    assert ":Evidence" not in QUERY_CREATE_EVIDENCE
    assert "derived_from" not in QUERY_LINK_EVIDENCE_TO_SOURCE
    assert "DERIVED_FROM" not in QUERY_LINK_EVIDENCE_TO_SOURCE
    assert "(evidence:证据)-[:来源于]->(source:来源)" not in lineage
    assert "UNION" in QUERY_SOURCE_DERIVATIONS


def test_to_frontend_node_hides_chinese_storage_keys():
    mapped = to_frontend_node(
        {
            "标识": "ev-1",
            "名称": "本草纲目",
            "证据原文": "人参主补五脏",
            "状态": "待验证",
            "来源": "本草纲目",
            "页码": "卷十二",
            "导入源": "不应泄漏",
        },
        include_evidence_fields=True,
    )

    assert mapped is not None
    assert mapped == {
        "id": "ev-1",
        "content": "人参主补五脏",
        "source_name": "本草纲目",
        "page_reference": "卷十二",
        "status": "pending",
    }
    assert "标识" not in mapped
    assert "证据原文" not in mapped
    assert "状态" not in mapped
    assert "来源" not in mapped
    assert "页码" not in mapped
    assert "导入源" not in mapped
    assert "name" not in mapped
    assert "evidence_text" not in mapped


def test_to_frontend_relationship_uses_originated_from():
    mapped = to_frontend_relationship(
        {"状态": "已验证"},
        rel_type="来源于",
        evidence_id="ev-1",
        source_id="src-1",
    )

    assert mapped == {
        "type": "来源于",
        "status": "verified",
        "evidence_id": "ev-1",
        "source_id": "src-1",
    }
    assert "状态" not in mapped


@pytest.mark.asyncio
async def test_create_evidence(provenance_service, mock_neo4j_driver):
    evidence_id = str(uuid4())
    mock_evidence = {
        "标识": evidence_id,
        "名称": "Bencao Gangmu",
        "证据原文": "本草纲目记载人参主补五脏",
        "状态": "待验证",
        "来源": "Bencao Gangmu",
        "页码": "卷十二",
    }
    mock_session = _ready_session(
        mock_neo4j_driver, record=_record(e=mock_evidence)
    )

    result = await provenance_service.create_evidence(
        content="本草纲目记载人参主补五脏",
        source_name="Bencao Gangmu",
        page_reference="卷十二",
    )

    assert result["content"] == "本草纲目记载人参主补五脏"
    assert result["source_name"] == "Bencao Gangmu"
    assert result["page_reference"] == "卷十二"
    assert result["status"] == "pending"
    assert "标识" not in result
    assert "证据原文" not in result
    mock_session.run.assert_called_once()
    query = mock_session.run.call_args.args[0]
    stored = mock_session.run.call_args.kwargs["props"]
    assert "证据" in query
    assert stored["标识"]
    assert stored["名称"] == "Bencao Gangmu"
    assert stored["证据原文"] == "本草纲目记载人参主补五脏"
    assert stored["状态"] == "待验证"
    assert stored["来源"] == "Bencao Gangmu"
    assert stored["页码"] == "卷十二"
    assert "id" not in stored
    assert "content" not in stored
    assert "source_name" not in stored
    assert "evidence_text" not in stored


@pytest.mark.asyncio
async def test_get_evidence(provenance_service, mock_neo4j_driver):
    evidence_id = str(uuid4())
    _ready_session(
        mock_neo4j_driver,
        record=_record(
            e={
                "标识": evidence_id,
                "名称": "Bencao Gangmu",
                "证据原文": "人参主补五脏",
                "状态": "待验证",
                "来源": "Bencao Gangmu",
                "页码": "卷十二",
            }
        ),
    )

    result = await provenance_service.get_evidence(evidence_id)

    assert result is not None
    assert result["id"] == evidence_id
    assert result["content"] == "人参主补五脏"
    assert result["source_name"] == "Bencao Gangmu"
    assert result["page_reference"] == "卷十二"
    assert "证据原文" not in result


@pytest.mark.asyncio
async def test_get_evidence_not_found(provenance_service, mock_neo4j_driver):
    _ready_session(mock_neo4j_driver, record=None)

    result = await provenance_service.get_evidence("nonexistent-id")

    assert result is None


@pytest.mark.asyncio
async def test_link_evidence_to_source(provenance_service, mock_neo4j_driver):
    mock_session = _ready_session(
        mock_neo4j_driver,
        record=_record(r={"状态": "待验证"}, rel_type="来源于"),
    )

    result = await provenance_service.link_evidence_to_source(
        evidence_id="evidence-456",
        source_id="source-123",
    )

    assert result["type"] == "来源于"
    assert result["status"] == "pending"
    assert result["evidence_id"] == "evidence-456"
    assert result["source_id"] == "source-123"
    query = mock_session.run.call_args.args[0]
    assert "来源于" in query
    assert "证据" in query
    assert "来源" in query
    assert mock_session.run.call_args.kwargs["props"]["状态"] == "待验证"


@pytest.mark.asyncio
async def test_query_entity_lineage(provenance_service, mock_neo4j_driver):
    entity_id = str(uuid4())
    evidence_id = str(uuid4())
    source_id = str(uuid4())
    _ready_session(
        mock_neo4j_driver,
        record=_record(
            entity={"标识": entity_id, "名称": "人参", "状态": "已验证"},
            evidence={
                "标识": evidence_id,
                "名称": "Bencao Gangmu",
                "证据原文": "人参主补五脏",
                "状态": "待验证",
                "来源": "Bencao Gangmu",
            },
            source={"标识": source_id, "名称": "本草纲目", "状态": "已验证"},
        ),
    )

    result = await provenance_service.query_entity_lineage(entity_id=entity_id)

    assert result is not None
    assert result["entity"] == {"id": entity_id, "name": "人参", "status": "verified"}
    assert result["evidence"]["id"] == evidence_id
    assert result["evidence"]["content"] == "人参主补五脏"
    assert result["evidence"]["source_name"] == "Bencao Gangmu"
    assert result["source"] == {"id": source_id, "name": "本草纲目", "status": "verified"}
    assert "作者" not in result["source"]
    assert "标识" not in result["entity"]


@pytest.mark.asyncio
async def test_query_source_derivations(provenance_service, mock_neo4j_driver):
    source_id = str(uuid4())
    entity1_id = str(uuid4())
    entity2_id = str(uuid4())
    _ready_session(
        mock_neo4j_driver,
        records=[
            {
                "entity": {"标识": entity1_id, "名称": "人参", "状态": "待验证"},
                "evidence": {
                    "标识": "ev-1",
                    "名称": "本草纲目",
                    "证据原文": "补气",
                    "状态": "待验证",
                    "来源": "本草纲目",
                },
                "source": {"标识": source_id, "名称": "本草纲目", "状态": "待验证"},
            },
            {
                "entity": {"标识": entity2_id, "名称": "党参", "状态": "待验证"},
                "evidence": {
                    "标识": "ev-2",
                    "名称": "本草纲目",
                    "证据原文": "补血",
                    "状态": "待验证",
                    "来源": "本草纲目",
                },
                "source": {"标识": source_id, "名称": "本草纲目", "状态": "待验证"},
            },
        ],
    )

    result = await provenance_service.query_source_derivations(source_id=source_id)

    assert len(result) == 2
    assert result[0]["entity"]["name"] == "人参"
    assert result[1]["entity"]["name"] == "党参"
    assert result[0]["evidence"]["content"] == "补气"


@pytest.mark.asyncio
async def test_collect_evidence_for_entity(provenance_service, mock_neo4j_driver):
    entity_id = str(uuid4())
    evidence1_id = str(uuid4())
    evidence2_id = str(uuid4())
    _ready_session(
        mock_neo4j_driver,
        records=[
            {
                "evidence": {
                    "标识": evidence1_id,
                    "名称": "本草纲目",
                    "证据原文": "补气养血",
                    "状态": "待验证",
                    "来源": "本草纲目",
                },
                "source": {"标识": "src-1", "名称": "本草纲目", "状态": "待验证"},
            },
            {
                "evidence": {
                    "标识": evidence2_id,
                    "名称": "上海本草",
                    "证据原文": "健脾益肺",
                    "状态": "待验证",
                    "来源": "上海本草",
                },
                "source": {"标识": "src-2", "名称": "上海本草", "状态": "待验证"},
            },
        ],
    )

    result = await provenance_service.collect_evidence_for_entity(entity_id=entity_id)

    assert len(result) == 2
    assert result[0]["evidence"]["content"] == "补气养血"
    assert result[1]["evidence"]["content"] == "健脾益肺"
    assert result[0]["source"]["name"] == "本草纲目"


@pytest.mark.asyncio
async def test_lineage_chain_completeness(provenance_service, mock_neo4j_driver):
    entity_id = str(uuid4())
    evidence_id = str(uuid4())
    source_id = str(uuid4())
    mock_session = _ready_session(
        mock_neo4j_driver,
        record=_record(
            entity={"标识": entity_id, "名称": "人参", "状态": "待验证"},
            evidence={
                "标识": evidence_id,
                "名称": "本草纲目",
                "证据原文": "人参主补五脏",
                "状态": "待验证",
                "来源": "本草纲目",
            },
            source={"标识": source_id, "名称": "本草纲目", "状态": "待验证"},
            has_evidence=True,
            has_source=True,
            chain_complete=True,
        ),
    )

    result = await provenance_service.lineage_chain_completeness(entity_id=entity_id)

    assert result is not None
    assert result["chain_complete"] is True
    assert result["has_evidence"] is True
    assert result["has_source"] is True
    assert result["entity"]["name"] == "人参"
    assert result["evidence"]["content"] == "人参主补五脏"
    assert "标识" not in result["entity"]
    query = _compact(mock_session.run.call_args.args[0])
    assert "collect(DISTINCTevidence)ASevidences" in query
    assert "LIMIT1" not in query


@pytest.mark.asyncio
async def test_query_entity_lineage_uses_entity_originated_from_source(
    provenance_service, mock_neo4j_driver
):
    entity_id = str(uuid4())
    mock_session = _ready_session(
        mock_neo4j_driver,
        record=_record(
            entity={"标识": entity_id, "名称": "人参", "状态": "待验证"},
            evidence={
                "标识": "ev-entity-source",
                "名称": "本草纲目",
                "证据原文": "人参主补五脏",
                "状态": "待验证",
                "来源": "本草纲目",
            },
            source={"标识": "src-entity", "名称": "本草纲目", "状态": "待验证"},
        ),
    )

    result = await provenance_service.query_entity_lineage(entity_id=entity_id)

    assert result is not None
    assert result["source"]["id"] == "src-entity"
    query = mock_session.run.call_args.args[0]
    compacted = _compact(query)
    assert "(entity)-[:来源于]->" in compacted
    assert "coalesce(entity_source,evidence_source)" in compacted
