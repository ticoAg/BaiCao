from pathlib import Path

from data_ingestion.source_models import RawEntryBlock, SourceFileContext


def _looks_like_entry_title(lines: list[str], index: int) -> bool:
    line = lines[index].strip()
    if not line or not (2 <= len(line) <= 20):
        return False
    if any(not ("\u4e00" <= char <= "\u9fff") for char in line):
        return False
    if index + 1 >= len(lines):
        return False
    next_line = lines[index + 1].strip()
    return next_line.isascii() and next_line.isalpha()


def segment_pharmacopoeia_entries(context: SourceFileContext) -> list[RawEntryBlock]:
    lines = Path(context.local_abspath).read_text(encoding="utf-8").splitlines()
    starts = [index for index in range(len(lines)) if _looks_like_entry_title(lines, index)]
    blocks: list[RawEntryBlock] = []

    for idx, start in enumerate(starts):
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
