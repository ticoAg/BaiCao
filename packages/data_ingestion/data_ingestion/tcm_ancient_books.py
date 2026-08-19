"""只读审计 TCM-Ancient-Books：建立书目台账，不把全文提升为图事实。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcm-ancient-books"
IMPORT_SCOPE_KEY = "github:xiaopangxia/TCM-Ancient-Books"
DEFAULT_BATCH_ID = "2026-08-19-tcm-ancient-books-v1"
PROCESSOR = "tcm_ancient_books"
PROMPT_HASH = prompt_hash_for(Path(__file__))
NUMBERED_RE = re.compile(r"^(\d{3})-(.+)\.txt$")
PREFERRED_ENCODINGS = ("utf-8", "gb18030")


class TcmAncientBooksError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = repo_root() / ".cache/github/xiaopangxia/TCM-Ancient-Books"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decode(raw: bytes) -> tuple[str, str]:
    for encoding in PREFERRED_ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise TcmAncientBooksError("cannot decode book with utf-8 or gb18030")


def clean_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise TcmAncientBooksError(f"input is not a directory: {path}")

    numbered: list[dict[str, Any]] = []
    isolated: list[dict[str, str]] = []
    titles: dict[str, str] = {}
    encodings: dict[str, int] = {}
    present_ids: list[int] = []
    total_bytes = 0

    for file_path in sorted(path.iterdir(), key=lambda item: item.name):
        if not file_path.is_file():
            continue
        name = file_path.name
        if name in {".DS_Store"} or name.startswith("."):
            continue
        if name in {"README.md", "LICENSE", "LICENSE.md"}:
            isolated.append({"file": name, "reason": "repo_metadata"})
            continue
        if name.endswith(".downloading") or name.endswith(".downloading.cfg"):
            isolated.append({"file": name, "reason": "incomplete_download"})
            continue
        match = NUMBERED_RE.match(name)
        if match is None:
            isolated.append({"file": name, "reason": "unnumbered_or_non_txt"})
            continue
        book_id = int(match.group(1))
        present_ids.append(book_id)
        title = match.group(2).strip()
        if not title:
            raise TcmAncientBooksError(f"{name} has empty title")
        if title in titles:
            raise TcmAncientBooksError(f"duplicate title {title}: {titles[title]} vs {name}")
        raw = file_path.read_bytes()
        if not raw:
            raise TcmAncientBooksError(f"{name} is empty")
        try:
            _text, encoding = _decode(raw)
        except TcmAncientBooksError:
            isolated.append({"file": name, "reason": "decode_error"})
            continue
        encodings[encoding] = encodings.get(encoding, 0) + 1
        titles[title] = name
        total_bytes += len(raw)
        numbered.append(
            {
                "book_id": book_id,
                "title": title,
                "file": name,
                "encoding": encoding,
                "bytes": len(raw),
            }
        )

    if not numbered:
        raise TcmAncientBooksError("no numbered book files found")
    ids = [item["book_id"] for item in numbered]
    expected = list(range(min(present_ids), max(present_ids) + 1))
    missing = sorted(set(expected) - set(present_ids))
    if missing:
        raise TcmAncientBooksError(f"missing book ids: {missing[:20]}")

    records: list[DatasetRecord] = []
    report = {
        "publish": False,
        "license_status": "unlicensed_upstream_digital_edition_unverified",
        "consumed_files": [item["file"] for item in numbered],
        "isolated_files": isolated,
        "source_doc_counts": {
            "numbered_books": len(numbered),
            "isolated_files": len(isolated),
        },
        "book_count": len(numbered),
        "book_id_min": min(ids),
        "book_id_max": max(ids),
        "encoding_counts": encodings,
        "total_bytes": total_bytes,
        "directory_sha256": _sha256(path / numbered[0]["file"]),
        "first_book": numbered[0]["title"],
        "last_book": numbered[-1]["title"],
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "full_text_books": len(numbered),
            "incomplete_downloads": sum(
                1 for item in isolated if item["reason"] == "incomplete_download"
            ),
            "decode_errors": sum(1 for item in isolated if item["reason"] == "decode_error"),
            "unnumbered_files": sum(
                1 for item in isolated if item["reason"] == "unnumbered_or_non_txt"
            ),
        },
        "quality_samples": {
            "isolated_files": isolated,
            "modern_looking_titles": [
                item["title"]
                for item in numbered
                if any(
                    marker in item["title"]
                    for marker in ("思考中医", "中医之钥", "余无言", "李翰卿", "名老中医之路")
                )
            ],
        },
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
    }
    return records, report


def write_clean_outputs(
    records: list[DatasetRecord], report: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    if records:
        raise TcmAncientBooksError("TCM-Ancient-Books must not emit graph records this round")
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text("", encoding="utf-8")
    slim_report = dict(report)
    slim_report["consumed_files"] = [
        report["consumed_files"][0],
        f"... {report['book_count'] - 2} more ...",
        report["consumed_files"][-1],
    ] if report["book_count"] > 2 else report["consumed_files"]
    stats = {**compute_stats(records), **slim_report}
    stats_path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": 0,
        "edge_count": 0,
        "publish": False,
    }
