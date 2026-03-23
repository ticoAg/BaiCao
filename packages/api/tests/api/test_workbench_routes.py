import pytest
from unittest.mock import AsyncMock, patch

from .helpers import assert_status, assert_json_keys


class TestWorkbenchExecute:
    @pytest.mark.asyncio
    async def test_execute_workbench_command_returns_frames(self, client):
        service_response = {
            "command": ":help",
            "frames": [
                {
                    "id": "frame-help",
                    "type": "text",
                    "title": "命令帮助",
                    "status": "ok",
                    "payload": {"markdown": "help"},
                }
            ],
            "history_item": {
                "command": ":help",
                "source": "workbench",
            },
        }

        with patch("app.api.workbench.workbench_service") as mock_service:
            mock_service.execute = AsyncMock(return_value=service_response)

            resp = await client.post(
                "/api/v1/workbench/execute",
                json={"command": ":help", "source": "workbench"},
            )

        assert_status(resp, 200)
        data = resp.json()
        assert_json_keys(data, {"command", "frames", "history_item"})
        assert data["frames"][0]["type"] == "text"


class TestValidateCypher:
    @pytest.mark.asyncio
    async def test_validate_cypher_returns_result(self, client):
        validation_result = {
            "valid": False,
            "normalized_query": "MATCH (n) DELETE n",
            "errors": ["Write operations are not allowed."],
            "warnings": [],
            "readonly": False,
        }

        with patch("app.api.workbench.workbench_service") as mock_service:
            mock_service.validate_cypher = AsyncMock(return_value=validation_result)

            resp = await client.post(
                "/api/v1/workbench/validate-cypher",
                json={"query": "MATCH (n) DELETE n", "source": "workbench"},
            )

        assert_status(resp, 200)
        data = resp.json()
        assert data["valid"] is False
        assert "Write operations are not allowed." in data["errors"]

    @pytest.mark.asyncio
    async def test_validate_cypher_returns_422_for_missing_query(self, client):
        resp = await client.post("/api/v1/workbench/validate-cypher", json={})

        assert_status(resp, 422)
