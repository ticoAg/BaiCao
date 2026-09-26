"""TypeSafe system_one 客户端。

问答循环里的判定是第一个调用方。以后的审查预筛复用 ask，不要再包一个客户端。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

_PLACEHOLDER_KEYS = {"", "your_api_key_here"}
_DEFAULT_MODEL = "decision-model-preview"


def typesafe_ready(settings: object) -> bool:
    key = str(getattr(settings, "typesafe_api_key", "") or "").strip()
    base_url = str(getattr(settings, "typesafe_base_url", "") or "").strip()
    return key not in _PLACEHOLDER_KEYS and bool(base_url)


class SystemOneClient(Protocol):
    async def system_one(self, state: Any, questions: Mapping[str, Any]) -> Any: ...

    async def aclose(self) -> None: ...


def dump_answers(response: Any) -> dict[str, Any]:
    answers = getattr(response, "answers", {}) or {}
    dumped: dict[str, Any] = {}
    for name, answer in answers.items():
        dump = getattr(answer, "model_dump", None)
        if callable(dump):
            dumped[str(name)] = dump(mode="json")
        elif isinstance(answer, dict):
            dumped[str(name)] = answer
    model = getattr(response, "model", "")
    return {"model": "" if model is None else str(model), "answers": dumped}


class SystemOneJudge:
    """一次 system_one 调用。questions 由调用方给定，这里不保存业务标准。"""

    def __init__(self, client: SystemOneClient) -> None:
        self._client = client

    @classmethod
    def from_settings(cls, settings: object) -> SystemOneJudge:
        timeout = float(getattr(settings, "typesafe_timeout_seconds", 60) or 60)
        model = str(getattr(settings, "typesafe_model", "") or _DEFAULT_MODEL)
        client = AsyncTypeSafeClient(
            api_key=str(getattr(settings, "typesafe_api_key", "") or ""),
            base_url=str(getattr(settings, "typesafe_base_url", "") or ""),
            model=model,
            timeout=timeout,
            retry=RetryPolicy(max_retries=2),
        )
        return cls(client)

    async def ask(self, state: Any, questions: Mapping[str, Any]) -> dict[str, Any]:
        response = await self._client.system_one(state, questions)
        return dump_answers(response)

    async def aclose(self) -> None:
        await self._client.aclose()
