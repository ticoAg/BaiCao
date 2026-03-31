from typing import Any

from knowledge_model.constants import parse_node_type

from .db import cypher_rows, cypher_single


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
CALL db.relationshipTypes() YIELD relationshipType
WITH relationshipType AS rel_type
OPTIONAL MATCH ()-[r]->() WHERE type(r) = rel_type
WITH rel_type, count(r) AS rel_count, collect(DISTINCT keys(r)) AS all_keys
RETURN
    rel_type AS name,
    rel_count AS count,
    reduce(acc = [], ks IN all_keys | acc + ks) AS property_keys
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

INDEXES_QUERY = """
SHOW INDEXES
YIELD name, type, entityType, labelsOrTypes, properties, state
RETURN
    name,
    type,
    entityType,
    labelsOrTypes,
    properties,
    state
"""

CONSTRAINTS_QUERY = """
SHOW CONSTRAINTS
YIELD name, type, entityType, labelsOrTypes, properties
RETURN
    name,
    type,
    entityType,
    labelsOrTypes,
    properties
"""

LEGACY_INDEXES_QUERY = """
CALL db.indexes()
YIELD name, type, entityType, labelsOrTypes, properties, state
RETURN
    name,
    type,
    entityType,
    labelsOrTypes,
    properties,
    state
"""

LEGACY_CONSTRAINTS_QUERY = """
CALL db.constraints()
YIELD name, type, entityType, labelsOrTypes, properties
RETURN
    name,
    type,
    entityType,
    labelsOrTypes,
    properties
"""


class GraphMetadataService:
    def __init__(self) -> None:
        self.driver: Any | None = None

    async def _query_rows(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if self.driver:
            async with self.driver.session() as session:
                result = await session.run(query, **(params or {}))
                return await result.data()
        return await cypher_rows(query, params)

    async def _query_single(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if self.driver:
            async with self.driver.session() as session:
                result = await session.run(query, **(params or {}))
                return await result.single()
        return await cypher_single(query, params)

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
            "labels_or_types": self._localize_label_list(
                item.get("labelsOrTypes") or item.get("labels_or_types") or []
            ),
            "properties": item.get("properties") or [],
            "state": item.get("state"),
        }

    def _localize_label_value(self, label: Any) -> str:
        try:
            return parse_node_type(str(label)).value
        except ValueError:
            return str(label)

    def _localize_label_list(self, labels: list[Any]) -> list[str]:
        return [self._localize_label_value(label) for label in labels]

    async def get_summary(self) -> dict[str, Any]:
        rows = await self._query_rows(SUMMARY_QUERY)
        named = self._extract_named_rows(rows)
        labels = named.get("labels") or []
        rel_types = named.get("relationshipTypes") or []
        property_keys = named.get("propertyKeys") or []
        indexes = named.get("indexes")
        constraints = named.get("constraints")
        if indexes is None or constraints is None:
            schema = await self.get_schema()
            indexes = schema["indexes"]
            constraints = schema["constraints"]

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
        items = await self._query_rows(LABELS_QUERY, {"offset": offset, "limit": limit})
        total_record = await self._query_single(LABELS_TOTAL_QUERY)

        normalized_items = [
            {
                "name": self._localize_label_value(item["name"]),
                "count": item["count"],
                "property_keys": sorted(set(item.get("property_keys") or [])),
            }
            for item in items
            if not q or q.lower() in self._localize_label_value(item["name"]).lower()
        ]
        total = total_record["total"] if total_record else len(normalized_items)
        return {"items": normalized_items, "total": total}

    async def list_relationship_types(
        self,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        items = await self._query_rows(
            RELATIONSHIP_TYPES_QUERY,
            {"offset": offset, "limit": limit},
        )
        total_record = await self._query_single(RELATIONSHIP_TYPES_TOTAL_QUERY)

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
        items = await self._query_rows(PROPERTY_KEYS_QUERY, {"offset": offset, "limit": limit})
        total_record = await self._query_single(PROPERTY_KEYS_TOTAL_QUERY)

        normalized_items = []
        for item in items:
            if q and q.lower() not in item["name"].lower():
                continue
            normalized_items.append(
                {
                    "name": item["name"],
                    "used_by_labels": sorted(
                        set(self._localize_label_list(item.get("used_by_labels") or []))
                    ),
                    "used_by_relationship_types": sorted(
                        set(item.get("used_by_relationship_types") or [])
                    ),
                }
            )

        total = total_record["total"] if total_record else len(normalized_items)
        return {"items": normalized_items, "total": total}

    async def get_schema(self) -> dict[str, Any]:
        try:
            indexes_rows = await self._query_rows(INDEXES_QUERY)
            constraints_rows = await self._query_rows(CONSTRAINTS_QUERY)
        except Exception:
            indexes_rows = await self._query_rows(LEGACY_INDEXES_QUERY)
            constraints_rows = await self._query_rows(LEGACY_CONSTRAINTS_QUERY)

        indexes = [self._normalize_schema_item(item) for item in indexes_rows]
        constraints = [self._normalize_schema_item(item) for item in constraints_rows]
        return {"indexes": indexes, "constraints": constraints}


graph_metadata_service = GraphMetadataService()
