"""覆盖药典 dry-run 与切分评估 CLI 的参数解析。"""

from data_ingestion.cli.pharmacopoeia_dry_run import build_parser
from data_ingestion.cli.pharmacopoeia_segmentation_assessment import build_parser as build_segmentation_parser


def test_cli_parser_sets_limit_to_ten_by_default():
    """验证 dry-run CLI 的默认样本数为 10。"""

    # 默认跑 10 条，兼顾观察样本量和调试成本。
    parser = build_parser()
    args = parser.parse_args(
        [
            "--provider",
            "huggingface",
            "--dataset",
            "ZJUFanLab/TCMChat-dataset-600k",
            "--file-path",
            "pretrain/train/books/national_standard/2022年中药药典.txt",
            "--local-path",
            ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt",
        ]
    )

    assert args.limit == 10


def test_cli_parser_accepts_debug_timeout_and_real_run_dir():
    """验证 dry-run CLI 支持调试时常用的 offset、timeout 和输出目录参数。"""

    # 调试真实模型链路时，入口参数要能精确控制 offset、timeout 和输出目录。
    parser = build_parser()
    args = parser.parse_args(
        [
            "--provider",
            "huggingface",
            "--dataset",
            "ZJUFanLab/TCMChat-dataset-600k",
            "--file-path",
            "pretrain/train/books/national_standard/2022年中药药典.txt",
            "--local-path",
            ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt",
            "--limit",
            "1",
            "--entry-offset",
            "2",
            "--output-dir",
            "tmp/pharmacopoeia-dry-run/real-run-1",
            "--timeout-seconds",
            "45",
            "--concurrency",
            "10",
        ]
    )

    assert args.limit == 1
    assert args.entry_offset == 2
    assert args.timeout_seconds == 45
    assert args.concurrency == 10


def test_segmentation_assessment_cli_parser_supports_summary_limit():
    """验证切分评估 CLI 支持单独控制可疑样本上限。"""

    # 切分评估需要单独控制抽样上限，避免一次导出过多可疑样本。
    parser = build_segmentation_parser()
    args = parser.parse_args(
        [
            "--provider",
            "huggingface",
            "--dataset",
            "ZJUFanLab/TCMChat-dataset-600k",
            "--file-path",
            "pretrain/train/books/national_standard/2022年中药药典.txt",
            "--local-path",
            ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt",
            "--output-dir",
            "tmp/pharmacopoeia-segmentation-assessment",
            "--sample-limit",
            "15",
        ]
    )

    assert args.output_dir == "tmp/pharmacopoeia-segmentation-assessment"
    assert args.sample_limit == 15


def test_segmentation_assessment_cli_uses_default_output_dir():
    """验证切分评估 CLI 的默认输出目录稳定可复用。"""

    # 默认输出目录要稳定，方便 launch.json 和本地脚本复用。
    parser = build_segmentation_parser()
    args = parser.parse_args(
        [
            "--dataset",
            "ZJUFanLab/TCMChat-dataset-600k",
            "--file-path",
            "pretrain/train/books/national_standard/2022年中药药典.txt",
            "--local-path",
            ".cache/huggingface/ZJUFanLab/TCMChat-dataset-600k/pretrain/train/books/national_standard/2022年中药药典.txt",
        ]
    )

    assert args.output_dir == "tmp/pharmacopoeia-segmentation-assessment"
