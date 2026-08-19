"""对仍待清洗的可用源做高确定性抽取。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.pending_extract import (
    extract_ancient_sources,
    extract_chatmed_mentions,
    extract_daiy_terms,
    extract_sft_knowledge,
    extract_sylvanl_entries,
    list_decodable_numbered_books,
    repo_root,
    write_source_outputs,
    _record_from_drafts,
)
from data_ingestion.tcm_ancient_books import clean_directory as audit_ancient
from data_ingestion.tcmchat_case_units import load_lexicon


def _lexicon(repo: Path) -> dict[str, str]:
    return load_lexicon(
        repo
        / "datasets/baicao-knowledge/sources/national-standard-terms/processed/latest/records.jsonl"
    )


def run_kind(kind: str, *, repo: Path, limit: int | None = None) -> dict:
    cache = repo / ".cache"
    if kind == "sft-knowledge":
        drafts, extra = extract_sft_knowledge(
            cache
            / "huggingface/ZJUFanLab/TCMChat-dataset-600k/sft/train/knowledge.json",
            lexicon=_lexicon(repo),
        )
        records, report = _record_from_drafts(
            drafts,
            source_id="tcmchat-sft-knowledge",
            batch_id="2026-08-19-sft-knowledge-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k:sft/train/knowledge.json",
            processor="pending_extract",
        )
        report.update(extra)
        return write_source_outputs(
            repo=repo, source_id="tcmchat-sft-knowledge", records=records, report=report
        )
    if kind == "web":
        drafts, extra = extract_daiy_terms(
            cache / "huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/web/daiy_data.txt"
        )
        records, report = _record_from_drafts(
            drafts,
            source_id="tcmchat-web",
            batch_id="2026-08-19-tcmchat-web-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/web",
            processor="pending_extract",
        )
        report.update(extra)
        report["skip_baike"] = "2019_baidubaike.txt 无稳定词条边界，只保留 daiy 中医病名/病证名行"
        return write_source_outputs(
            repo=repo, source_id="tcmchat-web", records=records, report=report
        )
    if kind == "chatmed":
        drafts, extra = extract_chatmed_mentions(
            cache
            / "huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/opendata/ChatMed_TCM-v0.2_.txt",
            _lexicon(repo),
            limit=limit,
        )
        records, report = _record_from_drafts(
            drafts,
            source_id="tcmchat-chatmed",
            batch_id="2026-08-19-tcmchat-chatmed-v1",
            import_scope_key="huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/opendata",
            processor="pending_extract",
        )
        report.update(extra)
        return write_source_outputs(
            repo=repo, source_id="tcmchat-chatmed", records=records, report=report
        )
    if kind == "sylvanl":
        directory = (
            cache / "huggingface/SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain"
        )
        drafts: list = []
        extras = {}
        for name in (
            "CPT_tcmKnowledge_source1_17921.json",
            "CPT_tcmKnowledge_source2_12889.json",
        ):
            part, extra = extract_sylvanl_entries(directory / name)
            drafts.extend(part)
            extras[name] = extra
        records, report = _record_from_drafts(
            drafts,
            source_id="sylvanl-tcm-pretrain",
            batch_id="2026-08-19-sylvanl-entries-v1",
            import_scope_key="huggingface:SylvanL/Traditional-Chinese-Medicine-Dataset-Pretrain",
            processor="pending_extract",
        )
        report["files"] = extras
        return write_source_outputs(
            repo=repo, source_id="sylvanl-tcm-pretrain", records=records, report=report
        )
    if kind == "ancient-books":
        _, audit = audit_ancient(cache / "github/xiaopangxia/TCM-Ancient-Books")
        root = cache / "github/xiaopangxia/TCM-Ancient-Books"
        books, listing = list_decodable_numbered_books(root)
        drafts = extract_ancient_sources(books)
        records, report = _record_from_drafts(
            drafts,
            source_id="tcm-ancient-books",
            batch_id="2026-08-19-ancient-sources-v1",
            import_scope_key="github:xiaopangxia/TCM-Ancient-Books",
            processor="pending_extract",
        )
        report["audit"] = {
            "book_count": audit.get("book_count"),
            "decode_errors": audit.get("quarantine_counts", {}).get("decode_errors"),
        }
        report["listing"] = listing
        return write_source_outputs(
            repo=repo, source_id="tcm-ancient-books", records=records, report=report
        )
    if kind == "skip-notes":
        notes = {
            "tcm-ner": "PEND-04：说明书 NER 品牌与跨类型噪声，只作评测，不自动入图。",
            "tcmchat-600k": "PEND-04/05：entity_extraction 与 sft/medical_case 不升格事实；后者与 TCM-SD 同源。",
            "zybert-pretrain-corpus": "PEND-07：RAR 未解压，环境无可靠解压则不出记录。",
            "classical-tcm-canon": "Dataset Card 为 proprietary-commercial，禁止整包再用。",
        }
        results = []
        for source_id, reason in notes.items():
            results.append(
                write_source_outputs(
                    repo=repo,
                    source_id=source_id,
                    records=[],
                    report={"publish": False, "skipped": True, "reason": reason},
                    skip_reason=reason,
                )
            )
        return {"skips": results}
    raise SystemExit(f"unknown kind: {kind}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--kind",
        required=True,
        choices=["sft-knowledge", "web", "chatmed", "sylvanl", "ancient-books", "skip-notes"],
    )
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    print(json.dumps(run_kind(args.kind, repo=repo_root(), limit=args.limit), ensure_ascii=False))


if __name__ == "__main__":
    main()
