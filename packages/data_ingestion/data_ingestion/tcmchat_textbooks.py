"""把 TCMChat 教材切成章节单元，并用国标词表做规则提及。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from knowledge_model.constants import EdgeType, NodeType

from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.organize_workflow import AgentTask, OrganizeBatch, WorkUnit
from data_ingestion.provenance import prompt_hash_for
from data_ingestion.tcmchat_case_units import load_lexicon, longest_lexicon_hits

SOURCE_ID = "tcmchat-textbooks"
IMPORT_SCOPE_KEY = (
    "huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/books/textbook"
)
DEFAULT_BATCH_ID = "2026-08-19-tcmchat-textbooks-v1"
PROCESSOR = "tcmchat_textbooks"
PROMPT_HASH = prompt_hash_for(Path(__file__))
CHAPTER_RE = re.compile(r"(第[一二三四五六七八九十百千0-9]+章[^\n]{0,40})")
AGENT_INSTRUCTION = (
    "从教材章节中抽取确定性实体。只输出 ExtractionCandidate JSON 数组。"
    "允许类型：病证、方剂、药材、治法。不要用近义合并。"
)


class TcmChatTextbookError(ValueError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


DEFAULT_INPUT_PATH = (
    repo_root()
    / ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/textbook"
)


def split_textbook(path: Path) -> list[WorkUnit]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    parts = CHAPTER_RE.split(raw)
    units: list[WorkUnit] = []
    if len(parts) == 1:
        units.append(
            WorkUnit(
                unit_id=f"{path.stem}:full",
                kind="textbook",
                locator=path.name,
                text=raw,
                metadata={"book": path.stem, "marker": "full"},
            )
        )
        return units
    preface = parts[0]
    if preface.strip():
        units.append(
            WorkUnit(
                unit_id=f"{path.stem}:前言",
                kind="textbook",
                locator=f"{path.name}:前言",
                text=preface,
                metadata={"book": path.stem, "marker": "前言"},
            )
        )
    index = 1
    while index + 1 < len(parts):
        marker = parts[index].strip()
        body = parts[index + 1]
        text = f"{marker}\n{body}".strip()
        if len(text) >= 8:
            units.append(
                WorkUnit(
                    unit_id=f"{path.stem}:{marker[:20]}",
                    kind="textbook",
                    locator=f"{path.name}:{marker[:20]}",
                    text=text,
                    metadata={"book": path.stem, "marker": marker},
                )
            )
        index += 2
    return units


def prepare_directory(path: Path, *, lexicon_path: Path | list[Path] | None = None) -> OrganizeBatch:
    if not path.is_dir():
        raise TcmChatTextbookError(f"input is not a directory: {path}")
    files = sorted(item for item in path.glob("*.txt") if item.is_file())
    if not files:
        raise TcmChatTextbookError("no textbook txt files")
    lexicon = load_lexicon(lexicon_path)
    units: list[WorkUnit] = []
    for file_path in files:
        units.extend(split_textbook(file_path))
    records: list[DatasetRecord] = []
    mention_counts = {"病证": 0, "方剂": 0, "药材": 0, "治法": 0}
    for unit in units:
        source_name = f"{unit.metadata['book']}-{unit.metadata['marker']}"[:80]
        source = DatasetRecord(
            source_id=SOURCE_ID,
            batch_id=DEFAULT_BATCH_ID,
            unit_id=unit.unit_id,
            unit_title=source_name,
            processor=PROCESSOR,
            node_type=NodeType.SOURCE.value,
            node_name=source_name,
            source=SOURCE_ID,
            status="pending",
            evidence_refs=[unit.locator],
            prompt_hash=PROMPT_HASH,
            import_scope_key=IMPORT_SCOPE_KEY,
            properties={
                "import_source_id": SOURCE_ID,
                "import_batch_id": DEFAULT_BATCH_ID,
                "import_unit_id": unit.unit_id,
                "tcm_type": "来源教材章节",
                "source_book": str(unit.metadata["book"]),
            },
        )
        source.validate_types()
        records.append(source)
        for name, node_type in longest_lexicon_hits(unit.text, lexicon):
            mention = DatasetRecord(
                source_id=SOURCE_ID,
                batch_id=DEFAULT_BATCH_ID,
                unit_id=f"{node_type}:{name}:{unit.unit_id}",
                unit_title=name,
                processor=PROCESSOR,
                node_type=node_type,
                node_name=name,
                source=SOURCE_ID,
                status="pending",
                evidence_refs=[unit.locator],
                prompt_hash=PROMPT_HASH,
                import_scope_key=IMPORT_SCOPE_KEY,
                properties={
                    "import_source_id": SOURCE_ID,
                    "import_batch_id": DEFAULT_BATCH_ID,
                    "import_unit_id": f"{node_type}:{name}:{unit.unit_id}",
                    "tcm_type": "教材提及",
                },
                edges=[
                    DatasetEdge(
                        type=EdgeType.ORIGINATED_FROM.value,
                        target=source_name,
                        properties={"evidence_ref": unit.locator},
                    )
                ],
            )
            mention.validate_types()
            records.append(mention)
            if node_type in mention_counts:
                mention_counts[node_type] += 1
    queue = [
        AgentTask(
            unit_id=unit.unit_id,
            locator=unit.locator,
            kind=unit.kind,
            redacted_text=unit.text[:4000],
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
        "book_count": len(files),
        "unit_count": len(units),
        "agent_queue_count": len(queue),
        "mention_counts": mention_counts,
        "source_id": SOURCE_ID,
        "batch_id": DEFAULT_BATCH_ID,
        "import_scope_key": IMPORT_SCOPE_KEY,
        "processor": PROCESSOR,
        "prompt_hash": PROMPT_HASH,
    }
    return OrganizeBatch(records=records, agent_queue=queue, quarantined=[], report=report)


def dump_prepare(batch: OrganizeBatch, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "agent_queue.jsonl").write_text(
        "".join(
            json.dumps(
                {
                    "unit_id": task.unit_id,
                    "locator": task.locator,
                    "kind": task.kind,
                    "instruction": task.instruction,
                    "redacted_text": task.redacted_text,
                    "allowed_node_types": task.allowed_node_types,
                },
                ensure_ascii=False,
            )
            + "\n"
            for task in batch.agent_queue
        ),
        encoding="utf-8",
    )
    (out_dir / "records.jsonl").write_text(
        "".join(record.model_dump_json(exclude_none=True) + "\n" for record in batch.records),
        encoding="utf-8",
    )
    stats = {**batch.report, "record_count": len(batch.records), "publish": False}
    (out_dir / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "record_count": len(batch.records),
        "unit_count": batch.report["unit_count"],
        "publish": False,
        "out_dir": str(out_dir),
    }
