"""把道医苏子阳原文拷进 staging，并按章节拆成独立文件与抽取批次。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

CHAPTER_RE = re.compile(r"^## 第(\d+)章[^\n]*", re.MULTILINE)
DEFAULT_INTAKE = Path("/Users/ticoag/Downloads/道医苏子阳.md")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def split_chapters(text: str) -> list[dict[str, object]]:
    matches = list(CHAPTER_RE.finditer(text))
    if not matches:
        raise ValueError("no chapter headings found")
    chapters: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(0).removeprefix("## ").strip()
        number = int(match.group(1))
        body = text[start:end].strip() + "\n"
        chapters.append(
            {
                "chapter_number": number,
                "title": title,
                "unit_id": f"chapter-{number:03d}",
                "text": body,
                "char_count": len(body),
                "line_count": body.count("\n"),
            }
        )
    return chapters


def write_batches(chapters: list[dict[str, object]], batch_dir: Path, batch_size: int) -> list[dict[str, object]]:
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifests: list[dict[str, object]] = []
    for offset in range(0, len(chapters), batch_size):
        chunk = chapters[offset : offset + batch_size]
        batch_index = offset // batch_size + 1
        batch_id = f"2026-08-16-suyang-b{batch_index:02d}"
        first = int(chunk[0]["chapter_number"])
        last = int(chunk[-1]["chapter_number"])
        batch_path = batch_dir / f"batch-{batch_index:02d}-ch{first:03d}-{last:03d}.md"
        parts = [
            f"# batch {batch_id}",
            f"chapters {first}-{last}",
            "用 `===CHAPTER===` 分隔。只抽本文件内的章节。",
            "",
        ]
        for chapter in chunk:
            parts.append("===CHAPTER===")
            parts.append(f"UNIT_ID={chapter['unit_id']}")
            parts.append(f"TITLE={chapter['title']}")
            parts.append("")
            parts.append(str(chapter["text"]).rstrip())
            parts.append("")
        batch_path.write_text("\n".join(parts), encoding="utf-8")
        manifests.append(
            {
                "batch_id": batch_id,
                "batch_index": batch_index,
                "path": str(batch_path),
                "chapter_start": first,
                "chapter_end": last,
                "unit_ids": [chapter["unit_id"] for chapter in chunk],
            }
        )
    return manifests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument("--batch-size", type=int, default=40)
    args = parser.parse_args()
    if not args.intake.is_file():
        raise SystemExit(f"intake not found: {args.intake}")

    source_root = repo_root() / "datasets/baicao-knowledge/sources/daoyi-suyang"
    source_dir = source_root / "source"
    chapters_dir = source_root / "source/chapters"
    batch_dir = source_root / "work/batches"
    source_dir.mkdir(parents=True, exist_ok=True)
    chapters_dir.mkdir(parents=True, exist_ok=True)

    dest = source_dir / "道医苏子阳.md"
    shutil.copy2(args.intake, dest)
    text = dest.read_text(encoding="utf-8")
    chapters = split_chapters(text)
    for chapter in chapters:
        path = chapters_dir / f"{chapter['unit_id']}.md"
        path.write_text(str(chapter["text"]), encoding="utf-8")
    manifests = write_batches(chapters, batch_dir, args.batch_size)
    manifest = {
        "source_id": "daoyi-suyang",
        "intake": str(args.intake),
        "copied_to": str(dest),
        "chapter_count": len(chapters),
        "batch_size": args.batch_size,
        "batches": manifests,
        "chapters": [
            {
                "unit_id": chapter["unit_id"],
                "title": chapter["title"],
                "char_count": chapter["char_count"],
                "line_count": chapter["line_count"],
            }
            for chapter in chapters
        ],
    }
    manifest_path = source_root / "work/split_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"chapters={len(chapters)} batches={len(manifests)} manifest={manifest_path}")


if __name__ == "__main__":
    main()
