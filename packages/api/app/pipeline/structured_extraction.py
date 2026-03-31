from __future__ import annotations

import json
from typing import Any, cast

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_client import _normalize_chunk_content, get_chat_model


class PipelineStructuredExtractionClient:
    async def extract_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        model = get_chat_model()
        if model is None:
            raise ValueError("LLM provider unavailable for pharmacopoeia extraction")

        response = await model.ainvoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=json.dumps(user_payload, ensure_ascii=False)),
            ]
        )
        content = _normalize_chunk_content(response.content)
        return cast(dict[str, Any], json.loads(content))
