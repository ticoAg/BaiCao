"""数据集级图谱重置 CLI。"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.importers.dataset_reset import reset_dataset_graph, reset_graph_from_records
from app.importers.jsonl_importer import JSONLImporter


def build_parser() -> argparse.ArgumentParser:
    """构建数据集重置 CLI 参数。"""

    parser = argparse.ArgumentParser(description="BaiCao 数据集图谱重置工具")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--file-path")
    parser.add_argument("--snapshot-jsonl", help="可选：按指定 GraphImportRecord 快照做精确清理")
    return parser


def main() -> None:
    """执行数据集级或快照级图谱重置。"""

    args = build_parser().parse_args()

    async def _run():
        scoped = await reset_dataset_graph(provider=args.provider, dataset=args.dataset, file_path=args.file_path)
        snapshot = None
        if args.snapshot_jsonl:
            records = list(JSONLImporter().load(str(Path(args.snapshot_jsonl))))
            snapshot = await reset_graph_from_records(records)
        return scoped, snapshot

    scoped_result, snapshot_result = asyncio.run(_run())
    print(
        f"scoped_nodes_deleted={scoped_result.nodes_deleted} "
        f"scoped_relationships_deleted={scoped_result.relationships_deleted}"
    )
    if snapshot_result is not None:
        print(
            f"snapshot_nodes_deleted={snapshot_result.nodes_deleted} "
            f"snapshot_relationships_deleted={snapshot_result.relationships_deleted}"
        )


if __name__ == "__main__":
    main()
