from data_ingestion.cli.pharmacopoeia_dry_run import build_parser


def test_cli_parser_sets_limit_to_ten_by_default():
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
