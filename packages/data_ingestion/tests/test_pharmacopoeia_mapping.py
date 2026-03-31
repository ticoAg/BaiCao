from data_ingestion.source_models import RawEntryBlock, SourceFileContext
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.extraction_models import (
    PharmacopoeiaEntrySections,
    PharmacopoeiaExtractionResult,
    PharmacopoeiaHerbExtraction,
    PharmacopoeiaPreparedPieceExtraction,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.mapping import (
    build_pharmacopoeia_bundle,
)
from knowledge_model.constants import EdgeType, NodeType


def test_mapping_builds_herb_piece_evidence_bundle():
    parsed = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=["Yizhihuanghua", "SOLIDAGINISHERBA"],
        base_description="本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
        sections={},
        piece_sections={
            "炮制": "除去杂质，喷淋清水，切段，干燥。",
            "性味与归经": "辛、苦，凉。归肺、肝经。",
            "功能与主治": "清热解毒，疏散风热。",
        },
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n饮片\n【炮制】除去杂质，喷淋清水，切段，干燥。\n【性味与归经】辛、苦，凉。归肺、肝经。\n【功能与主治】清热解毒，疏散风热。",
    )
    block = RawEntryBlock(
        entry_id="entry-1",
        entry_title="一枝黄花",
        raw_text=parsed.raw_text,
        start_line=1,
        end_line=8,
        context=SourceFileContext(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
            local_abspath="/tmp/2022.txt",
            file_size=512,
            line_count=8,
        ),
    )
    extraction = PharmacopoeiaExtractionResult(
        herb=PharmacopoeiaHerbExtraction(herb_name="一枝黄花"),
        prepared_piece=PharmacopoeiaPreparedPieceExtraction(
            piece_name="一枝黄花饮片",
            parent_herb_name="一枝黄花",
            processing_text="除去杂质，喷淋清水，切段，干燥。",
            flavors=["辛", "苦"],
            nature="凉",
            meridians=["肺经", "肝经"],
            efficacies=["清热解毒", "疏散风热"],
        ),
    )

    bundle = build_pharmacopoeia_bundle(block, parsed, extraction)

    assert {node.name for node in bundle.nodes} >= {"一枝黄花", "一枝黄花饮片", "辛", "苦", "肺经", "肝经"}
    assert any(getattr(edge, "type", None) == EdgeType.HAS_PREPARED_FORM for edge in bundle.edges)
    assert any(getattr(node, "type", None) == NodeType.EVIDENCE for node in bundle.nodes)
