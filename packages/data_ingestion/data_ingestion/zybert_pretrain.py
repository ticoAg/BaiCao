"""解压 ZY-BERT 预训练 RAR，抽取书目方剂索引行。"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.entity_identity import EntityDraft
from data_ingestion.organize_workflow import finalize_drafts
from data_ingestion.provenance import prompt_hash_for
from data_ingestion.tcmchat_case_units import default_lexicon_paths, load_lexicon, longest_lexicon_hits

SOURCE_ID = "zybert-pretrain-corpus"
IMPORT_SCOPE_KEY = "dropbox:zybert:tcm_pretrain_corpus_a.rar"
DEFAULT_BATCH_ID = "2026-08-20-zybert-pretrain-v2"
MENTION_BATCH_ID = "2026-08-20-zybert-mentions-v1"
PROCESSOR = "zybert_pretrain"
MENTION_PROCESSOR = "zybert_pretrain_mentions"
CORPUS_SOURCE_NAME = "ZY-BERT预训练语料"
PROMPT_HASH = prompt_hash_for(Path(__file__))
RAR_MAGIC = b"Rar!"
FORMULA_LINE_RE = re.compile(
    r"^(?P<name>[\u4e00-\u9fff]{2,30})"
    r"[（(](?P<source>[^）)]{1,80})[）)]"
    r"(?:[（(]又名[^）)]+[）)])?"
    r"\s+(?P<body>.+)$"
)
DOSAGE_RE = re.compile(r"^[一二三四五六七八九十百千万半\d]+\s*(两|钱|分|升|合|勺|铢|枚|个|只|斤)")
BOOKISH_RE = re.compile(
    r"《|》|验方|经验|药典|标准|局方|金匮|伤寒|景岳|医宗|本草|心法|准绳|入门|直诀|良方|医话|医案|集成|大全|全书|纲目|条辨"
)
HERB_PAREN_RE = re.compile(r"[（(][^）)]*[）)]")


class ZybertPretrainError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root()
    / ".cache/dropbox/zybert/tcm_pretrain_corpus_a.rar"
)
DEFAULT_EXTRACTED_PATH = (
    repo_root() / ".cache/dropbox/zybert/extracted/tcm_pretrain_corpus_a.txt"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def parse_bsdtar_listing(listing: str) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) < 9:
            continue
        name = parts[-1]
        try:
            size = int(parts[4])
        except ValueError:
            size = None
        members.append({"name": name, "size": size, "listing": line})
    if not members:
        raise ZybertPretrainError("rar listing is empty")
    return members


def extract_rar(path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / "tcm_pretrain_corpus_a.txt"
    if target.is_file() and target.stat().st_size > 0:
        return target
    try:
        result = subprocess.run(
            ["bsdtar", "-xf", str(path), "-C", str(dest_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ZybertPretrainError("bsdtar is required to extract the rar archive") from exc
    if result.returncode != 0 or not target.is_file():
        raise ZybertPretrainError(
            f"bsdtar extract failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return target


def _clean_herb_token(token: str) -> str:
    name = HERB_PAREN_RE.sub("", token).strip("，,、；; ")
    if len(name) < 2 or name in {"等", "各等分"}:
        return ""
    if DOSAGE_RE.match(name):
        return ""
    return name


def parse_formula_index_lines(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        match = FORMULA_LINE_RE.match(line)
        if not match:
            continue
        source = match.group("source").strip()
        if DOSAGE_RE.match(source) or not BOOKISH_RE.search(source):
            continue
        name = match.group("name").strip()
        if "注射" in name:
            continue
        herbs = []
        seen: set[str] = set()
        for token in match.group("body").split():
            herb = _clean_herb_token(token)
            if not herb or herb in seen:
                continue
            seen.add(herb)
            herbs.append(herb)
        if not herbs:
            continue
        book = source.strip("《》")
        rows.append(
            {
                "name": name,
                "source": book,
                "herbs": herbs,
                "line": line_no,
            }
        )
    return rows


def _drafts_from_rows(rows: list[dict[str, Any]]) -> list[EntityDraft]:
    drafts: list[EntityDraft] = []
    books: set[str] = set()
    herbs: set[str] = set()
    for item in rows:
        book = item["source"]
        if book not in books:
            books.add(book)
            drafts.append(
                EntityDraft(
                    node_type=NodeType.SOURCE,
                    raw_name=book,
                    role="方剂书目",
                    stable_id=book,
                    evidence_refs=[f"tcm_pretrain_corpus_a.txt:{item['line']}"],
                    properties={"tcm_type": "来源方剂索引"},
                )
            )
        for herb in item["herbs"]:
            if herb in herbs:
                continue
            herbs.add(herb)
            drafts.append(
                EntityDraft(
                    node_type=NodeType.HERB,
                    raw_name=herb,
                    role="药材",
                    stable_id=herb,
                    evidence_refs=[f"tcm_pretrain_corpus_a.txt:{item['line']}"],
                    properties={"tcm_type": "来源方剂索引"},
                )
            )
        drafts.append(
            EntityDraft(
                node_type=NodeType.FORMULA,
                raw_name=item["name"],
                role="方剂",
                stable_id=f"{item['name']}|{book}",
                evidence_refs=[f"tcm_pretrain_corpus_a.txt:{item['line']}"],
                properties={
                    "tcm_type": "来源方剂索引",
                    "source_book": book,
                },
                edges=[
                    (EdgeType.CONTAINS_HERB.value, herb) for herb in item["herbs"]
                ]
                + [(EdgeType.ORIGINATED_FROM.value, book)],
            )
        )
    return drafts


def list_rar_members(path: Path) -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["bsdtar", "-tvf", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise ZybertPretrainError("bsdtar is required to list the rar archive") from exc
    if result.returncode != 0:
        raise ZybertPretrainError(
            f"bsdtar failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return parse_bsdtar_listing(result.stdout)


def clean_file(
    path: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = DEFAULT_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not path.is_file():
        raise ZybertPretrainError(f"missing archive: {path}")
    header = path.read_bytes()[:4]
    if header != RAR_MAGIC:
        raise ZybertPretrainError(f"{path.name} is not a RAR archive")
    members = list_rar_members(path)
    extracted = extract_rar(path, path.parent / "extracted")
    rows = parse_formula_index_lines(
        extracted.read_text(encoding="utf-8", errors="replace")
    )
    records, quarantined, identity_report = finalize_drafts(
        _drafts_from_rows(rows),
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
        processor=PROCESSOR,
    )
    report = {
        "publish": False,
        "license_status": "unverified_dropbox_archive_not_inherited_from_tcm_sd",
        "consumed_files": [path.name, extracted.name],
        "file_sha256": {path.name: _sha256(path)},
        "archive_bytes": path.stat().st_size,
        "extracted_bytes": extracted.stat().st_size,
        "members": [{"name": item["name"], "size": item["size"]} for item in members],
        "parsed_formula_rows": len(rows),
        "mapped_relation_counts": {},
        "quarantine_counts": {
            "archive_members": len(members),
            "uncompressed_bytes": sum(item["size"] or 0 for item in members),
            "brand_names": identity_report.get("brand_quarantine", 0),
        },
        "quality_samples": {
            "members": [item["name"] for item in members],
            "formulas": [item["name"] for item in rows[:20]],
        },
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
        **identity_report,
        "quarantined": quarantined[:20],
    }
    return records, report


def extract_remaining_mentions(
    extracted: Path,
    *,
    source_id: str = SOURCE_ID,
    batch_id: str = MENTION_BATCH_ID,
    import_scope_key: str = IMPORT_SCOPE_KEY,
    lexicon_path: Path | list[Path] | None = None,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    if not extracted.is_file():
        raise ZybertPretrainError(f"missing extracted corpus: {extracted}")
    lexicon = load_lexicon(lexicon_path if lexicon_path is not None else default_lexicon_paths())
    drafts: list[EntityDraft] = [
        EntityDraft(
            node_type=NodeType.SOURCE,
            raw_name=CORPUS_SOURCE_NAME,
            role="预训练语料",
            stable_id=CORPUS_SOURCE_NAME,
            evidence_refs=[extracted.name],
            properties={"tcm_type": "来源方剂索引", "source_book": CORPUS_SOURCE_NAME},
        )
    ]
    scanned = 0
    skipped_index = 0
    mention_count = 0
    seen: set[tuple[str, str]] = set()
    buffer: list[str] = []
    buffer_chars = 0
    chunk_start_line = 1
    chunk_size = 1_000_000

    def flush(evidence_line: int) -> None:
        nonlocal buffer, buffer_chars, mention_count
        if not buffer:
            return
        text = "\n".join(buffer)
        buffer = []
        buffer_chars = 0
        for name, node_type in longest_lexicon_hits(text, lexicon):
            key = (node_type, name)
            if key in seen:
                continue
            seen.add(key)
            mention_count += 1
            drafts.append(
                EntityDraft(
                    node_type=NodeType(node_type),
                    raw_name=name,
                    role="语料提及",
                    stable_id=name,
                    evidence_refs=[f"{extracted.name}:{evidence_line}:{name}"],
                    properties={"tcm_type": "来源方剂索引提及"},
                    edges=[(EdgeType.ORIGINATED_FROM.value, CORPUS_SOURCE_NAME)],
                )
            )

    for line_no, raw in enumerate(
        extracted.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
        line = raw.strip()
        if not line:
            continue
        if FORMULA_LINE_RE.match(line):
            skipped_index += 1
            continue
        if not buffer:
            chunk_start_line = line_no
        scanned += 1
        buffer.append(line)
        buffer_chars += len(line)
        if buffer_chars >= chunk_size:
            flush(chunk_start_line)
    flush(chunk_start_line)
    records, quarantined, identity = finalize_drafts(
        drafts,
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
        processor=MENTION_PROCESSOR,
    )
    report = {
        "publish": False,
        "license_status": "unverified_dropbox_archive_not_inherited_from_tcm_sd",
        "scanned_non_index_lines": scanned,
        "skipped_index_lines": skipped_index,
        "raw_mention_hits": mention_count,
        "lexicon_size": len(lexicon),
        "source_id": source_id,
        "batch_id": batch_id,
        "import_scope_key": import_scope_key,
        "processor": MENTION_PROCESSOR,
        "prompt_hash": PROMPT_HASH,
        **identity,
        "quarantined": quarantined[:20],
    }
    return records, report


def write_clean_outputs(
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
