"""覆盖药典抽取结果到图谱 bundle 的映射行为。"""

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
from graph_schema.constants import EdgeType, NodeType


def test_mapping_builds_herb_piece_evidence_bundle():
    """验证完整抽取结果会映射出药材、饮片、证据及其关系。"""

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
            indications=["喉痹", "风热感冒"],
        ),
    )

    bundle = build_pharmacopoeia_bundle(block, parsed, extraction)

    assert {node.name for node in bundle.nodes} >= {"一枝黄花", "一枝黄花饮片", "辛", "苦", "肺经", "肝经", "喉痹", "风热感冒"}
    assert any(getattr(edge, "type", None) == EdgeType.HAS_PREPARED_FORM for edge in bundle.edges)
    assert any(getattr(edge, "type", None) == EdgeType.TREATS for edge in bundle.edges)
    assert any(getattr(node, "type", None) == NodeType.EVIDENCE for node in bundle.nodes)
    assert {record.node_name for record in bundle.records} >= {
        "一枝黄花",
        "一枝黄花饮片",
        "一枝黄花条目证据",
        "辛",
        "苦",
        "肺经",
        "肝经",
        "清热解毒",
        "疏散风热",
        "喉痹",
        "风热感冒",
    }

    herb_record = next(record for record in bundle.records if record.node_name == "一枝黄花")
    piece_record = next(record for record in bundle.records if record.node_name == "一枝黄花饮片")

    assert "pinyin_name" not in herb_record.properties
    assert "latin_name" not in herb_record.properties

    assert any(edge.type == EdgeType.HAS_PREPARED_FORM and edge.target == "一枝黄花饮片" for edge in herb_record.edges)
    assert any(edge.type == EdgeType.SUPPORTED_BY and edge.target == "一枝黄花条目证据" for edge in piece_record.edges)
    assert any(edge.type == EdgeType.HAS_FLAVOR and edge.target == "辛" for edge in piece_record.edges)
    assert any(edge.type == EdgeType.TREATS and edge.target == "喉痹" for edge in piece_record.edges)


def test_mapping_falls_back_to_herb_indications_when_piece_absent():
    """验证缺少饮片时仍会回退使用药材层的适应症生成病证关系。"""

    parsed = PharmacopoeiaEntrySections(
        title_zh="八角茴香",
        header_lines=[],
        base_description="本品为木兰科植物八角茴香的干燥成熟果实。",
        sections={},
        piece_sections={},
        raw_text="八角茴香\n本品为木兰科植物八角茴香的干燥成熟果实。",
    )
    block = RawEntryBlock(
        entry_id="entry-2",
        entry_title="八角茴香",
        raw_text=parsed.raw_text,
        start_line=1,
        end_line=2,
        context=SourceFileContext(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
            local_abspath="/tmp/2022.txt",
            file_size=128,
            line_count=2,
        ),
    )
    extraction = PharmacopoeiaExtractionResult(
        herb=PharmacopoeiaHerbExtraction(
            herb_name="八角茴香",
            indications=["寒疝腹痛", "胃寒呕吐"],
        ),
        prepared_piece=None,
    )

    bundle = build_pharmacopoeia_bundle(block, parsed, extraction)

    assert {node.name for node in bundle.nodes} >= {"八角茴香", "寒疝腹痛", "胃寒呕吐"}
    assert any(edge.type == EdgeType.TREATS and edge.source == "药材:八角茴香" for edge in bundle.edges)
