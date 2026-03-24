# 溯源模块 (Provenance module)
# 数据模型: Entity -> has_evidence -> Evidence -> derived_from -> Source

from typing import Optional, Any, Dict, List
from uuid import uuid4

from ..kg.db import cypher_rows, cypher_single
from ..models.enums import NodeStatus


# ============ Lineage Query Patterns (Extracted) ============
# Common Cypher path pattern: Entity -> Evidence -> Source
_LINEAGE_PATH = (
    "(entity)-[:has_evidence]->(evidence:Evidence)"
    "-[:derived_from]->(source:Source)"
)

# ============ Cypher Query Constants ============

QUERY_CREATE_EVIDENCE = """
CREATE (e:Evidence $props)
RETURN e
"""

QUERY_GET_EVIDENCE_BY_ID = """
MATCH (e:Evidence)
WHERE e.id = $evidence_id
RETURN e
"""

QUERY_LINK_EVIDENCE_TO_SOURCE = """
MATCH (e:Evidence {id: $evidence_id})
MATCH (s:Source {id: $source_id})
CREATE (e)-[r:DERIVED_FROM]->(s)
SET r = $props
RETURN r
"""

QUERY_ENTITY_LINEAGE = f"""
MATCH {_LINEAGE_PATH}
WHERE entity.id = $entity_id
RETURN entity, evidence, source
LIMIT 1
"""

QUERY_SOURCE_DERIVATIONS = f"""
MATCH {_LINEAGE_PATH}
WHERE source.id = $source_id
RETURN entity, evidence, source
"""

QUERY_COLLECT_ENTITY_EVIDENCE = """
MATCH (entity)-[:has_evidence]->(e:Evidence)
WHERE entity.id = $entity_id
OPTIONAL MATCH (e)-[:derived_from]->(s:Source)
RETURN e as evidence, s as source
"""

QUERY_LINEAGE_COMPLETENESS = """
MATCH (entity {id: $entity_id})
OPTIONAL MATCH (entity)-[:has_evidence]->(evidence:Evidence)
OPTIONAL MATCH (evidence)-[:derived_from]->(source:Source)
RETURN entity,
       evidence,
       source,
       count(DISTINCT evidence) > 0 as has_evidence,
       count(DISTINCT source) > 0 AND count(DISTINCT evidence) > 0 as has_source,
       count(DISTINCT evidence) > 0 AND count(DISTINCT source) > 0 as chain_complete
"""


# ============ Type Aliases ============
NodeDict = Dict[str, Any]
LineageChain = Dict[str, Any]
EvidenceRecord = Dict[str, Any]


class ProvenanceService:
    """溯源服务 - 管理 Evidence -> Source 链路

    提供以下核心能力:
    - 证据节点 CRUD (create_evidence, get_evidence)
    - 证据-来源关联 (link_evidence_to_source)
    - 溯源链查询 (query_entity_lineage, query_source_derivations)
    - 证据收集与链路完整性校验 (collect_evidence_for_entity, lineage_chain_completeness)
    """

    def __init__(self) -> None:
        self.driver: Optional[Any] = None

    # ============ Helper Methods ============

    async def _query_rows(
        self,
        query: str,
        params: Optional[NodeDict] = None,
    ) -> List[Dict[str, Any]]:
        if self.driver:
            async with self.driver.session() as session:
                result = await session.run(query, **(params or {}))
                return await result.data()
        return await cypher_rows(query, params)

    async def _query_single(
        self,
        query: str,
        params: Optional[NodeDict] = None,
    ) -> Dict[str, Any] | None:
        if self.driver:
            async with self.driver.session() as session:
                result = await session.run(query, **(params or {}))
                return await result.single()
        return await cypher_single(query, params)

    def _map_node_to_dict(self, node: Any) -> NodeDict:
        """Map Neo4j node to dictionary"""
        if node is None:
            return {}
        return dict(node)

    def _map_relationship_to_dict(self, rel: Any) -> NodeDict:
        """Map Neo4j relationship to dictionary"""
        if rel is None:
            return {}
        return dict(rel)

    def _build_lineage_chain(
        self,
        entity: NodeDict,
        evidence: NodeDict,
        source: NodeDict
    ) -> LineageChain:
        """构建溯源链字典 - 辅助方法"""
        return {
            "entity": entity,
            "evidence": evidence,
            "source": source
        }

    # ============ Evidence Operations ============

    async def create_evidence(
        self,
        content: str,
        source_name: str,
        page_reference: Optional[str] = None,
        status: str = NodeStatus.PENDING.value
    ) -> NodeDict:
        """创建证据节点

        Args:
            content: 证据文本内容
            source_name: 来源名称
            page_reference: 页码/章节引用(可选)
            status: 初始状态, 默认 pending

        Returns:
            新建的证据节点字典
        """
        evidence_id = str(uuid4())
        props: NodeDict = {
            "id": evidence_id,
            "content": content,
            "source_name": source_name,
            "page_reference": page_reference,
            "status": status
        }

        record = await self._query_single(QUERY_CREATE_EVIDENCE, {"props": props})
        return self._map_node_to_dict(record["e"]) if record else {}

    async def get_evidence(self, evidence_id: str) -> Optional[NodeDict]:
        """根据 ID 获取证据

        Args:
            evidence_id: 证据节点 ID

        Returns:
            证据节点字典, 不存在时返回 None
        """
        record = await self._query_single(QUERY_GET_EVIDENCE_BY_ID, {"evidence_id": evidence_id})
        if record:
            return self._map_node_to_dict(record["e"])
        return None

    async def link_evidence_to_source(
        self,
        evidence_id: str,
        source_id: str,
        status: str = NodeStatus.PENDING.value
    ) -> NodeDict:
        """创建证据-来源关系 (Evidence)-[:DERIVED_FROM]->(Source)

        Args:
            evidence_id: 证据节点 ID
            source_id: 来源节点 ID
            status: 关系初始状态, 默认 pending

        Returns:
            新建的关系字典
        """
        props: NodeDict = {
            "status": status,
            "source_id": source_id,
            "evidence_id": evidence_id
        }

        record = await self._query_single(
            QUERY_LINK_EVIDENCE_TO_SOURCE,
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "props": props,
            },
        )
        return self._map_relationship_to_dict(record["r"]) if record else {}

    # ============ Lineage Query Operations ============

    async def query_entity_lineage(self, entity_id: str) -> Optional[LineageChain]:
        """查询实体的完整溯源链: Entity -> Evidence -> Source

        Args:
            entity_id: 实体节点 ID

        Returns:
            溯源链字典 {entity, evidence, source}, 无链路时返回 None
        """
        record = await self._query_single(QUERY_ENTITY_LINEAGE, {"entity_id": entity_id})
        if record:
            return self._build_lineage_chain(
                entity=self._map_node_to_dict(record["entity"]),
                evidence=self._map_node_to_dict(record["evidence"]),
                source=self._map_node_to_dict(record["source"])
            )
        return None

    async def query_source_derivations(self, source_id: str) -> List[LineageChain]:
        """查找来源的所有派生实体

        Args:
            source_id: 来源节点 ID

        Returns:
            溯源链列表, 每项为 {entity, evidence, source}
        """
        records = await self._query_rows(QUERY_SOURCE_DERIVATIONS, {"source_id": source_id})
        return [
            self._build_lineage_chain(
                entity=self._map_node_to_dict(r["entity"]),
                evidence=self._map_node_to_dict(r["evidence"]),
                source=self._map_node_to_dict(r["source"])
            )
            for r in records
        ]

    async def collect_evidence_for_entity(self, entity_id: str) -> List[EvidenceRecord]:
        """收集实体的所有证据

        Args:
            entity_id: 实体节点 ID

        Returns:
            证据记录列表, 每项为 {evidence, source}
        """
        records = await self._query_rows(QUERY_COLLECT_ENTITY_EVIDENCE, {"entity_id": entity_id})
        return [
            {
                "evidence": self._map_node_to_dict(r["evidence"]),
                "source": self._map_node_to_dict(r["source"]) if r["source"] else None
            }
            for r in records
        ]

    async def lineage_chain_completeness(self, entity_id: str) -> Optional[LineageChain]:
        """验证溯源链完整性

        Args:
            entity_id: 实体节点 ID

        Returns:
            包含完整性标记的溯源链字典:
            {entity, evidence, source, has_evidence, has_source, chain_complete}
        """
        record = await self._query_single(QUERY_LINEAGE_COMPLETENESS, {"entity_id": entity_id})
        if record:
            entity = self._map_node_to_dict(record["entity"])
            evidence = self._map_node_to_dict(record["evidence"]) if record["evidence"] else None
            source = self._map_node_to_dict(record["source"]) if record["source"] else None
            return {
                "entity": entity,
                "evidence": evidence,
                "source": source,
                "has_evidence": record["has_evidence"],
                "has_source": record["has_source"],
                "chain_complete": record["chain_complete"]
            }
        return None


# 全局单例
provenance_service = ProvenanceService()
