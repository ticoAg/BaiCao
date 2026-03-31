from data_ingestion.source_models import RawEntryBlock, SourceFileContext
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.parsing import (
    parse_pharmacopoeia_entry,
)


def test_parser_extracts_piece_sections():
    block = RawEntryBlock(
        entry_id="entry-1",
        entry_title="一枝黄花",
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n饮片\n【炮制】除去杂质\n【性味与归经】辛、苦，凉。归肺、肝经。\n【功能与主治】清热解毒，疏散风热。",
        start_line=1,
        end_line=8,
        context=SourceFileContext(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
            local_abspath="/tmp/sample.txt",
            file_size=128,
            line_count=8,
        ),
    )

    parsed = parse_pharmacopoeia_entry(block)

    assert parsed.title_zh == "一枝黄花"
    assert parsed.piece_sections["炮制"] == "除去杂质"
    assert parsed.piece_sections["性味与归经"].startswith("辛、苦")
