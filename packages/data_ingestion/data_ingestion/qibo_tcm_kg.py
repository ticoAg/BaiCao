"""清洗 fengxi177/Knowlegde_Graph_TCM 药材/方剂关系，输出 DatasetRecord。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "fengxi177-knowledge-graph-tcm"
IMPORT_SCOPE_KEY = "github:fengxi177/Knowlegde_Graph_TCM"
DEFAULT_BATCH_ID = "2026-08-19-kg-tcm-v1"
PROCESSOR = "qibo_tcm_kg"
PROMPT_HASH = prompt_hash_for(Path(__file__))

_QIBO_RELATIVE_ROOT = Path("tmp/qibo-datasets/Knowlegde_Graph_TCM")
_RELATION_KEYS = {"node_1", "relation", "node_2"}

ALIASES_KEY = "aliases"
ORIGIN_KEY = "origin"
FORMULA_NAME_KEY = "formula_name"
DOSAGE_KEY = "dosage"

KIND_HERB = "中药名"
KIND_FORMULA_NAME = "方名"
KIND_PRESCRIPTION = "处方"
KIND_ALIAS = "别名"
KIND_AREA = "分布"
KIND_SOURCE = "来源"
KIND_FUNCTION = "功能"
KIND_INDICATION = "主治"
KIND_QI = "四气"
KIND_FLAVOR = "五味"
KIND_MERIDIAN = "归经"
KIND_FORMULA_FUNCTION = "功能主治"
KIND_DOSE = "剂量"

REL_INCLUDE = "include"
REL_FROM = "from"
REL_DISTRIBUTION = "distribution area"
REL_ATTENDING = "attending"
REL_FOUR_PROPERTIES = "four properties"
REL_FIVE_FLAVORS = "five flavors"
REL_CHANNEL = "channel tropism"
REL_FUNCTIONS = "functions"
REL_ANOTHER_NAME = "another name"
REL_PRESCRIPTION_TYPE = "prescription type"
REL_COMPOSITION = "composition"
REL_DOSE = "dose"

_IGNORED_RELATIONS = {REL_INCLUDE, REL_PRESCRIPTION_TYPE}
_PRESCRIPTION_SUFFIX_RE = re.compile(r"^(.+)_(\d+)$")
_NODE_TYPE_RANK = {item.value: index for index, item in enumerate(NodeType)}
_EDGE_TYPE_RANK = {item.value: index for index, item in enumerate(EdgeType)}
_EDGE_TARGET_TYPE = {
    EdgeType.HAS_EFFICACY.value: NodeType.EFFICACY.value,
    EdgeType.TREATS.value: NodeType.DISEASE.value,
    EdgeType.HAS_FLAVOR.value: NodeType.FLAVOR.value,
    EdgeType.ENTERS_MERIDIAN.value: NodeType.MERIDIAN.value,
    EdgeType.ORIGINATED_FROM.value: NodeType.SOURCE.value,
    EdgeType.CONTAINS_HERB.value: NodeType.HERB.value,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_ZHONGYAO_PATH = (
    repo_root()
    / _QIBO_RELATIVE_ROOT
    / "zhongyao/data_zhongyao/relations_zhongyao.json"
)
DEFAULT_FANGJI_PATH = (
    repo_root() / _QIBO_RELATIVE_ROOT / "fangji/data_fangji/relations_fangji.json"
)


@dataclass(frozen=True, slots=True)
class Endpoint:
    kind: str
    name: str


@dataclass(frozen=True, slots=True)
class Triple:
    relation: str
    left: Endpoint
    right: Endpoint


@dataclass
class _NodeDraft:
    node_type: str
    node_name: str
    properties: dict[str, Any] = field(default_factory=dict)
    edges: list[DatasetEdge] = field(default_factory=list)

    def add_values(self, key: str, values: Iterable[str]) -> None:
        existing = list(self.properties.get(key) or [])
        seen = set(existing)
        for value in values:
            if value and value not in seen:
                existing.append(value)
                seen.add(value)
        if existing:
            self.properties[key] = existing

    def add_edge(
        self,
        edge_type: str,
        target: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        incoming = dict(properties or {})
        for edge in self.edges:
            if edge.type != edge_type or edge.target != target:
                continue
            current = dict(edge.properties or {})
            if current == incoming:
                return
            raise ValueError(
                "conflicting edge properties for "
                f"{self.node_type}:{self.node_name} {edge_type} -> {target}: "
                f"{current!r} vs {incoming!r}"
            )
        self.edges.append(DatasetEdge(type=edge_type, target=target, properties=incoming))


@dataclass
class _FormulaGroup:
    name: str
    prescriptions: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)


def parse_endpoint(raw: object, *, field: str = "endpoint") -> Endpoint:
    """解析恰好一段 `类型\\t名称`；tab 数量不对或空段都显式失败。"""

    if not isinstance(raw, str) or raw.count("\t") != 1:
        raise ValueError(f"invalid endpoint {field}: {raw!r}; expected 类型\\t名称")
    kind, name = raw.split("\t", 1)
    kind = kind.strip()
    name = name.strip()
    if not kind or not name:
        raise ValueError(f"invalid endpoint {field}: {raw!r}; expected 类型\\t名称")
    return Endpoint(kind=kind, name=name)


def load_relations(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"expected JSON list in {path}")
    return payload


def clean_relations(
    herb_relations: list[dict[str, Any]],
    formula_relations: list[dict[str, Any]],
    *,
    batch_id: str = DEFAULT_BATCH_ID,
    source_id: str = SOURCE_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> list[DatasetRecord]:
    drafts: dict[tuple[str, str], _NodeDraft] = {}
    _apply_herb_triples(_parse_triples(herb_relations), drafts)
    _apply_formula_triples(_parse_triples(formula_relations), drafts)
    _ensure_edge_targets(drafts)
    records = [
        _to_record(
            draft,
            source_id=source_id,
            batch_id=batch_id,
            import_scope_key=import_scope_key,
        )
        for draft in drafts.values()
    ]
    records.sort(key=_record_sort_key)
    for record in records:
        record.validate_types()
    return records


def clean_relation_files(
    zhongyao_path: Path,
    fangji_path: Path,
    *,
    batch_id: str = DEFAULT_BATCH_ID,
    source_id: str = SOURCE_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> list[DatasetRecord]:
    return clean_relations(
        load_relations(zhongyao_path),
        load_relations(fangji_path),
        batch_id=batch_id,
        source_id=source_id,
        import_scope_key=import_scope_key,
    )


def write_clean_outputs(records: list[DatasetRecord], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records),
        encoding="utf-8",
    )
    stats = compute_stats(records)
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": len(records),
        "unit_count": stats["unit_count"],
    }


def _parse_triples(relations: list[dict[str, Any]]) -> list[Triple]:
    triples: list[Triple] = []
    for index, item in enumerate(relations):
        if not isinstance(item, dict):
            raise ValueError(f"invalid relation at index {index}: {item!r}")
        if set(item) != _RELATION_KEYS:
            raise ValueError(
                f"invalid relation keys at index {index}: {sorted(item)}; "
                "expected node_1/relation/node_2"
            )
        relation = item.get("relation")
        if not isinstance(relation, str) or not relation.strip():
            raise ValueError(f"unknown relation: {relation!r}")
        triples.append(
            Triple(
                relation=relation.strip(),
                left=parse_endpoint(item.get("node_1"), field="node_1"),
                right=parse_endpoint(item.get("node_2"), field="node_2"),
            )
        )
    return triples


def _apply_herb_triples(triples: list[Triple], drafts: dict[tuple[str, str], _NodeDraft]) -> None:
    for triple in triples:
        if triple.relation == REL_INCLUDE:
            continue
        if triple.relation == REL_ANOTHER_NAME:
            _require_kinds(triple, {KIND_HERB}, {KIND_ALIAS})
            herb = _ensure(drafts, NodeType.HERB.value, triple.left.name)
            herb.add_values(ALIASES_KEY, [triple.right.name])
            continue
        if triple.relation == REL_DISTRIBUTION:
            _require_kinds(triple, {KIND_HERB}, {KIND_AREA})
            herb = _ensure(drafts, NodeType.HERB.value, triple.left.name)
            herb.add_values(ORIGIN_KEY, [triple.right.name])
            continue
        mapping = _herb_edge_mapping(triple.relation)
        if mapping is None:
            raise ValueError(f"unknown relation: {triple.relation!r}")
        edge_type, target_type, left_kinds, right_kinds = mapping
        _require_kinds(triple, left_kinds, right_kinds)
        herb = _ensure(drafts, NodeType.HERB.value, triple.left.name)
        _ensure(drafts, target_type, triple.right.name)
        herb.add_edge(edge_type, triple.right.name)


def _apply_formula_triples(triples: list[Triple], drafts: dict[tuple[str, str], _NodeDraft]) -> None:
    groups, prescription_to_base = _index_formula_groups(triples)
    for group in groups.values():
        for prescription in group.prescriptions:
            _materialize_formula(drafts, prescription, group)

    index = 0
    while index < len(triples):
        triple = triples[index]
        if triple.relation in _IGNORED_RELATIONS:
            index += 1
            continue
        if triple.relation in {REL_ANOTHER_NAME, REL_FROM}:
            right_kind = KIND_ALIAS if triple.relation == REL_ANOTHER_NAME else KIND_SOURCE
            _require_kinds(triple, {KIND_FORMULA_NAME}, {right_kind})
            index += 1
            continue
        if triple.relation == REL_DOSE:
            raise ValueError(
                "uncontextualized dose "
                f"{triple.left.kind}\\t{triple.left.name} -> "
                f"{triple.right.kind}\\t{triple.right.name}"
            )
        if triple.relation == REL_COMPOSITION:
            _require_kinds(triple, {KIND_PRESCRIPTION}, {KIND_HERB})
            dosage = None
            if index + 1 < len(triples):
                nxt = triples[index + 1]
                if (
                    nxt.relation == REL_DOSE
                    and nxt.left.kind == KIND_HERB
                    and nxt.left.name == triple.right.name
                ):
                    _require_kinds(nxt, {KIND_HERB}, {KIND_DOSE})
                    dosage = nxt.right.name
                    index += 1
            group = _group_for_prescription(triple.left.name, groups, prescription_to_base)
            formula = _materialize_formula(drafts, triple.left.name, group)
            _ensure(drafts, NodeType.HERB.value, triple.right.name)
            props = {DOSAGE_KEY: dosage} if dosage else {}
            formula.add_edge(EdgeType.CONTAINS_HERB.value, triple.right.name, props)
            index += 1
            continue
        if triple.relation == REL_FUNCTIONS:
            _require_kinds(triple, {KIND_PRESCRIPTION}, {KIND_FORMULA_FUNCTION})
            group = _group_for_prescription(triple.left.name, groups, prescription_to_base)
            formula = _materialize_formula(drafts, triple.left.name, group)
            _ensure(drafts, NodeType.DISEASE.value, triple.right.name)
            formula.add_edge(EdgeType.TREATS.value, triple.right.name)
            index += 1
            continue
        raise ValueError(f"unknown relation: {triple.relation!r}")


def _index_formula_groups(triples: list[Triple]) -> tuple[dict[str, _FormulaGroup], dict[str, str]]:
    groups: dict[str, _FormulaGroup] = {}
    prescription_to_base: dict[str, str] = {}
    for triple in triples:
        if triple.relation == REL_PRESCRIPTION_TYPE:
            _require_kinds(triple, {KIND_FORMULA_NAME}, {KIND_PRESCRIPTION})
            group = groups.setdefault(triple.left.name, _FormulaGroup(name=triple.left.name))
            if triple.right.name not in group.prescriptions:
                group.prescriptions.append(triple.right.name)
            prescription_to_base[triple.right.name] = triple.left.name
            continue
        if triple.relation == REL_ANOTHER_NAME and triple.left.kind == KIND_FORMULA_NAME:
            _require_kinds(triple, {KIND_FORMULA_NAME}, {KIND_ALIAS})
            group = groups.setdefault(triple.left.name, _FormulaGroup(name=triple.left.name))
            if triple.right.name not in group.aliases:
                group.aliases.append(triple.right.name)
            continue
        if triple.relation == REL_FROM and triple.left.kind == KIND_FORMULA_NAME:
            _require_kinds(triple, {KIND_FORMULA_NAME}, {KIND_SOURCE})
            group = groups.setdefault(triple.left.name, _FormulaGroup(name=triple.left.name))
            if triple.right.name not in group.sources:
                group.sources.append(triple.right.name)
    return groups, prescription_to_base


def _group_for_prescription(
    prescription: str,
    groups: dict[str, _FormulaGroup],
    prescription_to_base: dict[str, str],
) -> _FormulaGroup | None:
    base = prescription_to_base.get(prescription)
    if base is None:
        match = _PRESCRIPTION_SUFFIX_RE.match(prescription)
        base = match.group(1) if match else None
    if base is None:
        return None
    return groups.get(base)


def _inheritable_sources(group: _FormulaGroup) -> list[str]:
    if not group.sources or not group.prescriptions:
        return []
    if len(group.prescriptions) == 1 or len(group.sources) == 1:
        return list(group.sources)
    return []


def _materialize_formula(
    drafts: dict[tuple[str, str], _NodeDraft],
    prescription: str,
    group: _FormulaGroup | None,
) -> _NodeDraft:
    formula = _ensure(drafts, NodeType.FORMULA.value, prescription)
    base_name = group.name if group is not None else _infer_formula_name(prescription)
    formula.properties[FORMULA_NAME_KEY] = base_name
    if group is not None:
        formula.add_values(ALIASES_KEY, group.aliases)
        for source_name in _inheritable_sources(group):
            _ensure(drafts, NodeType.SOURCE.value, source_name)
            formula.add_edge(EdgeType.ORIGINATED_FROM.value, source_name)
    return formula


def _infer_formula_name(prescription: str) -> str:
    match = _PRESCRIPTION_SUFFIX_RE.match(prescription)
    return match.group(1) if match else prescription


def _herb_edge_mapping(
    relation: str,
) -> tuple[str, str, set[str], set[str]] | None:
    table: dict[str, tuple[str, str, set[str], set[str]]] = {
        REL_FUNCTIONS: (
            EdgeType.HAS_EFFICACY.value,
            NodeType.EFFICACY.value,
            {KIND_HERB},
            {KIND_FUNCTION},
        ),
        REL_ATTENDING: (
            EdgeType.TREATS.value,
            NodeType.DISEASE.value,
            {KIND_HERB},
            {KIND_INDICATION},
        ),
        REL_FOUR_PROPERTIES: (
            EdgeType.HAS_FLAVOR.value,
            NodeType.FLAVOR.value,
            {KIND_HERB},
            {KIND_QI},
        ),
        REL_FIVE_FLAVORS: (
            EdgeType.HAS_FLAVOR.value,
            NodeType.FLAVOR.value,
            {KIND_HERB},
            {KIND_FLAVOR},
        ),
        REL_CHANNEL: (
            EdgeType.ENTERS_MERIDIAN.value,
            NodeType.MERIDIAN.value,
            {KIND_HERB},
            {KIND_MERIDIAN},
        ),
        REL_FROM: (
            EdgeType.ORIGINATED_FROM.value,
            NodeType.SOURCE.value,
            {KIND_HERB},
            {KIND_SOURCE},
        ),
    }
    return table.get(relation)


def _require_kinds(triple: Triple, left_kinds: set[str], right_kinds: set[str]) -> None:
    if triple.left.kind not in left_kinds or triple.right.kind not in right_kinds:
        raise ValueError(
            "invalid endpoint types for "
            f"{triple.relation}: {triple.left.kind}\\t{triple.left.name} -> "
            f"{triple.right.kind}\\t{triple.right.name}"
        )


def _ensure(drafts: dict[tuple[str, str], _NodeDraft], node_type: str, node_name: str) -> _NodeDraft:
    key = (node_type, node_name)
    draft = drafts.get(key)
    if draft is None:
        draft = _NodeDraft(node_type=node_type, node_name=node_name)
        drafts[key] = draft
    return draft


def _ensure_edge_targets(drafts: dict[tuple[str, str], _NodeDraft]) -> None:
    pending: list[tuple[str, str]] = []
    for draft in drafts.values():
        for edge in draft.edges:
            target_type = _EDGE_TARGET_TYPE.get(edge.type)
            if target_type is None:
                raise ValueError(f"unsupported edge type: {edge.type}")
            pending.append((target_type, edge.target))
    for node_type, node_name in pending:
        _ensure(drafts, node_type, node_name)


def _to_record(
    draft: _NodeDraft,
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> DatasetRecord:
    unit_id = f"{draft.node_type}:{draft.node_name}"
    properties: dict[str, Any] = {
        "import_source_id": source_id,
        "import_batch_id": batch_id,
        "import_unit_id": unit_id,
    }
    for key, value in draft.properties.items():
        if value not in (None, "", [], {}):
            properties[key] = value
    record = DatasetRecord(
        source_id=source_id,
        batch_id=batch_id,
        unit_id=unit_id,
        unit_title=draft.node_name,
        processor=PROCESSOR,
        node_type=draft.node_type,
        node_name=draft.node_name,
        source=source_id,
        status="pending",
        prompt_hash=PROMPT_HASH,
        import_scope_key=import_scope_key,
        properties=properties,
        edges=_sorted_edges(draft.edges),
    )
    record.validate_types()
    return record


def _sorted_edges(edges: list[DatasetEdge]) -> list[DatasetEdge]:
    return sorted(
        edges,
        key=lambda edge: (
            _EDGE_TYPE_RANK.get(edge.type, len(_EDGE_TYPE_RANK)),
            edge.type,
            edge.target,
            str((edge.properties or {}).get(DOSAGE_KEY) or ""),
        ),
    )


def _record_sort_key(record: DatasetRecord) -> tuple[int, str, str]:
    return (
        _NODE_TYPE_RANK.get(record.node_type, len(_NODE_TYPE_RANK)),
        record.node_type,
        record.node_name,
    )
