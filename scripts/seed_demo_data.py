#!/usr/bin/env python3
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

from neo4j import AsyncGraphDatabase

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "packages" / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal, init_db
from app.models import (
    EntityType,
    HerbModel,
    SourceModel,
    SourceType,
    UserModel,
    UserRole,
    VerificationEvidenceModel,
    VerificationModel,
    VerificationStatus,
)

settings = get_settings()


def u(value: str) -> UUID:
    return UUID(value)


DATASET_TAG = "demo-20260320"
NOW = datetime.now().replace(microsecond=0)


USERS = [
    {
        "id": u("11111111-1111-1111-1111-111111111111"),
        "username": "demo_user",
        "email": "demo-user@baicao.local",
        "hashed_password": "demo-not-for-login",
        "role": UserRole.USER,
        "is_active": True,
        "expert_fields": [],
        "verified_at": None,
    },
    {
        "id": u("22222222-2222-2222-2222-222222222222"),
        "username": "demo_expert",
        "email": "demo-expert@baicao.local",
        "hashed_password": "demo-not-for-login",
        "role": UserRole.EXPERT,
        "is_active": True,
        "expert_fields": ["中药鉴定", "药性归经", "本草文献"],
        "verified_at": NOW,
    },
]


SOURCES = [
    {
        "id": u("33333333-3333-3333-3333-333333333331"),
        "name": "中国药典（2020年版）",
        "type": SourceType.DATABASE,
        "author": "国家药典委员会",
        "publication_date": "2020",
        "url": None,
        "isbn": None,
        "pages": "191-194",
        "citation": "国家药典委员会. 中国药典（2020年版）. 北京: 中国医药科技出版社.",
        "description": "国家药典标准与药材性状、功效、归经等基础来源。",
    },
    {
        "id": u("33333333-3333-3333-3333-333333333332"),
        "name": "本草纲目",
        "type": SourceType.ANCIENT,
        "author": "李时珍",
        "publication_date": "1596",
        "url": None,
        "isbn": None,
        "pages": "卷一至卷五十二",
        "citation": "李时珍. 本草纲目. 明万历年间成书.",
        "description": "经典本草文献，用于演示古籍溯源。",
    },
    {
        "id": u("33333333-3333-3333-3333-333333333333"),
        "name": "中药现代研究汇编",
        "type": SourceType.MODERN,
        "author": "白草药坛 Demo Lab",
        "publication_date": "2024",
        "url": "https://example.com/baicao-demo-study",
        "isbn": None,
        "pages": "12-48",
        "citation": "白草药坛 Demo Lab. 中药现代研究汇编. 2024.",
        "description": "用于演示成分、现代药理和问答引用。",
    },
]


HERBS = [
    {
        "id": u("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1"),
        "name": "人参",
        "latin_name": "Panax ginseng C.A.Mey.",
        "category": "补气药",
        "description": "五加科植物人参的干燥根和根茎，常用于大补元气、益脾肺、生津安神。",
    },
    {
        "id": u("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2"),
        "name": "黄芪",
        "latin_name": "Astragalus membranaceus",
        "category": "补气药",
        "description": "豆科植物蒙古黄芪或膜荚黄芪的干燥根，常用于补气升阳、固表止汗。",
    },
    {
        "id": u("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa3"),
        "name": "陈皮",
        "latin_name": "Citrus reticulata Blanco",
        "category": "理气药",
        "description": "芸香科植物橘及其栽培变种的干燥成熟果皮，主用于理气健脾、燥湿化痰。",
    },
]


VERIFICATIONS = [
    {
        "id": u("44444444-4444-4444-4444-444444444441"),
        "entity_type": EntityType.HERB,
        "entity_id": str(HERBS[2]["id"]),
        "field_name": "description",
        "claimed_value": "陈皮为芸香科植物橘及其栽培变种的干燥成熟果皮。",
        "source_id": SOURCES[0]["id"],
        "status": VerificationStatus.PENDING,
        "applicant_id": USERS[0]["id"],
        "verifier_id": None,
        "verdict": None,
        "verified_at": None,
        "created_at": NOW,
    },
    {
        "id": u("44444444-4444-4444-4444-444444444442"),
        "entity_type": EntityType.EFFICACY,
        "entity_id": "黄芪::补气升阳",
        "field_name": "efficacy",
        "claimed_value": "黄芪可补气升阳、固表止汗。",
        "source_id": SOURCES[2]["id"],
        "status": VerificationStatus.PENDING,
        "applicant_id": USERS[0]["id"],
        "verifier_id": None,
        "verdict": None,
        "verified_at": None,
        "created_at": NOW,
    },
    {
        "id": u("44444444-4444-4444-4444-444444444443"),
        "entity_type": EntityType.HERB,
        "entity_id": str(HERBS[0]["id"]),
        "field_name": "category",
        "claimed_value": "人参属于补气药。",
        "source_id": SOURCES[0]["id"],
        "status": VerificationStatus.VERIFIED,
        "applicant_id": USERS[0]["id"],
        "verifier_id": USERS[1]["id"],
        "verdict": "药典与图谱一致，予以通过。",
        "verified_at": NOW,
        "created_at": NOW,
    },
]


VERIFICATION_EVIDENCES = [
    {
        "id": u("55555555-5555-5555-5555-555555555551"),
        "verification_id": VERIFICATIONS[0]["id"],
        "source_id": SOURCES[0]["id"],
        "quote": "陈皮：橘及其栽培变种的干燥成熟果皮。",
        "page_reference": "2020版一部 191页",
        "relevance_score": 0.98,
    },
    {
        "id": u("55555555-5555-5555-5555-555555555552"),
        "verification_id": VERIFICATIONS[1]["id"],
        "source_id": SOURCES[2]["id"],
        "quote": "黄芪在补气升阳与卫表固护方面应用广泛。",
        "page_reference": "第18页",
        "relevance_score": 0.91,
    },
]


GRAPH_NODES = [
    {
        "label": "Herb",
        "name": "人参",
        "props": {
            "id": str(HERBS[0]["id"]),
            "type": "base",
            "category": "补气药",
            "latin_name": HERBS[0]["latin_name"],
            "description": HERBS[0]["description"],
            "source": SOURCES[0]["name"],
            "status": "verified",
            "verification_id": str(VERIFICATIONS[2]["id"]),
            "verified_by": str(USERS[1]["id"]),
            "verified_at": NOW.isoformat(),
            "dataset": DATASET_TAG,
        },
    },
    {
        "label": "Herb",
        "name": "黄芪",
        "props": {
            "id": str(HERBS[1]["id"]),
            "type": "base",
            "category": "补气药",
            "latin_name": HERBS[1]["latin_name"],
            "description": HERBS[1]["description"],
            "source": SOURCES[0]["name"],
            "status": "verified",
            "verification_id": None,
            "verified_by": None,
            "verified_at": None,
            "dataset": DATASET_TAG,
        },
    },
    {
        "label": "Herb",
        "name": "陈皮",
        "props": {
            "id": str(HERBS[2]["id"]),
            "type": "base",
            "category": "理气药",
            "latin_name": HERBS[2]["latin_name"],
            "description": HERBS[2]["description"],
            "source": SOURCES[0]["name"],
            "status": "pending",
            "verification_id": None,
            "verified_by": None,
            "verified_at": None,
            "dataset": DATASET_TAG,
        },
    },
    {"label": "Component", "name": "人参皂苷Rb1", "props": {"id": "c-renshen-rb1", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Component", "name": "人参多糖", "props": {"id": "c-renshen-polysaccharide", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Component", "name": "黄芪甲苷", "props": {"id": "c-huangqi-astragaloside", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Component", "name": "黄芪多糖", "props": {"id": "c-huangqi-polysaccharide", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Component", "name": "挥发油", "props": {"id": "c-chenpi-oil", "source": SOURCES[2]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Component", "name": "橙皮苷", "props": {"id": "c-chenpi-hesperidin", "source": SOURCES[2]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Component", "name": "陈皮素", "props": {"id": "c-chenpi-nobiletin", "source": SOURCES[2]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "大补元气", "props": {"id": "e-renshen-1", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "健脾益肺", "props": {"id": "e-renshen-2", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "生津养血", "props": {"id": "e-renshen-3", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "安神益智", "props": {"id": "e-renshen-4", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "补气升阳", "props": {"id": "e-huangqi-1", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "固表止汗", "props": {"id": "e-huangqi-2", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "利水消肿", "props": {"id": "e-huangqi-3", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "托毒生肌", "props": {"id": "e-huangqi-4", "source": SOURCES[2]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "理气健脾", "props": {"id": "e-chenpi-1", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Efficacy", "name": "燥湿化痰", "props": {"id": "e-chenpi-2", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Flavor", "name": "甘", "props": {"id": "f-gan", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Flavor", "name": "微苦", "props": {"id": "f-wei-ku", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Flavor", "name": "微温", "props": {"id": "f-wei-wen", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Flavor", "name": "辛", "props": {"id": "f-xin", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Flavor", "name": "苦", "props": {"id": "f-ku", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Meridian", "name": "脾经", "props": {"id": "m-pi", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Meridian", "name": "肺经", "props": {"id": "m-fei", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Meridian", "name": "心经", "props": {"id": "m-xin", "source": SOURCES[0]["name"], "status": "verified", "dataset": DATASET_TAG}},
    {"label": "Variant", "name": "大红皮", "props": {"id": "v-chenpi-1", "parent_herb": "陈皮", "description": "果实成熟度较高，皮厚色红。", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Variant", "name": "二红皮", "props": {"id": "v-chenpi-2", "parent_herb": "陈皮", "description": "成熟度中等，香气清扬。", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Process", "name": "晒干陈化", "props": {"id": "p-chenpi-1", "description": "采收果皮后阴干、晒干，再长期陈化。", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Trait", "name": "油室", "props": {"id": "t-chenpi-1", "category": "external", "description": "表面有多数凹入油点。", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "Trait", "name": "外皮棕红", "props": {"id": "t-chenpi-2", "category": "external", "description": "外表面棕红或红黄色。", "source": SOURCES[0]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "TimePoint", "name": "3年", "props": {"id": "tp-3", "years": 3, "description": "三年陈化后香气形成。", "source": SOURCES[2]["name"], "status": "pending", "dataset": DATASET_TAG}},
    {"label": "TimePoint", "name": "5年", "props": {"id": "tp-5", "years": 5, "description": "五年陈化后气味醇厚。", "source": SOURCES[2]["name"], "status": "pending", "dataset": DATASET_TAG}},
]


GRAPH_EDGES = [
    {"from": ("Herb", "人参"), "to": ("Component", "人参皂苷Rb1"), "type": "CONTAINS", "props": {"status": "verified", "quantity": "主要皂苷成分", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Component", "人参多糖"), "type": "CONTAINS", "props": {"status": "verified", "quantity": "多糖活性组分", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Efficacy", "大补元气"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Efficacy", "健脾益肺"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Efficacy", "生津养血"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Efficacy", "安神益智"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Flavor", "甘"), "type": "HAS_FLAVOR", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Flavor", "微苦"), "type": "HAS_FLAVOR", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Meridian", "脾经"), "type": "ENTERS_MERIDIAN", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Meridian", "肺经"), "type": "ENTERS_MERIDIAN", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "人参"), "to": ("Meridian", "心经"), "type": "ENTERS_MERIDIAN", "props": {"status": "verified", "dataset": DATASET_TAG}},

    {"from": ("Herb", "黄芪"), "to": ("Component", "黄芪甲苷"), "type": "CONTAINS", "props": {"status": "verified", "quantity": "皂苷类成分", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Component", "黄芪多糖"), "type": "CONTAINS", "props": {"status": "verified", "quantity": "多糖活性组分", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Efficacy", "补气升阳"), "type": "HAS_EFFICACY", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Efficacy", "固表止汗"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Efficacy", "利水消肿"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Efficacy", "托毒生肌"), "type": "HAS_EFFICACY", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Flavor", "甘"), "type": "HAS_FLAVOR", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Flavor", "微温"), "type": "HAS_FLAVOR", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Meridian", "脾经"), "type": "ENTERS_MERIDIAN", "props": {"status": "verified", "dataset": DATASET_TAG}},
    {"from": ("Herb", "黄芪"), "to": ("Meridian", "肺经"), "type": "ENTERS_MERIDIAN", "props": {"status": "verified", "dataset": DATASET_TAG}},

    {"from": ("Herb", "陈皮"), "to": ("Component", "挥发油"), "type": "CONTAINS", "props": {"status": "pending", "quantity": "约1-2%", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Component", "橙皮苷"), "type": "CONTAINS", "props": {"status": "pending", "quantity": "约5-10%", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Component", "陈皮素"), "type": "CONTAINS", "props": {"status": "pending", "quantity": "约2-3%", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Efficacy", "理气健脾"), "type": "HAS_EFFICACY", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Efficacy", "燥湿化痰"), "type": "HAS_EFFICACY", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Flavor", "辛"), "type": "HAS_FLAVOR", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Flavor", "苦"), "type": "HAS_FLAVOR", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Meridian", "脾经"), "type": "ENTERS_MERIDIAN", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Meridian", "肺经"), "type": "ENTERS_MERIDIAN", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Variant", "大红皮"), "type": "HAS_VARIANT", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Variant", "二红皮"), "type": "HAS_VARIANT", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Variant", "大红皮"), "to": ("Herb", "陈皮"), "type": "VARIANT_OF", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Variant", "二红皮"), "to": ("Herb", "陈皮"), "type": "VARIANT_OF", "props": {"status": "pending", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Process", "晒干陈化"), "type": "PROCESSED_BY", "props": {"status": "pending", "duration": "3年以上", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Trait", "油室"), "type": "HAS_TRAIT", "props": {"status": "pending", "value": "明显", "observation": "肉眼可见凹入油点", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("Trait", "外皮棕红"), "type": "HAS_TRAIT", "props": {"status": "pending", "value": "棕红或红黄", "observation": "外表面色泽清晰", "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("TimePoint", "3年"), "type": "STORED_FOR", "props": {"status": "pending", "years": 3, "dataset": DATASET_TAG}},
    {"from": ("Herb", "陈皮"), "to": ("TimePoint", "5年"), "type": "STORED_FOR", "props": {"status": "pending", "years": 5, "dataset": DATASET_TAG}},
]


async def upsert_model(session, model, payload):
    instance = await session.get(model, payload["id"])
    if instance is None:
        instance = model(**payload)
        session.add(instance)
        return

    for key, value in payload.items():
        setattr(instance, key, value)


async def seed_postgres():
    await init_db()
    async with AsyncSessionLocal() as session:
        for payload in USERS:
            await upsert_model(session, UserModel, payload)

        for payload in SOURCES:
            await upsert_model(session, SourceModel, payload)

        for payload in HERBS:
            await upsert_model(session, HerbModel, payload)

        for payload in VERIFICATIONS:
            await upsert_model(session, VerificationModel, payload)

        for payload in VERIFICATION_EVIDENCES:
            await upsert_model(session, VerificationEvidenceModel, payload)

        await session.commit()


async def seed_neo4j():
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        async with driver.session() as session:
            for node in GRAPH_NODES:
                query = f"""
                MERGE (n:{node['label']} {{name: $name}})
                SET n += $props
                RETURN n
                """
                await session.run(query, name=node["name"], props={"name": node["name"], **node["props"]})

            for edge in GRAPH_EDGES:
                from_label, from_name = edge["from"]
                to_label, to_name = edge["to"]
                query = f"""
                MATCH (a:{from_label} {{name: $from_name}})
                MATCH (b:{to_label} {{name: $to_name}})
                MERGE (a)-[r:{edge['type']}]->(b)
                SET r += $props
                RETURN r
                """
                await session.run(
                    query,
                    from_name=from_name,
                    to_name=to_name,
                    props=edge["props"],
                )
    finally:
        await driver.close()


async def main():
    await seed_postgres()
    await seed_neo4j()
    print("Demo data seeded for PostgreSQL and Neo4j.")


if __name__ == "__main__":
    asyncio.run(main())
