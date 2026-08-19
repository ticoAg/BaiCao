# 溯源模块 (Provenance module)
# 图谱存储主路径: Entity -[:由证据支持]-> 证据，Entity -[:来源于]-> 来源
# 兼容路径: 证据 -[:来源于]-> 来源
# 存储键: 标识 / 名称 / 证据原文 / 状态；对外映射为前端友好字段。

from typing import Any, Dict, List, Optional
from uuid import uuid4

from knowledge_model.constants import EdgeType, NodeStatus, NodeType, to_neo4j_label, to_neo4j_rel
from knowledge_model.graph_i18n import delocalize_status, to_graph_properties

from ..kg.db import cypher_rows, cypher_single


EVIDENCE_LABEL = to_neo4j_label(NodeType.EVIDENCE)
SOURCE_LABEL = to_neo4j_label(NodeType.SOURCE)
SUPPORTED_BY_REL = to_neo4j_rel(EdgeType.SUPPORTED_BY)
ORIGINATED_FROM_REL = to_neo4j_rel(EdgeType.ORIGINATED_FROM)

QUERY_CREATE_EVIDENCE = f"""
CREATE (e:{EVIDENCE_LABEL} $props)
RETURN e
"""

QUERY_GET_EVIDENCE_BY_ID = f"""
MATCH (e:{EVIDENCE_LABEL})
WHERE e.标识 = $evidence_id
RETURN e
"""

QUERY_LINK_EVIDENCE_TO_SOURCE = f"""
MATCH (e:{EVIDENCE_LABEL} {{标识: $evidence_id}})
MATCH (s:{SOURCE_LABEL} {{标识: $source_id}})
MERGE (e)-[r:{ORIGINATED_FROM_REL}]->(s)
SET r += $props
RETURN r, type(r) AS rel_type
"""

QUERY_ENTITY_LINEAGE = f"""
MATCH (entity {{标识: $entity_id}})
OPTIONAL MATCH (entity)-[:{SUPPORTED_BY_REL}]->(evidence:{EVIDENCE_LABEL})
OPTIONAL MATCH (entity)-[:{ORIGINATED_FROM_REL}]->(entity_source:{SOURCE_LABEL})
OPTIONAL MATCH (evidence)-[:{ORIGINATED_FROM_REL}]->(evidence_source:{SOURCE_LABEL})
WITH entity, evidence, coalesce(entity_source, evidence_source) AS source
WHERE evidence IS NOT NULL AND source IS NOT NULL
RETURN entity, evidence, source
LIMIT 1
"""

QUERY_SOURCE_DERIVATIONS = f"""
MATCH (source:{SOURCE_LABEL} {{标识: $source_id}})<-[:{ORIGINATED_FROM_REL}]-(entity)
WHERE NOT entity:{EVIDENCE_LABEL}
OPTIONAL MATCH (entity)-[:{SUPPORTED_BY_REL}]->(evidence:{EVIDENCE_LABEL})
RETURN entity, evidence, source
UNION
MATCH (source:{SOURCE_LABEL} {{标识: $source_id}})<-[:{ORIGINATED_FROM_REL}]-(evidence:{EVIDENCE_LABEL})
      <-[:{SUPPORTED_BY_REL}]-(entity)
WHERE NOT (entity)-[:{ORIGINATED_FROM_REL}]->(:{SOURCE_LABEL} {{标识: $source_id}})
RETURN entity, evidence, source
"""

QUERY_COLLECT_ENTITY_EVIDENCE = f"""
MATCH (entity {{标识: $entity_id}})-[:{SUPPORTED_BY_REL}]->(e:{EVIDENCE_LABEL})
OPTIONAL MATCH (entity)-[:{ORIGINATED_FROM_REL}]->(entity_source:{SOURCE_LABEL})
OPTIONAL MATCH (e)-[:{ORIGINATED_FROM_REL}]->(evidence_source:{SOURCE_LABEL})
RETURN e AS evidence, coalesce(entity_source, evidence_source) AS source
"""

QUERY_LINEAGE_COMPLETENESS = f"""
MATCH (entity {{标识: $entity_id}})
OPTIONAL MATCH (entity)-[:{SUPPORTED_BY_REL}]->(evidence:{EVIDENCE_LABEL})
OPTIONAL MATCH (entity)-[:{ORIGINATED_FROM_REL}]->(entity_source:{SOURCE_LABEL})
OPTIONAL MATCH (evidence)-[:{ORIGINATED_FROM_REL}]->(evidence_source:{SOURCE_LABEL})
WITH entity,
     collect(DISTINCT evidence) AS evidences,
     collect(DISTINCT coalesce(entity_source, evidence_source)) AS sources
WITH entity, head(evidences) AS evidence, head(sources) AS source,
     size(evidences) > 0 AS has_evidence,
     size(sources) > 0 AS has_source
RETURN entity,
       evidence,
       source,
       has_evidence,
       has_source,
       (has_evidence AND has_source) AS chain_complete
"""

NodeDict = Dict[str, Any]
LineageChain = Dict[str, Any]
EvidenceRecord = Dict[str, Any]

_ENTITY_KEYS = ("id", "name", "status")
_EVIDENCE_KEYS = ("id", "content", "source_name", "page_reference", "status")
_RELATIONSHIP_KEYS = ("type", "status", "evidence_id", "source_id")


def _as_prop_dict(value: Any) -> NodeDict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    properties = getattr(value, "__properties__", None)
    if properties is not None:
        return dict(properties)
    try:
        return dict(value)
    except TypeError:
        return {}


def _first_present(raw: NodeDict, *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return None


def _frontend_status(value: Any) -> str:
    if value is None:
        return NodeStatus.PENDING.value
    normalized = delocalize_status(str(getattr(value, "value", value)))
    return normalized or NodeStatus.PENDING.value


def to_frontend_node(node: Any, *, include_evidence_fields: bool = False) -> NodeDict | None:
    """把图谱节点映射为前端字段，并去掉中文存储键。"""
    raw = _as_prop_dict(node)
    if not raw:
        return None

    node_id = _first_present(raw, "id", "标识")
    if not node_id:
        return None

    mapped: NodeDict = {
        "id": str(node_id),
        "name": str(_first_present(raw, "name", "名称") or ""),
        "status": _frontend_status(_first_present(raw, "status", "状态")),
    }
    if include_evidence_fields:
        page_reference = _first_present(raw, "page_reference", "页码")
        evidence: NodeDict = {
            "id": mapped["id"],
            "content": str(
                _first_present(raw, "content", "evidence_text", "证据原文", "raw_text", "原文") or ""
            ),
            "source_name": str(
                _first_present(raw, "source_name", "source", "来源", "name", "名称") or ""
            ),
            "status": mapped["status"],
        }
        if page_reference is not None and str(page_reference) != "":
            evidence["page_reference"] = str(page_reference)
        return {key: evidence[key] for key in _EVIDENCE_KEYS if key in evidence}
    return {key: mapped[key] for key in _ENTITY_KEYS}


def to_frontend_relationship(
    rel: Any,
    *,
    rel_type: str | None = None,
    evidence_id: str | None = None,
    source_id: str | None = None,
) -> NodeDict:
    """把图谱关系映射为前端字段，并去掉中文存储键。"""
    raw = _as_prop_dict(rel)
    type_value = rel_type or getattr(rel, "type", None) or raw.get("type")
    if type_value is None:
        type_value = ORIGINATED_FROM_REL
    mapped: NodeDict = {
        "type": str(getattr(type_value, "value", type_value)),
        "status": _frontend_status(_first_present(raw, "status", "状态")),
    }
    if evidence_id:
        mapped["evidence_id"] = evidence_id
    if source_id:
        mapped["source_id"] = source_id
    return {key: mapped[key] for key in _RELATIONSHIP_KEYS if key in mapped}


def _record_value(record: Any, key: str) -> Any:
    if record is None:
        return None
    try:
        return record[key]
    except (KeyError, TypeError, IndexError):
        if isinstance(record, dict):
            return record.get(key)
        getter = getattr(record, "get", None)
        if callable(getter):
            return getter(key)
        return None


class ProvenanceService:
    """溯源服务 - 管理 证据 -> 来源 链路

    提供以下核心能力:
    - 证据节点 CRUD (create_evidence, get_evidence)
    - 证据-来源关联 (link_evidence_to_source)
    - 溯源链查询 (query_entity_lineage, query_source_derivations)
    - 证据收集与链路完整性校验 (collect_evidence_for_entity, lineage_chain_completeness)
    """

    def __init__(self) -> None:
        self.driver: Optional[Any] = None

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

    def _map_evidence(self, node: Any) -> NodeDict | None:
        return to_frontend_node(node, include_evidence_fields=True)

    def _map_entity(self, node: Any) -> NodeDict | None:
        return to_frontend_node(node, include_evidence_fields=False)

    def _build_lineage_chain(
        self,
        entity: Any,
        evidence: Any,
        source: Any,
        *,
        require_evidence: bool = False,
    ) -> LineageChain | None:
        mapped_entity = self._map_entity(entity)
        mapped_evidence = self._map_evidence(evidence)
        mapped_source = self._map_entity(source)
        if not mapped_entity or not mapped_source:
            return None
        if require_evidence and not mapped_evidence:
            return None
        return {
            "entity": mapped_entity,
            "evidence": mapped_evidence,
            "source": mapped_source,
        }

    async def create_evidence(
        self,
        content: str,
        source_name: str,
        page_reference: Optional[str] = None,
        status: str = NodeStatus.PENDING.value,
    ) -> NodeDict:
        """创建证据节点，写入中文存储键并回映射为前端字段。"""
        evidence_id = str(uuid4())
        stored = to_graph_properties(
            {
                "id": evidence_id,
                "name": source_name,
                "evidence_text": content,
                "source": source_name,
                "status": getattr(status, "value", status),
            }
        )
        if page_reference:
            stored["页码"] = page_reference
        record = await self._query_single(QUERY_CREATE_EVIDENCE, {"props": stored})
        mapped = self._map_evidence(_record_value(record, "e")) if record else None
        return mapped or {}

    async def get_evidence(self, evidence_id: str) -> Optional[NodeDict]:
        """根据 ID 获取证据。"""
        record = await self._query_single(
            QUERY_GET_EVIDENCE_BY_ID, {"evidence_id": evidence_id}
        )
        if not record:
            return None
        return self._map_evidence(_record_value(record, "e"))

    async def link_evidence_to_source(
        self,
        evidence_id: str,
        source_id: str,
        status: str = NodeStatus.PENDING.value,
    ) -> NodeDict:
        """创建证据-来源关系 (证据)-[:来源于]->(来源)。"""
        stored = to_graph_properties({"status": getattr(status, "value", status)})
        record = await self._query_single(
            QUERY_LINK_EVIDENCE_TO_SOURCE,
            {
                "evidence_id": evidence_id,
                "source_id": source_id,
                "props": stored,
            },
        )
        if not record:
            return {}
        return to_frontend_relationship(
            _record_value(record, "r"),
            rel_type=_record_value(record, "rel_type"),
            evidence_id=evidence_id,
            source_id=source_id,
        )

    async def query_entity_lineage(self, entity_id: str) -> Optional[LineageChain]:
        """查询实体溯源链，优先 Entity -[:来源于]-> 来源，兼容证据 -[:来源于]-> 来源。"""
        record = await self._query_single(QUERY_ENTITY_LINEAGE, {"entity_id": entity_id})
        if not record:
            return None
        return self._build_lineage_chain(
            entity=_record_value(record, "entity"),
            evidence=_record_value(record, "evidence"),
            source=_record_value(record, "source"),
            require_evidence=True,
        )

    async def query_source_derivations(self, source_id: str) -> List[LineageChain]:
        """查找来源的所有派生实体。"""
        records = await self._query_rows(QUERY_SOURCE_DERIVATIONS, {"source_id": source_id})
        chains: List[LineageChain] = []
        for record in records:
            chain = self._build_lineage_chain(
                entity=_record_value(record, "entity"),
                evidence=_record_value(record, "evidence"),
                source=_record_value(record, "source"),
            )
            if chain:
                chains.append(chain)
        return chains

    async def collect_evidence_for_entity(self, entity_id: str) -> List[EvidenceRecord]:
        """收集实体的所有证据。"""
        records = await self._query_rows(
            QUERY_COLLECT_ENTITY_EVIDENCE, {"entity_id": entity_id}
        )
        collected: List[EvidenceRecord] = []
        for record in records:
            evidence = self._map_evidence(_record_value(record, "evidence"))
            if not evidence:
                continue
            collected.append(
                {
                    "evidence": evidence,
                    "source": self._map_entity(_record_value(record, "source")),
                }
            )
        return collected

    async def lineage_chain_completeness(self, entity_id: str) -> Optional[LineageChain]:
        """验证溯源链完整性。"""
        record = await self._query_single(
            QUERY_LINEAGE_COMPLETENESS, {"entity_id": entity_id}
        )
        if not record:
            return None
        entity = self._map_entity(_record_value(record, "entity"))
        if not entity:
            return None
        return {
            "entity": entity,
            "evidence": self._map_evidence(_record_value(record, "evidence")),
            "source": self._map_entity(_record_value(record, "source")),
            "has_evidence": bool(_record_value(record, "has_evidence")),
            "has_source": bool(_record_value(record, "has_source")),
            "chain_complete": bool(_record_value(record, "chain_complete")),
        }


provenance_service = ProvenanceService()
