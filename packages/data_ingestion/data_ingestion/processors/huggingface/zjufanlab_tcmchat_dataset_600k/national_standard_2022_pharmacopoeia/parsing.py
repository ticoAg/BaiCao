"""把原始药典条目块解析为章节化结构。"""

import re

from data_ingestion.source_models import RawEntryBlock

from .extraction_models import PharmacopoeiaEntrySections


SECTION_RE = re.compile(r"【([^】]+)】")


def _split_piece_text(raw_text: str) -> tuple[str, str]:
    """按“饮片”标记把药材正文和饮片正文拆成两段。"""

    marker = "\n饮片\n"
    if marker not in raw_text:
        return raw_text, ""
    return raw_text.split(marker, 1)


def _extract_header_lines(before_piece: str) -> list[str]:
    """提取标题后的两行头部信息，通常对应拼音名和英文/拉丁名。"""

    lines = [line.strip() for line in before_piece.splitlines() if line.strip()]
    return lines[1:3]


def _extract_base_description(before_piece: str) -> str | None:
    """提取紧随头部之后的第一段基础描述正文。"""

    lines = [line.strip() for line in before_piece.splitlines() if line.strip()]
    for line in lines[3:]:
        if not line.startswith("【"):
            return line
    return None


def _extract_sections(text: str) -> dict[str, str]:
    """把带有【章节名】标记的正文拆成章节字典。"""

    matches = list(SECTION_RE.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        section_name = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[section_name] = text[start:end].strip()
    return sections


def parse_pharmacopoeia_entry(block: RawEntryBlock) -> PharmacopoeiaEntrySections:
    """把原始条目块解析成供抽取阶段消费的章节对象。"""

    before_piece, piece_text = _split_piece_text(block.raw_text)
    return PharmacopoeiaEntrySections(
        title_zh=block.entry_title,
        header_lines=_extract_header_lines(before_piece),
        base_description=_extract_base_description(before_piece),
        sections=_extract_sections(before_piece),
        piece_sections=_extract_sections(piece_text) if piece_text else {},
        raw_text=block.raw_text,
    )
