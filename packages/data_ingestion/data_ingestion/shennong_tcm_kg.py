"""清洗 ShenNong TCM-KG 三元组，保留确定映射并隔离化学与跨语言候选。"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.text_normalize import canonicalize_name, nfkc_strip

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "shennong-tcm-kg"
IMPORT_SCOPE_KEY = "github:michael-wzhu/ShenNong-TCM-LLM:src/TCM-KG_triples.txt"
DEFAULT_BATCH_ID = "2026-08-19-shennong-tcm-kg-v1"
PROCESSOR = "shennong_tcm_kg"
PROMPT_HASH = prompt_hash_for(Path(__file__))

REL_SYNDROME = "证候"
REL_HERB = "中药"
REL_METHOD = "治法"
REL_FUNCTION = "功能"
REL_MERIDIAN = "归经"
REL_FLAVOR = "药味"
REL_NATURE = "药性"
REL_TCM_MODERN_SYMPTOM = "TS_MS"
REL_SYMMAP_CHEMICAL = "symmap_chemical"
REL_CHEMICAL_MODERN = "chemical_MM"

ATTRIBUTE_RELATIONS = {
    "部位": "location",
    "贮藏": "storage_text",
    "用量": "quantity",
    "毒性": "toxicity",
    "注意": "caution_text",
    "用法": "usage_text",
}
EDGE_RELATIONS = {
    REL_SYNDROME,
    REL_HERB,
    REL_METHOD,
    REL_FUNCTION,
    REL_MERIDIAN,
    REL_FLAVOR,
    REL_NATURE,
}
EXCLUDED_CHEMICAL_RELATIONS = {REL_SYMMAP_CHEMICAL, REL_CHEMICAL_MODERN}
KNOWN_RELATIONS = (
    EDGE_RELATIONS
    | set(ATTRIBUTE_RELATIONS)
    | EXCLUDED_CHEMICAL_RELATIONS
    | {REL_TCM_MODERN_SYMPTOM}
)
HERB_HEAD_RELATIONS = {REL_FUNCTION, REL_MERIDIAN, REL_FLAVOR, REL_NATURE} | set(
    ATTRIBUTE_RELATIONS
)
CLINICAL_HEAD_RELATIONS = {REL_SYNDROME, REL_HERB, REL_METHOD}
_MULTIVALUE_RE = re.compile(r"[、，,]")
_NODE_TYPE_RANK = {item.value: index for index, item in enumerate(NodeType)}
_EDGE_TYPE_RANK = {item.value: index for index, item in enumerate(EdgeType)}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root() / ".cache/github/michael-wzhu/ShenNong-TCM-LLM/src/TCM-KG_triples.txt"
)


@dataclass(frozen=True, slots=True)
class Triple:
    head: str
    tail: str
    relation: str
    line_no: int
    source_file: str


@dataclass
class _NodeDraft:
    node_type: str
    node_name: str
    properties: dict[str, Any] = field(default_factory=dict)
    edges: list[DatasetEdge] = field(default_factory=list)
    evidence_refs: set[str] = field(default_factory=set)

    def add_value(self, key: str, value: str) -> None:
        values = list(self.properties.get(key) or [])
        if value and value not in values:
            values.append(value)
        if values:
            self.properties[key] = values

    def add_edge(self, edge_type: str, target: str) -> None:
        if not any(edge.type == edge_type and edge.target == target for edge in self.edges):
            self.edges.append(DatasetEdge(type=edge_type, target=target))


def parse_lines(
    lines: Iterable[str], *, source_file: str = "TCM-KG_triples.txt"
) -> list[Triple]:
    triples: list[Triple] = []
    for line_no, raw in enumerate(lines, start=1):
        line = raw.rstrip("\r\n")
        columns = line.split("\t")
        if len(columns) != 3:
            raise ValueError(
                f"invalid line {line_no}: expected head<TAB>tail<TAB>relation"
            )
        head, tail, relation = (nfkc_strip(value) for value in columns)
        if not head or not tail or not relation:
            raise ValueError(f"invalid line {line_no}: empty field")
        if relation not in KNOWN_RELATIONS:
            raise ValueError(f"unknown relation at line {line_no}: {relation!r}")
        triples.append(
            Triple(
                head=head,
                tail=tail,
                relation=relation,
                line_no=line_no,
                source_file=source_file,
            )
        )
    return triples


def load_triples(path: Path) -> list[Triple]:
    return parse_lines(path.read_text(encoding="utf-8").splitlines(), source_file=path.name)


def clean_triples(
    triples: list[Triple],
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    relation_counts = Counter(triple.relation for triple in triples)
    unique: list[Triple] = []
    seen_rows: set[tuple[str, str, str]] = set()
    duplicate_rows = 0
    for triple in triples:
        key = (triple.head, triple.tail, triple.relation)
        if key in seen_rows:
            duplicate_rows += 1
            continue
        seen_rows.add(key)
        unique.append(triple)

    source_labeled_syndrome_names = {
        canonicalize_name(triple.tail, NodeType.DISEASE.value)
        for triple in unique
        if triple.relation == REL_SYNDROME
    }
    syndrome_relation_heads = {
        canonicalize_name(triple.head, NodeType.DISEASE.value)
        for triple in unique
        if triple.relation == REL_SYNDROME
    }
    clinical_names = {
        canonicalize_name(triple.head, NodeType.DISEASE.value)
        for triple in unique
        if triple.relation in CLINICAL_HEAD_RELATIONS
    } | source_labeled_syndrome_names
    herb_names = {
        canonicalize_name(triple.tail, NodeType.HERB.value)
        for triple in unique
        if triple.relation == REL_HERB
    } | {
        canonicalize_name(triple.head, NodeType.HERB.value)
        for triple in unique
        if triple.relation in HERB_HEAD_RELATIONS
    }

    drafts: dict[tuple[str, str], _NodeDraft] = {}
    decisions: Counter[str] = Counter()
    self_edges_skipped = 0
    function_clinical_overlap = 0
    quality_samples: dict[str, list[dict[str, Any]]] = {
        "quarantined_external_mapping": [],
        "function_clinical_overlap": [],
    }

    def ensure(node_type: NodeType, raw_name: str, triple: Triple) -> _NodeDraft:
        name = canonicalize_name(raw_name, node_type.value)
        key = (node_type.value, name)
        draft = drafts.setdefault(key, _NodeDraft(node_type.value, name))
        draft.evidence_refs.add(f"{triple.source_file}:{triple.line_no}")
        if node_type == NodeType.DISEASE:
            draft.properties["tcm_type"] = (
                "来源标注证候"
                if name in source_labeled_syndrome_names
                else "未分类临床概念"
            )
        return draft

    for triple in unique:
        relation = triple.relation
        if relation in EXCLUDED_CHEMICAL_RELATIONS:
            decisions["excluded_chemical"] += 1
            continue
        if relation == REL_TCM_MODERN_SYMPTOM:
            decisions["quarantined_external_mapping"] += 1
            _append_sample(
                quality_samples["quarantined_external_mapping"],
                triple,
                reason="跨语言映射不参与实体合并",
            )
            continue
        if relation in ATTRIBUTE_RELATIONS:
            herb = ensure(NodeType.HERB, triple.head, triple)
            herb.add_value(ATTRIBUTE_RELATIONS[relation], triple.tail)
            decisions["mapped_property"] += 1
            continue

        if relation == REL_SYNDROME:
            clinical = ensure(NodeType.DISEASE, triple.head, triple)
            syndrome = ensure(NodeType.DISEASE, triple.tail, triple)
            if clinical.node_name == syndrome.node_name:
                self_edges_skipped += 1
                decisions["self_edge_skipped"] += 1
            else:
                clinical.add_edge(EdgeType.RELATED_SYNDROME.value, syndrome.node_name)
                decisions["mapped_edge"] += 1
            continue
        if relation == REL_HERB:
            clinical = ensure(NodeType.DISEASE, triple.head, triple)
            herb = ensure(NodeType.HERB, triple.tail, triple)
            clinical.add_edge(EdgeType.RELATED_HERB.value, herb.node_name)
            decisions["mapped_edge"] += 1
            continue
        if relation == REL_METHOD:
            clinical = ensure(NodeType.DISEASE, triple.head, triple)
            method = ensure(NodeType.TREATMENT_METHOD, triple.tail, triple)
            clinical.add_edge(EdgeType.RELATED_TREATMENT_METHOD.value, method.node_name)
            decisions["mapped_edge"] += 1
            continue
        if relation == REL_FUNCTION:
            herb = ensure(NodeType.HERB, triple.head, triple)
            if canonicalize_name(triple.tail, NodeType.DISEASE.value) in clinical_names:
                function_clinical_overlap += 1
                _append_sample(
                    quality_samples["function_clinical_overlap"],
                    triple,
                    reason="源标为功能，但名称也出现在临床概念集合",
                )
                decisions["quarantined_function_clinical_overlap"] += 1
                continue
            efficacy = ensure(NodeType.EFFICACY, triple.tail, triple)
            herb.add_edge(EdgeType.HAS_EFFICACY.value, efficacy.node_name)
            decisions["mapped_edge"] += 1
            continue
        if relation == REL_MERIDIAN:
            herb = ensure(NodeType.HERB, triple.head, triple)
            for value in _split_values(triple.tail):
                meridian = ensure(NodeType.MERIDIAN, value, triple)
                herb.add_edge(EdgeType.ENTERS_MERIDIAN.value, meridian.node_name)
            decisions["mapped_edge"] += 1
            continue
        if relation in {REL_FLAVOR, REL_NATURE}:
            herb = ensure(NodeType.HERB, triple.head, triple)
            for value in _split_values(triple.tail):
                flavor = ensure(NodeType.FLAVOR, value, triple)
                herb.add_edge(EdgeType.HAS_FLAVOR.value, flavor.node_name)
            decisions["mapped_edge"] += 1
            continue
        raise AssertionError(f"unhandled relation: {relation}")

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
    report = {
        "source_relation_counts": dict(sorted(relation_counts.items())),
        "decision_counts": dict(decisions),
        "duplicate_rows": duplicate_rows,
        "self_edges_skipped": self_edges_skipped,
        "role_counts": {
            "source_labeled_syndrome_names": len(source_labeled_syndrome_names),
            "unclassified_clinical_names": len(clinical_names - source_labeled_syndrome_names),
            "dual_source_syndrome_head_names": len(
                source_labeled_syndrome_names & syndrome_relation_heads
            ),
            "herb_names": len(herb_names),
            "cross_type_same_name": len(clinical_names & herb_names),
        },
        "semantic_warning_counts": {
            "function_clinical_overlap": function_clinical_overlap,
        },
        "quality_samples": quality_samples,
    }
    return records, report


def clean_file(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    return clean_triples(
        load_triples(path),
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
    )


def write_clean_outputs(
    records: list[DatasetRecord], report: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records),
        encoding="utf-8",
    )
    stats = {**compute_stats(records), **report}
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": len(records),
        "unit_count": stats["unit_count"],
    }


def _append_sample(
    samples: list[dict[str, Any]], triple: Triple, *, reason: str, limit: int = 20
) -> None:
    if len(samples) < limit:
        samples.append(
            {
                "line": triple.line_no,
                "head": triple.head,
                "tail": triple.tail,
                "relation": triple.relation,
                "reason": reason,
            }
        )


def _split_values(value: str) -> list[str]:
    return [item for part in _MULTIVALUE_RE.split(value) if (item := nfkc_strip(part))]


def _to_record(
    draft: _NodeDraft,
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> DatasetRecord:
    unit_id = f"{draft.node_type}:{draft.node_name}"
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
        evidence_refs=sorted(draft.evidence_refs, key=_evidence_sort_key),
        prompt_hash=PROMPT_HASH,
        import_scope_key=import_scope_key,
        properties={
            "import_source_id": source_id,
            "import_batch_id": batch_id,
            "import_unit_id": unit_id,
            **draft.properties,
        },
        edges=sorted(
            draft.edges,
            key=lambda edge: (
                _EDGE_TYPE_RANK.get(edge.type, len(_EDGE_TYPE_RANK)),
                edge.type,
                edge.target,
            ),
        ),
    )
    record.validate_types()
    return record


def _evidence_sort_key(value: str) -> tuple[str, int]:
    path, _, line = value.rpartition(":")
    return (path, int(line))


def _record_sort_key(record: DatasetRecord) -> tuple[int, str, str]:
    return (
        _NODE_TYPE_RANK.get(record.node_type, len(_NODE_TYPE_RANK)),
        record.node_type,
        record.node_name,
    )
