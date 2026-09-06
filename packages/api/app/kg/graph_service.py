# Knowledge Graph Service using Neo4j
# 完整数据模型支持：药材-成分-品种-工艺-性状

from typing import Optional, Any, Dict, List
from uuid import uuid4 as uuid_module_uuid4

from ..models.enums import (
    NodeType,
    NodeStatus,
    EdgeType,
    HerbType,
    TraitCategory,
)
from knowledge_model.constants import parse_node_type, to_neo4j_label
from knowledge_model.graph_i18n import (
    PROPERTY_ZH_TO_EN,
    delocalize_status,
    localize_status,
    to_graph_properties,
    zh_property,
)
from ..schemas.graph import GRAPH_QUERY_PROPERTY_KEYS
from .db import cypher_rows, cypher_single
from .models import NODE_MODEL_MAP, REL_TYPE_TO_ATTR

QUERY_LABEL_DISPLAY = {node_type.value: node_type.value for node_type in NodeType}
QUERY_REL_TYPE_DISPLAY = {edge_type.value: edge_type.value for edge_type in EdgeType}
QUERY_STATUS_DISPLAY = {
    NodeStatus.PENDING.value: "待验证",
    NodeStatus.VERIFIED.value: "已验证",
    NodeStatus.REJECTED.value: "已拒绝",
}
QUERY_PROPERTY_DISPLAY = {
    "latin_name": "拉丁名",
    "category": "分类",
    "description": "描述",
    "chemical_formula": "化学式",
    "parent_herb": "母本药材",
    "min_duration": "最短时长",
    "conditions": "条件",
    "trait_category": "性状分类",
    "years": "年份",
    "quality_indicator": "质量指标",
    "nature": "药性",
    "tcm_type": "中医类型",
    "type": "类型",
}
ALLOWED_QUERY_REL_TYPES = {edge_type.value for edge_type in EdgeType}
ALLOWED_QUERY_PROPERTY_KEYS = set(GRAPH_QUERY_PROPERTY_KEYS)


# ============ Cypher Query Constants ============

QUERY_CREATE_NODE = """
CREATE (n:{label} $props) RETURN n
"""

QUERY_GET_NODE_BY_ID = """
MATCH (n) WHERE n.标识 = $node_id
RETURN n, labels(n) as labels
"""

QUERY_GET_NODE_BY_NAME = """
MATCH (n:{label} {{名称: $name}})
RETURN n, labels(n) as labels
"""

QUERY_CREATE_RELATIONSHIP = """
MATCH (a {{名称: $from_name}})
MATCH (b {{名称: $to_name}})
CREATE (a)-[r:{rel_type}]->(b)
SET r = $props
RETURN r
"""

QUERY_VERIFY_NODE = """
MATCH (n)
WHERE n.标识 = $node_id
SET n.状态 = $status,
    n.验证标识 = $verification_id,
    n.验证人 = $verifier_id,
    n.验证时间 = datetime()
RETURN n
"""

QUERY_VERIFY_RELATIONSHIP = """
MATCH (from)-[r:{rel_type}]->(to)
WHERE from.名称 = $from_name AND to.名称 = $to_name
SET r.状态 = $status,
    r.验证标识 = $verification_id,
    r.验证人 = $verifier_id,
    r.验证时间 = datetime()
RETURN r
"""

QUERY_EXPAND_QUERY_FRONTIER = """
MATCH (current)-[r]-(connected)
WHERE current.标识 IN $frontier_ids
RETURN
    connected {.*, labels: labels(connected)} AS connected_node,
    {
        id: coalesce(r.标识, elementId(r)),
        rel_type: type(r),
        status: coalesce(r.状态, '待验证'),
        verification_id: r.验证标识,
        verified_by: r.验证人,
        verified_at: toString(r.验证时间),
        source: {
            id: startNode(r).标识,
            name: startNode(r).名称,
            source: startNode(r).来源,
            status: startNode(r).状态,
            labels: labels(startNode(r))
        },
        target: {
            id: endNode(r).标识,
            name: endNode(r).名称,
            source: endNode(r).来源,
            status: endNode(r).状态,
            labels: labels(endNode(r))
        }
    } AS edge
LIMIT $hop_limit
"""

class GraphService:
    """Neo4j 图谱服务 - 支持多维度数据模型"""

    def __init__(self) -> None:
        self.driver: Optional[Any] = None

    async def close(self) -> None:
        if self.driver is not None and hasattr(self.driver, "close"):
            await self.driver.close()
        self.driver = None

    # ============ Helper Methods ============

    async def _query_rows(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self.driver:
            async with self.driver.session() as session:
                result = await session.run(query, **(params or {}))
                return await result.data()
        return await cypher_rows(query, params)

    async def _query_single(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any] | None:
        if self.driver:
            async with self.driver.session() as session:
                result = await session.run(query, **(params or {}))
                return await result.single()
        return await cypher_single(query, params)

    def _map_node_to_dict(self, node: Any, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Map Neo4j node to dictionary with optional labels"""
        result = dict(node)
        for zh_key, en_key in PROPERTY_ZH_TO_EN.items():
            if zh_key in result and en_key not in result:
                result[en_key] = result[zh_key]
        if "status" in result:
            result["status"] = delocalize_status(result["status"])
        if labels is not None:
            result["labels"] = self._localize_label_list(labels)
        elif "labels" in result and isinstance(result["labels"], list):
            result["labels"] = self._localize_label_list(result["labels"])
        return result

    def _map_relationship_to_dict(self, rel: Any) -> Dict[str, Any]:
        """Map Neo4j relationship to dictionary"""
        if hasattr(rel, "__properties__"):
            return dict(rel.__properties__)
        return dict(rel)

    def _default_relationship_props(
        self,
        extra_props: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        props: Dict[str, Any] = {
            "status": NodeStatus.PENDING.value,
            "verification_id": None,
            "verified_by": None,
            "verified_at": None,
        }
        if extra_props:
            props.update(extra_props)
        return to_graph_properties(props)

    def _clean_properties(self, props: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in props.items() if value is not None}

    def _map_connected_relationship(
        self,
        rel: Any,
        rel_type: str,
    ) -> Dict[str, Any]:
        mapped = self._map_relationship_to_dict(rel) if rel is not None else {}
        mapped.setdefault("type", rel_type)
        return mapped

    def _localize_label_value(self, label: Any) -> str:
        try:
            return parse_node_type(str(label)).value
        except ValueError:
            return str(label)

    def _localize_label_list(self, labels: List[Any]) -> List[str]:
        return [self._localize_label_value(label) for label in labels]

    def _localize_edge_payload(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        localized = dict(edge)
        if "status" in localized:
            localized["status"] = delocalize_status(localized.get("status"))
        for endpoint in ("source", "target"):
            node_ref = localized.get(endpoint)
            if isinstance(node_ref, dict):
                mapped = self._map_node_to_dict(node_ref)
                if "status" in mapped:
                    mapped["status"] = delocalize_status(mapped.get("status"))
                localized[endpoint] = mapped
        return localized

    def _normalize_query_label(self, label: Any) -> str | None:
        value = self._query_value(label)
        if value in (None, ""):
            return None
        try:
            return to_neo4j_label(str(value))
        except ValueError:
            return None

    def _display_query_label(self, label: Any) -> str | None:
        value = self._query_value(label)
        if value in (None, ""):
            return None
        try:
            return parse_node_type(str(value)).value
        except ValueError:
            return None

    async def get_relationships(
        self,
        node_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = """
        MATCH (n {标识: $node_id})-[r]-(connected)
        WHERE $status IS NULL OR r.状态 = $status
        RETURN {
            id: coalesce(r.标识, elementId(r)),
            rel_type: type(r),
            status: coalesce(r.状态, '待验证'),
            verification_id: r.验证标识,
            verified_by: r.验证人,
            verified_at: toString(r.验证时间),
            source: {
                id: startNode(r).标识,
                name: startNode(r).名称,
                source: startNode(r).来源,
                status: startNode(r).状态,
                labels: labels(startNode(r))
            },
            target: {
                id: endNode(r).标识,
                name: endNode(r).名称,
                source: endNode(r).来源,
                status: endNode(r).状态,
                labels: labels(endNode(r))
            }
        } AS edge
        """
        rows = await self._query_rows(query, {"node_id": node_id, "status": status})
        return self._dedupe_edges(
            [self._localize_edge_payload(row["edge"]) for row in rows if row.get("edge")]
        )

    def _record_value(self, record: Any, key: str) -> Any:
        """Safely read a Neo4j record-like object by key."""
        try:
            return record[key]
        except (KeyError, TypeError):
            return None

    def _dedupe_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: Dict[str, Dict[str, Any]] = {}
        for node in nodes:
            if not node:
                continue
            node_key = str(node.get("id") or node.get("标识") or node.get("name") or node.get("名称"))
            deduped[node_key] = node
        return list(deduped.values())

    def _dedupe_edges(self, edges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        deduped: Dict[tuple[str, str, str], Dict[str, Any]] = {}
        for edge in edges:
            if not edge:
                continue
            source = edge.get("source") or {}
            target = edge.get("target") or {}
            edge_key = (
                str(source.get("id") or source.get("name")),
                str(edge.get("rel_type") or edge.get("type") or ""),
                str(target.get("id") or target.get("name")),
            )
            deduped[edge_key] = edge
        return list(deduped.values())

    def _query_value(self, value: Any) -> Any:
        """Normalize enum-like filter values to plain strings."""
        return getattr(value, "value", value)

    def _edge_key(self, edge: Dict[str, Any]) -> tuple[str, str, str]:
        """Build a stable dedupe key for an edge payload."""
        source = edge.get("source") or {}
        target = edge.get("target") or {}
        return (
            str(source.get("id") or source.get("name")),
            str(edge.get("rel_type") or edge.get("type") or ""),
            str(target.get("id") or target.get("name")),
        )

    def _normalize_query_payload(self, payload: Any) -> Dict[str, Any]:
        """Accept dict or Pydantic payload and normalize for query building."""
        if hasattr(payload, "model_dump"):
            raw_payload = payload.model_dump(mode="python")
        else:
            raw_payload = dict(payload or {})

        depth = int(raw_payload.get("depth", 1))
        limit = int(raw_payload.get("limit", 20))
        return {
            "node": dict(raw_payload.get("node") or {}),
            "edge": dict(raw_payload.get("edge") or {}),
            "depth": max(1, min(depth, 6)),
            "limit": max(1, min(limit, 100)),
        }

    def _build_scene_info(
        self,
        *,
        truncated: bool = False,
        node_limit_hit: bool = False,
        relationship_limit_hit: bool = False,
        info_message: str | None = None,
    ) -> Dict[str, Any]:
        return {
            "truncated": truncated,
            "node_limit_hit": node_limit_hit,
            "relationship_limit_hit": relationship_limit_hit,
            "info_message": info_message,
        }

    def _build_active_filters(
        self,
        node_filters: Dict[str, Any],
        edge_filters: Dict[str, Any],
    ) -> List[str]:
        """Build Chinese summary strings for currently active filters."""
        active_filters: List[str] = []
        name_contains = node_filters.get("name_contains")
        if name_contains:
            active_filters.append(f"名称包含: {name_contains}")

        label = self._display_query_label(node_filters.get("label"))
        if label:
            active_filters.append(f"节点类型: {QUERY_LABEL_DISPLAY.get(label, label)}")

        node_status = self._query_value(node_filters.get("status"))
        if node_status in QUERY_STATUS_DISPLAY:
            active_filters.append(f"节点状态: {QUERY_STATUS_DISPLAY[node_status]}")

        source_contains = node_filters.get("source_contains")
        if source_contains:
            active_filters.append(f"来源包含: {source_contains}")

        property_key = self._query_value(node_filters.get("property_key"))
        property_value = node_filters.get("property_value_contains")
        if property_key in ALLOWED_QUERY_PROPERTY_KEYS:
            property_label = QUERY_PROPERTY_DISPLAY.get(property_key, property_key)
            if property_value:
                active_filters.append(f"{property_label}包含: {property_value}")
            else:
                active_filters.append(f"存在属性: {property_label}")

        rel_type = self._query_value(edge_filters.get("rel_type"))
        if rel_type in ALLOWED_QUERY_REL_TYPES:
            active_filters.append(f"关系类型: {QUERY_REL_TYPE_DISPLAY.get(rel_type, rel_type)}")

        edge_status = self._query_value(edge_filters.get("status"))
        if edge_status in QUERY_STATUS_DISPLAY:
            active_filters.append(f"关系状态: {QUERY_STATUS_DISPLAY[edge_status]}")

        connected_name = edge_filters.get("connected_name_contains")
        if connected_name:
            active_filters.append(f"关联节点名称包含: {connected_name}")

        return active_filters

    def _build_seed_query(
        self,
        node_filters: Dict[str, Any],
        edge_filters: Dict[str, Any],
        limit: int,
    ) -> tuple[str, Dict[str, Any]]:
        """Build the bounded first-stage seed-node query."""
        normalized_label = self._normalize_query_label(node_filters.get("label"))
        label_clause = f":{normalized_label}" if normalized_label else ""
        params: Dict[str, Any] = {"seed_limit": limit + 1}
        where_clauses: List[str] = []

        name_contains = node_filters.get("name_contains")
        if name_contains:
            where_clauses.append("n.名称 CONTAINS $name_contains")
            params["name_contains"] = name_contains

        node_status = self._query_value(node_filters.get("status"))
        if node_status in QUERY_STATUS_DISPLAY:
            where_clauses.append("n.状态 = $node_status")
            params["node_status"] = localize_status(node_status)

        source_contains = node_filters.get("source_contains")
        if source_contains:
            where_clauses.append("coalesce(n.来源, '') CONTAINS $node_source_contains")
            params["node_source_contains"] = source_contains

        property_key = self._query_value(node_filters.get("property_key"))
        property_value = node_filters.get("property_value_contains")
        if property_key in ALLOWED_QUERY_PROPERTY_KEYS:
            stored_key = zh_property(property_key)
            where_clauses.append(f"n.`{stored_key}` IS NOT NULL")
            if property_value:
                where_clauses.append(f"toString(n.`{stored_key}`) CONTAINS $property_value_contains")
                params["property_value_contains"] = property_value

        rel_type = self._query_value(edge_filters.get("rel_type"))
        rel_clause = f":{rel_type}" if rel_type in ALLOWED_QUERY_REL_TYPES else ""
        edge_where_clauses: List[str] = []

        edge_status = self._query_value(edge_filters.get("status"))
        if edge_status in QUERY_STATUS_DISPLAY:
            edge_where_clauses.append("r.状态 = $edge_status")
            params["edge_status"] = localize_status(edge_status)

        connected_name = edge_filters.get("connected_name_contains")
        if connected_name:
            edge_where_clauses.append("connected.名称 CONTAINS $connected_name_contains")
            params["connected_name_contains"] = connected_name

        if rel_clause or edge_where_clauses:
            edge_where_sql = ""
            if edge_where_clauses:
                edge_where_sql = f"\n              WHERE {' AND '.join(edge_where_clauses)}"
            where_clauses.append(
                f"""EXISTS {{
              MATCH (n)-[r{rel_clause}]-(connected){edge_where_sql}
            }}"""
            )

        where_sql = ""
        if where_clauses:
            where_sql = f"\n        WHERE {' AND '.join(where_clauses)}"

        query = f"""
        MATCH (n{label_clause}){where_sql}
        RETURN n {{.*, labels: labels(n)}} AS node
        ORDER BY n.名称
        LIMIT $seed_limit
        """
        return query, params

    def _build_expand_query(self, edge_filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """Build the one-hop expansion query plus bound parameters."""
        rel_type = self._query_value(edge_filters.get("rel_type"))
        rel_clause = f":{rel_type}" if rel_type in ALLOWED_QUERY_REL_TYPES else ""
        where_clauses = ["current.标识 IN $frontier_ids"]
        params: Dict[str, Any] = {}

        edge_status = self._query_value(edge_filters.get("status"))
        if edge_status in QUERY_STATUS_DISPLAY:
            where_clauses.append("r.状态 = $edge_status")
            params["edge_status"] = localize_status(edge_status)

        connected_name = edge_filters.get("connected_name_contains")
        if connected_name:
            where_clauses.append("connected.名称 CONTAINS $connected_name_contains")
            params["connected_name_contains"] = connected_name

        query = QUERY_EXPAND_QUERY_FRONTIER.replace(
            "MATCH (current)-[r]-(connected)\nWHERE current.标识 IN $frontier_ids",
            f"MATCH (current)-[r{rel_clause}]-(connected)\nWHERE {' AND '.join(where_clauses)}",
        )
        return query, params

    def _edge_matches_filters(
        self,
        edge: Dict[str, Any],
        connected_node: Optional[Dict[str, Any]],
        edge_filters: Dict[str, Any],
    ) -> bool:
        """Apply edge filters defensively to expansion results."""
        rel_type = self._query_value(edge_filters.get("rel_type"))
        if rel_type in ALLOWED_QUERY_REL_TYPES and edge.get("rel_type") != rel_type:
            return False

        edge_status = self._query_value(edge_filters.get("status"))
        if edge_status in QUERY_STATUS_DISPLAY and edge.get("status") != edge_status:
            return False

        connected_name = edge_filters.get("connected_name_contains")
        if connected_name and not connected_node:
            return False
        if connected_name and connected_node:
            connected_name_value = connected_node.get("name") or ""
            if connected_name not in connected_name_value:
                return False

        return True

    async def _expand_query_subgraph(
        self,
        session: Any,
        seed_node_ids: List[str],
        depth: int,
        limit: int,
        edge_filters: Dict[str, Any],
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Expand from seed nodes one hop at a time, avoiding dynamic Cypher ranges."""
        frontier_ids = list(seed_node_ids)
        seen_node_ids = set(seed_node_ids)
        seen_edge_keys = set()
        collected_nodes: List[Dict[str, Any]] = []
        collected_edges: List[Dict[str, Any]] = []
        max_graph_nodes = max(limit * max(depth, 1), len(seed_node_ids))
        max_graph_edges = limit * max(depth, 1)
        remaining_node_budget = max(max_graph_nodes - len(seed_node_ids), 0)
        remaining_edge_budget = max_graph_edges
        expand_query, expand_params = self._build_expand_query(edge_filters)

        for _ in range(depth):
            if not frontier_ids or remaining_node_budget <= 0 or remaining_edge_budget <= 0:
                break

            hop_limit = min(remaining_node_budget, remaining_edge_budget)
            if hop_limit <= 0:
                break

            if session is not None:
                result = await session.run(
                    expand_query,
                    frontier_ids=frontier_ids,
                    hop_limit=hop_limit,
                    **expand_params,
                )
                rows = (await result.data())[:hop_limit]
            else:
                rows = (
                    await self._query_rows(
                        expand_query,
                        {
                            "frontier_ids": frontier_ids,
                            "hop_limit": hop_limit,
                            **expand_params,
                        },
                    )
                )[:hop_limit]
            next_frontier: List[str] = []

            for row in rows:
                edge = row.get("edge")
                connected_node = row.get("connected_node")
                if not edge or not self._edge_matches_filters(edge, connected_node, edge_filters):
                    continue

                if isinstance(edge, dict):
                    edge = self._localize_edge_payload(edge)
                if isinstance(connected_node, dict):
                    connected_node = self._map_node_to_dict(connected_node)

                edge_key = self._edge_key(edge)
                if edge_key not in seen_edge_keys and remaining_edge_budget > 0:
                    collected_edges.append(edge)
                    seen_edge_keys.add(edge_key)
                    remaining_edge_budget -= 1

                if connected_node and connected_node.get("id") not in seen_node_ids and remaining_node_budget > 0:
                    connected_id = connected_node["id"]
                    seen_node_ids.add(connected_id)
                    collected_nodes.append(connected_node)
                    next_frontier.append(connected_id)
                    remaining_node_budget -= 1

            frontier_ids = next_frontier

        return self._dedupe_nodes(collected_nodes), self._dedupe_edges(collected_edges)

    # ============ 基础节点操作 ============

    async def create_node(
        self,
        label: str,
        name: str,
        source: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建任意类型节点（默认 status=pending）"""
        node_id = str(uuid_module_uuid4())
        props: Dict[str, Any] = dict(properties or {})
        props.setdefault("id", node_id)
        props.setdefault("name", name)
        props.setdefault("source", source)
        props.setdefault("status", NodeStatus.PENDING.value)
        props.setdefault("verification_id", None)
        props.setdefault("verified_by", None)
        props.setdefault("verified_at", None)
        stored = to_graph_properties(props)

        query = QUERY_CREATE_NODE.format(label=to_neo4j_label(label))
        record = await self._query_single(query, {"props": stored})
        if not record:
            return {}
        return self._map_node_to_dict(record["n"], [to_neo4j_label(label)])

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取节点"""
        record = await self._query_single(QUERY_GET_NODE_BY_ID, {"node_id": node_id})
        if record:
            return self._map_node_to_dict(record["n"], record["labels"])
        return None

    async def expand_node_graph(
        self,
        node_id: str,
        depth: int = 1,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """按节点 ID 扩展最多两跳邻居子图。Workbench HTTP 仍限制 depth=1；agent 可用 2 跳看证据来源。"""
        bounded_depth = max(1, min(depth, 2))
        bounded_limit = max(1, min(limit, 50))

        record = await self._query_single(QUERY_GET_NODE_BY_ID, {"node_id": node_id})
        if not record:
            return {"center": None, "nodes": [], "edges": []}

        center = self._map_node_to_dict(record["n"], record["labels"])
        expanded_nodes, edges = await self._expand_query_subgraph(
            self.driver.session() if self.driver else None,
            [node_id],
            bounded_depth,
            bounded_limit,
            {},
        )

        return {
            "center": center,
            "nodes": self._dedupe_nodes([center, *expanded_nodes]),
            "edges": edges,
        }

    async def get_node_by_name(self, name: str, label: str) -> Optional[Dict[str, Any]]:
        """根据名称和类型获取节点"""
        query = QUERY_GET_NODE_BY_NAME.format(label=to_neo4j_label(label))
        record = await self._query_single(query, {"name": name})
        if record:
            return self._map_node_to_dict(record["n"], record["labels"])
        return None

    async def create_relationship(
        self,
        from_label: str,
        from_name: str,
        to_label: str,
        to_name: str,
        rel_type: str,
        extra_props: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from_node = await NODE_MODEL_MAP[from_label].nodes.get(name=from_name)
        to_node = await NODE_MODEL_MAP[to_label].nodes.get(name=to_name)
        rel_attr = REL_TYPE_TO_ATTR[rel_type]
        rel_manager = getattr(from_node, rel_attr)
        rel = await rel_manager.connect(
            to_node,
            properties=self._clean_properties(self._default_relationship_props(extra_props)),
        )
        return self._map_connected_relationship(rel, rel_type)

    # ============ 药材操作 ============

    async def create_herb(
        self,
        name: str,
        source: str,
        herb_type: HerbType = HerbType.BASE,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建药材节点"""
        return await self.create_node("Herb", name, source, {
            "type": herb_type.value,
            "category": category
        })

    async def get_herb(self, name: str) -> Optional[Dict[str, Any]]:
        """获取药材"""
        return await self.get_node_by_name(name, "Herb")

    # ============ 成分操作 ============

    async def create_component(
        self,
        name: str,
        source: str,
        chemical_formula: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建成分节点"""
        return await self.create_node("Component", name, source, {
            "chemical_formula": chemical_formula
        })

    async def link_herb_contains_component(
        self,
        herb_name: str,
        component_name: str,
        quantity: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建药材-成分关系 (Herb)-[:包含成分]->(Component)"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Component",
            component_name,
            EdgeType.CONTAINS.value,
            {"quantity": quantity},
        )

    async def link_herb_parent(
        self,
        child_name: str,
        parent_name: str
    ) -> Dict[str, Any]:
        """创建药材-父子关系 (Child)-[:父类]->(Parent)

        表示child是parent的子类/衍生物
        """
        return await self.create_relationship(
            "Herb",
            child_name,
            "Herb",
            parent_name,
            EdgeType.PARENT_OF.value,
        )

    async def link_herb_child(
        self,
        parent_name: str,
        child_name: str
    ) -> Dict[str, Any]:
        """创建药材-子关系 (Parent)-[:子类]->(Child)

        表示parent是child的父级/来源
        """
        return await self.create_relationship(
            "Herb",
            parent_name,
            "Herb",
            child_name,
            EdgeType.CHILD_OF.value,
        )

    async def link_herb_source(
        self,
        herb_name: str,
        source_name: str
    ) -> Dict[str, Any]:
        """创建药材-来源关系 (Herb)-[:来源于]->(Source)

        表示herb来源于source（产地、供应商等）
        """
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Source",
            source_name,
            EdgeType.ORIGINATED_FROM.value,
        )

    # ============ 品种操作 ============

    async def create_variant(
        self,
        name: str,
        parent_herb: str,
        source: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建品种变种节点"""
        node = await self.create_node("Variant", name, source, {
            "parent_herb": parent_herb,
            "description": description
        })

        # 创建品种-药材关系
        await self.link_variant_of(name, parent_herb)

        return node

    async def link_variant_of(self, variant_name: str, herb_name: str) -> Dict[str, Any]:
        """创建品种-药材关系 (Variant)-[:属于药材]->(Herb)"""
        return await self.create_relationship(
            "Variant",
            variant_name,
            "Herb",
            herb_name,
            EdgeType.VARIANT_OF.value,
        )

    async def link_herb_has_variant(self, herb_name: str, variant_name: str) -> Dict[str, Any]:
        """创建药材-品种关系 (Herb)-[:具有品种]->(Variant)"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Variant",
            variant_name,
            EdgeType.HAS_VARIANT.value,
        )

    # ============ 工艺操作 ============

    async def create_process(
        self,
        name: str,
        source: str,
        description: Optional[str] = None,
        min_duration: Optional[str] = None,
        conditions: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建加工工艺节点"""
        return await self.create_node("Process", name, source, {
            "description": description,
            "min_duration": min_duration,
            "conditions": conditions
        })

    async def link_herb_processed_by(
        self,
        herb_name: str,
        process_name: str,
        duration: Optional[str] = None,
        conditions: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建药材-工艺关系 (Herb)-[:经过工艺]->(Process)"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Process",
            process_name,
            EdgeType.PROCESSED_BY.value,
            {
                "duration": duration,
                "conditions": conditions,
                "start_date": None,
                "end_date": None,
            },
        )

    # ============ 性状操作 ============

    async def create_trait(
        self,
        name: str,
        source: str,
        trait_category: TraitCategory = TraitCategory.EXTERNAL,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建性状特征节点"""
        return await self.create_node("Trait", name, source, {
            "category": trait_category.value,
            "description": description
        })

    async def link_herb_has_trait(
        self,
        herb_name: str,
        trait_name: str,
        value: str,
        observation: Optional[str] = None,
        year_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建药材-性状关系 (Herb)-[:具有性状]->(Trait)"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Trait",
            trait_name,
            EdgeType.HAS_TRAIT.value,
            {
                "value": value,
                "observation": observation,
                "year_range": year_range,
            },
        )

    # ============ 时间点操作 ============

    async def create_timepoint(
        self,
        years: int,
        source: str,
        description: Optional[str] = None,
        quality_indicator: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建时间点节点"""
        return await self.create_node("TimePoint", f"{years}年", source, {
            "years": years,
            "description": description,
            "quality_indicator": quality_indicator
        })

    async def link_herb_stored_for(
        self,
        herb_name: str,
        years: int,
        start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建药材-储存时间关系 (Herb)-[:储存时间]->(TimePoint)"""
        # 查找或创建时间点节点
        await self.create_timepoint(years, "system")
        timepoint_name = f"{years}年"
        return await self.create_relationship(
            "Herb",
            herb_name,
            "TimePoint",
            timepoint_name,
            EdgeType.STORED_FOR.value,
            {
                "years": years,
                "start_date": start_date,
                "end_date": None,
            },
        )

    # ============ 功效/性味/归经操作 ============

    async def create_efficacy(self, name: str, source: str, category: Optional[str] = None) -> Dict[str, Any]:
        """创建功效节点"""
        return await self.create_node("Efficacy", name, source, {"category": category})

    async def create_flavor(self, name: str, source: str, nature: Optional[str] = None) -> Dict[str, Any]:
        """创建性味节点"""
        return await self.create_node("Flavor", name, source, {"nature": nature})

    async def create_meridian(self, name: str, source: str) -> Dict[str, Any]:
        """创建归经节点"""
        return await self.create_node("Meridian", name, source)

    async def link_herb_has_efficacy(self, herb_name: str, efficacy_name: str) -> Dict[str, Any]:
        """创建药材-功效关系"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Efficacy",
            efficacy_name,
            EdgeType.HAS_EFFICACY.value,
        )

    async def link_herb_has_flavor(self, herb_name: str, flavor_name: str) -> Dict[str, Any]:
        """创建药材-性味关系"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Flavor",
            flavor_name,
            EdgeType.HAS_FLAVOR.value,
        )

    async def link_herb_enters_meridian(self, herb_name: str, meridian_name: str) -> Dict[str, Any]:
        """创建药材-归经关系"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Meridian",
            meridian_name,
            EdgeType.ENTERS_MERIDIAN.value,
        )

    async def create_disease(
        self, name: str, source: str, tcm_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建疾病节点"""
        return await self.create_node(
            label=to_neo4j_label(NodeType.DISEASE.value),
            name=name,
            source=source,
            properties={"tcm_type": tcm_type} if tcm_type else {},
        )

    async def link_herb_treats(self, herb_name: str, disease_name: str) -> Dict[str, Any]:
        """创建药材-主治关系 (Herb)-[:治疗病证]->(Disease)"""
        return await self.create_relationship(
            "Herb",
            herb_name,
            "Disease",
            disease_name,
            EdgeType.TREATS.value,
        )

    async def link_herb_similar(
        self, herb_name_1: str, herb_name_2: str, similarity_score: float = 0.0
    ) -> Dict[str, Any]:
        """创建药材相似关系 (Herb)-[:相似于]->(Herb)"""
        return await self.create_relationship(
            "Herb",
            herb_name_1,
            "Herb",
            herb_name_2,
            EdgeType.SIMILAR_TO.value,
            {"similarity_score": similarity_score},
        )

    # ============ 图谱查询 ============

    async def get_herb_graph(self, herb_name: str, depth: int = 1) -> Dict[str, Any]:
        """获取以药材为中心的完整图谱"""
        query = f"""
        MATCH (h:药材 {{名称: $name}})
        OPTIONAL MATCH path = (h)-[*1..{depth}]-(connected)
        WITH h, [p IN collect(path) WHERE p IS NOT NULL] AS paths
        RETURN
            h {{.*, labels: labels(h)}} AS center,
            reduce(node_maps = [], p IN paths |
                node_maps + [n IN nodes(p) | n {{.*, labels: labels(n)}}]
            ) AS nodes,
            reduce(edge_maps = [], p IN paths |
                edge_maps + [r IN relationships(p) |
                    {{
                        id: coalesce(r.标识, elementId(r)),
                        rel_type: type(r),
                        status: coalesce(r.状态, '待验证'),
                        verification_id: r.验证标识,
                        verified_by: r.验证人,
                        verified_at: toString(r.验证时间),
                        source: {{
                            id: startNode(r).标识,
                            name: startNode(r).名称,
                            source: startNode(r).来源,
                            status: startNode(r).状态,
                            labels: labels(startNode(r))
                        }},
                        target: {{
                            id: endNode(r).标识,
                            name: endNode(r).名称,
                            source: endNode(r).来源,
                            status: endNode(r).状态,
                            labels: labels(endNode(r))
                        }}
                    }}
                ]
            ) AS edges
        """

        record = await self._query_single(query, {"name": herb_name})
        center = self._record_value(record, "center") if record else None
        if center:
            nodes = self._dedupe_nodes([center, *(self._record_value(record, "nodes") or [])])
            nodes = [self._map_node_to_dict(node) for node in nodes]
            edges = self._dedupe_edges(
                [self._localize_edge_payload(edge) for edge in (self._record_value(record, "edges") or [])]
            )
            return {
                "center": self._map_node_to_dict(center),
                "nodes": nodes,
                "edges": edges,
                "scene": self._build_scene_info(),
            }

        legacy_center = self._record_value(record, "h") if record else None
        if legacy_center:
            return {
                "center": self._map_node_to_dict(legacy_center),
                "nodes": [self._map_node_to_dict(n) for n in self._record_value(record, "nodes") or []],
                "edges": [self._map_relationship_to_dict(r) for r in self._record_value(record, "edges") or []],
                "scene": self._build_scene_info(),
            }
        return {
            "center": None,
            "nodes": [],
            "edges": [],
            "scene": self._build_scene_info(),
        }

    async def query_graph(self, payload: Any) -> Dict[str, Any]:
        """按过滤条件查询 seed nodes，并在指定深度内扩展为子图。"""
        normalized_payload = self._normalize_query_payload(payload)
        node_filters = normalized_payload["node"]
        edge_filters = normalized_payload["edge"]
        depth = normalized_payload["depth"]
        limit = normalized_payload["limit"]
        active_filters = self._build_active_filters(node_filters, edge_filters)
        seed_query, seed_params = self._build_seed_query(node_filters, edge_filters, limit)

        seed_rows = await self._query_rows(seed_query, seed_params)
        matched_seed_nodes = [
            self._map_node_to_dict(row["node"]) for row in seed_rows if isinstance(row.get("node"), dict)
        ]

        truncated = len(matched_seed_nodes) > limit
        matched_seed_nodes = matched_seed_nodes[:limit]
        if not matched_seed_nodes:
            return {
                "summary": {
                    "mode": "advanced-query",
                    "matched_nodes": 0,
                    "matched_edges": 0,
                    "truncated": False,
                    "active_filters": active_filters,
                },
                "graph": {"center": None, "nodes": [], "edges": []},
                "scene": self._build_scene_info(),
            }

        node_ids = [node["id"] for node in matched_seed_nodes if node.get("id")]
        if not node_ids:
            return {
                "summary": {
                    "mode": "advanced-query",
                    "matched_nodes": len(matched_seed_nodes),
                    "matched_edges": 0,
                    "truncated": truncated,
                    "active_filters": active_filters,
                },
                "graph": {
                    "center": None,
                    "nodes": self._dedupe_nodes(matched_seed_nodes),
                    "edges": [],
                },
                "scene": self._build_scene_info(truncated=truncated),
            }

        expanded_nodes, edges = await self._expand_query_subgraph(
            None,
            node_ids,
            depth,
            limit,
            edge_filters,
        )

        all_nodes = self._dedupe_nodes([*matched_seed_nodes, *expanded_nodes])
        return {
            "summary": {
                "mode": "advanced-query",
                "matched_nodes": len(matched_seed_nodes),
                "matched_edges": len(edges),
                "truncated": truncated,
                "active_filters": active_filters,
            },
            "graph": {"center": None, "nodes": all_nodes, "edges": edges},
            "scene": self._build_scene_info(truncated=truncated),
        }

    async def get_herb_components(self, herb_name: str) -> List[Dict[str, Any]]:
        """获取药材的所有成分"""
        query = """
        MATCH (h:药材 {名称: $name})-[r:包含成分]->(c:成分)
        RETURN c, r.用量 as quantity, r.状态 as status
        """
        records = await self._query_rows(query, {"name": herb_name})
        return [{"component": dict(r["c"]), "quantity": r["quantity"], "status": r["status"]} for r in records]

    async def get_herb_variants(self, herb_name: str) -> List[Dict[str, Any]]:
        """获取药材的所有品种"""
        query = """
        MATCH (h:药材 {名称: $name})-[r:具有品种]->(v:品种)
        RETURN v, r.状态 as status
        """
        records = await self._query_rows(query, {"name": herb_name})
        return [{"variant": dict(r["v"]), "status": r["status"]} for r in records]

    async def get_herb_traits(self, herb_name: str, year_range: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取药材的性状特征"""
        if year_range:
            query = """
            MATCH (h:药材 {名称: $name})-[r:具有性状]->(t:性状)
            WHERE r.年份范围 IS NULL OR r.年份范围 CONTAINS $year_range
            RETURN t, r.取值 as value, r.观察 as observation, r.年份范围 as year_range, r.状态 as status
            """
            params = {"name": herb_name, "year_range": year_range}
        else:
            query = """
            MATCH (h:药材 {名称: $name})-[r:具有性状]->(t:性状)
            RETURN t, r.取值 as value, r.观察 as observation, r.年份范围 as year_range, r.状态 as status
            """
            params = {"name": herb_name}

        records = await self._query_rows(query, params)
        return [{"trait": dict(r["t"]), "value": r["value"], "observation": r["observation"], "year_range": r["year_range"], "status": r["status"]} for r in records]

    async def get_variant_details(self, variant_name: str) -> Dict[str, Any]:
        """获取品种详细信息"""
        query = """
        MATCH (v:品种 {名称: $name})-[:属于药材]->(h:药材)
        OPTIONAL MATCH (v)-[r1:具有性状]->(t:性状)
        OPTIONAL MATCH (h)-[r2:具有功效]->(e:功效)
        RETURN v, h.名称 as base_herb, collect(DISTINCT {trait: t, value: r1.取值}) as traits, collect(DISTINCT e.名称) as efficacies
        """
        record = await self._query_single(query, {"name": variant_name})
        if record:
            return {
                "variant": dict(record["v"]),
                "base_herb": record["base_herb"],
                "traits": record["traits"],
                "efficacies": record["efficacies"]
            }
        return {}

    # ============ 搜索 ============

    async def search_nodes(self, query_text: str, label: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索节点"""
        normalized_label = self._normalize_query_label(label)
        if normalized_label:
            cypher = f"""
            MATCH (n:{normalized_label})
            WHERE n.名称 CONTAINS $search_text OR n.标识 = $search_text
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
        else:
            cypher = """
            MATCH (n)
            WHERE n.名称 CONTAINS $search_text OR n.标识 = $search_text
            RETURN n, labels(n) as labels
            LIMIT $limit
            """

        records = await self._query_rows(cypher, {"search_text": query_text, "limit": limit})
        return [
            {
                "node": self._map_node_to_dict(r["n"]),
                "labels": self._localize_label_list(r["labels"]),
            }
            for r in records
        ]

    async def execute_readonly_cypher(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """执行只读 Cypher 查询并返回原始记录列表。"""
        return await self._query_rows(query, params)

    async def find_path(self, from_name: str, to_name: str, max_depth: int = 4) -> List[Dict[str, Any]]:
        """查找两个节点之间的路径"""
        query = """
        MATCH path = (from {名称: $from_name})-[*1..%d]-(to {名称: $to_name})
        RETURN path
        """ % max_depth

        records = await self._query_rows(query, {"from_name": from_name, "to_name": to_name})
        return [{"path": [dict(node) for node in record["path"]]} for record in records]

    # ============ 验证状态 ============

    async def get_pending_nodes(self, label: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有待验证节点"""
        normalized_label = self._normalize_query_label(label)
        if normalized_label:
            query = f"""
            MATCH (n:{normalized_label}) WHERE n.状态 = $status
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            params = {"limit": limit, "status": localize_status(NodeStatus.PENDING.value)}
        else:
            query = """
            MATCH (n) WHERE n.状态 = $status
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            params = {"limit": limit, "status": localize_status(NodeStatus.PENDING.value)}

        records = await self._query_rows(query, params)
        return [
            {
                "node": self._map_node_to_dict(r["n"]),
                "labels": self._localize_label_list(r["labels"]),
            }
            for r in records
        ]

    async def get_pending_relationships(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有待验证关系"""
        query = """
        MATCH ()-[r]->()
        WHERE r.status = $status
        RETURN r
        LIMIT $limit
        """
        records = await self._query_rows(query, {"limit": limit, "status": NodeStatus.PENDING.value})
        return [dict(r["r"]) for r in records]

    async def verify_node(
        self,
        node_id: str,
        verification_id: str,
        verifier_id: str,
        status: str = NodeStatus.VERIFIED.value
    ) -> Optional[Dict[str, Any]]:
        """验证节点"""
        record = await self._query_single(
            QUERY_VERIFY_NODE,
            {
                "node_id": node_id,
                "verification_id": verification_id,
                "verifier_id": verifier_id,
                "status": localize_status(status),
            },
        )
        if record:
            return self._map_node_to_dict(record["n"])
        return None

    async def verify_relationship(
        self,
        from_name: str,
        rel_type: str,
        to_name: str,
        verification_id: str,
        verifier_id: str,
        status: str = NodeStatus.VERIFIED.value
    ) -> Optional[Dict[str, Any]]:
        """验证关系"""
        query = QUERY_VERIFY_RELATIONSHIP.format(rel_type=rel_type)
        record = await self._query_single(
            query,
            {
                "from_name": from_name,
                "to_name": to_name,
                "verification_id": verification_id,
                "verifier_id": verifier_id,
                "status": status,
            },
        )
        if record:
            return self._map_relationship_to_dict(record["r"])
        return None


# 全局单例
graph_service = GraphService()
