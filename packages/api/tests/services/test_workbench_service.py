import pytest
from unittest.mock import AsyncMock, patch


def test_validate_cypher_response_rejects_write_queries():
    from app.schemas.workbench import CypherValidationResult

    result = CypherValidationResult.model_validate(
        {
            "valid": False,
            "normalized_query": "MATCH (n) DELETE n",
            "errors": ["Write operations are not allowed."],
            "warnings": [],
        }
    )

    assert result.valid is False
    assert result.normalized_query == "MATCH (n) DELETE n"
    assert result.errors == ["Write operations are not allowed."]


def test_workbench_execute_response_supports_graph_and_error_frames():
    from app.schemas.workbench import WorkbenchExecuteResponse

    response = WorkbenchExecuteResponse.model_validate(
        {
            "command": ":help",
            "frames": [
                {
                    "id": "frame-help",
                    "type": "text",
                    "title": "Commands",
                    "status": "ok",
                    "payload": {"markdown": "help"},
                },
                {
                    "id": "frame-error",
                    "type": "error",
                    "title": "Unknown command",
                    "status": "error",
                    "payload": {"message": "bad command"},
                },
            ],
            "history_item": {
                "command": ":help",
                "source": "workbench",
            },
        }
    )

    assert response.command == ":help"
    assert len(response.frames) == 2
    assert response.frames[0].type == "text"
    assert response.frames[1].type == "error"
    assert response.history_item.source == "workbench"


@pytest.mark.asyncio
async def test_execute_routes_help_command_to_text_frame():
    from app.services.workbench_service import WorkbenchService

    service = WorkbenchService()
    response = await service.execute(":help", source="workbench")

    assert response.frames[0].type == "text"
    assert response.frames[0].title == "命令帮助"


@pytest.mark.asyncio
async def test_execute_routes_exact_semantic_query_to_graph_frame():
    from app.services.workbench_service import WorkbenchService

    graph_data = {
        "center": {"id": "herb-1", "name": "人参", "labels": ["Herb"], "status": "verified"},
        "nodes": [{"id": "herb-1", "name": "人参", "labels": ["Herb"], "status": "verified"}],
        "edges": [],
    }

    service = WorkbenchService()
    with patch("app.services.workbench_service.graph_service") as mock_graph_service:
        mock_graph_service.get_herb_graph = AsyncMock(return_value=graph_data)
        response = await service.execute("查人参的功效", source="workbench")

    assert response.frames[0].type == "graph"
    assert response.frames[0].status == "ok"
    assert response.frames[0].payload["graph"]["center"]["name"] == "人参"


@pytest.mark.asyncio
async def test_validate_cypher_rejects_delete_keyword():
    from app.services.workbench_service import WorkbenchService

    service = WorkbenchService()
    result = await service.validate_cypher("MATCH (n) DELETE n")

    assert result.valid is False
    assert "Write operations are not allowed." in result.errors
