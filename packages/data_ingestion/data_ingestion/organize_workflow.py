"""规则、脚本、agent 与图库共用的整理合同。

确定性步骤先切分、过滤并给出身份；agent 只补不确定抽取。
agent 产物必须再次经过同一套门禁，才能变成 DatasetRecord。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from knowledge_model.constants import NodeType

from data_ingestion.dataset_records import DatasetRecord
from data_ingestion.entity_identity import (
    EntityDraft,
    assign_display_names,
    contains_brand,
    merge_same_identity,
    redact_sensitive,
)
from data_ingestion.models import ExtractionCandidate
from data_ingestion.provenance import prompt_hash_for
from pathlib import Path

PROMPT_HASH = prompt_hash_for(Path(__file__))
ALLOWED_AGENT_TYPES = {item.value for item in NodeType}


@dataclass
class WorkUnit:
    unit_id: str
    kind: str
    locator: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTask:
    unit_id: str
    locator: str
    kind: str
    redacted_text: str
    allowed_node_types: list[str]
    instruction: str


@dataclass
class OrganizeBatch:
    records: list[DatasetRecord]
    agent_queue: list[AgentTask]
    quarantined: list[dict[str, Any]]
    report: dict[str, Any]


def candidates_to_drafts(
    candidates: list[ExtractionCandidate],
) -> list[EntityDraft]:
    drafts: list[EntityDraft] = []
    for candidate in candidates:
        name = redact_sensitive(str(candidate.node_name or "")).strip()
        if not name:
            continue
        if candidate.node_type.value not in ALLOWED_AGENT_TYPES:
            continue
        drafts.append(
            EntityDraft(
                node_type=candidate.node_type,
                raw_name=name,
                role=candidate.role or candidate.node_type.value,
                stable_id=candidate.stable_id or name,
                aliases=list(candidate.aliases or []),
                evidence_refs=[candidate.evidence_ref]
                if candidate.evidence_ref
                else [],
                properties={
                    key: redact_sensitive(str(value)) if isinstance(value, str) else value
                    for key, value in (candidate.properties or {}).items()
                },
            )
        )
    return drafts


def finalize_drafts(
    drafts: list[EntityDraft],
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
    processor: str,
) -> tuple[list[DatasetRecord], list[dict[str, Any]], dict[str, Any]]:
    merged, collapsed = merge_same_identity(drafts)
    resolved = assign_display_names(merged)
    quarantined: list[dict[str, Any]] = []
    accepted: list[EntityDraft] = []
    for draft in resolved:
        if contains_brand(draft.raw_name) or contains_brand(draft.display_name):
            quarantined.append(
                {
                    "name": draft.raw_name,
                    "reason": "brand",
                    "stable_id": draft.stable_id,
                }
            )
            continue
        accepted.append(draft)
    records: list[DatasetRecord] = []
    for draft in accepted:
        unit_id = f"{draft.node_type.value}:{draft.display_name}"
        record = DatasetRecord(
            source_id=source_id,
            batch_id=batch_id,
            unit_id=unit_id,
            unit_title=draft.display_name,
            processor=processor,
            node_type=draft.node_type.value,
            node_name=draft.display_name,
            source=source_id,
            status="pending",
            evidence_refs=draft.evidence_refs,
            prompt_hash=PROMPT_HASH,
            import_scope_key=import_scope_key,
            properties={
                "import_source_id": source_id,
                "import_batch_id": batch_id,
                "import_unit_id": unit_id,
                **draft.properties,
            },
        )
        record.validate_types()
        records.append(record)
    report = {
        "collapsed_same_identity": collapsed,
        "accepted_records": len(records),
        "brand_quarantine": len(quarantined),
        "qualified_display_names": [
            item.display_name
            for item in accepted
            if item.display_name != item.raw_name
        ],
    }
    return records, quarantined, report


def accept_agent_candidates(
    candidates: list[ExtractionCandidate],
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
    processor: str,
) -> OrganizeBatch:
    drafts = candidates_to_drafts(candidates)
    records, quarantined, report = finalize_drafts(
        drafts,
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
        processor=processor,
    )
    return OrganizeBatch(
        records=records,
        agent_queue=[],
        quarantined=quarantined,
        report=report,
    )
