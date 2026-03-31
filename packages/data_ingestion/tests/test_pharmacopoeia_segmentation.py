from data_ingestion.source_models import SourceFileContext
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.segmentation import (
    segment_pharmacopoeia_entries,
)


def test_segmenter_extracts_first_herb_entry_from_sample(tmp_path):
    source = tmp_path / "sample.txt"
    source.write_text(
        "一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n饮片\n【炮制】除去杂质\n【性味与归经】辛、苦，凉。归肺、肝经。\n丁香\nDingxiang\n",
        encoding="utf-8",
    )
    context = SourceFileContext(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath=str(source),
        file_size=source.stat().st_size,
        line_count=source.read_text(encoding="utf-8").count("\n") + 1,
    )

    blocks = segment_pharmacopoeia_entries(context)

    assert blocks[0].entry_title == "一枝黄花"
    assert "饮片" in blocks[0].raw_text
    assert blocks[0].end_line < context.line_count
