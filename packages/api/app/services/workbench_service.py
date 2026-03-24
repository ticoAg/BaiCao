from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from ..kg.graph_service import graph_service
from ..schemas.workbench import (
    CypherValidationResult,
    WorkbenchExecuteResponse,
    WorkbenchFrame,
    WorkbenchHistoryItem,
)


FORBIDDEN_CYPHER_KEYWORDS = {
    "CREATE",
    "MERGE",
    "DELETE",
    "SET",
    "REMOVE",
    "DROP",
    "LOAD CSV",
    "FOREACH",
    "APOC",
}
READONLY_CYPHER_PREFIXES = ("MATCH", "RETURN", "WITH", "UNWIND", "OPTIONAL MATCH")


class WorkbenchService:
    def __init__(self) -> None:
        self.history: list[WorkbenchHistoryItem] = []

    async def execute(
        self,
        command: str,
        source: str = "workbench",
    ) -> WorkbenchExecuteResponse:
        normalized_command = command.strip()
        history_item = self._build_history_item(normalized_command, source)
        self.history.append(history_item)

        if normalized_command.startswith(":help"):
            frames = [self._text_frame("命令帮助", self._help_markdown(), command=normalized_command)]
        elif normalized_command.startswith(":clear"):
            frames = [self._text_frame("结果已清空", "已请求清空结果流。", command=normalized_command)]
        elif normalized_command.startswith(":history"):
            frames = [self._text_frame("命令历史", self._history_markdown(), command=normalized_command)]
        elif self._looks_like_cypher(normalized_command):
            validation = await self.validate_cypher(normalized_command)
            if not validation.valid:
                frames = [
                    self._error_frame(
                        "Cypher 校验失败",
                        validation.errors[0] if validation.errors else "Cypher 校验失败",
                        details=validation.errors[1:] or validation.warnings,
                        command=normalized_command,
                    )
                ]
            else:
                rows = await graph_service.execute_readonly_cypher(validation.normalized_query)
                frames = [
                    self._table_frame(
                        title="Cypher 查询结果",
                        rows=rows,
                        command=normalized_command,
                    )
                ]
        else:
            frames = [await self.run_exact_query(normalized_command, command=normalized_command)]

        return WorkbenchExecuteResponse(
            command=normalized_command,
            frames=frames,
            history_item=history_item,
        )

    async def validate_cypher(self, query: str) -> CypherValidationResult:
        normalized_query = " ".join(query.strip().split())
        upper_query = normalized_query.upper()
        errors: list[str] = []
        warnings: list[str] = []

        if ";" in normalized_query:
            errors.append("Multiple statements are not allowed.")

        for keyword in FORBIDDEN_CYPHER_KEYWORDS:
            if keyword in upper_query:
                errors.append("Write operations are not allowed.")
                break

        if not upper_query.startswith(READONLY_CYPHER_PREFIXES):
            warnings.append("Query does not start with a common read-only clause.")

        return CypherValidationResult(
            valid=not errors,
            normalized_query=normalized_query,
            errors=errors,
            warnings=warnings,
            readonly=not errors,
        )

    async def run_exact_query(self, text: str, command: str | None = None) -> WorkbenchFrame:
        herb_name = self._extract_entity_name(text)
        graph = await graph_service.get_herb_graph(herb_name, depth=2)
        summary = f"以 {herb_name} 为中心的精确图谱查询结果"
        return self._graph_frame(
            title=f"{herb_name} 图谱",
            graph=graph,
            summary=summary,
            mode="exact",
            command=command or text,
        )

    def _extract_entity_name(self, text: str) -> str:
        patterns = [
            r"查(?P<name>[\u4e00-\u9fffA-Za-z0-9]+?)的",
            r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]+?)有什么",
            r"(?P<name>[\u4e00-\u9fffA-Za-z0-9]+?)图谱",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group("name")
        fallback = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,8}", text)
        return fallback[0] if fallback else "陈皮"

    def _looks_like_cypher(self, command: str) -> bool:
        upper_command = command.upper()
        return upper_command.startswith(READONLY_CYPHER_PREFIXES) or "MATCH " in upper_command

    def _build_history_item(self, command: str, source: str) -> WorkbenchHistoryItem:
        return WorkbenchHistoryItem(
            command=command,
            source=source,  # type: ignore[arg-type]
            executed_at=datetime.now(timezone.utc).isoformat(),
        )

    def _help_markdown(self) -> str:
        return "\n".join(
            [
                "### Workbench Commands",
                "- `:help` 查看命令帮助",
                "- `:clear` 清空结果流",
                "- `:history` 查看命令历史",
                "- 直接输入自然语言，例如 `查人参的功效`",
                "- 直接输入只读 Cypher，例如 `MATCH (n) RETURN n LIMIT 5`",
            ]
        )

    def _history_markdown(self) -> str:
        if not self.history:
            return "暂无历史命令。"
        return "\n".join(
            f"- `{item.command}` · {item.source}" for item in reversed(self.history[-20:])
        )

    def _text_frame(self, title: str, markdown: str, command: str) -> WorkbenchFrame:
        return WorkbenchFrame(
            id=f"frame-{uuid4()}",
            type="text",
            title=title,
            status="ok",
            payload={"markdown": markdown},
            command=command,
        )

    def _error_frame(
        self,
        title: str,
        message: str,
        details: list[str] | None = None,
        command: str | None = None,
    ) -> WorkbenchFrame:
        payload: dict[str, Any] = {"message": message}
        if details:
            payload["details"] = details
        return WorkbenchFrame(
            id=f"frame-{uuid4()}",
            type="error",
            title=title,
            status="error",
            payload=payload,
            command=command,
        )

    def _table_frame(
        self,
        title: str,
        rows: list[dict],
        command: str | None = None,
    ) -> WorkbenchFrame:
        columns = list(rows[0].keys()) if rows else []
        return WorkbenchFrame(
            id=f"frame-{uuid4()}",
            type="table",
            title=title,
            status="ok",
            payload={"columns": columns, "rows": rows},
            command=command,
        )

    def _graph_frame(
        self,
        title: str,
        graph: dict,
        summary: str,
        mode: str,
        command: str | None = None,
    ) -> WorkbenchFrame:
        return WorkbenchFrame(
            id=f"frame-{uuid4()}",
            type="graph",
            title=title,
            status="ok",
            payload={
                "graph": graph,
                "summary": summary,
                "mode": mode,
            },
            command=command,
        )


workbench_service = WorkbenchService()
