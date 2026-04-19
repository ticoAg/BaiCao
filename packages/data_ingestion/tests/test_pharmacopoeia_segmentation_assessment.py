"""覆盖药典条目切分评估的统计与可疑样本逻辑。"""

from pathlib import Path

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.segmentation import (
    assess_pharmacopoeia_entry_segmentation,
    segment_pharmacopoeia_entries,
)
from data_ingestion.source_models import SourceFileContext


def _build_context(source: Path) -> SourceFileContext:
    """为临时样例文件构造最小来源上下文。"""

    return SourceFileContext(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath=str(source),
        file_size=source.stat().st_size,
        line_count=source.read_text(encoding="utf-8").count("\n") + 1,
    )


def test_segmenter_accepts_mixed_case_third_header_line(tmp_path):
    """验证第三行混合大小写时条目仍可被切分出来。"""

    # 第三行出现混合大小写时不应直接丢条目，只标记为可疑并继续切段。
    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "蛇床子\n"
            "Shengchuangzi\n"
            "CnidiiFructus\n"
            "本品为伞形科植物蛇床的干燥成熟果实。\n"
            "饮片\n"
            "【炮制】除去杂质。\n"
            "人工牛黄\n"
            "本品由牛胆粉等加工制成。\n"
        ),
        encoding="utf-8",
    )

    blocks = segment_pharmacopoeia_entries(_build_context(source))

    assert [block.entry_title for block in blocks] == ["蛇床子", "人工牛黄"]
    assert blocks[0].raw_text.startswith("蛇床子\nShengchuangzi\nCnidiiFructus")


def test_segmenter_falls_back_to_body_sentence_when_english_header_missing(tmp_path):
    """验证缺英文头部时会回退使用正文前缀规则。"""

    # 缺英文头部的条目仍应能通过正文前缀兜底识别出来。
    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "人工牛黄\n"
            "本品由牛胆粉、胆酸等加工制成。\n"
            "【性状】本品为黄色疏松粉末。\n"
            "人参\n"
            "Renshen\n"
            "GINSENGRADIXETRHIZOMA\n"
            "本品为五加科植物人参的干燥根和根茎。\n"
        ),
        encoding="utf-8",
    )

    blocks = segment_pharmacopoeia_entries(_build_context(source))

    assert [block.entry_title for block in blocks] == ["人工牛黄", "人参"]
    assert blocks[0].end_line == 3


def test_assessment_counts_header_rules_and_suspicious_entries(tmp_path):
    """验证切分评估会正确统计规则分布和健康标签。"""

    # 评估摘要需要同时覆盖规则分布、排除标题和健康标签统计。
    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "蛇床子\n"
            "Shengchuangzi\n"
            "CnidiiFructus\n"
            "本品为伞形科植物蛇床的干燥成熟果实。\n"
            "饮片\n"
            "【炮制】除去杂质。\n"
            "人工牛黄\n"
            "本品由牛胆粉、胆酸等加工制成。\n"
        ),
        encoding="utf-8",
    )

    assessment = assess_pharmacopoeia_entry_segmentation(_build_context(source))

    assert assessment.total_entries == 2
    assert assessment.start_rule_counts["three_line_header"] == 1
    assert assessment.start_rule_counts["body_text_fallback"] == 1
    assert assessment.excluded_title_counts["饮片"] == 1
    assert assessment.mixed_case_third_line_count == 1
    assert assessment.health_label_counts["header_missing_english"] == 1
    assert assessment.health_label_counts["header_third_line_mixed_case"] == 1
    assert any(
        check.entry_title == "人工牛黄" and "header_missing_english" in check.health_labels
        for check in assessment.entry_health_checks
    )


def test_assessment_flags_duplicate_titles_with_distinct_headers(tmp_path):
    """验证重复标题但头部不同会被标记为冲突样本。"""

    # 同名标题但英文头部不同，应该被识别为更高优先级的冲突样本。
    source = tmp_path / "sample.txt"
    source.write_text(
        (
            "五倍子\n"
            "Wuweizi\n"
            "SCHISANDRAECHINENSISFRUCTUS\n"
            "本品为木兰科植物五味子的干燥成熟果实。\n"
            "五倍子\n"
            "Wubeizi\n"
            "GALLACHINENSIS\n"
            "本品为漆树科植物盐肤木叶上的虫瘿。\n"
        ),
        encoding="utf-8",
    )

    assessment = assess_pharmacopoeia_entry_segmentation(_build_context(source))

    assert assessment.duplicate_title_counts["五倍子"] == 2
    assert assessment.health_label_counts["duplicate_title_with_distinct_headers"] == 2
    assert any(
        sample.entry_title == "五倍子" and "duplicate_title_with_distinct_headers" in sample.anomaly_flags
        for sample in assessment.suspicious_entries
    )
    assert any(
        check.entry_title == "五倍子" and "duplicate_title_with_distinct_headers" in check.health_labels
        for check in assessment.entry_health_checks
    )
