# Knowledge Graph Service using Neo4j
# 完整数据模型支持：药材-成分-品种-工艺-性状

from typing import Optional, Any, Dict, List
from uuid import UUID, uuid4 as uuid_module_uuid4

from neo4j import AsyncGraphDatabase

from ..core.config import get_settings
from ..models.enums import (
    NodeType,
    NodeStatus,
    EdgeType,
    HerbType,
    TraitCategory,
)

settings = get_settings()


# ============ Cypher Query Constants ============

QUERY_CREATE_NODE = """
CREATE (n:{label} $props) RETURN n
"""

QUERY_GET_NODE_BY_ID = """
MATCH (n) WHERE n.id = $node_id
RETURN n, labels(n) as labels
"""

QUERY_GET_NODE_BY_NAME = """
MATCH (n:{label} {{name: $name}})
RETURN n, labels(n) as labels
"""

QUERY_CREATE_RELATIONSHIP = """
MATCH (a {{name: $from_name}})
MATCH (b {{name: $to_name}})
CREATE (a)-[r:{rel_type}]->(b)
SET r = $props
RETURN r
"""

QUERY_VERIFY_NODE = """
MATCH (n)
WHERE n.id = $node_id
SET n.status = $status,
    n.verification_id = $verification_id,
    n.verified_by = $verifier_id,
    n.verified_at = datetime()
RETURN n
"""

QUERY_VERIFY_RELATIONSHIP = """
MATCH (from)-[r:{rel_type}]->(to)
WHERE from.name = $from_name AND to.name = $to_name
SET r.status = $status,
    r.verification_id = $verification_id,
    r.verified_by = $verifier_id,
    r.verified_at = datetime()
RETURN r
"""

class GraphService:
    """Neo4j 图谱服务 - 支持多维度数据模型"""

    def __init__(self) -> None:
        self.driver: Optional[Any] = None

    async def connect(self) -> None:
        """建立 Neo4j 连接"""
        if not self.driver:
            self.driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )

    async def close(self) -> None:
        """关闭 Neo4j 连接"""
        if self.driver:
            await self.driver.close()
            self.driver = None

    async def ensure_connected(self) -> None:
        """确保已连接"""
        if not self.driver:
            await self.connect()

    # ============ Helper Methods ============

    def _map_node_to_dict(self, node: Any, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Map Neo4j node to dictionary with optional labels"""
        result = dict(node)
        if labels is not None:
            result["labels"] = labels
        return result

    def _map_relationship_to_dict(self, rel: Any) -> Dict[str, Any]:
        """Map Neo4j relationship to dictionary"""
        return dict(rel)

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
            node_key = str(node.get("id") or node.get("name"))
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

    # ============ 基础节点操作 ============

    async def create_node(
        self,
        label: str,
        name: str,
        source: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建任意类型节点（默认 status=pending）"""
        await self.ensure_connected()

        node_id = str(uuid_module_uuid4())
        props: Dict[str, Any] = properties or {}
        props.setdefault("id", node_id)
        props.setdefault("name", name)
        props.setdefault("source", source)
        props.setdefault("imported_at", "datetime()")
        props.setdefault("status", NodeStatus.PENDING.value)
        props.setdefault("verification_id", None)
        props.setdefault("verified_by", None)
        props.setdefault("verified_at", None)

        query = QUERY_CREATE_NODE.format(label=label)
        async with self.driver.session() as session:
            result = await session.run(query, props=props)
            record = await result.single()
            return dict(record["n"])

    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """根据 ID 获取节点"""
        await self.ensure_connected()

        async with self.driver.session() as session:
            result = await session.run(QUERY_GET_NODE_BY_ID, node_id=node_id)
            record = await result.single()
            if record:
                return self._map_node_to_dict(record["n"], record["labels"])
            return None

    async def get_node_by_name(self, name: str, label: str) -> Optional[Dict[str, Any]]:
        """根据名称和类型获取节点"""
        await self.ensure_connected()

        query = QUERY_GET_NODE_BY_NAME.format(label=label)
        async with self.driver.session() as session:
            result = await session.run(query, name=name)
            record = await result.single()
            if record:
                return self._map_node_to_dict(record["n"], record["labels"])
            return None

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
        """创建药材-成分关系 (Herb)-[:CONTAINS]->(Component)"""
        await self.ensure_connected()

        props: Dict[str, Any] = {
            "status": NodeStatus.PENDING.value,
            "verification_id": None,
            "verified_by": None,
            "verified_at": None,
            "quantity": quantity
        }

        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (c:Component {name: $component_name})
        CREATE (h)-[r:CONTAINS]->(c)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, component_name=component_name, props=props)
            record = await result.single()
            return self._map_relationship_to_dict(record["r"])

    async def link_herb_parent(
        self,
        child_name: str,
        parent_name: str
    ) -> Dict[str, Any]:
        """创建药材-父子关系 (Child)-[:PARENT_OF]->(Parent)

        表示child是parent的子类/衍生物
        """
        await self.ensure_connected()

        props: Dict[str, Any] = {
            "status": NodeStatus.PENDING.value,
            "verification_id": None,
            "verified_by": None,
            "verified_at": None
        }

        query = """
        MATCH (child:Herb {name: $child_name})
        MATCH (parent:Herb {name: $parent_name})
        CREATE (child)-[r:PARENT_OF]->(parent)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, child_name=child_name, parent_name=parent_name, props=props)
            record = await result.single()
            return self._map_relationship_to_dict(record["r"])

    async def link_herb_child(
        self,
        parent_name: str,
        child_name: str
    ) -> Dict[str, Any]:
        """创建药材-子关系 (Parent)-[:CHILD_OF]->(Child)

        表示parent是child的父级/来源
        """
        await self.ensure_connected()

        props: Dict[str, Any] = {
            "status": NodeStatus.PENDING.value,
            "verification_id": None,
            "verified_by": None,
            "verified_at": None
        }

        query = """
        MATCH (parent:Herb {name: $parent_name})
        MATCH (child:Herb {name: $child_name})
        CREATE (parent)-[r:CHILD_OF]->(child)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, parent_name=parent_name, child_name=child_name, props=props)
            record = await result.single()
            return self._map_relationship_to_dict(record["r"])

    async def link_herb_source(
        self,
        herb_name: str,
        source_name: str
    ) -> Dict[str, Any]:
        """创建药材-来源关系 (Herb)-[:ORIGINATED_FROM]->(Source)

        表示herb来源于source（产地、供应商等）
        """
        await self.ensure_connected()

        props: Dict[str, Any] = {
            "status": NodeStatus.PENDING.value,
            "verification_id": None,
            "verified_by": None,
            "verified_at": None
        }

        query = """
        MATCH (herb:Herb {name: $herb_name})
        MATCH (source:Source {name: $source_name})
        CREATE (herb)-[r:ORIGINATED_FROM]->(source)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, source_name=source_name, props=props)
            record = await result.single()
            return self._map_relationship_to_dict(record["r"])

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
        """创建品种-药材关系 (Variant)-[:VARIANT_OF]->(Herb)"""
        await self.ensure_connected()

        props = {"status": NodeStatus.PENDING.value}

        query = """
        MATCH (v:Variant {name: $variant_name})
        MATCH (h:Herb {name: $herb_name})
        CREATE (v)-[r:VARIANT_OF]->(h)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, variant_name=variant_name, herb_name=herb_name, props=props)
            record = await result.single()
            return dict(record["r"])

    async def link_herb_has_variant(self, herb_name: str, variant_name: str) -> Dict[str, Any]:
        """创建药材-品种关系 (Herb)-[:HAS_VARIANT]->(Variant)"""
        await self.ensure_connected()

        props = {"status": NodeStatus.PENDING.value}

        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (v:Variant {name: $variant_name})
        CREATE (h)-[r:HAS_VARIANT]->(v)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, variant_name=variant_name, props=props)
            record = await result.single()
            return dict(record["r"])

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
        """创建药材-工艺关系 (Herb)-[:PROCESSED_BY]->(Process)"""
        await self.ensure_connected()

        props = {
            "status": NodeStatus.PENDING.value,
            "duration": duration,
            "conditions": conditions,
            "start_date": None,
            "end_date": None
        }

        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (p:Process {name: $process_name})
        CREATE (h)-[r:PROCESSED_BY]->(p)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, process_name=process_name, props=props)
            record = await result.single()
            return dict(record["r"])

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
        """创建药材-性状关系 (Herb)-[:HAS_TRAIT]->(Trait)"""
        await self.ensure_connected()

        props = {
            "status": NodeStatus.PENDING.value,
            "value": value,
            "observation": observation,
            "year_range": year_range
        }

        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (t:Trait {name: $trait_name})
        CREATE (h)-[r:HAS_TRAIT]->(t)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, trait_name=trait_name, props=props)
            record = await result.single()
            return dict(record["r"])

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
        """创建药材-储存时间关系 (Herb)-[:STORED_FOR]->(TimePoint)"""
        await self.ensure_connected()

        props = {
            "status": NodeStatus.PENDING.value,
            "years": years,
            "start_date": start_date,
            "end_date": None
        }

        # 查找或创建时间点节点
        await self.create_timepoint(years, "system")

        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (t:TimePoint {years: $years})
        CREATE (h)-[r:STORED_FOR]->(t)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, years=years, props=props)
            record = await result.single()
            return dict(record["r"])

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
        await self.ensure_connected()
        props = {"status": NodeStatus.PENDING.value}
        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (e:Efficacy {name: $efficacy_name})
        CREATE (h)-[r:HAS_EFFICACY]->(e)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, efficacy_name=efficacy_name, props=props)
            record = await result.single()
            return dict(record["r"])

    async def link_herb_has_flavor(self, herb_name: str, flavor_name: str) -> Dict[str, Any]:
        """创建药材-性味关系"""
        await self.ensure_connected()
        props = {"status": NodeStatus.PENDING.value}
        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (f:Flavor {name: $flavor_name})
        CREATE (h)-[r:HAS_FLAVOR]->(f)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, flavor_name=flavor_name, props=props)
            record = await result.single()
            return dict(record["r"])

    async def link_herb_enters_meridian(self, herb_name: str, meridian_name: str) -> Dict[str, Any]:
        """创建药材-归经关系"""
        await self.ensure_connected()
        props = {"status": NodeStatus.PENDING.value}
        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (m:Meridian {name: $meridian_name})
        CREATE (h)-[r:ENTERS_MERIDIAN]->(m)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(query, herb_name=herb_name, meridian_name=meridian_name, props=props)
            record = await result.single()
            return dict(record["r"])

    async def create_disease(
        self, name: str, source: str, tcm_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建疾病节点"""
        return await self.create_node(
            label=NodeType.DISEASE.value,
            name=name,
            source=source,
            extra_props={"tcm_type": tcm_type} if tcm_type else {},
        )

    async def link_herb_treats(self, herb_name: str, disease_name: str) -> Dict[str, Any]:
        """创建药材-主治关系 (Herb)-[:TREATS]->(Disease)"""
        await self.ensure_connected()
        props = {"status": NodeStatus.PENDING.value}
        query = """
        MATCH (h:Herb {name: $herb_name})
        MATCH (d:Disease {name: $disease_name})
        CREATE (h)-[r:TREATS]->(d)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(
                query, herb_name=herb_name, disease_name=disease_name, props=props
            )
            record = await result.single()
            return dict(record["r"])

    async def link_herb_similar(
        self, herb_name_1: str, herb_name_2: str, similarity_score: float = 0.0
    ) -> Dict[str, Any]:
        """创建药材相似关系 (Herb)-[:SIMILAR_TO]->(Herb)"""
        await self.ensure_connected()
        props = {"status": NodeStatus.PENDING.value, "similarity_score": similarity_score}
        query = """
        MATCH (h1:Herb {name: $herb_name_1})
        MATCH (h2:Herb {name: $herb_name_2})
        CREATE (h1)-[r:SIMILAR_TO]->(h2)
        SET r = $props
        RETURN r
        """
        async with self.driver.session() as session:
            result = await session.run(
                query,
                herb_name_1=herb_name_1,
                herb_name_2=herb_name_2,
                props=props,
            )
            record = await result.single()
            return dict(record["r"])

    # ============ 图谱查询 ============

    async def get_herb_graph(self, herb_name: str, depth: int = 1) -> Dict[str, Any]:
        """获取以药材为中心的完整图谱"""
        await self.ensure_connected()

        query = f"""
        MATCH (h:Herb {{name: $name}})
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
                        id: coalesce(r.id, elementId(r)),
                        rel_type: type(r),
                        status: coalesce(r.status, 'pending'),
                        verification_id: r.verification_id,
                        verified_by: r.verified_by,
                        verified_at: toString(r.verified_at),
                        source: {{
                            id: startNode(r).id,
                            name: startNode(r).name,
                            source: startNode(r).source,
                            status: startNode(r).status,
                            labels: labels(startNode(r))
                        }},
                        target: {{
                            id: endNode(r).id,
                            name: endNode(r).name,
                            source: endNode(r).source,
                            status: endNode(r).status,
                            labels: labels(endNode(r))
                        }}
                    }}
                ]
            ) AS edges
        """

        async with self.driver.session() as session:
            result = await session.run(query, name=herb_name)
            record = await result.single()
            center = self._record_value(record, "center") if record else None
            if center:
                nodes = self._dedupe_nodes([center, *(self._record_value(record, "nodes") or [])])
                edges = self._dedupe_edges(self._record_value(record, "edges") or [])
                return {
                    "center": center,
                    "nodes": nodes,
                    "edges": edges,
                }

            legacy_center = self._record_value(record, "h") if record else None
            if legacy_center:
                return {
                    "center": self._map_node_to_dict(legacy_center),
                    "nodes": [self._map_node_to_dict(n) for n in self._record_value(record, "nodes") or []],
                    "edges": [self._map_relationship_to_dict(r) for r in self._record_value(record, "edges") or []]
                }
            return {"center": None, "nodes": [], "edges": []}

    async def get_herb_components(self, herb_name: str) -> List[Dict[str, Any]]:
        """获取药材的所有成分"""
        await self.ensure_connected()

        query = """
        MATCH (h:Herb {name: $name})-[r:CONTAINS]->(c:Component)
        RETURN c, r.quantity as quantity, r.status as status
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=herb_name)
            records = await result.data()
            return [{"component": dict(r["c"]), "quantity": r["quantity"], "status": r["status"]} for r in records]

    async def get_herb_variants(self, herb_name: str) -> List[Dict[str, Any]]:
        """获取药材的所有品种"""
        await self.ensure_connected()

        query = """
        MATCH (h:Herb {name: $name})-[r:HAS_VARIANT]->(v:Variant)
        RETURN v, r.status as status
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=herb_name)
            records = await result.data()
            return [{"variant": dict(r["v"]), "status": r["status"]} for r in records]

    async def get_herb_traits(self, herb_name: str, year_range: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取药材的性状特征"""
        await self.ensure_connected()

        if year_range:
            query = """
            MATCH (h:Herb {name: $name})-[r:HAS_TRAIT]->(t:Trait)
            WHERE r.year_range IS NULL OR r.year_range CONTAINS $year_range
            RETURN t, r.value as value, r.observation as observation, r.year_range as year_range, r.status as status
            """
            params = {"name": herb_name, "year_range": year_range}
        else:
            query = """
            MATCH (h:Herb {name: $name})-[r:HAS_TRAIT]->(t:Trait)
            RETURN t, r.value as value, r.observation as observation, r.year_range as year_range, r.status as status
            """
            params = {"name": herb_name}

        async with self.driver.session() as session:
            result = await session.run(query, **params)
            records = await result.data()
            return [{"trait": dict(r["t"]), "value": r["value"], "observation": r["observation"], "year_range": r["year_range"], "status": r["status"]} for r in records]

    async def get_variant_details(self, variant_name: str) -> Dict[str, Any]:
        """获取品种详细信息"""
        await self.ensure_connected()

        query = """
        MATCH (v:Variant {name: $name})-[:VARIANT_OF]->(h:Herb)
        OPTIONAL MATCH (v)-[r1:HAS_TRAIT]->(t:Trait)
        OPTIONAL MATCH (h)-[r2:HAS_EFFICACY]->(e:Efficacy)
        RETURN v, h.name as base_herb, collect(DISTINCT {trait: t, value: r1.value}) as traits, collect(DISTINCT e.name) as efficacies
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=variant_name)
            record = await result.single()
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
        await self.ensure_connected()

        if label:
            cypher = f"""
            MATCH (n:{label})
            WHERE n.name CONTAINS $search_text
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
        else:
            cypher = """
            MATCH (n)
            WHERE n.name CONTAINS $search_text
            RETURN n, labels(n) as labels
            LIMIT $limit
            """

        async with self.driver.session() as session:
            result = await session.run(cypher, search_text=query_text, limit=limit)
            records = await result.data()
            return [{"node": dict(r["n"]), "labels": r["labels"]} for r in records]

    async def find_path(self, from_name: str, to_name: str, max_depth: int = 4) -> List[Dict[str, Any]]:
        """查找两个节点之间的路径"""
        await self.ensure_connected()

        query = """
        MATCH path = (from {name: $from_name})-[*1..%d]-(to {name: $to_name})
        RETURN path
        """ % max_depth

        async with self.driver.session() as session:
            result = await session.run(query, from_name=from_name, to_name=to_name)
            records = await result.data()
            return [{"path": [dict(node) for node in record["path"]]} for record in records]

    # ============ 验证状态 ============

    async def get_pending_nodes(self, label: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有待验证节点"""
        await self.ensure_connected()

        if label:
            query = f"""
            MATCH (n:{label}) WHERE n.status = $status
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            params = {"limit": limit, "status": NodeStatus.PENDING.value}
        else:
            query = """
            MATCH (n) WHERE n.status = $status
            RETURN n, labels(n) as labels
            LIMIT $limit
            """
            params = {"limit": limit, "status": NodeStatus.PENDING.value}

        async with self.driver.session() as session:
            result = await session.run(query, **params)
            records = await result.data()
            return [{"node": dict(r["n"]), "labels": r["labels"]} for r in records]

    async def get_pending_relationships(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有待验证关系"""
        await self.ensure_connected()

        query = """
        MATCH ()-[r]->()
        WHERE r.status = $status
        RETURN r
        LIMIT $limit
        """
        async with self.driver.session() as session:
            result = await session.run(query, limit=limit, status=NodeStatus.PENDING.value)
            records = await result.data()
            return [dict(r["r"]) for r in records]

    async def verify_node(
        self,
        node_id: str,
        verification_id: str,
        verifier_id: str,
        status: str = NodeStatus.VERIFIED.value
    ) -> Optional[Dict[str, Any]]:
        """验证节点"""
        await self.ensure_connected()

        async with self.driver.session() as session:
            result = await session.run(
                QUERY_VERIFY_NODE,
                node_id=node_id,
                verification_id=verification_id,
                verifier_id=verifier_id,
                status=status
            )
            record = await result.single()
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
        await self.ensure_connected()

        query = QUERY_VERIFY_RELATIONSHIP.format(rel_type=rel_type)
        async with self.driver.session() as session:
            result = await session.run(
                query,
                from_name=from_name,
                to_name=to_name,
                verification_id=verification_id,
                verifier_id=verifier_id,
                status=status
            )
            record = await result.single()
            if record:
                return self._map_relationship_to_dict(record["r"])
            return None


# 全局单例
graph_service = GraphService()
