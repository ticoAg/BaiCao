"""把已持有、尚未入图的结构化剩余文件抽成 records。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from graph_schema.constants import EdgeType, NodeType

from data_ingestion.entity_identity import EntityDraft
from data_ingestion.organize_workflow import finalize_drafts
from data_ingestion.pending_extract import write_source_outputs
from data_ingestion.tcmchat_case_units import default_lexicon_paths, load_lexicon, longest_lexicon_hits

TOKEN_SPLIT_RE = re.compile(r"[、，,；;]+")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _load_json_array(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} is not a JSON array")
    return payload


def extract_entity_extraction(path: Path) -> list[EntityDraft]:
    drafts: list[EntityDraft] = []
    if not path.is_file():
        return drafts
    mapping = {
        "药物成分": NodeType.HERB,
        "药物": NodeType.FORMULA,
        "中药功效": NodeType.EFFICACY,
        "症状": NodeType.SYMPTOM,
        "药物性味": NodeType.FLAVOR,
    }
    for index, item in enumerate(_load_json_array(path)):
        output = str(item.get("output") or "")
        for chunk in output.split("；"):
            parts = re.split(r"[:：]", chunk, maxsplit=1)
            if len(parts) != 2:
                continue
            label, body = parts
            node_type = mapping.get(label.strip())
            if node_type is None:
                continue
            for raw in TOKEN_SPLIT_RE.split(body):
                name = raw.strip()
                if len(name) < 2:
                    continue
                drafts.append(
                    EntityDraft(
                        node_type=node_type,
                        raw_name=name,
                        role="说明书抽取",
                        stable_id=name,
                        evidence_refs=[f"entity_extraction.json:{index}"],
                        properties={"tcm_type": "来源TCMChat剩余"},
                    )
                )
    return drafts


def extract_similar(path: Path, *, node_type: NodeType, kind: str) -> list[EntityDraft]:
    drafts: list[EntityDraft] = []
    if not path.is_file():
        return drafts
    for index, item in enumerate(_load_json_array(path)):
        query = str(item.get("input") or "")
        rank = str(item.get("rank") or "")
        if not rank:
            continue
        head = re.split(r"具有|含有|与", query, maxsplit=1)[0]
        head = re.sub(r"[？?。．\s].*$", "", head).strip("（）()《》 ")
        if len(head) < 2:
            continue
        drafts.append(
            EntityDraft(
                node_type=node_type,
                raw_name=head,
                role=kind,
                stable_id=head,
                evidence_refs=[f"{path.name}:{index}"],
                properties={"tcm_type": "来源TCMChat剩余"},
                edges=[
                    (EdgeType.SIMILAR_TO.value, peer.strip())
                    for peer in TOKEN_SPLIT_RE.split(rank)
                    if len(peer.strip()) >= 2
                ],
            )
        )
        for peer in TOKEN_SPLIT_RE.split(rank):
            name = peer.strip()
            if len(name) < 2:
                continue
            drafts.append(
                EntityDraft(
                    node_type=node_type,
                    raw_name=name,
                    role=kind,
                    stable_id=name,
                    evidence_refs=[f"{path.name}:{index}"],
                    properties={"tcm_type": "来源TCMChat剩余"},
                )
            )
    return drafts


def extract_unique_mentions(path: Path, *, locator: str) -> list[EntityDraft]:
    if not path.is_file():
        return []
    lexicon = load_lexicon(default_lexicon_paths())
    text = path.read_text(encoding="utf-8", errors="replace")
    drafts: list[EntityDraft] = []
    for name, node_type in longest_lexicon_hits(text, lexicon):
        drafts.append(
            EntityDraft(
                node_type=NodeType(node_type),
                raw_name=name,
                role="语料提及",
                stable_id=name,
                evidence_refs=[f"{locator}:{name}"],
                properties={"tcm_type": "来源TCMChat剩余"},
            )
        )
    return drafts


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", default="all")
    args = parser.parse_args(argv)
    repo = repo_root()
    cache = repo / ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k"
    if args.kind == "all":
        drafts: list[EntityDraft] = []
        drafts.extend(extract_entity_extraction(cache / "sft/train/entity_extraction.json"))
        drafts.extend(
            extract_similar(
                cache / "sft/train/recommend_herb.json",
                node_type=NodeType.HERB,
                kind="化学谱相似药材",
            )
        )
        drafts.extend(
            extract_unique_mentions(
                cache / "pretrain/train/papers/fix_abstract_segmentation.txt",
                locator="papers/fix_abstract_segmentation.txt",
            )
        )
        baike = cache / "pretrain/train/web/2019_baidubaike.txt"
        drafts.extend(extract_unique_mentions(baike, locator="web/2019_baidubaike.txt"))
        records, _, report = finalize_drafts(
            drafts,
            source_id="tcmchat-600k",
            batch_id="2026-08-20-tcmchat-held-remaining-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k",
            processor="held_remaining",
        )
        report["kinds"] = ["entity_extraction", "recommend_herb", "papers", "baike"]
        print(
            json.dumps(
                write_source_outputs(
                    repo=repo, source_id="tcmchat-600k", records=records, report=report
                ),
                ensure_ascii=False,
            )
        )
        return
    if args.kind == "sft-ner":
        drafts = extract_entity_extraction(cache / "sft/train/entity_extraction.json")
        records, _, report = finalize_drafts(
            drafts,
            source_id="tcmchat-600k",
            batch_id="2026-08-20-tcmchat-sft-ner-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k:sft/train/entity_extraction.json",
            processor="held_remaining",
        )
        print(json.dumps(write_source_outputs(repo=repo, source_id="tcmchat-600k", records=records, report=report), ensure_ascii=False))
        return
    if args.kind == "similar-herb":
        drafts = extract_similar(
            cache / "sft/train/recommend_herb.json",
            node_type=NodeType.HERB,
            kind="化学谱相似药材",
        )
        records, _, report = finalize_drafts(
            drafts,
            source_id="tcmchat-sft-knowledge",
            batch_id="2026-08-20-similar-herb-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k:sft/train/recommend_herb.json",
            processor="held_remaining",
        )
        print(json.dumps(write_source_outputs(repo=repo, source_id="tcmchat-sft-knowledge", records=records, report=report), ensure_ascii=False))
        return
    if args.kind == "papers":
        drafts = extract_unique_mentions(
            cache / "pretrain/train/papers/fix_abstract_segmentation.txt",
            locator="papers/fix_abstract_segmentation.txt",
        )
        records, _, report = finalize_drafts(
            drafts,
            source_id="tcmchat-600k",
            batch_id="2026-08-20-tcmchat-papers-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/papers",
            processor="held_remaining",
        )
        print(json.dumps(write_source_outputs(repo=repo, source_id="tcmchat-600k", records=records, report=report), ensure_ascii=False))
        return
    raise SystemExit(f"unknown kind {args.kind}")


if __name__ == "__main__":
    main()
