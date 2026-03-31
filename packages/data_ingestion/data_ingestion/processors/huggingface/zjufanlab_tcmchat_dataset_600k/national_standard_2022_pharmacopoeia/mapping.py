from __future__ import annotations

import hashlib

from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord
from knowledge_model.labels import EDGE_TYPE_LABELS
from knowledge_model.node_models import (
    DiseaseNodeModel,
    EfficacyNodeModel,
    EvidenceNodeModel,
    FlavorNodeModel,
    HerbNodeModel,
    MeridianNodeModel,
    PreparedHerbNodeModel,
)

from data_ingestion.bundles import BundleEdge, UnifiedGraphBundle
from data_ingestion.source_models import RawEntryBlock

from .extraction_models import PharmacopoeiaEntrySections, PharmacopoeiaExtractionResult


def hash_text(raw_text: str) -> str:
    return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:12]


def build_evidence_id(block: RawEntryBlock) -> str:
    return (
        f"证据:{block.context.provider}:{block.context.dataset}:{block.context.file_path}:"
        f"{block.entry_title}:{hash_text(block.raw_text)}"
    )


def build_flavor_nodes(extraction: PharmacopoeiaExtractionResult) -> list[FlavorNodeModel]:
    names = extraction.prepared_piece.flavors if extraction.prepared_piece is not None else []
    return [FlavorNodeModel(id=f"性味:{name}", name=name, source="huggingface") for name in names]


def build_meridian_nodes(extraction: PharmacopoeiaExtractionResult) -> list[MeridianNodeModel]:
    names = extraction.prepared_piece.meridians if extraction.prepared_piece is not None else []
    return [MeridianNodeModel(id=f"归经:{name}", name=name, source="huggingface") for name in names]


def build_efficacy_nodes(extraction: PharmacopoeiaExtractionResult) -> list[EfficacyNodeModel]:
    names = extraction.prepared_piece.efficacies if extraction.prepared_piece is not None else []
    return [EfficacyNodeModel(id=f"功效:{name}", name=name, source="huggingface") for name in names]


def build_disease_nodes(extraction: PharmacopoeiaExtractionResult) -> list[DiseaseNodeModel]:
    indications = extraction.prepared_piece.indications if extraction.prepared_piece is not None else extraction.herb.indications
    return [DiseaseNodeModel(id=f"病证:{name}", name=name, source="huggingface") for name in indications]


def build_relation_edges(
    *,
    herb: HerbNodeModel,
    piece: PreparedHerbNodeModel | None,
    evidence: EvidenceNodeModel,
    extraction: PharmacopoeiaExtractionResult,
) -> list[BundleEdge]:
    edges: list[BundleEdge] = [
        BundleEdge(source=herb.id, target=evidence.id, type=EdgeType.SUPPORTED_BY),
    ]
    target_entity_id = piece.id if piece is not None else herb.id
    flavor_names = extraction.prepared_piece.flavors if extraction.prepared_piece is not None else []
    meridian_names = extraction.prepared_piece.meridians if extraction.prepared_piece is not None else []
    efficacy_names = extraction.prepared_piece.efficacies if extraction.prepared_piece is not None else []
    indication_names = extraction.prepared_piece.indications if extraction.prepared_piece is not None else extraction.herb.indications

    if piece is None:
        for name in indication_names:
            edges.append(BundleEdge(source=target_entity_id, target=f"病证:{name}", type=EdgeType.TREATS))
        return edges

    edges.extend(
        [
            BundleEdge(source=herb.id, target=piece.id, type=EdgeType.HAS_PREPARED_FORM),
            BundleEdge(source=piece.id, target=evidence.id, type=EdgeType.SUPPORTED_BY),
        ]
    )
    for name in flavor_names:
        edges.append(BundleEdge(source=target_entity_id, target=f"性味:{name}", type=EdgeType.HAS_FLAVOR))
    for name in meridian_names:
        edges.append(BundleEdge(source=target_entity_id, target=f"归经:{name}", type=EdgeType.ENTERS_MERIDIAN))
    for name in efficacy_names:
        edges.append(BundleEdge(source=target_entity_id, target=f"功效:{name}", type=EdgeType.HAS_EFFICACY))
    for name in indication_names:
        edges.append(BundleEdge(source=target_entity_id, target=f"病证:{name}", type=EdgeType.TREATS))
    return edges


def build_import_records(
    *,
    herb: HerbNodeModel,
    piece: PreparedHerbNodeModel | None,
    evidence: EvidenceNodeModel,
    extraction: PharmacopoeiaExtractionResult,
) -> list[GraphImportRecord]:
    records = [
        GraphImportRecord(
            node_type=NodeType.HERB,
            node_name=herb.name,
            source=herb.source or "huggingface",
            evidence_refs=[evidence.id],
            properties={
                "pinyin_name": extraction.herb.pinyin_name,
                "latin_name": extraction.herb.latin_name,
                "base_description": extraction.herb.base_description,
                "indications": extraction.herb.indications,
                "usage_text": extraction.herb.usage_text,
                "storage_text": extraction.herb.storage_text,
                "caution_text": extraction.herb.caution_text,
            },
            edges=[GraphImportEdge(type=EdgeType.SUPPORTED_BY, target=evidence.name)],
        ),
        GraphImportRecord(
            node_type=NodeType.EVIDENCE,
            node_name=evidence.name,
            source=evidence.source or "huggingface",
            properties={
                "file_path": evidence.file_path,
                "entry_title": evidence.entry_title,
                "line_start": evidence.line_start,
                "line_end": evidence.line_end,
            },
        ),
    ]
    if piece is not None:
        records.append(
            GraphImportRecord(
                node_type=NodeType.PREPARED_HERB,
                node_name=piece.name,
                source=piece.source or "huggingface",
                evidence_refs=[evidence.id],
                properties={
                    "prepared_from_herb": piece.prepared_from_herb,
                    "processing_method_text": extraction.prepared_piece.processing_text,
                    "usage_text": extraction.prepared_piece.usage_text,
                    "storage_text": extraction.prepared_piece.storage_text,
                    "caution_text": extraction.prepared_piece.caution_text,
                    "indications": extraction.prepared_piece.indications,
                },
                edges=[GraphImportEdge(type=EdgeType.HAS_PREPARED_FORM, target=piece.name)],
            )
        )
    return records


def build_pharmacopoeia_bundle(
    block: RawEntryBlock,
    parsed: PharmacopoeiaEntrySections,
    extraction: PharmacopoeiaExtractionResult,
) -> UnifiedGraphBundle:
    evidence = EvidenceNodeModel(
        id=build_evidence_id(block),
        name=f"{block.entry_title}条目证据",
        source=block.context.provider,
        raw_text=block.raw_text,
        source_provider=block.context.provider,
        dataset_name=block.context.dataset,
        file_path=block.context.file_path,
        entry_title=block.entry_title,
        line_start=block.start_line,
        line_end=block.end_line,
        chunk_hash=hash_text(block.raw_text),
    )
    herb = HerbNodeModel(
        id=f"药材:{extraction.herb.herb_name}",
        name=extraction.herb.herb_name,
        source=block.context.provider,
    )
    piece = None
    if extraction.prepared_piece is not None:
        piece = PreparedHerbNodeModel(
            id=f"饮片:{extraction.prepared_piece.piece_name}",
            name=extraction.prepared_piece.piece_name,
            source=block.context.provider,
            prepared_from_herb=extraction.herb.herb_name,
            processing_method_text=extraction.prepared_piece.processing_text,
            description=parsed.piece_sections.get("炮制"),
        )

    flavor_nodes = build_flavor_nodes(extraction)
    meridian_nodes = build_meridian_nodes(extraction)
    efficacy_nodes = build_efficacy_nodes(extraction)
    disease_nodes = build_disease_nodes(extraction)

    return UnifiedGraphBundle(
        nodes=[
            evidence,
            herb,
            *([piece] if piece is not None else []),
            *flavor_nodes,
            *meridian_nodes,
            *efficacy_nodes,
            *disease_nodes,
        ],
        edges=build_relation_edges(herb=herb, piece=piece, evidence=evidence, extraction=extraction),
        records=build_import_records(herb=herb, piece=piece, evidence=evidence, extraction=extraction),
        warnings=[],
        errors=[],
        stats={"entries_processed": 1, "entry_titles": [block.entry_title]},
    )


def edge_type_to_label(edge_type: EdgeType) -> str:
    return EDGE_TYPE_LABELS.get(edge_type, getattr(edge_type, "value", str(edge_type)))
