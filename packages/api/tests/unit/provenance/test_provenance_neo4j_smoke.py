"""Isolated Neo4j smoke for provenance create/get/link/lineage/evidence/completeness."""

from uuid import uuid4

import pytest
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from app.core.config import get_settings
from app.provenance import ProvenanceService
from knowledge_model.constants import NodeStatus, NodeType, to_neo4j_label
from knowledge_model.graph_i18n import to_graph_properties


pytestmark = pytest.mark.integration


async def _connect_or_skip():
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
        connection_timeout=3,
    )
    try:
        await driver.verify_connectivity()
    except (ServiceUnavailable, AuthError, OSError) as exc:
        await driver.close()
        pytest.skip(f"Isolated Neo4j smoke skipped: {exc}")
    return driver


@pytest.mark.asyncio
async def test_provenance_roundtrip_on_isolated_neo4j():
    driver = await _connect_or_skip()
    service = ProvenanceService()
    service.driver = driver
    suffix = uuid4().hex[:8]
    entity_id = f"prov-smoke-entity-{suffix}"
    source_id = f"prov-smoke-source-{suffix}"
    created_ids = [entity_id, source_id]
    herb_label = to_neo4j_label(NodeType.HERB)
    source_label = to_neo4j_label(NodeType.SOURCE)

    try:
        async with driver.session() as session:
            result = await session.run(
                f"""
                CREATE (entity:{herb_label} $entity_props)
                CREATE (source:{source_label} $source_props)
                """,
                entity_props=to_graph_properties(
                    {
                        "id": entity_id,
                        "name": f"隔离溯源药材-{suffix}",
                        "status": NodeStatus.PENDING.value,
                    }
                ),
                source_props=to_graph_properties(
                    {
                        "id": source_id,
                        "name": f"隔离溯源来源-{suffix}",
                        "status": NodeStatus.PENDING.value,
                    }
                ),
            )
            await result.consume()

        evidence = await service.create_evidence(
            content="人参主补五脏，安精神。",
            source_name=f"隔离溯源来源名-{suffix}",
            page_reference="卷十二",
        )
        assert evidence["content"] == "人参主补五脏，安精神。"
        assert evidence["source_name"] == f"隔离溯源来源名-{suffix}"
        assert evidence["page_reference"] == "卷十二"
        assert evidence["status"] == "pending"
        assert "标识" not in evidence
        assert "证据原文" not in evidence
        evidence_id = evidence["id"]
        created_ids.append(evidence_id)

        fetched = await service.get_evidence(evidence_id)
        assert fetched is not None
        assert fetched["id"] == evidence_id
        assert fetched["content"] == "人参主补五脏，安精神。"
        assert fetched["source_name"] == f"隔离溯源来源名-{suffix}"
        assert fetched["page_reference"] == "卷十二"

        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (entity {标识: $entity_id})
                MATCH (evidence {标识: $evidence_id})
                MATCH (source {标识: $source_id})
                MERGE (entity)-[:来源于]->(source)
                MERGE (entity)-[:由证据支持]->(evidence)
                """,
                entity_id=entity_id,
                evidence_id=evidence_id,
                source_id=source_id,
            )
            await result.consume()

        lineage = await service.query_entity_lineage(entity_id)
        assert lineage is not None
        assert lineage["entity"]["id"] == entity_id
        assert lineage["evidence"]["id"] == evidence_id
        assert lineage["source"]["id"] == source_id
        assert lineage["evidence"]["content"] == "人参主补五脏，安精神。"
        assert lineage["evidence"]["source_name"] == f"隔离溯源来源名-{suffix}"
        assert "证据原文" not in lineage["evidence"]

        collected = await service.collect_evidence_for_entity(entity_id)
        assert len(collected) == 1
        assert collected[0]["source"]["id"] == source_id

        completeness = await service.lineage_chain_completeness(entity_id)
        assert completeness is not None
        assert completeness["chain_complete"] is True
        assert completeness["has_evidence"] is True
        assert completeness["has_source"] is True

        derivations = await service.query_source_derivations(source_id)
        assert any(item["entity"]["id"] == entity_id for item in derivations)

        linked = await service.link_evidence_to_source(evidence_id, source_id)
        assert linked["type"] == "来源于"
        assert linked["status"] == "pending"
        assert linked["evidence_id"] == evidence_id
        assert linked["source_id"] == source_id
    finally:
        try:
            async with driver.session() as session:
                result = await session.run(
                    "MATCH (n) WHERE n.标识 IN $ids DETACH DELETE n",
                    ids=created_ids,
                )
                await result.consume()
        finally:
            await driver.close()
