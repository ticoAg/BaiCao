"""提供药典条目切分评估的命令行入口。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.segmentation import (
    assess_pharmacopoeia_entry_segmentation,
    segment_pharmacopoeia_entries,
)
from data_ingestion.source_models import SourceFileContext


def build_parser() -> argparse.ArgumentParser:
    """构建切分评估 CLI 的参数解析器。"""

    parser = argparse.ArgumentParser(description="药典条目切分评估工具")
    parser.add_argument("--provider", default="huggingface")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--file-path", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--output-dir", default="tmp/pharmacopoeia-segmentation-assessment")
    parser.add_argument("--sample-limit", type=int, default=20)
    return parser


def _build_context(args: argparse.Namespace) -> SourceFileContext:
    """根据命令行参数构造来源文件上下文。"""

    local_path = Path(args.local_path)
    return SourceFileContext(
        provider=args.provider,
        dataset=args.dataset,
        file_path=args.file_path,
        local_abspath=str(local_path),
        file_size=local_path.stat().st_size,
        line_count=local_path.read_text(encoding="utf-8").count("\n") + 1,
    )


def main() -> None:
    """执行一次切分评估并把摘要与样本写入输出目录。"""

    parser = build_parser()
    args = parser.parse_args()
    context = _build_context(args)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 评估结果和完整切段结果都落盘，方便后续在 VS Code / shell 中对照问题条目复查。
    assessment = assess_pharmacopoeia_entry_segmentation(context, sample_limit=args.sample_limit)
    blocks = segment_pharmacopoeia_entries(context)

    (output_dir / "segmentation_summary.json").write_text(
        json.dumps(assessment.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "segmented_entries.jsonl").write_text(
        "\n".join(json.dumps(block.model_dump(mode="json"), ensure_ascii=False) for block in blocks) + "\n",
        encoding="utf-8",
    )
    (output_dir / "suspicious_entries.jsonl").write_text(
        "\n".join(
            json.dumps(sample.model_dump(mode="json"), ensure_ascii=False)
            for sample in assessment.suspicious_entries
        )
        + ("\n" if assessment.suspicious_entries else ""),
        encoding="utf-8",
    )
    (output_dir / "entry_health_checks.jsonl").write_text(
        "\n".join(
            json.dumps(check.model_dump(mode="json"), ensure_ascii=False)
            for check in assessment.entry_health_checks
        )
        + ("\n" if assessment.entry_health_checks else ""),
        encoding="utf-8",
    )

    # 终端摘要尽量保持单行，便于 grep、日志归档和 launch.json 调试时快速查看。
    print(f"total_entries={assessment.total_entries}")
    print(f"start_rule_counts={json.dumps(assessment.start_rule_counts, ensure_ascii=False, sort_keys=True)}")
    print(f"excluded_title_counts={json.dumps(assessment.excluded_title_counts, ensure_ascii=False, sort_keys=True)}")
    print(f"duplicate_title_counts={json.dumps(assessment.duplicate_title_counts, ensure_ascii=False, sort_keys=True)}")
    print(f"health_label_counts={json.dumps(assessment.health_label_counts, ensure_ascii=False, sort_keys=True)}")
    print(f"mixed_case_third_line_count={assessment.mixed_case_third_line_count}")
    print(f"output_dir={output_dir}")


if __name__ == "__main__":
    main()
