from typing import Any

from neo4j import AsyncGraphDatabase

from ..core.config import get_settings

settings = get_settings()


SUMMARY_QUERY = """
CALL db.labels() YIELD label
RETURN {name:'labels', data: collect(label)} AS result
UNION ALL
CALL db.relationshipTypes() YIELD relationshipType
RETURN {name:'relationshipTypes', data: collect(relationshipType)} AS result
UNION ALL
CALL db.propertyKeys() YIELD propertyKey
RETURN {name:'propertyKeys', data: collect(propertyKey)} AS result
UNION ALL
MATCH (n)
RETURN {name:'nodes', data: count(n)} AS result
UNION ALL
MATCH ()-[r]->()
RETURN {name:'relationships', data: count(r)} AS result
UNION ALL
CALL db.indexes() YIELD name
RETURN {name:'indexes', data: collect({name: name})} AS result
UNION ALL
CALL db.constraints() YIELD name
RETURN {name:'constraints', data: collect({name: name})} AS result
"""

LABELS_QUERY = """
MATCH (n)
UNWIND labels(n) AS label
UNWIND CASE WHEN size(keys(n)) = 0 THEN [null] ELSE keys(n) END AS property_key
WITH label, count(DISTINCT n) AS node_count, collect(DISTINCT property_key) AS property_keys
RETURN
    label AS name,
    node_count AS count,
    [item IN property_keys WHERE item IS NOT NULL] AS property_keys
ORDER BY name
SKIP $offset
LIMIT $limit
"""

LABELS_TOTAL_QUERY = """
CALL db.labels() YIELD label
RETURN count(label) AS total
"""

RELATIONSHIP_TYPES_QUERY = """
MATCH ()-[r]->()
WITH type(r) AS rel_type, collect(DISTINCT key IN keys(r) | key) AS nested_keys, count(r) AS rel_count
RETURN
    rel_type AS name,
    rel_count AS count,
    reduce(acc = [], keys IN nested_keys | acc + keys) AS property_keys
ORDER BY name
SKIP $offset
LIMIT $limit
"""

RELATIONSHIP_TYPES_TOTAL_QUERY = """
CALL db.relationshipTypes() YIELD relationshipType
RETURN count(relationshipType) AS total
"""

PROPERTY_KEYS_QUERY = """
CALL db.propertyKeys() YIELD propertyKey
WITH propertyKey
OPTIONAL MATCH (n)
WHERE propertyKey IN keys(n)
WITH propertyKey, collect(DISTINCT head(labels(n))) AS used_by_labels
OPTIONAL MATCH ()-[r]->()
WHERE propertyKey IN keys(r)
RETURN
    propertyKey AS name,
    [item IN used_by_labels WHERE item IS NOT NULL] AS used_by_labels,
    collect(DISTINCT type(r)) AS used_by_relationship_types
ORDER BY name
SKIP $offset
LIMIT $limit
"""

PROPERTY_KEYS_TOTAL_QUERY = """
CALL db.propertyKeys() YIELD propertyKey
RETURN count(propertyKey) AS total
"""

SCHEMA_QUERY = """
CALL db.indexes() YIELD name, type, entityType, labelsOrTypes, properties, state
RETURN {name:'indexes', data: collect({
    name: name,
    type: type,
    entityType: entityType,
    labelsOrTypes: labelsOrTypes,
    properties: properties,
    state: state
})} AS result
UNION ALL
CALL db.constraints() YIELD name, type, entityType, labelsOrTypes, properties
RETURN {name:'constraints', data: collect({
    name: name,
    type: type,
    entityType: entityType,
    labelsOrTypes: labelsOrTypes,
    properties: properties
})} AS result
"""


class GraphMetadataService:
    def __init__(self) -> None:
        self.driver: Any | None = None

    async def connect(self) -> None:
        if not self.driver:
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )

    async def ensure_connected(self) -> None:
        if not self.driver:
            await self.connect()

    async def close(self) -> None:
        if self.driver:
            await self.driver.close()
            self.driver = None

    def _extract_named_rows(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        named: dict[str, Any] = {}
        for row in rows:
            result = row.get("result") or {}
            name = result.get("name")
            if name:
                named[name] = result.get("data")
        return named

    def _normalize_schema_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": item.get("name"),
            "type": item.get("type"),
            "entity_type": item.get("entityType") or item.get("entity_type"),
            "labels_or_types": item.get("labelsOrTypes") or item.get("labels_or_types") or [],
            "properties": item.get("properties") or [],
            "state": item.get("state"),
        }

    async def get_summary(self) -> dict[str, Any]:
        await self.ensure_connected()
        async with self.driver.session() as session:
            rows = await (await session.run(SUMMARY_QUERY)).data()

        named = self._extract_named_rows(rows)
        labels = named.get("labels") or []
        rel_types = named.get("relationshipTypes") or []
        property_keys = named.get("propertyKeys") or []
        indexes = named.get("indexes") or []
        constraints = named.get("constraints") or []

        return {
            "node_count": named.get("nodes") or 0,
            "relationship_count": named.get("relationships") or 0,
            "label_count": len(labels),
            "relationship_type_count": len(rel_types),
            "property_key_count": len(property_keys),
            "index_count": len(indexes),
            "constraint_count": len(constraints),
            "truncated": False,
            "generated_at": "2026-03-23T10:00:00Z",
        }

    async def list_labels(self, q: str | None = None, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        await self.ensure_connected()
        async with self.driver.session() as session:
            items = await (await session.run(LABELS_QUERY, offset=offset, limit=limit)).data()
            total_record = await (await session.run(LABELS_TOTAL_QUERY)).single()

        normalized_items = [
            {
                "name": item["name"],
                "count": item["count"],
                "property_keys": sorted(set(item.get("property_keys") or [])),
            }
            for item in items
            if not q or q.lower() in item["name"].lower()
        ]
        total = total_record["total"] if total_record else len(normalized_items)
        return {"items": normalized_items, "total": total}

    async def list_relationship_types(
        self,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        await self.ensure_connected()
        async with self.driver.session() as session:
            items = await (
                await session.run(RELATIONSHIP_TYPES_QUERY, offset=offset, limit=limit)
            ).data()
            total_record = await (await session.run(RELATIONSHIP_TYPES_TOTAL_QUERY)).single()

        normalized_items = []
        for item in items:
            if q and q.lower() not in item["name"].lower():
                continue
            normalized_items.append(
                {
                    "name": item["name"],
                    "count": item["count"],
                    "property_keys": sorted(set(item.get("property_keys") or [])),
                }
            )

        total = total_record["total"] if total_record else len(normalized_items)
        return {"items": normalized_items, "total": total}

    async def list_property_keys(
        self,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        await self.ensure_connected()
        async with self.driver.session() as session:
            items = await (
                await session.run(PROPERTY_KEYS_QUERY, offset=offset, limit=limit)
            ).data()
            total_record = await (await session.run(PROPERTY_KEYS_TOTAL_QUERY)).single()

        normalized_items = []
        for item in items:
            if q and q.lower() not in item["name"].lower():
                continue
            normalized_items.append(
                {
                    "name": item["name"],
                    "used_by_labels": sorted(set(item.get("used_by_labels") or [])),
                    "used_by_relationship_types": sorted(
                        set(item.get("used_by_relationship_types") or [])
                    ),
                }
            )

        total = total_record["total"] if total_record else len(normalized_items)
        return {"items": normalized_items, "total": total}

    async def get_schema(self) -> dict[str, Any]:
        await self.ensure_connected()
        async with self.driver.session() as session:
            rows = await (await session.run(SCHEMA_QUERY)).data()

        named = self._extract_named_rows(rows)
        indexes = [self._normalize_schema_item(item) for item in named.get("indexes") or []]
        constraints = [
            self._normalize_schema_item(item) for item in named.get("constraints") or []
        ]
        return {"indexes": indexes, "constraints": constraints}


graph_metadata_service = GraphMetadataService()
