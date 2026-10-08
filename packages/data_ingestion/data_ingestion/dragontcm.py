"""只读清洗 DragonTCM 的药材、方剂、疾病、临床表现和显式关系。"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq  # ty: ignore[unresolved-import]
from graph_schema.constants import EdgeType, NodeType
from graph_schema.text_normalize import name_surface_key, nfkc_strip

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "dragontcm"
SOURCE_REVISION = "57e19c6bb7aaf62feacbba97aa84d9baecd05582"
IMPORT_SCOPE_KEY = f"huggingface:f-galkin/DragonTCM@{SOURCE_REVISION}"
DEFAULT_BATCH_ID = "2026-08-19-dragontcm-v1"
PROCESSOR = "dragontcm"
PROMPT_HASH = prompt_hash_for(Path(__file__))

PARQUET_FILES = {
    "herbs": "herbs/train-00000-of-00001.parquet",
    "formulas": "formulas/train-00000-of-00001.parquet",
    "conditions": "conditions/train-00000-of-00001.parquet",
    "relations": "relations/train-00000-of-00001.parquet",
}
REQUIRED_COLUMNS = {
    "herbs": {
        "name",
        "synonyms",
        "category",
        "properties",
        "actions",
        "contraindications",
        "interactions",
        "incompatibility",
        "notes",
        "dosage",
        "indications",
    },
    "formulas": {
        "name",
        "synonyms",
        "actions",
        "syndromes",
        "treats",
        "contraindications",
        "notes",
        "composition",
    },
    "conditions": {
        "name",
        "synonyms",
        "symptoms",
        "description",
        "herb_formulas",
        "points",
    },
    "relations": {
        "source",
        "target",
        "source_type",
        "target_type",
        "edge_type",
        "dosage",
    },
}
JSON_FIELDS: dict[str, dict[str, type[list[Any]] | type[dict[str, Any]]]] = {
    "herbs": {
        "synonyms": list,
        "category": list,
        "properties": dict,
        "actions": list,
        "contraindications": list,
        "interactions": list,
        "incompatibility": list,
        "notes": list,
        "dosage": list,
        "indications": list,
    },
    "formulas": {
        "synonyms": list,
        "actions": list,
        "syndromes": list,
        "treats": list,
        "contraindications": list,
        "notes": list,
        "composition": dict,
    },
    "conditions": {
        "synonyms": list,
        "symptoms": list,
        "herb_formulas": list,
        "points": list,
    },
}
ALLOWED_RELATION_SHAPES = {
    ("formula", "herb", "contains"),
    ("condition", "formula", "treats"),
    ("condition", "herb", "treats"),
}

_CONDITION_TAG_RE = re.compile(r"\(([^()]*)\)\s*$")
_SNOMED_RE = re.compile(r"SNOMED:([1-9][0-9]{5,17})", re.IGNORECASE)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_DIR = repo_root() / ".cache/huggingface/f-galkin/DragonTCM"


@dataclass
class _Draft:
    node_type: str
    node_name: str
    properties: dict[str, Any]
    evidence_refs: set[str] = field(default_factory=set)
    edges: dict[tuple[str, str], DatasetEdge] = field(default_factory=dict)

    def add_edge(
        self,
        edge_type: EdgeType,
        target: str,
        evidence_ref: str,
        **properties: Any,
    ) -> bool:
        key = (edge_type.value, target)
        if key in self.edges:
            existing = {
                name: value
                for name, value in self.edges[key].properties.items()
                if name != "evidence_ref"
            }
            if existing != properties:
                raise ValueError(
                    f"conflicting edge properties for {self.node_name} "
                    f"{edge_type.value} {target}"
                )
            self.evidence_refs.add(evidence_ref)
            return False
        self.edges[key] = DatasetEdge(
            type=edge_type.value,
            target=target,
            properties={"evidence_ref": evidence_ref, **properties},
        )
        self.evidence_refs.add(evidence_ref)
        return True


@dataclass
class _Condition:
    row_no: int
    name: str
    key: str
    semantic_tag: str
    snomed_id: str | None
    aliases: list[str]
    payload: dict[str, Any]
    quarantine_reason: str | None = None


@dataclass(frozen=True)
class _EntityGroup:
    members: tuple[tuple[int, dict[str, Any], dict[str, Any]], ...]
    display_name: str
    values: dict[str, Any]
    conflicting_fields: tuple[str, ...]


def _identity_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _display_name(value: Any, locator: str) -> str:
    name = nfkc_strip(str(value or ""))
    if not name:
        raise ValueError(f"{locator} has empty name")
    return name


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _compact_json_or_none(value: Any) -> str | None:
    return _compact_json(value) if value not in (None, "", [], {}) else None


def _dedupe_strings(values: list[Any], locator: str) -> list[str]:
    result: list[str] = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, str):
            raise ValueError(f"{locator}:{index} must be a string")
        cleaned = nfkc_strip(value)
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result


def _read_tables(input_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    if not input_dir.is_dir():
        raise FileNotFoundError(input_dir)
    tables: dict[str, list[dict[str, Any]]] = {}
    hashes: dict[str, str] = {}
    for table_name, relative in PARQUET_FILES.items():
        path = input_dir / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        parquet = pq.ParquetFile(path)
        columns = set(parquet.schema_arrow.names)
        if missing := sorted(REQUIRED_COLUMNS[table_name] - columns):
            raise ValueError(
                f"{relative} missing required columns: {', '.join(missing)}"
            )
        tables[table_name] = parquet.read().to_pylist()
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in ("README.md", "4Nov2024_connector.json.gz"):
        path = input_dir / relative
        if path.is_file():
            hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return tables, hashes


def _parse_json_fields(
    tables: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, int]]]:
    parsed: dict[str, list[dict[str, Any]]] = {}
    item_counts: dict[str, dict[str, int]] = {}
    for table_name, specs in JSON_FIELDS.items():
        parsed_rows: list[dict[str, Any]] = []
        counts: dict[str, int] = {}
        for row_no, row in enumerate(tables[table_name], start=1):
            parsed_row: dict[str, Any] = {}
            for field_name, expected_type in specs.items():
                raw = row[field_name]
                if not isinstance(raw, str):
                    raise ValueError(
                        f"{table_name}:{row_no}:{field_name} must be JSON text"
                    )
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"{table_name}:{row_no}:{field_name} invalid JSON"
                    ) from exc
                if not isinstance(value, expected_type):
                    raise ValueError(
                        f"{table_name}:{row_no}:{field_name} must decode to "
                        f"{expected_type.__name__}"
                    )
                parsed_row[field_name] = value
                counts[field_name] = counts.get(field_name, 0) + len(value)
            parsed_rows.append(parsed_row)
        parsed[table_name] = parsed_rows
        item_counts[table_name] = counts
    return parsed, item_counts


def _unique_index(
    rows: list[dict[str, Any]], table_name: str
) -> dict[str, tuple[int, str]]:
    index: dict[str, tuple[int, str]] = {}
    for row_no, row in enumerate(rows, start=1):
        name = _display_name(row["name"], f"{table_name}:{row_no}")
        key = _identity_key(name)
        if key in index:
            prior_row, prior_name = index[key]
            raise ValueError(
                f"{table_name} ambiguous identity key {key!r}: "
                f"rows {prior_row} ({prior_name!r}) and {row_no} ({name!r})"
            )
        index[key] = (row_no, name)
    return index


def _entity_groups(
    rows: list[dict[str, Any]],
    parsed_rows: list[dict[str, Any]],
    table_name: str,
) -> list[_EntityGroup]:
    grouped: dict[str, list[tuple[int, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
    for row_no, (row, parsed) in enumerate(zip(rows, parsed_rows, strict=True), start=1):
        name = _display_name(row["name"], f"{table_name}:{row_no}")
        grouped[name_surface_key(name).casefold()].append((row_no, row, parsed))

    result: list[_EntityGroup] = []
    for members in grouped.values():
        fields = members[0][2]
        merged: dict[str, Any] = {}
        conflicts: list[str] = []
        for field_name in fields:
            values: list[Any] = []
            tokens: set[str] = set()
            for _row_no, _row, parsed in members:
                value = parsed[field_name]
                if value in (None, "", [], {}):
                    continue
                token = _compact_json(value)
                if token not in tokens:
                    tokens.add(token)
                    values.append(value)
            if len(values) > 1:
                conflicts.append(field_name)
            merged[field_name] = values[0] if values else fields[field_name].__class__()
        winner = max(
            members,
            key=lambda item: (
                sum(value not in (None, "", [], {}) for value in item[2].values()),
                str(item[1]["name"]).count(" "),
                -item[0],
            ),
        )
        result.append(
            _EntityGroup(
                members=tuple(members),
                display_name=_display_name(winner[1]["name"], f"{table_name}:{winner[0]}"),
                values=merged,
                conflicting_fields=tuple(sorted(conflicts)),
            )
        )
    return result


def _base_properties(file_path: str, **properties: Any) -> dict[str, Any]:
    return {
        "source_provider": "huggingface",
        "dataset_name": "f-galkin/DragonTCM",
        "file_path": file_path,
        **{key: value for key, value in properties.items() if value not in (None, "", [], {})},
    }


def _ensure_draft(
    drafts: dict[tuple[str, str], _Draft],
    node_type: NodeType,
    name: str,
    properties: dict[str, Any],
    evidence_ref: str,
) -> _Draft:
    key = (node_type.value, _identity_key(name))
    draft = drafts.get(key)
    if draft is None:
        draft = _Draft(node_type.value, name, properties)
        drafts[key] = draft
    draft.evidence_refs.add(evidence_ref)
    return draft


def _condition_tag(name: str) -> str:
    match = _CONDITION_TAG_RE.search(name)
    return match.group(1).casefold() if match else "<none>"


def _condition_snomed(aliases: list[str]) -> tuple[str | None, str | None]:
    identifiers: list[str] = []
    for alias in aliases:
        if not alias.casefold().startswith("snomed:"):
            continue
        match = _SNOMED_RE.fullmatch(alias)
        if match is None:
            return None, "invalid_snomed_id"
        if match.group(1) not in identifiers:
            identifiers.append(match.group(1))
    if len(identifiers) > 1:
        return None, "multiple_snomed_ids"
    return (identifiers[0] if identifiers else None), None


def _condition_infos(
    rows: list[dict[str, Any]], parsed_rows: list[dict[str, Any]]
) -> list[_Condition]:
    infos: list[_Condition] = []
    id_rows: dict[str, list[_Condition]] = defaultdict(list)
    for row_no, (row, parsed) in enumerate(zip(rows, parsed_rows, strict=True), start=1):
        name = _display_name(row["name"], f"conditions:{row_no}")
        aliases = _dedupe_strings(parsed["synonyms"], f"conditions:{row_no}:synonyms")
        snomed_id, snomed_error = _condition_snomed(aliases)
        semantic_tag = _condition_tag(name)
        info = _Condition(
            row_no=row_no,
            name=name,
            key=_identity_key(name),
            semantic_tag=semantic_tag,
            snomed_id=snomed_id,
            aliases=[alias for alias in aliases if not alias.casefold().startswith("snomed:")],
            payload={**row, **parsed},
            quarantine_reason=snomed_error,
        )
        if info.quarantine_reason is None and semantic_tag != "disorder":
            info.quarantine_reason = f"unsupported_condition_tag:{semantic_tag}"
        infos.append(info)
        if snomed_id:
            id_rows[snomed_id].append(info)
    for snomed_id, grouped in id_rows.items():
        if len(grouped) > 1:
            for info in grouped:
                info.quarantine_reason = f"duplicate_snomed_id:{snomed_id}"
    return infos


def _make_record(
    draft: _Draft,
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
        evidence_refs=sorted(draft.evidence_refs),
        prompt_hash=PROMPT_HASH,
        import_scope_key=import_scope_key,
        properties={
            "import_source_id": source_id,
            "import_batch_id": batch_id,
            "import_unit_id": unit_id,
            **draft.properties,
        },
        edges=_sorted_edges(draft),
    )
    record.validate_types()
    return record


def _sorted_edges(draft: _Draft) -> list[DatasetEdge]:
    edges = list(draft.edges.values())
    edges.sort(key=lambda edge: (edge.type, edge.target))
    return edges


def clean_directory(
    input_dir: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    tables, file_hashes = _read_tables(input_dir)
    parsed, json_item_counts = _parse_json_fields(tables)
    indexes = {
        table_name: _unique_index(tables[table_name], table_name)
        for table_name in ("herbs", "formulas", "conditions")
    }
    drafts: dict[tuple[str, str], _Draft] = {}
    row_drafts: dict[tuple[str, str], _Draft] = {}
    quarantine: Counter[str] = Counter()
    mapped: Counter[str] = Counter()
    quality_samples: dict[str, list[dict[str, Any]]] = {
        "unsupported_conditions": [],
        "quarantined_relations": [],
        "invalid_manifestations": [],
        "surface_identity_conflicts": [],
    }
    surface_stats: Counter[str] = Counter()

    def sample(bucket: str, value: dict[str, Any]) -> None:
        if len(quality_samples[bucket]) < 50:
            quality_samples[bucket].append(value)

    herb_file = PARQUET_FILES["herbs"]
    for group in _entity_groups(tables["herbs"], parsed["herbs"], "herbs"):
        units = [group]
        if len(group.members) > 1:
            surface_stats["herb_duplicate_groups"] += 1
            if group.conflicting_fields:
                surface_stats["herb_conflict_groups"] += 1
                surface_stats["herb_conflict_rows"] += len(group.members)
                sample(
                    "surface_identity_conflicts",
                    {
                        "table": "herbs",
                        "rows": [member[0] for member in group.members],
                        "names": [member[1]["name"] for member in group.members],
                        "conflicting_fields": list(group.conflicting_fields),
                    },
                )
                units = [
                    _EntityGroup((member,), str(member[1]["name"]), member[2], ())
                    for member in group.members
                ]
            else:
                surface_stats["herb_merged_groups"] += 1
                surface_stats["herb_merged_rows"] += len(group.members)
        for unit in units:
            aliases = _dedupe_strings(unit.values["synonyms"], "herbs:surface:aliases")
            for _row_no, row, _values in unit.members:
                raw_name = _display_name(row["name"], f"herbs:{_row_no}")
                if raw_name != unit.display_name and raw_name not in aliases:
                    aliases.append(raw_name)
            evidence_refs = [f"{herb_file}:row:{member[0]}" for member in unit.members]
            draft = _ensure_draft(
                drafts,
                NodeType.HERB,
                unit.display_name,
                _base_properties(
                    herb_file,
                    aliases=aliases,
                    category=_dedupe_strings(
                        unit.values["category"], "herbs:surface:category"
                    ),
                    nature=_compact_json_or_none(unit.values["properties"]),
                    contraindication=_dedupe_strings(
                        unit.values["contraindications"],
                        "herbs:surface:contraindications",
                    ),
                    dosage=_compact_json_or_none(unit.values["dosage"]),
                    indications=_dedupe_strings(
                        unit.values["indications"], "herbs:surface:indications"
                    ),
                    source_actions=unit.values["actions"],
                    source_interactions=unit.values["interactions"],
                    source_incompatibility=unit.values["incompatibility"],
                    source_notes=unit.values["notes"],
                ),
                evidence_refs[0],
            )
            draft.evidence_refs.update(evidence_refs)
            for _row_no, row, _values in unit.members:
                row_drafts[("herb", _identity_key(str(row["name"])))] = draft

    formula_file = PARQUET_FILES["formulas"]
    for group in _entity_groups(tables["formulas"], parsed["formulas"], "formulas"):
        units = [group]
        if len(group.members) > 1:
            surface_stats["formula_duplicate_groups"] += 1
            if group.conflicting_fields:
                surface_stats["formula_conflict_groups"] += 1
                surface_stats["formula_conflict_rows"] += len(group.members)
                sample(
                    "surface_identity_conflicts",
                    {
                        "table": "formulas",
                        "rows": [member[0] for member in group.members],
                        "names": [member[1]["name"] for member in group.members],
                        "conflicting_fields": list(group.conflicting_fields),
                    },
                )
                units = [
                    _EntityGroup((member,), str(member[1]["name"]), member[2], ())
                    for member in group.members
                ]
            else:
                surface_stats["formula_merged_groups"] += 1
                surface_stats["formula_merged_rows"] += len(group.members)
        for unit in units:
            aliases = _dedupe_strings(
                unit.values["synonyms"], "formulas:surface:aliases"
            )
            for _row_no, row, _values in unit.members:
                raw_name = _display_name(row["name"], f"formulas:{_row_no}")
                if raw_name != unit.display_name and raw_name not in aliases:
                    aliases.append(raw_name)
            evidence_refs = [f"{formula_file}:row:{member[0]}" for member in unit.members]
            draft = _ensure_draft(
                drafts,
                NodeType.FORMULA,
                unit.display_name,
                _base_properties(
                    formula_file,
                    aliases=aliases,
                    syndrome_text=_compact_json_or_none(unit.values["syndromes"]),
                    indications=_dedupe_strings(
                        unit.values["treats"], "formulas:surface:treats"
                    ),
                    contraindication=_dedupe_strings(
                        unit.values["contraindications"],
                        "formulas:surface:contraindications",
                    ),
                    composition_text=_compact_json_or_none(unit.values["composition"]),
                    source_actions=unit.values["actions"],
                    source_notes=unit.values["notes"],
                ),
                evidence_refs[0],
            )
            draft.evidence_refs.update(evidence_refs)
            for _row_no, row, _values in unit.members:
                row_drafts[("formula", _identity_key(str(row["name"])))] = draft

    condition_infos = _condition_infos(tables["conditions"], parsed["conditions"])
    condition_file = PARQUET_FILES["conditions"]
    condition_by_key = {info.key: info for info in condition_infos}
    accepted_conditions = [info for info in condition_infos if not info.quarantine_reason]
    for info in condition_infos:
        if info.quarantine_reason:
            quarantine["unsupported_condition_rows"] += 1
            quarantine[info.quarantine_reason] += 1
            sample(
                "unsupported_conditions",
                {
                    "evidence_ref": f"{condition_file}:row:{info.row_no}",
                    "name": info.name,
                    "reason": info.quarantine_reason,
                },
            )
            continue
        evidence_ref = f"{condition_file}:row:{info.row_no}"
        draft = _ensure_draft(
            drafts,
            NodeType.DISEASE,
            info.name,
            _base_properties(
                condition_file,
                aliases=info.aliases,
                snomed_id=info.snomed_id,
                tcm_type="SNOMED disorder",
                description=nfkc_strip(str(info.payload.get("description") or "")),
                core_symptoms=_compact_json_or_none(info.payload["symptoms"]),
                representative_formulas=_compact_json_or_none(
                    info.payload["herb_formulas"]
                ),
                related_acupoints=_compact_json_or_none(info.payload["points"]),
            ),
            evidence_ref,
        )
        row_drafts[("condition", info.key)] = draft

    symptom_file = PARQUET_FILES["conditions"]
    duplicate_symptom_edges = 0
    for info in accepted_conditions:
        condition = row_drafts[("condition", info.key)]
        for pattern_index, pattern in enumerate(info.payload["symptoms"], start=1):
            pattern_ref = (
                f"{symptom_file}:row:{info.row_no}:symptoms:{pattern_index}"
            )
            if not isinstance(pattern, dict):
                quarantine["invalid_pattern_objects"] += 1
                sample(
                    "invalid_manifestations",
                    {"evidence_ref": pattern_ref, "reason": "pattern_not_object"},
                )
                continue
            manifestations = pattern.get("clinical_manifestations")
            if manifestations is None:
                quarantine["missing_manifestation_lists"] += 1
                sample(
                    "invalid_manifestations",
                    {"evidence_ref": pattern_ref, "reason": "missing_list"},
                )
                continue
            if not isinstance(manifestations, list):
                quarantine["invalid_manifestation_lists"] += 1
                sample(
                    "invalid_manifestations",
                    {"evidence_ref": pattern_ref, "reason": "list_not_array"},
                )
                continue
            for manifestation_index, raw in enumerate(manifestations, start=1):
                evidence_ref = (
                    f"{pattern_ref}:clinical_manifestations:{manifestation_index}"
                )
                if not isinstance(raw, str):
                    quarantine["non_string_manifestations"] += 1
                    sample(
                        "invalid_manifestations",
                        {"evidence_ref": evidence_ref, "reason": "not_string"},
                    )
                    continue
                name = nfkc_strip(raw)
                if not name:
                    quarantine["empty_manifestations"] += 1
                    sample(
                        "invalid_manifestations",
                        {"evidence_ref": evidence_ref, "reason": "empty"},
                    )
                    continue
                if name.endswith(("...", "…")):
                    quarantine["truncated_manifestations"] += 1
                    sample(
                        "invalid_manifestations",
                        {
                            "evidence_ref": evidence_ref,
                            "name": name,
                            "reason": "truncated",
                        },
                    )
                    continue
                symptom = _ensure_draft(
                    drafts,
                    NodeType.SYMPTOM,
                    name,
                    _base_properties(
                        symptom_file,
                        category="DragonTCM 临床表现（含体征）",
                        tcm_type="来源标注临床表现",
                    ),
                    evidence_ref,
                )
                if condition.add_edge(
                    EdgeType.RELATED_SYMPTOM,
                    symptom.node_name,
                    evidence_ref,
                    source_field="conditions.symptoms[].clinical_manifestations",
                ):
                    mapped[EdgeType.RELATED_SYMPTOM.value] += 1
                else:
                    duplicate_symptom_edges += 1

    relation_file = PARQUET_FILES["relations"]
    endpoint_casefold_matches = 0
    surface_rewritten_endpoints = 0
    duplicate_relation_edges = 0
    source_relation_counts: Counter[str] = Counter()
    for row_no, row in enumerate(tables["relations"], start=1):
        shape = (row["source_type"], row["target_type"], row["edge_type"])
        source_relation_counts["->".join(shape)] += 1
        if shape not in ALLOWED_RELATION_SHAPES:
            raise ValueError(f"relations:{row_no} unsupported relation shape: {shape}")
        evidence_ref = f"{relation_file}:row:{row_no}"
        source_key = _identity_key(str(row["source"]))
        target_key = _identity_key(str(row["target"]))
        source = row_drafts.get((str(row["source_type"]), source_key))
        target = row_drafts.get((str(row["target_type"]), target_key))
        if source is None or target is None:
            quarantine["quarantined_relations"] += 1
            info = condition_by_key.get(source_key)
            reason = (
                info.quarantine_reason
                if info and info.quarantine_reason
                else "missing_or_quarantined_endpoint"
            )
            sample(
                "quarantined_relations",
                {"evidence_ref": evidence_ref, "shape": shape, "reason": reason},
            )
            continue
        if source.node_name != row["source"]:
            if _identity_key(source.node_name) == source_key:
                endpoint_casefold_matches += 1
            else:
                surface_rewritten_endpoints += 1
        if target.node_name != row["target"]:
            if _identity_key(target.node_name) == target_key:
                endpoint_casefold_matches += 1
            else:
                surface_rewritten_endpoints += 1
        if shape == ("formula", "herb", "contains"):
            properties = {"source_relation": "contains"}
            dosage = nfkc_strip(str(row.get("dosage") or ""))
            if dosage:
                properties["dosage"] = dosage
            added = source.add_edge(
                EdgeType.CONTAINS_HERB,
                target.node_name,
                evidence_ref,
                **properties,
            )
            if added:
                mapped[EdgeType.CONTAINS_HERB.value] += 1
            else:
                duplicate_relation_edges += 1
        elif shape == ("condition", "herb", "treats"):
            added = source.add_edge(
                EdgeType.RELATED_HERB,
                target.node_name,
                evidence_ref,
                source_relation="treats",
            )
            if added:
                mapped[EdgeType.RELATED_HERB.value] += 1
            else:
                duplicate_relation_edges += 1
        else:
            quarantine["condition_formula_treats_relations"] += 1
            sample(
                "quarantined_relations",
                {
                    "evidence_ref": evidence_ref,
                    "shape": shape,
                    "reason": "no_neutral_formula_association_edge",
                },
            )

    records = [
        _make_record(
            draft,
            source_id=source_id,
            batch_id=batch_id,
            import_scope_key=import_scope_key,
        )
        for draft in drafts.values()
    ]
    node_rank = {item.value: index for index, item in enumerate(NodeType)}
    records.sort(key=lambda item: (node_rank[item.node_type], item.node_name))
    herb_names = set(indexes["herbs"])
    formula_names = set(indexes["formulas"])
    chinese_alias_rows = sum(
        any("\u4e00" <= char <= "\u9fff" for alias in parsed_row["synonyms"] for char in alias)
        for parsed_row in parsed["herbs"]
    )
    semantic_tags = Counter(info.semantic_tag for info in condition_infos)
    report = {
        "publish": False,
        "license_status": "restricted_noncommercial_upstream_rights_unverified",
        "source_revision": SOURCE_REVISION,
        "source_file_sha256": file_hashes,
        "source_row_counts": {name: len(rows) for name, rows in tables.items()},
        "json_item_counts": json_item_counts,
        "condition_semantic_tag_counts": dict(sorted(semantic_tags.items())),
        "snomed_counts": {
            "all_with_id": sum(info.snomed_id is not None for info in condition_infos),
            "accepted_with_id": sum(info.snomed_id is not None for info in accepted_conditions),
            "accepted_without_id": sum(info.snomed_id is None for info in accepted_conditions),
        },
        "identity_counts": {
            "cross_type_herb_formula_names": len(herb_names & formula_names),
            "endpoint_casefold_matches": endpoint_casefold_matches,
            "surface_rewritten_endpoints": surface_rewritten_endpoints,
            "chinese_alias_herb_rows": chinese_alias_rows,
            "herb_surface_duplicate_groups": surface_stats["herb_duplicate_groups"],
            "herb_surface_merged_groups": surface_stats["herb_merged_groups"],
            "herb_surface_conflict_groups": surface_stats["herb_conflict_groups"],
            "formula_surface_duplicate_groups": surface_stats[
                "formula_duplicate_groups"
            ],
            "formula_surface_merged_groups": surface_stats["formula_merged_groups"],
            "formula_surface_conflict_groups": surface_stats[
                "formula_conflict_groups"
            ],
            "alias_based_merges": 0,
            "cross_language_merges": 0,
        },
        "source_relation_counts": dict(sorted(source_relation_counts.items())),
        "mapped_relation_counts": dict(sorted(mapped.items())),
        "duplicate_symptom_edges_collapsed": duplicate_symptom_edges,
        "duplicate_relation_edges_collapsed": duplicate_relation_edges,
        "quarantine_counts": dict(sorted(quarantine.items())),
        "quality_samples": quality_samples,
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
