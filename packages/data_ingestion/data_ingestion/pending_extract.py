"""PEND 可用源的高确定性抽取：切分、过滤、身份门禁。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from graph_schema.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetRecord, compute_stats
from data_ingestion.entity_identity import (
    EntityDraft,
    contains_brand,
    name_key,
    redact_sensitive,
)
from data_ingestion.organize_workflow import finalize_drafts
from data_ingestion.provenance import prompt_hash_for
from data_ingestion.source_layout import (
    ensure_source_layout,
    processed_latest_dir,
    work_dir,
)
from data_ingestion.tcm_ancient_books import NUMBERED_RE, _decode
from data_ingestion.tcmchat_case_units import longest_lexicon_hits

PROMPT_HASH = prompt_hash_for(Path(__file__))
FORMULA_ASK_RE = re.compile(r"请对(.+?)(?:成药)?说明")
HERB_INTRO_RE = re.compile(r"中药(.+?)介绍")
BRACKET_RE = re.compile(r"【([^】]+)】([^【]*)")
NAME_KIND_RE = re.compile(r"^(.{2,40}?)是一种(方剂|中药材|中药)")
PRESCRIPTION_BODY_RE = re.compile(r"其处方由(.+?)组成")
TOKEN_SPLIT_RE = re.compile(r"[、，,；;]+")
KEEP_SFT_INSTRUCTIONS = frozenset(
    {
        "介绍",
        "类别",
        "性味归经",
        "功效主治",
        "疾病挑选",
        "证候",
        "配伍应用",
        "方剂-介绍",
        "方剂-类别",
        "方剂-处方",
        "方剂-功效主治",
        "方剂-证候",
        "方剂-疾病挑选",
        "方剂-方解",
    }
)
SKIP_SFT_INSTRUCTIONS = frozenset(
    {
        "基因",
        "方剂-基因",
        "方剂-西医疾病",
        "方剂-单体化合物",
        "药理",
        "简单成分",
        "中药-中药西医疾病",
        "效用分析",
    }
)
FORBIDDEN_SFT_FIELDS = frozenset({"基因", "西医疾病", "成分", "药理", "单体化合物"})
SFT_KNOWLEDGE_TYPE = "来源SFT知识"
SFT_MENTION_TYPE = "来源SFT知识提及"


class PendingExtractError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _record_from_drafts(
    drafts: list[EntityDraft],
    *,
    source_id: str,
    batch_id: str,
    import_scope_key: str,
    processor: str,
) -> tuple[list[DatasetRecord], dict[str, Any]]:
    records, quarantined, report = finalize_drafts(
        drafts,
        source_id=source_id,
        batch_id=batch_id,
        import_scope_key=import_scope_key,
        processor=processor,
    )
    report["quarantined"] = quarantined
    report["publish"] = False
    return records, report


def _parse_brackets(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in BRACKET_RE.finditer(text):
        key = match.group(1).strip()
        if key in FORBIDDEN_SFT_FIELDS:
            continue
        found[key] = redact_sensitive(match.group(2).strip())
    return found


def _kept_sft_instruction(instruction: str) -> bool:
    if instruction.startswith("以下是"):
        return False
    if instruction in SKIP_SFT_INSTRUCTIONS:
        return False
    return instruction in KEEP_SFT_INSTRUCTIONS


def _sft_name_and_type(
    instruction: str, raw_input: str, output: str
) -> tuple[str, NodeType | None]:
    match = NAME_KIND_RE.match(output.lstrip())
    if match:
        name = match.group(1).strip()
        kind = match.group(2)
        node_type = NodeType.FORMULA if kind == "方剂" else NodeType.HERB
        return name, node_type
    if instruction.startswith("方剂"):
        match = FORMULA_ASK_RE.search(raw_input)
        return (match.group(1).strip() if match else ""), NodeType.FORMULA
    match = HERB_INTRO_RE.search(raw_input)
    if match:
        return match.group(1).strip(), NodeType.HERB
    return "", None


def _drop_sft_name(name: str) -> bool:
    return (not name) or ("注射" in name) or contains_brand(name)


def _split_tokens(text: str) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in TOKEN_SPLIT_RE.split(text) if part.strip()]


def _clean_herb_token(token: str) -> str | None:
    text = token.strip().strip("。；;，,、")
    if len(text) < 2 or len(text) > 12:
        return None
    if "注射" in text:
        return None
    if "等" in text and "种" in text:
        return None
    if contains_brand(text):
        return None
    return text


def _composition_text(fields: dict[str, str], output: str) -> str:
    text = (fields.get("处方") or "").strip()
    if text:
        return text
    match = PRESCRIPTION_BODY_RE.search(output)
    return match.group(1).strip() if match else ""


def _sft_properties(fields: dict[str, str], composition_text: str) -> dict[str, Any]:
    properties: dict[str, Any] = {"tcm_type": SFT_KNOWLEDGE_TYPE}
    if fields.get("类别"):
        properties["category"] = fields["类别"]
    if composition_text:
        properties["composition_text"] = composition_text
    indications = fields.get("功能主治") or fields.get("功效主治")
    if indications:
        properties["indications"] = indications
    if fields.get("性味归经"):
        properties["flavor_text"] = fields["性味归经"]
    return properties


def _mention_draft(name: str, evidence_ref: str) -> EntityDraft:
    return EntityDraft(
        node_type=NodeType.DISEASE,
        raw_name=name,
        role="病证提及",
        stable_id=name,
        evidence_refs=[evidence_ref],
        properties={"tcm_type": SFT_MENTION_TYPE},
    )


def _fill_draft(existing: EntityDraft, incoming: EntityDraft) -> None:
    for alias in incoming.aliases:
        if alias not in existing.aliases:
            existing.aliases.append(alias)
    for ref in incoming.evidence_refs:
        if ref not in existing.evidence_refs:
            existing.evidence_refs.append(ref)
    for field_name, value in incoming.properties.items():
        current = existing.properties.get(field_name)
        if current in (None, "", [], {}):
            existing.properties[field_name] = value
    seen_edges = set(existing.edges)
    for edge in incoming.edges:
        if edge not in seen_edges:
            existing.edges.append(edge)
            seen_edges.add(edge)


def _upsert_draft(
    merged: dict[tuple[str, str], EntityDraft], draft: EntityDraft
) -> EntityDraft:
    key = (draft.node_type.value, name_key(draft.raw_name, draft.node_type))
    existing = merged.get(key)
    if existing is None:
        merged[key] = draft
        return draft
    _fill_draft(existing, draft)
    return existing


def extract_sft_knowledge(
    path: Path, lexicon: dict[str, str] | None = None
) -> tuple[list[EntityDraft], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise PendingExtractError("knowledge.json is not a list")
    lexicon = lexicon or {}
    merged: dict[tuple[str, str], EntityDraft] = {}
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            continue
        instruction = str(item.get("instruction") or "").strip()
        if not _kept_sft_instruction(instruction):
            continue
        raw_input = str(item.get("input") or "")
        output = str(item.get("output") or "")
        name, node_type = _sft_name_and_type(instruction, raw_input, output)
        if node_type is None or _drop_sft_name(name):
            continue
        fields = _parse_brackets(output)
        composition_text = _composition_text(fields, output)
        evidence_ref = f"knowledge.json:{index}"
        edges: list[tuple[str, str]] = []
        if node_type == NodeType.FORMULA:
            for token in _split_tokens(composition_text):
                cleaned = _clean_herb_token(token)
                if cleaned:
                    edges.append((EdgeType.CONTAINS_HERB.value, cleaned))
        for token in _split_tokens(fields.get("配伍应用") or ""):
            cleaned = _clean_herb_token(token)
            if cleaned:
                edges.append((EdgeType.RELATED_HERB.value, cleaned))
        for token in _split_tokens(fields.get("证候") or ""):
            if lexicon.get(token) != NodeType.DISEASE.value:
                continue
            edges.append((EdgeType.RELATED_SYNDROME.value, token))
            _upsert_draft(merged, _mention_draft(token, evidence_ref))
        for field_name in ("中医疾病", "中药疾病"):
            for token in _split_tokens(fields.get(field_name) or ""):
                if lexicon.get(token) != NodeType.DISEASE.value:
                    continue
                edges.append((EdgeType.APPLIES_TO.value, token))
                _upsert_draft(merged, _mention_draft(token, evidence_ref))
        _upsert_draft(
            merged,
            EntityDraft(
                node_type=node_type,
                raw_name=name,
                role="知识条目",
                stable_id=name,
                evidence_refs=[evidence_ref],
                properties=_sft_properties(fields, composition_text),
                edges=edges,
            ),
        )
    drafts = list(merged.values())
    unique_entries = sum(
        1 for item in drafts if item.properties.get("tcm_type") == SFT_KNOWLEDGE_TYPE
    )
    return drafts, {
        "source_rows": len(payload),
        "unique_entries": unique_entries,
        "mention_entries": len(drafts) - unique_entries,
    }


def extract_daiy_terms(path: Path) -> tuple[list[EntityDraft], dict[str, Any]]:
    drafts: list[EntityDraft] = []
    kept = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if "中医病名" not in line and "中医病证名" not in line:
            continue
        title = line.split("，", 1)[0].strip()
        if len(title) < 2 or contains_brand(title):
            continue
        if any(item.raw_name == title for item in drafts):
            continue
        kept += 1
        drafts.append(
            EntityDraft(
                node_type=NodeType.DISEASE,
                raw_name=title,
                role="疾病",
                stable_id=f"daiy:{title}",
                evidence_refs=[f"daiy_data.txt:{line_no}"],
                properties={
                    "tcm_type": "来源百科病名",
                    "description": redact_sensitive(line[:240]),
                },
            )
        )
    return drafts, {"kept_term_lines": kept}


def extract_chatmed_mentions(
    path: Path, lexicon: dict[str, str], *, limit: int | None = None
) -> tuple[list[EntityDraft], dict[str, Any]]:
    drafts: list[EntityDraft] = []
    seen: set[tuple[str, str]] = set()
    scanned = 0
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        text = line.strip()
        if len(text) < 24:
            continue
        scanned += 1
        for name, node_type in longest_lexicon_hits(text, lexicon):
            if len(name) < 3:
                continue
            key = (node_type, name)
            if key in seen:
                continue
            seen.add(key)
            drafts.append(
                EntityDraft(
                    node_type=NodeType(node_type),
                    raw_name=name,
                    role="对话提及",
                    stable_id=name,
                    evidence_refs=[f"ChatMed_TCM-v0.2_.txt:{line_no}"],
                    properties={"tcm_type": "对话提及"},
                )
            )
        if limit is not None and scanned >= limit:
            break
    return drafts, {"scanned_lines": scanned, "unique_mentions": len(drafts)}


def extract_sylvanl_entries(path: Path) -> tuple[list[EntityDraft], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    drafts: list[EntityDraft] = []
    for index, item in enumerate(payload):
        text = str((item or {}).get("text") or "")
        head = text.split("\n", 1)[0]
        if head.startswith("药名:") or head.startswith("中药材:"):
            name = head.split(":", 1)[1].strip()
            node_type = NodeType.HERB
        elif head.startswith("方剂:"):
            name = head.split(":", 1)[1].strip()
            node_type = NodeType.FORMULA
        else:
            continue
        if not name or contains_brand(name) or "注射用" in name:
            continue
        if any(item.raw_name == name and item.node_type == node_type for item in drafts):
            continue
        drafts.append(
            EntityDraft(
                node_type=node_type,
                raw_name=name,
                role="百科条目",
                stable_id=name,
                evidence_refs=[f"{path.name}:{index}"],
                properties={"tcm_type": "来源预训练百科", "description": redact_sensitive(text[:240])},
            )
        )
    return drafts, {"source_rows": len(payload), "kept": len(drafts)}


def list_decodable_numbered_books(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    books: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for file_path in sorted(root.glob("*.txt")):
        match = NUMBERED_RE.match(file_path.name)
        if not match:
            skipped.append({"file": file_path.name, "reason": "unnumbered"})
            continue
        try:
            _decode(file_path.read_bytes())
        except Exception:
            skipped.append({"file": file_path.name, "reason": "undecodable"})
            continue
        books.append(
            {
                "book_id": int(match.group(1)),
                "title": match.group(2),
                "file": file_path.name,
            }
        )
    return books, {"kept": len(books), "skipped": skipped}


def extract_ancient_sources(books: Iterable[dict[str, Any]]) -> list[EntityDraft]:
    drafts: list[EntityDraft] = []
    for item in books:
        drafts.append(
            EntityDraft(
                node_type=NodeType.SOURCE,
                raw_name=str(item["title"]),
                role="古籍",
                stable_id=f"{item['book_id']:03d}",
                evidence_refs=[str(item["file"])],
                properties={
                    "tcm_type": "来源古籍书目",
                    "term_code": f"{item['book_id']:03d}",
                    "source_book": str(item["title"]),
                },
            )
        )
    return drafts


def write_source_outputs(
    *,
    repo: Path,
    source_id: str,
    records: list[DatasetRecord],
    report: dict[str, Any],
    queue_lines: list[dict[str, Any]] | None = None,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    ensure_source_layout(repo, source_id)
    latest = processed_latest_dir(repo, source_id)
    records_path = latest / "records.jsonl"
    stats_path = latest / "stats.json"
    if skip_reason:
        (work_dir(repo, source_id) / "notes" / "skip.md").write_text(
            skip_reason.strip() + "\n", encoding="utf-8"
        )
        if not records:
            return {
                "source_id": source_id,
                "records": str(records_path),
                "stats": str(stats_path),
                "record_count": sum(1 for _ in records_path.open()) if records_path.is_file() else 0,
                "publish": False,
                "skipped": True,
            }
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in records),
        encoding="utf-8",
    )
    stats = {**compute_stats(records), **report, "record_count": len(records)}
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    work = work_dir(repo, source_id)
    if queue_lines:
        (work / "queue" / "agent_queue.jsonl").write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in queue_lines),
            encoding="utf-8",
        )
    return {
        "source_id": source_id,
        "records": str(records_path),
        "stats": str(stats_path),
        "record_count": len(records),
        "publish": False,
    }
