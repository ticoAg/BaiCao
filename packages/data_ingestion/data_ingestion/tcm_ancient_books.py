"""只读审计 TCM-Ancient-Books：建立书目台账，不把全文提升为图事实。"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.entity_identity import EntityDraft
from data_ingestion.organize_workflow import finalize_drafts
from data_ingestion.provenance import prompt_hash_for
from data_ingestion.tcmchat_case_units import default_lexicon_paths, load_lexicon, longest_lexicon_hits

SOURCE_ID = "tcm-ancient-books"
IMPORT_SCOPE_KEY = "github:xiaopangxia/TCM-Ancient-Books"
DEFAULT_BATCH_ID = "2026-08-19-tcm-ancient-books-v1"
MENTION_BATCH_ID = "2026-08-20-ancient-mentions-v1"
PROCESSOR = "tcm_ancient_books"
MENTION_PROCESSOR = "tcm_ancient_books_mentions"
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


def decode_book_bytes(raw: bytes) -> tuple[str, str, int]:
    try:
        text, encoding = _decode(raw)
        return text, encoding, 0
    except TcmAncientBooksError:
        text = raw.decode("gb18030", errors="replace")
        return text, "gb18030-replace", text.count("\ufffd")


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


def extract_directory(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = MENTION_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
    min_id: int = 0,
    max_id: int = 999,
    include_unnumbered: bool = False,
    lexicon_path: Path | list[Path] | None = None,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_dir():
        raise TcmAncientBooksError(f"input is not a directory: {path}")
    lexicon = load_lexicon(lexicon_path if lexicon_path is not None else default_lexicon_paths())
    drafts: list[EntityDraft] = []
    mention_count = 0
    books: list[dict[str, Any]] = []
    for file_path in sorted(path.iterdir(), key=lambda item: item.name):
        if not file_path.is_file():
            continue
        name = file_path.name
        if name.endswith(".downloading") or name.endswith(".downloading.cfg"):
            continue
        match = NUMBERED_RE.match(name)
        raw = file_path.read_bytes()
        if not raw:
            continue
        if match:
            book_id = int(match.group(1))
            if book_id < min_id or book_id > max_id:
                continue
            title = match.group(2).strip()
            text, encoding, replacements = decode_book_bytes(raw)
            role = "古籍"
            tcm_type = "来源古籍书目"
            stable_id = f"{book_id:03d}"
            term_code = f"{book_id:03d}"
        elif include_unnumbered and name.endswith(".txt") and name not in {"README.txt"}:
            title = Path(name).stem
            text, encoding, replacements = decode_book_bytes(raw)
            role = "现代医论"
            tcm_type = "来源现代医论"
            stable_id = title
            term_code = ""
            book_id = None
        else:
            continue
        books.append(
            {
                "file": name,
                "title": title,
                "encoding": encoding,
                "replacements": replacements,
                "chars": len(text),
            }
        )
        properties = {
            "tcm_type": tcm_type,
            "source_book": title,
        }
        if term_code:
            properties["term_code"] = term_code
        drafts.append(
            EntityDraft(
                node_type=NodeType.SOURCE,
                raw_name=title,
                role=role,
                stable_id=stable_id,
                evidence_refs=[name],
                properties=properties,
            )
        )
        for hit_name, node_type in longest_lexicon_hits(text, lexicon):
            mention_count += 1
            drafts.append(
                EntityDraft(
                    node_type=NodeType(node_type),
                    raw_name=hit_name,
                    role=f"{role}提及",
                    stable_id=hit_name,
                    evidence_refs=[f"{name}:{hit_name}"],
                    # Mentions merge by name across 古籍/现代医论; keep tcm_type stable.
                    properties={"tcm_type": "来源古籍书目提及"},
                    edges=[(EdgeType.ORIGINATED_FROM.value, title)],
                )
            )
    if not drafts:
        raise TcmAncientBooksError("no books in id range")
    records, quarantined, identity = finalize_drafts(
        drafts,
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
        processor=MENTION_PROCESSOR,
    )
    report = {
        "publish": False,
        "license_status": "unlicensed_upstream_digital_edition_unverified",
        "book_count": len(books),
        "min_id": min_id,
        "max_id": max_id,
        "include_unnumbered": include_unnumbered,
        "lexicon_size": len(lexicon),
        "raw_mention_hits": mention_count,
        "titles": [item["title"] for item in books],
        "lossy_decode_files": [item["file"] for item in books if item["replacements"]],
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": MENTION_PROCESSOR,
        "prompt_hash": PROMPT_HASH,
        **identity,
        "quarantined": quarantined[:20],
    }
    return records, report


def write_extract_outputs(
    records: list[DatasetRecord], report: dict[str, Any], out_dir: Path
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records),
        encoding="utf-8",
    )
    stats = {**compute_stats(records), **report}
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": len(records),
        "edge_count": sum(len(record.edges) for record in records),
        "publish": False,
    }


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
