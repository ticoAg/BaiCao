import warnings
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.models import VerificationEvidenceModel, VerificationModel


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_create_verification_then_verify_updates_postgres_and_neo4j(
    client,
    demo_seed_data,
    db_session_factory,
    load_graph_node,
):
    chenpi_id = demo_seed_data["herb_ids"]["陈皮"]
    source_id = demo_seed_data["source_ids"]["中国药典（2020年版）"]
    baseline_node = await load_graph_node(chenpi_id)

    assert baseline_node is not None
    assert baseline_node["name"] == "陈皮"
    assert baseline_node["status"] == "pending"

    claimed_value = f"陈皮 integration smoke {uuid4()}"
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        create_response = await client.post(
            "/api/v1/verifications/",
            json={
                "entity_type": "herb",
                "entity_id": chenpi_id,
                "field_name": "description",
                "claimed_value": claimed_value,
                "source_id": source_id,
                "evidence": [
                    {
                        "source_id": source_id,
                        "quote": "陈皮：橘及其栽培变种的干燥成熟果皮。",
                        "page_reference": "2020版一部 191页",
                        "relevance_score": 0.98,
                    }
                ],
            },
        )

    assert create_response.status_code == 200

    created = create_response.json()
    verification_id = UUID(created["id"])

    assert created["entity_type"] == "herb"
    assert created["entity_id"] == chenpi_id
    assert created["status"] == "pending"
    assert created["applicant_id"] == demo_seed_data["user_ids"]["demo_user"]
    assert created["source_id"] == source_id

    async with db_session_factory() as session:
        verification = await session.get(VerificationModel, verification_id)
        assert verification is not None
        assert verification.claimed_value == claimed_value
        assert str(verification.applicant_id) == demo_seed_data["user_ids"]["demo_user"]

        evidence_rows = await session.execute(
            select(VerificationEvidenceModel).where(
                VerificationEvidenceModel.verification_id == verification_id
            )
        )
        evidence = evidence_rows.scalars().all()
        assert len(evidence) == 1
        assert evidence[0].quote == "陈皮：橘及其栽培变种的干燥成熟果皮。"

    verify_response = await client.post(
        f"/api/v1/verifications/{verification_id}/verify",
        params={"status": "verified", "verdict": "专家审核通过 integration smoke"},
    )

    assert verify_response.status_code == 200

    approved = verify_response.json()
    assert approved["id"] == str(verification_id)
    assert approved["status"] == "verified"
    assert approved["verifier_id"] == demo_seed_data["user_ids"]["demo_expert"]
    assert approved["verdict"] == "专家审核通过 integration smoke"
    assert approved["verified_at"] is not None

    async with db_session_factory() as session:
        refreshed = await session.get(VerificationModel, verification_id)
        assert refreshed is not None
        assert refreshed.status == "verified"
        assert str(refreshed.verifier_id) == demo_seed_data["user_ids"]["demo_expert"]
        assert refreshed.verified_at is not None

    synced_node = await load_graph_node(chenpi_id)
    assert synced_node is not None
    assert synced_node["status"] == "verified"
    assert synced_node["verification_id"] == str(verification_id)
    assert synced_node["verified_by"] == demo_seed_data["user_ids"]["demo_expert"]
    assert synced_node["verified_at"] is not None
