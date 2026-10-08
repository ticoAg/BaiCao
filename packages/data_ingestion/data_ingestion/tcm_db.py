"""只读清洗 tcm-db 的核心中医药实体与显式关系。"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from pathlib import Path
from typing import Any

from graph_schema.constants import EdgeType, NodeType
from graph_schema.text_normalize import canonicalize_name, nfkc_strip

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcm-db"
IMPORT_SCOPE_KEY = "github:xiaogege6697/tcm-db:tcm_knowledge.db"
DEFAULT_BATCH_ID = "2026-08-19-tcm-db-v1"
PROCESSOR = "tcm_db"
PROMPT_HASH = prompt_hash_for(Path(__file__))

_PUNCTUATED_LONG_NAME_RE = re.compile(r"[。，.,；;：:！!？?]")
_FORMULA_SPLIT_RE = re.compile(r"[、和与及]")
_FORMULA_SUFFIX_RE = re.compile(r"[汤丸散丹膏饮]")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root() / ".cache/github/xiaogege6697/tcm-db/tcm_knowledge.db"
)

ENTITY_SPECS: dict[str, tuple[NodeType, tuple[tuple[str, str], ...]]] = {
    "herbs": (
        NodeType.HERB,
        (
            ("alias", "alias"),
            ("category", "category"),
            ("nature", "nature"),
            ("flavor", "flavor_text"),
            ("toxicity", "toxicity"),
            ("meridian_tropism", "meridian_tropism"),
            ("origin", "origin"),
            ("indication", "indication"),
            ("bencao_raw", "bencao_raw"),
            ("commentary", "commentary"),
            ("raw_path", "raw_path"),
            ("source_repo", "source_repo"),
        ),
    ),
    "formulas": (
        NodeType.FORMULA,
        (
            ("alias", "alias"),
            ("source_book", "source_book"),
            ("chapter", "chapter"),
            ("six_channel", "six_channel"),
            ("syndrome", "syndrome_text"),
            ("indication", "indication"),
            ("composition", "composition_text"),
            ("dosage", "dosage"),
            ("contraindication", "contraindication"),
            ("differentiation", "differentiation"),
            ("lesson_ref", "lesson_ref"),
            ("is_high_risk", "is_high_risk"),
            ("commentary", "commentary"),
            ("raw_path", "raw_path"),
            ("source_repo", "source_repo"),
        ),
    ),
    "symptoms": (
        NodeType.SYMPTOM,
        (
            ("category", "category"),
            ("description", "description"),
            ("first_gateway", "first_gateway"),
            ("target_module", "target_module"),
            ("required_questions", "required_questions"),
            ("differential", "differential"),
        ),
    ),
    "syndromes": (
        NodeType.DISEASE,
        (
            ("six_channel", "six_channel"),
            ("eight_principles", "eight_principles"),
            ("location", "location"),
            ("core_symptoms", "core_symptoms"),
            ("key_differentiation", "key_differentiation"),
            ("representative_formulas", "representative_formulas"),
            ("contraindication", "contraindication"),
            ("course_ref", "course_ref"),
            ("description", "description"),
        ),
    ),
    "treatment_methods": (
        NodeType.TREATMENT_METHOD,
        (
            ("category", "category"),
            ("description", "description"),
            ("related_pathomechanism", "related_pathomechanism"),
            ("related_herbs", "related_herbs"),
            ("related_acupoints", "related_acupoints"),
            ("raw_path", "raw_path"),
            ("source_repo", "source_repo"),
        ),
    ),
}

RELATION_COLUMNS: dict[str, tuple[str, ...]] = {
    "formula_herbs": (
        "formula_id",
        "herb_id",
        "role",
        "dosage_in_formula",
        "note",
    ),
    "formula_syndromes": ("formula_id", "syndrome_id", "relevance"),
    "syndrome_symptoms": ("syndrome_id", "symptom_id", "is_key"),
}


def open_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _required_schema() -> dict[str, set[str]]:
    schema = {
        table: {"id", "name", *(column for column, _ in fields)}
        for table, (_node_type, fields) in ENTITY_SPECS.items()
    }
    schema.update({table: set(columns) for table, columns in RELATION_COLUMNS.items()})
    return schema


def validate_schema(conn: sqlite3.Connection) -> set[str]:
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    for table, required_columns in _required_schema().items():
        if table not in tables:
            raise ValueError(f"missing required table: {table}")
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if missing := sorted(required_columns - columns):
            raise ValueError(f"{table} missing required columns: {', '.join(missing)}")
    return tables


def formula_warning_reasons(name: str) -> list[str]:
    reasons: list[str] = []
    if len(name) > 8 and _PUNCTUATED_LONG_NAME_RE.search(name):
        reasons.append("descriptive_name")
    parts = _FORMULA_SPLIT_RE.split(name)
    if sum(bool(_FORMULA_SUFFIX_RE.search(part)) for part in parts) >= 2:
        reasons.append("multiple_entities")
    return reasons


def _clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return nfkc_strip(value) or None
    return value


def _row_properties(
    row: sqlite3.Row, fields: tuple[tuple[str, str], ...]
) -> dict[str, Any]:
    properties = {
        target: value
        for source, target in fields
        if (value := _clean_value(row[source])) is not None
    }
    if "is_high_risk" in properties:
        properties["is_high_risk"] = bool(properties["is_high_risk"])
    return properties


def _merge_properties(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    merged: dict[str, Any] = {}
    conflicts: dict[str, list[Any]] = {}
    for key in sorted({key for row in rows for key in row}):
        values: list[Any] = []
        for row in rows:
            if key in row and row[key] not in values:
                values.append(row[key])
        if len(values) > 1:
            conflicts[key] = values
        elif values:
            merged[key] = values[0]
    return merged, conflicts


def _locator(table: str, row_id: int) -> str:
    return f"tcm_knowledge.db:{table}:{row_id}"


def _make_record(
    node_type: NodeType,
    name: str,
    properties: dict[str, Any],
    evidence_refs: list[str],
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> DatasetRecord:
    unit_id = f"{node_type.value}:{name}"
    record = DatasetRecord(
        source_id=source_id,
        batch_id=batch_id,
        unit_id=unit_id,
        unit_title=name,
        processor=PROCESSOR,
        node_type=node_type.value,
        node_name=name,
        source=source_id,
        status="pending",
        evidence_refs=evidence_refs,
        prompt_hash=PROMPT_HASH,
        import_scope_key=import_scope_key,
        properties={
            "import_source_id": source_id,
            "import_batch_id": batch_id,
            "import_unit_id": unit_id,
            **properties,
        },
    )
    record.validate_types()
    return record


def _load_entities(
    conn: sqlite3.Connection,
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> tuple[
    list[DatasetRecord],
    dict[tuple[str, int], DatasetRecord],
    dict[str, int],
    Counter[str],
    dict[str, list[dict[str, Any]]],
]:
    records: list[DatasetRecord] = []
    row_records: dict[tuple[str, int], DatasetRecord] = {}
    source_counts: dict[str, int] = {}
    quarantine: Counter[str] = Counter()
    samples: dict[str, list[dict[str, Any]]] = {
        "formula_name_warnings": [],
        "conflicting_duplicates": [],
        "cross_type_same_name_edges": [],
        "quarantined_endpoint_relations": [],
    }

    for table, (node_type, fields) in ENTITY_SPECS.items():
        columns = ("id", "name", *(source for source, _target in fields))
        rows = list(
            conn.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY id")
        )
        source_counts[table] = len(rows)
        groups: dict[str, list[tuple[sqlite3.Row, dict[str, Any]]]] = defaultdict(list)
        for row in rows:
            name = canonicalize_name(str(row["name"] or ""), node_type.value)
            if not name:
                raise ValueError(f"{table}:{row['id']} has empty name")
            if table == "formulas" and (reasons := formula_warning_reasons(name)):
                quarantine["formula_name_warning_rows"] += 1
                quarantine["formula_name_warning_events"] += len(reasons)
                samples["formula_name_warnings"].append(
                    {"id": row["id"], "name": name, "reasons": reasons}
                )
                continue
            groups[name].append((row, _row_properties(row, fields)))

        for name, group in groups.items():
            properties, conflicts = _merge_properties([item[1] for item in group])
            if conflicts:
                quarantine["conflicting_duplicate_groups"] += 1
                quarantine["conflicting_duplicate_rows"] += len(group)
                samples["conflicting_duplicates"].append(
                    {
                        "table": table,
                        "name": name,
                        "ids": [item[0]["id"] for item in group],
                        "conflicting_fields": sorted(conflicts),
                    }
                )
                continue
            if table == "syndromes":
                properties["tcm_type"] = "来源标注证候"
            evidence_refs = [_locator(table, item[0]["id"]) for item in group]
            record = _make_record(
                node_type,
                name,
                properties,
                evidence_refs,
                source_id=source_id,
                batch_id=batch_id,
                import_scope_key=import_scope_key,
            )
            records.append(record)
            for row, _properties in group:
                row_records[(table, row["id"])] = record

    return records, row_records, source_counts, quarantine, samples


def _add_edge(
    record: DatasetRecord,
    edge_type: EdgeType,
    target: DatasetRecord,
    *,
    evidence_ref: str,
    dosage: str | None = None,
) -> None:
    properties = {"evidence_ref": evidence_ref}
    if dosage:
        properties["dosage"] = dosage
    record.edges.append(
        DatasetEdge(type=edge_type.value, target=target.node_name, properties=properties)
    )
    record.evidence_refs.append(evidence_ref)


def _load_relations(
    conn: sqlite3.Connection,
    row_records: dict[tuple[str, int], DatasetRecord],
    quarantine: Counter[str],
    samples: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, int], dict[str, int]]:
    source_counts: dict[str, int] = {}
    mapped: Counter[str] = Counter()
    specs = (
        (
            "formula_herbs",
            "formulas",
            "formula_id",
            "herbs",
            "herb_id",
            EdgeType.CONTAINS_HERB,
        ),
        (
            "formula_syndromes",
            "formulas",
            "formula_id",
            "syndromes",
            "syndrome_id",
            EdgeType.RELATED_SYNDROME,
        ),
        (
            "syndrome_symptoms",
            "syndromes",
            "syndrome_id",
            "symptoms",
            "symptom_id",
            EdgeType.RELATED_SYMPTOM,
        ),
    )
    for table, source_table, source_key, target_table, target_key, edge_type in specs:
        columns = RELATION_COLUMNS[table]
        rows = list(
            conn.execute(
                f"SELECT rowid AS _rowid, {', '.join(columns)} FROM {table} ORDER BY rowid"
            )
        )
        source_counts[table] = len(rows)
        for row in rows:
            source = row_records.get((source_table, row[source_key]))
            target = row_records.get((target_table, row[target_key]))
            evidence_ref = _locator(table, row["_rowid"])
            if source is None or target is None:
                quarantine["quarantined_endpoint_relations"] += 1
                samples["quarantined_endpoint_relations"].append(
                    {"evidence_ref": evidence_ref, "table": table}
                )
                continue
            if table == "syndrome_symptoms" and source.node_name == target.node_name:
                quarantine["cross_type_same_name_edges"] += 1
                samples["cross_type_same_name_edges"].append(
                    {
                        "evidence_ref": evidence_ref,
                        "name": source.node_name,
                        "reason": "疾病名称误入症状表，不保留同名类型边",
                    }
                )
                continue
            dosage = (
                _clean_value(row["dosage_in_formula"])
                if table == "formula_herbs"
                else None
            )
            _add_edge(
                source,
                edge_type,
                target,
                evidence_ref=evidence_ref,
                dosage=dosage,
            )
            mapped[edge_type.value] += 1
    for record in row_records.values():
        record.evidence_refs = sorted(set(record.evidence_refs))
        record.edges.sort(key=lambda edge: (edge.type, edge.target))
    return source_counts, dict(mapped)


def clean_file(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    with closing(open_readonly(path)) as conn:
        tables = validate_schema(conn)
        records, row_records, entity_counts, quarantine, samples = _load_entities(
            conn,
            source_id=source_id,
            batch_id=batch_id,
            import_scope_key=import_scope_key,
        )
        relation_counts, mapped_relations = _load_relations(
            conn, row_records, quarantine, samples
        )

    symptom_names = {r.node_name for r in records if r.node_type == NodeType.SYMPTOM}
    syndrome_names = {r.node_name for r in records if r.node_type == NodeType.DISEASE}
    records.sort(key=lambda record: (list(NodeType).index(NodeType(record.node_type)), record.node_name))
    consumed = set(ENTITY_SPECS) | set(RELATION_COLUMNS)
    report = {
        "publish": False,
        "license_status": "mixed_unlicensed_upstreams",
        "database_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "consumed_tables": sorted(consumed),
        "ignored_tables": sorted(tables - consumed - {"sqlite_sequence"}),
        "source_table_counts": entity_counts,
        "source_relation_counts": relation_counts,
        "mapped_relation_counts": mapped_relations,
        "cross_type_same_name_names": sorted(symptom_names & syndrome_names),
        "quarantine_counts": dict(sorted(quarantine.items())),
        "quality_samples": samples,
    }
    return records, report


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
        "edge_count": sum(len(record.edges) for record in records),
    }
