"""把 TCMChat 名医验案切成去标识工作单元，并生成 agent 抽取队列。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from knowledge_model.constants import NodeType

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
SURNAME_RE = re.compile(r"[\u4e00-\u9fff]{1,2}某[男女]?\d{0,3}岁?")
AGENT_INSTRUCTION = (
    "从已去标识的医案中抽取确定性实体。只输出 ExtractionCandidate JSON 数组。"
    "允许类型：病证、方剂、药材、治法。不要恢复姓名、医院品牌或商品名。"
    "不要用近义或猜测合并；稳定身份缺省用规范名。"
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


def prepare_directory(path: Path) -> OrganizeBatch:
    if not path.is_dir():
        raise TcmChatCaseError(f"input is not a directory: {path}")
    files = sorted(item for item in path.glob("*.txt") if item.is_file())
    if not files:
        raise TcmChatCaseError("no medical case txt files")
    units: list[WorkUnit] = []
    for file_path in files:
        units.extend(split_case_book(file_path))
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
        "source_id": SOURCE_ID,
        "batch_id": DEFAULT_BATCH_ID,
        "import_scope_key": IMPORT_SCOPE_KEY,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
    }
    return OrganizeBatch(records=[], agent_queue=queue, quarantined=[], report=report)


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
    records_path.write_text("", encoding="utf-8")
    stats_path.write_text(
        json.dumps(batch.report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "agent_queue": str(queue_path),
        "records": str(records_path),
        "stats": str(stats_path),
        "unit_count": batch.report["unit_count"],
        "publish": False,
    }
