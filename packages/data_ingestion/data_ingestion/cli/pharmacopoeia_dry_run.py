from __future__ import annotations

import argparse
from pathlib import Path

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.dry_run import (
    run_pharmacopoeia_dry_run,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.llm_extraction import (
    FakeExtractionTransport,
    OpenAICompatibleExtractionTransport,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="药典条目 LLM dry-run 工具")
    parser.add_argument("--provider", default="huggingface")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--file-path", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--output-dir", default="tmp/pharmacopoeia-dry-run")
    parser.add_argument("--entry-offset", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--use-fake-response", action="store_true")
    parser.add_argument(
        "--fake-response",
        default='{"herb":{"herb_name":"一枝黄花"},"prepared_piece":null,"warnings":[],"confidence_notes":"dry-run"}',
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.name or output_dir.suffix:
        target_dir = output_dir
    else:
        target_dir = output_dir / "manual-run"
    transport = (
        FakeExtractionTransport(response_text=args.fake_response)
        if args.use_fake_response
        else OpenAICompatibleExtractionTransport(timeout_seconds=args.timeout_seconds)
    )

    def _print_entry_result(entry_result: dict[str, object]) -> None:
        preview = str(entry_result["raw_response_preview"])
        print(
            "entry_title={entry_title} status={status} elapsed_ms={elapsed_ms} raw_response_preview={preview}".format(
                entry_title=entry_result["entry_title"],
                status=entry_result["status"],
                elapsed_ms=entry_result["elapsed_ms"],
                preview=preview,
            )
        )
        if entry_result.get("error_message"):
            print(f"error_message={entry_result['error_message']}")

    result = run_pharmacopoeia_dry_run(
        local_path=Path(args.local_path),
        output_dir=target_dir,
        limit=args.limit,
        entry_offset=args.entry_offset,
        request_timeout_seconds=args.timeout_seconds,
        concurrency=args.concurrency,
        transport=transport,
        provider=args.provider,
        dataset=args.dataset,
        file_path=args.file_path,
        on_entry_result=_print_entry_result,
    )
    print(f"entries_attempted={result.summary['entries_attempted']}")
    print(f"total_llm_elapsed_ms={result.summary['total_llm_elapsed_ms']}")
    print(f"output_dir={result.output_dir}")


if __name__ == "__main__":
    main()
