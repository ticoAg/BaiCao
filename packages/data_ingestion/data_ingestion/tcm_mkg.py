"""只读清洗 TCM-MKG 的中医药主域表。"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.text_normalize import nfkc_strip

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord, compute_stats
from data_ingestion.entity_identity import has_han
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcm-mkg"
SOURCE_REVISION = "zenodo:13763953:V1.0"
IMPORT_SCOPE_KEY = "zenodo:10.5281/zenodo.13763953@V1.0"
DEFAULT_BATCH_ID = "2026-08-19-tcm-mkg-v1"
PROCESSOR = "tcm_mkg"
PROMPT_HASH = prompt_hash_for(Path(__file__))

SOURCE_FILES = {
    "D1": "D1_TCM_terminology.tsv",
    "D2": "D2_Chinese_patent_medicine.tsv",
    "D3": "D3_CPM_TCMT.tsv",
    "D4": "D4_CPM_CHP.tsv",
    "D5": "D5_CPM_ICD11.tsv",
    "D6": "D6_Chinese_herbal_pieces.tsv",
    "D7": "D7_CHP_Medicinal_properties.tsv",
    "D18": "D18_ICD11.tsv",
}
REQUIRED_COLUMNS = {
    "D1": (
        "TCMT_ID",
        "Chinese_group",
        "English_group",
        "Chinese_term",
        "Pinyin_term",
        "Chinese_synonyms",
        "English_term",
        "Synonyms",
        "English_definition_description",
    ),
    "D2": (
        "CPM_ID",
        "Chinese_patent_medicine",
        "Pinyin_term",
        "Routes_of_administration",
    ),
    "D3": (
        "CPM_ID",
        "TCMT_ID",
        "Chinese_group",
        "English_group",
        "Chinese_term",
        "Pinyin_term",
        "English_term",
        "Synonyms",
    ),
    "D4": ("CPM_ID", "CHP_ID", "Dosage_ratio"),
    "D5": ("CPM_ID", "ICD11_code"),
    "D6": (
        "CHP_ID",
        "Chinese_herbal_pieces",
        "Chinese_synonyms",
        "Pinyin_term",
        "English_term",
        "Sources",
    ),
    "D7": ("CHP_ID", "Medicinal_properties", "Class", "x_rank", "y_rank"),
    "D18": (
        "ICD11_code",
        "BlockId",
        "English_term",
        "Chinese_term",
        "ClassKind",
        "DepthInKind",
        "IsResidual",
        "ChapterNo",
        "BrowserLink",
        "isLeaf",
        "Primary tabulation",
        "Grouping1",
        "Grouping2",
        "Grouping3",
        "Grouping4",
        "Grouping5",
        "Version:2024 Jan 21 22:30 UTC",
    ),
}
TCMT_NODE_TYPES = {
    "传统医学疾病": NodeType.DISEASE,
    "传统医学证候": NodeType.DISEASE,
    "治则": NodeType.TREATMENT_METHOD,
    "治法": NodeType.TREATMENT_METHOD,
}
TCMT_EDGE_TYPES = {
    "传统医学疾病": EdgeType.APPLIES_TO,
    "传统医学证候": EdgeType.RELATED_SYNDROME,
    "治则": EdgeType.USES_METHOD,
    "治法": EdgeType.USES_METHOD,
}
PROPERTY_EDGE_TYPES = {
    "Medicinal flavor": (NodeType.FLAVOR, EdgeType.HAS_FLAVOR),
    "Therapeutic nature": (NodeType.FLAVOR, EdgeType.HAS_FLAVOR),
    "Meridian tropism": (NodeType.MERIDIAN, EdgeType.ENTERS_MERIDIAN),
}
SOURCE_CATEGORIES = {"Algae", "Fungi", "Metazoa", "Mineral", "Viridiplantae"}
ID_PATTERNS = {
    "TCMT_ID": re.compile(r"TCMT\d{5}\Z"),
    "CPM_ID": re.compile(r"CPM\d{5}\Z"),
    "CHP_ID": re.compile(r"CHP\d{5}\Z"),
}
_ALIAS_SPLIT_RE = re.compile(r"\|+|_x000D_\s*|[\r\n]+")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_DIR = repo_root() / ".cache/huggingface/JX-Lab/TCM-MKG"


@dataclass
class _Draft:
    node_type: NodeType
    node_name: str
    properties: dict[str, Any]
    evidence_refs: set[str] = field(default_factory=set)
    edges: dict[tuple[str, str], DatasetEdge] = field(default_factory=dict)

    def merge_properties(self, properties: dict[str, Any]) -> None:
        for key, value in properties.items():
            if value in (None, "", [], {}):
                continue
            if key == "aliases":
                current = list(self.properties.get(key) or [])
                self.properties[key] = _dedupe([*current, *value])
            elif key not in self.properties:
                self.properties[key] = value
            elif self.properties[key] != value:
                raise ValueError(
                    f"conflicting {key} for {self.node_type.value}:{self.node_name}"
                )

    def add_edge(
        self,
        edge_type: EdgeType,
        target: str,
        evidence_ref: str,
        **properties: Any,
    ) -> bool:
        key = (edge_type.value, target)
        edge_props = {name: value for name, value in properties.items() if value != ""}
        if key in self.edges:
            existing = self.edges[key]
            comparable = {
                name: value
                for name, value in existing.properties.items()
                if name != "evidence_ref"
            }
            if comparable != edge_props:
                raise ValueError(
                    f"conflicting edge properties for {self.node_name} "
                    f"{edge_type.value} {target}"
                )
            refs = set(str(existing.properties["evidence_ref"]).split(" || "))
            refs.add(evidence_ref)
            existing.properties["evidence_ref"] = " || ".join(sorted(refs))
            self.evidence_refs.add(evidence_ref)
            return False
        self.edges[key] = DatasetEdge(
            type=edge_type.value,
            target=target,
            properties={"evidence_ref": evidence_ref, **edge_props},
        )
        self.evidence_refs.add(evidence_ref)
        return True


def _identity_key(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = nfkc_strip(value)
        key = _identity_key(cleaned)
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _aliases(*values: str) -> list[str]:
    items: list[str] = []
    for value in values:
        items.extend(_ALIAS_SPLIT_RE.split(value or ""))
    return [item for item in _dedupe(items) if has_han(item)]


def _read_table(
    root: Path, table: str, repairs: Counter[str]
) -> list[tuple[int, dict[str, str]]]:
    path = root / SOURCE_FILES[table]
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(
            handle,
            delimiter="\t",
            restkey="_extra",
            restval=None,
            strict=True,
        )
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS[table]:
            raise ValueError(f"{table} unexpected columns: {reader.fieldnames}")
        rows: list[tuple[int, dict[str, str]]] = []
        for record_no, raw in enumerate(reader, start=1):
            extra = raw.pop("_extra", None)
            if any(raw[column] is None for column in REQUIRED_COLUMNS[table]):
                raise ValueError(f"{table}:record:{record_no} has missing columns")
            row = {
                column: nfkc_strip(str(raw[column] or ""))
                for column in REQUIRED_COLUMNS[table]
            }
            if extra:
                if (
                    table == "D6"
                    and len(extra) == 1
                    and not row["Pinyin_term"]
                    and nfkc_strip(extra[0]) in SOURCE_CATEGORIES
                ):
                    row["Pinyin_term"] = row["English_term"]
                    row["English_term"] = row["Sources"]
                    row["Sources"] = nfkc_strip(extra[0])
                    repairs["D6_shifted_column_rows"] += 1
                    repairs["D6_shifted_column_record"] = record_no
                else:
                    raise ValueError(f"{table}:record:{record_no} has extra columns")
            rows.append((record_no, row))
    return rows


def _validate_id(value: str, key: str, evidence_ref: str) -> None:
    if not ID_PATTERNS[key].fullmatch(value):
        raise ValueError(f"{evidence_ref} invalid {key}: {value}")


def _unique_index(
    rows: list[tuple[int, dict[str, str]]], key: str, table: str
) -> dict[str, tuple[int, dict[str, str]]]:
    result: dict[str, tuple[int, dict[str, str]]] = {}
    for record_no, row in rows:
        value = row[key]
        _validate_id(value, key, f"{SOURCE_FILES[table]}:record:{record_no}")
        if value in result:
            raise ValueError(f"{table} duplicate {key}: {value}")
        result[value] = (record_no, row)
    return result


def _ensure_draft(
    drafts: dict[tuple[NodeType, str], _Draft],
    node_type: NodeType,
    name: str,
    properties: dict[str, Any],
    evidence_ref: str,
) -> tuple[_Draft, bool]:
    display_name = nfkc_strip(name)
    if not display_name:
        raise ValueError(f"{evidence_ref} has empty node name")
    key = (node_type, _identity_key(display_name))
    existing = drafts.get(key)
    if existing is not None:
        existing.merge_properties(properties)
        existing.evidence_refs.add(evidence_ref)
        return existing, False
    draft = _Draft(node_type=node_type, node_name=display_name, properties={})
    draft.merge_properties(properties)
    draft.evidence_refs.add(evidence_ref)
    drafts[key] = draft
    return draft, True


def _properties(**values: Any) -> dict[str, Any]:
    return {
        "source_provider": "zenodo",
        "dataset_name": "TCM-MKG V1.0",
        **{key: value for key, value in values.items() if value not in (None, "", [], {})},
    }


def _make_record(
    draft: _Draft,
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
) -> DatasetRecord:
    unit_id = f"{draft.node_type.value}:{draft.node_name}"
    sorted_edges: list[DatasetEdge] = sorted(
        draft.edges.values(), key=lambda edge: (edge.type, edge.target)
    )
    record = DatasetRecord(
        source_id=source_id,
        batch_id=batch_id,
        unit_id=unit_id,
        unit_title=draft.node_name,
        processor=PROCESSOR,
        node_type=draft.node_type.value,
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
        edges=sorted_edges,
    )
    record.validate_types()
    return record


def clean_directory(
    root: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    repairs: Counter[str] = Counter()
    tables = {table: _read_table(root, table, repairs) for table in SOURCE_FILES}
    indexes = {
        "D1": _unique_index(tables["D1"], "TCMT_ID", "D1"),
        "D2": _unique_index(tables["D2"], "CPM_ID", "D2"),
        "D6": _unique_index(tables["D6"], "CHP_ID", "D6"),
    }
    drafts: dict[tuple[NodeType, str], _Draft] = {}
    by_source_id: dict[tuple[str, str], _Draft] = {}
    quarantine: Counter[str] = Counter()
    mapped: Counter[str] = Counter()
    duplicate_edges: Counter[str] = Counter()

    d7_property_classes: dict[str, str] = {}
    for record_no, row in tables["D7"]:
        property_name = row["Medicinal_properties"]
        property_class = row["Class"]
        if property_class not in PROPERTY_EDGE_TYPES:
            raise ValueError(f"D7:record:{record_no} unsupported class: {property_class}")
        if previous := d7_property_classes.get(property_name):
            if previous != property_class:
                raise ValueError(f"D7 property has conflicting classes: {property_name}")
        d7_property_classes[property_name] = property_class

    property_terms: dict[str, tuple[int, dict[str, str]]] = {}
    for record_no, row in tables["D1"]:
        if row["Chinese_group"] == "药性" and row["English_term"] in d7_property_classes:
            if row["English_term"] in property_terms:
                raise ValueError(f"D1 duplicate medicinal property: {row['English_term']}")
            property_terms[row["English_term"]] = (record_no, row)
    if missing := sorted(set(d7_property_classes) - set(property_terms)):
        raise ValueError(f"D7 properties missing from D1: {', '.join(missing)}")

    for tcmt_id, (record_no, row) in indexes["D1"].items():
        group = row["Chinese_group"]
        node_type = TCMT_NODE_TYPES.get(group)
        if node_type is None and row["English_term"] in d7_property_classes:
            node_type = PROPERTY_EDGE_TYPES[d7_property_classes[row["English_term"]]][0]
        if node_type is None:
            quarantine[f"excluded_D1_group:{group}"] += 1
            continue
        evidence_ref = f"{SOURCE_FILES['D1']}:record:{record_no}"
        aliases = _aliases(
            row["Chinese_synonyms"], row["English_term"], row["Synonyms"]
        )
        aliases = [alias for alias in aliases if _identity_key(alias) != _identity_key(row["Chinese_term"])]
        draft, _created = _ensure_draft(
            drafts,
            node_type,
            row["Chinese_term"],
            _properties(
                tcmt_id=tcmt_id,
                aliases=aliases,
                description=row["English_definition_description"],
                tcm_type=group,
            ),
            evidence_ref,
        )
        by_source_id[("TCMT", tcmt_id)] = draft

    for cpm_id, (record_no, row) in indexes["D2"].items():
        evidence_ref = f"{SOURCE_FILES['D2']}:record:{record_no}"
        draft, _created = _ensure_draft(
            drafts,
            NodeType.FORMULA,
            row["Chinese_patent_medicine"],
            _properties(
                cpm_id=cpm_id,
                category="中成药",
                administration_route=row["Routes_of_administration"],
            ),
            evidence_ref,
        )
        by_source_id[("CPM", cpm_id)] = draft

    for chp_id, (record_no, row) in indexes["D6"].items():
        evidence_ref = f"{SOURCE_FILES['D6']}:record:{record_no}"
        aliases = _aliases(row["Chinese_synonyms"], row["English_term"])
        aliases = [alias for alias in aliases if _identity_key(alias) != _identity_key(row["Chinese_herbal_pieces"])]
        draft, _created = _ensure_draft(
            drafts,
            NodeType.PREPARED_HERB,
            row["Chinese_herbal_pieces"],
            _properties(
                chp_id=chp_id,
                aliases=aliases,
                category=row["Sources"],
            ),
            evidence_ref,
        )
        by_source_id[("CHP", chp_id)] = draft

    d18_by_code: dict[str, tuple[int, dict[str, str]]] = {}
    for record_no, row in tables["D18"]:
        code = row["ICD11_code"]
        if not code:
            continue
        if code in d18_by_code:
            raise ValueError(f"D18 duplicate ICD11_code: {code}")
        d18_by_code[code] = (record_no, row)

    accepted_icd_codes: set[str] = set()
    for record_no, row in tables["D5"]:
        cpm_id = row["CPM_ID"]
        if cpm_id not in indexes["D2"]:
            raise ValueError(f"D5:record:{record_no} missing CPM endpoint: {cpm_id}")
        code = row["ICD11_code"]
        if code not in d18_by_code:
            raise ValueError(f"D5:record:{record_no} missing ICD endpoint: {code}")
        _icd_record_no, icd = d18_by_code[code]
        if icd["ClassKind"] != "category":
            raise ValueError(f"D5:record:{record_no} non-category ICD endpoint: {code}")
        chapter = int(icd["ChapterNo"])
        if not 1 <= chapter <= 20:
            quarantine[f"excluded_D5_chapter:{chapter}"] += 1
            continue
        accepted_icd_codes.add(code)

    merged_tcmt_icd_names = 0
    for code in sorted(accepted_icd_codes):
        record_no, row = d18_by_code[code]
        evidence_ref = f"{SOURCE_FILES['D18']}:record:{record_no}"
        draft, created = _ensure_draft(
            drafts,
            NodeType.DISEASE,
            row["Chinese_term"],
            _properties(
                icd11_code=code,
                aliases=_aliases(row["English_term"]),
                category="ICD-11 category",
                chapter=row["ChapterNo"],
            ),
            evidence_ref,
        )
        merged_tcmt_icd_names += not created
        by_source_id[("ICD11", code)] = draft

    d3_seen: set[tuple[str, str]] = set()
    d3_synonym_mismatches = 0
    canonical_d1 = {key: value[1] for key, value in indexes["D1"].items()}
    for record_no, row in tables["D3"]:
        cpm_id, tcmt_id = row["CPM_ID"], row["TCMT_ID"]
        if cpm_id not in indexes["D2"] or tcmt_id not in canonical_d1:
            raise ValueError(f"D3:record:{record_no} missing endpoint")
        canonical = canonical_d1[tcmt_id]
        for column in (
            "Chinese_group",
            "English_group",
            "Chinese_term",
            "Pinyin_term",
            "English_term",
        ):
            if row[column] != canonical[column]:
                raise ValueError(f"D3:record:{record_no} mismatches D1 column {column}")
        d3_synonym_mismatches += row["Synonyms"] != canonical["Synonyms"]
        pair = (cpm_id, tcmt_id)
        if pair in d3_seen:
            duplicate_edges["duplicate_D3_pairs"] += 1
        d3_seen.add(pair)
        target = by_source_id.get(("TCMT", tcmt_id))
        edge_type = TCMT_EDGE_TYPES.get(canonical["Chinese_group"])
        if target is None or edge_type is None:
            quarantine[f"excluded_D3_group:{canonical['Chinese_group']}"] += 1
            continue
        evidence_ref = f"{SOURCE_FILES['D3']}:record:{record_no}"
        if by_source_id[("CPM", cpm_id)].add_edge(
            edge_type, target.node_name, evidence_ref
        ):
            mapped[edge_type.value] += 1
        else:
            duplicate_edges["collapsed_D3_edges"] += 1

    for record_no, row in tables["D4"]:
        cpm_id, chp_id = row["CPM_ID"], row["CHP_ID"]
        if ("CPM", cpm_id) not in by_source_id or ("CHP", chp_id) not in by_source_id:
            raise ValueError(f"D4:record:{record_no} missing endpoint")
        ratio = row["Dosage_ratio"]
        if ratio:
            try:
                parsed_ratio = Decimal(ratio)
            except InvalidOperation as exc:
                raise ValueError(f"D4:record:{record_no} invalid ratio: {ratio}") from exc
            if not 0 < parsed_ratio <= 1:
                raise ValueError(f"D4:record:{record_no} ratio out of range: {ratio}")
        source = by_source_id[("CPM", cpm_id)]
        target = by_source_id[("CHP", chp_id)]
        evidence_ref = f"{SOURCE_FILES['D4']}:record:{record_no}"
        if not source.add_edge(
            EdgeType.CONTAINS_HERB,
            target.node_name,
            evidence_ref,
            dosage_ratio=ratio,
        ):
            duplicate_edges["collapsed_D4_edges"] += 1
        else:
            mapped[EdgeType.CONTAINS_HERB.value] += 1

    for record_no, row in tables["D5"]:
        code = row["ICD11_code"]
        target = by_source_id.get(("ICD11", code))
        if target is None:
            continue
        source = by_source_id[("CPM", row["CPM_ID"])]
        evidence_ref = f"{SOURCE_FILES['D5']}:record:{record_no}"
        if source.add_edge(EdgeType.APPLIES_TO, target.node_name, evidence_ref):
            mapped[EdgeType.APPLIES_TO.value] += 1
        else:
            duplicate_edges["collapsed_cross_table_treatment_edges"] += 1

    for record_no, row in tables["D7"]:
        chp_id = row["CHP_ID"]
        if ("CHP", chp_id) not in by_source_id:
            raise ValueError(f"D7:record:{record_no} missing CHP endpoint: {chp_id}")
        property_record_no, property_row = property_terms[row["Medicinal_properties"]]
        target = by_source_id[("TCMT", property_row["TCMT_ID"])]
        _node_type, edge_type = PROPERTY_EDGE_TYPES[row["Class"]]
        evidence_ref = f"{SOURCE_FILES['D7']}:record:{record_no}"
        if by_source_id[("CHP", chp_id)].add_edge(
            edge_type, target.node_name, evidence_ref
        ):
            mapped[edge_type.value] += 1
        else:
            duplicate_edges["collapsed_D7_edges"] += 1
        target.evidence_refs.add(
            f"{SOURCE_FILES['D1']}:record:{property_record_no}"
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
    records.sort(key=lambda record: (node_rank[record.node_type], record.node_name))
    file_hashes = {
        SOURCE_FILES[table]: hashlib.sha256((root / SOURCE_FILES[table]).read_bytes()).hexdigest()
        for table in SOURCE_FILES
    }
    report = {
        "publish": False,
        "license_status": "restricted_noncommercial_sharealike_no_derivatives_upstream_rights_unverified",
        "source_revision": SOURCE_REVISION,
        "source_file_sha256": file_hashes,
        "source_table_counts": {table: len(rows) for table, rows in tables.items()},
        "consumed_tables": list(SOURCE_FILES),
        "excluded_tables": [
            "D8-D17",
            "D19-D24",
            "SD1_predicted_InChIKey_EntrezID.tsv",
            "original_kg/nodes.tsv",
            "original_kg/edges.tsv (not held)",
        ],
        "accepted_icd11_codes": len(accepted_icd_codes),
        "merged_tcmt_icd_exact_names": merged_tcmt_icd_names,
        "D3_redundant_synonym_mismatches": d3_synonym_mismatches,
        "repair_counts": dict(sorted(repairs.items())),
        "mapped_relation_counts": dict(sorted(mapped.items())),
        "duplicate_edge_counts": dict(sorted(duplicate_edges.items())),
        "quarantine_counts": dict(sorted(quarantine.items())),
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
