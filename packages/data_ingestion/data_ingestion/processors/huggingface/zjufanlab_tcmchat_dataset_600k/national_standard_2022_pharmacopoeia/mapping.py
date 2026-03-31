from __future__ import annotations

import hashlib

from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord
from knowledge_model.node_models import (
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
    piece = extraction.prepared_piece
    if piece is None:
        return []
    return [FlavorNodeModel(id=f"性味:{name}", name=name, source="huggingface") for name in piece.flavors]


def build_meridian_nodes(extraction: PharmacopoeiaExtractionResult) -> list[MeridianNodeModel]:
    piece = extraction.prepared_piece
    if piece is None:
        return []
    return [MeridianNodeModel(id=f"归经:{name}", name=name, source="huggingface") for name in piece.meridians]


def build_efficacy_nodes(extraction: PharmacopoeiaExtractionResult) -> list[EfficacyNodeModel]:
    piece = extraction.prepared_piece
    if piece is None:
        return []
    return [EfficacyNodeModel(id=f"功效:{name}", name=name, source="huggingface") for name in piece.efficacies]


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
    if piece is None:
        return edges

    edges.extend(
        [
            BundleEdge(source=herb.id, target=piece.id, type=EdgeType.HAS_PREPARED_FORM),
            BundleEdge(source=piece.id, target=evidence.id, type=EdgeType.SUPPORTED_BY),
        ]
    )
    for name in extraction.prepared_piece.flavors:
        edges.append(BundleEdge(source=piece.id, target=f"性味:{name}", type=EdgeType.HAS_FLAVOR))
    for name in extraction.prepared_piece.meridians:
        edges.append(BundleEdge(source=piece.id, target=f"归经:{name}", type=EdgeType.ENTERS_MERIDIAN))
    for name in extraction.prepared_piece.efficacies:
        edges.append(BundleEdge(source=piece.id, target=f"功效:{name}", type=EdgeType.HAS_EFFICACY))
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

    return UnifiedGraphBundle(
        nodes=[evidence, herb, *([piece] if piece is not None else []), *flavor_nodes, *meridian_nodes, *efficacy_nodes],
        edges=build_relation_edges(herb=herb, piece=piece, evidence=evidence, extraction=extraction),
        records=build_import_records(herb=herb, piece=piece, evidence=evidence, extraction=extraction),
        warnings=[],
        errors=[],
        stats={"entries_processed": 1, "entry_titles": [block.entry_title]},
    )
