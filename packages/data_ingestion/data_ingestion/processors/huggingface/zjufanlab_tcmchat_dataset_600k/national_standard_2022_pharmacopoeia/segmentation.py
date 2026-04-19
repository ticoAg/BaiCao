"""实现药典源文件的条目切段与切分质量评估。"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from data_ingestion.source_models import RawEntryBlock, SourceFileContext


ENTRY_START_RULE = Literal["three_line_header", "body_text_fallback"]
BODY_TEXT_PREFIXES = ("本品为", "本品由")
EXCLUDED_ENTRY_TITLES = {"饮片"}
ENGLISH_LINE_CLEAN_RE = re.compile(r"[\s\-‐‑–—·．.()（）,，/:：]+")


class PharmacopoeiaEntryStart(BaseModel):
    """描述一个被识别为药典条目起点的位置和命中规则。"""

    entry_title: str = Field(description="条目标题")
    start_line: int = Field(description="起始行号（1-based）")
    rule: ENTRY_START_RULE = Field(description="命中的切分规则")
    header_lines: list[str] = Field(default_factory=list, description="命中的头部行")
    anomaly_flags: list[str] = Field(default_factory=list, description="头部异常标记")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaSegmentationSample(BaseModel):
    """记录需要人工复核的可疑条目样本。"""

    entry_title: str = Field(description="条目标题")
    start_line: int = Field(description="起始行号")
    rule: ENTRY_START_RULE = Field(description="命中的切分规则")
    anomaly_flags: list[str] = Field(default_factory=list, description="异常标记")
    raw_preview: str = Field(description="条目预览")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaEntryHealthCheck(BaseModel):
    """汇总单个条目的切分健康标签和头部信息。"""

    entry_title: str = Field(description="条目标题")
    start_line: int = Field(description="起始行号")
    rule: ENTRY_START_RULE = Field(description="命中的切分规则")
    health_labels: list[str] = Field(default_factory=list, description="条目健康标签")
    header_lines: list[str] = Field(default_factory=list, description="命中的头部行")

    model_config = ConfigDict(use_enum_values=False)


class PharmacopoeiaSegmentationAssessment(BaseModel):
    """汇总整份药典文件的切分质量统计结果。"""

    total_entries: int = Field(description="切分出的条目总数")
    start_rule_counts: dict[str, int] = Field(default_factory=dict, description="起始规则分布")
    excluded_title_counts: dict[str, int] = Field(default_factory=dict, description="被排除标题分布")
    duplicate_title_counts: dict[str, int] = Field(default_factory=dict, description="重复中文标题分布")
    mixed_case_third_line_count: int = Field(description="第三行包含小写字母的三行头部条目数")
    health_label_counts: dict[str, int] = Field(default_factory=dict, description="健康标签分布")
    entry_health_checks: list[PharmacopoeiaEntryHealthCheck] = Field(
        default_factory=list,
        description="每个条目的健康检查结果",
    )
    suspicious_entries: list[PharmacopoeiaSegmentationSample] = Field(
        default_factory=list,
        description="需要人工抽样复核的条目样本",
    )

    model_config = ConfigDict(use_enum_values=False)


def _is_cjk(char: str) -> bool:
    """判断单个字符是否属于常用中日韩统一表意文字区间。"""

    return "\u4e00" <= char <= "\u9fff"


def _looks_like_short_chinese_text(line: str) -> bool:
    """判断一行文本是否像一个简短中文标题。"""

    stripped = line.strip()
    if not stripped or not (2 <= len(stripped) <= 20):
        return False
    return all(_is_cjk(char) for char in stripped)


def _normalize_english_like_line(line: str) -> str:
    """去掉英文头部中的常见分隔符，便于后续规则判断。"""

    return ENGLISH_LINE_CLEAN_RE.sub("", line.strip())


def _looks_like_english_header_line(line: str) -> bool:
    """判断一行是否近似药典条目头部里的拼音/英文名称行。"""

    stripped = line.strip()
    if not stripped:
        return False
    if any(_is_cjk(char) for char in stripped):
        return False
    normalized = _normalize_english_like_line(stripped)
    if len(normalized) < 3:
        return False
    alpha_count = sum(1 for char in normalized if char.isalpha())
    return alpha_count >= max(3, int(len(normalized) * 0.8))


def _starts_with_body_text(line: str) -> bool:
    """判断一行是否已经进入“本品为/本品由”这类正文字段。"""

    stripped = line.strip()
    return any(stripped.startswith(prefix) for prefix in BODY_TEXT_PREFIXES)


def _classify_entry_start(lines: list[str], index: int) -> PharmacopoeiaEntryStart | None:
    """判断某一行能否作为条目起点，并返回对应命中的规则。"""

    line = lines[index].strip()
    if not _looks_like_short_chinese_text(line):
        return None
    if line in EXCLUDED_ENTRY_TITLES:
        return None

    next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
    third_line = lines[index + 2].strip() if index + 2 < len(lines) else ""

    # 标准药典条目大多符合“中文名 + 拼音/英文行 + 拉丁名/英文行”的三行头部。
    if _looks_like_english_header_line(next_line) and _looks_like_english_header_line(third_line):
        anomaly_flags: list[str] = []
        normalized_third_line = _normalize_english_like_line(third_line)
        if any(char.islower() for char in normalized_third_line):
            anomaly_flags.append("third_line_contains_lowercase")
        return PharmacopoeiaEntryStart(
            entry_title=line,
            start_line=index + 1,
            rule="three_line_header",
            header_lines=[line, next_line, third_line],
            anomaly_flags=anomaly_flags,
        )

    # 少数条目缺英文头部，但第二行会直接进入“本品为/本品由”正文，这里走兜底规则。
    if _starts_with_body_text(next_line):
        return PharmacopoeiaEntryStart(
            entry_title=line,
            start_line=index + 1,
            rule="body_text_fallback",
            header_lines=[line, next_line],
            anomaly_flags=["missing_english_header"],
        )

    return None


def find_pharmacopoeia_entry_starts(context: SourceFileContext) -> list[PharmacopoeiaEntryStart]:
    """扫描整份来源文件，找出所有疑似药典条目起点。"""

    lines = Path(context.local_abspath).read_text(encoding="utf-8").splitlines()
    starts: list[PharmacopoeiaEntryStart] = []
    for index in range(len(lines)):
        start = _classify_entry_start(lines, index)
        if start is not None:
            starts.append(start)
    return starts


def assess_pharmacopoeia_entry_segmentation(
    context: SourceFileContext,
    *,
    sample_limit: int = 20,
) -> PharmacopoeiaSegmentationAssessment:
    """生成药典条目切分的统计摘要和可疑样本列表。"""

    lines = Path(context.local_abspath).read_text(encoding="utf-8").splitlines()
    starts = find_pharmacopoeia_entry_starts(context)
    blocks = segment_pharmacopoeia_entries(context)

    start_rule_counts = Counter(start.rule for start in starts)
    excluded_title_counts = Counter(
        line.strip()
        for line in lines
        if _looks_like_short_chinese_text(line.strip()) and line.strip() in EXCLUDED_ENTRY_TITLES
    )
    title_counts = Counter(start.entry_title for start in starts)
    duplicate_title_counts = Counter({title: count for title, count in title_counts.items() if count > 1})
    mixed_case_third_line_count = sum(
        1 for start in starts if "third_line_contains_lowercase" in start.anomaly_flags
    )

    block_by_title = {(block.entry_title, block.start_line): block for block in blocks}
    starts_by_title: dict[str, list[PharmacopoeiaEntryStart]] = {}
    for start in starts:
        starts_by_title.setdefault(start.entry_title, []).append(start)

    health_label_counts = Counter()
    entry_health_checks: list[PharmacopoeiaEntryHealthCheck] = []
    suspicious_entries: list[PharmacopoeiaSegmentationSample] = []
    for start in starts:
        health_labels: list[str] = []
        if start.rule == "body_text_fallback":
            health_labels.append("header_missing_english")
        if "third_line_contains_lowercase" in start.anomaly_flags:
            health_labels.append("header_third_line_mixed_case")

        duplicate_starts = starts_by_title.get(start.entry_title, [])
        if len(duplicate_starts) > 1:
            # 同名条目既可能是源文本重复，也可能是标题相同但英文头部不同的真实冲突。
            header_pairs = {(tuple(item.header_lines[1:3]), item.rule) for item in duplicate_starts}
            if len(header_pairs) > 1:
                health_labels.append("duplicate_title_with_distinct_headers")
            else:
                health_labels.append("duplicate_title_repeated")

        for label in health_labels:
            health_label_counts[label] += 1

        entry_health_checks.append(
            PharmacopoeiaEntryHealthCheck(
                entry_title=start.entry_title,
                start_line=start.start_line,
                rule=start.rule,
                health_labels=health_labels,
                header_lines=start.header_lines,
            )
        )

        # 可疑样本只保留真正值得人工抽样的项；大小写异常单独计数，不单独挤占样本配额。
        anomaly_flags = [label for label in health_labels if label != "header_third_line_mixed_case"]
        if anomaly_flags:
            block = block_by_title.get((start.entry_title, start.start_line))
            raw_preview = ""
            if block is not None:
                raw_preview = block.raw_text.replace("\n", " ")[:200]
            suspicious_entries.append(
                PharmacopoeiaSegmentationSample(
                    entry_title=start.entry_title,
                    start_line=start.start_line,
                    rule=start.rule,
                    anomaly_flags=anomaly_flags,
                    raw_preview=raw_preview,
                )
            )
            if len(suspicious_entries) >= sample_limit:
                break

    return PharmacopoeiaSegmentationAssessment(
        total_entries=len(blocks),
        start_rule_counts=dict(start_rule_counts),
        excluded_title_counts=dict(excluded_title_counts),
        duplicate_title_counts=dict(duplicate_title_counts),
        mixed_case_third_line_count=mixed_case_third_line_count,
        health_label_counts=dict(health_label_counts),
        entry_health_checks=entry_health_checks,
        suspicious_entries=suspicious_entries,
    )


def _looks_like_entry_title(lines: list[str], index: int) -> bool:
    """兼容早期调用方的标题判定辅助函数。"""

    return _classify_entry_start(lines, index) is not None


def segment_pharmacopoeia_entries(context: SourceFileContext) -> list[RawEntryBlock]:
    """按识别出的起点把来源文件切成连续的原始条目块。"""

    lines = Path(context.local_abspath).read_text(encoding="utf-8").splitlines()
    starts = [start.start_line - 1 for start in find_pharmacopoeia_entry_starts(context)]
    blocks: list[RawEntryBlock] = []

    for idx, start in enumerate(starts):
        # 每个起点向后切到下一个起点前一行，形成完整条目块，供后续解析与映射复用。
        end = starts[idx + 1] - 1 if idx + 1 < len(starts) else len(lines) - 1
        chunk = "\n".join(lines[start : end + 1]).strip()
        blocks.append(
            RawEntryBlock(
                entry_id=f"{context.dataset}:{context.file_path}:{lines[start].strip()}:{start + 1}",
                entry_title=lines[start].strip(),
                raw_text=chunk,
                start_line=start + 1,
                end_line=end + 1,
                context=context,
            )
        )

    return blocks
