"""把 TCMChat 名医验案切成去标识工作单元，并生成 agent 抽取队列。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.entity_identity import redact_sensitive
from data_ingestion.organize_workflow import AgentTask, OrganizeBatch, WorkUnit
from data_ingestion.provenance import prompt_hash_for

SOURCE_ID = "tcmchat-medical-cases"
IMPORT_SCOPE_KEY = (
    "huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/books/medical_case"
)
DEFAULT_BATCH_ID = "2026-08-19-tcmchat-cases-v1"
PROCESSOR = "tcmchat_case_units"
PROMPT_HASH = prompt_hash_for(Path(__file__))

CASE_SPLIT_RE = re.compile(r"(例[一二三四五六七八九十百千0-9]+)")
SURNAME_RE = re.compile(r"(?<!例)[\u4e00-\u9fff]{1,2}某")
SEX_AGE_RE = re.compile(r"(?P<sex>[男女])(?P<age>\d{1,3}岁)")
AGENT_INSTRUCTION = (
    "从已去标识的医案中抽取确定性实体。只输出 ExtractionCandidate JSON 数组。"
    "允许类型：病证、方剂、药材、治法。不要恢复姓名或商品名。"
    "必须保留性别和年龄。不要用近义或猜测合并。"
)


class TcmChatCaseError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root()
    / ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/medical_case"
)


def redact_case_text(text: str) -> str:
    cleaned = SURNAME_RE.sub("患者", text)
    return redact_sensitive(cleaned)


def parse_sex_age(text: str) -> tuple[str | None, str | None]:
    match = SEX_AGE_RE.search(text)
    if not match:
        return None, None
    return match.group("sex"), match.group("age")


def load_lexicon(records_path: Path | None) -> dict[str, str]:
    lexicon: dict[str, str] = {}
    if records_path is None or not records_path.is_file():
        return lexicon
    for line in records_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        name = str(payload.get("node_name") or "")
        node_type = str(payload.get("node_type") or "")
        if node_type in {NodeType.DISEASE.value, NodeType.FORMULA.value} and len(name) >= 2:
            lexicon[name] = node_type
    return lexicon


def longest_lexicon_hits(text: str, lexicon: dict[str, str]) -> list[tuple[str, str]]:
    by_first: dict[str, list[str]] = {}
    for name in lexicon:
        by_first.setdefault(name[0], []).append(name)
    for names in by_first.values():
        names.sort(key=len, reverse=True)
    hits: dict[tuple[str, str], None] = {}
    index = 0
    length = len(text)
    while index < length:
        candidates = by_first.get(text[index])
        matched = None
        if candidates:
            for name in candidates:
                end = index + len(name)
                if end <= length and text.startswith(name, index):
                    matched = name
                    break
        if matched:
            hits[(matched, lexicon[matched])] = None
            index += len(matched)
        else:
            index += 1
    return list(hits)


def split_case_book(path: Path) -> list[WorkUnit]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    parts = CASE_SPLIT_RE.split(raw)
    units: list[WorkUnit] = []
    if len(parts) == 1:
        units.append(
            WorkUnit(
                unit_id=f"{path.stem}:full",
                kind="medical_case",
                locator=path.name,
                text=redact_case_text(raw),
                metadata={"book": path.stem, "marker": "full"},
            )
        )
        return units
    prefix = parts[0]
    index = 0
    while index + 2 <= len(parts):
        marker = parts[index + 1]
        body = parts[index + 2] if index + 2 < len(parts) else ""
        text = redact_case_text(f"{marker}{body}")
        if len(text.strip()) >= 8:
            units.append(
                WorkUnit(
                    unit_id=f"{path.stem}:{marker}",
                    kind="medical_case",
                    locator=f"{path.name}:{marker}",
                    text=text,
                    metadata={"book": path.stem, "marker": marker, "preface": prefix[:80]},
                )
            )
        index += 2
    if not units:
        units.append(
            WorkUnit(
                unit_id=f"{path.stem}:full",
                kind="medical_case",
                locator=path.name,
                text=redact_case_text(raw),
                metadata={"book": path.stem, "marker": "full"},
            )
        )
    return units


def _case_record(unit: WorkUnit) -> DatasetRecord:
    sex, age = parse_sex_age(unit.text)
    book = str(unit.metadata.get("book") or "医案")
    marker = str(unit.metadata.get("marker") or unit.unit_id)
    name = f"{book}-{marker}"
    record = DatasetRecord(
        source_id=SOURCE_ID,
        batch_id=DEFAULT_BATCH_ID,
        unit_id=unit.unit_id,
        unit_title=name,
        processor=PROCESSOR,
        node_type=NodeType.MEDICAL_CASE.value,
        node_name=name,
        source=SOURCE_ID,
        status="pending",
        evidence_refs=[unit.locator],
        prompt_hash=PROMPT_HASH,
        import_scope_key=IMPORT_SCOPE_KEY,
        properties={
            "import_source_id": SOURCE_ID,
            "import_batch_id": DEFAULT_BATCH_ID,
            "import_unit_id": unit.unit_id,
            "tcm_type": "来源名医验案",
            "sex": sex,
            "age": age,
            "chief_complaint": unit.text[:180],
            "source_book": book,
        },
    )
    record.validate_types()
    return record


def _mention_record(name: str, node_type: str, case_name: str, locator: str) -> DatasetRecord:
    record = DatasetRecord(
        source_id=SOURCE_ID,
        batch_id=DEFAULT_BATCH_ID,
        unit_id=f"{node_type}:{name}:{locator}",
        unit_title=name,
        processor=PROCESSOR,
        node_type=node_type,
        node_name=name,
        source=SOURCE_ID,
        status="pending",
        evidence_refs=[locator],
        prompt_hash=PROMPT_HASH,
        import_scope_key=IMPORT_SCOPE_KEY,
        properties={
            "import_source_id": SOURCE_ID,
            "import_batch_id": DEFAULT_BATCH_ID,
            "import_unit_id": f"{node_type}:{name}:{locator}",
            "tcm_type": "验案提及",
        },
        edges=[
            DatasetEdge(
                type=EdgeType.RECORDED_IN_CASE.value,
                target=case_name,
                properties={"evidence_ref": locator},
            )
        ],
    )
    record.validate_types()
    return record


def prepare_directory(path: Path, *, lexicon_path: Path | None = None) -> OrganizeBatch:
    if not path.is_dir():
        raise TcmChatCaseError(f"input is not a directory: {path}")
    files = sorted(item for item in path.glob("*.txt") if item.is_file())
    if not files:
        raise TcmChatCaseError("no medical case txt files")
    lexicon = load_lexicon(lexicon_path)
    units: list[WorkUnit] = []
    for file_path in files:
        units.extend(split_case_book(file_path))
    records: list[DatasetRecord] = []
    mention_counts = {"病证": 0, "方剂": 0}
    for unit in units:
        case = _case_record(unit)
        records.append(case)
        for name, node_type in longest_lexicon_hits(unit.text, lexicon):
            records.append(_mention_record(name, node_type, case.node_name, unit.locator))
            if node_type in mention_counts:
                mention_counts[node_type] += 1
    queue = [
        AgentTask(
            unit_id=unit.unit_id,
            locator=unit.locator,
            kind=unit.kind,
            redacted_text=unit.text,
            allowed_node_types=[
                NodeType.DISEASE.value,
                NodeType.FORMULA.value,
                NodeType.HERB.value,
                NodeType.TREATMENT_METHOD.value,
            ],
            instruction=AGENT_INSTRUCTION,
        )
        for unit in units
    ]
    report = {
        "publish": False,
        "license_status": "apache-2.0_dataset_filter_brand_and_pii",
        "book_count": len(files),
        "unit_count": len(units),
        "agent_queue_count": len(queue),
        "lexicon_size": len(lexicon),
        "mention_counts": mention_counts,
        "cases_with_sex": sum(1 for record in records if record.node_type == "医案" and record.properties.get("sex")),
        "source_id": SOURCE_ID,
        "batch_id": DEFAULT_BATCH_ID,
        "import_scope_key": IMPORT_SCOPE_KEY,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
    }
    return OrganizeBatch(records=records, agent_queue=queue, quarantined=[], report=report)


def dump_prepare(batch: OrganizeBatch, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = out_dir / "agent_queue.jsonl"
    stats_path = out_dir / "stats.json"
    records_path = out_dir / "records.jsonl"
    queue_path.write_text(
        "".join(
            json.dumps(
                {
                    "unit_id": task.unit_id,
                    "locator": task.locator,
                    "kind": task.kind,
                    "allowed_node_types": task.allowed_node_types,
                    "instruction": task.instruction,
                    "redacted_text": task.redacted_text,
                },
                ensure_ascii=False,
            )
            + "\n"
            for task in batch.agent_queue
        ),
        encoding="utf-8",
    )
    records_path.write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in batch.records),
        encoding="utf-8",
    )
    stats_path.write_text(
        json.dumps({**batch.report, "record_count": len(batch.records)}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return {
        "agent_queue": str(queue_path),
        "records": str(records_path),
        "stats": str(stats_path),
        "unit_count": batch.report["unit_count"],
        "record_count": len(batch.records),
        "publish": False,
    }
