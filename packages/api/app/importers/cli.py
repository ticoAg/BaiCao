"""
数据导入 CLI 工具

用法：
    python -m app.importers.cli data/herbs.csv
    python -m app.importers.cli data/herbs.jsonl
    python -m app.importers.cli data/herbs.csv --dry-run
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加父目录到 path 以便导入 app 模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.importers import CSVImporter, JSONLImporter
from app.importers.neo4j_import import write_records_to_neo4j


def detect_importer(path: str) -> tuple[str, CSVImporter | JSONLImporter]:
    """根据文件扩展名检测导入器"""
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".csv":
        return "CSV", CSVImporter()
    elif suffix == ".jsonl":
        return "JSONL", JSONLImporter()
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def print_stats(name: str, stats, dry_run: bool):
    """打印导入统计"""
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}{name} 导入结果:")
    print(f"  总记录数: {stats.total}")
    print(f"  成功: {stats.success}")
    print(f"  失败: {stats.failed}")
    if stats.errors:
        print("  错误 (前10条):")
        for err in stats.errors[:10]:
            print(f"    - {err}")
        if len(stats.errors) > 10:
            print(f"    ... 还有 {len(stats.errors) - 10} 条错误")
    print(f"  成功率: {stats.success_rate:.1%}")


def print_neo4j_stats(nodes_written: int, edges_written: int) -> None:
    """打印 Neo4j 写入统计。"""

    print("\n[Neo4j] 写入结果:")
    print(f"  节点写入数: {nodes_written}")
    print(f"  边写入数: {edges_written}")


def main():
    parser = argparse.ArgumentParser(description="BaiCao 数据导入工具")
    parser.add_argument("file", help="导入文件路径 (CSV 或 JSONL)")
    parser.add_argument("--dry-run", action="store_true", help="仅验证不导入")
    parser.add_argument("--neo4j", action="store_true", help="导入到 Neo4j")
    args = parser.parse_args()

    try:
        name, importer = detect_importer(args.file)
        print(f"检测到 {name} 文件: {args.file}")

        result = importer.import_all(args.file, dry_run=args.dry_run)
        print_stats(name, result.stats, args.dry_run)

        if args.dry_run:
            print("\n[DRY-RUN] 前5条有效记录预览:")
            for i, record in enumerate(result.records[:5]):
                print(f"  {i+1}. {record.model_dump(mode='json')}")

        if args.neo4j and not args.dry_run:
            graph_result = asyncio.run(write_records_to_neo4j(result.records))
            print_neo4j_stats(graph_result.nodes_written, graph_result.edges_written)

        sys.exit(0 if result.stats.failed == 0 else 1)

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
