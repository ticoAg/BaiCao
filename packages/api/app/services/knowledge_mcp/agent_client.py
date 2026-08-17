"""给 OpenAI Agents SDK 用的长期 MCP stdio 客户端。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agents.mcp import MCPServerStdio

_API_DIR = Path(__file__).resolve().parents[3]
_server: MCPServerStdio | None = None


async def get_knowledge_mcp_server() -> MCPServerStdio:
    global _server
    if _server is None:
        env = os.environ.copy()
        _server = MCPServerStdio(
            name="baicao-knowledge",
            params={
                "command": sys.executable,
                "args": ["-m", "app.services.knowledge_mcp"],
                "cwd": str(_API_DIR),
                "env": env,
            },
            cache_tools_list=True,
        )
        await _server.connect()
    return _server


async def close_knowledge_mcp_server() -> None:
    global _server
    if _server is not None:
        await _server.cleanup()
        _server = None
