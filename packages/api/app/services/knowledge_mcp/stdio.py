"""MCP 进程入口：stdio 或 Streamable HTTP。

    uv run python -m app.services.knowledge_mcp
    uv run python -m app.services.knowledge_mcp --transport streamable-http
"""

from __future__ import annotations

import argparse

from .server import knowledge_mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="BaiCao knowledge MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http", "sse"),
        default="stdio",
        help="MCP transport. streamable-http 是现行 HTTP 传输；sse 已弃用。",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.transport == "streamable-http":
        knowledge_mcp.settings.host = args.host
        knowledge_mcp.settings.port = args.port
    knowledge_mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
